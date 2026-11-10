// Independent staging-only visual check. Never load a Yandex account or mutate
// an original application: the CELIKOM form is rendered without Application.Run.
using System.Drawing.Imaging;
using Celikom.Companion;

if (args.Length != 1 || !Path.IsPathFullyQualified(args[0]))
    throw new ArgumentException("W59_ABSOLUTE_OUTPUT_PNG_REQUIRED");
ApplicationConfiguration.Initialize();
using var form = new MainWindow();
form.CreateControl();
form.PerformLayout();
using var image = new Bitmap(form.Width, form.Height);
form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
image.Save(args[0], ImageFormat.Png);
Console.WriteLine("W59_VISUAL_PREVIEW_RENDER_PASS " + image.Width + "x" + image.Height);
