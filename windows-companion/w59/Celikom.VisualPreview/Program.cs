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
    !buttons.Any(b => b.Text == "Вернуть оригинал") ||
    !buttons.Any(b => b.Text == "Загрузить версию") ||
    !buttons.Any(b => b.Text == "Предложить песню") ||
    !buttons.Any(b => b.Text.Contains("Аккаунт", StringComparison.Ordinal)))
    throw new Exception("W62_EXTENSION_BUTTONS_MISSING");
Console.WriteLine("W62_VISIBLE_START_STOP_AND_EXTENSION_HIERARCHY_PASS");
using var image = new Bitmap(form.Width, form.Height);
form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
image.Save(args[0], ImageFormat.Png);
Console.WriteLine("W59_VISUAL_PREVIEW_RENDER_PASS " + image.Width + "x" + image.Height);
