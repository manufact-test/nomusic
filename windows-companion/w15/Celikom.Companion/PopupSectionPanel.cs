using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Dark rounded bordered section matching extension .upload-panel.</summary>
public sealed class PopupSectionPanel : Panel
{
    public PopupSectionPanel()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        BackColor = ColorTranslator.FromHtml("#121C20");
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        if (Width < 15 || Height < 15) return;
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        using var pen = new Pen(ColorTranslator.FromHtml("#30474B"), 1f);
        var r = new RectangleF(.8f, .8f, Width - 2f, Height - 2f);
        using var path = new GraphicsPath();
        const float a = 10f;
        path.AddArc(r.Left, r.Top, a * 2, a * 2, 180, 90);
        path.AddArc(r.Right - a * 2, r.Top, a * 2, a * 2, 270, 90);
        path.AddArc(r.Right - a * 2, r.Bottom - a * 2, a * 2, a * 2, 0, 90);
        path.AddArc(r.Left, r.Bottom - a * 2, a * 2, a * 2, 90, 90);
        path.CloseFigure();
        e.Graphics.DrawPath(pen, path);
    }
}