using System.Buffers;
using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using Celikom.NativeInstaller;

[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("Celikom.Companion.Tests")]

namespace Celikom.Companion;

/// <summary>
/// W155: verified staging for the single production stable updater.
/// Production activation remains fail-closed until a release build embeds
/// the approved P-256 public key and official feed origin.
/// </summary>
public static class StableUpdatePackageStager
{
    public sealed record VerifiedInstaller(
        string Path, Version Version, long Sequence, string Sha256);

    private const long MaxBytes = 125_000_000;
    private static readonly Regex Sha256Pattern = new(
        "^[a-fA-F0-9]{64}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

    /// <summary>
    /// Network stage is only an untrusted download until the pinned P-256
    /// manifest signature, package SHA-256, PE metadata and bytes are verified.
    /// Caller must supply a release produced by verified signed-manifest parsing.
    /// </summary>
    public static async Task<VerifiedInstaller> FetchVerifiedAsync(
        StableUpdateManifestVerifier.VerifiedRelease release,
        CancellationToken cancellationToken = default)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_UPDATE_WINDOWS_ONLY");
        RequirePayloadIdentity(release);

        // This also verifies every CELIKOM/Windows/StableUpdates ancestor
        // against reparse-point substitution before creating a staging folder.
        EnsurePendingDirectory();
        var root = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CELIKOM", "Windows", "StableUpdates");

        // Do not follow redirects or attach user cookies/credentials to the
        // public signed package URL. Never fetch from a caller-chosen origin.
        using var handler = new HttpClientHandler
        {
            AllowAutoRedirect = false,
            UseCookies = false,
            UseDefaultCredentials = false
        };
        using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(5) };
        var downloaded = await DownloadUntrustedAsync(release, root, client, cancellationToken);
        try
        {
            VerifyInstaller(downloaded, release);
            return new VerifiedInstaller(downloaded, release.Version,
                release.Sequence, release.Sha256);
        }
        catch
        {
            CleanupStage(downloaded);
            throw;
        }
    }

    /// <summary>
    /// Downloads or reuses the exact authenticated package in a durable,
    /// user-scoped pending cache. The manifest is re-fetched and verified on
    /// every scheduler pass; the cached EXE is always rechecked before reuse.
    /// </summary>
    public static async Task<VerifiedInstaller> FetchOrReusePendingAsync(
        StableUpdateManifestVerifier.VerifiedRelease release,
        CancellationToken cancellationToken = default)
    {
        EnsurePendingDirectory();
        var pendingRoot = PendingRoot;
        var pendingPath = GetPendingPackagePath(pendingRoot, release);

        if (File.Exists(pendingPath))
        {
            try
            {
                VerifyInstaller(pendingPath, release);
                CleanupPendingPackages(pendingPath);
                return new VerifiedInstaller(pendingPath, release.Version,
                    release.Sequence, release.Sha256);
            }
            catch
            {
                TryDeletePendingFile(pendingPath);
            }
        }

        var downloaded = await FetchVerifiedAsync(
            release, cancellationToken);
        try
        {
            EnsurePendingDirectory();
            File.Move(downloaded.Path, pendingPath, overwrite: true);
            VerifyInstaller(pendingPath, release);
            CleanupPendingPackages(pendingPath);
            return new VerifiedInstaller(pendingPath, release.Version,
                release.Sequence, release.Sha256);
        }
        catch
        {
            TryDeletePendingFile(pendingPath);
            throw;
        }
        finally
        {
            CleanupVerifiedStage(downloaded);
        }
    }

    internal static string GetPendingPackagePath(
        string root, StableUpdateManifestVerifier.VerifiedRelease release)
    {
        var sha256 = release?.Sha256 ?? "";
        if (string.IsNullOrWhiteSpace(root) || release is null ||
            release.Version.Major < 0 || release.Version.Minor < 0 ||
            release.Version.Build < 0 || release.Sequence <= 0 ||
            !Sha256Pattern.IsMatch(sha256))
            throw new IOException("STABLE_UPDATE_PENDING_IDENTITY_INVALID");

        var name = $"CELIKOM-{release.Version.ToString(3)}-{release.Sequence}-" +
            sha256.ToLowerInvariant() + ".exe";
        return Path.Combine(Path.GetFullPath(root), name);
    }

    /// <summary>Remove stale cached update packages after an authenticated no-update result.</summary>
    public static void CleanupPendingPackages() => CleanupPendingPackages(null);

    private static void CleanupPendingPackages(string? keepPath)
    {
        try
        {
            var root = PendingRoot;
            if (!Directory.Exists(root) ||
                File.GetAttributes(root).HasFlag(FileAttributes.ReparsePoint))
                return;
            var keep = string.IsNullOrWhiteSpace(keepPath)
                ? "" : Path.GetFullPath(keepPath);
            foreach (var file in Directory.EnumerateFiles(
                root, "CELIKOM-*.exe", SearchOption.TopDirectoryOnly))
            {
                if (keep.Length > 0 &&
                    string.Equals(Path.GetFullPath(file), keep,
                        StringComparison.OrdinalIgnoreCase))
                    continue;
                TryDeletePendingFile(file);
            }
        }
        catch { /* Cache cleanup must never turn a valid update into a launch. */ }
    }

    internal static void CleanupStagedPackage(VerifiedInstaller installer)
    {
        if (installer is null) return;
        try
        {
            var root = Path.GetFullPath(PendingRoot) + Path.DirectorySeparatorChar;
            var path = Path.GetFullPath(installer.Path);
            if (path.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            {
                TryDeletePendingFile(path);
                return;
            }
        }
        catch { }
        CleanupStage(installer.Path);
    }

    private static string PendingRoot => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows", "StableUpdates", "Pending");

    private static void EnsurePendingDirectory()
    {
        var local = Environment.GetFolderPath(
            Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrWhiteSpace(local))
            throw new IOException("STABLE_UPDATE_LOCAL_DATA_ROOT_MISSING");
        var current = Path.GetFullPath(local);
        foreach (var segment in new[] { "CELIKOM", "Windows", "StableUpdates", "Pending" })
        {
            current = Path.Combine(current, segment);
            Directory.CreateDirectory(current);
            if (File.GetAttributes(current).HasFlag(FileAttributes.ReparsePoint))
                throw new IOException("STABLE_UPDATE_PENDING_REPARSE_POINT");
        }
    }

    private static void TryDeletePendingFile(string path)
    {
        try
        {
            if (File.Exists(path))
                File.Delete(path); // Also removes a file reparse point itself, never its target.
        }
        catch { }
    }

    /// <summary>
    /// Recheck immediately before any eventual installer launch. Never trust
    /// a staged path just because it passed at an earlier moment.
    /// </summary>
    public static void VerifyInstaller(
        string stagedPath, StableUpdateManifestVerifier.VerifiedRelease release)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_UPDATE_WINDOWS_ONLY");
        VerifyInstallerCore(stagedPath, release, path =>
        {
            var meta = FileVersionInfo.GetVersionInfo(path);
            return (meta.FileVersion, meta.CompanyName, meta.ProductName);
        });
    }

    // The signed P-256 manifest authenticates the exact package bytes. PE
    // metadata is an additional product/version guard, not a publisher claim.
    internal static void VerifyInstallerCore(
        string stagedPath, StableUpdateManifestVerifier.VerifiedRelease release,
        Func<string, (string? FileVersion, string? CompanyName, string? ProductName)> readIdentity)
    {
        ArgumentNullException.ThrowIfNull(readIdentity);
        if (release is null)
            throw new IOException("STABLE_UPDATE_RELEASE_INVALID");
        RequirePayloadIdentity(release);
        if (!File.Exists(stagedPath))
            throw new IOException("STABLE_UPDATE_FILE_MISSING");

        var file = new FileInfo(stagedPath);
        if (file.Attributes.HasFlag(FileAttributes.ReparsePoint) ||
            !string.Equals(file.Extension, ".exe", StringComparison.OrdinalIgnoreCase) ||
            file.Length != release.PackageSize ||
            file.Length is < 10_000 or > MaxBytes)
            throw new IOException("STABLE_UPDATE_SIZE_INVALID");

        var expectedHash = DecodeExpectedHash(release.Sha256);
        using (var stream = new FileStream(stagedPath, FileMode.Open,
            FileAccess.Read, FileShare.Read, 65536, FileOptions.SequentialScan))
        {
            var actualHash = SHA256.HashData(stream);
            if (!CryptographicOperations.FixedTimeEquals(expectedHash, actualHash))
                throw new IOException("STABLE_UPDATE_SHA256_MISMATCH");
        }

        var meta = readIdentity(stagedPath);
        if (!Version.TryParse(meta.FileVersion?.Trim(), out var version) ||
            !SameVersion(version, release.Version) ||
            !string.Equals(meta.CompanyName?.Trim(), "CELIKOM", StringComparison.Ordinal) ||
            !string.Equals(meta.ProductName?.Trim(), "CELIKOM", StringComparison.Ordinal))
            throw new IOException("STABLE_UPDATE_PE_IDENTITY_INVALID");
    }

    /// <summary>
    /// Internal testable downloader. Its return value is UNTRUSTED; never run
    /// the file without VerifyInstaller. A failed transfer is always deleted.
    /// </summary>
    internal static async Task<string> DownloadUntrustedAsync(
        StableUpdateManifestVerifier.VerifiedRelease release, string root,
        HttpClient client, CancellationToken cancellationToken = default)
    {
        if (release is null || release.PackageUri is null ||
            release.PackageUri.Scheme != Uri.UriSchemeHttps ||
            release.PackageUri.UserInfo.Length != 0 ||
            release.PackageUri.Query.Length != 0 ||
            release.PackageUri.Fragment.Length != 0 ||
            release.PackageSize is < 10_000 or > MaxBytes)
            throw new IOException("STABLE_UPDATE_PACKAGE_INVALID");
        var expectedHash = DecodeExpectedHash(release.Sha256);
        Directory.CreateDirectory(root);
        if (File.GetAttributes(root).HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("STABLE_UPDATE_STAGE_ROOT_REPARSE_POINT");
        var stagingDir = Path.Combine(root, Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(stagingDir);
        if (File.GetAttributes(stagingDir).HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("STABLE_UPDATE_STAGE_DIRECTORY_REPARSE_POINT");
        var part = Path.Combine(stagingDir, "package.part");
        var output = Path.Combine(stagingDir, "CELIKOM-stable.exe");
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, release.PackageUri);
            using var response = await client.SendAsync(request,
                HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            if (response.StatusCode != HttpStatusCode.OK ||
                response.RequestMessage?.RequestUri != release.PackageUri ||
                response.Content.Headers.ContentLength is long len && len != release.PackageSize)
                throw new IOException("STABLE_UPDATE_HTTP_INVALID");

            await using var input = await response.Content.ReadAsStreamAsync(cancellationToken);
            await using var file = new FileStream(part, FileMode.CreateNew,
                FileAccess.Write, FileShare.None, 65536, FileOptions.Asynchronous);
            using var hasher = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
            var buffer = ArrayPool<byte>.Shared.Rent(64 * 1024);
            long total = 0;
            try
            {
                int read;
                while ((read = await input.ReadAsync(buffer.AsMemory(0, 64 * 1024), cancellationToken)) != 0)
                {
                    total += read;
                    if (total > release.PackageSize)
                        throw new IOException("STABLE_UPDATE_OVERSIZE");
                    await file.WriteAsync(buffer.AsMemory(0, read), cancellationToken);
                    hasher.AppendData(buffer.AsSpan(0, read));
                }
                if (total != release.PackageSize ||
                    !CryptographicOperations.FixedTimeEquals(
                        expectedHash, hasher.GetHashAndReset()))
                    throw new IOException("STABLE_UPDATE_HASH_OR_LENGTH");
            }
            finally { ArrayPool<byte>.Shared.Return(buffer, clearArray: true); }
            await file.FlushAsync(cancellationToken);
            file.Close();
            File.Move(part, output);
            return output;
        }
        catch
        {
            try { Directory.Delete(stagingDir, recursive: true); }
            catch { /* Do not turn a failed download into installer execution. */ }
            throw;
        }
    }

    private static void RequirePayloadIdentity(
        StableUpdateManifestVerifier.VerifiedRelease release)
    {
        if (!Sha256Pattern.IsMatch(release.ApplicationSha256 ?? "") ||
            !Sha256Pattern.IsMatch(release.NativeHostSha256 ?? "") ||
            !Sha256Pattern.IsMatch(release.RendererSha256 ?? "") ||
            !Sha256Pattern.IsMatch(release.SupervisorSha256 ?? ""))
            throw new IOException("STABLE_UPDATE_PAYLOAD_IDENTITY_MISSING");
    }

    private static byte[] DecodeExpectedHash(string sha256)
    {
        if (sha256 is null || !Sha256Pattern.IsMatch(sha256))
            throw new IOException("STABLE_UPDATE_SHA256_INVALID");
        return Convert.FromHexString(sha256);
    }

    private static bool SameVersion(Version a, Version b) =>
        a.Major == b.Major && a.Minor == b.Minor &&
        a.Build == b.Build && Math.Max(a.Revision, 0) == Math.Max(b.Revision, 0);

    internal static void CleanupVerifiedStage(VerifiedInstaller installer)
    {
        if (installer is not null) CleanupStage(installer.Path);
    }

    private static void CleanupStage(string path)
    {
        try
        {
            var folder = Path.GetDirectoryName(path);
            if (folder != null && Directory.Exists(folder))
                Directory.Delete(folder, recursive: true);
        }
        catch { /* Failed trust check is terminal regardless of cleanup. */ }
    }
}

/// <summary>
/// Most conservative possible no-playback-interruption gate: an active
/// Yandex process, connected bridge, unknown playback state or concurrent
/// install always defers the update. No automated launch uses this yet.
/// </summary>
public static class StableUpdateInstallSafety
{
    // Feed checks and verified package downloads are background work. Only
    // the final installer launch is gated by the live Yandex/playback state.
    public static bool CanDownload(bool installerBusy) => !installerBusy;

    public static bool CanInstall(
        bool bridgeEnabled, bool yandexProcessRunning,
        bool playbackStateKnown, bool installerBusy) =>
        !bridgeEnabled && !yandexProcessRunning && playbackStateKnown && !installerBusy;
}
