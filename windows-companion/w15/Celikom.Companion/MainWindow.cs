using System.Diagnostics;
using System.Drawing;

namespace Celikom.Companion;

/// <summary>
/// One native CELIKOM window, never a media player. Yandex remains the
/// only source of media keys, queue, pause and seek.
/// </summary>
public sealed class MainWindow : Form
{
    private static readonly Color Ink = ColorTranslator.FromHtml("#0B1013");
    private static readonly Color Paper = ColorTranslator.FromHtml("#F7F8F4");
    private static readonly Color Secondary = ColorTranslator.FromHtml("#556368");
    private static readonly Color Accent = ColorTranslator.FromHtml("#14594D");
    private static readonly Color Border = ColorTranslator.FromHtml("#DCE8E3");

    private readonly SessionStore _store = new();
    private readonly CelikomApi _api;
    private readonly BridgeServer _bridge;
    private readonly TextBox _origin = new();
    private readonly TextBox _email = new();
    private readonly TextBox _password = new();
    private readonly TextBox _code = new();
    private readonly Label _status = new();
    private readonly Label _song = new();
    private readonly Label _accountStatus = new();
    private readonly Button _login = new();
    private readonly Button _logout = new();
    private readonly Button _toggle = new();
    private readonly Button _rotate = new();
    private readonly Button _copy = new();
    private readonly NotifyIcon _tray;
    private readonly TabControl _pages = new();
    private bool _bridgeStarted;
    private bool _closing;
    private bool _loggingIn;

    public MainWindow()
    {
        _api = new CelikomApi(_store);
        _bridge = new BridgeServer(_api, _store);
        _bridge.Changed += UpdateSafe;

        Text = "CELIKOM Companion — Windows";
        ClientSize = new Size(488, 612);
        MinimumSize = new Size(465, 620);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 10F);
        BackColor = Paper;
        ForeColor = Ink;
        AutoScaleMode = AutoScaleMode.Dpi;

        var header = new Panel { Dock = DockStyle.Top, Height = 76, BackColor = Ink };
        var logo = new Label
        {
            Text = "CELIKOM", Font = new Font("Segoe UI", 23F, FontStyle.Bold),
            ForeColor = Color.White, Location = new Point(20, 5),
            AutoSize = false, Height = 45, Width = 420
        };
        var tagline = new Label
        {
            Text = "Для Яндекс.Музыки · Windows",
            ForeColor = ColorTranslator.FromHtml("#66E0BF"), Location = new Point(22, 51),
            AutoSize = false, Height = 21, Width = 415
        };
        header.Controls.Add(logo);
        header.Controls.Add(tagline);

