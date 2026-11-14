namespace Celikom.Companion;

/// <summary>
/// W124: the single production stable-update transaction. It stays disabled
/// until the build contains real P-256 and Authenticode pins. A signed update
/// is staged, journaled, supervised and launched only while playback is idle.
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
        if (!CanInstall(getContext()))
            return new(Outcome.Deferred);

        StableUpdatePackageStager.VerifiedInstaller? staged = null;
        StableUpdateRollbackJournal.Record? record = null;
        var journalPhase = StableUpdateRollbackJournal.Phase.Prepared;
        var root = StableUpdateRollbackJournal.DefaultPrivateRoot;

        try
        {
            var lastKnownGood = await StableUpdateBootstrapper.EnsureInitialLastKnownGoodAsync(
                trust.OfficialOrigin, trust.ManifestPublicKeyDer,
                trust.SignerCertificateSha256, cancellationToken);

            var latest = await StableUpdateManifestFetcher.FetchSignedIfNewerAsync(
                trust.OfficialOrigin, trust.ManifestPublicKeyDer,
                AppUpdateManager.RunningVersion, lastKnownGood.Release.Sequence,
                cancellationToken);
            if (latest is null)
                return new(Outcome.NoUpdate);

            staged = await StableUpdatePackageStager.FetchVerifiedAsync(
                latest, trust.SignerCertificateSha256, cancellationToken);

            // A user may start Yandex or CELIKOM while the package downloads.
            // Recheck before creating a durable transaction or starting helper.
            var installContext = getContext();
            if (!CanInstall(installContext))
                return new(Outcome.Deferred, latest.Version);

            StableUpdatePackageStager.VerifyInstaller(
                staged.Path, latest, trust.SignerCertificateSha256);

            record = StableUpdateRollbackJournal.PrepareSigned(
                root,
                lastKnownGood.Release,
                lastKnownGood.Path,
                latest,
                staged.Path,
                trust.SignerCertificateSha256,
                AppUpdateManager.RunningVersion,
                DateTimeOffset.UtcNow,
                installContext.HasSession,
                installContext.NativeWasInstalled);

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
                return new(Outcome.Deferred, latest.Version);
            }

            StableUpdateRollbackJournal.Advance(
                root, record.Id, StableUpdateRollbackJournal.Phase.Prepared,
                StableUpdateRollbackJournal.Phase.InstallerStarted);
            journalPhase = StableUpdateRollbackJournal.Phase.InstallerStarted;

            var targetInstaller = StableUpdateRollbackJournal.GetTargetInstallerPath(
                root, record.Id);
            StableUpdatePackageStager.VerifyInstaller(
                targetInstaller, latest, trust.SignerCertificateSha256);

            try
            {
                AppUpdateManager.MarkPending(latest.Version);
                AppUpdateManager.LaunchVerifiedSigned(
                    targetInstaller, latest, trust.SignerCertificateSha256);
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
            throw;
        }
        catch (Exception e) when (IsPendingTransaction(e))
        {
            return new(Outcome.PendingTransaction);
        }
        catch
        {
            if (record is not null)
                TryAdvance(record.Id, journalPhase,
                    StableUpdateRollbackJournal.Phase.ManualRecovery);
            return new(Outcome.Failed, null, "STABLE_UPDATE_CHECK_FAILED");
        }
        finally
        {
            if (staged is not null)
                StableUpdatePackageStager.CleanupVerifiedStage(staged);
        }
    }

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
