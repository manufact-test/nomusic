using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Owner-drawn extension-style rights confirmation, no native white square.</summary>
public sealed class PopupRightsCheck : CheckBox
{
    private static readonly Color AccentColor = ColorTranslator.FromHtml("#66E0BF");
    private static readonly Color Muted = ColorTranslator.FromHtml("#AAB8BE");
    private static readonly Color Outline = ColorTranslator.FromHtml("#58706C");
    private static readonly Color Surface = ColorTranslator.FromHtml("#141B1F");
    public PopupRightsCheck()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        AutoSize = false;
        BackColor = ColorTranslator.FromHtml("#121C20");
        ForeColor = Muted;
        Cursor = Cursors.Hand;
        Font = new Font("Segoe UI", 8.5F);
        Text = "Подтверждаю, что имею необходимые права на этот аудиофайл.";
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent?.BackColor ?? BackColor);
        var box = new Rectangle(1, 5, 17, 17);
        using var fill = new SolidBrush(Checked ? AccentColor : Surface);
        using var pen = new Pen(Checked ? AccentColor : Outline, 1.2f);
        e.Graphics.FillRectangle(fill, box);
        e.Graphics.DrawRectangle(pen, box);
        if (Checked)
        {
            using var checkPen = new Pen(ColorTranslator.FromHtml("#07110E"), 2f)
                { StartCap = LineCap.Round, EndCap = LineCap.Round };
            e.Graphics.DrawLines(checkPen,
                [new Point(5, 13), new Point(9, 17), new Point(15, 9)]);
        }
        var textBox = new Rectangle(28, 0, Math.Max(1, Width - 30), Height);
        TextRenderer.DrawText(e.Graphics, Text, Font, textBox, ForeColor,
            TextFormatFlags.Left | TextFormatFlags.Top | TextFormatFlags.WordBreak);
    }
}