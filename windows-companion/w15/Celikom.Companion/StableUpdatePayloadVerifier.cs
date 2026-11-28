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
    private const long DefaultInstalledPayloadMaxBytes = 250_000_000;
    /// <summary>
    /// Opens the exact SHA-256-verified image while denying write and delete
    /// sharing. Callers keep this handle alive through Process.Start so a
    /// verified installer/helper cannot be swapped at the execution boundary.
    /// </summary>
    public static FileStream OpenVerifiedReadHandle(
        string path, string expectedSha256, long? expectedSize = null,
        long maxBytes = DefaultInstalledPayloadMaxBytes)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            expectedSha256 is not { Length: 64 } ||
            expectedSha256.Any(c => c is not
                (>= '0' and <= '9' or >= 'a' and <= 'f')) ||
            maxBytes is < 1 or > 250_000_000 ||
            expectedSize.HasValue &&
                (expectedSize.Value < 1 || expectedSize.Value > maxBytes))
            throw new IOException("STABLE_UPDATE_LAUNCH_IDENTITY_INVALID");

        var fullPath = Path.GetFullPath(path);
        EnsureNoReparseAncestors(fullPath);
        var info = new FileInfo(fullPath);
        if (!info.Exists || info.LinkTarget is not null ||
            info.Attributes.HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("STABLE_UPDATE_LAUNCH_IMAGE_INVALID");

        var file = new FileStream(fullPath, FileMode.Open, FileAccess.Read,
            FileShare.Read, 64 * 1024, FileOptions.SequentialScan);
        try
        {
            if (File.GetAttributes(fullPath).HasFlag(FileAttributes.ReparsePoint) ||
                file.Length is < 1 || file.Length > maxBytes ||
                expectedSize.HasValue && file.Length != expectedSize.Value)
                throw new IOException("STABLE_UPDATE_LAUNCH_IMAGE_INVALID");

            var expected = Convert.FromHexString(expectedSha256);
            var actual = SHA256.HashData(file);
            if (!CryptographicOperations.FixedTimeEquals(expected, actual))
                throw new IOException("STABLE_UPDATE_LAUNCH_IMAGE_HASH_MISMATCH");
            file.Position = 0;
            return file;
        }
        catch
        {
            file.Dispose();
            throw;
        }
    }

    private static void EnsureNoReparseAncestors(string path)
    {
        if (path.StartsWith(@"\\", StringComparison.Ordinal))
            throw new IOException("STABLE_UPDATE_LAUNCH_PATH_UNSAFE");
        var current = Path.GetPathRoot(path);
        if (string.IsNullOrWhiteSpace(current))
            throw new IOException("STABLE_UPDATE_LAUNCH_PATH_UNSAFE");
        foreach (var segment in path[current.Length..].Split(
            new[] { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar },
            StringSplitOptions.RemoveEmptyEntries))
        {
            current = Path.Combine(current, segment);
            if ((Directory.Exists(current) || File.Exists(current)) &&
                File.GetAttributes(current).HasFlag(FileAttributes.ReparsePoint))
                throw new IOException("STABLE_UPDATE_LAUNCH_REPARSE_POINT");
        }
    }

    public static bool MatchesFile(string path, string expectedSha256,
        long maxBytes = DefaultInstalledPayloadMaxBytes)
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
