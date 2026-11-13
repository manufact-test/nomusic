using System.Diagnostics;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

public sealed partial class MainWindow
{
    /// <summary>
    /// Silent, opt-in Windows startup. The user previously pressed Start, the
    /// registry identity still matches, and the server must authorize NOW.
    /// Never invoke manual Start, spawn Yandex, open modal dialogs, or trust a
    /// locally remembered token as a playback entitlement.
    /// </summary>
    private async Task ResumeSavedPlaybackAsync()
    {
        if (_closing || _autoReconnectBusy || _integrationBusy || _compactStarting ||
            !_bridgeStarted || !_api.IsLoggedIn || _bridge.Enabled ||
            _resumeAfterNetworkFailure ||
            !WindowsLaunchSettings.MayResume(_api.Settings, Application.ExecutablePath))
            return;

        _autoReconnectBusy = true;
        _autoReconnectLastAttempt = DateTimeOffset.UtcNow;
        var generation = _compactStartEpoch;
        var account = _api.Settings;
        bool StillRequested() => !_closing && !IsDisposed &&
            generation == _compactStartEpoch && _api.IsLoggedIn &&
            !_bridge.Enabled &&
            _api.Settings.InstallationId == account.InstallationId &&
            string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase) &&
            WindowsLaunchSettings.MayResume(_api.Settings, Application.ExecutablePath);
        try
        {
            await RefreshHostAsync();
            if (!StillRequested()) return;

            // Never start a new trial in a background process. This GET is
            // read-only; server authority is required at every auto resume.
            var access = await _api.GetEntitlementAsync();
            if (!StillRequested()) return;
            if (!PlaybackEntitlement.Allowed(access, DateTimeOffset.UtcNow))
            {
                DiagnosticLog.Record("WIN_AUTORUN_ACCESS_NOT_ALLOWED");
                return;
            }

            if (_nativeInstallState == NativeInstallState.Active &&
                !_installedModule.MatchesApplication)
            {
                // A signed module update is safe only if Yandex isn't already
                // playing. Never interrupt a listener while logging in.
                if (IsYandexRunning())
                {
                    DiagnosticLog.Record("WIN_AUTORUN_MODULE_REPAIR_DEFERRED");
                    return;
                }

                _integrationBusy = true;
                UpdateSafe();
                try
                {
                    if (!StillRequested()) return;
                    DiagnosticLog.Record("WIN_AUTORUN_MODULE_REPAIR_REQUEST");
                    await Task.Run(() => NativeIntegrationManager.Upgrade());
                    DiagnosticLog.Record("WIN_AUTORUN_MODULE_REPAIR_OK");
                }
                finally
                {
                    _integrationBusy = false;
                }
                await RefreshHostAsync();
            }
            else if (_nativeInstallState == NativeInstallState.VerifiedVendorUpdate)
            {
                if (!NativeIntegrationManager.IsPreviouslyApprovedVendorUpdate() ||
                    IsYandexRunning())
                {
                    DiagnosticLog.Record("WIN_AUTORUN_VENDOR_RECOVERY_DEFERRED");
                    return;
                }
                _integrationBusy = true;
                UpdateSafe();
                try
                {
                    if (!StillRequested()) return;
                    DiagnosticLog.Record("WIN_AUTORUN_VENDOR_REPAIR_REQUEST");
                    await Task.Run(() => NativeIntegrationManager.Install());
                    DiagnosticLog.Record("WIN_AUTORUN_VENDOR_REPAIR_OK");
                }
                finally
                {
                    _integrationBusy = false;
                }
                await RefreshHostAsync();
            }

            if (!StillRequested()) return;
            if (_nativeInstallState != NativeInstallState.Active ||
                !_installedModule.MatchesApplication)
            {
                DiagnosticLog.Record("WIN_AUTORUN_HOST_NOT_READY");
                return;
            }

            // A native rebuild can take time and an entitlement may expire;
            // verify one more time just before enabling the bridge.
            var finalAccess = await _api.GetEntitlementAsync();
            if (!StillRequested() ||
                !PlaybackEntitlement.Allowed(finalAccess, DateTimeOffset.UtcNow))
            {
                DiagnosticLog.Record("WIN_AUTORUN_RECHECK_NOT_ALLOWED");
                return;
            }
            _bridge.SetEnabled(true);
            DiagnosticLog.Record("WIN_AUTORUN_CONNECTED_IN_TRAY");
            // Deliberately no Process.Start(Yandex). The owner opens it.
        }
        catch (Exception)
        {
            DiagnosticLog.Record("WIN_AUTORUN_CHECK_OR_REPAIR_FAILED");
            // No popup or auto retry storm. 2-minute backoff is in timer.
        }
        finally
        {
            _autoReconnectBusy = false;
            if (!_closing && !IsDisposed) UpdateSafe();
        }
    }

    private static bool IsYandexRunning()
    {
        try
        {
            var processes = Process.GetProcessesByName("Яндекс Музыка");
            try { return processes.Length != 0; }
            finally { foreach (var process in processes) process.Dispose(); }
        }
        catch { return true; } // fail closed on inability to inspect
    }
}
