using System.Drawing;
using System.Windows.Forms;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

// Mirrors the SHIPPED extension/popup/popup.html visual hierarchy:
// header, Start/Stop, original, contribution, access, track, Account, Support, staff.
public sealed partial class MainWindow
{
    private readonly Panel _compactScroll = new();
    private readonly Panel _compactHeader = new();
    private readonly Panel _compactActions = new();
    private readonly PopupButton _compactOriginal = new();
    private readonly PopupButton _compactUploadButton = new();
    private readonly PopupButton _compactSuggestButton = new();
    private readonly Panel _compactUploadBody = new();
    private readonly Panel _compactSuggestBody = new();
    private readonly Label _compactAccess = new();
    private readonly Label _compactTrack = new();
    private readonly PopupButton _compactAccountTrigger = new();
    private readonly Panel _compactAccountBody = new();
    private readonly PopupButton _compactSupportTrigger = new();
    private readonly Panel _compactSupportBody = new();
    private readonly Label _compactVersion = new();
    private readonly TextBox _compactCode = new();
    private readonly TextBox _compactNewPassword = new();
    private readonly PopupButton _compactModeButton = new();
    private readonly PopupButton _compactForgotButton = new();
    private readonly Label _compactAccountMessage = new();
    private readonly PopupButton _compactPromoToggle = new();
    private readonly TextBox _compactPromoCode = new();
    private readonly PopupButton _compactPromoSubmit = new();
    private readonly Label _compactPromoMessage = new();
    private readonly ComboBox _compactSupportKind = new();
    private readonly ComboBox _compactSupportCategory = new();
    private readonly Label _compactSupportCategoryLabel = Tiny("Что произошло?", 9);
    private readonly TextBox _compactSupportText = new();
    private readonly PopupButton _compactSupportSubmit = new();
    private readonly Label _compactSupportMessage = new();
    private readonly Label _compactUploadNote = new();
    private readonly TextBox _compactUploadDuration = new();
    private readonly PopupButton _compactFilePicker = new();
    private readonly Label _compactFileName = new();
    private readonly CheckBox _compactRights = new();
    private readonly PopupButton _compactUploadSubmit = new();
    private readonly Label _compactSuggestNote = new();
    private readonly PopupButton _compactSuggestSubmit = new();
    private readonly Label _compactUploadTrack = new();
    private readonly Label _compactSuggestTrack = new();
    private readonly Label _compactEmailLabel = new();
    private readonly Label _compactPasswordLabel = new();
    private PopupInput _compactEmailInput = null!;
    private PopupInput _compactPasswordInput = null!;
    private PopupInput _compactCodeInput = null!;
    private PopupInput _compactNewPasswordInput = null!;
    private PopupInput _compactPromoInput = null!;
    private PopupInput _compactDurationInput = null!;

    private bool _compactReady;
    private bool _compactLayoutBusy;
    private bool _compactAccountOpen;
    private bool _compactSupportOpen;
    private bool _compactPromoOpen;
    private bool _compactUploadOpen;
    private bool _compactSuggestOpen;
    private string _compactAccountMode = "login";
    private string? _compactSelectedAudio;
    private string? _compactPendingEmail;
    private int _compactAccessGeneration;
    private bool _compactAccessBusy;
    private DateTimeOffset _compactAccessChecked;
    private bool _compactSupportBusy;
    private bool _compactPromoBusy;
    private bool _compactContributionBusy;

    private static readonly Color Quiet = ColorTranslator.FromHtml("#788991");

    private static Label Tiny(string value = "", int font = 11, Color? color = null)
        => new() { Text = value, BackColor = Paper, ForeColor = color ?? Secondary,
            Font = new Font("Segoe UI", font), AutoEllipsis = false };

    private static PopupButton CompactButton(string value, bool primary = false)
    {
        var b = new PopupButton();
        ConfigureAuthButton(b, primary, value);
        b.Dock = DockStyle.None; // absolute compact stacking, never overlap sibling actions
        b.Font = new Font("Segoe UI", 9F, primary ? FontStyle.Bold : FontStyle.Regular);
        return b;
    }

