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
            if (!AddonOrigin.IsMatch(origin))
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                return;
            }
            context.Response.Headers.AccessControlAllowOrigin = origin;
            context.Response.Headers.Vary = "Origin";
            context.Response.Headers.AccessControlAllowHeaders = "Content-Type, X-Celikom-Bridge-Token";
            context.Response.Headers.AccessControlAllowMethods = "GET, POST, OPTIONS";
            context.Response.Headers.CacheControl = "no-store";
            context.Response.Headers["X-Content-Type-Options"] = "nosniff";
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
            return Results.Json(new { enabled = CanResolve,
                signedIn = _api.IsLoggedIn, apiOrigin = _api.IsLoggedIn ? _api.Origin : "", transport = "paired" });
        });

        app.MapGet("/v1/resolve", async (HttpContext ctx) =>
        {
            if (!Authorized(ctx)) return Results.Unauthorized();
            var id = ctx.Request.Query["track_id"].ToString();
            if (!GrantValidator.IsTrackId(id)) return Results.BadRequest(new { error = "invalid_track" });
            if (!CanResolve) return Results.Json(new { found = false });
            try
            {
                var grant = await _api.ResolveAsync(id, ctx.RequestAborted);
                if (!CanResolve || grant is null) return Results.Json(new { found = false });
                return Results.Json(new { found = true, grant });
            }
            catch (OperationCanceledException) { return Results.StatusCode(499); }
            catch (ApiFailure) { return Results.Json(new { found = false }); }
            catch (HttpRequestException) { return Results.Json(new { found = false }); }
        });

        app.MapPost("/v1/heartbeat", async (HttpContext ctx) =>
        {
            if (!Authorized(ctx)) return Results.Unauthorized();
            Heartbeat? beat;
            try { beat = await ctx.Request.ReadFromJsonAsync<Heartbeat>(cancellationToken: ctx.RequestAborted); }
            catch (Exception ex) when (ex is JsonException or BadHttpRequestException)
            { return Results.BadRequest(); }
            if (beat == null || beat.Status is not ("OFF" or "UNAVAILABLE" or "ORIGINAL" or
                  "RESOLVING" or "SDK_MAPPING_ACCEPTED" or "HOST_ERROR"))
                return Results.BadRequest();
            lock (_gate)
            {
                _lastSong = GrantValidator.IsTrackId(beat.TrackId) ? beat.TrackId! : "";
                _lastStatus = beat.Status;
            }
            Changed?.Invoke();
            return Results.Json(new { ok = true });
        });

        try
        {
            await app.StartAsync(ct);
            _app = app;
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