        _pages.Dock = DockStyle.Fill;
        _pages.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        var home = new TabPage("Главная") { BackColor = Paper, UseVisualStyleBackColor = false };
        var account = new TabPage("Аккаунт") { BackColor = Paper, UseVisualStyleBackColor = false };
        _pages.TabPages.Add(home);
        _pages.TabPages.Add(account);
        Controls.Add(_pages);
        Controls.Add(header);
        BuildHome(home);
        BuildAccount(account);

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
        Shown += async (_, _) => await StartBridgeAsync();
        UpdateSafe();
    }

    private static TableLayoutPanel PageLayout(TabPage page)
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 0,
            Padding = new Padding(17, 13, 17, 8),
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
            AutoEllipsis = true
        };

    private static Button Button(string caption, bool primary)
    {
        var btn = new Button
        {
            Text = caption, FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            BackColor = primary ? Accent : Paper,
            ForeColor = primary ? Color.White : Ink,
            Cursor = Cursors.Hand, UseVisualStyleBackColor = false
        };
        btn.FlatAppearance.BorderSize = primary ? 0 : 1;
        btn.FlatAppearance.BorderColor = Border;
        return btn;
    }

    private void BuildHome(TabPage page)
    {
        var layout = PageLayout(page);
        Add(layout, Label("Управление остаётся в Яндекс.Музыке.", 10, false, Secondary), 38);
        _status.ForeColor = Accent;
        _status.Font = new Font("Segoe UI", 11F, FontStyle.Bold);
        _status.AutoEllipsis = false;
        Add(layout, _status, 50);
        Add(layout, Label("ПОДМЕНА ВЕРСИЙ", 11, true), 36);
        _toggle.Text = "Старт";
        _toggle.FlatStyle = FlatStyle.Flat;
        _toggle.FlatAppearance.BorderSize = 0;
        _toggle.BackColor = Accent;
        _toggle.ForeColor = Color.White;
        _toggle.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
        _toggle.Click += (_, _) => _bridge.SetEnabled(!_bridge.Enabled);
        Add(layout, _toggle, 52);
        _song.ForeColor = Secondary;
        _song.AutoEllipsis = false;
        Add(layout, _song, 53);

        Add(layout, Label("ПЕРВОЕ ПОДКЛЮЧЕНИЕ", 11, true), 39);
        Add(layout, Label("Открой дополнение CELIKOM внутри Яндекса и введи код.", 9, false, Secondary), 41);
        var pair = new TableLayoutPanel
        {
            Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1,
            Margin = Padding.Empty
        };
        pair.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 60));
        pair.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40));
        _code.ReadOnly = true;
        _code.TabStop = false;
        _code.BackColor = Paper;
        _code.BorderStyle = BorderStyle.None;
        _code.Font = new Font("Consolas", 20F, FontStyle.Bold);
        _code.ForeColor = Accent;
        _code.Dock = DockStyle.Fill;
        _code.TextAlign = HorizontalAlignment.Center;
        pair.Controls.Add(_code, 0, 0);
        _copy.Text = "Копировать";
        _copy.FlatStyle = FlatStyle.Flat;
        _copy.FlatAppearance.BorderColor = Border;
        _copy.BackColor = Paper;
        _copy.Click += (_, _) =>
        {
            if (_bridge.PairCode.Length == 6 && _api.IsLoggedIn)
                try { Clipboard.SetText(_bridge.PairCode); }
                catch { /* Clipboard can be busy; leave code visible. */ }
        };
        _copy.Dock = DockStyle.Fill;
        pair.Controls.Add(_copy, 1, 0);
        Add(layout, pair, 48);
        _rotate.Text = "Получить новый код";
        _rotate.FlatStyle = FlatStyle.Flat;
        _rotate.BackColor = Paper;
        _rotate.FlatAppearance.BorderColor = Border;
        _rotate.Click += (_, _) => _bridge.RotateCode();
        Add(layout, _rotate, 43);

        var openYandex = Button("Открыть Яндекс.Музыку", false);
        openYandex.Click += (_, _) =>
        {
            try { Process.Start(new ProcessStartInfo("yandexmusic://") { UseShellExecute = true }); }
            catch { MessageBox.Show(this, "Открой Яндекс.Музыку обычным способом.", "CELIKOM"); }
        };
        Add(layout, openYandex, 47);
        Add(layout, Label("CELIKOM не управляет громкостью, очередью или перемоткой.", 9, false, Secondary), 39);
    }

    private void BuildAccount(TabPage page)
    {
        var layout = PageLayout(page);
        Add(layout, Label("Вход в существующий аккаунт CELIKOM", 11, true), 44);
        Add(layout, Label("Адрес твоего API (HTTPS)", 9, false, Secondary), 28);
        _origin.Text = _api.Origin;
        _origin.PlaceholderText = "https://адрес-API-CELIKOM";
        Add(layout, _origin, 42);
        Add(layout, Label("Учётная запись", 9, false, Secondary), 31);
        _email.Text = _api.Email;
        _email.PlaceholderText = "Электронная почта CELIKOM";
        Add(layout, _email, 42);
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
        button.FlatAppearance.BorderSize = primary ? 0 : 1;
        button.FlatAppearance.BorderColor = Border;
        button.BackColor = primary ? Accent : Paper;
        button.ForeColor = primary ? Color.White : Ink;
    }

    private async Task StartBridgeAsync()
    {
        try
        {
            await _bridge.StartAsync();
            _bridgeStarted = true;
            UpdateSafe();
        }
        catch
        {
            _bridgeStarted = false;
            _status.Text = "Локальная служба недоступна. Закрой другие копии CELIKOM.";
            _accountStatus.Text = "Не удалось запустить службу CELIKOM.";
            _toggle.Enabled = false;
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
            _password.Clear();
            _accountStatus.Text = "Вход подтверждён. Перейди на «Главная» и нажми «Старт».";
        }
        catch (ApiFailure e2)
        {
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
        try { await _api.LogoutAsync(); _accountStatus.Text = "Выход выполнен. Старый код подключения недействителен."; }
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
        _toggle.Enabled = connected;
        _toggle.Text = _bridge.Enabled ? "Стоп" : "Старт";
        _toggle.BackColor = connected ? Accent : ColorTranslator.FromHtml("#D1D9D6");
        _toggle.ForeColor = connected ? Color.White : Secondary;
        if (_bridge.PairCode.Length == 6 && _api.IsLoggedIn)
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
        var state = _bridge.LastStatus;
        _song.Text = state switch
        {
            "SDK_MAPPING_ACCEPTED" => "Подмена передана SDK. Реальный звук пока не подтверждён.",
            "RESOLVING" => "Ищем одобренную версию песни…",
            "ORIGINAL" => "Подмена недоступна — оригинальная версия.",
            "OFF" => "Подмена выключена.",
            "UNAVAILABLE" => "Ожидаем текущую песню Яндекса.",
            "HOST_ERROR" => "Ошибка подключения к модулю Яндекса.",
            _ => "Модуль Яндекса пока не подключён."
        };
        _status.Text = !_bridgeStarted ? "Локальная служба пока не запущена"
            : !_api.IsLoggedIn ? "Войди в CELIKOM на вкладке «Аккаунт»"
            : !_bridge.Enabled ? "CELIKOM готов. Подмена выключена."
            : "CELIKOM включён. Ожидаем модуль Яндекса.";
        if (!preserveAccountStatus)
            _accountStatus.Text = _api.IsLoggedIn
                ? "Вход выполнен: " + _api.Email
                : "Нет активной сессии CELIKOM.";
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
            _api.Dispose();
            _tray.Dispose();
            Close();
        }
    }
}
