namespace Celikom.Companion;

/// <summary>
/// W124/W140: the single production stable-update transaction. Signed feed
/// discovery and package staging run in the background during playback. The
/// verified package is retained until the existing strict safe-point gate
/// allows the Supervisor-controlled in-place installation.
/// </summary>
public static class StableUpdateInstallCoordinator
{
    public sealed record Context(
        bool BridgeEnabled,
        bool YandexProcessRunning,
        bool PlaybackStateKnown,
        bool InstallerBusy,
        bool HasSession,
        bool NativeWasInstalled);

    public enum Outcome
    {
        TrustNotConfigured,
        Deferred,
        DownloadedWaitingForSafePoint,
        NoUpdate,
        PendingTransaction,
        SupervisorNotReady,
        InstallerLaunchFailed,
        InstallerStarted,
        Failed
    }

    public sealed record Result(
        Outcome Outcome,
        Version? TargetVersion = null,
        string? DiagnosticCode = null);

    public static async Task<Result> CheckAndInstallAsync(
        Func<Context> getContext,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(getContext);
        if (!OperatingSystem.IsWindows())
            return new(Outcome.Failed, null, "STABLE_UPDATE_CHECK_FAILED");
        if (!StableUpdateTrustConfiguration.TryGetProduction(out var trust) ||
            trust is null)
            return new(Outcome.TrustNotConfigured);

        // This gate deliberately ignores active playback. Only another
        // installer/integration operation may suppress background discovery.
        if (!CanDownload(getContext()))
            return new(Outcome.Deferred);

        StableUpdatePackageStager.VerifiedInstaller? staged = null;
        StableUpdateRollbackJournal.Record? record = null;
        var journalPhase = StableUpdateRollbackJournal.Phase.Prepared;
        var keepPendingPackage = false;
        var root = StableUpdateRollbackJournal.DefaultPrivateRoot;

        try
        {
            // Authenticate the currently installed version and all companion
            // payloads without downloading its installer. This gives us the
            // anti-downgrade sequence even before the first LKG bootstrap.
            var installedRelease =
                await StableUpdateBootstrapper.FetchInstalledManifestReleaseAsync(
                    trust.OfficialOrigin, trust.ManifestPublicKeyDer, cancellationToken);

            var lastAcceptedSequence = installedRelease.Sequence;
            var hasLastKnownGood = false;
            try
            {
                var cached = StableUpdateRollbackJournal.GetLastKnownGood(
                    root, trust.ManifestPublicKeySha256);
                if (cached.Release.Version != AppUpdateManager.RunningVersion ||
                    cached.Release.Sequence != installedRelease.Sequence)
                    throw new IOException("STABLE_UPDATE_CURRENT_LKG_MISMATCH");
                lastAcceptedSequence = Math.Max(
                    cached.LastAcceptedSequence, cached.Release.Sequence);
                hasLastKnownGood = true;
            }
            catch (IOException e) when (e.Message == "STABLE_ROLLBACK_RECORD_MISSING")
            {
                // First signed bootstrap: the immutable current-version
                // manifest supplies the monotonic sequence until LKG is seeded.
            }

            if (!CanDownload(getContext()))
                return new(Outcome.Deferred);

            var latest = await StableUpdateManifestFetcher.FetchSignedIfNewerAsync(
                trust.OfficialOrigin, trust.ManifestPublicKeyDer,
                AppUpdateManager.RunningVersion, lastAcceptedSequence,
                cancellationToken);
            if (latest is null)
            {
                StableUpdatePackageStager.CleanupPendingPackages();
                // Seed the initial rollback image only when the strict safe
                // point is available. This never blocks music or installs.
                if (!hasLastKnownGood && CanInstall(getContext()))
                {
                    await StableUpdateBootstrapper.EnsureInitialLastKnownGoodAsync(
                        trust.OfficialOrigin, trust.ManifestPublicKeyDer,
                        trust.ManifestPublicKeySha256, cancellationToken);
                }
                return new(Outcome.NoUpdate);
            }

            if (!CanDownload(getContext()))
                return new(Outcome.Deferred);

            // The package is fully manifest-SHA-256/PE verified before it
            // enters the durable pending cache. A later pass re-verifies it
            // against the freshly authenticated latest manifest.
            staged = await StableUpdatePackageStager.FetchOrReusePendingAsync(
                latest, cancellationToken);

            if (!CanInstall(getContext()))
            {
                keepPendingPackage = true;
                return new(Outcome.DownloadedWaitingForSafePoint, latest.Version,
                    "STABLE_UPDATE_DOWNLOADED_WAITING_FOR_SAFE_POINT");
            }

            // Initial LKG bootstrap is intentionally deferred until Yandex is
            // idle; its download is not allowed to interrupt playback either.
            var lastKnownGood =
                await StableUpdateBootstrapper.EnsureInitialLastKnownGoodAsync(
                    trust.OfficialOrigin, trust.ManifestPublicKeyDer,
                    trust.ManifestPublicKeySha256, cancellationToken);

            // Bootstrap can take time. If Yandex started meanwhile, retain the
            // verified pending package and retry only at a later safe point.
            if (!CanInstall(getContext()))
            {
                keepPendingPackage = true;
                return new(Outcome.DownloadedWaitingForSafePoint, latest.Version,
                    "STABLE_UPDATE_DOWNLOADED_WAITING_FOR_SAFE_POINT");
            }

            StableUpdatePackageStager.VerifyInstaller(
                staged.Path, latest);

            record = StableUpdateRollbackJournal.PrepareManifestVerified(
                root,
                lastKnownGood.Release,
                lastKnownGood.InstallerPath,
                latest,
                staged.Path,
                trust.ManifestPublicKeySha256,
                AppUpdateManager.RunningVersion,
                DateTimeOffset.UtcNow,
                getContext().HasSession,
                getContext().NativeWasInstalled);

            // The durable DPAPI transaction now owns byte-identical verified
            // previous and target installers. The pending cache can be removed.
            keepPendingPackage = false;

            if (!await StableUpdateSupervisorLauncher.StartAsync(record, cancellationToken))
            {
                TryAdvance(record.Id, StableUpdateRollbackJournal.Phase.Prepared,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
                return new(Outcome.SupervisorNotReady, latest.Version,
                    "STABLE_UPDATE_SUPERVISOR_FAILED");
            }

            // The helper is alive and has validated its DPAPI journal and image.
            // Recheck safety after the async handshake; no await follows this check.
            if (!CanInstall(getContext()))
            {
                TryAdvance(record.Id, StableUpdateRollbackJournal.Phase.Prepared,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
                return new(Outcome.Deferred, latest.Version,
                    "STABLE_UPDATE_SAFE_POINT_LOST_DURING_HANDSHAKE");
            }

            StableUpdateRollbackJournal.Advance(
                root, record.Id, StableUpdateRollbackJournal.Phase.Prepared,
                StableUpdateRollbackJournal.Phase.InstallerStarted);
            journalPhase = StableUpdateRollbackJournal.Phase.InstallerStarted;

            var targetInstaller = StableUpdateRollbackJournal.GetTargetInstallerPath(
                root, record.Id);
            StableUpdatePackageStager.VerifyInstaller(
                targetInstaller, latest);

            try
            {
                AppUpdateManager.MarkPending(latest.Version);
                AppUpdateManager.LaunchManifestVerified(
                    targetInstaller, latest, trust.ManifestPublicKeySha256);
            }
            catch
            {
                AppUpdateManager.ClearPending();
                TryAdvance(record.Id, journalPhase,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
                return new(Outcome.InstallerLaunchFailed, latest.Version,
                    "STABLE_UPDATE_INSTALL_LAUNCH_FAILED");
            }

            return new(Outcome.InstallerStarted, latest.Version);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            if (record is not null)
                TryAdvance(record.Id, journalPhase,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
            else if (staged is not null)
                keepPendingPackage = true;
            throw;
        }
        catch (Exception e) when (IsPendingTransaction(e))
        {
            if (record is not null)
                TryAdvance(record.Id, journalPhase,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
            else if (staged is not null)
                keepPendingPackage = true;
            return new(Outcome.PendingTransaction);
        }
        catch
        {
            if (record is not null)
                TryAdvance(record.Id, journalPhase,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
            else if (staged is not null)
                keepPendingPackage = true;
            return new(Outcome.Failed, null, "STABLE_UPDATE_CHECK_FAILED");
        }
        finally
        {
            if (staged is not null && !keepPendingPackage)
                StableUpdatePackageStager.CleanupStagedPackage(staged);
        }
    }

    private static bool CanDownload(Context context) =>
        StableUpdateInstallSafety.CanDownload(context.InstallerBusy);

    private static bool CanInstall(Context context) =>
        StableUpdateInstallSafety.CanInstall(
            context.BridgeEnabled,
            context.YandexProcessRunning,
            context.PlaybackStateKnown,
            context.InstallerBusy);

    private static bool IsPendingTransaction(Exception error) =>
        error.Message.Contains("LAST_KNOWN_GOOD_NOT_READY", StringComparison.Ordinal) ||
        error.Message.Contains("PENDING_EXISTS", StringComparison.Ordinal) ||
        error.Message.Contains("TRANSACTION_ALREADY_ACTIVE", StringComparison.Ordinal);

    private static void TryAdvance(
        Guid id, StableUpdateRollbackJournal.Phase expected,
        StableUpdateRollbackJournal.Phase next)
    {
        try
        {
            StableUpdateRollbackJournal.Advance(
                StableUpdateRollbackJournal.DefaultPrivateRoot, id, expected, next);
        }
        catch { /* A newer Supervisor phase always wins; never overwrite it. */ }
    }
}