    private static void Place(Control child, Control parent, int x, int y, int width, int height)
    {
        child.Location = new Point(x, y);
        child.Size = new Size(Math.Max(10, width), height);
        if (child.Parent != parent) parent.Controls.Add(child);
    }

    private static Panel Pane() => new() { BackColor = Paper };

    private void BuildCompactPopup()
    {
        _origin.Text = string.IsNullOrWhiteSpace(_api.Origin) ? DefaultApiOrigin : _api.Origin;
        // The browser popup uses a 292px minimum width. Windows retains its
        // native title bar; the *content* is matched without wide tabs.
        ClientSize = new Size(308, 515);
        MinimumSize = new Size(308, 490);
        MaximumSize = new Size(308, 820);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        Font = new Font("Segoe UI", 9F);
        BackColor = Paper;
        _compactEmailInput = new PopupInput(_email);
        _compactPasswordInput = new PopupInput(_password);
        _compactCodeInput = new PopupInput(_compactCode);
        _compactNewPasswordInput = new PopupInput(_compactNewPassword);
        _compactPromoInput = new PopupInput(_compactPromoCode);
        _compactDurationInput = new PopupInput(_compactUploadDuration);

        _compactScroll.Dock = DockStyle.Fill;
        _compactScroll.BackColor = Paper;
        _compactScroll.AutoScroll = true;
        _compactScroll.Resize += (_, _) => LayoutCompact();
        Controls.Add(_compactScroll);

        _connectionMark.Text = "●";
        _connectionMark.Font = new Font("Segoe UI Symbol", 12F);
        _connectionMark.ForeColor = ColorTranslator.FromHtml("#858B8E");
        Place(_connectionMark, _compactHeader, 0, 5, 17, 24);
        var logo = Tiny("CELIKOM", 11, Ink);
        logo.Font = new Font("Segoe UI", 11F, FontStyle.Bold);
        Place(logo, _compactHeader, 19, 8, 92, 24);
        _connectionState.Font = new Font("Segoe UI", 8F);
        _connectionState.ForeColor = Secondary;
        _connectionState.TextAlign = ContentAlignment.MiddleRight;
        Place(_connectionState, _compactHeader, 114, 7, 150, 25);

        ConfigureAuthButton(_start, true, "Старт");
        ConfigureAuthButton(_stop, false, "Стоп");
        _start.Dock = _stop.Dock = DockStyle.None;
        _start.Font = _stop.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
        _start.Click += StartAction;
        _stop.Click += (_, _) => _bridge.SetEnabled(false);
        _compactActions.Controls.Add(_start);
        _compactActions.Controls.Add(_stop);

        SetupMainButton(_compactOriginal, "Вернуть оригинал", (_, _) => _bridge.SetEnabled(false));
        SetupMainButton(_compactUploadButton, "Загрузить версию", (_, _) =>
        {
            _compactUploadOpen = !_compactUploadOpen;
            _compactSuggestOpen = false;
            LayoutCompact();
        });
        SetupMainButton(_compactSuggestButton, "Предложить песню", (_, _) =>
        {
            _compactSuggestOpen = !_compactSuggestOpen;
            _compactUploadOpen = false;
            LayoutCompact();
        });
        _compactAccess.ForeColor = Accent;
        _compactAccess.Font = new Font("Segoe UI", 9F);
        _compactAccess.Text = _api.IsLoggedIn ? "Проверяем доступ…" : "Войдите в аккаунт, чтобы начать";
        _compactTrack.ForeColor = Secondary;
        _compactTrack.Font = new Font("Segoe UI", 9F);
        _compactTrack.Text = "Запустите трек в Яндекс Музыке";
        SetupMainButton(_compactAccountTrigger, "Аккаунт · войти", (_, _) =>
        {
            _compactAccountOpen = !_compactAccountOpen;
            LayoutCompact();
        });
        SetupMainButton(_compactSupportTrigger, "▸ Связь с поддержкой", (_, _) =>
        {
            _compactSupportOpen = !_compactSupportOpen;
            _compactSupportTrigger.Text = (_compactSupportOpen ? "▾" : "▸") + " Связь с поддержкой";
            LayoutCompact();
        });
        _compactSupportTrigger.BackColor = Paper;
        _compactSupportTrigger.ForeColor = Secondary;
        _compactSupportTrigger.TextAlign = ContentAlignment.MiddleLeft;
        _compactSupportTrigger.Font = new Font("Segoe UI", 9F);
        _compactVersion.ForeColor = Quiet;
        _compactVersion.Font = new Font("Segoe UI", 8F);
        _compactVersion.Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3);

