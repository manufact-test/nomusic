using System.Diagnostics;
using System.Drawing;
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
    private readonly PopupButton _connectYandex = new();
    private readonly PopupButton _restoreYandex = new();
    private NativeInstallState _nativeInstallState = NativeInstallState.NotInstalled;
    private bool _integrationBusy;
    private YandexHostResult? _hostReport;
    private bool _hostProbeBusy;
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
    private bool _bridgeStarted;
    private bool _closing;
    private bool _loggingIn;
    // Server is the authority; this periodic check only updates UI/state
    // after a subscription expires or the network becomes unavailable.
    private readonly System.Windows.Forms.Timer _entitlementPulse = new()
        { Interval = 15000 };

    public MainWindow(bool finishApplicationUpdate = false)
    {
        _finishApplicationUpdate = finishApplicationUpdate;
        _api = new CelikomApi(_store);
        _bridge = new BridgeServer(_api, _store);
        _bridge.Changed += () => UpdateSafe();

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

        var menu = new ContextMenuStrip();
        menu.Items.Add("Открыть CELIKOM", null, (_, _) => ShowMain());
        menu.Items.Add("Остановить подмену", null, (_, _) => _bridge.SetEnabled(false));
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
            if (!_closing && _bridge.Enabled && _api.IsLoggedIn)
                _ = RefreshCompactAccessAsync(force: true);
        };
        FormClosing += ClosingAsync;
        Shown += async (_, _) =>
        {
            await StartBridgeAsync();
            _entitlementPulse.Start();
            await RefreshHostAsync();
            if (_finishApplicationUpdate) await CompleteApplicationUpdateAsync();
            if (_api.IsLoggedIn)
            {
                await RefreshDiagnosticsAccessAsync();
                await RefreshCompactAccessAsync(force: true);
            }
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
        _stop.Click += (_, _) => _bridge.SetEnabled(false);
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
        // Every Start, including a later reinstall or expired subscription,
        // requires live server authority. Never infer playback entitlement
        // from the presence of stored DPAPI tokens or the account UI.
        var generation = ++_compactStartEpoch;
        var account = _api.Settings;
        _compactStarting = true;
        _compactStartupText = "Проверяем пробный период или подписку…";
        RenderCompact();
        LayoutCompact();
        try
        {
            var access = await _api.ActivatePlaybackAsync();
            if (generation != _compactStartEpoch || _closing || IsDisposed ||
                _api.Settings.InstallationId != account.InstallationId ||
                _api.Settings.Email != account.Email || !_api.IsLoggedIn) return;
            ++_compactAccessGeneration; // invalidate an older read-only preview
            _compactAccess.Text = AccessLabel(access);
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
                ConnectYandexAsync(sender, e);
                return;
            }
            if (!OpenYandexIfNeeded())
            {
                _compactStarting = false;
                _compactStartupText = "";
                return;
            }
            _bridge.SetEnabled(true);
            _compactStarting = true;
            _compactStartupText = "Подождите, идёт загрузка Яндекс.Музыки…";
            _ = MonitorStartupAsync(generation);
        }
        catch (Exception)
        {
            if (generation != _compactStartEpoch || _closing || IsDisposed) return;
            _bridge.SetEnabled(false);
            _compactStarting = false;
            _compactStartupText = "Не удалось проверить доступ на сервере. Подмена выключена.";
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

        if (MessageBox.Show(this, "Открыть Яндекс.Музыку?",
                "Запустить Яндекс.Музыку", MessageBoxButtons.YesNo,
                MessageBoxIcon.Question) != DialogResult.Yes)
            return false;
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
        RenderCompact();
        LayoutCompact();
    }

    private async Task RefreshDiagnosticsAccessAsync()
    {
        var generation = ++_diagnosticsEpoch;
        var email = _api.Email;
        _diagnosticsAllowed = false;
        _staffPanel.Visible = false;
        if (!_api.IsLoggedIn) return;
        bool allowed;
        try { allowed = await _api.CanExportDiagnosticsAsync(); }
        catch { allowed = false; }
        if (generation != _diagnosticsEpoch || !_api.IsLoggedIn ||
            !string.Equals(email, _api.Email, StringComparison.OrdinalIgnoreCase)) return;
        _diagnosticsAllowed = allowed;
        _staffPanel.Visible = allowed;
        LayoutCompact();
    }

    private async void SaveDiagnosticsAuthorized(object? sender, EventArgs e)
    {
        // A previous visible button is not enough: verify live authority again.
        bool allowed;
        try { allowed = _api.IsLoggedIn && await _api.CanExportDiagnosticsAsync(); }
        catch { allowed = false; }
        if (!allowed)
        {
            _diagnosticsAllowed = false;
            _staffPanel.Visible = false;
            return;
        }
        SaveDiagnostics();
    }

    private async void CopyDiagnosticsAuthorized(object? sender, EventArgs e)
    {
        // A visible button alone never authorizes exporting diagnostics.
        bool allowed;
        try { allowed = _api.IsLoggedIn && await _api.CanExportDiagnosticsAsync(); }
        catch { allowed = false; }
        if (!allowed)
        {
            _diagnosticsAllowed = false;
            _staffPanel.Visible = false;
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

    private async Task RefreshHostAsync()
    {
        if (_closing || _hostProbeBusy) return;
        _hostProbeBusy = true;
        try
        {
            var inspected = await Task.Run(() =>
            {
                var nativeState = NativeIntegrationManager.Inspect();
                return (YandexHostProbe.Inspect(), nativeState,
                    NativeModuleIdentity.Inspect(nativeState));
            });
            _hostReport = inspected.Item1;
            _nativeInstallState = inspected.Item2;
            _installedModule = inspected.Item3;
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

    private async void ConnectYandexAsync(object? sender, EventArgs e)
    {
        if (_integrationBusy) return;
        var upgrading = _nativeInstallState == NativeInstallState.Active;
        if (!upgrading && _hostReport?.Status != YandexHostStatus.OfficialBaselineVerified)
        {
            MessageBox.Show(this, "Установленная версия Яндекс.Музыки пока не поддерживается.", "CELIKOM");
            return;
        }
        var answer = MessageBox.Show(this,
            upgrading
                ? "Чтобы CELIKOM работал, нужно обновить подключение к Яндекс.Музыке. Яндекс перезапустится. Продолжить?"
                : "Подключить CELIKOM к Яндекс.Музыке? Оригинальные файлы будут сохранены, Яндекс перезапустится.",
            "Подключение CELIKOM",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes) return;
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
            if (upgrading)
            {
                _bridge.SetEnabled(false);
                await Task.Run(() => NativeIntegrationManager.Restore());
                DiagnosticLog.Record("NATIVE_RESTORE_OK");
            }
            await Task.Run(() => NativeIntegrationManager.Install());
            DiagnosticLog.Record("NATIVE_INSTALL_OK");
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
                NativeIntegrationManager.Restore();
                NativeIntegrationManager.Install();
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
        "UNSUPPORTED_YANDEX_VERSION" or "UNSUPPORTED_ASAR_VERSION" =>
            "Текущая версия Яндекс.Музыки ещё не поддерживается.",
        "CELIKOM_NATIVE_MODULE_NOT_INSTALLED" =>
            "Модуль интеграции не найден. Установи полную сборку CELIKOM.",
        "YANDEX_UPDATED_OR_BACKUP_CHANGED" or "YANDEX_FILES_DIFFER_FROM_KNOWN_BACKUP" =>
            "Файлы Яндекс.Музыки изменились. CELIKOM не будет перезаписывать их вслепую.",
        "PREVIOUS_INSTALL_INTERRUPTED_RESTORE_FIRST" =>
            "Предыдущая установка прервалась. Сначала восстанови оригинал.",
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
        ++_compactStartEpoch;
        _compactStarting = false;
        _bridge.SetEnabled(false);
        ++_diagnosticsEpoch;
        _diagnosticsAllowed = false;
        _staffPanel.Visible = false;
        _logout.Enabled = false;
        try { await _api.LogoutAsync(); DiagnosticLog.Record("LOGOUT_OK"); _accountStatus.Text = ""; }
        catch { _accountStatus.Text = "Не удалось завершить выход. Проверь подключение."; }
        finally
        {
            ++_compactAccessGeneration;
            _compactAccess.Text = "Войдите в аккаунт, чтобы начать";
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

        var connected = _bridgeStarted && _api.IsLoggedIn;
        _login.Enabled = !_loggingIn;
        _logout.Enabled = !_loggingIn && _api.IsLoggedIn;
        var switchAvailable = connected && _nativeInstallState == NativeInstallState.Active &&
            _installedModule.MatchesApplication;
        _start.Enabled = _bridgeStarted && !_integrationBusy && !_updatingApplication &&
            (!switchAvailable || !_bridge.Enabled);
        _stop.Enabled = switchAvailable && _bridge.Enabled;
        _connectionMark.ForeColor = switchAvailable && _bridge.Enabled
            ? Accent : ColorTranslator.FromHtml("#858B8E");
        _connectionState.Text = !connected ? "Войти в аккаунт" :
            !switchAvailable ? "Нужно подключить" :
            _bridge.Enabled ? "Подключён" : "Выключен";
        _connectionState.ForeColor = switchAvailable && _bridge.Enabled ? Accent : Secondary;
        _switchHint.Text = !_api.IsLoggedIn ? "Войди в аккаунт, чтобы начать." :
            !switchAvailable ? "Нажми «Старт», чтобы подключить Яндекс.Музыку." :
            _bridge.Enabled ? "Подмена включена" : "Подмена выключена";
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
        var state = _bridge.LastStatus;
        _song.Text = state switch
        {
            "SDK_MAPPING_ACCEPTED" => "Подмена передана проигрывателю Яндекса.",
            "NATIVE_CONNECTED" => "Связь с Яндексом есть. Ожидаем композицию.",
            "NATIVE_MAPPING_ACCEPTED" => "Версия CELIKOM передана Яндекс.Музыке.",
            "RESOLVING" => "Ищем одобренную версию песни…",
            "ORIGINAL" => "Подмена недоступна — оригинальная версия.",
            "OFF" => "Подмена выключена. Текущий звук может быть в кеше Яндекса.",
            "UNAVAILABLE" => "Ожидаем текущую песню Яндекса.",
            "HOST_ERROR" => "Ошибка подключения к модулю Яндекса.",
            _ => "Модуль Яндекса пока не подключён."
        };
        _status.Text = !_bridgeStarted ? "Не удалось запустить CELIKOM"
            : !_api.IsLoggedIn ? "Для начала войди в аккаунт."
            : !switchAvailable ? "Подключение к Яндексу требуется один раз."
            : !_bridge.Enabled ? "Готов к работе" : "CELIKOM работает";
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
                : "В Яндексе старый модуль! Нажми «Обновить модуль».";
        else if (_nativeInstallState == NativeInstallState.Interrupted)
            _hostStatus.Text = "Подключение прервалось. Доступно восстановление оригинала.";
        else if (_nativeInstallState == NativeInstallState.Changed)
            _hostStatus.Text = "Яндекс обновился или изменён. Автоматических изменений не будет.";
        _versionFooter.Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3);
        _tray.Text = connected && _bridge.Enabled
            ? "CELIKOM — включён" : "CELIKOM — выключен";
        RenderCompact();
    }

    private void ShowMain()
    {
        Show();
        WindowState = FormWindowState.Normal;
        Activate();
    }

    private async void ClosingAsync(object? sender, FormClosingEventArgs e)
    {
        if (_closing) return;
        e.Cancel = true;
        _closing = true;
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
