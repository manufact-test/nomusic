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
    private bool _nativeNetworkRecoveryPending;
    private bool _nativeNetworkRecoveryAwaitingHeartbeat;
    // Generation-gated acknowledgement: stale heartbeats may not release a
    // same-track source hold before the renderer has seen the resumed state.
    private int _nativeNetworkRecoveryEpoch;
    private string _nativeCurrentTrackRevalidationId = "";
    private int _nativeCurrentTrackRevalidationEpoch;
    private bool _playerUnavailable;
    // High-frequency native state checks used to flood diagnostics every
    // ~370 ms, rotating out the exact failure the owner was trying to report.
    private long _lastNativeStateDiagUtcTicks;
    private void RecordNativeStateSample()
    {
        var now = DateTime.UtcNow.Ticks;
        var prior = Interlocked.Read(ref _lastNativeStateDiagUtcTicks);
        if (now - prior < TimeSpan.FromSeconds(10).Ticks ||
            Interlocked.CompareExchange(ref _lastNativeStateDiagUtcTicks, now, prior) != prior)
            return;
        DiagnosticLog.Record("NATIVE_STATE_RECEIVED");
    }
    private string _lastSong = "";
    private string _lastTitle = "";
    private string _lastArtist = "";
    private long _lastDurationMs;
    private string _lastStatus = "NOT_CONNECTED";
    private string _lastSource = "UNKNOWN";
    private string _lastPlaybackState = "UNKNOWN";
    private string _lastHeartbeatInstanceId = "";
    private long _lastHeartbeatSequence;
    // Prevent a delayed heartbeat from a retired native host instance from
    // taking control of the owner's current song after a newer host takes over.
    private readonly HashSet<string> _retiredHeartbeatInstances = new(StringComparer.Ordinal);
    private DateTimeOffset _lastHeartbeatAt = DateTimeOffset.MinValue;
    private const int HeartbeatFreshnessSeconds = 12;
    private const int TrackMetadataGapGraceSeconds = 9;
    private DateTimeOffset _lastValidTrackAt = DateTimeOffset.MinValue;
    public static bool IsTransientTrackMetadataGap(bool validTrackId,
        string? status, string? playbackState) =>
        !validTrackId && (playbackState is "PLAYING" or "PAUSED") &&
        (status is "RESOLVING" or "NATIVE_RECOVERING" or "NATIVE_CONNECTED" or
            "NATIVE_MAPPING_ACCEPTED" or "NATIVE_SOURCE_VERIFIED" or
            "NATIVE_ORIGINAL_SOURCE_VERIFIED");
    public static bool IsTrackMetadataDisplayable(DateTimeOffset lastValidTrackAt,
        DateTimeOffset now, bool enabled, bool playerUnavailable) =>
        enabled && !playerUnavailable && lastValidTrackAt != DateTimeOffset.MinValue &&
        now >= lastValidTrackAt &&
        now - lastValidTrackAt <= TimeSpan.FromSeconds(TrackMetadataGapGraceSeconds);
    public static bool IsHeartbeatFresh(DateTimeOffset seenAt, DateTimeOffset now) =>
        seenAt != DateTimeOffset.MinValue && now >= seenAt &&
        now - seenAt <= TimeSpan.FromSeconds(HeartbeatFreshnessSeconds);
    private bool IsHeartbeatFreshLocked() =>
        _enabled && IsHeartbeatFresh(_lastHeartbeatAt, DateTimeOffset.UtcNow);
    // Contribution actions and the visible current-track UI must share the
    // same bounded metadata lease. Heartbeat freshness alone can outlive the
    // last valid track ID and expose a stale previous song to Suggest/Upload.
    private bool IsTrackMetadataDisplayableLocked() =>
        IsTrackMetadataDisplayable(_lastValidTrackAt, DateTimeOffset.UtcNow,
            _enabled, _playerUnavailable);
    public event Action? Changed;

    public BridgeServer(CelikomApi api, SessionStore store)
    {
        _api = api;
        _store = store;
        RotateCode();
    }
    public bool Enabled { get { lock (_gate) return _enabled; } }
    public bool NativeNetworkRecoveryPending
    { get { lock (_gate) return _nativeNetworkRecoveryPending; } }
    public int NativeNetworkRecoveryEpoch
    { get { lock (_gate) return _nativeNetworkRecoveryEpoch; } }
    public string PairCode { get { lock (_gate) return _code; } }
    public string LastSong { get { lock (_gate) return IsTrackMetadataDisplayableLocked() ? _lastSong : ""; } }
    public string LastTrackTitle { get { lock (_gate) return IsTrackMetadataDisplayableLocked() ? _lastTitle : ""; } }
    public string LastTrackArtist { get { lock (_gate) return IsTrackMetadataDisplayableLocked() ? _lastArtist : ""; } }
    public long LastTrackDurationMs { get { lock (_gate) return IsTrackMetadataDisplayableLocked() ? _lastDurationMs : 0; } }
    public string LastStatus { get { lock (_gate) return IsHeartbeatFreshLocked() ? _lastStatus : _enabled ? "UNAVAILABLE" : "OFF"; } }
    public string LastSource { get { lock (_gate) return IsHeartbeatFreshLocked() ? _lastSource : "UNKNOWN"; } }
    public string LastPlaybackState { get { lock (_gate) return IsHeartbeatFreshLocked() ? _lastPlaybackState : "UNKNOWN"; } }
    public bool HasFreshHeartbeat { get { lock (_gate) return IsHeartbeatFreshLocked(); } }
    public bool PlayerUnavailable { get { lock (_gate) return _playerUnavailable; } }
    public DateTimeOffset LastHeartbeatAt { get { lock (_gate) return _lastHeartbeatAt; } }
    public DateTimeOffset CodeExpires { get { lock (_gate) return _codeExpires; } }

    // One immutable, lock-consistent view prevents the GUI from combining
    // a new track ID with title/artist fields from a different heartbeat.
    public PlaybackSnapshot GetPlaybackSnapshot()
    {
        lock (_gate)
        {
            var now = DateTimeOffset.UtcNow;
            var fresh = IsHeartbeatFresh(_lastHeartbeatAt, now) && _enabled;
            var trackMetadataDisplayable = IsTrackMetadataDisplayable(
                _lastValidTrackAt, now, _enabled, _playerUnavailable);
            return new PlaybackSnapshot(
                _enabled, fresh, _playerUnavailable, _nativeNetworkRecoveryPending,
                trackMetadataDisplayable ? _lastSong : "",
                trackMetadataDisplayable ? _lastTitle : "",
                trackMetadataDisplayable ? _lastArtist : "",
                trackMetadataDisplayable ? _lastDurationMs : 0,
                fresh ? _lastStatus : (_enabled ? "UNAVAILABLE" : "OFF"),
                fresh ? _lastSource : "UNKNOWN",
                fresh ? _lastPlaybackState : "UNKNOWN",
                _lastHeartbeatAt);
        }
    }

    public bool CanResolve => Enabled && _api.IsLoggedIn;

    public void SetNativeNetworkRecoveryPending(bool pending)
    {
        lock (_gate)
        {
            _nativeNetworkRecoveryPending = pending;
            if (pending)
                _nativeNetworkRecoveryEpoch = _nativeNetworkRecoveryEpoch == int.MaxValue
                    ? 1 : _nativeNetworkRecoveryEpoch + 1;
            // A newer route signal invalidates any earlier re-enable handshake.
            _nativeNetworkRecoveryAwaitingHeartbeat = false;
        }
    }

    public static int NextCurrentTrackRevalidationEpoch(int current) =>
        current >= int.MaxValue ? 1 : Math.Max(0, current) + 1;

    public int RequestCurrentTrackRevalidation(string trackId)
    {
        if (!GrantValidator.IsTrackId(trackId)) return 0;
        int epoch;
        lock (_gate)
        {
            if (!_api.IsLoggedIn || (!_enabled && !_nativeNetworkRecoveryPending))
                return 0;
            _nativeCurrentTrackRevalidationId = trackId;
            _nativeCurrentTrackRevalidationEpoch =
                NextCurrentTrackRevalidationEpoch(_nativeCurrentTrackRevalidationEpoch);
            epoch = _nativeCurrentTrackRevalidationEpoch;
        }
        DiagnosticLog.Record("CURRENT_TRACK_REVALIDATION_REQUESTED");
        return epoch;
    }

    public void MarkPlayerUnavailable(bool retireNativeHostInstance = false)
    {
        lock (_gate)
        {
            _playerUnavailable = true;
            if (retireNativeHostInstance && _lastHeartbeatInstanceId.Length > 0)
            {
                _retiredHeartbeatInstances.Add(_lastHeartbeatInstanceId);
                _lastHeartbeatInstanceId = "";
                _lastHeartbeatSequence = 0;
            }
            _lastSong = "";
            _lastTitle = "";
            _lastArtist = "";
            _lastDurationMs = 0;
            _lastValidTrackAt = DateTimeOffset.MinValue;
            _lastStatus = "UNAVAILABLE";
            _lastSource = "UNKNOWN";
            _lastPlaybackState = "UNKNOWN";
            _lastHeartbeatAt = DateTimeOffset.MinValue;
        }
        if (retireNativeHostInstance)
            DiagnosticLog.Record("YANDEX_PROCESS_UNAVAILABLE");
        Changed?.Invoke();
    }

    public void SetEnabled(bool enabled)
    {
        lock (_gate)
        {
            if (_enabled == enabled)
            {
                if (!enabled && !_nativeNetworkRecoveryPending)
                    _playerUnavailable = false;
                return;
            }
            var wasEnabled = _enabled;
            _enabled = enabled;
            if (enabled && !wasEnabled && _nativeNetworkRecoveryPending)
                _nativeNetworkRecoveryAwaitingHeartbeat = true;
            if (!enabled)
            {
                _nativeNetworkRecoveryAwaitingHeartbeat = false;
                if (!_nativeNetworkRecoveryPending)
                    _playerUnavailable = false;
            }
            _lastStatus = enabled ? "UNAVAILABLE" : "OFF";
            _lastSource = "UNKNOWN";
            _lastPlaybackState = "UNKNOWN";
            _lastHeartbeatInstanceId = "";
            _lastHeartbeatSequence = 0;
            // A transient VPN suspension must not make an exited native-host
            // instance valid again. Keep its retirement fence until a real
            // Stop/logout/denial ends the recovery session.
            if (!_nativeNetworkRecoveryPending)
                _retiredHeartbeatInstances.Clear();
            _lastHeartbeatAt = DateTimeOffset.MinValue;
            _lastSong = "";
            _lastTitle = "";
            _lastArtist = "";
            _lastDurationMs = 0;
            _lastValidTrackAt = DateTimeOffset.MinValue;
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
            if (IsNativeProtocolRequest(ctx)) RecordNativeStateSample();
            string currentTrackRevalidationId;
            int currentTrackRevalidationEpoch;
            lock (_gate)
            {
                currentTrackRevalidationId = _api.IsLoggedIn
                    ? _nativeCurrentTrackRevalidationId : "";
                currentTrackRevalidationEpoch = _nativeCurrentTrackRevalidationEpoch;
            }
            return Results.Json(new { enabled = CanResolve,
                signedIn = _api.IsLoggedIn, apiOrigin = _api.IsLoggedIn ? _api.Origin : "",
                networkRecoveryPending = NativeNetworkRecoveryPending,
                recoveryEpoch = NativeNetworkRecoveryEpoch,
                currentTrackRevalidationId, currentTrackRevalidationEpoch,
                transport = "paired" });
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
            catch (ApiFailure failure)
            {
                DiagnosticLog.Record("RESOLVE_API_FAILURE", id);
                // Denied/no-version are authoritative. Retry ONLY temporary
                // API failures; client still validates entitlements each time.
                return Results.Json(new { found = false,
                    retryable = failure.HttpStatus is 408 or >= 500 and <= 599 });
            }
            catch (HttpRequestException)
            {
                DiagnosticLog.Record("RESOLVE_NETWORK_FAILURE", id);
                return Results.Json(new { found = false, retryable = true });
            }
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
                  "NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED" or
                  "NATIVE_SOURCE_VERIFIED" or "NATIVE_ORIGINAL_SOURCE_VERIFIED" or
                  "NATIVE_RECOVERING" or "NATIVE_SOURCE_FAILED"))
                return Results.BadRequest();
            var accepted = false;
            lock (_gate)
            {
                if (_enabled)
                {
                    var sequenced = beat.InstanceId is { Length: >= 8 and <= 80 } &&
                        beat.InstanceId.All(c => char.IsAsciiLetterOrDigit(c) ||
                            c is '-' or '_') && beat.Sequence is > 0;
                    // An old in-flight heartbeat cannot restore a previous
                    // track after a newer one has already been observed.
                    if (sequenced &&
                        !_retiredHeartbeatInstances.Contains(beat.InstanceId!) &&
                        (beat.InstanceId != _lastHeartbeatInstanceId ||
                         beat.Sequence!.Value > _lastHeartbeatSequence))
                    {
                        if (_lastHeartbeatInstanceId.Length > 0 &&
                            beat.InstanceId != _lastHeartbeatInstanceId)
                            _retiredHeartbeatInstances.Add(_lastHeartbeatInstanceId);
                        _lastHeartbeatInstanceId = beat.InstanceId!;
                        _lastHeartbeatSequence = beat.Sequence!.Value;
                        accepted = true;
                    }
                    else if (!sequenced && _lastHeartbeatInstanceId.Length == 0)
                        accepted = true; // old native host until W141 is installed
                    if (accepted)
                    {
                        var valid = GrantValidator.IsTrackId(beat.TrackId);
                        var transientTrackGap = IsTransientTrackMetadataGap(
                            valid, beat.Status, beat.PlaybackState);
                        var title = valid ? SafeTrackText(beat.Title) : "";
                        var artist = valid ? SafeTrackText(beat.Artist) : "";
                        var durationMs = valid && beat.DurationMs is >= 1000 and <= 86400000
                            ? beat.DurationMs.Value : 0;
                        if (valid)
                        {
                            var sameTrack = string.Equals(
                                _lastSong, beat.TrackId, StringComparison.Ordinal);
                            _lastSong = beat.TrackId!;
                            _lastValidTrackAt = DateTimeOffset.UtcNow;
                            if (!sameTrack)
                            {
                                // A real track change replaces all prior metadata,
                                // including with empty values when Yandex has none yet.
                                _lastTitle = title;
                                _lastArtist = artist;
                                _lastDurationMs = durationMs;
                            }
                            else
                            {
                                // Same-track heartbeat pulses can temporarily omit
                                // MediaSession metadata while the player surface moves.
                                if (title.Length > 0) _lastTitle = title;
                                if (artist.Length > 0) _lastArtist = artist;
                                if (durationMs > 0) _lastDurationMs = durationMs;
                            }
                        }
                        else if (!transientTrackGap)
                        {
                            // Explicit stop/unavailable/unknown state clears identity.
                            // A short ID-less PLAYING/PAUSED transition keeps the last
                            // title while Yandex resolves the next queue entity.
                            _lastSong = "";
                            _lastTitle = "";
                            _lastArtist = "";
                            _lastDurationMs = 0;
                            _lastValidTrackAt = DateTimeOffset.MinValue;
                        }
                        _lastStatus = beat.Status;
                        _playerUnavailable = beat.Status == "UNAVAILABLE" && !valid;
                        _lastSource = beat.Status == "NATIVE_SOURCE_VERIFIED" &&
                            beat.Source == "ACTIVE_REPLACEMENT" ? "ACTIVE_REPLACEMENT" :
                            PlaybackSourceEvidence.OriginalVerified(
                                _enabled, beat.Status, beat.Source) ? "ORIGINAL" : "UNKNOWN";
                        _lastPlaybackState = beat.PlaybackState is "PLAYING" or "PAUSED" or "STOPPED"
                            ? beat.PlaybackState : "UNKNOWN";
                        _lastHeartbeatAt = DateTimeOffset.UtcNow;
                        // This generation is echoed only AFTER the host
                        // delivers the resumed state to the real renderer.
                        // Pre-resume heartbeats cannot clear the hold early.
                        if (_nativeNetworkRecoveryAwaitingHeartbeat &&
                            beat.RecoveryEpoch == _nativeNetworkRecoveryEpoch &&
                            beat.Status is ("NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED" or
                                "NATIVE_SOURCE_VERIFIED" or "NATIVE_ORIGINAL_SOURCE_VERIFIED"))
                        {
                            _nativeNetworkRecoveryAwaitingHeartbeat = false;
                            _nativeNetworkRecoveryPending = false;
                        }
                    }
                }
            }
            if (accepted)
            {
                DiagnosticLog.Record("HEARTBEAT_" + beat.Status);
                Changed?.Invoke();
            }
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
    public sealed record PlaybackSnapshot(
        bool Enabled,
        bool HeartbeatFresh,
        bool PlayerUnavailable,
        bool NativeNetworkRecoveryPending,
        string TrackId,
        string Title,
        string Artist,
        long DurationMs,
        string Status,
        string Source,
        string PlaybackState,
        DateTimeOffset HeartbeatAt);

    private static string SafeTrackText(string? value) =>
        value is { Length: <= 180 } && !value.Any(char.IsControl) ? value.Trim() : "";

    public sealed record Heartbeat(string? TrackId, string Status,
        string? Title = null, string? Artist = null, long? DurationMs = null,
        string? Source = null, string? PlaybackState = null,
        string? InstanceId = null, long? Sequence = null,
        int? RecoveryEpoch = null);
}
