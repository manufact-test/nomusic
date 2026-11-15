using System.Windows.Forms;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

public partial class MainWindow
{
    private readonly System.Windows.Forms.Timer _stableUpdatePulse = new()
        { Interval = 30 * 60 * 1000 };
    private bool _stableUpdateCheckBusy;
    private bool _stableUpdatePendingSafePoint;

    private void InitializeStableUpdateScheduler()
    {
        _stableUpdatePulse.Tick += async (_, _) => await CheckStableUpdateIfSafeAsync();
    }

    private async Task CheckStableUpdateIfSafeAsync()
    {
        if (_stableUpdateCheckBusy || _closing ||
            !StableUpdateTrustConfiguration.TryGetProduction(out _))
            return;

        // W145: while a verified package is pending, check for a safe-point
        // every 30 seconds without redownloading a feed while Yandex runs.
        if (_stableUpdatePendingSafePoint)
        {
            var current = GetStableUpdateInstallContext();
            var safeNow = StableUpdateInstallSafety.CanInstall(
                current.BridgeEnabled, current.YandexProcessRunning,
                current.PlaybackStateKnown, current.InstallerBusy);
            if (!StableUpdatePendingPollPolicy.ShouldInspectFeed(
                    waitingForSafePoint: true, safeNow))
                return;
        }

        _stableUpdateCheckBusy = true;
        try
        {
            if (_bridgeStarted && !_integrationBusy && !_hostProbeBusy &&
                DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
                await RefreshHostAsync();

            var result = await StableUpdateInstallCoordinator.CheckAndInstallAsync(
                GetStableUpdateInstallContext);
            _stableUpdatePendingSafePoint =
                result.Outcome == StableUpdateInstallCoordinator.Outcome.DownloadedWaitingForSafePoint ||
                (_stableUpdatePendingSafePoint &&
                 result.Outcome == StableUpdateInstallCoordinator.Outcome.Deferred);
            var nextInterval = StableUpdatePendingPollPolicy.IntervalMs(_stableUpdatePendingSafePoint);
            if (_stableUpdatePulse.Interval != nextInterval)
                _stableUpdatePulse.Interval = nextInterval;
            if (result.Outcome == StableUpdateInstallCoordinator.Outcome.InstallerStarted)
            {
                _updatingApplication = true;
                _stableUpdatePulse.Stop();
                UpdateSafe();
                Application.Exit();
                return;
            }

            if (!string.IsNullOrWhiteSpace(result.DiagnosticCode))
                DiagnosticLog.Record(result.DiagnosticCode);
        }
        catch
        {
            DiagnosticLog.Record("STABLE_UPDATE_CHECK_FAILED");
        }
        finally
        {
            _stableUpdateCheckBusy = false;
        }
    }

    private StableUpdateInstallCoordinator.Context GetStableUpdateInstallContext()
    {
        var yandexRunning = !AppUpdateManager.CanLaunchWithoutPlaybackInterrupt(
            bridgeEnabled: false);
        var nativeStateKnown = _nativeInstallState is
            NativeInstallState.Active or NativeInstallState.NotInstalled;
        return new StableUpdateInstallCoordinator.Context(
            BridgeEnabled: _bridge.Enabled,
            YandexProcessRunning: yandexRunning,
            PlaybackStateKnown: _bridgeStarted && nativeStateKnown,
            InstallerBusy: _integrationBusy || _updatingApplication ||
                _closing || _hostProbeBusy,
            HasSession: _api.IsLoggedIn,
            NativeWasInstalled: _nativeInstallState == NativeInstallState.Active);
    }
}


/// <summary>
/// W145: a verified pending update switches to cheap 30-second safe-point
/// checks. No repeated network discovery is made while Yandex is still in use.
/// </summary>
public static class StableUpdatePendingPollPolicy
{
    public const int NormalIntervalMs = 30 * 60 * 1000;
    public const int WaitingIntervalMs = 30 * 1000;

    public static int IntervalMs(bool waitingForSafePoint) =>
        waitingForSafePoint ? WaitingIntervalMs : NormalIntervalMs;

    public static bool ShouldInspectFeed(bool waitingForSafePoint, bool safeNow) =>
        !waitingForSafePoint || safeNow;
}
