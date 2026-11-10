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

    public void Dispose() { _http.Dispose(); _refreshLock.Dispose(); }
}
