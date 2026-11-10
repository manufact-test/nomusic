// Independent staging-only visual check. Never load a Yandex account or mutate
// an original application: the CELIKOM form is rendered without Application.Run.
using System.Drawing.Imaging;
using Celikom.Companion;

if (args.Length != 1 || !Path.IsPathFullyQualified(args[0]))
    throw new ArgumentException("W59_ABSOLUTE_OUTPUT_PNG_REQUIRED");
ApplicationConfiguration.Initialize();
using var form = new MainWindow();
// DrawToBitmap needs a realized child control tree. No account/Yandex session
// is present on the disposable CI runner; showing the window is safe here.
form.Show();
Application.DoEvents();
form.PerformLayout();
Thread.Sleep(450);
Application.DoEvents();
// W62: the old UI compiled green but accidentally painted Stop OVER Start.
// Validate actual rendered control geometry on the Windows runner.
IEnumerable<Control> Descendants(Control root)
{
    foreach (Control child in root.Controls)
    {
        yield return child;
        foreach (var sub in Descendants(child)) yield return sub;
    }
}
var buttons = Descendants(form).OfType<Button>().ToArray();
var start = buttons.SingleOrDefault(b => b.Text == "Старт");
var stop = buttons.SingleOrDefault(b => b.Text == "Стоп");
if (start is null || stop is null || start.Parent != stop.Parent ||
    start.Bounds.IntersectsWith(stop.Bounds) || !start.Visible || !stop.Visible)
    throw new Exception("W62_START_STOP_OVERLAP_OR_MISSING");
if (form.ClientSize.Width is < 292 or > 320)
    throw new Exception("W62_NOT_EXTENSION_SIZED");
if (!buttons.Any(b => b.Text.Contains("Связь с поддержкой", StringComparison.Ordinal)) ||
    buttons.Any(b => b.Text == "Вернуть оригинал") ||
    !buttons.Any(b => b.Text == "Загрузить версию") ||
    !buttons.Any(b => b.Text == "Предложить песню") ||
    !buttons.Any(b => b.Text.Contains("Аккаунт", StringComparison.Ordinal)))
    throw new Exception("W63_EXTENSION_BUTTONS_MISSING_OR_EXTRA_ORIGINAL");
Console.WriteLine("W62_VISIBLE_START_STOP_AND_EXTENSION_HIERARCHY_PASS");
using var image = new Bitmap(form.Width, form.Height);
form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
image.Save(args[0], ImageFormat.Png);
Console.WriteLine("W59_VISUAL_PREVIEW_RENDER_PASS " + image.Width + "x" + image.Height);

void SaveStage(string name)
{
    form.PerformLayout();
    Application.DoEvents();
    using var bitmap = new Bitmap(form.Width, form.Height);
    form.DrawToBitmap(bitmap, new Rectangle(Point.Empty, form.Size));
    bitmap.Save(name, ImageFormat.Png);
}
object Get(string field)
    => typeof(MainWindow).GetField(field,
        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)?
        .GetValue(form) ?? throw new Exception("W63_STAGE_FIELD_MISSING " + field);
void Set(string field, object value)
    => typeof(MainWindow).GetField(field,
        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)?
        .SetValue(form, value);
void Relayout()
    => typeof(MainWindow).GetMethod("LayoutCompact",
        System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)?
        .Invoke(form, null);
void ScrollStage(Control row)
{
    var positions = (Dictionary<Control, int>)Get("_compactPositions");
    Control owner = row;
    while (!positions.ContainsKey(owner) && owner.Parent is not null)
        owner = owner.Parent;
    if (!positions.TryGetValue(owner, out var y))
        throw new Exception("W65_STAGE_POSITION_MISSING " + row.Name);
    typeof(MainWindow).GetMethod("SetCompactOffset",
        System.Reflection.BindingFlags.Instance |
        System.Reflection.BindingFlags.NonPublic)!.Invoke(form, [Math.Max(0, y - 15)]);
    Application.DoEvents();
}

var prefix = Path.Combine(Path.GetDirectoryName(args[0])!,
    Path.GetFileNameWithoutExtension(args[0]));
// Test real expanded SIGNED-OUT account controls; W62 hid all children forever.
form.ClientSize = new Size(308, 780);
Set("_compactAccountOpen", true);
Relayout();
var account = (Control)Get("_compactAccountBody");
var email = (Control)Get("_compactEmailInput");
var password = (Control)Get("_compactPasswordInput");
var login = (Control)Get("_login");
if (!email.Visible || !password.Visible || !login.Visible ||
    email.Parent != account || password.Parent != account ||
    email.Bounds.IntersectsWith(password.Bounds) ||
    login.Bounds.IntersectsWith(password.Bounds))
    throw new Exception("W63_ACCOUNT_FORM_INVISIBLE_OR_OVERLAPPING");

