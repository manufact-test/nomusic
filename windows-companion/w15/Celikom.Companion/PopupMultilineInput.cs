using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Extension-styled rounded textarea while preserving real TextBox editing.</summary>
public sealed class PopupMultilineInput : UserControl
{
    private readonly TextBox _input;
    public PopupMultilineInput(TextBox input)
    {
        _input = input;
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        BackColor = ColorTranslator.FromHtml("#0B1013");
        _input.Multiline = true;
        _input.BorderStyle = BorderStyle.None;
        _input.BackColor = ColorTranslator.FromHtml("#141B1F");
        _input.ForeColor = ColorTranslator.FromHtml("#F4F7F8");
        _input.Font = new Font("Segoe UI", 9F);
        _input.ScrollBars = ScrollBars.Vertical;
        Controls.Add(_input);
        _input.GotFocus += (_, _) => Invalidate();
        _input.LostFocus += (_, _) => Invalidate();
        Resize += (_, _) => LayoutText();
        LayoutText();
    }
    private void LayoutText()
    {
        _input.SetBounds(12, 11, Math.Max(15, Width - 24), Math.Max(15, Height - 22));
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent?.BackColor ?? BackColor);
        if (Width <= 10 || Height <= 10) return;
        var rect = new RectangleF(.8f, .8f, Width - 2f, Height - 2f);
        using var path = new GraphicsPath();
        const float corner = 10f;
        path.AddArc(rect.Left, rect.Top, 2*corner, 2*corner, 180, 90);
        path.AddArc(rect.Right-2*corner, rect.Top, 2*corner, 2*corner, 270, 90);
        path.AddArc(rect.Right-2*corner, rect.Bottom-2*corner, 2*corner, 2*corner, 0, 90);
        path.AddArc(rect.Left, rect.Bottom-2*corner, 2*corner, 2*corner, 90, 90);
        path.CloseFigure();
        using var fill = new SolidBrush(_input.BackColor);
        using var pen = new Pen(_input.Focused ?
            ColorTranslator.FromHtml("#66E0BF") :
            ColorTranslator.FromHtml("#2A3439"), 1.2f);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(pen, path);
    }
}
