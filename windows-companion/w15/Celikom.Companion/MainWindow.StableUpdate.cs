using Celikom.NativeInstaller;

namespace Celikom.Companion;

public partial class MainWindow
{
    private readonly System.Windows.Forms.Timer _stableUpdatePulse = new()
        { Interval = 30 * 60 * 1000 };
    private bool _stableUpdateCheckBusy;

    private void InitializeStableUpdateScheduler()
    {
        _stableUpdatePulse.Tick += async (_, _) => await CheckStableUpdateIfSafeAsync();
    }

    private async Task CheckStableUpdateIfSafeAsync()
    {
        if (_stableUpdateCheckBusy || _closing ||
            !StableUpdateTrustConfiguration.TryGetProduction(out _))
            return;

        _stableUpdateCheckBusy = true;
        try
        {
            if (_bridgeStarted && !_integrationBusy && !_hostProbeBusy &&
                DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
                await RefreshHostAsync();

            var result = await StableUpdateInstallCoordinator.CheckAndInstallAsync(
                GetStableUpdateInstallContext);
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
