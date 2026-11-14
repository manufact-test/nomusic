using System.Security.Cryptography;

namespace Celikom.Companion;

/// <summary>
/// W112 exact installed-payload witness. The signed stable manifest supplies
/// hashes for the executable and both native bridge assets. The supervisor
/// compares installed bytes to those immutable values before calling a build
/// healthy. Files are opened read-only without write/delete sharing.
/// </summary>
public static class StableUpdatePayloadVerifier
{
    public static bool MatchesFile(string path, string expectedSha256,
        long maxBytes = 125_000_000)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            expectedSha256 is not { Length: 64 } ||
            expectedSha256.Any(c => c is not
                (>= '0' and <= '9' or >= 'a' and <= 'f')) ||
            maxBytes is < 1 or > 250_000_000)
            return false;
        try
        {
            using var file = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.Read, 64 * 1024, FileOptions.SequentialScan);
            if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0 ||
                file.Length is < 1 || file.Length > maxBytes)
                return false;
            var expected = Convert.FromHexString(expectedSha256);
            var actual = SHA256.HashData(file);
            return CryptographicOperations.FixedTimeEquals(expected, actual);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or
            CryptographicException or ArgumentException or NotSupportedException)
        {
            return false;
        }
    }
}
