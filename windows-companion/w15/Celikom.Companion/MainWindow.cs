using System.Diagnostics;
using System.Drawing;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

/// <summary>
/// One native CELIKOM window, never a media player. Yandex remains the
/// only source of media keys, queue, pause and seek.
/// </summary>
public sealed class MainWindow : Form
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
    private readonly Label _connectionMark = new();
    private readonly Label _switchHint = new();
    private readonly PopupButton _rotate = new();
    private readonly PopupButton _copy = new();
    private readonly NotifyIcon _tray;
    private readonly Panel _pages = new();
    private readonly Panel _homePanel = new();
    private readonly Panel _accountPanel = new();
    private readonly PopupButton _homeTab = new();
    private readonly PopupButton _accountTab = new();
    private bool _bridgeStarted;
    private bool _closing;
    private bool _loggingIn;

    public MainWindow(bool finishApplicationUpdate = false)
    {
        _finishApplicationUpdate = finishApplicationUpdate;
        _api = new CelikomApi(_store);
        _bridge = new BridgeServer(_api, _store);
        _bridge.Changed += () => UpdateSafe();

        Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3) + " — Windows";
        ClientSize = new Size(462, 760);
        MinimumSize = new Size(440, 730);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 10F);
        BackColor = Paper;
        ForeColor = Ink;
        AutoScaleMode = AutoScaleMode.Dpi;

        // Popup-style header: green connected mark, compact brand, live status.
        var header = new Panel { Dock = DockStyle.Top, Height = 74, BackColor = Paper };
        _connectionMark.Text = "●";
        _connectionMark.Font = new Font("Segoe UI Symbol", 16F, FontStyle.Regular);
        _connectionMark.ForeColor = ColorTranslator.FromHtml("#858B8E");
        _connectionMark.Location = new Point(18, 20);
        _connectionMark.Size = new Size(23, 31);
        var logo = new Label
        {
            Text = "CELIKOM", Font = new Font("Segoe UI", 20F, FontStyle.Bold),
            ForeColor = Ink, Location = new Point(42, 14),
            AutoSize = false, Height = 40, Width = 220
        };
        _connectionState.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
        _connectionState.ForeColor = Secondary;
        _connectionState.TextAlign = ContentAlignment.MiddleRight;
        _connectionState.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        _connectionState.Location = new Point(285, 23);
        _connectionState.Size = new Size(156, 27);
        _connectionState.Text = "Отключён";
        header.Resize += (_, _) =>
            _connectionState.Left = header.ClientSize.Width - _connectionState.Width - 20;
        header.Controls.Add(_connectionMark);
        header.Controls.Add(logo);
        header.Controls.Add(_connectionState);

        _pages.Dock = DockStyle.Fill;
        _pages.BackColor = Paper;
        _homePanel.Dock = DockStyle.Fill;
        _homePanel.BackColor = Paper;
        _accountPanel.Dock = DockStyle.Fill;
        _accountPanel.BackColor = Paper;
        _pages.Controls.Add(_accountPanel);
        _pages.Controls.Add(_homePanel);
        _accountPanel.Visible = false;

        // Extension-like navigation without the native WinForms tab strip:
        // its system-colored border/blank gutter cannot match popup.css.
        var navigation = new Panel { Dock = DockStyle.Top, Height = 46,
            BackColor = Paper, Padding = new Padding(17, 1, 17, 1) };
        var navButtons = new TableLayoutPanel { Dock = DockStyle.Left,
            Width = 304, ColumnCount = 2, RowCount = 1, Margin = Padding.Empty };
        navButtons.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        navButtons.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        ConfigureAuthButton(_homeTab, true, "Главная");
        ConfigureAuthButton(_accountTab, false, "Аккаунт");
        _homeTab.Margin = new Padding(0, 0, 4, 3);
        _accountTab.Margin = new Padding(4, 0, 0, 3);
        _homeTab.Click += (_, _) => NavigateAccount(false);
        _accountTab.Click += (_, _) => NavigateAccount(true);
        navButtons.Controls.Add(_homeTab, 0, 0);
        navButtons.Controls.Add(_accountTab, 1, 0);
        navigation.Controls.Add(navButtons);
        var footerBar = new Panel { Dock = DockStyle.Bottom, Height = 36,
            BackColor = Surface };
        _versionFooter.Dock = DockStyle.Fill;
        _versionFooter.Padding = new Padding(15, 0, 8, 0);
        _versionFooter.TextAlign = ContentAlignment.MiddleLeft;
        _versionFooter.Font = new Font("Segoe UI", 8.5F);
        _versionFooter.ForeColor = Secondary;
        _versionFooter.AutoEllipsis = true;
        footerBar.Controls.Add(_versionFooter);
        Controls.Add(_pages);
        Controls.Add(navigation);
        Controls.Add(header);
        Controls.Add(footerBar);
        BuildHome(_homePanel);
        BuildAccount(_accountPanel);

        var menu = new ContextMenuStrip();
        menu.Items.Add("Открыть CELIKOM", null, (_, _) => ShowMain());
        menu.Items.Add("Остановить подмену", null, (_, _) => _bridge.SetEnabled(false));
        menu.Items.Add("Выход", null, (_, _) => Close());
        _tray = new NotifyIcon
        {
            Icon = SystemIcons.Application, ContextMenuStrip = menu,
            Visible = true, Text = "CELIKOM — выключено"
        };
        _tray.DoubleClick += (_, _) => ShowMain();
        Resize += (_, _) => { if (WindowState == FormWindowState.Minimized) Hide(); };
        FormClosing += ClosingAsync;
        Shown += async (_, _) =>
        {
            await StartBridgeAsync();
            await RefreshHostAsync();
            if (_finishApplicationUpdate) await CompleteApplicationUpdateAsync();
        };
        Activated += (_, _) =>
        {
            if (DateTimeOffset.UtcNow - _lastHostProbe > TimeSpan.FromMinutes(2))
                _ = RefreshHostAsync();
        };
        UpdateSafe();
    }

    private void NavigateAccount(bool account)
    {
        _accountPanel.Visible = account;
        _homePanel.Visible = !account;
        _accountTab.BackColor = account ? Accent : Surface;
        _accountTab.ForeColor = account ? AccentInk : Ink;
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
            Padding = new Padding(17, 12, 17, 9),
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
        Add(layout, Label("Управление CELIKOM", 11, true), 32);
        _status.ForeColor = Secondary;
        _status.Font = new Font("Segoe UI", 10F, FontStyle.Regular);
        _status.AutoEllipsis = false;
        Add(layout, _status, 47);

        // Same separate Start / Stop controls as the Chrome popup; they change
        // the existing native bridge state, not any Yandex account or player keys.
        var primaryActions = new TableLayoutPanel {
            ColumnCount = 2, RowCount = 1, Dock = DockStyle.Fill, Margin = Padding.Empty
        };
        primaryActions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        primaryActions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        ConfigureAuthButton(_start, true, "Старт");
        ConfigureAuthButton(_stop, false, "Стоп");
        _start.Margin = new Padding(0, 2, 4, 2);
        _stop.Margin = new Padding(4, 2, 0, 2);
        _start.Click += (_, _) => _bridge.SetEnabled(true);
        _stop.Click += (_, _) => _bridge.SetEnabled(false);
        primaryActions.Controls.Add(_start, 0, 0);
        primaryActions.Controls.Add(_stop, 1, 0);
        Add(layout, primaryActions, 52);

        _switchHint.ForeColor = Secondary;
        _switchHint.Font = new Font("Segoe UI", 8.5F);
        _switchHint.AutoEllipsis = false;
        Add(layout, _switchHint, 49);

        _song.ForeColor = Secondary;
        _song.Font = new Font("Segoe UI", 9F);
        _song.AutoEllipsis = false;
        Add(layout, _song, 49);

        Add(layout, Label("Яндекс.Музыка", 11, true), 34);
        Add(layout, Label("Слушай музыку в Яндексе. CELIKOM работает отдельно, твой аккаунт Яндекса здесь не нужен.", 9, false, Secondary), 44);
        var pair = new TableLayoutPanel
        {
            Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1,
            Margin = Padding.Empty
        };
        pair.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 60));
        pair.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40));
        _code.ReadOnly = true;
        _code.TabStop = false;
        _code.BackColor = Surface;
        _code.BorderStyle = BorderStyle.None;
        _code.Font = new Font("Consolas", 20F, FontStyle.Bold);
        _code.ForeColor = Accent;
        _code.Dock = DockStyle.Fill;
        _code.TextAlign = HorizontalAlignment.Center;
        pair.Controls.Add(_code, 0, 0);
        _copy.Text = "Копировать";
        _copy.FlatStyle = FlatStyle.Flat;
        _copy.FlatAppearance.BorderColor = Border;
        _copy.BackColor = Surface;
        _copy.ForeColor = Ink;
        _copy.Click += (_, _) =>
        {
            if (_api.IsLoggedIn)
                try
                {
                    if (_bridge.PairCode.Length != 6 ||
                        _bridge.CodeExpires <= DateTimeOffset.UtcNow)
                        _bridge.RotateCode();
                    Clipboard.SetText(_bridge.PairCode);
                }
                catch { /* Clipboard can be busy; leave code visible. */ }
        };
        _copy.Dock = DockStyle.Fill;
        pair.Controls.Add(_copy, 1, 0);
        // Native integration uses a same-user ephemeral capability. Old
        // PulseSync pairing widgets are retained in code for legacy tests,
        // but are not exposed in the native Windows consumer journey.
        _rotate.Text = "Получить новый код";
        _rotate.FlatStyle = FlatStyle.Flat;
        _rotate.BackColor = Surface;
        _rotate.ForeColor = Ink;
        _rotate.FlatAppearance.BorderColor = Border;
        _rotate.Click += (_, _) => _bridge.RotateCode();

        var hostActions = new TableLayoutPanel
        {
            Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1,
            Margin = Padding.Empty
        };
        hostActions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 53));
        hostActions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 47));
        ConfigureAuthButton(_connectYandex, true, "Подключить CELIKOM");
        ConfigureAuthButton(_restoreYandex, false, "Восстановить Яндекс");
        hostActions.Controls.Add(_connectYandex, 0, 0);
        hostActions.Controls.Add(_restoreYandex, 1, 0);
        _connectYandex.Click += ConnectYandexAsync;
        _restoreYandex.Click += RestoreYandexAsync;
        Add(layout, hostActions, 50);

        var openYandex = Button("Открыть Яндекс", false);
        openYandex.Click += (_, _) =>
        {
            try { Process.Start(new ProcessStartInfo("yandexmusic://") { UseShellExecute = true }); }
            catch { MessageBox.Show(this, "Открой Яндекс.Музыку обычным способом.", "CELIKOM"); }
        };
        var tools = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1 };
        tools.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        tools.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        var downloadDiagnostics = Button("Диагностика", false);
        // Default WinForms button width truncated both labels in the owner screenshot.
        openYandex.Dock = DockStyle.Fill;
        downloadDiagnostics.Dock = DockStyle.Fill;
        downloadDiagnostics.Click += (_, _) => SaveDiagnostics();
        tools.Controls.Add(openYandex, 0, 0);
        tools.Controls.Add(downloadDiagnostics, 1, 0);
        Add(layout, tools, 46);
        ConfigureAuthButton(_updateApplication, false, "Обновить CELIKOM");
        _updateApplication.Click += UpdateApplicationAsync;
        Add(layout, _updateApplication, 43);
        _hostStatus.ForeColor = Secondary;
        _hostStatus.Font = new Font("Segoe UI", 8.5F);
        _hostStatus.AutoEllipsis = false;
        Add(layout, _hostStatus, 54);
    }

    private void BuildAccount(Control page)
    {
        var layout = PageLayout(page);
        Add(layout, Label("Вход в существующий аккаунт CELIKOM", 11, true), 44);
        Add(layout, Label("Адрес твоего API (HTTPS)", 9, false, Secondary), 28);
        _origin.BackColor = Surface;
        _origin.ForeColor = Ink;
        _origin.BorderStyle = BorderStyle.FixedSingle;
        _origin.Text = _api.Origin;
        _origin.PlaceholderText = "https://адрес-API-CELIKOM";
        Add(layout, _origin, 42);
        Add(layout, Label("Учётная запись", 9, false, Secondary), 31);
        _email.BackColor = Surface;
        _email.ForeColor = Ink;
        _email.BorderStyle = BorderStyle.FixedSingle;
        _email.Text = _api.Email;
        _email.PlaceholderText = "Электронная почта CELIKOM";
        Add(layout, _email, 42);
        _password.BackColor = Surface;
        _password.ForeColor = Ink;
        _password.BorderStyle = BorderStyle.FixedSingle;
        _password.UseSystemPasswordChar = true;
        _password.PlaceholderText = "Пароль CELIKOM";
        Add(layout, _password, 42);

        var buttons = new TableLayoutPanel { ColumnCount = 2, RowCount = 1 };
        buttons.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 52));
        buttons.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 48));
        ConfigureAuthButton(_login, true, "Войти");
        ConfigureAuthButton(_logout, false, "Выйти");
        buttons.Controls.Add(_login, 0, 0);
        buttons.Controls.Add(_logout, 1, 0);
        Add(layout, buttons, 51);
        _login.Click += LoginAsync;
        _logout.Click += LogoutAsync;

        _accountStatus.ForeColor = Accent;
        _accountStatus.AutoEllipsis = false;
        Add(layout, _accountStatus, 65);
        Add(layout, Label("Пароль Яндекс.Музыки здесь НЕ нужен.", 10, true, Accent), 41);
        Add(layout, Label("CELIKOM хранит свою сессию в защищённом хранилище Windows. При выходе старый код подключения отключается.", 9, false, Secondary), 72);
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
                ? "Обновить модуль CELIKOM внутри Яндекс.Музыки? " +
                  "Сначала будут проверены и восстановлены оригинальные файлы, затем " +
                  "установлен новый модуль с диагностикой. Яндекс перезапустится."
                : "CELIKOM сохранит оригинальные файлы Яндекс.Музыки и подключит свою подмену. " +
                  "Яндекс будет аккуратно закрыт и перезапущен. Продолжить?",
            upgrading ? "Обновить модуль CELIKOM" : "Подключить CELIKOM",
            MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes) return;
        _integrationBusy = true;
        UpdateSafe();
        try
        {
            DiagnosticLog.Record(upgrading ? "NATIVE_UPGRADE_REQUEST" : "NATIVE_INSTALL_REQUEST");
            if (upgrading)
            {
                _bridge.SetEnabled(false);
                await Task.Run(() => NativeIntegrationManager.Restore());
                DiagnosticLog.Record("NATIVE_RESTORE_OK");
            }
            await Task.Run(() => NativeIntegrationManager.Install());
            DiagnosticLog.Record("NATIVE_INSTALL_OK");
            _bridge.SetEnabled(_api.IsLoggedIn);
            _hostStatus.Text = "CELIKOM подключён к Яндексу.";
            try
            {
                var exe = Path.Combine(NativeIntegrationManager.DefaultYandexDirectory,
                    "Яндекс Музыка.exe");
                Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true });
            }
            catch { /* Connected files verified; user may open Yandex normally. */ }
        }
        catch (Exception error)
        {
            DiagnosticLog.Record(upgrading ? "NATIVE_UPGRADE_FAILED" : "NATIVE_INSTALL_FAILED");
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
            _bridge.SetEnabled(_api.IsLoggedIn);
            var exe = Path.Combine(NativeIntegrationManager.DefaultYandexDirectory, "Яндекс Музыка.exe");
            try { Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true }); }
            catch { /* Owner can open Yandex normally. */ }
        }
        catch (Exception error)
        {
            DiagnosticLog.Record("APP_UPDATE_NATIVE_REFRESH_FAILED");
            MessageBox.Show(this,
                "CELIKOM обновился, но модуль Яндекса не обновился: " +
                DescribeIntegrationFailure(error) + "\nНажми «Обновить модуль» после проверки.",
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
        _login.Enabled = false;
        _bridge.SetEnabled(false);
        try
        {
            await _api.LoginAsync(_origin.Text.Trim(), _email.Text.Trim(), _password.Text);
            DiagnosticLog.Record("LOGIN_OK");
            _password.Clear();
            _accountStatus.Text = "Вход выполнен. Можно нажать «Старт».";
            NavigateAccount(false);
        }
        catch (ApiFailure e2)
        {
            DiagnosticLog.Record("LOGIN_FAILED");
            _accountStatus.Text = e2.Category switch
            {
                "INVALID_CREDENTIALS" => "Неверная почта или пароль.",
                "EMAIL_VERIFICATION_REQUIRED" => "Сначала подтверди почту в CELIKOM.",
                "RATE_LIMITED" => "Слишком много попыток входа.",
                _ => "Не удалось войти. Проверь адрес API и доступ."
            };
        }
        catch (Exception) { _accountStatus.Text = "Не удалось войти. Проверь сеть и адрес API."; }
        finally
        {
            _loggingIn = false;
            UpdateSafe(preserveAccountStatus: true);
        }
    }

    private async void LogoutAsync(object? sender, EventArgs e)
    {
        _bridge.SetEnabled(false);
        _logout.Enabled = false;
        try { await _api.LogoutAsync(); DiagnosticLog.Record("LOGOUT_OK"); _accountStatus.Text = "Выход выполнен. Старый код подключения недействителен."; }
        catch { _accountStatus.Text = "Не удалось завершить выход. Проверь подключение."; }
        finally { UpdateSafe(preserveAccountStatus: true); }
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
        _start.Enabled = switchAvailable && !_bridge.Enabled;
        _stop.Enabled = switchAvailable && _bridge.Enabled;
        _connectionMark.ForeColor = switchAvailable && _bridge.Enabled
            ? Accent : ColorTranslator.FromHtml("#858B8E");
        _connectionState.Text = !connected ? "Войти в CELIKOM" :
            !switchAvailable ? "Нет подключения" :
            _bridge.Enabled ? "Подключён" : "Выключен";
        _connectionState.ForeColor = switchAvailable && _bridge.Enabled ? Accent : Secondary;
        // A source URL already delivered to Yandex cannot be changed by a
        // bridge state toggle. Explain that existing playback/preload may
        // survive, rather than promising instant hot-swap that does not exist.
        _switchHint.Text = _bridge.Enabled
            ? "Подмена включена. Для уже играющей песни CELIKOM попробует обновить источник без сброса позиции."
            : "Подмена выключена. Уже играющая песня переключится на оригинал, если Яндекс поддержит обновление.";
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
        _status.Text = !_bridgeStarted ? "Локальная служба пока не запущена"
            : !_api.IsLoggedIn ? "Войди в CELIKOM на вкладке «Аккаунт»"
            : _nativeInstallState != NativeInstallState.Active ? "Подключи CELIKOM к Яндекс.Музыке."
            : !_bridge.Enabled ? "CELIKOM подключён. Подмена выключена."
            : "CELIKOM подключён. Слушай в Яндекс.Музыке.";
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
        if (!preserveAccountStatus)
            _accountStatus.Text = _api.IsLoggedIn
                ? "Вход выполнен: " + _api.Email
                : "Нет активной сессии CELIKOM.";
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
        var moduleText = _nativeInstallState == NativeInstallState.Active
            ? _installedModule.MatchesApplication
                ? "Модуль Яндекса: " + AppUpdateManager.RunningVersion.ToString(3) + " ✓"
                : "Модуль Яндекса: " +
                  (_installedModule.Version == "unknown" ? "старая версия" : _installedModule.Version) +
                  " — не совпадает"
            : "Модуль Яндекса: не подключён";
        _versionFooter.Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3) +
            "   |   " + moduleText;
        _tray.Text = connected && _bridge.Enabled
            ? "CELIKOM — включён" : "CELIKOM — выключен";
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
