using System.Diagnostics;
using System.Drawing;
using System.Net.NetworkInformation;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

/// <summary>
/// One native CELIKOM window, never a media player. Yandex remains the
/// only source of media keys, queue, pause and seek.
/// </summary>
public sealed partial class MainWindow : Form
{
    // Windows presentation follows the actual shipped Chrome extension popup.css.
    // Keep these colors synchronized with extension/popup/popup.css (W59).
    private static readonly Color Ink = ColorTranslator.FromHtml("#F4F7F8");
    private static readonly Color Paper = ColorTranslator.FromHtml("#0B1013");
    private static readonly Color Surface = ColorTranslator.FromHtml("#141B1F");
    private static readonly Color Secondary = ColorTranslator.FromHtml("#AAB8BE");
    private static readonly Color Accent = ColorTranslator.FromHtml("#66E0BF");
    private static readonly Color AccentInk = ColorTranslator.FromHtml("#07110E");
    private static readonly Color Border = ColorTranslator.FromHtml("#2A3439");
    private static readonly Color Danger = ColorTranslator.FromHtml("#F05A69");
    private const string DefaultApiOrigin = "https://darkred-camel-588676.hostingersite.com";

    private readonly SessionStore _store = new();
    private NativeTokenPublisher? _nativeToken;
    private readonly CelikomApi _api;
    private readonly BridgeServer _bridge;
    private readonly TextBox _origin = new();
    private readonly TextBox _email = new();
    private readonly TextBox _password = new();
    private readonly TextBox _code = new();
    private readonly Label _status = new();
    private readonly Label _song = new();
    private readonly Label _hostStatus = new();
    private readonly Label _versionFooter = new();
    private readonly PopupButton _updateApplication = new();
    private NativeModuleIdentity _installedModule = NativeModuleIdentity.Unknown;
    private bool _updatingApplication;
    private readonly bool _finishApplicationUpdate;
    private readonly bool _backgroundStartup;
    private bool _autoReconnectBusy;
    private DateTimeOffset _autoReconnectLastAttempt;
    private readonly PopupButton _connectYandex = new();
    private readonly PopupButton _restoreYandex = new();
    private NativeInstallState _nativeInstallState = NativeInstallState.NotInstalled;
    private bool _integrationBusy;
    private YandexHostResult? _hostReport;
    private bool _hostProbeBusy;
    private Task? _hostProbeTask; // shared by startup and background inspection
    private readonly YandexFailureRecheckGate _failureRecheckGate = new();
    private DateTimeOffset _lastHostProbe;
    private readonly Label _accountStatus = new();
    private readonly PopupButton _login = new();
    private readonly PopupButton _logout = new();
    private readonly PopupButton _start = new();
    private readonly PopupButton _stop = new();
    private readonly Label _connectionState = new();
    private readonly Panel _connectionMark = new(); // exact 7px indicator; Label enforces 10px minimum on Windows
    private readonly Label _switchHint = new();
    private readonly PopupButton _rotate = new();
    private readonly PopupButton _copy = new();
    private readonly NotifyIcon _tray;
    private readonly Panel _pages = new();
    private readonly Panel _homePanel = new();
    private readonly Panel _accountPanel = new();
    private readonly PopupButton _homeTab = new();
    private readonly PopupButton _accountTab = new();
    private readonly Panel _accountSignedOut = new();
    private readonly Panel _accountSignedIn = new();
    private readonly Label _signedInIdentity = new();
    private readonly Panel _staffPanel = new();
    private readonly PopupButton _diagnosticsButton = new();
    private bool _diagnosticsAllowed;
    private int _diagnosticsEpoch;
    private string _diagnosticsVerifiedOrigin = "";
    private string _diagnosticsVerifiedInstallation = "";
    private string _diagnosticsVerifiedEmail = "";

    private bool DiagnosticsVerificationStillCurrent()
    {
        var session = _api.Settings;
        return _api.IsLoggedIn && _diagnosticsAllowed &&
            string.Equals(_diagnosticsVerifiedOrigin, session.Origin, StringComparison.Ordinal) &&
            string.Equals(_diagnosticsVerifiedInstallation, session.InstallationId, StringComparison.Ordinal) &&
            string.Equals(_diagnosticsVerifiedEmail, session.Email, StringComparison.OrdinalIgnoreCase);
    }

    private void RevokeDiagnosticsVisibility()
    {
        _diagnosticsAllowed = false;
        _staffPanel.Visible = false;
        _diagnosticsVerifiedOrigin = "";
        _diagnosticsVerifiedInstallation = "";
        _diagnosticsVerifiedEmail = "";
    }
    private bool _bridgeStarted;
    // A brief server outage may suspend music. Never auto-start without a new,
    // positive authenticated entitlement and the user's original Start intent.
    private bool _resumeAfterNetworkFailure;
    private DateTimeOffset _lastNetworkRecheckHint;
    private DateTimeOffset _lastNetworkRouteLoggedAt;
    private CancellationTokenSource? _compactAccessRequestCancellation;
    private bool _networkRouteRecheckPending;
    private int _networkRouteEpoch;
    private bool _closing;
    private bool _loggingIn;
    // Server is the authority; this periodic check only updates UI/state
    // after a subscription expires or the network becomes unavailable.
    private readonly System.Windows.Forms.Timer _entitlementPulse = new()
        { Interval = 15000 };
    private readonly System.Windows.Forms.Timer _yandexVersionDebounce = new()
        { Interval = 1500 };
    private FileSystemWatcher? _yandexInstallWatcher;

