using System.Drawing;
using System.Windows.Forms;
using Celikom.NativeInstaller;

namespace Celikom.Companion;

// Mirrors the SHIPPED extension/popup/popup.html visual hierarchy:
// header, Start/Stop, original, contribution, access, track, Account, Support, staff.
public sealed partial class MainWindow
{
    private readonly Panel _compactScroll = new();
    private readonly Panel _compactFooter = new();
    private readonly VScrollBar _compactScrollbar = new();
    private readonly Dictionary<Control, int> _compactPositions = new();
    private int _compactScrollTop;
    private int _compactScrollMax;
    private readonly Panel _compactHeader = new();
    private readonly Panel _compactActions = new();
    private readonly PopupButton _compactUploadButton = new();
    private readonly PopupButton _compactSuggestButton = new();
    private readonly Panel _compactUploadBody = new();
    private readonly Panel _compactSuggestBody = new();
    private readonly Label _compactAccess = new();
    private readonly Label _compactTrack = new();
    private readonly Label _compactTrackArtist = new();
    private readonly Label _compactVersionStatus = new();
    private readonly Label _compactStartup = new();
    private readonly Panel _compactUploadResult = new();
    private readonly Label _compactUploadResultTitle = new();
    private readonly Label _compactUploadResultNote = new();
    private readonly Panel _compactSuggestResult = new();
    private readonly Label _compactSuggestResultTitle = new();
    private readonly Label _compactSuggestResultNote = new();
    private readonly ProgressBar _compactUploadProgress = new();
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
    private readonly PopupSelect _compactSupportKind = new();
    private readonly PopupSelect _compactSupportCategory = new();
    private readonly Label _compactSupportDescriptionLabel = Tiny("Опишите проблему", 9);
    private readonly Label _compactUploadDurationCaption = Tiny("Длительность песни, сек", 9);
    private readonly Label _compactUploadDurationKnown = Tiny("", 9);
    private readonly Label _compactSupportCategoryLabel = Tiny("Что произошло?", 9);
    private readonly TextBox _compactSupportText = new();
    private readonly PopupButton _compactSupportSubmit = new();
    private readonly Label _compactSupportMessage = new();
    private readonly Label _compactUploadNote = new();
    private readonly TextBox _compactUploadDuration = new();
    private readonly PopupFilePicker _compactFilePicker = new();
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
    private string _compactUploadView = "error";
    private string _compactSuggestView = "error";
    private string _compactPresenceTrack = "";
    private string _compactPresenceStatus = "";
    private DateTimeOffset _compactPresenceChecked;
    private Task<string>? _compactPresencePending;
    private string _compactPresencePendingTrack = "";
    private Guid _compactUploadRequestId = Guid.NewGuid();
    private int _compactPresenceEpoch;
    private int _compactOpenEpoch;
    private string _compactPinnedUploadTrack = "";
    private string _compactPinnedSuggestTrack = "";
    private string _compactStartupText = "";
    private bool _compactStarting;
    private int _compactStartEpoch;

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
        child.Visible = true; // W63: previous layout hid all account form controls permanently
        if (child.Parent != parent) parent.Controls.Add(child);
    }

    private static Panel Pane() => new() { BackColor = Paper };

    private void BuildCompactPopup()
    {
        _origin.Text = string.IsNullOrWhiteSpace(_api.Origin) ? DefaultApiOrigin : _api.Origin;
        // The browser popup uses a 292px minimum width. Windows retains its
        // native title bar; the *content* is matched without wide tabs.
        ClientSize = new Size(308, 450);
        MinimumSize = new Size(308, 440);
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
        // The standard WinForms AutoScroll changes viewport width during layout
        // and caused the owner's double right gutter / unreachable forms.
        // A stable scrollbar owns the vertical viewport explicitly.
        _compactScroll.AutoScroll = false;
        _compactScroll.TabStop = true;
        _compactScroll.Resize += (_, _) => LayoutCompact();
        _compactScroll.MouseWheel += CompactMouseWheel;
        _compactFooter.Dock = DockStyle.Bottom;
        _compactFooter.Height = 30;
        _compactFooter.BackColor = Paper;
        Controls.Add(_compactFooter);
        Controls.Add(_compactScroll);
        _compactFooter.BringToFront();
        _compactScrollbar.Dock = DockStyle.Right;
        _compactScrollbar.Width = SystemInformation.VerticalScrollBarWidth;
        _compactScrollbar.SmallChange = 30;
        _compactScrollbar.Scroll += (_, e) => SetCompactOffset(e.NewValue);
        _compactScroll.Controls.Add(_compactScrollbar);
        _compactScrollbar.BringToFront();

        _connectionMark.Text = "●";
        _connectionMark.Font = new Font("Segoe UI Symbol", 12F);
        _connectionMark.ForeColor = ColorTranslator.FromHtml("#858B8E");
        _connectionMark.Font = new Font("Segoe UI Symbol", 10F);
        _connectionMark.TextAlign = ContentAlignment.MiddleCenter;
        Place(_connectionMark, _compactHeader, 0, 10, 11, 15);
        var logo = Tiny("CELIKOM", 11, Ink);
        logo.Font = new Font("Segoe UI", 11F, FontStyle.Bold);
        Place(logo, _compactHeader, 15, 8, 97, 24);
        _connectionState.Font = new Font("Segoe UI", 8F);
        _connectionState.ForeColor = Secondary;
        _connectionState.TextAlign = ContentAlignment.MiddleRight;
        Place(_connectionState, _compactHeader, 114, 7, 150, 25);

        ConfigureAuthButton(_start, true, "Старт");
        ConfigureAuthButton(_stop, false, "Стоп");
        _start.Dock = _stop.Dock = DockStyle.None;
        _start.Font = _stop.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
        _start.Click += StartAction;
        _stop.Click += (_, _) =>
        {
            ++_compactStartEpoch;
            _compactStarting = false;
            _compactStartupText = "";
            _bridge.SetEnabled(false);
            RenderCompact();
            LayoutCompact();
        };
        _compactActions.Controls.Add(_start);
        _compactActions.Controls.Add(_stop);

        SetupMainButton(_compactUploadButton, "Загрузить версию", async (_, _) =>
        {
            if (_compactUploadOpen)
            {
                _compactUploadOpen = false;
                ++_compactOpenEpoch;
                LayoutCompact();
                return;
            }
            await OpenCompactContributionAsync(upload: true);
        });
        SetupMainButton(_compactSuggestButton, "Предложить песню", async (_, _) =>
        {
            if (_compactSuggestOpen)
            {
                _compactSuggestOpen = false;
                ++_compactOpenEpoch;
                LayoutCompact();
                return;
            }
            await OpenCompactContributionAsync(upload: false);
        });
        _compactAccess.ForeColor = Accent;
        _compactAccess.Font = new Font("Segoe UI", 9F);
        _compactAccess.Text = _api.IsLoggedIn ? "Проверяем доступ…" : "Войдите в аккаунт, чтобы начать";
        _compactTrack.ForeColor = Secondary;
        _compactTrack.Font = new Font("Segoe UI", 9F);
        _compactTrack.Text = "Запустите трек в Яндекс Музыке";
        _compactTrackArtist.ForeColor = Secondary;
        _compactTrackArtist.Font = new Font("Segoe UI", 8.5F);
        _compactTrackArtist.Text = "";
        _compactTrackArtist.AutoEllipsis = true;
        _compactVersionStatus.Font = new Font("Segoe UI", 8.5F);
        _compactVersionStatus.ForeColor = Secondary;
        _compactVersionStatus.Text = "Версия песни CELIKOM";
        _compactStartup.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        _compactStartup.ForeColor = Accent;
        _compactStartup.Text = "";
        SetupMainButton(_compactAccountTrigger, "Аккаунт · войти", (_, _) =>
        {
            _compactAccountOpen = !_compactAccountOpen;
            LayoutCompact();
            if (_compactAccountOpen) ScrollCompactTo(_compactAccountTrigger);
        });
        SetupMainButton(_compactSupportTrigger, "▸ Связь с поддержкой", (_, _) =>
        {
            _compactSupportOpen = !_compactSupportOpen;
            _compactSupportTrigger.Text = (_compactSupportOpen ? "▾" : "▸") + " Связь с поддержкой";
            LayoutCompact();
            if (_compactSupportOpen) ScrollCompactTo(_compactSupportTrigger);
        });
        _compactSupportTrigger.BackColor = Paper;
        _compactSupportTrigger.ForeColor = Secondary;
        _compactSupportTrigger.TextAlign = ContentAlignment.MiddleLeft;
        _compactSupportTrigger.Font = new Font("Segoe UI", 9F);
        _compactVersion.ForeColor = Quiet;
        _compactVersion.Font = new Font("Segoe UI", 9F);
        _compactVersion.Text = "CELIKOM " + AppUpdateManager.RunningVersion.ToString(3);
        _compactVersion.Location = new Point(16, 6);
        _compactVersion.Size = new Size(250, 20);
        _compactFooter.Controls.Add(_compactVersion);

        BuildCompactAccountBody();
        BuildCompactSupportBody();
        BuildCompactContributions();

        _staffPanel.BackColor = Paper;
        ConfigureAuthButton(_diagnosticsButton, false, "Скопировать диагностику");
        _diagnosticsButton.Dock = DockStyle.None;
        _diagnosticsButton.BackColor = Paper;
        _diagnosticsButton.ForeColor = Quiet;
        _diagnosticsButton.Font = new Font("Segoe UI", 8F);
        _diagnosticsButton.Click += CopyDiagnosticsAuthorized;
        _staffPanel.Controls.Add(_diagnosticsButton);
        _staffPanel.Visible = false;
        _compactReady = true;
        _compactAccountOpen = false; // first-run red CTA; Start expands form on demand

        foreach (var c in new Control[]
        {
            _compactHeader, _compactActions, _compactStartup, _compactUploadButton,
            _compactUploadBody, _compactSuggestButton, _compactSuggestBody,
            _compactAccess, _compactTrack, _compactTrackArtist,
            _compactVersionStatus, _compactAccountTrigger,
            _compactAccountBody, _compactSupportTrigger, _compactSupportBody,
            _staffPanel
        }) _compactScroll.Controls.Add(c);
        _compactScrollbar.BringToFront();
        InstallCompactWheelSupport(_compactScroll);
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
        _compactSupportKind.DropDownWidth = 350;
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
        _compactSupportCategory.DropDownWidth = 310;
        _compactSupportBody.Controls.Add(_compactSupportCategory);
        _compactSupportBody.Controls.Add(_compactSupportCategoryLabel);
        Place(_compactSupportDescriptionLabel, _compactSupportBody, 0, 79, 250, 24);
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
        Place(_compactUploadDurationCaption, _compactUploadBody, 0, 28, 250, 23);
        _compactUploadDurationKnown.ForeColor = Secondary;
        _compactUploadBody.Controls.Add(_compactUploadDurationKnown);
        _compactUploadDuration.PlaceholderText = "Например, 180";
        _compactUploadBody.Controls.Add(_compactDurationInput);
        _compactFilePicker.Click += CompactChooseAudio;
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
        _compactUploadProgress.Visible = false;
        _compactUploadProgress.Style = ProgressBarStyle.Continuous;
        _compactUploadBody.Controls.Add(_compactUploadProgress);
        ConfigureCompactResult(_compactUploadResult, _compactUploadResultTitle, _compactUploadResultNote);
        _compactUploadBody.Controls.Add(_compactUploadResult);

        _compactSuggestTrack.ForeColor = Secondary;
        _compactSuggestBody.Controls.Add(_compactSuggestTrack);
        SetupMainButton(_compactSuggestSubmit, "Отправить предложение", CompactSuggestAsync);
        _compactSuggestBody.Controls.Add(_compactSuggestSubmit);
        _compactSuggestNote.ForeColor = Accent;
        _compactSuggestNote.Font = new Font("Segoe UI", 8F);
        _compactSuggestBody.Controls.Add(_compactSuggestNote);
        ConfigureCompactResult(_compactSuggestResult, _compactSuggestResultTitle, _compactSuggestResultNote);
        _compactSuggestBody.Controls.Add(_compactSuggestResult);
    }

    private static void ConfigureCompactResult(Panel panel, Label heading, Label description)
    {
        panel.BackColor = ColorTranslator.FromHtml("#123B31");
        panel.BorderStyle = BorderStyle.FixedSingle;
        heading.BackColor = panel.BackColor;
        heading.ForeColor = ColorTranslator.FromHtml("#8AFFCF");
        heading.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        description.BackColor = panel.BackColor;
        description.ForeColor = ColorTranslator.FromHtml("#E3F7ED");
        description.Font = new Font("Segoe UI", 8.5F);
        panel.Controls.Add(heading);
        panel.Controls.Add(description);
    }

    private void InstallCompactWheelSupport(Control control)
    {
        foreach (Control child in control.Controls)
        {
            if (child == _compactScrollbar) continue;
            // Native dropdown and multiline editor must retain their own input.
            if (child is not ComboBox && child is not TextBox)
                child.MouseWheel += CompactMouseWheel;
            InstallCompactWheelSupport(child);
        }
    }

    private void CompactMouseWheel(object? sender, MouseEventArgs e)
    {
        if (_compactScrollMax == 0) return;
        var lines = Math.Max(1, SystemInformation.MouseWheelScrollLines);
        var delta = -Math.Sign(e.Delta) * Math.Min(lines, 5) * 30;
        SetCompactOffset(_compactScrollTop + delta);
    }

    private void SetCompactOffset(int value)
    {
        var clamped = Math.Clamp(value, 0, _compactScrollMax);
        if (_compactScrollTop == clamped) return;
        _compactScrollTop = clamped;
        LayoutCompact();
    }

    private void ScrollCompactTo(Control target)
    {
        if (!IsHandleCreated || IsDisposed) return;
        BeginInvoke(new Action(() =>
        {
            if (IsDisposed || !_compactPositions.TryGetValue(target, out var y)) return;
            SetCompactOffset(Math.Max(0, y - 14));
        }));
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
        _signedInIdentity.Text = _api.Email;
        _start.Text = "Старт";
        var nativeStatus = _bridge.LastStatus;
        if (_compactStarting && _bridge.Enabled &&
            nativeStatus is "NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED" or
                "ORIGINAL" or "RESOLVING")
        {
            ++_compactStartEpoch;
            _compactStarting = false;
            _compactStartupText = "";
            if (IsHandleCreated) BeginInvoke(new Action(LayoutCompact));
        }
        _compactStartup.Text = _compactStartupText;

        var id = _bridge.LastSong;
        var valid = GrantValidator.IsTrackId(id);
        if (valid)
        {
            var title = _bridge.LastTrackTitle;
            var artist = _bridge.LastTrackArtist;
            _compactTrack.Text = title.Length > 0 ? title : "Track ID " + id;
            _compactTrackArtist.Text = artist;
        }
        else
        {
            _compactTrack.Text = "Запустите трек в Яндекс Музыке";
            _compactTrackArtist.Text = "";
        }

        _compactUploadTrack.Text = _compactTrack.Text +
            (_compactTrackArtist.Text.Length > 0 ? " — " + _compactTrackArtist.Text : "");
        _compactSuggestTrack.Text = _compactUploadTrack.Text;
        var duration = _bridge.LastTrackDurationMs;
        _compactUploadDurationKnown.Text = duration >= 1000 ?
            "Длительность: " + TimeSpan.FromMilliseconds(duration).ToString(@"m\:ss") : "";

        if (id != _compactPresenceTrack)
        {
            _compactPresenceTrack = valid ? id : "";
            _compactPresenceStatus = "";
            _compactPresenceChecked = DateTimeOffset.MinValue;
            ++_compactPresenceEpoch;
            if (_compactUploadCancellation is null)
            {
                _compactUploadRequestId = Guid.NewGuid();
                _compactUploadOpen = false;
                _compactSuggestOpen = false;
                ++_compactOpenEpoch;
            }
            if (valid && _api.IsLoggedIn && IsHandleCreated)
                _ = RefreshCompactPresenceAsync(id);
        }
        var activelyReplacing = _bridge.Enabled && _bridge.LastStatus ==
            "NATIVE_MAPPING_ACCEPTED" && _compactPresenceStatus == "approved";
        _compactVersionStatus.Text = activelyReplacing ?
            "Подмена активна · версия CELIKOM" :
            !_api.IsLoggedIn ? "Войди, чтобы проверить версию" :
            _compactPresenceStatus switch
            {
                "approved" => "Версия песни CELIKOM доступна для подмены",
                "pending" => "Версия песни CELIKOM на проверке",
                "none" => "Версия песни CELIKOM ещё не загружена",
                "error" => "Не удалось проверить версию песни CELIKOM",
                _ => "Проверяем версию песни CELIKOM…"
            };
        _compactVersionStatus.ForeColor =
            activelyReplacing || _compactPresenceStatus == "approved" ? Accent :
            _compactPresenceStatus == "pending" ? ColorTranslator.FromHtml("#FFE1A1") : Secondary;
        _compactUploadButton.Enabled = _api.IsLoggedIn && !_compactContributionBusy;
        _compactSuggestButton.Enabled = _api.IsLoggedIn && !_compactContributionBusy;
        _compactSuggestSubmit.Enabled = _api.IsLoggedIn &&
            valid && !_compactContributionBusy && _compactSuggestView == "form";
        _compactUploadSubmit.Enabled = _api.IsLoggedIn &&
            valid && (_compactUploadCancellation is not null || _compactUploadView == "form");
        _compactAccountBody.Invalidate();
    }

    private void LayoutCompact()
    {
        if (!_compactReady || _compactLayoutBusy || _compactScroll.IsDisposed) return;
        _compactLayoutBusy = true;
        try
        {
            _compactScroll.SuspendLayout();
            var hasTrack = GrantValidator.IsTrackId(_bridge.LastSong);
            var rows = new (Control item, int height, int gap, bool visible)[]
            {
                (_compactHeader, 34, 7, true),
                (_compactActions, 40, 8, true),
                (_compactStartup, 45, 8, !string.IsNullOrWhiteSpace(_compactStartupText)),
                (_compactUploadButton, 40, 8, true),
                (_compactUploadBody, _compactUploadView == "form" ?
                    (_bridge.LastTrackDurationMs >= 1000 ? 310 : 356) : 126, 8,
                    _compactUploadOpen),
                (_compactSuggestButton, 40, 12, true),
                (_compactSuggestBody, _compactSuggestView == "form"
                    ? (string.IsNullOrWhiteSpace(_compactSuggestNote.Text) ? 92 : 128)
                    : 126, 8, _compactSuggestOpen),
                (_compactAccess, 35, 8, true),
                (_compactTrack, 32, 0, true),
                (_compactTrackArtist, 25, 3, !string.IsNullOrWhiteSpace(_compactTrackArtist.Text)),
                (_compactVersionStatus, 40, 8, hasTrack),
                (_compactAccountTrigger, 44, 8, true),
                (_compactAccountBody, CompactAccountHeight(), 8, _compactAccountOpen),
                (_compactSupportTrigger, 29, 8, true),
                (_compactSupportBody, _compactSupportKind.SelectedIndex == 1 ? 373 : 296,
                    8, _compactSupportOpen),
                (_staffPanel, 29, 8, _diagnosticsAllowed)
            };
            var contentHeight = 18 + rows.Where(r => r.visible).Sum(r => r.height + r.gap);
            _compactScrollMax = Math.Max(0, contentHeight - _compactScroll.ClientSize.Height);
            _compactScrollTop = Math.Clamp(_compactScrollTop, 0, _compactScrollMax);
            var showBar = _compactScrollMax > 0;
            _compactScrollbar.Visible = showBar;
            if (showBar)
            {
                _compactScrollbar.Minimum = 0;
                _compactScrollbar.LargeChange = Math.Max(1, _compactScroll.ClientSize.Height);
                _compactScrollbar.Maximum = Math.Max(
                    _compactScrollbar.LargeChange - 1, contentHeight - 1);
                _compactScrollbar.Value = _compactScrollTop;
            }
            var viewportWidth = _compactScroll.ClientSize.Width -
                (showBar ? _compactScrollbar.Width : 0);
            var width = Math.Max(190, viewportWidth - 32);
            _compactPositions.Clear();
            int y = 15;
            foreach (var row in rows)
            {
                row.item.Visible = row.visible;
                if (!row.visible) continue;
                _compactPositions[row.item] = y;
                row.item.SetBounds(16, y - _compactScrollTop, width, row.height);
                y += row.height + row.gap;
            }
            // Viewport and footer do not move. Content alone translates.
            _connectionState.SetBounds(Math.Max(112, width - 136), 7,
                Math.Min(136, width - 112), 23);
            _start.SetBounds(0, 0, (width - 8) / 2, 40);
            _stop.SetBounds((width + 8) / 2, 0, (width - 8) / 2, 40);
            Place(_diagnosticsButton, _staffPanel, 0, 0, width, 28);
            LayoutCompactAccount(width);
            LayoutCompactSupport(width);
            LayoutCompactContributions(width);
            _compactScrollbar.BringToFront();
        }
        finally { _compactScroll.ResumeLayout(false); _compactLayoutBusy = false; }
    }

    private int CompactAccountHeight() => _api.IsLoggedIn ?
        (_compactPromoOpen ? 270 : 132) :
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
            // Same order as extension/popup/popup.html:
            // Promo section, signed-in identity, then sign out.
            Place(_compactPromoToggle, _compactAccountBody, 0, 5, w, 35);
            if (_compactPromoOpen)
            {
                Place(_compactPromoInput, _compactAccountBody, 0, 49, w, 42);
                Place(_compactPromoSubmit, _compactAccountBody, 0, 100, w, 40);
                Place(_compactPromoMessage, _compactAccountBody, 0, 146, w, 44);
            }
            Place(_signedInIdentity, _compactAccountBody, 0,
                _compactPromoOpen ? 199 : 48, w, 26);
            Place(_logout, _compactAccountBody, 0,
                _compactPromoOpen ? 230 : 81, w, 40);
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
        Place(_compactSupportDescriptionLabel, _compactSupportBody, 0,
            song ? 145 : 78, w, 24);
        Place(_compactSupportText, _compactSupportBody, 0, song ? 174 : 109, w, 94);
        Place(_compactSupportSubmit, _compactSupportBody, 0, song ? 275 : 209, w, 40);
        Place(_compactSupportMessage, _compactSupportBody, 0, song ? 324 : 256, w, 48);
    }

    private void LayoutCompactContributions(int w)
    {
        bool form = _compactUploadView == "form";
        bool result = _compactUploadView == "result";
        foreach (var child in new Control[] {
            _compactUploadTrack, _compactUploadDurationCaption,
            _compactDurationInput, _compactUploadDurationKnown, _compactFilePicker,
            _compactFileName, _compactRights, _compactUploadSubmit,
            _compactUploadNote, _compactUploadProgress, _compactUploadResult
        }) child.Visible = false;
        if (form)
        {
            Place(_compactUploadTrack, _compactUploadBody, 0, 0, w, 28);
            var known = _bridge.LastTrackDurationMs >= 1000;
            Place(known ? _compactUploadDurationKnown : _compactUploadDurationCaption,
                _compactUploadBody, 0, 30, w, 21);
            if (!known) Place(_compactDurationInput, _compactUploadBody, 0, 51, w, 38);
            Place(_compactFilePicker, _compactUploadBody, 0, known ? 54 : 96, w, 74);
            Place(_compactFileName, _compactUploadBody, 0, known ? 132 : 174, w, 24);
            Place(_compactRights, _compactUploadBody, 0, known ? 162 : 206, w, 31);
            Place(_compactUploadSubmit, _compactUploadBody, 0, known ? 202 : 246, w, 40);
            if (_compactUploadCancellation is not null)
                Place(_compactUploadProgress, _compactUploadBody, 0,
                    known ? 248 : 292, w, 13);
            Place(_compactUploadNote, _compactUploadBody, 0,
                known ? 266 : 309, w, 45);
        }
        else if (result)
        {
            Place(_compactUploadResult, _compactUploadBody, 0, 0, w, 112);
            Place(_compactUploadResultTitle, _compactUploadResult, 12, 12, w - 24, 28);
            Place(_compactUploadResultNote, _compactUploadResult, 12, 44, w - 24, 65);
        }
        else
        {
            Place(_compactUploadNote, _compactUploadBody, 0, 0, w, 110);
        }

        _compactSuggestResult.Visible = _compactSuggestView == "result";
        _compactSuggestTrack.Visible = _compactSuggestView == "form";
        _compactSuggestSubmit.Visible = _compactSuggestView == "form";
        _compactSuggestNote.Visible = _compactSuggestView is "error" or "checking" or "form";
        if (_compactSuggestView == "result")
        {
            Place(_compactSuggestResult, _compactSuggestBody, 0, 0, w, 114);
            Place(_compactSuggestResultTitle, _compactSuggestResult, 12, 12, w - 24, 27);
            Place(_compactSuggestResultNote, _compactSuggestResult, 12, 43, w - 24, 68);
        }
        else if (_compactSuggestView == "form")
        {
            Place(_compactSuggestTrack, _compactSuggestBody, 0, 0, w, 28);
            Place(_compactSuggestSubmit, _compactSuggestBody, 0, 36, w, 40);
            Place(_compactSuggestNote, _compactSuggestBody, 0, 80, w, 38);
        }
        else Place(_compactSuggestNote, _compactSuggestBody, 0, 0, w, 110);
    }

}
