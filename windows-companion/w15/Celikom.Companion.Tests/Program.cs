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
