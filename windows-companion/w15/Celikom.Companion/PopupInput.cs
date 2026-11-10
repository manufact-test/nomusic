using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Rounded extension-style text field; no default WinForms inset border.</summary>
public sealed class PopupInput : UserControl
{
    private static readonly Color Background = ColorTranslator.FromHtml("#141B1F");
    private static readonly Color Outline = ColorTranslator.FromHtml("#2A3439");
    private static readonly Color FocusOutline = ColorTranslator.FromHtml("#66E0BF");
    private readonly TextBox _input;

    public PopupInput(TextBox input)
    {
        _input = input;
        DoubleBuffered = true;
        BackColor = ColorTranslator.FromHtml("#0B1013");
        ForeColor = ColorTranslator.FromHtml("#F4F7F8");
        TabStop = false;
        _input.BorderStyle = BorderStyle.None;
        _input.BackColor = Background;
        _input.ForeColor = ForeColor;
        _input.Font = new Font("Segoe UI", 9F);
        _input.GotFocus += (_, _) => Invalidate();
        _input.LostFocus += (_, _) => Invalidate();
        Controls.Add(_input);
        Resize += (_, _) => ArrangeInput();
        ArrangeInput();
    }

    private void ArrangeInput()
    {
        _input.Width = Math.Max(15, ClientSize.Width - 28);
        _input.Location = new Point(14, Math.Max(6, (ClientSize.Height - _input.Height) / 2));
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        if (Width <= 8 || Height <= 8) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var r = 10f;
        var rect = new RectangleF(.8f, .8f, Width - 2f, Height - 2f);
        using var path = new GraphicsPath();
        path.AddArc(rect.Left, rect.Top, r * 2, r * 2, 180, 90);
        path.AddArc(rect.Right - r * 2, rect.Top, r * 2, r * 2, 270, 90);
        path.AddArc(rect.Right - r * 2, rect.Bottom - r * 2, r * 2, r * 2, 0, 90);
        path.AddArc(rect.Left, rect.Bottom - r * 2, r * 2, r * 2, 90, 90);
        path.CloseFigure();
        using var fill = new SolidBrush(Background);
        using var pen = new Pen(_input.Focused ? FocusOutline : Outline, 1.2F);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(pen, path);
    }
}