var accountFrame = (Control)Get("_compactAccountFrame");
var supportFrame = (Control)Get("_compactSupportFrame");
if (!ReferenceEquals(account.Parent, accountFrame) ||
    !ReferenceEquals(((Control)Get("_compactAccountTrigger")).Parent, accountFrame) ||
    !ReferenceEquals(((Control)Get("_compactSupportBody")).Parent, supportFrame) ||
    !ReferenceEquals(((Control)Get("_compactSupportTrigger")).Parent, supportFrame))
    throw new Exception("W65_ACCOUNT_SUPPORT_HAVE_NO_SHARED_BORDER");
if (accountFrame.Width != supportFrame.Width ||
    account.Left < 10 || account.Right > accountFrame.Width - 10)
    throw new Exception("W65_CARD_GUTTER_NOT_BALANCED");
var promo = (PopupButton)Get("_compactPromoToggle");
if (!promo.Borderless || promo.Font.Size > 9F)
    throw new Exception("W65_PROMO_NOT_MATCHING_EXTENSION_TYPOGRAPHY");

ScrollStage(account);
SaveStage(prefix + "-account.png");

// Test support form actually opens and exposes a working Send button.
Set("_compactAccountOpen", false);
Set("_compactSupportOpen", true);
Relayout();
var support = (Control)Get("_compactSupportBody");
var send = (Control)Get("_compactSupportSubmit");
if (!send.Visible || send.Parent != support ||
    send.Bottom > support.ClientSize.Height)
    throw new Exception("W63_SUPPORT_SEND_HIDDEN_OR_CLIPPED");
var supportSelection = (PopupOptionSelect)Get("_compactSupportKind");
var textArea = (Control)Get("_compactSupportInput");
if (!textArea.Visible || !supportSelection.Visible ||
    ((TextBox)Get("_compactSupportText")).BorderStyle != BorderStyle.None ||
    !ReferenceEquals(textArea.Parent, support) ||
    !ReferenceEquals(supportSelection.Parent, support))
    throw new Exception("W65_SUPPORT_STILL_USES_WHITE_NATIVE_BORDER");
ScrollStage(support);
SaveStage(prefix + "-support.png");

// Approved/pending status must replace the upload form, not duplicate it.
Set("_compactSupportOpen", false);
Set("_compactUploadOpen", true);
Set("_compactUploadView", "result");
((Label)Get("_compactUploadResultTitle")).Text = "Версия уже доступна";
((Label)Get("_compactUploadResultNote")).Text =
    "Для этой песни уже есть одобренная версия CELIKOM. Повторная отправка не требуется.";
Relayout();
var result = (Control)Get("_compactUploadResult");
var uploadSubmit = (Control)Get("_compactUploadSubmit");
if (!result.Visible || uploadSubmit.Visible)
    throw new Exception("W63_APPROVED_UPLOAD_DID_NOT_HIDE_FORM");
ScrollStage((Control)Get("_compactUploadBody"));
SaveStage(prefix + "-approved.png");

// The normal upload path must visibly contain the file chooser, rights
// declaration and a usable submit button; no hidden/overlapping controls.
Set("_compactUploadView", "form");
Relayout();
var picker = (Control)Get("_compactFilePicker");
var rights = (Control)Get("_compactRights");
var submitUpload = (Control)Get("_compactUploadSubmit");
var uploadPanel = (Control)Get("_compactUploadBody");
if (!picker.Visible || !rights.Visible || !submitUpload.Visible ||
    picker.Bounds.IntersectsWith(rights.Bounds) ||
    submitUpload.Bottom > uploadPanel.ClientSize.Height)
    throw new Exception("W63_UPLOAD_FORM_INVISIBLE_OR_CLIPPED");
ScrollStage(uploadPanel);
SaveStage(prefix + "-upload.png");

// Ensure the user can reach Send via scroll even when the window is narrow.
Set("_compactUploadOpen", false);
Set("_compactSupportOpen", true);
((PopupOptionSelect)Get("_compactSupportKind")).SelectedIndex = 1;
Relayout();
var category = (Control)Get("_compactSupportCategory");
var desc = (Control)Get("_compactSupportInput");
if (!category.Visible || !send.Visible ||
    category.Bounds.IntersectsWith(desc.Bounds) ||
    send.Bottom > support.ClientSize.Height)
    throw new Exception("W63_SONG_SUPPORT_FORM_NOT_USABLE");
ScrollStage(support);
SaveStage(prefix + "-song-support.png");
Console.WriteLine("W63_EXPANDED_ACCOUNT_SUPPORT_AND_GREEN_DUPLICATE_CARD_PASS");

