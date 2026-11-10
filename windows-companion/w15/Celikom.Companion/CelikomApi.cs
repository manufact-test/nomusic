using System.Net;
using System.Security.Cryptography;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text;

namespace Celikom.Companion;

public sealed class ApiFailure(int code, string category) : Exception(category)
{
    public int HttpStatus { get; } = code;
    public string Category { get; } = category;
}

/// <summary>Own CELIKOM login/refresh; never reads Yandex or browser sessions.</summary>
public sealed class CelikomApi : IDisposable
{
    private readonly HttpClient _http;
    private readonly SessionStore _store;
    private readonly SemaphoreSlim _refreshLock = new(1, 1);
    private SecretRecord _current;
    private const int MaxJsonBytes = 48 * 1024;

    public CelikomApi(SessionStore store, HttpMessageHandler? handler = null)
    {
        _store = store;
        _current = store.LoadOrCreate();
        _http = handler is null
            ? new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, UseCookies = false })
            : new HttpClient(handler);
        _http.Timeout = TimeSpan.FromSeconds(9);
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("CELIKOM-WindowsCompanion/0.15");
    }

    public SecretRecord Settings => Volatile.Read(ref _current);
    public bool IsLoggedIn =>
        SessionStore.IsHexToken(Settings.AccessToken) && SessionStore.IsHexToken(Settings.RefreshToken);
    public string Origin => Settings.Origin;
    public string Email => Settings.Email;

    // Keep in sync with extension/src/auth/diagnostic-access.ts.
    // The local UI is not an authority: verify active user ID/status/email
    // against the signed-in CELIKOM backend on every diagnostic export.
    private static readonly HashSet<string> DiagnosticIdentityHashes =
        new(StringComparer.Ordinal)
        {
            "18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572",
            "50bc7e488885f21b0af751f8e2ed3bc622d3bc097c6541817c9ef742cdf7777e"
        };

    public async Task<bool> CanExportDiagnosticsAsync(CancellationToken ct = default)
    {
        var session = Settings;
        if (!IsLoggedIn || string.IsNullOrWhiteSpace(session.Origin)) return false;
        JsonElement data;
        var endpoint = new Uri(session.Origin + "/api/v1/auth/me");
        try
        {
            data = await RequestAsync(endpoint, HttpMethod.Get, null, session.AccessToken, ct);
        }
        catch (ApiFailure ex) when (ex.HttpStatus == 401)
        {
            if (!await RefreshOnceAsync(session.AccessToken, ct)) return false;
            var latest = Settings;
            if (!IsLoggedIn || latest.InstallationId != session.InstallationId ||
                latest.Origin != session.Origin || latest.Email != session.Email) return false;
            data = await RequestAsync(endpoint, HttpMethod.Get, null, latest.AccessToken, ct);
        }
        if (!IsLoggedIn || Settings.Email != session.Email ||
            Settings.InstallationId != session.InstallationId ||
            Settings.Origin != session.Origin) return false;
        if (data.ValueKind != JsonValueKind.Object ||
            !data.TryGetProperty("user", out var user) ||
            user.ValueKind != JsonValueKind.Object ||
            !user.TryGetProperty("id", out var id) ||
            !id.TryGetInt64(out var userId) || userId < 1 ||
            !user.TryGetProperty("status", out var status) ||
            status.GetString() != "active" ||
            !user.TryGetProperty("email", out var emailValue) ||
            emailValue.ValueKind != JsonValueKind.String) return false;
        var email = emailValue.GetString()?.Trim().ToLowerInvariant() ?? "";
        if (!string.Equals(email, session.Email.Trim(), StringComparison.OrdinalIgnoreCase)) return false;
        var digest = Convert.ToHexString(
            SHA256.HashData(Encoding.UTF8.GetBytes(email))).ToLowerInvariant();
        return DiagnosticIdentityHashes.Contains(digest);
    }

    public async Task LoginAsync(string origin, string email, string password, CancellationToken ct = default)
    {
        var normalized = GrantValidator.NormalizeOrigin(origin).GetLeftPart(UriPartial.Authority);
        if (string.IsNullOrWhiteSpace(email) || password.Length == 0 || password.Length > 512)
            throw new ApiFailure(400, "INVALID_CREDENTIALS");
        var previous = Settings;
        var response = await RequestAsync(
            new Uri(normalized + "/api/v1/auth/login"), HttpMethod.Post,
            new { email = email.Trim(), password, installation_id = previous.InstallationId }, null, ct);
        var tokens = ReadTokens(response);
        if (tokens is null) throw new ApiFailure(403, "EMAIL_VERIFICATION_REQUIRED");
        var next = previous with
        {
            Origin = normalized,
            Email = tokens.Value.email,
            AccessToken = tokens.Value.access,
            RefreshToken = tokens.Value.refresh,
            // A prior SDK pairing must not gain access to a newly signed-in account.
            BridgeToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant()
        };
        _store.Save(next);
        Volatile.Write(ref _current, next);
    }

    public async Task LogoutAsync(CancellationToken ct = default)
    {
        var previous = Settings;
        var cleaned = previous with
        {
            Email = "", AccessToken = "", RefreshToken = "",
            BridgeToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant()
        };
        Volatile.Write(ref _current, cleaned);
        _store.Save(cleaned);
        if (!SessionStore.IsHexToken(previous.RefreshToken) || previous.Origin.Length == 0) return;
        try
        {
            await RequestAsync(
                new Uri(previous.Origin + "/api/v1/auth/logout"), HttpMethod.Post,
                new { refresh_token = previous.RefreshToken, installation_id = previous.InstallationId }, null, ct);
        }
        catch { /* Local logout must work offline. Never retry an old refresh. */ }
    }

    public async Task<SourceGrant?> ResolveAsync(string id, CancellationToken ct)
    {
        if (!GrantValidator.IsTrackId(id) || !IsLoggedIn) return null;
        var session = Settings;
        Uri origin;
        try { origin = GrantValidator.NormalizeOrigin(session.Origin); }
        catch { return null; }
        var target = new Uri(origin,
            "/api/v1/resolve?service=yandex&track_id=" + Uri.EscapeDataString(id) + "&audio_formats=mp3,m4a");
        JsonElement result;
        try
        {
            result = await RequestAsync(target, HttpMethod.Get, null, session.AccessToken, ct);
        }
        catch (ApiFailure ex) when (ex.HttpStatus == 401)
        {
            if (!await RefreshOnceAsync(session.AccessToken, ct)) return null;
            var newer = Settings;
            if (!IsLoggedIn || newer.InstallationId != session.InstallationId ||
                newer.Origin != session.Origin) return null;
            result = await RequestAsync(target, HttpMethod.Get, null, newer.AccessToken, ct);
        }
        if (Settings.Origin != session.Origin || !IsLoggedIn) return null;
        return GrantValidator.FromResolve(result, id, origin, DateTimeOffset.UtcNow);
    }

    private async Task<bool> RefreshOnceAsync(string failedAccess, CancellationToken ct)
    {
        await _refreshLock.WaitAsync(ct);
        try
        {
            var session = Settings;
            if (!SessionStore.IsHexToken(session.RefreshToken)) return false;
            if (session.AccessToken != failedAccess) return true; // another request rotated it
            JsonElement response;
            try
            {
                response = await RequestAsync(
                    new Uri(session.Origin + "/api/v1/auth/refresh"), HttpMethod.Post,
                    new { refresh_token = session.RefreshToken, installation_id = session.InstallationId }, null, ct);
            }
            catch (ApiFailure ex) when (ex.HttpStatus is 401 or 403)
            {
                return false;
            }
            var tokens = ReadTokens(response);
            if (tokens is null) return false;
            var updated = session with
            {
                Email = tokens.Value.email,
                AccessToken = tokens.Value.access,
                RefreshToken = tokens.Value.refresh
            };
            // Persist the new refresh token BEFORE subsequent requests can use it.
            _store.Save(updated);
            Volatile.Write(ref _current, updated);
            return true;
        }
        finally { _refreshLock.Release(); }
    }

    private static (string email, string access, string refresh)? ReadTokens(JsonElement response)
    {
        if (response.ValueKind != JsonValueKind.Object ||
            !response.TryGetProperty("access_token", out var a) ||
            !response.TryGetProperty("refresh_token", out var r) ||
            !response.TryGetProperty("user", out var u) ||
            u.ValueKind != JsonValueKind.Object ||
            !u.TryGetProperty("email", out var e) ||
            a.ValueKind != JsonValueKind.String || r.ValueKind != JsonValueKind.String ||
            e.ValueKind != JsonValueKind.String) return null;
        var access = a.GetString() ?? "";
        var refresh = r.GetString() ?? "";
        var email = e.GetString() ?? "";
        return SessionStore.IsHexToken(access) && SessionStore.IsHexToken(refresh) &&
               email.Length is > 3 and < 255 ? (email, access, refresh) : null;
    }

    private async Task<JsonElement> RequestAsync(Uri endpoint, HttpMethod method,
        object? body, string? access, CancellationToken ct)
    {
        using var request = new HttpRequestMessage(method, endpoint);
        if (access is { Length: 64 }) request.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", access);
        if (body != null) request.Content = JsonContent.Create(body);
        using var response = await _http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
        if ((int)response.StatusCode is >= 300 and < 400)
            throw new ApiFailure((int)response.StatusCode, "REDIRECT_FORBIDDEN");
        if (response.Content.Headers.ContentLength is > MaxJsonBytes)
            throw new ApiFailure(0, "RESPONSE_TOO_LARGE");
        using var stream = await response.Content.ReadAsStreamAsync(ct);
        using var memory = new MemoryStream();
        var buffer = new byte[4096];
        while (true)
        {
            var count = await stream.ReadAsync(buffer.AsMemory(), ct);
            if (count == 0) break;
            if (memory.Length + count > MaxJsonBytes)
                throw new ApiFailure(0, "RESPONSE_TOO_LARGE");
            memory.Write(buffer, 0, count);
        }
        JsonElement element;
        try
        {
            using var doc = JsonDocument.Parse(memory.ToArray());
            element = doc.RootElement.Clone();
        }
        catch (JsonException) { throw new ApiFailure(0, "INVALID_API_JSON"); }
        if (!response.IsSuccessStatusCode)
        {
            string category = "API_ERROR";
            if (element.ValueKind == JsonValueKind.Object &&
                element.TryGetProperty("error", out var err) &&
                err.ValueKind == JsonValueKind.String)
                category = (err.GetString() ?? "API_ERROR") switch
                {
                    "invalid_credentials" => "INVALID_CREDENTIALS",
                    "invalid_session" => "INVALID_SESSION",
                    "access_denied" => "ACCESS_DENIED",
                    "rate_limited" => "RATE_LIMITED",
                    "email_unverified" => "EMAIL_VERIFICATION_REQUIRED",
                    _ => "API_ERROR"
                };
            throw new ApiFailure((int)response.StatusCode, category);
        }
        return element;
    }

    // The popup uses the SAME CELIKOM endpoints as the browser extension.
    // UI previews never authorize playback; ResolveAsync is still the authority.
    private async Task<JsonElement> SignedRequestAsync(string route, HttpMethod method,
        object? body = null, CancellationToken ct = default)
    {
        var session = Settings;
        if (!IsLoggedIn) throw new ApiFailure(401, "INVALID_SESSION");
        var target = new Uri(session.Origin + "/api/v1/" + route);
        try { return await RequestAsync(target, method, body, session.AccessToken, ct); }
        catch (ApiFailure ex) when (ex.HttpStatus == 401)
        {
            if (!await RefreshOnceAsync(session.AccessToken, ct))
                throw new ApiFailure(401, "INVALID_SESSION");
            var current = Settings;
            if (!IsLoggedIn || current.Origin != session.Origin ||
                current.InstallationId != session.InstallationId ||
                current.Email != session.Email)
                throw new ApiFailure(401, "INVALID_SESSION");
            // Repeat only idempotent reads; never replay promo/support writes.
            // POST auth/activate is idempotent in MySQL. A 401 means the
            // expired access token could not start the trial; after rotating
            // the refresh token it is safe to retry this specific operation.
            // NEVER blindly replay promo, upload or support writes.
            if (method != HttpMethod.Get && !(route == "auth/activate" && method == HttpMethod.Post))
                throw new ApiFailure(401, "INVALID_SESSION");
            return await RequestAsync(target, method, body, current.AccessToken, ct);
        }
    }

    // Mirrors extension benefits-popup.ts: no referral code is created just
    // by opening the account. Only an explicit button performs the POST.
    public Task<JsonElement> GetReferralsAsync(CancellationToken ct = default) =>
        SignedRequestAsync("referrals", HttpMethod.Get, ct: ct);

    public Task<JsonElement> GetRewardsAsync(CancellationToken ct = default) =>
        SignedRequestAsync("rewards", HttpMethod.Get, ct: ct);

    public Task<JsonElement> CreateReferralCodeAsync(CancellationToken ct = default) =>
        SignedRequestAsync("referrals/code", HttpMethod.Post, new { }, ct);


    public Task<JsonElement> GetEntitlementAsync(CancellationToken ct = default) =>
        SignedRequestAsync("entitlement", HttpMethod.Get, ct: ct);

    // Same explicit first-Start transaction as the browser extension.
    // Merely logging in, installing, showing the account or checking the
    // entitlement preview must NEVER start a trial.
    public async Task<JsonElement> ActivatePlaybackAsync(CancellationToken ct = default)
    {
        var response = await SignedRequestAsync("auth/activate", HttpMethod.Post, new { }, ct);
        if (response.ValueKind != JsonValueKind.Object ||
            !response.TryGetProperty("entitlement", out var entitlement) ||
            entitlement.ValueKind != JsonValueKind.Object)
            throw new ApiFailure(502, "ENTITLEMENT_REQUIRED");
        return entitlement.Clone();
    }

    public Task<JsonElement> RedeemPromoAsync(string rawCode, CancellationToken ct = default)
    {
        var code = rawCode.Trim();
        if (code.Length is < 8 or > 64 ||
            !System.Text.RegularExpressions.Regex.IsMatch(code, "^[A-Za-z0-9_-]+$"))
            throw new ApiFailure(400, "INVALID_PROMO");
        return SignedRequestAsync("promos/redeem", HttpMethod.Post, new { code }, ct);
    }

    public Task<JsonElement> SendSupportAsync(string message, Guid requestKey,
        CancellationToken ct = default)
    {
        if (message.Trim().Length is < 3 or > 2000)
            throw new ApiFailure(400, "INVALID_REQUEST");
        return SignedRequestAsync("support", HttpMethod.Post,
            new { message = message.Trim(), request_key = requestKey.ToString("D"), kind = "general" }, ct);
    }

    // Same typed server SongReport contract as extension/src/popup/song-report.ts.
    // Only the current exact Yandex ID and observed bridge booleans are sent.
    public Task<JsonElement> SendSongSupportAsync(string message, Guid requestKey,
        string trackId, string category, bool bridgeStarted, bool enabled,
        CancellationToken ct = default)
    {
        if (!GrantValidator.IsTrackId(trackId) ||
            category is not ("not_replacing" or "wrong_version" or "audio_issue" or "other") ||
            message.Trim().Length > 2000)
            throw new ApiFailure(400, "INVALID_REQUEST");
        var report = new
        {
            category,
            version = AppUpdateManager.RunningVersion.ToString(3),
            track = new { id = trackId, title = "", artist = "", album = "" },
            diagnostics = new { enabled, bridgeReady = bridgeStarted }
        };
        return SignedRequestAsync("support", HttpMethod.Post,
            new { message = message.Trim(), request_key = requestKey.ToString("D"),
                  kind = "song", report }, ct);
    }

    public async Task<JsonElement> RegisterAsync(string origin, string email, string password,
        CancellationToken ct = default)
    {
        var normalized = GrantValidator.NormalizeOrigin(origin).GetLeftPart(UriPartial.Authority);
        return await RequestAsync(new Uri(normalized + "/api/v1/auth/register"),
            HttpMethod.Post, new { email = email.Trim(), password,
                installation_id = Settings.InstallationId }, null, ct);
    }

    public async Task VerifyEmailAsync(string origin, string email, string code,
        CancellationToken ct = default)
    {
        if (!System.Text.RegularExpressions.Regex.IsMatch(code.Trim(), "^[0-9]{6}$"))
            throw new ApiFailure(400, "INVALID_CODE");
        var normalized = GrantValidator.NormalizeOrigin(origin).GetLeftPart(UriPartial.Authority);
        var previous = Settings;
        var result = await RequestAsync(new Uri(normalized + "/api/v1/auth/verify-email"),
            HttpMethod.Post,
            new { email = email.Trim(), code = code.Trim(),
                installation_id = previous.InstallationId }, null, ct);
        var tokens = ReadTokens(result);
        if (tokens is null) throw new ApiFailure(403, "EMAIL_VERIFICATION_REQUIRED");
        var next = previous with
        {
            Origin = normalized, Email = tokens.Value.email,
            AccessToken = tokens.Value.access, RefreshToken = tokens.Value.refresh,
            BridgeToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant()
        };
        _store.Save(next);
        Volatile.Write(ref _current, next);
    }

    public async Task RequestPasswordResetAsync(string email, CancellationToken ct = default)
    {
        await RequestAsync(new Uri(GrantValidator.NormalizeOrigin(
            Settings.Origin.Length > 0 ? Settings.Origin :
                "https://darkred-camel-588676.hostingersite.com") + "api/v1/auth/request-reset"),
            HttpMethod.Post, new { email = email.Trim() }, null, ct);
    }

    public async Task ResetPasswordAsync(string email, string code, string newPassword,
        CancellationToken ct = default)
    {
        await RequestAsync(new Uri(GrantValidator.NormalizeOrigin(
            Settings.Origin.Length > 0 ? Settings.Origin :
                "https://darkred-camel-588676.hostingersite.com") + "api/v1/auth/reset-password"),
            HttpMethod.Post,
            new { email = email.Trim(), code = code.Trim(), new_password = newPassword }, null, ct);
    }

    public Task<JsonElement> GetConfigAsync(CancellationToken ct = default)
    {
        var origin = Settings.Origin.Length != 0 ? Settings.Origin :
            "https://darkred-camel-588676.hostingersite.com";
        return RequestAsync(new Uri(origin + "/api/v1/config"),
            HttpMethod.Get, null, null, ct);
    }

    public Task<JsonElement> GetTrackVersionStatusAsync(string id, CancellationToken ct = default)
    {
        if (!GrantValidator.IsTrackId(id)) throw new ApiFailure(400, "INVALID_TRACK");
        return SignedRequestAsync("tracks/version-status?service=yandex&track_id=" + id,
            HttpMethod.Get, ct: ct);
    }

    // The real server requires multipart/form-data. A POST must NOT be retried
    // automatically on 401/timeouts: its result could already have committed.
    private async Task<JsonElement> SendContributionAsync(string route, string trackId,
        Dictionary<string,string> fields, string? audioFile, CancellationToken ct,
        IProgress<int>? progress = null)
    {
        if (!GrantValidator.IsTrackId(trackId) || !IsLoggedIn)
            throw new ApiFailure(401, "INVALID_SESSION");
        var auth = Settings;
        using var http = new HttpClient(new HttpClientHandler
            { AllowAutoRedirect = false, UseCookies = false })
            { Timeout = TimeSpan.FromMinutes(2) };
        using var form = new MultipartFormDataContent();
        form.Add(new StringContent("yandex"), "service");
        form.Add(new StringContent(trackId), "track_id");
        foreach (var (key,value) in fields) form.Add(new StringContent(value), key);
        if (audioFile is not null)
        {
            var info = new FileInfo(audioFile);
            if (!info.Exists || info.Length is < 1024 or > 31_457_280 ||
                !(info.Extension.Equals(".mp3", StringComparison.OrdinalIgnoreCase) ||
                  info.Extension.Equals(".m4a", StringComparison.OrdinalIgnoreCase)))
                throw new ApiFailure(413, "INVALID_FILE");
            var input = new FileStream(audioFile, FileMode.Open, FileAccess.Read,
                FileShare.Read, 81920, FileOptions.Asynchronous);
            var file = new StreamContent(progress is null ? input :
                new ProgressReadStream(input, progress));
            file.Headers.ContentType = new MediaTypeHeaderValue(
                info.Extension.Equals(".m4a", StringComparison.OrdinalIgnoreCase) ?
                    "audio/mp4" : "audio/mpeg");
            form.Add(file, "file", info.Name);
        }
        using var request = new HttpRequestMessage(HttpMethod.Post,
            auth.Origin + "/api/v1/" + route);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", auth.AccessToken);
        request.Content = form;
        using var response = await http.SendAsync(request,
            HttpCompletionOption.ResponseHeadersRead, ct);
        if (Settings.AccessToken != auth.AccessToken || Settings.Origin != auth.Origin)
            throw new ApiFailure(401, "INVALID_SESSION");
        if ((int)response.StatusCode is >= 300 and < 400)
            throw new ApiFailure((int)response.StatusCode, "REDIRECT_FORBIDDEN");
        if (response.Content.Headers.ContentLength > 48_000)
            throw new ApiFailure(0, "RESPONSE_TOO_LARGE");
        var bytes = await response.Content.ReadAsByteArrayAsync(ct);
        if (bytes.Length > 48_000) throw new ApiFailure(0, "RESPONSE_TOO_LARGE");
        JsonElement result;
        try
        {
            using var document = JsonDocument.Parse(bytes);
            result = document.RootElement.Clone();
        }
        catch (JsonException) { throw new ApiFailure(0, "INVALID_API_JSON"); }
        if (!response.IsSuccessStatusCode)
        {
            var error = result.ValueKind == JsonValueKind.Object &&
                result.TryGetProperty("error", out var e) && e.ValueKind == JsonValueKind.String
                ? e.GetString() ?? "CONTRIBUTION_FAILED" : "CONTRIBUTION_FAILED";
            throw new ApiFailure((int)response.StatusCode, error);
        }
        return result;
    }

    public Task<JsonElement> SuggestTrackAsync(string id, string title = "",
        string artist = "", CancellationToken ct = default) =>
        SendContributionAsync("track-requests", id, new Dictionary<string,string>
        {
            ["title"] = SafeMetadata(title),
            ["artist"] = SafeMetadata(artist)
        }, null, ct);

    private static string SafeMetadata(string value) =>
        value is { Length: <= 240 } && !value.Any(char.IsControl) ? value.Trim() : "";

    public Task<JsonElement> UploadTrackAsync(string id, string audioFile, long durationMs,
        string title, string artist, Guid requestKey, IProgress<int>? progress,
        CancellationToken ct = default)
    {
        if (durationMs is < 1000 or > 86_400_000)
            throw new ApiFailure(400, "INVALID_DURATION");
        var fields = new Dictionary<string,string>
        {
            ["declaration"] = "1",
            ["request_id"] = requestKey.ToString("D"),
            ["duration_ms"] = durationMs.ToString(System.Globalization.CultureInfo.InvariantCulture),
            ["title"] = SafeMetadata(title),
            ["artist"] = SafeMetadata(artist),
            ["album"] = ""
        };
        return SendContributionAsync("uploads", id, fields, audioFile, ct, progress);
    }

    public void Dispose() { _http.Dispose(); _refreshLock.Dispose(); }
}
