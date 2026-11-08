using System.Diagnostics;
using System.Drawing;

namespace Celikom.Companion;

/// <summary>Visible CELIKOM Companion control surface. No media playback code.</summary>
public sealed class MainWindow : Form
{
    private readonly SessionStore _store = new();
    private readonly CelikomApi _api;
    private readonly BridgeServer _bridge;
    private readonly TextBox _origin = new();
    private readonly TextBox _email = new();
    private readonly TextBox _password = new();
    private readonly Label _status = new();
    private readonly Label _pairCode = new();
    private readonly Label _nowPlaying = new();
    private readonly Button _login = new();
    private readonly Button _logout = new();
    private readonly Button _toggle = new();
    private readonly Button _rotate = new();
    private readonly NotifyIcon _tray;
    private bool _bridgeStarted;
    private bool _closing;

    public MainWindow()
    {
        _api = new CelikomApi(_store);
        _bridge = new BridgeServer(_api, _store);
        _bridge.Changed += () => UpdateSafe();
        Text = "CELIKOM Companion — Windows";
        Width = 495;
        Height = 655;
        MinimumSize = new Size(440, 560);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = ColorTranslator.FromHtml("#F7F8F4");
        ForeColor = ColorTranslator.FromHtml("#0B1013");
        Font = new Font("Segoe UI", 10F);
        AutoScaleMode = AutoScaleMode.Dpi;

        var trayMenu = new ContextMenuStrip();
        trayMenu.Items.Add("Открыть CELIKOM", null, (_, _) => ShowMain());
        trayMenu.Items.Add("Стоп", null, (_, _) => { _bridge.SetEnabled(false); });
        trayMenu.Items.Add("Выход", null, (_, _) => Close());
        _tray = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            ContextMenuStrip = trayMenu,
            Visible = true,
            Text = "CELIKOM — выключено"
        };
        _tray.DoubleClick += (_, _) => ShowMain();
        Resize += (_, _) => { if (WindowState == FormWindowState.Minimized) Hide(); };
        FormClosing += ClosingAsync;

