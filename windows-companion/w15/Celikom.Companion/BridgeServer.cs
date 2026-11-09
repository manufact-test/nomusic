using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;

namespace Celikom.Companion;

/// <summary>
/// Localhost ONLY, versioned API for the PulseSync isolated add-on.
/// No Yandex account data or CELIKOM auth/refresh token is returned.
/// </summary>
public sealed class BridgeServer : IAsyncDisposable
{
    public const int Port = 21471;
    private static readonly Regex AddonOrigin =
        new(@"^https://addon-[1-9][0-9]{0,7}\.pulsesync\.invalid$",
            RegexOptions.CultureInvariant);
    // Native Electron renderer origins (no wildcard, no file: or null).
    private static readonly HashSet<string> NativeYandexOrigins =
        new(StringComparer.Ordinal)
        {
            "https://desktop.app.music.yandex.net",
            "https://music.yandex.ru",
            "https://next.music.yandex.ru",
            "https://music.yandex.com"
        };
    public static bool ValidNativeOrigin(string? origin) =>
        origin is not null && NativeYandexOrigins.Contains(origin);
    public static bool ValidNativeProtocolOrigin(string? origin) =>
        origin is "null" or "musicapplication://desktop";
    private static void TraceNative(HttpContext context)
    {
        if (!ValidNativeProtocolOrigin(context.Request.Headers.Origin.ToString())) return;
        if (!IsNativeProtocolRequest(context)) return;
        var target = Environment.GetEnvironmentVariable("CELIKOM_W23_DEV_BRIDGE_DIAG");
        if (string.IsNullOrWhiteSpace(target)) return;
        var code = context.Request.Method == "OPTIONS" ? "NATIVE_PREFLIGHT" :
            context.Request.Path == "/v1/state" ? "NATIVE_STATE_REQUEST" :
            context.Request.Path == "/v1/heartbeat" ? "NATIVE_HEARTBEAT_REQUEST" : "";
        if (code.Length == 0) return;
        try { File.AppendAllText(target, code + Environment.NewLine); }
        catch (IOException) { }
        catch (UnauthorizedAccessException) { }
    }
    private static bool IsNativeProtocolRequest(HttpContext context)
    {
        var origin = context.Request.Headers.Origin.ToString();
        if (!ValidNativeProtocolOrigin(origin)) return false;
        // A file:/sandboxed web page cannot access native playback without
        // possessing the 256-bit same-user capability and explicit native marker.
        if (context.Request.Method == "OPTIONS")
        {
            var requested = context.Request.Headers.AccessControlRequestHeaders.ToString();
            return requested.Contains("x-celikom-bridge-token", StringComparison.OrdinalIgnoreCase) &&
                   requested.Contains("x-celikom-native-host", StringComparison.OrdinalIgnoreCase);
        }
        return context.Request.Headers["X-Celikom-Native-Host"].ToString() == "1" &&
               SessionStore.IsHexToken(context.Request.Headers["X-Celikom-Bridge-Token"].ToString());
    }
    private readonly object _gate = new();
    private readonly CelikomApi _api;
    private readonly SessionStore _store;
    private WebApplication? _app;
    private string _code = "";
    private DateTimeOffset _codeExpires;
    private int _failedPairs;
    private bool _enabled;
    private string _lastSong = "";
    private string _lastStatus = "NOT_CONNECTED";
    public event Action? Changed;

    public BridgeServer(CelikomApi api, SessionStore store)
    {
        _api = api;
        _store = store;
        RotateCode();
    }
    public bool Enabled { get { lock (_gate) return _enabled; } }
    public string PairCode { get { lock (_gate) return _code; } }
    public string LastSong { get { lock (_gate) return _lastSong; } }
    public string LastStatus { get { lock (_gate) return _lastStatus; } }
    public DateTimeOffset CodeExpires { get { lock (_gate) return _codeExpires; } }
    public bool CanResolve => Enabled && _api.IsLoggedIn;

    public void SetEnabled(bool enabled)
    {
        lock (_gate)
        {
            if (_enabled == enabled) return;
            _enabled = enabled;
            _lastStatus = enabled ? "UNAVAILABLE" : "OFF";
            _lastSong = "";
        }
        DiagnosticLog.Record(enabled ? "START_ENABLED" : "STOP_DISABLED");
        Changed?.Invoke();
    }

    public void RotateCode()
    {
        lock (_gate)
        {
            _code = RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");
            _codeExpires = DateTimeOffset.UtcNow.AddMinutes(10);
            _failedPairs = 0;
        }
        Changed?.Invoke();
    }

    public bool TryPair(string? submittedCode, out string token)
    {
        token = "";
        lock (_gate)
        {
            if (submittedCode is not { Length: 6 } ||
                submittedCode.Any(x => x is < '0' or > '9') ||
                _failedPairs >= 5 || DateTimeOffset.UtcNow >= _codeExpires)
                return false;
            var input = Encoding.UTF8.GetBytes(submittedCode);
            var expected = Encoding.UTF8.GetBytes(_code);
            if (!CryptographicOperations.FixedTimeEquals(input, expected))
            {
                _failedPairs++;
                return false;
            }
            token = _api.Settings.BridgeToken;
            // Single-use code; pair again only after user manually rotates.
            _code = "";
            return true;
        }
    }

    public bool ValidBridgeToken(string? offered)
    {
        if (!SessionStore.IsHexToken(offered)) return false;
        var token = _api.Settings.BridgeToken;
        return CryptographicOperations.FixedTimeEquals(
            Convert.FromHexString(offered!), Convert.FromHexString(token));
    }

