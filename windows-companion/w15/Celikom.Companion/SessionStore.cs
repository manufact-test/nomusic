using System.Security.Cryptography;
using System.Text.Json;

namespace Celikom.Companion;

public sealed record SecretRecord(
    string InstallationId, string Origin, string Email,
    string AccessToken, string RefreshToken, string BridgeToken);

/// <summary>Windows user-bound encrypted storage. Never writes a password.</summary>
public sealed class SessionStore
{
    private readonly string _folder;
    private readonly string _path;

    public SessionStore(string? folder = null)
    {
        _folder = folder ?? Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CELIKOM", "Windows");
        _path = Path.Combine(_folder, "session.dpapi");
    }

    public SecretRecord LoadOrCreate()
    {
        if (File.Exists(_path))
        {
            try
            {
                var ciphertext = File.ReadAllBytes(_path);
                var raw = ProtectedData.Unprotect(ciphertext, null, DataProtectionScope.CurrentUser);
                try
                {
                    var record = JsonSerializer.Deserialize<SecretRecord>(raw);
                    if (record != null &&
                        Guid.TryParseExact(record.InstallationId, "D", out _) &&
                        IsHexToken(record.BridgeToken))
                        return record;
                }
                finally { CryptographicOperations.ZeroMemory(raw); }
            }
            catch (CryptographicException) { throw new InvalidOperationException("LOCAL_SESSION_CANNOT_BE_DECRYPTED"); }
            catch (JsonException) { throw new InvalidOperationException("LOCAL_SESSION_CORRUPTED"); }
        }

        var fresh = new SecretRecord(Guid.NewGuid().ToString("D"), "", "", "", "",
            Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant());
        Save(fresh);
        return fresh;
    }

    public void Save(SecretRecord value)
    {
        if (!Guid.TryParseExact(value.InstallationId, "D", out _) ||
            !IsHexToken(value.BridgeToken)) throw new ArgumentException("Invalid session identity");
        Directory.CreateDirectory(_folder);
        var bytes = JsonSerializer.SerializeToUtf8Bytes(value);
        byte[] encrypted;
        try { encrypted = ProtectedData.Protect(bytes, null, DataProtectionScope.CurrentUser); }
        finally { CryptographicOperations.ZeroMemory(bytes); }
        var temp = Path.Combine(_folder, ".session-" + Guid.NewGuid().ToString("N"));
        try
        {
            File.WriteAllBytes(temp, encrypted);
            File.Move(temp, _path, true);
        }
        finally { if (File.Exists(temp)) File.Delete(temp); }
    }

    public static bool IsHexToken(string? value) =>
        value is { Length: 64 } && value.All(ch =>
            ch is >= '0' and <= '9' or >= 'a' and <= 'f');
}
