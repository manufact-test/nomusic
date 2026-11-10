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
((ScrollableControl)Get("_compactScroll")).ScrollControlIntoView(account);
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
((ScrollableControl)Get("_compactScroll")).ScrollControlIntoView(support);
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
((ScrollableControl)Get("_compactScroll")).ScrollControlIntoView(result);
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
((ScrollableControl)Get("_compactScroll")).ScrollControlIntoView(uploadPanel);
SaveStage(prefix + "-upload.png");

// Ensure the user can reach Send via scroll even when the window is narrow.
Set("_compactUploadOpen", false);
Set("_compactSupportOpen", true);
((ComboBox)Get("_compactSupportKind")).SelectedIndex = 1;
Relayout();
var category = (Control)Get("_compactSupportCategory");
var desc = (Control)Get("_compactSupportText");
if (!category.Visible || !send.Visible ||
    category.Bounds.IntersectsWith(desc.Bounds) ||
    send.Bottom > support.ClientSize.Height)
    throw new Exception("W63_SONG_SUPPORT_FORM_NOT_USABLE");
((ScrollableControl)Get("_compactScroll")).ScrollControlIntoView(support);
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
var dot = (Control)Get("_connectionMark");
if (!ReferenceEquals(footerLabel.Parent, footer) ||
    footer.Bottom != form.ClientSize.Height ||
    dot.Width > 12 || dot.TextAlign != ContentAlignment.MiddleCenter)
    throw new Exception("W64_VERSION_FOOTER_NOT_ANCHORED_OR_INDICATOR_NOT_CENTERED");

Set("_compactSupportOpen", true);
Set("_compactAccountOpen", true);
Set("_compactUploadOpen", true);
Set("_compactUploadView", "form");
Relayout();
var scrollbar = (VScrollBar)Get("_compactScrollbar");
if (!scrollbar.Visible ||
    ((Control)Get("_compactUploadButton")).Width != baselineWidth ||
    footer.Bottom != form.ClientSize.Height)
    throw new Exception("W64_SCROLLBAR_CHANGED_GUTTER_OR_MOVED_FOOTER");
var layoutTop = ((Control)Get("_compactHeader")).Top;
var offsetSetter = typeof(MainWindow).GetMethod("SetCompactOffset",
    System.Reflection.BindingFlags.Instance |
    System.Reflection.BindingFlags.NonPublic)!;
offsetSetter.Invoke(form, [300]);
if (((Control)Get("_compactHeader")).Top >= layoutTop ||
    scrollbar.Value <= 0 || footer.Bottom != form.ClientSize.Height)
    throw new Exception("W64_SCROLL_NOT_WORKING");
SaveStage(prefix + "-scrolled.png");

Set("_compactAccountOpen", false);
Set("_compactSupportOpen", false);
Set("_compactUploadOpen", true);
Set("_compactUploadView", "form");
Set("_compactSelectedAudio", "bad_audio.mp3");
Set("_compactAudioPreflight", new AudioPreflight.Result(
    152000, true, true, "Оригинал: 3:43 · файл: 2:32. Допуск подмены — 1,5 с.",
    "Название файла не похоже на текущую песню."));
offsetSetter.Invoke(form, [0]);
Relayout();
var durationWarning = (Label)Get("_compactAudioValidation");
if (!durationWarning.Visible || durationWarning.ForeColor.R < 200 ||
    ((Button)Get("_compactUploadSubmit")).Enabled)
    throw new Exception("W64_INVALID_AUDIO_NOT_RED_OR_UPLOAD_NOT_BLOCKED");
SaveStage(prefix + "-invalid-audio.png");
Console.WriteLine("W64_SCROLLED_PANEL_EQUAL_GUTTERS_FIXED_FOOTER_RED_AUDIO_PRECHECK_PASS");