    public async Task StartAsync(CancellationToken ct = default)
    {
        if (_app != null) throw new InvalidOperationException("ALREADY_STARTED");
        var builder = WebApplication.CreateSlimBuilder();
        builder.WebHost.UseKestrel(o =>
        {
            o.AddServerHeader = false;
            o.Limits.MaxRequestBodySize = 4096;
            o.Listen(IPAddress.Loopback, Port);
        });
        var app = builder.Build();
        app.Use(async (context, next) =>
        {
            // Only explicitly approved isolated add-on origins may issue requests.
            var origin = context.Request.Headers.Origin.ToString();
            if (!AddonOrigin.IsMatch(origin) && !ValidNativeOrigin(origin) &&
                !IsNativeProtocolRequest(context))
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                return;
            }
            context.Response.Headers.AccessControlAllowOrigin = origin;
            context.Response.Headers.Vary = "Origin";
            context.Response.Headers.AccessControlAllowHeaders = "Content-Type, X-Celikom-Bridge-Token, X-Celikom-Native-Host";
            context.Response.Headers.AccessControlAllowMethods = "GET, POST, OPTIONS";
            context.Response.Headers.CacheControl = "no-store";
            context.Response.Headers["X-Content-Type-Options"] = "nosniff";
            TraceNative(context);
            if (context.Request.Method == "OPTIONS")
            {
                context.Response.StatusCode = StatusCodes.Status204NoContent;
                return;
            }
            await next(context);
        });

        app.MapGet("/v1/health", () => Results.Json(new { companion = true, version = 15 }));
        app.MapPost("/v1/pair", async (HttpContext ctx) =>
        {
            if (ctx.Request.ContentType?.StartsWith("application/json", StringComparison.OrdinalIgnoreCase) != true)
                return Results.StatusCode(415);
            PairRequest? request;
            try { request = await ctx.Request.ReadFromJsonAsync<PairRequest>(cancellationToken: ctx.RequestAborted); }
            catch (Exception ex) when (ex is JsonException or BadHttpRequestException)
            { return Results.BadRequest(new { error = "bad_request" }); }
            if (!TryPair(request?.Code, out var token))
                return Results.Json(new { error = "invalid_pair_code" }, statusCode: 403);
            Changed?.Invoke();
            return Results.Json(new { bridgeToken = token });
        });

        app.MapGet("/v1/state", (HttpContext ctx) =>
        {
            if (!Authorized(ctx)) return Results.Unauthorized();
            if (IsNativeProtocolRequest(ctx)) DiagnosticLog.Record("NATIVE_STATE_RECEIVED");
            return Results.Json(new { enabled = CanResolve,
                signedIn = _api.IsLoggedIn, apiOrigin = _api.IsLoggedIn ? _api.Origin : "", transport = "paired" });
        });

        app.MapGet("/v1/resolve", async (HttpContext ctx) =>
        {
            if (!Authorized(ctx)) return Results.Unauthorized();
            var id = ctx.Request.Query["track_id"].ToString();
            if (!GrantValidator.IsTrackId(id)) return Results.BadRequest(new { error = "invalid_track" });
            DiagnosticLog.Record("RESOLVE_REQUEST", id);
            if (!CanResolve) { DiagnosticLog.Record("RESOLVE_DISABLED", id); return Results.Json(new { found = false }); }
            try
            {
                var grant = await _api.ResolveAsync(id, ctx.RequestAborted);
                if (!CanResolve || grant is null)
                {
                    DiagnosticLog.Record("RESOLVE_MISS", id);
                    return Results.Json(new { found = false });
                }
                DiagnosticLog.Record("RESOLVE_APPROVED", id);
                return Results.Json(new { found = true, grant });
            }
            catch (OperationCanceledException) { DiagnosticLog.Record("RESOLVE_CANCELLED", id); return Results.StatusCode(499); }
            catch (ApiFailure) { DiagnosticLog.Record("RESOLVE_API_FAILURE", id); return Results.Json(new { found = false }); }
            catch (HttpRequestException) { DiagnosticLog.Record("RESOLVE_NETWORK_FAILURE", id); return Results.Json(new { found = false }); }
        });

        app.MapPost("/v1/heartbeat", async (HttpContext ctx) =>
        {
            if (!Authorized(ctx)) return Results.Unauthorized();
            Heartbeat? beat;
            try { beat = await ctx.Request.ReadFromJsonAsync<Heartbeat>(cancellationToken: ctx.RequestAborted); }
            catch (Exception ex) when (ex is JsonException or BadHttpRequestException)
            { return Results.BadRequest(); }
            if (beat == null || beat.Status is not ("OFF" or "UNAVAILABLE" or "ORIGINAL" or
                  "RESOLVING" or "SDK_MAPPING_ACCEPTED" or "HOST_ERROR" or
                  "NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED"))
                return Results.BadRequest();
            lock (_gate)
            {
                _lastSong = GrantValidator.IsTrackId(beat.TrackId) ? beat.TrackId! : "";
                _lastStatus = beat.Status;
            }
            DiagnosticLog.Record("HEARTBEAT_" + beat.Status);
            Changed?.Invoke();
            return Results.Json(new { ok = true });
        });

        try
        {
            await app.StartAsync(ct);
            _app = app;
            DiagnosticLog.Record("BRIDGE_STARTED");
        }
        catch { await app.DisposeAsync(); throw; }
    }

    private bool Authorized(HttpContext ctx) =>
        ValidBridgeToken(ctx.Request.Headers["X-Celikom-Bridge-Token"].ToString());

    public async ValueTask DisposeAsync()
    {
        if (_app == null) return;
        await _app.StopAsync();
        await _app.DisposeAsync();
        _app = null;
    }

    public sealed record PairRequest(string Code);
    public sealed record Heartbeat(string? TrackId, string Status);
}
