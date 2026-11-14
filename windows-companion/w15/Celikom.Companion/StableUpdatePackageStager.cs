using System.Buffers;
using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text.RegularExpressions;
using Celikom.NativeInstaller;

[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("Celikom.Companion.Tests")]

namespace Celikom.Companion;

/// <summary>
/// W105: verified offline staging for a future signed stable updater.
/// Deliberately NOT wired to app launch: the public production signing key,
/// signed release feed, independent crash rollback and safe-install scheduler
/// must all be shipped and tested before unattended activation.
/// </summary>
public static class StableUpdatePackageStager
{
    public sealed record VerifiedInstaller(
        string Path, Version Version, long Sequence, string Sha256);

    private const long MaxBytes = 125_000_000;
    private static readonly Regex CertFingerprint = new(
        "^[a-fA-F0-9]{64}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

    /// <summary>
    /// Network stage is only an untrusted download until WinVerifyTrust,
    /// pinned signer certificate, PE metadata and bytes pass VerifyInstaller.
    /// Caller must supply a release produced by verified signed-manifest parsing.
    /// </summary>
    public static async Task<VerifiedInstaller> FetchVerifiedAsync(
        StableUpdateManifestVerifier.VerifiedRelease release,
        string pinnedSignerCertSha256, CancellationToken cancellationToken = default)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_UPDATE_WINDOWS_ONLY");
        if (!CertFingerprint.IsMatch(pinnedSignerCertSha256 ?? ""))
            throw new IOException("STABLE_UPDATE_SIGNER_UNPINNED");
        RequirePayloadIdentity(release);

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
            VerifyInstaller(downloaded, release, pinnedSignerCertSha256!);
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
    /// Recheck immediately before any eventual installer launch. Never trust
    /// a staged path just because it passed at an earlier moment.
    /// </summary>
    public static void VerifyInstaller(
        string stagedPath, StableUpdateManifestVerifier.VerifiedRelease release,
        string pinnedSignerCertSha256)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_UPDATE_WINDOWS_ONLY");
        if (release is null || !CertFingerprint.IsMatch(pinnedSignerCertSha256 ?? ""))
            throw new IOException("STABLE_UPDATE_SIGNER_UNPINNED");
        RequirePayloadIdentity(release);
        if (!File.Exists(stagedPath))
            throw new IOException("STABLE_UPDATE_FILE_MISSING");

        var file = new FileInfo(stagedPath);
        if (file.Attributes.HasFlag(FileAttributes.ReparsePoint) ||
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

        // WinVerifyTrust checks a trusted Authenticode signature, not just
        // the presence of a certificate in the EXE resources. The signer
        // certificate must separately match a build-time trusted SHA256 pin.
        if (!NativeHostSignature.IsValid(stagedPath))
            throw new IOException("STABLE_UPDATE_AUTHENTICODE_INVALID");
        try
        {
#pragma warning disable SYSLIB0057
            using var signer = X509Certificate.CreateFromSignedFile(stagedPath);
#pragma warning restore SYSLIB0057
            var certHash = SHA256.HashData(signer.GetRawCertData());
            var pinned = Convert.FromHexString(pinnedSignerCertSha256!);
            if (!CryptographicOperations.FixedTimeEquals(certHash, pinned))
                throw new IOException("STABLE_UPDATE_SIGNER_MISMATCH");
        }
        catch (CryptographicException)
        {
            throw new IOException("STABLE_UPDATE_SIGNER_INVALID");
        }

        var meta = FileVersionInfo.GetVersionInfo(stagedPath);
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
        var stagingDir = Path.Combine(root, Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(stagingDir);
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
        if (!CertFingerprint.IsMatch(release.ApplicationSha256 ?? "") ||
            !CertFingerprint.IsMatch(release.NativeHostSha256 ?? "") ||
            !CertFingerprint.IsMatch(release.RendererSha256 ?? ""))
            throw new IOException("STABLE_UPDATE_PAYLOAD_IDENTITY_MISSING");
    }

    private static byte[] DecodeExpectedHash(string sha256)
    {
        if (sha256 is null || !CertFingerprint.IsMatch(sha256))
            throw new IOException("STABLE_UPDATE_SHA256_INVALID");
        return Convert.FromHexString(sha256);
    }

    private static bool SameVersion(Version a, Version b) =>
        a.Major == b.Major && a.Minor == b.Minor &&
        a.Build == b.Build && Math.Max(a.Revision, 0) == Math.Max(b.Revision, 0);

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
    public static bool CanInstall(
        bool bridgeEnabled, bool yandexProcessRunning,
        bool playbackStateKnown, bool installerBusy) =>
        !bridgeEnabled && !yandexProcessRunning && playbackStateKnown && !installerBusy;
}
