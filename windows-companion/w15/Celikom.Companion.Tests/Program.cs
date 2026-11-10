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

    // GitHub Windows installer workflow injects the built ZIP after Inno Setup.
    var zipFixture = Environment.GetEnvironmentVariable("CELIKOM_UPDATE_TEST_PACKAGE");
    if (!string.IsNullOrWhiteSpace(zipFixture))
    {
        var staged = AppUpdateManager.Stage(zipFixture, new Version(0, 24, 3, 0));
        Test(staged.Version == new Version(0, 24, 6, 0),
            "ZIP one-click updater accepts new CELIKOM version");
        Test(Path.GetFileName(staged.Path).StartsWith("CELIKOM-W50-",StringComparison.Ordinal),
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
    var nativeFixture = Path.Combine(DiagnosticLog.DirectoryPath, "native-events.log");
    Directory.CreateDirectory(DiagnosticLog.DirectoryPath);
    var when = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
        System.Globalization.CultureInfo.InvariantCulture);
    File.AppendAllText(nativeFixture,
        when + "|PLAYER_NET_REQUEST|resource_id=739209\n" +
        when + "|PLAYER_NET_HTTP_FORBIDDEN|resource_id=739209\n" +
        when + "|PLAYER_URL_QUERY_CHANGED|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=739209\n" +
        when + "|PLAYER_403_HTML|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_ACCESS_DENIED|resource_id=739209\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209?token=SENSITIVE\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209|sid=SENSITIVE\n");
    DiagnosticLog.Record("OWNER_DIAG_TEST", "123");
    var snapshot = DiagnosticLog.ExportText("5.126.1.0", "ACTIVE", true, true, true);
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
         snapshot.Contains("Native403PhpSignatureRejectionObserved=true") &&
         snapshot.Contains("Native403PhpAccessDenialObserved=true") &&
         snapshot.Contains("Native403HtmlResponseObserved=true"),
        "W53 owner summary correctly reflects native resource events");
    Test(!snapshot.Contains("SENSITIVE"),"W53 malformed native lines cannot leak signed query or sid");
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
