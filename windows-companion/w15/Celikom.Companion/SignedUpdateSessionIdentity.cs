using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Celikom.Companion;

/// <summary>
/// Read-only identity evidence for an in-place update. Never calls
/// SessionStore.LoadOrCreate(): a fresh DPAPI session must NOT count as
/// preservation of the old account/installation.
/// </summary>
public static class SignedUpdateSessionIdentity
{
    private static string DefaultPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows", "session.dpapi");

    public static SecretRecord? ReadExisting(string? path = null)
    {
        if (!OperatingSystem.IsWindows()) return null;
        try
        {
            var file = path ?? DefaultPath;
            if (!File.Exists(file) ||
                new FileInfo(file).Length is < 32 or > 64_000)
                return null;
            var plain = ProtectedData.Unprotect(File.ReadAllBytes(file), null,
                DataProtectionScope.CurrentUser);
            try
            {
                var record = JsonSerializer.Deserialize<SecretRecord>(plain);
                return record is not null &&
                    Guid.TryParseExact(record.InstallationId, "D", out _) &&
                    SessionStore.IsHexToken(record.BridgeToken)
                        ? record : null;
            }
            finally { CryptographicOperations.ZeroMemory(plain); }
        }
        catch (Exception e) when (e is IOException or CryptographicException or
            JsonException or UnauthorizedAccessException or ArgumentException)
        { return null; }
    }

    /// <summary>
    /// SHA256 identity of the installation and account email, not the
    /// rotating access/refresh tokens. The fingerprint is stored only in
    /// the DPAPI-protected rollback journal. An unexpected fresh session
    /// changes it and blocks false "healthy" claims.
    /// </summary>
    public static string? Fingerprint(SecretRecord? session)
    {
        if (session is null ||
            !Guid.TryParseExact(session.InstallationId, "D", out var id) ||
            !SessionStore.IsHexToken(session.BridgeToken))
            return null;
        var representation = id.ToString("D") + "|" +
            (session.Email ?? "").Trim().ToLowerInvariant();
        var bytes = Encoding.UTF8.GetBytes(representation);
        try { return Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant(); }
        finally { CryptographicOperations.ZeroMemory(bytes); }
    }

    public static string? ReadExistingFingerprint(string? path = null) =>
        Fingerprint(ReadExisting(path));
}