    public MainWindow(bool finishApplicationUpdate = false, bool startBackground = false)
    {
        _finishApplicationUpdate = finishApplicationUpdate;
        _backgroundStartup = startBackground;
        // Build and measure the full compact popup before the user can see
        // any empty WinForms rectangles during the first HandleCreated paint.
        Opacity = 0;
        if (startBackground) ShowInTaskbar = false;
        _api = new CelikomApi(_store);
        _bridge = new BridgeServer(_api, _store);
        _bridge.Changed += () =>
        {
            UpdateSafe();
            // A native HOST_ERROR is explicit; track source failures are not
            // evidence of a Yandex update. Never reload the player here.
            if (!_bridge.Enabled ||
                !YandexFailureRecheckGate.IsNativeHostFailure(_bridge.LastStatus) ||
                !IsHandleCreated || IsDisposed) return;
            try
            {
                BeginInvoke(new Action(() =>
                    _ = RecheckYandexAfterNativeFailureAsync("YANDEX_NATIVE_HOST_ERROR")));
            }
            catch (InvalidOperationException) { /* Window is shutting down. */ }
            catch (ObjectDisposedException) { /* Window is shutting down. */ }
        };
        NetworkChange.NetworkAddressChanged += OnNetworkAddressChanged;

        Text = "CELIKOM"; // version is shown in the compact popup footer, not clipped in titlebar
        // ApplicationIcon is built from the SAME official extension "C" mark.
        // The PE resource survives installation, so it also brands the taskbar.
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath) ?? SystemIcons.Application; }
        catch { Icon = SystemIcons.Application; }
        ClientSize = new Size(462, 570);
        MinimumSize = new Size(430, 540);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 10F);
        BackColor = Paper;
        ForeColor = Ink;
        AutoScaleMode = AutoScaleMode.Dpi;
        KeyPreview = true;
        KeyDown += (_, key) =>
        {
            // Staff-only offline update. Ordinary users see no developer tools.
            if (_diagnosticsAllowed && key.Control && key.Shift && key.KeyCode == Keys.U)
            {
                key.Handled = true;
                UpdateApplicationAsync(this, EventArgs.Empty);
            }
            if (_diagnosticsAllowed && key.Control && key.Shift && key.KeyCode == Keys.D)
            {
                key.Handled = true;
                SaveDiagnosticsAuthorized(this, EventArgs.Empty);
            }
        };

        // One compact popup sourced from the actual Chrome extension layout.
        BuildCompactPopup();

        // Turn on Windows-login startup on the first app launch ONLY.
        // This creates a one-time preference marker so a user who disables
        // autostart will never be silently re-enrolled by an app update.
        WindowsLaunchSettings.EnsureFirstLaunchDefault(Application.ExecutablePath);
        var menu = new ContextMenuStrip();
        menu.Items.Add("Открыть CELIKOM", null, (_, _) => ShowMain());
        menu.Items.Add("Остановить подмену", null, (_, _) => StopPlaybackExplicitly());
        menu.Items.Add(new ToolStripSeparator());
        var launchWithWindows = new ToolStripMenuItem();
        void SyncAutorunMenu()
        {
            var enabled = WindowsLaunchSettings.IsRunAtLoginEnabled(Application.ExecutablePath);
            launchWithWindows.Checked = enabled;
            launchWithWindows.Text = enabled
                ? "Отключить запуск с Windows"
                : "Включить запуск с Windows";
        }
        SyncAutorunMenu();
        menu.Opening += (_, _) => SyncAutorunMenu();
        launchWithWindows.Click += (_, _) =>
        {
            var enable = !WindowsLaunchSettings.IsRunAtLoginEnabled(Application.ExecutablePath);
            if (WindowsLaunchSettings.TrySetRunAtLogin(Application.ExecutablePath, enable))
            {
                SyncAutorunMenu();
                DiagnosticLog.Record(enable ? "WIN_AUTORUN_ENABLED_BY_OWNER" :
                    "WIN_AUTORUN_DISABLED_BY_OWNER");
                if (enable && !_bridge.Enabled) _ = ResumeSavedPlaybackAsync();
            }
            else
                MessageBox.Show(this, "Не удалось изменить автозапуск Windows. Проверь разрешения учётной записи.",
                    "CELIKOM", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        };
        menu.Items.Add(launchWithWindows);
        menu.Items.Add("Выход", null, (_, _) => Close());
        _tray = new NotifyIcon
        {
            Icon = Icon, ContextMenuStrip = menu,
            Visible = true, Text = "CELIKOM — выключено"
        };
        _tray.DoubleClick += (_, _) => ShowMain();
        Resize += (_, _) => { if (WindowState == FormWindowState.Minimized) Hide(); };
        _entitlementPulse.Tick += (_, _) =>
        {
            if (!_closing && (_bridge.Enabled || _resumeAfterNetworkFailure) && _api.IsLoggedIn)
                _ = RefreshCompactAccessAsync(force: true);
            // Yandex's own updater can replace an ACTIVE native pair while
            // CELIKOM stays in the tray. Detect it without touching vendor files.
            if (!_closing && !_integrationBusy && !_hostProbeBusy &&
                DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
                _ = RefreshHostAsync();
            // Background reconnect only if the owner previously requested
            // playback, opted into autorun and has fresh server entitlement.
            if (!_closing && !_integrationBusy && !_autoReconnectBusy &&
                !_bridge.Enabled && _api.IsLoggedIn &&
                DateTimeOffset.UtcNow - _autoReconnectLastAttempt > TimeSpan.FromMinutes(2) &&
                WindowsLaunchSettings.MayResume(_api.Settings, Application.ExecutablePath))
                _ = ResumeSavedPlaybackAsync();
        };
        _yandexVersionDebounce.Tick += async (_, _) =>
        {
            _yandexVersionDebounce.Stop();
            if (!_closing && !_integrationBusy)
                await RefreshHostAsync();
        };
        FormClosing += ClosingAsync;
        Shown += async (_, _) =>
        {
            RenderCompact();
            LayoutCompact();
            InitializeYandexInstallWatcher();
            if (_backgroundStartup)
            {
                // Zero visible loading window on OS sign-in; the tray still
                // initializes and handles remote Yandex launch later.
                Hide();
                Opacity = 1;
            }
            else
            {
                // Reveal only after a complete first layout; prevents the
                // owner-observed flash of empty unpainted UI squares.
                BeginInvoke(new Action(() => { if (!IsDisposed) Opacity = 1; }));
            }
            await StartBridgeAsync();
            _entitlementPulse.Start();
            await RefreshHostAsync();
            if (_finishApplicationUpdate) await CompleteApplicationUpdateAsync();
            if (_api.IsLoggedIn)
            {
                await RefreshDiagnosticsAccessAsync();
                await RefreshCompactAccessAsync(force: true);
            }
            if (_backgroundStartup)
                await ResumeSavedPlaybackAsync();
        };
        Activated += (_, _) =>
        {
            if (DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
                _ = RefreshHostAsync();
            if (_api.IsLoggedIn) _ = RefreshCompactAccessAsync();
        };
        UpdateSafe();
    }

    private void NavigateAccount(bool account)
    {
        if (_compactReady)
        {
            _compactAccountOpen = account;
            LayoutCompact();
            return;
        }
        _accountPanel.Visible = account;
        _homePanel.Visible = !account;
        if (account) _accountPanel.BringToFront();
        else _homePanel.BringToFront();
        UpdateNavigation(account);
    }

    private void UpdateNavigation(bool account)
    {
        _accountTab.BackColor = !_api.IsLoggedIn ? Danger : (account ? Accent : Surface);
        _accountTab.ForeColor = !_api.IsLoggedIn ? Color.White : (account ? AccentInk : Ink);
        _homeTab.BackColor = account ? Surface : Accent;
        _homeTab.ForeColor = account ? Ink : AccentInk;
        _accountTab.Invalidate();
        _homeTab.Invalidate();
    }

    private static TableLayoutPanel PageLayout(Control page)
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 0,
            Padding = new Padding(18, 18, 18, 9),
            BackColor = Paper,
            AutoScroll = false
        };
        root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        page.Controls.Add(root);
        return root;
    }

    private static void Add(TableLayoutPanel layout, Control control, int height)
    {
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, height));
        layout.RowCount++;
        control.Dock = DockStyle.Fill;
        control.Margin = new Padding(0, 2, 0, 3);
        layout.Controls.Add(control, 0, layout.RowCount - 1);
    }

    private static Label Label(string text, int font = 10, bool bold = false, Color? color = null) =>
        new()
        {
            Text = text, TextAlign = ContentAlignment.MiddleLeft,
            Font = new Font("Segoe UI", font, bold ? FontStyle.Bold : FontStyle.Regular),
            ForeColor = color ?? Ink,
            BackColor = Paper,
            AutoEllipsis = true
        };

    private static Button Button(string caption, bool primary)
    {
        var btn = new PopupButton
        {
            Text = caption, FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            BackColor = primary ? Accent : Surface,
            ForeColor = primary ? AccentInk : Ink,
            Cursor = Cursors.Hand, UseVisualStyleBackColor = false
        };
        btn.FlatAppearance.BorderSize = 1;
        btn.FlatAppearance.BorderColor = primary ? Accent : Border;
        return btn;
    }

    private void BuildHome(Control page)
    {
        var layout = PageLayout(page);
        Add(layout, Label("Управление музыкой", 12, true), 42);
        _status.ForeColor = Secondary;
        _status.Font = new Font("Segoe UI", 10F);
        _status.AutoEllipsis = false;
        Add(layout, _status, 49);

        var actions = new TableLayoutPanel
        {
            ColumnCount = 2, RowCount = 1, Dock = DockStyle.Fill,
            Margin = Padding.Empty
        };
        actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        ConfigureAuthButton(_start, true, "Старт");
        ConfigureAuthButton(_stop, false, "Стоп");
        _start.Margin = new Padding(0, 2, 5, 2);
        _stop.Margin = new Padding(5, 2, 0, 2);
        _start.Click += StartAction;
        _stop.Click += (_, _) => StopPlaybackExplicitly();
        actions.Controls.Add(_start, 0, 0);
        actions.Controls.Add(_stop, 1, 0);
        Add(layout, actions, 54);

        _switchHint.ForeColor = Secondary;
        _switchHint.Font = new Font("Segoe UI", 9F);
        _switchHint.AutoEllipsis = false;
        Add(layout, _switchHint, 54);
        _song.ForeColor = Secondary;
        _song.Font = new Font("Segoe UI", 9F);
        _song.AutoEllipsis = false;
        Add(layout, _song, 52);

        // Only a verified developer identity sees a diagnostic export button.
        _staffPanel.Dock = DockStyle.Bottom;
        _staffPanel.Height = 57;
        _staffPanel.Padding = new Padding(18, 4, 18, 4);
        _staffPanel.BackColor = Paper;
        _staffPanel.Visible = false;
        ConfigureAuthButton(_diagnosticsButton, false, "Диагностика");
        _diagnosticsButton.Click += SaveDiagnosticsAuthorized;
        _staffPanel.Controls.Add(_diagnosticsButton);
        page.Controls.Add(_staffPanel);
        _staffPanel.BringToFront();
    }

    private void BuildAccount(Control page)
    {
        _accountSignedOut.Dock = DockStyle.Fill;
        _accountSignedIn.Dock = DockStyle.Fill;
        _accountSignedOut.BackColor = Paper;
        _accountSignedIn.BackColor = Paper;
        page.Controls.Add(_accountSignedIn);
        page.Controls.Add(_accountSignedOut);

        var layout = PageLayout(_accountSignedOut);
        Add(layout, Label("Войти в CELIKOM", 13, true), 48);
        Add(layout, Label("Email", 9, false, Secondary), 30);
        _email.Text = _api.Email;
        _email.PlaceholderText = "Электронная почта";
        Add(layout, new PopupInput(_email), 51);
        Add(layout, new Panel { BackColor = Paper }, 13);
        Add(layout, Label("Пароль", 9, false, Secondary), 30);
        _password.UseSystemPasswordChar = true;
        _password.PlaceholderText = "Пароль";
        Add(layout, new PopupInput(_password), 51);
        Add(layout, new Panel { BackColor = Paper }, 18);
        ConfigureAuthButton(_login, true, "Войти");
        _login.Click += LoginAsync;
        Add(layout, _login, 52);
        _accountStatus.ForeColor = Danger;
        _accountStatus.Font = new Font("Segoe UI", 9F);
        _accountStatus.AutoEllipsis = false;
        _accountStatus.Text = "Войди в аккаунт, чтобы включить CELIKOM.";
        Add(layout, _accountStatus, 64);

        var signed = PageLayout(_accountSignedIn);
        Add(signed, Label("Аккаунт CELIKOM", 13, true), 49);
        _signedInIdentity.ForeColor = Accent;
        _signedInIdentity.Font = new Font("Segoe UI", 10F);
        _signedInIdentity.AutoEllipsis = true;
        Add(signed, _signedInIdentity, 49);
        Add(signed, new Panel { BackColor = Paper }, 18);
        ConfigureAuthButton(_logout, false, "Выйти из аккаунта");
        _logout.Click += LogoutAsync;
        Add(signed, _logout, 51);

        // Preserve encrypted origin for upgrades; default to shipped service.
        _origin.Text = string.IsNullOrWhiteSpace(_api.Origin) ? DefaultApiOrigin : _api.Origin;
        _accountSignedOut.Visible = !_api.IsLoggedIn;
        _accountSignedIn.Visible = _api.IsLoggedIn;
    }

    // Connectivity signals are hints only. Revalidate suspended music after
    // a VPN/adapter change, but never enable playback from an online event.
    private void OnNetworkAddressChanged(object? sender, EventArgs e)
    {
        if (_closing || !IsHandleCreated) return;
        try
        {
            BeginInvoke(new Action(() =>
            {
                // Detect route changes while CELIKOM is still playing, not
                // only AFTER the old VPN's 9s timeout suspended the bridge.
                if (_closing || IsDisposed || !_api.IsLoggedIn ||
                    !(_bridge.Enabled || _resumeAfterNetworkFailure)) return;
                var now = DateTimeOffset.UtcNow;
                // A VPN switch emits multiple addresses within milliseconds.
                // Never DROP the last signal; only throttle the log line.
                var shouldLog = NetworkRouteBurstPolicy.LogDue(now, _lastNetworkRouteLoggedAt);
                _lastNetworkRecheckHint = now;
                _networkRouteRecheckPending = true;
                var routeEpoch = _networkRouteEpoch =
                    NetworkRouteBurstPolicy.NextEpoch(_networkRouteEpoch);
                if (shouldLog)
                {
                    _lastNetworkRouteLoggedAt = now;
                    DiagnosticLog.Record("ACTIVE_ENTITLEMENT_ROUTE_CHANGED");
                }
                // Abandon a GET attached to the old VPN; a fresh server
                // response on the new route is still mandatory.
                _compactAccessRequestCancellation?.Cancel();
                _ = RecheckAfterRouteSettledAsync(routeEpoch);
            }));
        }
        catch (InvalidOperationException) { } // includes disposed handle
    }

    private async Task RecheckAfterRouteSettledAsync(int epoch)
    {
        await Task.Delay(750);
        if (!NetworkRouteBurstPolicy.Latest(epoch, _networkRouteEpoch) ||
            _closing || IsDisposed) return;
        if (!_api.IsLoggedIn || !(_bridge.Enabled || _resumeAfterNetworkFailure))
        {
            _networkRouteRecheckPending = false;
            return;
        }
        if (_compactAccessBusy) return; // in-flight finally will retry
        if (!_networkRouteRecheckPending) return;
        _networkRouteRecheckPending = false;
        await RefreshCompactAccessAsync(force: true);
    }

    private void StopPlaybackExplicitly()
    {
        // User Stop ALWAYS overrides any automatic reconnect intent.
        _networkRouteRecheckPending = false;
        _networkRouteEpoch = NetworkRouteBurstPolicy.NextEpoch(_networkRouteEpoch);
        _compactAccessRequestCancellation?.Cancel();
        _resumeAfterNetworkFailure = false;
        ++_compactAccessGeneration; // discard a just-finished stale pulse
        ++_compactStartEpoch;
        _compactStarting = false;
        _bridge.SetEnabled(false);
        WindowsLaunchSettings.RememberPlayback(_api.Settings, enabled: false);
        DiagnosticLog.Record("ACTIVE_ENTITLEMENT_MANUAL_STOP");
    }

    private async void StartAction(object? sender, EventArgs e)
    {
        if (!_bridgeStarted || _integrationBusy || _compactStarting || _closing) return;
        if (!_api.IsLoggedIn)
        {
            _compactAccountOpen = true;
            _compactAccountMessage.Text = "Войди в аккаунт, чтобы включить CELIKOM.";
            LayoutCompact();
            ScrollCompactTo(_compactAccountTrigger);
            return;
        }
        _resumeAfterNetworkFailure = false;
        ++_compactAccessGeneration; // user action wins over any outstanding poll
        // Every Start, including a later reinstall or expired subscription,
        // requires live server authority. Never infer playback entitlement
        // from the presence of stored DPAPI tokens or the account UI.
        var generation = ++_compactStartEpoch;
        var account = _api.Settings;
        bool StillSameStart() => generation == _compactStartEpoch && !_closing &&
            !IsDisposed && _api.IsLoggedIn &&
            _api.Settings.InstallationId == account.InstallationId &&
            _api.Settings.Email == account.Email;
        _compactStarting = true;
        _compactStartupText = "Проверяем Яндекс.Музыку…";
        RenderCompact();
        LayoutCompact();
        try
        {
            // Shown/Activated may still be scanning Yandex. Join that exact
            // in-flight check before deciding "unsupported" or calling the API.
            if (_hostReport is null || _hostProbeBusy ||
                DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
            {
                await RefreshHostAsync();
                if (!StillSameStart()) return;
            }
            if (StartupHostPreflight.BlockReason(_nativeInstallState, _hostReport) is
                { } hostProblem)
            {
                _compactStarting = false;
                _compactStartupText = hostProblem;
                DiagnosticLog.Record("START_HOST_PREFLIGHT_BLOCKED");
                return;
            }

            _compactStartupText = "Проверяем пробный период или подписку…";
            RenderCompact();
            LayoutCompact();
            var access = await StartupActivationRecovery.ActivateAsync(
                ct => _api.ActivatePlaybackAsync(ct), StillSameStart,
                code => DiagnosticLog.Record(code));
            if (!StillSameStart()) return;
            ++_compactAccessGeneration; // invalidate an older read-only preview
            _compactAccessConfirmedInstallation = account.InstallationId;
            _compactAccessConfirmedEmail = account.Email;
            SetCompactAccessText(AccessLabel(access));
            _compactAccessChecked = DateTimeOffset.UtcNow;
            if (!PlaybackEntitlement.Allowed(access, DateTimeOffset.UtcNow))
            {
                _bridge.SetEnabled(false);
                _compactStarting = false;
                _compactStartupText = "Доступ завершён. Активируй промокод или подписку.";
                DiagnosticLog.Record("START_ENTITLEMENT_DENIED");
                return;
            }
            if (_nativeInstallState != NativeInstallState.Active ||
                !_installedModule.MatchesApplication)
            {
                _compactStarting = false;
                _compactStartupText = "";
                await ConnectYandexAsync(sender, e);
                return;
            }
            if (!OpenYandexIfNeeded())
            {
                _compactStarting = false;
                _compactStartupText = "";
                return;
            }
            _bridge.SetEnabled(true);
            WindowsLaunchSettings.RememberPlayback(account, enabled: true);
            _compactStarting = true;
            _compactStartupText = "Подождите, идёт загрузка Яндекс.Музыки…";
            _ = MonitorStartupAsync(generation);
        }
        catch (Exception error)
        {
            if (!StillSameStart()) return;
            _bridge.SetEnabled(false);
            _compactStarting = false;
            // A failed transport/timeout is NOT evidence that the user's
            // subscription was denied or that the server is down.
            _compactStartupText = error switch
            {
                ApiFailure { HttpStatus: 401 } => "Сессия устарела. Войди в аккаунт повторно.",
                ApiFailure { HttpStatus: 403 } => "Сервер не разрешил доступ. Проверь подписку.",
                ApiFailure { HttpStatus: 429 } => "Слишком много запросов. Повтори чуть позже.",
                _ when EntitlementCheckRecovery.IsTransient(error) =>
                    "Не удалось установить связь. Подмена выключена — повтори «Старт».",
                _ => "Не удалось подтвердить доступ. Подмена выключена."
            };
            DiagnosticLog.Record(EntitlementCheckRecovery.FailureCode(error));
            DiagnosticLog.Record("START_ENTITLEMENT_UNAVAILABLE");
        }
        finally
        {
            if (generation == _compactStartEpoch && !_closing && !IsDisposed)
            {
                RenderCompact();
                LayoutCompact();
                UpdateSafe();
            }
        }
    }

    private bool OpenYandexIfNeeded()
    {
        try
        {
            if (Process.GetProcessesByName("Яндекс Музыка").Length != 0) return true;
        }
        catch { /* Try normal launch. */ }

        // A manual Start is already explicit consent to open the normal
        // official Yandex window after a successful entitlement check.
        try
        {
            var exe = Path.Combine(NativeIntegrationManager.DefaultYandexDirectory,
                "Яндекс Музыка.exe");
            if (File.Exists(exe))
                Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true });
            else
                Process.Start(new ProcessStartInfo("yandexmusic://") { UseShellExecute = true });
            return true;
        }
        catch
        {
            _compactStartupText = "Не удалось открыть Яндекс. Попробуй запустить его вручную.";
            RenderCompact();
            LayoutCompact();
            return false;
        }
    }

    private async Task MonitorStartupAsync(int generation)
    {
        // The Yandex application may genuinely need time to initialize its
        // Electron renderer. Show bounded guidance, never fake percentages.
        await Task.Delay(TimeSpan.FromSeconds(22));
        if (generation != _compactStartEpoch || _closing || !_compactStarting ||
            !_bridge.Enabled || IsDisposed) return;
        _compactStarting = false;
        _compactStartupText = "Яндекс запускается дольше обычного. Проверь его окно.";
        // Only a missing native handshake merits a forced Yandex version
        // recheck. Normal original playback and per-track source errors do not.
        if (YandexFailureRecheckGate.IsMissingStartupHandshake(_bridge.LastStatus))
            _ = RecheckYandexAfterNativeFailureAsync("YANDEX_NATIVE_START_TIMEOUT");
        RenderCompact();
        LayoutCompact();
    }

    private async Task RefreshDiagnosticsAccessAsync()
    {
        var generation = ++_diagnosticsEpoch;
        var account = _api.Settings;
        if (!_api.IsLoggedIn)
        {
            RevokeDiagnosticsVisibility();
            LayoutCompact();
            return;
        }
        // Do not hide an already authenticated owner's button just because
        // a new permission check is still in flight (VPN reconnect race).
        if (!DiagnosticsVerificationStillCurrent()) RevokeDiagnosticsVisibility();
        bool allowed;
        try { allowed = await _api.CanExportDiagnosticsAsync(); }
        catch (Exception error)
        {
            if (generation != _diagnosticsEpoch || !_api.IsLoggedIn ||
                _api.Settings.InstallationId != account.InstallationId ||
                _api.Settings.Origin != account.Origin ||
                !string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase))
                return;
            if (DiagnosticsAccessRecovery.KeepButtonOnFailure(
                _diagnosticsAllowed, _api.IsLoggedIn,
                _diagnosticsVerifiedOrigin, _diagnosticsVerifiedInstallation,
                _diagnosticsVerifiedEmail,
                account.Origin, account.InstallationId, account.Email, error))
            {
                // This preserves only UI visibility. Export still requires a
                // successful fresh online identity check on each click.
                DiagnosticLog.Record("DIAGNOSTICS_ACCESS_CHECK_DEFERRED");
                return;
            }
            allowed = false;
        }
        if (generation != _diagnosticsEpoch || !_api.IsLoggedIn ||
            _api.Settings.InstallationId != account.InstallationId ||
            _api.Settings.Origin != account.Origin ||
            !string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase))
            return;
        if (allowed)
        {
            _diagnosticsAllowed = true;
            _diagnosticsVerifiedOrigin = account.Origin;
            _diagnosticsVerifiedInstallation = account.InstallationId;
            _diagnosticsVerifiedEmail = account.Email;
            _staffPanel.Visible = true;
        }
        else RevokeDiagnosticsVisibility(); // genuine server rejection
        LayoutCompact();
    }

    private async void SaveDiagnosticsAuthorized(object? sender, EventArgs e)
    {
        // Owner shortcut: never export using a stale local grant.
        if (!DiagnosticsVerificationStillCurrent()) return;
        var account = _api.Settings;
        bool allowed;
        try { allowed = await _api.CanExportDiagnosticsAsync(); }
        catch (Exception error)
        {
            if (DiagnosticsAccessRecovery.KeepButtonOnFailure(
                DiagnosticsVerificationStillCurrent(), _api.IsLoggedIn,
                _diagnosticsVerifiedOrigin, _diagnosticsVerifiedInstallation,
                _diagnosticsVerifiedEmail,
                account.Origin, account.InstallationId, account.Email, error))
            {
                DiagnosticLog.Record("DIAGNOSTICS_EXPORT_CHECK_DEFERRED");
                return;
            }
            allowed = false;
        }
        if (!DiagnosticsVerificationStillCurrent() ||
            _api.Settings.InstallationId != account.InstallationId ||
            _api.Settings.Origin != account.Origin ||
            !string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase))
            return;
        if (!allowed)
        {
            RevokeDiagnosticsVisibility();
            LayoutCompact();
            return;
        }
        SaveDiagnostics();
    }

    private async void CopyDiagnosticsAuthorized(object? sender, EventArgs e)
    {
        // Only the same previously verified owner may attempt a new check.
        if (!DiagnosticsVerificationStillCurrent()) return;
        var account = _api.Settings;
        bool allowed;
        try { allowed = await _api.CanExportDiagnosticsAsync(); }
        catch (Exception error)
        {
            if (DiagnosticsAccessRecovery.KeepButtonOnFailure(
                DiagnosticsVerificationStillCurrent(), _api.IsLoggedIn,
                _diagnosticsVerifiedOrigin, _diagnosticsVerifiedInstallation,
                _diagnosticsVerifiedEmail,
                account.Origin, account.InstallationId, account.Email, error))
            {
                DiagnosticLog.Record("DIAGNOSTICS_EXPORT_CHECK_DEFERRED");
                _diagnosticsButton.Text = "Нет связи · повтори";
                await Task.Delay(1600);
                if (DiagnosticsVerificationStillCurrent() && !_diagnosticsButton.IsDisposed)
                    _diagnosticsButton.Text = "Скопировать диагностику";
                return;
            }
            allowed = false;
        }
        if (!DiagnosticsVerificationStillCurrent() ||
            _api.Settings.InstallationId != account.InstallationId ||
            _api.Settings.Origin != account.Origin ||
            !string.Equals(_api.Settings.Email, account.Email, StringComparison.OrdinalIgnoreCase))
            return;
        if (!allowed)
        {
            RevokeDiagnosticsVisibility(); // genuine revoked role / invalid account
            LayoutCompact();
            return;
        }
        try
        {
            var report = DiagnosticLog.ExportText(_hostReport?.Version,
                _nativeInstallState.ToString().ToUpperInvariant(), _bridgeStarted,
                _bridge.Enabled, _api.IsLoggedIn, _installedModule.Version,
                _nativeInstallState == NativeInstallState.Active ?
                    _installedModule.MatchesApplication : null);
            Clipboard.SetText(report);
            _diagnosticsButton.Text = "Скопировано";
            await Task.Delay(1200);
        }
        catch
        {
            _diagnosticsButton.Text = "Не удалось скопировать";
            await Task.Delay(1200);
        }
        finally
        {
            if (!_closing && !_diagnosticsButton.IsDisposed)
                _diagnosticsButton.Text = "Скопировать диагностику";
        }
    }

    private static void ConfigureAuthButton(Button button, bool primary, string text)
    {
        button.Text = text;
        button.Dock = DockStyle.Fill;
        button.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderSize = 1;
        button.FlatAppearance.BorderColor = primary ? Accent : Border;
        button.BackColor = primary ? Accent : Surface;
        button.ForeColor = primary ? AccentInk : Ink;
    }

    private Task RefreshHostAsync()
    {
        if (_closing) return Task.CompletedTask;
        if (_hostProbeTask is { IsCompleted: false } active) return active;
        _hostProbeTask = RefreshHostCoreAsync();
        return _hostProbeTask;
    }

    private async Task RecheckYandexAfterNativeFailureAsync(string reason)
    {
        // One bounded, read-only compatibility lookup. HOST_ERROR and startup
        // silence can have other causes; this does not authorize a new build,
        // restart Yandex, re-enable playback or bypass server entitlement.
        if (_closing || _integrationBusy ||
            !_failureRecheckGate.TryStart(DateTimeOffset.UtcNow)) return;
        DiagnosticLog.Record(reason);
        try
        {
            // Do not let an earlier probe overwrite the result of this forced
            // catalog refresh. The regular 15-minute feed cache is bypassed.
            if (_hostProbeTask is { IsCompleted: false } current)
                await current;
            if (_closing || IsDisposed) return;
            await OfficialYandexCatalog.RefreshAsync(force: true);
            if (_closing || IsDisposed) return;
            await RefreshHostAsync();
            DiagnosticLog.Record("YANDEX_FAILURE_COMPATIBILITY_RECHECK_COMPLETE");
        }
        catch
        {
            // Offline or local inspection failure: keep last verified pins and
            // existing fail-closed state; never turn a probe into an app crash.
            DiagnosticLog.Record("YANDEX_FAILURE_COMPATIBILITY_RECHECK_UNAVAILABLE");
        }
        finally { _failureRecheckGate.Finish(); }
    }

    private void InitializeYandexInstallWatcher()
    {
        var root = YandexHostProbe.DefaultInstallationRoot;
        if (!Directory.Exists(root)) return;
        try
        {
            var watcher = new FileSystemWatcher(root)
            {
                IncludeSubdirectories = true,
                NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite | NotifyFilters.Size,
                Filter = "*",
                EnableRaisingEvents = false
            };
            FileSystemEventHandler changed = (_, e) => QueueYandexVersionProbe(e.FullPath);
            RenamedEventHandler renamed = (_, e) => QueueYandexVersionProbe(e.FullPath);
            watcher.Changed += changed;
            watcher.Created += changed;
            watcher.Deleted += changed;
            watcher.Renamed += renamed;
            watcher.EnableRaisingEvents = true;
            _yandexInstallWatcher = watcher;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or ArgumentException)
        {
            // The existing two-minute host probe remains the safe fallback.
        }
    }

    private void QueueYandexVersionProbe(string changedPath)
    {
        try
        {
            var path = Path.GetFullPath(changedPath);
            var root = YandexHostProbe.DefaultInstallationRoot;
            var executable = Path.Combine(root, "Яндекс Музыка.exe");
            var asar = Path.Combine(root, "resources", "app.asar");
            if (!string.Equals(path, executable, StringComparison.OrdinalIgnoreCase) &&
                !string.Equals(path, asar, StringComparison.OrdinalIgnoreCase))
                return;
            if (IsDisposed || !IsHandleCreated) return;
            BeginInvoke(new Action(() =>
            {
                if (_closing || _integrationBusy) return;
                _yandexVersionDebounce.Stop();
                _yandexVersionDebounce.Start();
            }));
        }
        catch (Exception ex) when (ex is ArgumentException or IOException or InvalidOperationException)
        {
        }
    }

    private async Task RefreshHostCoreAsync()
    {
        _hostProbeBusy = true;
        try
        {
            var previousVersion = _hostReport?.Version ?? "";
            // A reviewed build can become supported without a CELIKOM EXE
            // update; offline failure leaves the shipped 5.127 pins intact.
            await OfficialYandexCatalog.RefreshAsync();
            var wasPlaying = _bridge.Enabled;
            var inspected = await Task.Run(() =>
            {
                var nativeState = NativeIntegrationManager.Inspect();
                return (YandexHostProbe.Inspect(), nativeState,
                    NativeModuleIdentity.Inspect(nativeState));
            });
            if (!string.IsNullOrWhiteSpace(previousVersion) &&
                !string.IsNullOrWhiteSpace(inspected.Item1.Version) &&
                !string.Equals(previousVersion, inspected.Item1.Version, StringComparison.Ordinal))
            {
                // The normal feed cache is 15 minutes; a detected vendor update
                // bypasses it immediately so the exact new EXE/ASAR pair is checked.
                await OfficialYandexCatalog.RefreshAsync(force: true);
                var refreshedHost = await Task.Run(() => YandexHostProbe.Inspect());
                inspected = (refreshedHost, inspected.Item2, inspected.Item3);
            }
            _hostReport = inspected.Item1;
            _nativeInstallState = inspected.Item2;
            _installedModule = inspected.Item3;
            if (wasPlaying && (inspected.Item2 != NativeInstallState.Active ||
                !inspected.Item3.MatchesApplication))
            {
                // Never claim connected when Yandex replaced the native host.
                _bridge.SetEnabled(false);
                _compactStarting = false;
                _resumeAfterNetworkFailure = false;
                ++_compactStartEpoch; // invalidate any old pending Start
                _compactStartupText = inspected.Item2 == NativeInstallState.VerifiedVendorUpdate
                    ? "Яндекс обновился. Нажми «Старт» для безопасного переподключения."
                    : "Яндекс изменился. Подключение остановлено, оригиналы сохранены.";
                DiagnosticLog.Record("YANDEX_VENDOR_UPDATE_DETECTED");
            }
        }
        catch
        {
            _hostReport = new(YandexHostStatus.InspectionUnavailable, "");
            _nativeInstallState = NativeInstallState.Changed;
            _installedModule = NativeModuleIdentity.Unknown;
        }
        finally
        {
            _lastHostProbe = DateTimeOffset.UtcNow;
            _hostProbeBusy = false;
            UpdateSafe();
        }
    }

    private async Task ConnectYandexAsync(object? sender, EventArgs e)
    {
        _resumeAfterNetworkFailure = false;
        if (_integrationBusy) return;
        var upgrading = _nativeInstallState == NativeInstallState.Active;
        // Defense-in-depth: no "unsupported version" modal based on a null or
        // temporarily unavailable scan. StartAction already awaited the probe.
        if (StartupHostPreflight.BlockReason(_nativeInstallState, _hostReport) is
            { } hostProblem)
        {
            _compactStarting = false;
            _compactStartupText = hostProblem;
            RenderCompact();
            LayoutCompact();
            DiagnosticLog.Record("START_HOST_PREFLIGHT_BLOCKED");
            return;
        }
        // Start is the explicit user action. Previously ACTIVE native users
        // can rejoin a newly reviewed official vendor build without being
        // forced through a second modal. RESTORED users still consent once.
        var previouslyApproved = _nativeInstallState == NativeInstallState.VerifiedVendorUpdate &&
            NativeIntegrationManager.IsPreviouslyApprovedVendorUpdate();
        // Manual Start is already consent to refresh a module the same
        // owner previously installed. First installation still asks once.
        if (!previouslyApproved && !upgrading)
        {
            var answer = MessageBox.Show(this,
                "Подключить CELIKOM к Яндекс.Музыке? Оригинальные файлы будут сохранены, Яндекс перезапустится.",
                "Подключение CELIKOM", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (answer != DialogResult.Yes) return;
        }
        else DiagnosticLog.Record("YANDEX_UPDATE_RECONNECT_PRIOR_CONSENT");
        _integrationBusy = true;
        var generation = ++_compactStartEpoch;
        var account = _api.Settings;
        _compactStartupText = "Проверяем пробный период или подписку…";
        RenderCompact();
        LayoutCompact();
        UpdateSafe();
        try
        {
            var access = await _api.ActivatePlaybackAsync();
            if (generation != _compactStartEpoch || _closing || !_api.IsLoggedIn ||
                _api.Settings.InstallationId != account.InstallationId ||
                _api.Settings.Email != account.Email) return;
            if (!PlaybackEntitlement.Allowed(access, DateTimeOffset.UtcNow))
            {
                _bridge.SetEnabled(false);
                _compactStarting = false;
                _compactStartupText = "Нет действующей подписки или пробного периода.";
                DiagnosticLog.Record("NATIVE_INSTALL_ENTITLEMENT_DENIED");
                return;
            }
            _compactStartupText = "Подождите, идёт загрузка Яндекс.Музыки…";
            RenderCompact();
            LayoutCompact();
            DiagnosticLog.Record(upgrading ? "NATIVE_UPGRADE_REQUEST" : "NATIVE_INSTALL_REQUEST");
            _bridge.SetEnabled(false);
            if (upgrading)
            {
                // Do not remove the still-working native pair before verifying
                // the complete replacement and its recoverable previous image.
                await Task.Run(() => NativeIntegrationManager.Upgrade());
                DiagnosticLog.Record("NATIVE_UPGRADE_OK");
            }
            else
            {
                await Task.Run(() => NativeIntegrationManager.Install());
                DiagnosticLog.Record("NATIVE_INSTALL_OK");
            }
            // Verify again after a long native install. Expiry, logout, Stop,
            // account switch or network failure must not enable playback.
            var allowedNow = false;
            if (generation == _compactStartEpoch && !_closing && _api.IsLoggedIn &&
                _api.Settings.InstallationId == account.InstallationId &&
                _api.Settings.Email == account.Email)
            {
                try {
                    var refreshed = await _api.GetEntitlementAsync();
                    allowedNow = PlaybackEntitlement.Allowed(refreshed, DateTimeOffset.UtcNow);
                } catch { DiagnosticLog.Record("NATIVE_INSTALL_ENTITLEMENT_RECHECK_FAILED"); }
            }
            _bridge.SetEnabled(allowedNow);
            if (allowedNow) WindowsLaunchSettings.RememberPlayback(account, enabled: true);
            _compactStartupText = allowedNow
                ? "Подождите, идёт загрузка Яндекс.Музыки…"
                : "Доступ не подтверждён. Нажми «Старт» после проверки подписки.";
            _compactStarting = allowedNow;
            if (allowedNow) _ = MonitorStartupAsync(generation);
            _hostStatus.Text = "CELIKOM подключён к Яндексу.";
            if (!allowedNow) return;
            try
            {
                var exe = Path.Combine(NativeIntegrationManager.DefaultYandexDirectory,
                    "Яндекс Музыка.exe");
                Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true });
            }
            catch { /* Connected files verified; user may open Yandex normally. */ }
        }
        catch (ApiFailure)
        {
            _bridge.SetEnabled(false);
            _compactStarting = false;
            _compactStartupText = "Не удалось проверить доступ. Яндекс не изменён.";
            DiagnosticLog.Record("NATIVE_INSTALL_ENTITLEMENT_UNAVAILABLE");
        }
        catch (Exception error)
        {
            DiagnosticLog.Record(upgrading ? "NATIVE_UPGRADE_FAILED" : "NATIVE_INSTALL_FAILED");
            ++_compactStartEpoch;
            _compactStarting = false;
            _compactStartupText = "Не удалось подключить Яндекс.Музыку.";
            MessageBox.Show(this, DescribeIntegrationFailure(error), "CELIKOM",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            _integrationBusy = false;
            RenderCompact();
            LayoutCompact();
            await RefreshHostAsync();
            UpdateSafe();
        }
    }

    private async void RestoreYandexAsync(object? sender, EventArgs e)
    {
        if (_integrationBusy) return;
        var answer = MessageBox.Show(this,
            "Отключить CELIKOM и вернуть оригинальные файлы Яндекс.Музыки?",
            "Восстановить Яндекс", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes) return;
        _integrationBusy = true;
        _bridge.SetEnabled(false);
        UpdateSafe();
        try
        {
            DiagnosticLog.Record("NATIVE_RESTORE_REQUEST");
            await Task.Run(() => NativeIntegrationManager.Restore());
            DiagnosticLog.Record("NATIVE_RESTORE_OK");
            WindowsLaunchSettings.RememberPlayback(_api.Settings, enabled: false);
            _hostStatus.Text = "Оригинальная Яндекс.Музыка восстановлена.";
        }
        catch (Exception error)
        {
            MessageBox.Show(this, DescribeIntegrationFailure(error), "CELIKOM",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            _integrationBusy = false;
            await RefreshHostAsync();
            UpdateSafe();
        }
    }

    private void SaveDiagnostics()
    {
        DiagnosticLog.Record("EXPORT_REQUEST");
        using var save = new SaveFileDialog
        {
            Title = "Скачать диагностику CELIKOM",
            Filter = "Текстовый файл (*.txt)|*.txt",
            FileName = "CELIKOM-diagnostics-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".txt",
            AddExtension = true,
            DefaultExt = "txt",
            OverwritePrompt = true,
            RestoreDirectory = true
        };
        if (save.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            var snapshot = DiagnosticLog.ExportText(_hostReport?.Version,
                _nativeInstallState.ToString().ToUpperInvariant(), _bridgeStarted,
                _bridge.Enabled, _api.IsLoggedIn, _installedModule.Version,
                _nativeInstallState == NativeInstallState.Active ? _installedModule.MatchesApplication : null);
            File.WriteAllText(save.FileName, snapshot, System.Text.Encoding.UTF8);
            DiagnosticLog.Record("EXPORT_SAVED");
            MessageBox.Show(this, "Диагностика сохранена. Пришли этот TXT в чат.", "CELIKOM");
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            DiagnosticLog.Record("EXPORT_FAILED");
            MessageBox.Show(this, "Не удалось сохранить файл. Выбери другую папку.", "CELIKOM");
        }
    }

    private async void UpdateApplicationAsync(object? sender, EventArgs e)
    {
        if (_updatingApplication || _integrationBusy) return;
        using var picker = new OpenFileDialog
        {
            Title = "Выбери скачанный ZIP CELIKOM (или установщик EXE)",
            Filter = "Обновление CELIKOM (*.zip;*.exe)|*.zip;*.exe",
            Multiselect = false,
            CheckFileExists = true,
            RestoreDirectory = true
        };
        if (picker.ShowDialog(this) != DialogResult.OK) return;

        _updatingApplication = true;
        UpdateSafe();
        AppUpdateManager.StagedInstaller? staged = null;
        try
        {
            DiagnosticLog.Record("APP_UPDATE_FILE_SELECTED");
            staged = await Task.Run(() =>
                AppUpdateManager.Stage(picker.FileName, AppUpdateManager.RunningVersion));
            var agree = MessageBox.Show(this,
                "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3) +
                " → " + staged.Version.ToString(3) + "\n\n" +
                "Обновим ЭТО ЖЕ приложение в Windows, без удаления и нового входа. " +
                "Затем проверим и при необходимости обновим модуль внутри Яндекса. " +
                "Яндекс может перезапуститься.\n\n" +
                "Используй только ZIP, скачанный из нашего GitHub (сборки пока без цифровой подписи).",
                "Обновить CELIKOM",
                MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (agree != DialogResult.Yes) return;
            AppUpdateManager.MarkPending(staged.Version);
            AppUpdateManager.Launch(staged);
            DiagnosticLog.Record("APP_UPDATE_INSTALLER_LAUNCHED");
            Close();
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
            System.IO.InvalidDataException or System.ComponentModel.Win32Exception or
            InvalidOperationException or ArgumentException)
        {
            DiagnosticLog.Record("APP_UPDATE_FAILED");
            var message = ex.Message switch
            {
                "UPDATE_NOT_NEWER" => "Этот ZIP содержит старую или уже установленную версию. Скачай более новую.",
                "UPDATE_NOT_CELIKOM" => "Файл не похож на подходящий установщик CELIKOM. Обновление остановлено.",
                "UPDATE_PACKAGE_INVALID" or "UPDATE_FILE_INVALID" =>
                    "Выбери ZIP с одним установщиком CELIKOM, скачанный из нашего GitHub.",
                _ => "Обновление не запустилось. CELIKOM остался без изменений."
            };
            MessageBox.Show(this, message, "CELIKOM", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            _updatingApplication = false;
            if (!_closing) UpdateSafe();
        }
    }

    // This path is authorized ONLY by a 20-minute, one-use ticket from the
    // previous running CELIKOM that launched the installer after owner consent.
    private async Task CompleteApplicationUpdateAsync()
    {
        if (!AppUpdateManager.TryConsumePending(AppUpdateManager.RunningVersion)) return;
        DiagnosticLog.Record("APP_UPDATE_COMPLETED");
        if (_nativeInstallState != NativeInstallState.Active || _installedModule.MatchesApplication)
            return;
        _integrationBusy = true;
        UpdateSafe();
        try
        {
            _bridge.SetEnabled(false);
            await Task.Run(() =>
            {
                NativeIntegrationManager.Upgrade();
            });
            DiagnosticLog.Record("APP_UPDATE_NATIVE_REFRESH_OK");
            // An upgrade must not restart native playback from a locally
            // remembered login. The owner presses Start for a fresh check.
            _bridge.SetEnabled(false);
            var exe = Path.Combine(NativeIntegrationManager.DefaultYandexDirectory, "Яндекс Музыка.exe");
            try { Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true }); }
            catch { /* Owner can open Yandex normally. */ }
        }
        catch (Exception error)
        {
            DiagnosticLog.Record("APP_UPDATE_NATIVE_REFRESH_FAILED");
            MessageBox.Show(this,
                "CELIKOM обновился, но подключение к Яндексу нужно завершить. " +
                DescribeIntegrationFailure(error) + "\nНажми «Старт», чтобы повторить.",
                "Обновление CELIKOM", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            _integrationBusy = false;
            await RefreshHostAsync();
            UpdateSafe();
        }
    }

    private static string DescribeIntegrationFailure(Exception error) => error.Message switch
    {
        "CLOSE_YANDEX_AND_TRY_AGAIN" => "Закрой Яндекс.Музыку и повтори действие.",
        "UNSUPPORTED_YANDEX_VERSION" or "UNSUPPORTED_ASAR_VERSION" or
        "UNSUPPORTED_YANDEX_BUILD" =>
            "Текущая сборка Яндекс.Музыки не совпадает с проверенной официальной версией.",
        "CELIKOM_NATIVE_MODULE_NOT_INSTALLED" =>
            "Модуль интеграции не найден. Установи полную сборку CELIKOM.",
        "YANDEX_UPDATED_OR_BACKUP_CHANGED" or "YANDEX_FILES_DIFFER_FROM_KNOWN_BACKUP" =>
            "Файлы Яндекс.Музыки изменились. CELIKOM не будет перезаписывать их вслепую.",
        "PREVIOUS_INSTALL_INTERRUPTED_RESTORE_FIRST" =>
            "Предыдущая установка прервалась. Сначала восстанови оригинал.",
        "UPGRADE_REQUIRES_ACTIVE_PATCH" or "YANDEX_CHANGED_DURING_UPGRADE_PREFLIGHT" or
        "HOST_UPDATED_DURING_UPGRADE_NO_AUTOREPAIR" =>
            "Яндекс обновился или изменил файлы. Сохранённые копии не тронуты; автоматическое восстановление остановлено.",
        _ => "Подключение не завершено. Файлы Яндекса не следует менять вручную."
    };

    private async Task StartBridgeAsync()
    {
        try
        {
            DiagnosticLog.Record("GUI_STARTED");
            await _bridge.StartAsync();
            _nativeToken = new NativeTokenPublisher();
            _nativeToken.Publish(_api.Settings.BridgeToken);
            _bridgeStarted = true;
            UpdateSafe();
        }
        catch
        {
            _bridgeStarted = false;
            _nativeToken?.Dispose();
            _nativeToken = null;
            _status.Text = "Локальная служба недоступна. Закрой другие копии CELIKOM.";
            _accountStatus.Text = "Не удалось запустить службу CELIKOM.";
            _start.Enabled = false;
            _stop.Enabled = false;
        }
    }

    private async void LoginAsync(object? sender, EventArgs e)
    {
        if (_loggingIn) return;
        _resumeAfterNetworkFailure = false;
        ++_compactAccessGeneration;
        ClearCompactAccessConfirmation();
        _loggingIn = true;
        ++_compactStartEpoch;
        _compactStarting = false;
        _login.Enabled = false;
        _bridge.SetEnabled(false);
        try
        {
            await _api.LoginAsync(_origin.Text.Trim(), _email.Text.Trim(), _password.Text);
            DiagnosticLog.Record("LOGIN_OK");
            _password.Clear();
            _accountStatus.Text = "";
            NavigateAccount(false);
            await RefreshDiagnosticsAccessAsync();
        }
        catch (ApiFailure e2)
        {
            DiagnosticLog.Record("LOGIN_FAILED");
            _accountStatus.Text = e2.Category switch
            {
                "INVALID_CREDENTIALS" => "Неверная почта или пароль.",
                "EMAIL_VERIFICATION_REQUIRED" => "Сначала подтверди почту в CELIKOM.",
                "RATE_LIMITED" => "Слишком много попыток входа.",
                _ => "Не удалось войти. Проверь подключение к интернету."
            };
        }
        catch (Exception) { _accountStatus.Text = "Не удалось войти. Проверь интернет."; }
        finally
        {
            _loggingIn = false;
            UpdateSafe(preserveAccountStatus: true);
        }
    }

    private async void LogoutAsync(object? sender, EventArgs e)
    {
        _resumeAfterNetworkFailure = false;
        ++_compactStartEpoch;
        _compactStarting = false;
        _bridge.SetEnabled(false);
        WindowsLaunchSettings.RememberPlayback(_api.Settings, enabled: false);
        ++_diagnosticsEpoch;
        RevokeDiagnosticsVisibility();
        _logout.Enabled = false;
        try { await _api.LogoutAsync(); DiagnosticLog.Record("LOGOUT_OK"); _accountStatus.Text = ""; }
        catch { _accountStatus.Text = "Не удалось завершить выход. Проверь подключение."; }
        finally
        {
            ++_compactAccessGeneration;
            ClearCompactAccessConfirmation();
            SetCompactAccessText("Войдите в аккаунт, чтобы начать");
            _compactPromoOpen = false;
            ResetCompactBenefits();
            _compactAccountMode = "login";
            UpdateSafe(preserveAccountStatus: true);
            NavigateAccount(true);
        }
    }

    private void UpdateSafe(bool preserveAccountStatus = false)
    {
        if (_closing || IsDisposed) return;
        if (InvokeRequired)
        {
            if (IsHandleCreated) BeginInvoke(new Action(() => UpdateSafe(preserveAccountStatus)));
            return;
        }

        // Match the extension's prompt recovery without polling the healthy
        // service more often. Network outages never grant offline playback.
        var pollInterval = EntitlementCheckRecovery.PollIntervalMs(
            _resumeAfterNetworkFailure);
        if (_entitlementPulse.Interval != pollInterval)
            _entitlementPulse.Interval = pollInterval;
        var connected = _bridgeStarted && _api.IsLoggedIn;
        _login.Enabled = !_loggingIn;
        _logout.Enabled = !_loggingIn && _api.IsLoggedIn;
        var state = _bridge.LastStatus;
        var sourcePresence = (state is "SDK_MAPPING_ACCEPTED" or "NATIVE_MAPPING_ACCEPTED" or "NATIVE_SOURCE_VERIFIED")
            ? "approved" : "none";
        var switchAvailable = connected && _nativeInstallState == NativeInstallState.Active &&
            _installedModule.MatchesApplication;
        var sourceVerified = PlaybackSourceEvidence.Verified(switchAvailable && _bridge.Enabled, state, sourcePresence);
        var mappingPending = PlaybackSourceEvidence.MappedButUnverified(switchAvailable && _bridge.Enabled, state, sourcePresence);
        _start.Enabled = _bridgeStarted && !_integrationBusy && !_updatingApplication &&
            (!switchAvailable || !_bridge.Enabled);
        _stop.Enabled = switchAvailable && (_bridge.Enabled || _resumeAfterNetworkFailure);
        _connectionMark.ForeColor = sourceVerified
            ? Accent : ColorTranslator.FromHtml("#858B8E");
        _connectionState.Text = !connected ? "Войти в аккаунт" :
            !switchAvailable ? "Нужно подключить" :
            !_bridge.Enabled ? (_resumeAfterNetworkFailure ? "Нет связи" : "Выключен") :
            sourceVerified ? "Источник выбран" :
            mappingPending ? "Ожидаем подтверждения" : "Сервис включён";
        _connectionState.ForeColor = sourceVerified ? Accent : Secondary;
        _switchHint.Text = !_api.IsLoggedIn ? "Войди в аккаунт, чтобы начать." :
            !switchAvailable ? "Нажми «Старт», чтобы подключить Яндекс.Музыку." :
            !_bridge.Enabled ? (_resumeAfterNetworkFailure ? "Проверяем связь для возобновления подмены" : "Подмена выключена") :
            sourceVerified ? "Плеер выбрал поток CELIKOM. Проверь звук." :
            mappingPending ? "Подмена подготовлена, но источник в плеере ещё не подтверждён." :
            "Сервис включён. Замена текущей песни не подтверждена.";
        if (_bridge.PairCode.Length == 6 && _api.IsLoggedIn &&
            _bridge.CodeExpires > DateTimeOffset.UtcNow)
        {
            _code.Text = _bridge.PairCode;
            _copy.Enabled = true;
            _rotate.Enabled = true;
        }
        else
        {
            _code.Text = "—";
            _copy.Enabled = false;
            _rotate.Enabled = _api.IsLoggedIn;
        }
        if (_bridgeStarted)
        {
            try { _nativeToken?.Publish(_api.Settings.BridgeToken); }
            catch { _status.Text = "Ошибка локального подключения CELIKOM."; }
        }
        _song.Text = state switch
        {
            "SDK_MAPPING_ACCEPTED" => "Подмена подготовлена. Ждём подтверждения источника плеером.",
            "NATIVE_CONNECTED" => "Яндекс подключён. Замена текущей песни не подтверждена.",
            "NATIVE_MAPPING_ACCEPTED" => "Подмена подготовлена. Плеер ещё не подтвердил источник CELIKOM.",
            "NATIVE_SOURCE_VERIFIED" => "Плеер выбрал поток CELIKOM. Проверь звук.",
            "NATIVE_RECOVERING" => "Восстанавливаем подмену…",
            "NATIVE_SOURCE_FAILED" => "Подмена этой песни не загрузилась.",
            "RESOLVING" => "Ищем одобренную версию песни…",
            "ORIGINAL" => "Сейчас играет оригинальная версия.",
            "OFF" => "Подмена выключена. Текущий звук может быть в кеше Яндекса.",
            "UNAVAILABLE" => "Ожидаем текущую песню Яндекса.",
            "HOST_ERROR" => "Ошибка подключения к модулю Яндекса.",
            _ => "Модуль Яндекса пока не подключён."
        };
        _song.ForeColor = sourceVerified ? Accent :
            state == "NATIVE_SOURCE_FAILED" ? ColorTranslator.FromHtml("#D36A6A") : Secondary;
        _status.Text = !_bridgeStarted ? "Не удалось запустить CELIKOM"
            : !_api.IsLoggedIn ? "Для начала войди в аккаунт."
            : !switchAvailable ? "Подключение к Яндексу требуется один раз."
            : !_bridge.Enabled ?
                (_resumeAfterNetworkFailure ? "Нет связи. Ожидаем восстановления." : "Готов к работе")
            : sourceVerified ? "Источник CELIKOM выбран плеером. Проверь звук."
            : mappingPending ? "Подмена подготовлена. Ожидаем подтверждения плеера."
            : "CELIKOM включён. Подмена текущей песни не подтверждена.";
        _hostStatus.Text = _hostReport?.Status switch
        {
            YandexHostStatus.NotInstalled => "Яндекс.Музыка не найдена. Установи её с официального сайта.",
            YandexHostStatus.IncompleteInstallation => "Яндекс установлен неполностью. Его файлы не изменялись.",
            YandexHostStatus.UnsupportedVersion => "Версия Яндекса не проверена: " + _hostReport.Version,
            YandexHostStatus.UntrustedExecutable => "Цифровая подпись Яндекса не прошла проверку. Ничего не меняем.",
            YandexHostStatus.UnknownAsar => "Файлы Яндекса отличаются от проверенного оригинала.",
            YandexHostStatus.OfficialBaselineVerified => "Оригинальная Яндекс.Музыка проверена. Можно подключать CELIKOM.",
            YandexHostStatus.InspectionUnavailable => "Не удалось безопасно проверить Яндекс. Файлы не менялись.",
            _ => "Проверяем совместимость установленной Яндекс.Музыки…"
        };
        _accountSignedIn.Visible = _api.IsLoggedIn;
        _accountSignedOut.Visible = !_api.IsLoggedIn;
        _signedInIdentity.Text = _api.Email;
        if (!preserveAccountStatus && !_api.IsLoggedIn && string.IsNullOrWhiteSpace(_accountStatus.Text))
            _accountStatus.Text = "Войди в аккаунт, чтобы начать.";
        UpdateNavigation(_accountPanel.Visible);
        _connectYandex.Text = _nativeInstallState == NativeInstallState.Active
            ? "Обновить модуль" : "Подключить CELIKOM";
        _connectYandex.Enabled = !_integrationBusy &&
            (_nativeInstallState == NativeInstallState.Active ||
             _hostReport?.Status == YandexHostStatus.OfficialBaselineVerified);
        _restoreYandex.Enabled = !_integrationBusy &&
            _nativeInstallState is NativeInstallState.Active or NativeInstallState.Interrupted;
        _updateApplication.Enabled = !_integrationBusy && !_updatingApplication;
        if (_nativeInstallState == NativeInstallState.Active)
            _hostStatus.Text = _installedModule.MatchesApplication
                ? "Модуль Яндекса подключён и совпадает с версией CELIKOM."
                : "Нажми «Старт», чтобы обновить модуль CELIKOM.";
        else if (_nativeInstallState == NativeInstallState.Interrupted)
            _hostStatus.Text = "Подключение прервалось. Доступно восстановление оригинала.";
        else if (_nativeInstallState == NativeInstallState.VerifiedVendorUpdate)
            _hostStatus.Text = "Обновление Яндекса проверено. Нажми «Старт» — CELIKOM переподключится без переустановки.";
        else if (_nativeInstallState == NativeInstallState.Changed)
            _hostStatus.Text = "Яндекс обновился или изменён. Автоматических изменений не будет.";
        _versionFooter.Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3);
        _tray.Text = connected && _bridge.Enabled
            ? sourceVerified ? "CELIKOM — источник выбран" : "CELIKOM — сервис включён"
            : "CELIKOM — выключен";
    }

    public void RestoreWindowFromSecondLaunch() => ShowMain();

    private void ShowMain()
    {
        RenderCompact();
        LayoutCompact();
        Opacity = 1;
        ShowInTaskbar = true;
        Show();
        WindowState = FormWindowState.Normal;
        Activate();
    }

    private async void ClosingAsync(object? sender, FormClosingEventArgs e)
    {
        if (_closing) return;
        e.Cancel = true;
        _closing = true;
        _resumeAfterNetworkFailure = false;
        NetworkChange.NetworkAddressChanged -= OnNetworkAddressChanged;
        _yandexInstallWatcher?.Dispose();
        _yandexInstallWatcher = null;
        _yandexVersionDebounce.Stop();
        _yandexVersionDebounce.Dispose();
        _entitlementPulse.Stop();
        _entitlementPulse.Dispose();
        _tray.Visible = false;
        try { await _bridge.DisposeAsync(); }
        finally
        {
            _nativeToken?.Dispose();
            _api.Dispose();
            _tray.Dispose();
            Close();
        }
    }
}

