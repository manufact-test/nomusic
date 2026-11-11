using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Celikom.Companion;

int checks = 0;
void Test(bool condition, string message)
{
    checks++;
    if (!condition) throw new Exception("W15_TEST_FAILED: " + message);
}
var folder = Path.Combine(Path.GetTempPath(), "celikom-w15-contract-" + Guid.NewGuid().ToString("N"));
try
{
    Test(YandexHostProbe.VerifiedVersion == "5.126.1.0", "pinned official host version");
    Test(YandexHostProbe.VerifiedAsarSha256.Length == 64, "pinned official ASAR fingerprint");
    Test(YandexHostProbe.Inspect(Path.Combine(folder, "yandex-not-installed")).Status ==
        YandexHostStatus.NotInstalled, "missing host does not prompt for patching");
    var incomplete = Path.Combine(folder, "broken-yandex");
    Directory.CreateDirectory(incomplete);
    File.WriteAllText(Path.Combine(incomplete, "Яндекс Музыка.exe"), "not an app");
    Test(YandexHostProbe.Inspect(incomplete).Status == YandexHostStatus.IncompleteInstallation,
        "incomplete install is never treated as compatible");
    Directory.Delete(incomplete, true);

    Test(BridgeServer.ValidNativeOrigin("https://desktop.app.music.yandex.net"),
        "native Yandex renderer is allowed");
    Test(!BridgeServer.ValidNativeOrigin("https://evil.yandex.net"),
        "unrelated renderer is denied");
    Test(!BridgeServer.ValidNativeOrigin("null"),
        "opaque origin denied without native capability");
    Test(BridgeServer.ValidNativeProtocolOrigin("null"),
        "custom Electron scheme can serialize an opaque origin");
    Test(BridgeServer.ValidNativeProtocolOrigin("musicapplication://desktop"),
        "exact official native protocol accepted for capability checking");
    Test(!BridgeServer.ValidNativeProtocolOrigin("file://local"),
        "arbitrary local protocol is not a native host");
    using (var native = new NativeTokenPublisher(Path.Combine(folder, "native-test")))
    {
        var key = new string('a', 64);
        native.Publish(key);
        Test(File.ReadAllText(native.FilePath) == key, "native bridge capability published");
        native.Publish(new string('b', 64));
        Test(File.ReadAllText(native.FilePath) == new string('b', 64),
            "native pairing capability rotates");
    }
    Test(!File.Exists(Path.Combine(folder, "native-test", "native-bridge.key")),
        "native bridge capability removed on shutdown");
    var store = new SessionStore(folder);
    var first = store.LoadOrCreate();
    Test(Guid.TryParse(first.InstallationId, out _), "device ID");
    Test(SessionStore.IsHexToken(first.BridgeToken), "bridge token");
    Test(first.AccessToken == "", "off by default");
    Test(Directory.GetFiles(folder).Length == 1, "only DPAPI session file");
    Test(!Encoding.UTF8.GetString(File.ReadAllBytes(Path.Combine(folder, "session.dpapi"))).Contains(first.BridgeToken),
        "bridge token is encrypted at rest");

    var now = DateTimeOffset.UtcNow;
    var unix = now.ToUnixTimeSeconds() + 200;
    var audio = "/api/v1/audio/42?token=" + new string('a', 64) + "&expires=" + unix + "&sid=7";
    JsonElement Parse(object source) { using var json = JsonDocument.Parse(JsonSerializer.Serialize(source)); return json.RootElement.Clone(); }
    var payload = Parse(new { found = true, audio_url = audio, expires_at = unix,
        duration_ms = 200_000, mime_type = "audio/mpeg" });
    var origin = GrantValidator.NormalizeOrigin("https://api.celikom.example");
    var grant = GrantValidator.FromResolve(payload, "123", origin, now);
    Test(grant != null, "real PHP ResolveService grant accepted");
    Test(grant!.ExpiresAt == unix * 1000, "server Unix seconds to JS milliseconds");
    Test(grant.MimeType == "audio/mpeg", "source mime survives bridge to native decoder");
    Test(grant.AudioUrl == "https://api.celikom.example" + audio, "exact HTTPS signed URL");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio.Replace("&sid=7", ""),
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "W68 legacy sid-less audio grants rejected before native SDK");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio + "&sid=8",
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "duplicate sid rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix + 1, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "mismatched expiry rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "text/html" }), "123", origin, now) == null,
        "unsupported audio rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = false }), "123", origin, now) == null,
        "missing track returns original");
    Test(!GrantValidator.IsTrackId("123:42"), "no fuzzy album ID");
    Test(!GrantValidator.IsTrackId("01"), "no ambiguous leading zeros");
    // W64: Only validate audio locally BEFORE a multipart request can begin.
    // Deterministic 128kbps 44.1kHz MPEG1 Layer III frames, no real music.
    var frames = new byte[417 * 90];
    for (var i = 0; i < 90; i++)
    {
        var at = i * 417;
        frames[at] = 0xff; frames[at + 1] = 0xfb;
        frames[at + 2] = 0x90; frames[at + 3] = 0x64;
    }
    var duration = AudioPreflight.Mp3DurationMs(frames);
    Test(duration is > 2300 and < 2400, "MP3 frames determine actual duration");
    var testAudio = Path.Combine(folder, "wrong_artist_wrong_song.mp3");
    Directory.CreateDirectory(folder);
    await File.WriteAllBytesAsync(testAudio, frames);
    var okDuration = await AudioPreflight.CheckAsync(testAudio, duration);
    Test(!okDuration.Blocked,
        "matching duration permits any filename regardless of title");
    var unicodeAudio = Path.Combine(folder, "中文-💿-неизвестно.mp3");
    File.Copy(testAudio, unicodeAudio);
    var unicodeOk = await AudioPreflight.CheckAsync(unicodeAudio, duration);
    Test(!unicodeOk.Blocked, "unicode filenames cannot trigger name-based rejection");
    File.Delete(unicodeAudio);
    var wrongDuration = await AudioPreflight.CheckAsync(testAudio, 223000);
    Test(wrongDuration.Blocked && wrongDuration.DurationMessage.Contains("Допуск подмены"),
        "large duration mismatch is rejected BEFORE any upload");
    var unknownOriginal = await AudioPreflight.CheckAsync(testAudio, null);
    Test(unknownOriginal.Blocked, "unverified original duration fails closed");
    var invalidAudio = Path.Combine(folder, "fake.mp3");
    await File.WriteAllBytesAsync(invalidAudio, new byte[2048]);
    var fake = await AudioPreflight.CheckAsync(invalidAudio, 2350);
    Test(fake.Blocked && fake.DurationMs == null,
        "fake MP3 is rejected locally (not just filename validation)");
    File.Delete(testAudio);
    File.Delete(invalidAudio);


    // GitHub Windows installer workflow injects the built ZIP after Inno Setup.
    var zipFixture = Environment.GetEnvironmentVariable("CELIKOM_UPDATE_TEST_PACKAGE");
    if (!string.IsNullOrWhiteSpace(zipFixture))
    {
        var staged = AppUpdateManager.Stage(zipFixture, new Version(0, 24, 16, 0));
        Test(staged.Version == new Version(0, 24, 18, 0),
            "ZIP one-click updater accepts new CELIKOM version");
        Test(Path.GetFileName(staged.Path).StartsWith("CELIKOM-W70-",StringComparison.Ordinal),
            "ZIP extraction stages only CELIKOM installer");
        bool oldRejected = false;
        try { AppUpdateManager.Stage(zipFixture, AppUpdateManager.RunningVersion); }
        catch (IOException e) when (e.Message == "UPDATE_NOT_NEWER") { oldRejected = true; }
        Test(oldRejected, "update button rejects already-installed version");
        Test(!File.Exists(Path.Combine(AppUpdateManager.RunningVersion.ToString(), "fake")),
            "upgrade acceptance never modifies Yandex");
    }
        var expectedAccess = new string('b', 64);
    var expectedRefresh = new string('c', 64);
    var backendCalls = new List<string>();
    using var api = new CelikomApi(store, new FakeHandler(request =>
    {
        var path = request.RequestUri!.AbsolutePath;
        backendCalls.Add(path);
        if (path == "/api/v1/auth/login")
            return JsonResponse(new { user = new { id = 1, email = "test@example.com", status = "active" },
                access_token = expectedAccess, refresh_token = expectedRefresh, expires_in = 900 });
        if (path == "/api/v1/auth/activate")
        {
            Test(request.Method == HttpMethod.Post &&
                request.Headers.Authorization?.Parameter == expectedAccess,
                "W68 trial activation uses POST with current user bearer");
            return JsonResponse(new { ok = true, trial = new { activated = true, trial_seconds = 259200 },
                entitlement = new { allowed = true, source = "trial",
                    valid_until = now.AddDays(3).ToString("O"), reason = "trial_active" } });
        }
        if (path == "/api/v1/entitlement")
            return JsonResponse(new { allowed = true, source = "promo",
                valid_until = (string?)null, reason = "promo_lifetime" });
        if (path == "/api/v1/promos/redeem")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "promo uses CELIKOM bearer only");
            return JsonResponse(new { revoked = false, already_activated = false,
                entitlement = new { allowed = true, source = "promo",
                    valid_until = (string?)null, reason = "promo_lifetime" } });
        }
        if (path == "/api/v1/support")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "support uses CELIKOM bearer only");
            var content = request.Content!.ReadAsStringAsync().GetAwaiter().GetResult();
            Test(!content.Contains("refresh_token") && !content.Contains("access_token"),
                "support does not leak tokens");
            using var payload = JsonDocument.Parse(content);
            var body = payload.RootElement;
            Test(body.GetProperty("request_key").GetString()!.Length == 36,
                "support idempotent request key");
            if (body.GetProperty("kind").GetString() == "song")
            {
                if (body.GetProperty("report").GetProperty("diagnostics")
                    .TryGetProperty("windows", out var songWindows) &&
                    songWindows.ValueKind == JsonValueKind.Object)
                    Test(songWindows.GetProperty("platform").GetString() == "windows" &&
                         songWindows.GetProperty("events").ValueKind == JsonValueKind.Array,
                         "W70 song ticket automatically carries bounded Windows diagnostic payload");
                Test(body.GetProperty("report").GetProperty("category").GetString() == "audio_issue",
                    "song report category matches extension");
                Test(body.GetProperty("report").GetProperty("track").GetProperty("id").GetString() == "144530503",
                    "only exact owner track ID reported");
            }
            else if (body.TryGetProperty("diagnostics", out var generalWindows) &&
                     generalWindows.ValueKind == JsonValueKind.Object)
            {
                Test(generalWindows.GetProperty("platform").GetString() == "windows" &&
                     generalWindows.GetProperty("scopeSeconds").GetInt32() == 900,
                     "W70 general ticket automatically carries bounded diagnostics");
            }
            return JsonResponse(new { ticket_id = 3 });
        }
        if (path == "/api/v1/auth/me")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "diagnostic permission asks server using CELIKOM authorization");
            return JsonResponse(new { user = new { id = 1, email = "test@example.com", status = "active" } });
        }
        if (path == "/api/v1/resolve")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "backend receives own CELIKOM session only");
            Test(request.RequestUri.Query.Contains("track_id=123"), "exact track ID query");
            return JsonResponse(new { found = true, audio_url = audio,
                expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" });
        }
        if (path == "/api/v1/auth/logout") return JsonResponse(new { ok = true });
        return JsonResponse(new { error = "not_found" }, 404);
    }));

    await api.LoginAsync("https://api.celikom.example", "test@example.com", "own_password");
    Test(api.IsLoggedIn, "CELIKOM auth session accepted");
    Test(api.Email == "test@example.com", "account displayed");
    Test(store.LoadOrCreate().RefreshToken == expectedRefresh, "session retained through DPAPI");
    var authenticatedBridgeToken = store.LoadOrCreate().BridgeToken;
    Test(authenticatedBridgeToken != first.BridgeToken,
        "sign-in rotates prior add-on bridge capability");
    var resolved = await api.ResolveAsync("123", CancellationToken.None);
    Test(resolved?.AudioUrl == "https://api.celikom.example" + audio, "live-contract resolve mapping");
    Test(backendCalls.SequenceEqual(new [] { "/api/v1/auth/login", "/api/v1/resolve" }),
        "only expected private backend endpoints");
    // W68 launch gate: trial begins on explicit first Start, never on login,
    // preview, or local session load. The server is the only clock/authority.
    var beforeTrialCalls = backendCalls.Count;
    var started = await api.ActivatePlaybackAsync();
    Test(backendCalls.Count == beforeTrialCalls + 1 &&
        backendCalls[^1] == "/api/v1/auth/activate",
        "W68 explicit server trial activation, not local timestamp");
    Test(PlaybackEntitlement.Allowed(started, now),
        "W68 active 72h trial accepted only after server response");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "trial", valid_until = now.AddSeconds(-1).ToString("O"),
        reason = "trial_active" }), now), "W68 expired trial blocked");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = false,
        source = "subscription", valid_until = now.AddDays(10).ToString("O"),
        reason = "subscription_inactive" }), now), "W68 unpaid account blocked");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "subscription", valid_until = (string?)null,
        reason = "subscription_active" }), now), "W68 malformed forever subscription denied");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "none", valid_until = (string?)null,
        reason = "trial_not_started" }), now), "W68 unknown perpetual source denied");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = false,
        source = "trial", valid_until = now.AddHours(10).ToString("O"),
        reason = "service_incident" }), now), "W68 incident not marked active");
    Test(PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "promo", valid_until = (string?)null,
        reason = "promo_active" }), now), "W68 genuine lifetime promo accepted");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "trial", valid_until = "invalid-date", reason = "trial_active" }), now),
        "W68 unparseable expiry fails closed");
    var accessPreview = await api.GetEntitlementAsync();
    Test(accessPreview.GetProperty("source").GetString() == "promo" &&
         accessPreview.GetProperty("valid_until").ValueKind == JsonValueKind.Null,
        "W62 lifetime promo access is server-backed (not hardcoded)");
    var redeemed = await api.RedeemPromoAsync("TESTPROMO123");
    Test(redeemed.GetProperty("entitlement").GetProperty("allowed").GetBoolean(),
        "W62 promo redeems via existing service");
    var automaticDiagnostics = DiagnosticLog.ExportSupportSnapshot(
        "5.126.1.0", "ACTIVE", true, true, "0.24.18", true, "144530503");
    var support = await api.SendSupportAsync("Проверка поддержки", Guid.NewGuid(),
        diagnostics: automaticDiagnostics);
    Test(support.GetProperty("ticket_id").GetInt32() == 3, "W62 general support real API");
    var songSupport = await api.SendSongSupportAsync("Звук прерывается", Guid.NewGuid(),
        "144530503", "audio_issue", true, true,
        windowsDiagnostics: automaticDiagnostics);
    Test(songSupport.GetProperty("ticket_id").GetInt32() == 3,
        "W62 typed song support real API");
    Test(!await api.CanExportDiagnosticsAsync(),
        "regular active user cannot export owner diagnostics");
    Test(backendCalls[^1] == "/api/v1/auth/me",
        "diagnostics access revalidates server user, not UI email alone");

    await using (var bridge = new BridgeServer(api, store))
    {
        await bridge.StartAsync();
        using var http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:21471") };
        async Task<HttpResponseMessage> Request(string route, HttpMethod method,
            object? body = null, string? token = null, string originHeader = "https://addon-1024.pulsesync.invalid")
        {
            using var req = new HttpRequestMessage(method, route);
            req.Headers.TryAddWithoutValidation("Origin", originHeader);
            if (token != null) req.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
            if (body != null) req.Content = JsonContent.Create(body);
            return await http.SendAsync(req);
        }
        using (var bad = await Request("/v1/health", HttpMethod.Get,
            originHeader: "https://evil.example"))
            Test(bad.StatusCode == HttpStatusCode.Forbidden, "foreign site blocked");
        using (var bad = await Request("/v1/state", HttpMethod.Get))
            Test(bad.StatusCode == HttpStatusCode.Unauthorized, "unpaired state forbidden");
        using (var preflight = await Request("/v1/state", HttpMethod.Options))
            Test(preflight.StatusCode == HttpStatusCode.NoContent, "CORS preflight");
        using var paired = await Request("/v1/pair", HttpMethod.Post, new { code = bridge.PairCode });
        Test(paired.IsSuccessStatusCode, "one-time code pairs");
        using var pairJson = JsonDocument.Parse(await paired.Content.ReadAsStringAsync());
        var token = pairJson.RootElement.GetProperty("bridgeToken").GetString();
        Test(SessionStore.IsHexToken(token), "isolated bridge token issued");
        bridge.SetEnabled(true);
        foreach (var nativeOrigin in new[] { "null", "musicapplication://desktop" })
        {
            using (var nativePreflight = new HttpRequestMessage(HttpMethod.Options, "/v1/state"))
            {
                nativePreflight.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                nativePreflight.Headers.TryAddWithoutValidation(
                    "Access-Control-Request-Headers", "x-celikom-bridge-token, x-celikom-native-host");
                using var response = await http.SendAsync(nativePreflight);
                Test(response.StatusCode == HttpStatusCode.NoContent,
                    "native custom-protocol preflight permitted");
                Test(response.Headers.GetValues("Access-Control-Allow-Origin").Single() == nativeOrigin,
                    "native preflight scoped to actual origin");
            }
            using (var nativeState = new HttpRequestMessage(HttpMethod.Get, "/v1/state"))
            {
                nativeState.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                nativeState.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
                nativeState.Headers.TryAddWithoutValidation("X-Celikom-Native-Host", "1");
                using var response = await http.SendAsync(nativeState);
                Test(response.IsSuccessStatusCode, "native Yandex renderer reads authorized state");
            }
            using (var foreign = new HttpRequestMessage(HttpMethod.Get, "/v1/state"))
            {
                foreign.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                foreign.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
                using var response = await http.SendAsync(foreign);
                Test(response.StatusCode == HttpStatusCode.Forbidden,
                    "opaque-origin request without native marker refused");
            }
        }
        using (var state = await Request("/v1/state", HttpMethod.Get, token: token))
        {
            Test(state.IsSuccessStatusCode, "paired can read state");
            var body = await state.Content.ReadAsStringAsync();
            Test(body.Contains("\"enabled\":true"), "start action reaches addon");
            Test(!body.Contains(expectedAccess), "no CELIKOM access token leaked");
            Test(!body.Contains(expectedRefresh), "no CELIKOM refresh token leaked");
        }
        using (var response = await Request("/v1/resolve?track_id=123", HttpMethod.Get, token: token))
        {
            var json = await response.Content.ReadAsStringAsync();
            Test(response.IsSuccessStatusCode && json.Contains("https://api.celikom.example"),
                "paired route emits authorized signed media");
            Test(!json.Contains(expectedAccess) && !json.Contains(expectedRefresh),
                "audio grant never exposes API credentials");
        }
        bridge.SetEnabled(false);
        using (var response = await Request("/v1/resolve?track_id=123", HttpMethod.Get, token: token))
            Test((await response.Content.ReadAsStringAsync()).Contains("\"found\":false"),
                "stop disables future source replacement");
    }

    await api.LogoutAsync();
    Test(!api.IsLoggedIn, "only Windows CELIKOM session logged out");
    Test(store.LoadOrCreate().RefreshToken == "", "local refresh token cleared");
    Test(store.LoadOrCreate().BridgeToken != authenticatedBridgeToken,
        "logout invalidates old add-on pairing without touching Yandex account");
    var safeTimestamp = "2026-11-09T17:06:00.000Z";
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|SOURCE_MAPPED|track=123"),
        "safe numeric track event passes export");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|SOURCE_MAPPED|track=123?token=SECRET"),
        "signed URL cannot appear in diagnostic event");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|LOGIN_EMAIL=test@example.com"),
        "email cannot appear in diagnostic event");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=139"),
        "W53 native resource id survives export allowlist");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=139"),
        "W53 typed 403 event survives export allowlist");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_URL_QUERY_CHANGED|resource_id=89"),
        "W53 signed URL mismatch classification survives export");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_URL_MATCH|resource_id=139?token=SECRET"),
        "W53 rejects URLs and query leakage in signed request log");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_403_HTML|resource_id=139|token=secret"),
        "W53 rejects extra log fields");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=0139"),
        "W53 rejects ambiguous leading-zero resource IDs");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=139\nSECRET"),
        "W53 rejects multiline log injection");
    var fixtureLogsDirectory = Path.Combine(folder, "owner-export-isolated");
    var nativeFixture = Path.Combine(fixtureLogsDirectory, "native-events.log");
    Directory.CreateDirectory(fixtureLogsDirectory);
    var when = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
        System.Globalization.CultureInfo.InvariantCulture);
    File.AppendAllText(nativeFixture,
        when + "|PLAYER_NET_REQUEST|resource_id=739209\n" +
        when + "|PLAYER_NET_HTTP_FORBIDDEN|resource_id=739209\n" +
        when + "|PLAYER_URL_QUERY_CHANGED|resource_id=739209\n" +
        when + "|PLAYER_URL_SIGNED_FIELDS_INTACT|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=739209\n" +
        when + "|PLAYER_403_HTML|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_ACCESS_DENIED|resource_id=739209\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209?token=SENSITIVE\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209|sid=SENSITIVE\n");
    File.AppendAllText(Path.Combine(fixtureLogsDirectory, "companion-events.log"),
        when + "|OWNER_DIAG_TEST|track=123\n");
    DiagnosticLog.Record("OWNER_DIAG_TEST", "123");
    var snapshot = DiagnosticLog.ExportText("5.126.1.0", "ACTIVE", true, true, true,
        diagnosticDirectory: fixtureLogsDirectory);
    Test(snapshot.Contains("OWNER_DIAG_TEST|track=123"), "diagnostic export has observed event");
    Test(snapshot.Contains("DiagnosticScope=LAST_15_MINUTES"), "recent sessions only");
    Test(snapshot.Contains("ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING"),
        "successful MP3 probe never implies audio replacement");
    Test(snapshot.Contains("CodeBaseline=W53_NATIVE_403_CLASSIFICATION_EXPORT_SAFE"), "W53 truthful diagnostics baseline");
    Test(snapshot.Contains("PLAYER_URL_QUERY_CHANGED|resource_id=739209"),
        "W53 native URL mismatch reaches actual exported TXT");
    Test(snapshot.Contains("PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=739209"),
        "W53 real PHP denial category reaches owner export");
    Test(snapshot.Contains("NativeAudio403Observed=true") &&
         snapshot.Contains("PlayerNetworkRequestObserved=true") &&
         snapshot.Contains("NativeMediaUrlQueryMismatchObserved=true") &&
         snapshot.Contains("NativeMediaUrlSignedFieldsIntactObserved=true") &&
         snapshot.Contains("Native403PhpSignatureRejectionObserved=true") &&
         snapshot.Contains("Native403PhpAccessDenialObserved=true") &&
         snapshot.Contains("Native403HtmlResponseObserved=true"),
        "W53 owner summary correctly reflects native resource events");
    Test(!snapshot.Contains("SENSITIVE"),"W53 malformed native lines cannot leak signed query or sid");
    var auto = DiagnosticLog.ExportSupportSnapshot("5.126.1.0","ACTIVE", true, true,
        "0.24.18", true, "123", fixtureLogsDirectory);
    var autoJson = JsonSerializer.Serialize(auto);
    using (var parsedAuto = JsonDocument.Parse(autoJson))
    {
        var root = parsedAuto.RootElement;
        Test(root.GetProperty("platform").GetString() == "windows" &&
            root.GetProperty("scopeSeconds").GetInt32() == 900,
            "W70 auto-attachment includes version, bounded scope and platform");
        var events = root.GetProperty("events");
        Test(events.GetArrayLength() <= 64 &&
             events.EnumerateArray().Any(x => x.GetProperty("code").GetString() ==
                "PLAYER_NET_HTTP_FORBIDDEN" &&
                x.GetProperty("resourceId").GetString() == "739209"),
             "W70 auto-support includes recent error and safe numeric resource id");
    }
    Test(!autoJson.Contains("SENSITIVE") && !autoJson.Contains("token=") &&
         !autoJson.Contains("test@example.com") && !autoJson.Contains("sid="),
         "W70 automatic customer attachment is free of tokens, email and signed URLs");
    Test(snapshot.Contains("EngineFastPauseObserved=") &&
        snapshot.Contains("PlayerAudibleEventObserved=") &&
        snapshot.Contains("DecoderErrorObserved="), "typed owner playback evidence summary");
    Test(snapshot.Contains("PlayerNetworkRequestObserved=") &&
        snapshot.Contains("PlayerNetworkCorsFailureObserved=") &&
        snapshot.Contains("FastPauseTrackAttribution=NOT_AVAILABLE_WITHOUT_PLAYER_TRACK_ID"),
        "real Yandex network evidence remains distinct from playable audio");
    Test(!snapshot.Contains("yandex-drm") && !snapshot.Contains("token="),
        "owner export never leaks native crypto or signed URLs");
    Test(!snapshot.Contains(expectedAccess) && !snapshot.Contains(expectedRefresh) &&
        !snapshot.Contains("test@example.com"), "diagnostics exclude credentials and email");
    Console.WriteLine("W15_NATIVE_CONTRACT_PASS " + checks);
}
finally
{
    if (Directory.Exists(folder)) Directory.Delete(folder, true);
}

static HttpResponseMessage JsonResponse(object value, int status = 200) =>
    new((HttpStatusCode)status) { Content = JsonContent.Create(value) };

sealed class FakeHandler(Func<HttpRequestMessage, HttpResponseMessage> reply) : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken cancellationToken) =>
        Task.FromResult(reply(request));
}
