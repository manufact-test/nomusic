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
    private readonly TableLayoutPanel _compactFrame = new();
    private readonly PopupThinScroll _compactScrollbar = new();
    private readonly Dictionary<Control, int> _compactPositions = new();
    private int _compactScrollTop;
    private int _compactScrollMax;
    private readonly Panel _compactHeader = new();
    private readonly Panel _compactActions = new();
    private readonly PopupButton _compactUploadButton = new();
    private readonly PopupButton _compactSuggestButton = new();
    private readonly PopupSectionPanel _compactUploadBody = new();
    private readonly PopupSectionPanel _compactSuggestBody = new();
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
    private readonly PopupSectionPanel _compactAccountFrame = new();
    private readonly Panel _compactAccountBody = new();
    private readonly PopupButton _compactSupportTrigger = new();
    private readonly PopupSectionPanel _compactSupportFrame = new();
    private readonly Panel _compactSupportBody = new();
    private PopupMultilineInput _compactSupportInput = null!;
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
    private readonly PopupOptionSelect _compactSupportKind = new();
    private readonly PopupOptionSelect _compactSupportCategory = new();
    private readonly Label _compactSupportDescriptionLabel = Tiny("Опишите проблему", 9);
    private readonly Label _compactUploadDurationCaption = Tiny("Длительность песни, сек", 9);
    private readonly Label _compactUploadDurationKnown = Tiny("", 9);
    private readonly Label _compactSupportCategoryLabel = Tiny("Что произошло?", 9);
    private readonly TextBox _compactSupportText = new();
    private readonly PopupButton _compactSupportSubmit = new();
    private readonly Label _compactSupportMessage = new();
    private readonly Label _compactUploadHeading = new();
    private readonly Label _compactUploadNote = new();
    private readonly Label _compactAudioValidation = new();
    private readonly Label _compactSuggestHeading = new();
    private readonly Label _compactSuggestCaption = new();
    private readonly TextBox _compactUploadDuration = new();
    private readonly PopupFilePicker _compactFilePicker = new();
    private readonly Label _compactFileName = new();
    private readonly PopupRightsCheck _compactRights = new();
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
    private AudioPreflight.Result? _compactAudioPreflight;
    private int _compactFilePreflightGeneration;
    private bool _compactFileChecking;
    private string _compactPreflightTrack = "";
    private long _compactPreflightReferenceMs;
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
        child.Size = new Size(Math.Max(1, width), height); // 7px status dot is intentional
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
        _compactScroll.Margin = Padding.Empty;
        _compactScroll.BackColor = Paper;
        // The standard WinForms AutoScroll changes viewport width during layout
        // and caused the owner's double right gutter / unreachable forms.
        // A stable scrollbar owns the vertical viewport explicitly.
        _compactScroll.AutoScroll = false;
        _compactScroll.TabStop = true;
        _compactScroll.Resize += (_, _) => LayoutCompact();
        _compactScroll.MouseWheel += CompactMouseWheel;
        _compactFooter.Dock = DockStyle.Fill;
        _compactFooter.Margin = Padding.Empty;
        _compactFooter.BackColor = Paper;
        _compactFrame.Dock = DockStyle.Fill;
        _compactFrame.Margin = Padding.Empty;
        _compactFrame.Padding = Padding.Empty;
        _compactFrame.RowCount = 2;
        _compactFrame.ColumnCount = 1;
        _compactFrame.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        _compactFrame.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
        _compactFrame.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        _compactFrame.Controls.Add(_compactScroll, 0, 0);
        _compactFrame.Controls.Add(_compactFooter, 0, 1);
        Controls.Add(_compactFrame);
        _compactScrollbar.Dock = DockStyle.Right;
        _compactScrollbar.Width = 5; // dark thumb inside right gutter
        _compactScrollbar.SmallChange = 30;
        _compactScrollbar.Scroll += (_, e) => SetCompactOffset(e.NewValue);
        _compactScroll.Controls.Add(_compactScrollbar);
        _compactScrollbar.BringToFront();

        // Render a true ~7px dot: a text bullet changes its baseline by DPI
        // and appeared oversized, crooked in the owner's Windows screenshot.
        _connectionMark.Text = "";
        _connectionMark.ForeColor = ColorTranslator.FromHtml("#858B8E");
        _connectionMark.Paint += (_, e) =>
        {
            e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            using var brush = new SolidBrush(_connectionMark.ForeColor);
            e.Graphics.FillEllipse(brush, 0, 0, 7, 7);
        };
        Place(_connectionMark, _compactHeader, 2, 15, 7, 7); // align with visible "CELIKOM" glyph, not Label bounding box
        var logo = Tiny("CELIKOM", 11, Ink);
        logo.Font = new Font("Segoe UI", 11F, FontStyle.Bold);
        Place(logo, _compactHeader, 16, 8, 97, 24);
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
        _compactTrack.ForeColor = Ink;
        _compactTrack.Font = new Font("Segoe UI", 9F);
        _compactTrack.BackColor = Paper;
        _compactTrack.AutoEllipsis = false;
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
            if (_compactAccountOpen)
            {
                _ = RefreshCompactBenefitsAsync();
                ScrollCompactTo(_compactAccountFrame);
            }
        });
        SetupMainButton(_compactSupportTrigger, "▸ Связь с поддержкой", (_, _) =>
        {
            _compactSupportOpen = !_compactSupportOpen;
            _compactSupportTrigger.Text = (_compactSupportOpen ? "▾" : "▸") + " Связь с поддержкой";
            LayoutCompact();
            if (_compactSupportOpen) ScrollCompactTo(_compactSupportFrame);
        });
        _compactAccountFrame.BackColor = Paper;
        _compactAccountFrame.OutlineColor = Border;
        _compactAccountTrigger.Borderless = true;
        _compactAccountTrigger.BackColor = Paper;
        _compactAccountTrigger.ForeColor = Ink;
        _compactAccountTrigger.TextAlign = ContentAlignment.MiddleLeft;
        _compactAccountFrame.Controls.Add(_compactAccountTrigger);
        _compactAccountFrame.Controls.Add(_compactAccountBody);
        _compactSupportFrame.BackColor = Paper;
        _compactSupportFrame.OutlineColor = Border;
        _compactSupportTrigger.Borderless = true;
        _compactSupportFrame.Controls.Add(_compactSupportTrigger);
        _compactSupportFrame.Controls.Add(_compactSupportBody);
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
        BuildCompactBenefits();
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
            _compactVersionStatus, _compactAccountFrame, _compactSupportFrame,
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
        _signedInIdentity.ForeColor = Accent;
        SetupMainButton(_compactPromoToggle, "▸ Промокод", (_, _) =>
        {
            _compactPromoOpen = !_compactPromoOpen;
            _compactPromoToggle.Text = (_compactPromoOpen ? "▾" : "▸") + " Промокод";
            _compactPromoMessage.Text = "";
            LayoutCompact();
        });
        _compactPromoToggle.BackColor = Paper;
        _compactPromoToggle.Borderless = true;
        _compactPromoToggle.TextAlign = ContentAlignment.MiddleLeft;
        _compactPromoToggle.ForeColor = Secondary;
        _compactPromoToggle.Font = new Font("Segoe UI", 8.5F);
        _compactPromoCode.PlaceholderText = "";
        _compactPromoInput.Hint = "Промокод"; // standard CELIKOM neutral #AAB8BE, not OS hint color
        _compactPromoCode.MaxLength = 64;
        _compactPromoCode.Font = new Font("Segoe UI", 9F);
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
        label.BackColor = Paper;
        Place(label, _compactSupportBody, 0, 1, 250, 24);
        _compactSupportKind.Items.AddRange(new object[]{
            "Обычное обращение · ответ по почте", "Проблема с текущей песней"
        });
        _compactSupportKind.SelectedIndex = 0;
        _compactSupportKind.SelectedIndexChanged += (_, _) => LayoutCompact();
        _compactSupportKind.BackColor = Surface;
        _compactSupportKind.ForeColor = Ink;
        _compactSupportKind.DropDownWidth = 300;
        _compactSupportBody.Controls.Add(_compactSupportKind);
        _compactSupportCategory.Items.AddRange(new object[] {
            "Не включается версия CELIKOM",
            "Играет неправильная версия",
            "Звук обрывается или рассинхронизируется",
            "Другая проблема"
        });
        _compactSupportCategory.SelectedIndex = 0;
        _compactSupportCategory.BackColor = Surface;
        _compactSupportCategory.ForeColor = Ink;
        _compactSupportCategory.DropDownWidth = 300;
        _compactSupportBody.Controls.Add(_compactSupportCategory);
        _compactSupportBody.Controls.Add(_compactSupportCategoryLabel);
        Place(_compactSupportDescriptionLabel, _compactSupportBody, 0, 79, 250, 24);
        _compactSupportText.Multiline = true;
        _compactSupportText.MaxLength = 2000;
        _compactSupportText.ScrollBars = ScrollBars.Vertical;
        _compactSupportText.BackColor = Surface;
        _compactSupportText.ForeColor = Ink;
        _compactSupportInput = new PopupMultilineInput(_compactSupportText);
        _compactSupportBody.Controls.Add(_compactSupportInput);
        SetupMainButton(_compactSupportSubmit, "Отправить", CompactSendSupportAsync);
        _compactSupportBody.Controls.Add(_compactSupportSubmit);
        _compactSupportMessage.ForeColor = Accent;
        _compactSupportMessage.Font = new Font("Segoe UI", 8F);
        _compactSupportMessage.AutoEllipsis = false;
        _compactSupportBody.Controls.Add(_compactSupportMessage);
    }

    private void BuildCompactContributions()
    {
        _compactUploadHeading.Text = "Загрузить версию";
        _compactUploadHeading.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        _compactUploadHeading.ForeColor = Ink;
        _compactUploadHeading.BackColor = _compactUploadBody.BackColor;
        _compactUploadBody.Controls.Add(_compactUploadHeading);
        _compactUploadTrack.ForeColor = Ink;
        _compactUploadTrack.Font = new Font("Segoe UI", 9F);
        _compactUploadTrack.BackColor = _compactUploadBody.BackColor;
        _compactUploadTrack.Text = "Текущая песня не определена";
        _compactUploadBody.Controls.Add(_compactUploadTrack);
        Place(_compactUploadDurationCaption, _compactUploadBody, 0, 28, 250, 23);
        _compactUploadDurationKnown.ForeColor = Secondary;
        _compactUploadDurationKnown.BackColor = _compactUploadBody.BackColor;
        _compactUploadDurationCaption.BackColor = _compactUploadBody.BackColor;
        _compactUploadBody.Controls.Add(_compactUploadDurationKnown);
        _compactUploadDuration.PlaceholderText = "Например, 180";
        _compactUploadDuration.TextChanged += (_, _) =>
        {
            if (_compactSelectedAudio is not null && _compactUploadView == "form")
                _ = CheckCompactFileAsync(debounceMs: 280);
        };
        _compactUploadBody.Controls.Add(_compactDurationInput);
        _compactFilePicker.Click += CompactChooseAudio;
        _compactUploadBody.Controls.Add(_compactFilePicker);
        _compactFileName.ForeColor = Secondary;
        _compactFileName.BackColor = _compactUploadBody.BackColor;
        _compactUploadBody.Controls.Add(_compactFileName);
        _compactRights.CheckedChanged += (_, _) => RenderCompact();
        _compactUploadBody.Controls.Add(_compactRights);
        SetupMainButton(_compactUploadSubmit, "Отправить на проверку", CompactUploadAsync);
        _compactUploadBody.Controls.Add(_compactUploadSubmit);
        _compactUploadNote.ForeColor = Secondary;
        _compactUploadNote.BackColor = _compactUploadBody.BackColor;
        _compactUploadNote.Font = new Font("Segoe UI", 8.5F);
        _compactUploadNote.Font = new Font("Segoe UI", 8F);
        _compactUploadBody.Controls.Add(_compactUploadNote);
        _compactAudioValidation.Font = new Font("Segoe UI", 8.5F);
        _compactAudioValidation.ForeColor = Secondary;
        _compactAudioValidation.BackColor = ColorTranslator.FromHtml("#152A28");
        _compactAudioValidation.Padding = new Padding(8, 5, 8, 5);
        _compactAudioValidation.BorderStyle = BorderStyle.FixedSingle;
        _compactUploadBody.Controls.Add(_compactAudioValidation);
        _compactUploadProgress.Visible = false;
        _compactUploadProgress.Style = ProgressBarStyle.Continuous;
        _compactUploadBody.Controls.Add(_compactUploadProgress);
        ConfigureCompactResult(_compactUploadResult, _compactUploadResultTitle, _compactUploadResultNote);
        _compactUploadBody.Controls.Add(_compactUploadResult);

        _compactSuggestTrack.ForeColor = Ink;
        _compactSuggestTrack.Font = new Font("Segoe UI", 9F);
        _compactSuggestTrack.BackColor = _compactSuggestBody.BackColor;
        _compactSuggestBody.Controls.Add(_compactSuggestTrack);
        _compactSuggestHeading.Text = "Предложить песню";
        _compactSuggestHeading.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        _compactSuggestHeading.ForeColor = Ink;
        _compactSuggestHeading.BackColor = _compactSuggestBody.BackColor;
        _compactSuggestBody.Controls.Add(_compactSuggestHeading);
        _compactSuggestCaption.Text = "Для этой песни нужна альтернативная версия.";
        _compactSuggestCaption.Font = new Font("Segoe UI", 8.5F);
        _compactSuggestCaption.ForeColor = Secondary;
        _compactSuggestCaption.BackColor = _compactSuggestBody.BackColor;
        _compactSuggestBody.Controls.Add(_compactSuggestCaption);
        SetupMainButton(_compactSuggestSubmit, "Отправить предложение", CompactSuggestAsync);
        _compactSuggestBody.Controls.Add(_compactSuggestSubmit);
        _compactSuggestNote.ForeColor = Secondary;
        _compactSuggestNote.BackColor = _compactSuggestBody.BackColor;
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
        _compactAccountFrame.OutlineColor = !_api.IsLoggedIn ? Danger : Border;
        _compactAccountTrigger.ForeColor = !_api.IsLoggedIn ? Color.White : Ink;
        _compactAccountFrame.Invalidate();
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
                ++_compactFilePreflightGeneration;
                _compactAudioPreflight = null;
                _compactSelectedAudio = null;
                _compactFilePicker.SelectedFile = "";
                _compactFileChecking = false;
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
        _compactUploadSubmit.Enabled = _compactUploadCancellation is not null ||
            (_api.IsLoggedIn && valid && _compactUploadView == "form" &&
             !_compactFileChecking && _compactSelectedAudio is not null &&
             _compactAudioPreflight is { Blocked: false } &&
             _compactPreflightTrack == _bridge.LastSong && _compactRights.Checked);
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
                    CompactUploadFormHeight() : 130, 8, _compactUploadOpen),
                (_compactSuggestButton, 40, 12, true),
                (_compactSuggestBody, _compactSuggestView == "form"
                    ? CompactSuggestFormHeight() : 130, 8, _compactSuggestOpen),
                (_compactAccess, 35, 8, true),
                (_compactTrack, 32, 0, true),
                (_compactTrackArtist, 25, 3, !string.IsNullOrWhiteSpace(_compactTrackArtist.Text)),
                (_compactVersionStatus, 40, 8, hasTrack),
                (_compactAccountFrame, _compactAccountOpen ? 54 + CompactAccountHeight() : 44, 10, true),
                (_compactSupportFrame, _compactSupportOpen ?
                    54 + CompactSupportBodyHeight() : 35, 8, true),
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
            // The thumb lives inside the existing right inset. Content width
            // is exactly the same with or without a vertical scrollbar.
            var width = Math.Max(190, _compactScroll.ClientSize.Width - 36);
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
            // Accordion headings and bodies share one border and parent control.
            Place(_compactAccountTrigger, _compactAccountFrame, 10, 3, width - 20, 40);
            _compactAccountBody.Visible = _compactAccountOpen;
            if (_compactAccountOpen)
                Place(_compactAccountBody, _compactAccountFrame, 12, 44,
                    width - 24, CompactAccountHeight());
            Place(_compactSupportTrigger, _compactSupportFrame, 10, 1, width - 20, 33);
            _compactSupportBody.Visible = _compactSupportOpen;
            if (_compactSupportOpen)
                Place(_compactSupportBody, _compactSupportFrame, 12, 42,
                    width - 24, CompactSupportBodyHeight());
            LayoutCompactAccount(width - 24);
            LayoutCompactSupport(width - 24);
            LayoutCompactContributions(width);
            _compactScrollbar.BringToFront();
        }
        finally { _compactScroll.ResumeLayout(false); _compactLayoutBusy = false; }
    }

    private int CompactAccountHeight() => _api.IsLoggedIn ?
        CompactSignedHeight() :
        _compactAccountMode is "login" or "register" ? 326 :
        _compactAccountMode is "verify" ? 256 :
        _compactAccountMode is "recovery" ? 207 : 308;

    private int CompactSignedHeight()
    {
        int y = 8 + 45; // promo summary + 12px breathing room
        if (_compactPromoOpen)
        {
            y += 52 + 52; // 42px input/button, 10px between them
            if (_compactPromoMessage.Text.Length > 0) y += 44;
        }
        y += 34; // email
        y += CompactBenefitsHeight();
        y += 50; // logout and bottom padding
        return y;
    }

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

        HideCompactBenefits();
        if (signed)
        {
            int y = 8;
            // Exact extension order: summary -> optional promo form -> email
            // -> real benefits -> logout. Everything stays inside one card.
            Place(_compactPromoToggle, _compactAccountBody, 0, y, w, 33);
            y += 45; // 12px between promo summary and form
            if (_compactPromoOpen)
            {
                Place(_compactPromoInput, _compactAccountBody, 0, y, w, 42);
                y += 52; // 10px between input and Activate
                Place(_compactPromoSubmit, _compactAccountBody, 0, y, w, 42);
                y += 52;
                if (_compactPromoMessage.Text.Length > 0)
                {
                    Place(_compactPromoMessage, _compactAccountBody, 0, y, w, 38);
                    y += 44;
                }
            }
            Place(_signedInIdentity, _compactAccountBody, 0, y, w, 30);
            y += 34;
            LayoutCompactBenefits(w, ref y);
            Place(_logout, _compactAccountBody, 0, y, w, 40);
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

    private int CompactSupportBodyHeight()
    {
        var song = _compactSupportKind.SelectedIndex == 1;
        var hasMessage = !string.IsNullOrWhiteSpace(_compactSupportMessage.Text);
        return (song ? 338 : 273) + (hasMessage ? 48 : 0);
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
        Place(_compactSupportInput, _compactSupportBody, 0, song ? 174 : 109, w, 99);
        // 13–14 px between textarea and submit, not a 1px collision.
        Place(_compactSupportSubmit, _compactSupportBody, 0, song ? 286 : 222, w, 40);
        _compactSupportMessage.Visible = false;
        if (!string.IsNullOrWhiteSpace(_compactSupportMessage.Text))
            Place(_compactSupportMessage, _compactSupportBody, 0,
                song ? 339 : 275, w, 42);
    }

    private int UploadBodyInnerWidth() =>
        Math.Max(110, Math.Max(190, _compactScroll.ClientSize.Width - 36) - 26);

    private int UploadTrackHeight()
    {
        var h = TextRenderer.MeasureText(_compactUploadTrack.Text,
            _compactUploadTrack.Font, new Size(UploadBodyInnerWidth(), 140),
            TextFormatFlags.WordBreak | TextFormatFlags.NoPadding).Height;
        return Math.Clamp(h + 4, 24, 56);
    }

    private int UploadNoteHeight()
    {
        if (string.IsNullOrWhiteSpace(_compactUploadNote.Text)) return 0;
        var h = TextRenderer.MeasureText(_compactUploadNote.Text,
            _compactUploadNote.Font, new Size(UploadBodyInnerWidth(), 140),
            TextFormatFlags.WordBreak | TextFormatFlags.NoPadding).Height;
        return Math.Clamp(h + 10, 26, 65);
    }

    private int CompactUploadFormHeight()
    {
        // Must exactly mirror the actual visible controls below. Nothing is
        // reserved for validation, progress or notes until they are shown.
        int y = 14 + 31 + UploadTrackHeight() + 6;
        y += _bridge.LastTrackDurationMs >= 1000 ? 25 : 70;
        y += 79 + 9; // file picker
        if (_compactFileChecking || _compactAudioPreflight is not null)
            y += CompactValidationHeight() + 8;
        y += 48 + 10; // rights declaration
        if (_compactUploadCancellation is not null) y += 15 + 7;
        y += 44 + 6; // submit
        y += UploadNoteHeight();
        return y + 14;
    }

    private int CompactValidationHeight() =>
        _compactFileChecking ? 46 :
        _compactAudioPreflight?.Blocked == true ? 108 : 56;

    private int CompactSuggestFormHeight() =>
        14 + 25 + 37 + 48 + 44 +
        (string.IsNullOrWhiteSpace(_compactSuggestNote.Text) ? 0 : 55) + 16;

    private void LayoutCompactContributions(int w)
    {
        var inner = Math.Max(110, w - 26);
        bool form = _compactUploadView == "form";
        bool result = _compactUploadView == "result";
        foreach (var child in new Control[] {
            _compactUploadHeading, _compactUploadTrack, _compactUploadDurationCaption,
            _compactDurationInput, _compactUploadDurationKnown, _compactFilePicker,
            _compactFileName, _compactRights, _compactUploadSubmit, _compactUploadNote,
            _compactUploadProgress, _compactUploadResult, _compactAudioValidation,
        }) child.Visible = false;

        if (form)
        {
            int y = 14;
            Place(_compactUploadHeading, _compactUploadBody, 13, y, inner, 25);
            y += 31;
            var titleHeight = UploadTrackHeight();
            Place(_compactUploadTrack, _compactUploadBody, 13, y, inner, titleHeight);
            y += titleHeight + 6;
            if (_bridge.LastTrackDurationMs >= 1000)
            {
                Place(_compactUploadDurationKnown, _compactUploadBody, 13, y, inner, 25);
                y += 25;
            }
            else
            {
                Place(_compactUploadDurationCaption, _compactUploadBody, 13, y, inner, 24);
                Place(_compactDurationInput, _compactUploadBody, 13, y + 24, inner, 40);
                y += 70;
            }
            Place(_compactFilePicker, _compactUploadBody, 13, y, inner, 79);
            y += 88;
            if (_compactFileChecking || _compactAudioPreflight is not null)
            {
                var blocked = _compactAudioPreflight?.Blocked == true;
                var label = _compactAudioValidation;
                label.Text = _compactFileChecking ? "Проверяем длительность файла…" :
                    _compactAudioPreflight?.DurationMessage ?? "";
                label.BackColor = blocked ?
                    ColorTranslator.FromHtml("#301C20") : ColorTranslator.FromHtml("#142B22");
                label.ForeColor = blocked ?
                    ColorTranslator.FromHtml("#FFBDB7") : ColorTranslator.FromHtml("#9CEACB");
                if (_compactFileChecking)
                {
                    label.BackColor = ColorTranslator.FromHtml("#152A28");
                    label.ForeColor = Secondary;
                }
                var size = CompactValidationHeight();
                Place(label, _compactUploadBody, 13, y, inner, size);
                y += size + 8;
            }
            Place(_compactRights, _compactUploadBody, 13, y, inner, 48);
            y += 58;
            if (_compactUploadCancellation is not null)
            {
                Place(_compactUploadProgress, _compactUploadBody, 13, y, inner, 15);
                y += 22;
            }
            Place(_compactUploadSubmit, _compactUploadBody, 13, y, inner, 44);
            y += 50;
            if (!string.IsNullOrWhiteSpace(_compactUploadNote.Text))
                Place(_compactUploadNote, _compactUploadBody, 13, y, inner,
                    UploadNoteHeight());
        }
        else if (result)
        {
            Place(_compactUploadResult, _compactUploadBody, 12, 12, inner, 108);
            Place(_compactUploadResultTitle, _compactUploadResult, 12, 11, inner - 24, 27);
            Place(_compactUploadResultNote, _compactUploadResult, 12, 42, inner - 24, 62);
        }
        else
            Place(_compactUploadNote, _compactUploadBody, 13, 13, inner, 102);

        _compactSuggestHeading.Visible = false;
        _compactSuggestCaption.Visible = false;
        _compactSuggestResult.Visible = false;
        _compactSuggestTrack.Visible = false;
        _compactSuggestSubmit.Visible = false;
        _compactSuggestNote.Visible = false;
        if (_compactSuggestView == "result")
        {
            Place(_compactSuggestResult, _compactSuggestBody, 12, 12, inner, 108);
            Place(_compactSuggestResultTitle, _compactSuggestResult, 12, 10, inner - 24, 28);
            Place(_compactSuggestResultNote, _compactSuggestResult, 12, 42, inner - 24, 60);
        }
        else if (_compactSuggestView == "form")
        {
            int y = 14;
            Place(_compactSuggestHeading, _compactSuggestBody, 13, y, inner, 25);
            y += 25;
            Place(_compactSuggestCaption, _compactSuggestBody, 13, y, inner, 37);
            y += 37;
            Place(_compactSuggestTrack, _compactSuggestBody, 13, y, inner, 48);
            y += 48;
            Place(_compactSuggestSubmit, _compactSuggestBody, 13, y, inner, 44);
            y += 44;
            if (!string.IsNullOrWhiteSpace(_compactSuggestNote.Text))
                Place(_compactSuggestNote, _compactSuggestBody, 13, y, inner, 55);
        }
        else Place(_compactSuggestNote, _compactSuggestBody, 13, 13, inner, 104);
    }

}