// W64: fixed footer and stable width must survive any expansion.
// Visual checks use the actual WinForms viewport and exercise the same
// explicit scrollbar used by mouse wheel, not AutoScroll which was broken.
form.ClientSize = new Size(308, 450);
Set("_compactSupportOpen", false);
Set("_compactUploadOpen", false);
Set("_compactSuggestOpen", false);
Set("_compactAccountOpen", false);
Relayout();
var baselineWidth = ((Control)Get("_compactUploadButton")).Width;
var footer = (Control)Get("_compactFooter");
var footerLabel = (Control)Get("_compactVersion");
var root = (TableLayoutPanel)Get("_compactFrame");
var dot = (Control)Get("_connectionMark");
if (!ReferenceEquals(footerLabel.Parent, footer) ||
    !ReferenceEquals(footer.Parent, root) ||
    !footer.Visible || !footerLabel.Visible ||
    footerLabel.Bounds.Bottom > footer.ClientSize.Height ||
    footer.Bottom != form.ClientSize.Height ||
    dot.Width > 8 || dot.Height > 8 || dot.Text.Length != 0)
    throw new Exception("W64_VERSION_FOOTER_NOT_ANCHORED_OR_INDICATOR_NOT_CENTERED");

Set("_compactSupportOpen", true);
Set("_compactAccountOpen", true);
Set("_compactUploadOpen", true);
Set("_compactUploadView", "form");
Relayout();
var scrollbar = (PopupThinScroll)Get("_compactScrollbar");
if (!scrollbar.Visible ||
    ((Control)Get("_compactUploadButton")).Width != baselineWidth ||
    footer.Bottom != form.ClientSize.Height ||
    scrollbar.Width > 6 ||
    scrollbar.Left - ((Control)Get("_compactUploadButton")).Right < 14)
    throw new Exception("W65_SCROLLBAR_TOUCHES_CARD_OR_CHANGED_GUTTER");
var layoutTop = ((Control)Get("_compactHeader")).Top;
var offsetSetter = typeof(MainWindow).GetMethod("SetCompactOffset",
    System.Reflection.BindingFlags.Instance |
    System.Reflection.BindingFlags.NonPublic)!;
offsetSetter.Invoke(form, [300]);
if (((Control)Get("_compactHeader")).Top >= layoutTop ||
    scrollbar.Value <= 0 || footer.Bottom != form.ClientSize.Height)
    throw new Exception("W64_SCROLL_NOT_WORKING");
SaveStage(prefix + "-scrolled.png");
// Wheel events must move the same scrollbar; the user should never be trapped.
var beforeWheel = scrollbar.Value;
typeof(MainWindow).GetMethod("CompactMouseWheel",
    System.Reflection.BindingFlags.Instance |
    System.Reflection.BindingFlags.NonPublic)!.Invoke(form,
    [(Control)Get("_compactScroll"),
      new MouseEventArgs(MouseButtons.None, 0, 5, 5, -120)]);
if (scrollbar.Value <= beforeWheel || footer.Bottom != form.ClientSize.Height)
    throw new Exception("W64_MOUSE_WHEEL_NOT_SCROLLING_OR_FOOTER_MOVED");
SaveStage(prefix + "-wheel.png");

Set("_compactAccountOpen", false);
Set("_compactSupportOpen", false);
Set("_compactUploadOpen", true);
Set("_compactUploadView", "form");
Set("_compactSelectedAudio", "bad_audio.mp3");
Set("_compactAudioPreflight", new AudioPreflight.Result(
    152000, true, "Оригинал: 3:43 · файл: 2:32. Допуск подмены — 1,5 с."));
offsetSetter.Invoke(form, [0]);
Relayout();
var durationWarning = (Label)Get("_compactAudioValidation");
if (!durationWarning.Visible || durationWarning.ForeColor.R < 200 ||
    ((Button)Get("_compactUploadSubmit")).Enabled)
    throw new Exception("W64_INVALID_AUDIO_NOT_RED_OR_UPLOAD_NOT_BLOCKED");
SaveStage(prefix + "-invalid-audio.png");
// The owner explicitly removed the guessed filename warning, including
// internal preflight fields. Verify no accidentally hidden counterpart exists.
if (typeof(AudioPreflight).GetMethod("FilenameSuspicious") is not null ||
    typeof(AudioPreflight.Result).GetProperty("NameSuspicious") is not null ||
    typeof(MainWindow).GetField("_compactFilenameWarning",
        System.Reflection.BindingFlags.Instance |
        System.Reflection.BindingFlags.NonPublic) is not null)
    throw new Exception("W65_FILENAME_HEURISTIC_MUST_NOT_EXIST");
var promoButton = (PopupButton)Get("_compactPromoToggle");
var benefitsButton = (PopupButton)Get("_compactBenefitsToggle");
if (!promoButton.Borderless || !benefitsButton.Borderless ||
    promoButton.Font.Size > 9 || benefitsButton.Font.Size > 9 ||
    !ReferenceEquals(benefitsButton.Parent, account))
    throw new Exception("W65_ACCOUNT_INNER_DETAILS_ARE_NOT_EXT_STYLE");
Console.WriteLine("W65_NO_FILENAME_CHECK_AND_REAL_BENEFITS_CONTROLS_PASS");

Console.WriteLine("W65_BORDERED_ACCORDIONS_DARK_SUPPORT_NO_FILENAME_CHECK_SCROLL_GUTTERS_PASS");
Console.WriteLine("W64_SCROLLED_PANEL_EQUAL_GUTTERS_FIXED_FOOTER_RED_AUDIO_PRECHECK_PASS");