        BuildCompactAccountBody();
        BuildCompactSupportBody();
        BuildCompactContributions();

        _staffPanel.BackColor = Paper;
        ConfigureAuthButton(_diagnosticsButton, false, "Скопировать диагностику");
        _diagnosticsButton.Dock = DockStyle.None;
        _diagnosticsButton.BackColor = Paper;
        _diagnosticsButton.ForeColor = Quiet;
        _diagnosticsButton.Font = new Font("Segoe UI", 8F);
        _diagnosticsButton.Click += SaveDiagnosticsAuthorized;
        _staffPanel.Controls.Add(_diagnosticsButton);
        _staffPanel.Visible = false;
        _compactReady = true;
        _compactAccountOpen = false; // first-run red CTA; Start expands form on demand

        foreach (var c in new Control[]
        {
            _compactHeader, _compactActions, _compactOriginal, _compactUploadButton,
            _compactUploadBody, _compactSuggestButton, _compactSuggestBody,
            _compactAccess, _compactTrack, _compactAccountTrigger,
            _compactAccountBody, _compactSupportTrigger, _compactSupportBody,
            _staffPanel, _compactVersion
        }) _compactScroll.Controls.Add(c);
        RenderCompact();
        LayoutCompact();
    }

    private static void SetupMainButton(PopupButton b, string caption, EventHandler clicked)
    {
        ConfigureAuthButton(b, false, caption);
        b.Dock = DockStyle.None;
        b.Font = new Font("Segoe UI", 9F);
        b.Click += clicked;
    }

    private void BuildCompactAccountBody()
    {
        _compactAccountBody.BackColor = Paper;
        _email.Text = _api.Email;
        _email.PlaceholderText = "Email";
        _password.UseSystemPasswordChar = true;
        _password.PlaceholderText = "Пароль";
        _compactCode.PlaceholderText = "Код из письма";
        _compactNewPassword.PlaceholderText = "Новый пароль";
        _compactNewPassword.UseSystemPasswordChar = true;
        _compactEmailLabel.Text = "Email";
        _compactPasswordLabel.Text = "Пароль";
        _compactEmailLabel.ForeColor = _compactPasswordLabel.ForeColor = Secondary;
        _compactEmailLabel.Font = _compactPasswordLabel.Font = new Font("Segoe UI", 9F);
        _compactAccountMessage.ForeColor = Accent;
        _compactAccountMessage.Font = new Font("Segoe UI", 9F);
        _compactAccountMessage.AutoEllipsis = false;
        ConfigureAuthButton(_login, true, "Войти");
        _login.Dock = DockStyle.None;
        _login.Click += CompactAccountSubmitAsync;
        SetupMainButton(_compactModeButton, "Создать аккаунт", (_, _) =>
        {
            _compactAccountMode = _compactAccountMode == "login" ? "register" : "login";
            _compactAccountMessage.Text = "";
            LayoutCompact();
        });
        SetupMainButton(_compactForgotButton, "Забыли пароль?", (_, _) =>
        {
            _compactAccountMode = "recovery";
            _compactAccountMessage.Text = "";
            LayoutCompact();
        });
        _compactModeButton.BackColor = _compactForgotButton.BackColor = Paper;
        _compactForgotButton.ForeColor = Secondary;
        _signedInIdentity.Font = new Font("Segoe UI", 9F);
        _signedInIdentity.ForeColor = Secondary;
        SetupMainButton(_compactPromoToggle, "▸ Промокод", (_, _) =>
        {
            _compactPromoOpen = !_compactPromoOpen;
            _compactPromoToggle.Text = (_compactPromoOpen ? "▾" : "▸") + " Промокод";
            LayoutCompact();
        });
        _compactPromoToggle.BackColor = Paper;
        _compactPromoToggle.ForeColor = Secondary;
        _compactPromoCode.PlaceholderText = "Промокод";
        _compactPromoCode.MaxLength = 64;
        SetupMainButton(_compactPromoSubmit, "Активировать", CompactPromoSubmitAsync);
        _compactPromoMessage.ForeColor = Accent;
        _compactPromoMessage.Font = new Font("Segoe UI", 8F);
        ConfigureAuthButton(_logout, false, "Выйти");
        _logout.Dock = DockStyle.None;
        _logout.Click += LogoutAsync;
        foreach (var child in new Control[]
        {
            _compactEmailLabel, _compactEmailInput, _compactPasswordLabel,
            _compactPasswordInput, _compactCodeInput, _compactNewPasswordInput,
            _login, _compactModeButton, _compactForgotButton, _compactAccountMessage,
            _signedInIdentity, _compactPromoToggle, _compactPromoInput,
            _compactPromoSubmit, _compactPromoMessage, _logout
        }) _compactAccountBody.Controls.Add(child);
    }

    private void BuildCompactSupportBody()
    {
        var label = Tiny("Вид обращения", 9);
        Place(label, _compactSupportBody, 0, 1, 250, 24);
        _compactSupportKind.DropDownStyle = ComboBoxStyle.DropDownList;
        _compactSupportKind.Items.AddRange(new object[]{
            "Обычное обращение · ответ по почте", "Проблема с текущей песней"
        });
        _compactSupportKind.SelectedIndex = 0;
        _compactSupportKind.SelectedIndexChanged += (_, _) => LayoutCompact();
        _compactSupportKind.BackColor = Surface;
        _compactSupportKind.ForeColor = Ink;
        _compactSupportKind.FlatStyle = FlatStyle.Flat;
        _compactSupportBody.Controls.Add(_compactSupportKind);
        _compactSupportCategory.Items.AddRange(new object[] {
            "Не включается версия CELIKOM",
            "Играет неправильная версия",
            "Звук обрывается или рассинхронизируется",
            "Другая проблема"
        });
        _compactSupportCategory.SelectedIndex = 0;
        _compactSupportCategory.DropDownStyle = ComboBoxStyle.DropDownList;
        _compactSupportCategory.BackColor = Surface;
        _compactSupportCategory.ForeColor = Ink;
        _compactSupportCategory.FlatStyle = FlatStyle.Flat;
        _compactSupportBody.Controls.Add(_compactSupportCategory);
        _compactSupportBody.Controls.Add(_compactSupportCategoryLabel);
        var description = Tiny("Опишите проблему", 9);
        Place(description, _compactSupportBody, 0, 79, 250, 24);
        _compactSupportText.Multiline = true;
        _compactSupportText.MaxLength = 2000;
        _compactSupportText.ScrollBars = ScrollBars.Vertical;
        _compactSupportText.BackColor = Surface;
        _compactSupportText.ForeColor = Ink;
        _compactSupportText.BorderStyle = BorderStyle.FixedSingle;
        _compactSupportBody.Controls.Add(_compactSupportText);
        SetupMainButton(_compactSupportSubmit, "Отправить", CompactSendSupportAsync);
        _compactSupportBody.Controls.Add(_compactSupportSubmit);
        _compactSupportMessage.ForeColor = Accent;
        _compactSupportMessage.Font = new Font("Segoe UI", 8F);
        _compactSupportMessage.AutoEllipsis = false;
        _compactSupportBody.Controls.Add(_compactSupportMessage);
    }

    private void BuildCompactContributions()
    {
        _compactUploadTrack.ForeColor = Secondary;
        _compactUploadTrack.Text = "Текущая песня не определена";
        _compactUploadBody.Controls.Add(_compactUploadTrack);
        var durationLabel = Tiny("Длительность песни, сек", 9);
        Place(durationLabel, _compactUploadBody, 0, 28, 250, 23);
        _compactUploadDuration.PlaceholderText = "Например, 180";
        _compactUploadBody.Controls.Add(_compactDurationInput);
        SetupMainButton(_compactFilePicker, "Выбрать MP3 / M4A", CompactChooseAudio);
        _compactUploadBody.Controls.Add(_compactFilePicker);
        _compactFileName.ForeColor = Secondary;
        _compactUploadBody.Controls.Add(_compactFileName);
        _compactRights.Text = "Подтверждаю права на аудиофайл";
        _compactRights.ForeColor = Secondary;
        _compactRights.BackColor = Paper;
        _compactRights.Font = new Font("Segoe UI", 8F);
        _compactUploadBody.Controls.Add(_compactRights);
        SetupMainButton(_compactUploadSubmit, "Отправить на проверку", CompactUploadAsync);
        _compactUploadBody.Controls.Add(_compactUploadSubmit);
        _compactUploadNote.ForeColor = Accent;
        _compactUploadNote.Font = new Font("Segoe UI", 8F);
        _compactUploadBody.Controls.Add(_compactUploadNote);

        _compactSuggestTrack.ForeColor = Secondary;
        _compactSuggestBody.Controls.Add(_compactSuggestTrack);
        SetupMainButton(_compactSuggestSubmit, "Отправить предложение", CompactSuggestAsync);
        _compactSuggestBody.Controls.Add(_compactSuggestSubmit);
        _compactSuggestNote.ForeColor = Accent;
        _compactSuggestNote.Font = new Font("Segoe UI", 8F);
        _compactSuggestBody.Controls.Add(_compactSuggestNote);
    }

    private void RenderCompact()
    {
        if (!_compactReady) return;
        var connected = _bridgeStarted && _api.IsLoggedIn &&
            _nativeInstallState == NativeInstallState.Active &&
            _installedModule.MatchesApplication;
        _compactAccountTrigger.Text = _api.IsLoggedIn ? "Аккаунт · подключён" :
            "Аккаунт · требуется вход";
        _compactAccountTrigger.BackColor = !_api.IsLoggedIn ? Danger : Surface;
        _compactAccountTrigger.ForeColor = !_api.IsLoggedIn ? Color.White : Ink;
        _compactAccountTrigger.Invalidate();
        _start.Text = !_api.IsLoggedIn ? "Старт" : connected ? "Старт" : "Повторить";
        _compactTrack.Text = GrantValidator.IsTrackId(_bridge.LastSong)
            ? "Track ID " + _bridge.LastSong : "Запустите трек в Яндекс Музыке";
        _compactUploadTrack.Text = GrantValidator.IsTrackId(_bridge.LastSong)
            ? "Track ID " + _bridge.LastSong : "Сначала запустите песню в Яндексе";
        _compactSuggestTrack.Text = _compactUploadTrack.Text;
        _compactOriginal.Enabled = connected && _bridge.Enabled;
        _compactSuggestSubmit.Enabled = _api.IsLoggedIn && GrantValidator.IsTrackId(_bridge.LastSong);
        _compactUploadSubmit.Enabled = _api.IsLoggedIn && GrantValidator.IsTrackId(_bridge.LastSong);
        _compactAccountBody.Invalidate();
    }

    private void LayoutCompact()
    {
        if (!_compactReady || _compactLayoutBusy || _compactScroll.IsDisposed) return;
        _compactLayoutBusy = true;
        try
        {
            _compactScroll.SuspendLayout();
            var dimensions = new (Control item, int height, int gap, bool visible)[]
            {
                (_compactHeader, 34, 7, true),
                (_compactActions, 40, 8, true),
                (_compactOriginal, 40, 8, true),
                (_compactUploadButton, 40, 8, true),
                (_compactUploadBody, 276, 8, _compactUploadOpen),
                (_compactSuggestButton, 40, 16, true),
                (_compactSuggestBody, 117, 8, _compactSuggestOpen),
                (_compactAccess, 35, 8, true),
                (_compactTrack, 38, 11, true),
                (_compactAccountTrigger, 44, 8, true),
                (_compactAccountBody, CompactAccountHeight(), 8, _compactAccountOpen),
                (_compactSupportTrigger, 29, 8, true),
                (_compactSupportBody, _compactSupportKind.SelectedIndex == 1 ? 364 : 284, 8, _compactSupportOpen),
                (_staffPanel, 29, 1, _diagnosticsAllowed),
                (_compactVersion, 19, 6, true)
            };
            int needed = 16;
            foreach (var row in dimensions) if (row.visible) needed += row.height + row.gap;
            var scrollWidth = needed > _compactScroll.ClientSize.Height ?
                SystemInformation.VerticalScrollBarWidth : 0;
            int width = Math.Max(215, _compactScroll.ClientSize.Width - 32 - scrollWidth);
            int y = 15;
            foreach (var row in dimensions)
            {
                row.item.Visible = row.visible;
                if (!row.visible) continue;
                row.item.SetBounds(16, y, width, row.height);
                y += row.height + row.gap;
            }
            _compactScroll.AutoScrollMinSize = new Size(0, y);
            _connectionState.SetBounds(Math.Max(112, width - 136), 7, Math.Min(136, width - 112), 23);
            _start.SetBounds(0, 0, (width - 8) / 2, 40);
            _stop.SetBounds((width + 8) / 2, 0, (width - 8) / 2, 40);
            Place(_diagnosticsButton, _staffPanel, 0, 0, width, 28);
            LayoutCompactAccount(width);
            LayoutCompactSupport(width);
            LayoutCompactContributions(width);
        }
        finally { _compactScroll.ResumeLayout(false); _compactLayoutBusy = false; }
    }

    private int CompactAccountHeight() => _api.IsLoggedIn ?
        (_compactPromoOpen ? 242 : 112) :
        _compactAccountMode is "login" or "register" ? 326 :
        _compactAccountMode is "verify" ? 256 :
        _compactAccountMode is "recovery" ? 207 : 308;

    private void LayoutCompactAccount(int w)
    {
        bool signed = _api.IsLoggedIn;
        bool login = _compactAccountMode is "login" or "register";
        bool verify = _compactAccountMode == "verify";
        bool recovery = _compactAccountMode == "recovery";
        bool reset = _compactAccountMode == "reset";
        foreach (var c in new Control[] { _compactEmailLabel,_compactEmailInput,
            _compactPasswordLabel,_compactPasswordInput,_compactCodeInput,
            _compactNewPasswordInput,_login,_compactModeButton,_compactForgotButton,
            _compactAccountMessage,_signedInIdentity,_compactPromoToggle,
            _compactPromoInput,_compactPromoSubmit,_compactPromoMessage,_logout }) c.Visible = false;

        if (signed)
        {
            Place(_signedInIdentity, _compactAccountBody, 0, 0, w, 27);
            Place(_compactPromoToggle, _compactAccountBody, 0, 30, w, 32);
            if (_compactPromoOpen)
            {
                Place(_compactPromoInput, _compactAccountBody, 0, 67, w, 42);
                Place(_compactPromoSubmit, _compactAccountBody, 0, 115, w, 40);
                Place(_compactPromoMessage, _compactAccountBody, 0, 159, w, 37);
            }
            Place(_logout, _compactAccountBody, 0, _compactPromoOpen ? 200 : 69, w, 40);
            return;
        }
        _compactEmailLabel.Text = "Email";
        Place(_compactEmailLabel, _compactAccountBody, 0, 2, w, 23);
        Place(_compactEmailInput, _compactAccountBody, 0, 27, w, 42);
        if (login)
        {
            _compactPasswordLabel.Text = "Пароль";
            Place(_compactPasswordLabel, _compactAccountBody, 0, 77, w, 23);
            Place(_compactPasswordInput, _compactAccountBody, 0, 102, w, 42);
            _login.Text = _compactAccountMode == "register" ? "Зарегистрироваться" : "Войти";
            Place(_login, _compactAccountBody, 0, 152, w, 40);
            _compactModeButton.Text = _compactAccountMode == "register" ? "Уже есть аккаунт? Войти" : "Создать аккаунт";
            Place(_compactModeButton, _compactAccountBody, 0, 197, w, 38);
            if (_compactAccountMode == "login")
                Place(_compactForgotButton, _compactAccountBody, 0, 241, w, 33);
            Place(_compactAccountMessage, _compactAccountBody, 0, 274, w, 45);
        }
        else if (recovery)
        {
            _login.Text = "Получить код";
            Place(_login, _compactAccountBody, 0, 75, w, 40);
            Place(_compactModeButton, _compactAccountBody, 0, 121, w, 33);
            _compactModeButton.Text = "Вернуться ко входу";
            Place(_compactAccountMessage, _compactAccountBody, 0, 160, w, 46);
        }
        else
        {
            // Verification and password reset share the known account email.
            _compactCode.PlaceholderText = "Шестизначный код из письма";
            Place(_compactCodeInput, _compactAccountBody, 0, 79, w, 42);
            if (reset)
                Place(_compactNewPasswordInput, _compactAccountBody, 0, 128, w, 42);
            _login.Text = verify ? "Подтвердить почту" : "Изменить пароль";
            Place(_login, _compactAccountBody, 0, reset ? 178 : 130, w, 40);
            _compactModeButton.Text = "Вернуться ко входу";
            Place(_compactModeButton, _compactAccountBody, 0, reset ? 225 : 176, w, 34);
            Place(_compactAccountMessage, _compactAccountBody, 0, reset ? 264 : 215, w, 38);
        }
    }

    private void LayoutCompactSupport(int w)
    {
        var song = _compactSupportKind.SelectedIndex == 1;
        Place(_compactSupportKind, _compactSupportBody, 0, 27, w, 39);
        _compactSupportCategory.Visible = song;
        _compactSupportCategoryLabel.Visible = song;
        if (song)
        {
            Place(_compactSupportCategoryLabel, _compactSupportBody, 0, 73, w, 22);
            Place(_compactSupportCategory, _compactSupportBody, 0, 98, w, 39);
        }
        Place(_compactSupportText, _compactSupportBody, 0, song ? 164 : 109, w, 90);
        Place(_compactSupportSubmit, _compactSupportBody, 0, song ? 264 : 206, w, 40);
        Place(_compactSupportMessage, _compactSupportBody, 0, song ? 312 : 249, w, 49);
    }

    private void LayoutCompactContributions(int w)
    {
        Place(_compactUploadTrack, _compactUploadBody, 0, 0, w, 26);
        Place(_compactDurationInput, _compactUploadBody, 0, 54, w, 38);
        Place(_compactFilePicker, _compactUploadBody, 0, 99, w, 40);
        Place(_compactFileName, _compactUploadBody, 0, 140, w, 28);
        Place(_compactRights, _compactUploadBody, 0, 170, w, 23);
        Place(_compactUploadSubmit, _compactUploadBody, 0, 201, w, 40);
        Place(_compactUploadNote, _compactUploadBody, 0, 245, w, 30);
        Place(_compactSuggestTrack, _compactSuggestBody, 0, 0, w, 27);
        Place(_compactSuggestSubmit, _compactSuggestBody, 0, 34, w, 40);
        Place(_compactSuggestNote, _compactSuggestBody, 0, 78, w, 39);
    }
}
