using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>
/// Chrome popup-inspired 10px-rounded button with legible disabled state.
/// Owner-drawn ONLY for presentation; preserves native WinForms Button events.
/// Palette matches extension/popup/popup.css.
/// </summary>
public sealed class PopupButton : Button
{
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    public bool Borderless { get; set; }
    public PopupButton()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        FlatStyle = FlatStyle.Flat;
        FlatAppearance.BorderSize = 0;
        UseVisualStyleBackColor = false;
        BackColor = ColorTranslator.FromHtml("#141B1F");
        ForeColor = ColorTranslator.FromHtml("#F4F7F8");
        Cursor = Cursors.Hand;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent?.BackColor ?? ColorTranslator.FromHtml("#0B1013"));
        if (Width < 5 || Height < 5) return;
        if (Borderless)
        {
            // Details summary inside the SAME outer bordered card; no nested rectangle.
            var bg = Parent?.BackColor ?? BackColor;
            e.Graphics.Clear(bg);
            var color = Enabled ? ForeColor : ColorTranslator.FromHtml("#778990");
            var align = TextAlign == ContentAlignment.MiddleLeft
                ? TextFormatFlags.Left : TextFormatFlags.HorizontalCenter;
            TextRenderer.DrawText(e.Graphics, Text, Font,
                Rectangle.Inflate(ClientRectangle, -6, 0), color,
                align | TextFormatFlags.VerticalCenter |
                TextFormatFlags.EndEllipsis | TextFormatFlags.SingleLine);
            return;
        }
        using var path = new GraphicsPath();
        var r = 10f;
        var rect = new RectangleF(.8f, .8f, Width - 2f, Height - 2f);
        path.AddArc(rect.Left, rect.Top, r * 2, r * 2, 180, 90);
        path.AddArc(rect.Right - r * 2, rect.Top, r * 2, r * 2, 270, 90);
        path.AddArc(rect.Right - r * 2, rect.Bottom - r * 2, r * 2, r * 2, 0, 90);
        path.AddArc(rect.Left, rect.Bottom - r * 2, r * 2, r * 2, 90, 90);
        path.CloseFigure();
        var background = Enabled ? BackColor : ColorTranslator.FromHtml("#182126");
        var outline = Enabled
            ? BackColor == ColorTranslator.FromHtml("#66E0BF")
                ? ColorTranslator.FromHtml("#66E0BF")
                : ColorTranslator.FromHtml("#2A3439")
            : ColorTranslator.FromHtml("#2A3439");
        using (var fill = new SolidBrush(background)) e.Graphics.FillPath(fill, path);
        using (var pen = new Pen(outline, 1f)) e.Graphics.DrawPath(pen, path);
        var foreground = Enabled ? ForeColor : ColorTranslator.FromHtml("#778990");
        var alignment = TextAlign == ContentAlignment.MiddleLeft ?
            TextFormatFlags.Left : TextFormatFlags.HorizontalCenter;
        TextRenderer.DrawText(e.Graphics, Text, Font,
            Rectangle.Inflate(ClientRectangle, -8, 0), foreground,
            alignment | TextFormatFlags.VerticalCenter |
            TextFormatFlags.EndEllipsis | TextFormatFlags.SingleLine);
    }
}