        var content = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            Padding = new Padding(20, 16, 20, 16),
            ColumnCount = 1,
            RowCount = 0,
            AutoScroll = true
        };
        content.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Controls.Add(content);

        Add(content, Header("CELIKOM", 26, true, 52), 52);
        Add(content, Hint("Windows Companion — управление музыкой остаётся в Яндексе.", 42), 42);
        _status.Text = "Запускаю локальную службу…";
        _status.ForeColor = ColorTranslator.FromHtml("#14594D");
        Add(content, _status, 56);
        Add(content, Section("Подключение к CELIKOM"), 28);
        Add(content, Hint("Адрес действующего API (HTTPS):", 23), 23);
        _origin.Text = _api.Origin;
        _origin.PlaceholderText = "https://адрес-вашего-сервера";
        Add(content, _origin, 36);
        _email.Text = _api.Email;
        _email.PlaceholderText = "Электронная почта";
        Add(content, _email, 36);
        _password.UseSystemPasswordChar = true;
        _password.PlaceholderText = "Пароль CELIKOM";
        Add(content, _password, 36);

        var authButtons = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
        Configure(_login, "Войти", true, 110);
        Configure(_logout, "Выйти", false, 100);
        authButtons.Controls.Add(_login);
        authButtons.Controls.Add(_logout);
        Add(content, authButtons, 45);

        Add(content, Section("Подмена версий"), 34);
        Configure(_toggle, "Старт", true, 180);
        Add(content, _toggle, 46);
        _nowPlaying.Text = "Песня: ожидаем подключение модуля";
        Add(content, _nowPlaying, 49);
        Add(content, Section("Первое соединение с модулем"), 32);
        Add(content, Hint("Код вводится один раз в дополнении CELIKOM внутри Яндекс.Музыки.", 37), 37);
        _pairCode.Font = new Font("Consolas", 17F, FontStyle.Bold);
        _pairCode.ForeColor = ColorTranslator.FromHtml("#14594D");
        Add(content, _pairCode, 43);
        Configure(_rotate, "Новый код подключения", false, 220);
        Add(content, _rotate, 43);

        var open = new Button();
        Configure(open, "Открыть Яндекс.Музыку", false, 215);
        Add(content, open, 43);
        open.Click += (_, _) =>
        {
            try { Process.Start(new ProcessStartInfo("yandexmusic://") { UseShellExecute = true }); }
            catch { MessageBox.Show(this, "Открой Яндекс.Музыку обычным способом.", "CELIKOM"); }
        };

        Add(content, Hint("CELIKOM не отключает защиту Windows и не изменяет файлы Яндекса.", 46), 46);

        _login.Click += LoginAsync;
        _logout.Click += LogoutAsync;
        _toggle.Click += (_, _) => _bridge.SetEnabled(!_bridge.Enabled);
        _rotate.Click += (_, _) => { _bridge.RotateCode(); UpdateSafe(); };
        UpdateSafe();
        Shown += async (_, _) => await StartBridgeAsync();
    }

    private static Label Header(string value, float size, bool bold, int height) =>
        new() { Text = value, Dock = DockStyle.Fill,
            Font = new Font("Segoe UI", size, bold ? FontStyle.Bold : FontStyle.Regular),
            TextAlign = ContentAlignment.MiddleLeft, Height = height };
    private static Label Section(string text) =>
        new() { Text = text, Font = new Font("Segoe UI", 11.5F, FontStyle.Bold),
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.BottomLeft };
    private static Label Hint(string text, int height) =>
        new() { Text = text, ForeColor = ColorTranslator.FromHtml("#556368"),
            Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft, Height = height };
    private static void Add(TableLayoutPanel root, Control control, int height)
    {
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, height));
        root.RowCount++;
        control.Dock = DockStyle.Fill;
        control.Margin = new Padding(0, 1, 0, 3);
        root.Controls.Add(control, 0, root.RowCount - 1);
    }
    private static void Configure(Button b, string text, bool primary, int width)
    {
        b.Text = text;
        b.Width = width;
        b.Height = 37;
        b.FlatStyle = FlatStyle.Flat;
        b.FlatAppearance.BorderSize = 1;
        b.BackColor = ColorTranslator.FromHtml(primary ? "#14594D" : "#F0F4F0");
        b.ForeColor = ColorTranslator.FromHtml(primary ? "#FFFFFF" : "#0B1013");
        b.Cursor = Cursors.Hand;
        b.Font = new Font("Segoe UI", 9.7F, FontStyle.Bold);
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
            _status.Text = "Не удалось открыть локальный порт 21471. Закрой другую копию CELIKOM.";
        }
    }
    private async void LoginAsync(object? sender, EventArgs e)
    {
        _login.Enabled = false;
        try
        {
            await _api.LoginAsync(_origin.Text.Trim(), _email.Text.Trim(), _password.Text);
            _password.Clear();
            _status.Text = "Вход в CELIKOM подтверждён. Нажми «Старт».";
        }
        catch (ApiFailure ex) { _status.Text = ex.Category switch
        {
            "INVALID_CREDENTIALS" => "Неверная почта или пароль.",
            "EMAIL_VERIFICATION_REQUIRED" => "Проверь почту и подтверди аккаунт.",
            "RATE_LIMITED" => "Слишком много попыток входа.",
            _ => "Вход не выполнен. Проверь адрес API и аккаунт."
        }; }
        catch (Exception) { _status.Text = "Не удалось войти. Проверь сеть и адрес API."; }
        finally { UpdateSafe(keepStatus: true); }
    }
    private async void LogoutAsync(object? sender, EventArgs e)
    {
        _bridge.SetEnabled(false);
        _logout.Enabled = false;
        await _api.LogoutAsync();
        _status.Text = "Выход из CELIKOM выполнен на этом устройстве.";
        UpdateSafe(keepStatus: true);
    }
    private void UpdateSafe(bool keepStatus = false)
    {
        if (_closing || IsDisposed) return;
        if (InvokeRequired) { BeginInvoke(new Action(() => UpdateSafe(keepStatus))); return; }
        _logout.Enabled = _api.IsLoggedIn;
        _login.Enabled = true;
        _toggle.Enabled = _api.IsLoggedIn && _bridgeStarted;
        _toggle.Text = _bridge.Enabled ? "Стоп" : "Старт";
        _pairCode.Text = _bridge.PairCode.Length == 6
            ? _bridge.PairCode + "  (10 мин.)"
            : "Код использован. Для нового соединения нажми кнопку.";
        var songStatus = _bridge.LastStatus switch
        {
            "SDK_MAPPING_ACCEPTED" => "Ссылка передана SDK (звук не подтверждён)",
            "RESOLVING" => "Ищем версию",
            "ORIGINAL" => "Воспроизведение оригинала",
            "OFF" => "Подмена выключена",
            "UNAVAILABLE" => "Ожидаем песню",
            "HOST_ERROR" => "Ошибка подключения модуля",
            _ => "Ожидание соединения"
        };
        _nowPlaying.Text = _bridge.LastStatus == "NOT_CONNECTED"
            ? "Модуль Яндекса ещё не подключён."
            : "ID песни: " + (_bridge.LastSong.Length > 0 ? _bridge.LastSong : "—") + " · " + songStatus;
        if (!keepStatus)
            _status.Text = !_bridgeStarted ? "Локальная служба не запущена"
                : !_api.IsLoggedIn ? "Не выполнен вход в CELIKOM"
                : _bridge.Enabled ? "CELIKOM включён. Ожидаем Яндекс." : "CELIKOM готов. Подмена выключена.";
        _tray.Text = _bridge.Enabled && _api.IsLoggedIn ? "CELIKOM — включён" : "CELIKOM — выключено";
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
        await _bridge.DisposeAsync();
        _api.Dispose();
        _tray.Dispose();
        Close();
    }
}
