using System.Diagnostics;
using System.Text.RegularExpressions;

namespace Celikom.Companion;

/// <summary>
/// W116 first-install bootstrap. It downloads only the signed installer for
/// the exact currently installed version, verifies the Authenticode signer and
/// every installed payload byte, and seeds a durable LKG cache. It never
/// launches an installer, changes Yandex, or interrupts playback.
/// </summary>
public static class StableUpdateBootstrapper
{
    public sealed record InstalledPayloadPaths(
        string Application, string NativeHost, string Renderer, string Supervisor)
    {
        public static InstalledPayloadPaths CurrentProcess()
        {
            var application = Environment.ProcessPath;
            if (string.IsNullOrWhiteSpace(application))
                throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_PROCESS_PATH_MISSING");
            var fullApplication = Path.GetFullPath(application);
            var directory = Path.GetDirectoryName(fullApplication);
            if (string.IsNullOrWhiteSpace(directory))
                throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALL_ROOT_INVALID");
            return new InstalledPayloadPaths(
                fullApplication,
                Path.Combine(directory, "integration", "host.cjs"),
                Path.Combine(directory, "integration", "renderer.js"),
                Path.Combine(directory, "CELIKOM.UpdateSupervisor.exe"));
        }
    }

    public static async Task<StableUpdateRollbackJournal.CachedSignedPackage>
        EnsureInitialLastKnownGoodAsync(
            Uri officialOrigin, byte[] pinnedPublicKey,
            string pinnedSignerCertificateSha256,
            CancellationToken cancellationToken = default)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_ROLLBACK_WINDOWS_ONLY");
        if (!Regex.IsMatch(pinnedSignerCertificateSha256 ?? "",
            "^[a-fA-F0-9]{64}$", RegexOptions.CultureInvariant))
            throw new IOException("STABLE_ROLLBACK_SIGNER_UNPINNED");

        var installed = InstalledPayloadPaths.CurrentProcess();
        var appInfo = FileVersionInfo.GetVersionInfo(installed.Application);
        if (!string.Equals(appInfo.CompanyName?.Trim(), "CELIKOM", StringComparison.Ordinal) ||
            !string.Equals(appInfo.ProductName?.Trim(), "CELIKOM", StringComparison.Ordinal) ||
            !Version.TryParse(appInfo.FileVersion?.Trim(), out var installedVersion) ||
            !SameVersion(installedVersion, AppUpdateManager.RunningVersion))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALLED_IDENTITY_INVALID");

        var root = StableUpdateRollbackJournal.DefaultPrivateRoot;
        try
        {
            var existing = StableUpdateRollbackJournal.GetLastKnownGood(
                root, pinnedSignerCertificateSha256);
            VerifyInstalledPayloads(existing.Release, installed);
            if (!SameVersion(existing.Release.Version, installedVersion))
                throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALLED_VERSION_MISMATCH");
            return existing;
        }
        catch (IOException e) when (e.Message == "STABLE_ROLLBACK_RECORD_MISSING")
        {
            // Only a genuinely absent journal permits first-install bootstrap.
            // Pending, corrupt, untrusted or incomplete records fail closed.
        }

        var release = await StableUpdateManifestFetcher.FetchSignedVersionAsync(
            officialOrigin, pinnedPublicKey, installedVersion, cancellationToken);
        if (!SameVersion(release.Version, installedVersion))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_VERSION_MISMATCH");

        var staged = await StableUpdatePackageStager.FetchVerifiedAsync(
            release, pinnedSignerCertificateSha256, cancellationToken);
        try
        {
            StableUpdateRollbackJournal.SeedInitialLastKnownGoodSigned(
                root, release, staged.Path, pinnedSignerCertificateSha256,
                installed.Application, installed.NativeHost,
                installed.Renderer, installed.Supervisor);
            var seeded = StableUpdateRollbackJournal.GetLastKnownGood(
                root, pinnedSignerCertificateSha256);
            VerifyInstalledPayloads(seeded.Release, installed);
            return seeded;
        }
        finally
        {
            StableUpdatePackageStager.CleanupVerifiedStage(staged);
        }
    }

    private static void VerifyInstalledPayloads(
        StableUpdateManifestVerifier.VerifiedRelease release,
        InstalledPayloadPaths installed)
    {
        if (!StableUpdatePayloadVerifier.MatchesFile(
                installed.Application, release.ApplicationSha256) ||
            !StableUpdatePayloadVerifier.MatchesFile(
                installed.NativeHost, release.NativeHostSha256) ||
            !StableUpdatePayloadVerifier.MatchesFile(
                installed.Renderer, release.RendererSha256) ||
            !StableUpdatePayloadVerifier.MatchesFile(
                installed.Supervisor, release.SupervisorSha256))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_PAYLOAD_MISMATCH");
    }

    private static bool SameVersion(Version left, Version right) =>
        left.Major == right.Major && left.Minor == right.Minor &&
        Math.Max(left.Build, 0) == Math.Max(right.Build, 0) &&
        Math.Max(left.Revision, 0) == Math.Max(right.Revision, 0);
}
