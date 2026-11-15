using System.Text.RegularExpressions;

namespace Celikom.Companion;

/// <summary>
/// W116 first-install bootstrap. It downloads only the manifest-verified installer for
/// the exact currently installed version, verifies the signed manifest and
/// every installed payload byte, and seeds a durable LKG cache. It never
/// launches an installer, changes Yandex, or interrupts playback.
/// </summary>
public static class StableUpdateBootstrapper
{
    private static readonly SemaphoreSlim BootstrapGate = new(1, 1);

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
            if (string.IsNullOrWhiteSpace(directory) ||
                !string.Equals(Path.GetFileName(fullApplication), "CELIKOM.Companion.exe",
                    StringComparison.OrdinalIgnoreCase))
                throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALL_ROOT_INVALID");
            return new InstalledPayloadPaths(
                fullApplication,
                Path.Combine(directory, "integration", "host.cjs"),
                Path.Combine(directory, "integration", "renderer.js"),
                Path.Combine(directory, "CELIKOM.UpdateSupervisor.exe"));
        }
    }

    /// <summary>
    /// Verifies the exact signed manifest and all four installed payloads for
    /// the running version. This lightweight identity check allows the app to
    /// discover/download a newer package while Yandex is playing; it does not
    /// seed rollback state or launch an installer.
    /// </summary>
    public static async Task<StableUpdateManifestVerifier.VerifiedRelease>
        FetchInstalledManifestReleaseAsync(
            Uri officialOrigin, byte[] pinnedPublicKey,
            CancellationToken cancellationToken = default)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_ROLLBACK_WINDOWS_ONLY");
        var installed = InstalledPayloadPaths.CurrentProcess();
        var installedVersion = AppUpdateManager.RunningVersion;
        if (installedVersion.Major < 0 || installedVersion.Minor < 0 ||
            installedVersion.Build < 0)
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALLED_IDENTITY_INVALID");

        var release = await StableUpdateManifestFetcher.FetchSignedVersionAsync(
            officialOrigin, pinnedPublicKey, installedVersion, cancellationToken);
        if (!SameVersion(release.Version, installedVersion))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_VERSION_MISMATCH");
        VerifyInstalledPayloads(release, installed);
        return release;
    }

    public static async Task<StableUpdateRollbackJournal.CachedVerifiedPackage>
        EnsureInitialLastKnownGoodAsync(
            Uri officialOrigin, byte[] pinnedPublicKey,
            string manifestPublicKeySha256,
            CancellationToken cancellationToken = default)
    {
        await BootstrapGate.WaitAsync(cancellationToken);
        try
        {
            return await EnsureInitialLastKnownGoodCoreAsync(
                officialOrigin, pinnedPublicKey, manifestPublicKeySha256,
                cancellationToken);
        }
        finally
        {
            BootstrapGate.Release();
        }
    }

    private static async Task<StableUpdateRollbackJournal.CachedVerifiedPackage>
        EnsureInitialLastKnownGoodCoreAsync(
            Uri officialOrigin, byte[] pinnedPublicKey,
            string manifestPublicKeySha256,
            CancellationToken cancellationToken)
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_ROLLBACK_WINDOWS_ONLY");
        if (manifestPublicKeySha256 is not { Length: 64 } ||
            !Regex.IsMatch(manifestPublicKeySha256,
                "^[a-f0-9]{64}$", RegexOptions.CultureInvariant))
            throw new IOException("STABLE_ROLLBACK_MANIFEST_KEY_UNPINNED");

        var installed = InstalledPayloadPaths.CurrentProcess();
        var installedVersion = AppUpdateManager.RunningVersion;
        if (installedVersion.Major < 0 || installedVersion.Minor < 0 ||
            installedVersion.Build < 0)
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_INSTALLED_IDENTITY_INVALID");

        var root = StableUpdateRollbackJournal.DefaultPrivateRoot;
        try
        {
            var existing = StableUpdateRollbackJournal.GetLastKnownGood(
                root, manifestPublicKeySha256);
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
            release, cancellationToken);
        try
        {
            StableUpdateRollbackJournal.SeedInitialLastKnownGoodVerified(
                root, release, staged.Path, manifestPublicKeySha256,
                installed.Application, installed.NativeHost,
                installed.Renderer, installed.Supervisor);
            var seeded = StableUpdateRollbackJournal.GetLastKnownGood(
                root, manifestPublicKeySha256);
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
