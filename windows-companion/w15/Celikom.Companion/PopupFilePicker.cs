using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Compact extension-like audio chooser (actual native file dialog).</summary>
public sealed class PopupFilePicker : Button
{
    private static readonly Color Base = ColorTranslator.FromHtml("#101F21");
    private static readonly Color Outline = ColorTranslator.FromHtml("#52756E");
    private static readonly Color Hover = ColorTranslator.FromHtml("#66E0BF");
    private static readonly Color Ink = ColorTranslator.FromHtml("#F4F7F8");
    private static readonly Color Muted = ColorTranslator.FromHtml("#AAB8BE");
    private bool _hovered;
    private string _selectedFile = "";
    [System.ComponentModel.DesignerSerializationVisibility(
        System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    [System.ComponentModel.Browsable(false)]
    public string SelectedFile
    {
        get => _selectedFile;
        set { _selectedFile = (value ?? "").Trim(); Invalidate(); }
    }

    public PopupFilePicker()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        FlatStyle = FlatStyle.Flat;
        FlatAppearance.BorderSize = 0;
        UseVisualStyleBackColor = false;
        BackColor = Base;
        ForeColor = Ink;
        Cursor = Cursors.Hand;
        TabStop = true;
        Text = "Выбрать MP3 или M4A";
    }

    protected override void OnMouseEnter(EventArgs e)
    {
        _hovered = true;
        Invalidate();
        base.OnMouseEnter(e);
    }
    protected override void OnMouseLeave(EventArgs e)
    {
        _hovered = false;
        Invalidate();
        base.OnMouseLeave(e);
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent?.BackColor ?? Base);
        if (Width < 30 || Height < 30) return;
        var rect = new RectangleF(1, 1, Width - 2, Height - 2);
        using var outline = new GraphicsPath();
        const float corner = 11f;
        outline.AddArc(rect.Left, rect.Top, corner * 2, corner * 2, 180, 90);
        outline.AddArc(rect.Right - corner * 2, rect.Top, corner * 2, corner * 2, 270, 90);
        outline.AddArc(rect.Right - corner * 2, rect.Bottom - corner * 2,
            corner * 2, corner * 2, 0, 90);
        outline.AddArc(rect.Left, rect.Bottom - corner * 2, corner * 2, corner * 2, 90, 90);
        outline.CloseFigure();
        using var fill = new SolidBrush(Base);
        using var pen = new Pen(_hovered ? Hover : Outline, 1.4f)
            { DashStyle = _selectedFile.Length > 0 ? DashStyle.Solid : DashStyle.Dash };
        e.Graphics.FillPath(fill, outline);
        e.Graphics.DrawPath(pen, outline);
        using var iconPen = new Pen(_hovered ? Hover : Muted, 2);
        var x = 31f; var y = Height / 2f;
        e.Graphics.DrawLine(iconPen, x, y + 4, x, y - 9);
        e.Graphics.DrawLine(iconPen, x, y - 9, x - 5, y - 3);
        e.Graphics.DrawLine(iconPen, x, y - 9, x + 5, y - 3);
        e.Graphics.DrawLine(iconPen, x - 8, y + 2, x - 8, y + 9);
        e.Graphics.DrawLine(iconPen, x + 8, y + 2, x + 8, y + 9);
        e.Graphics.DrawLine(iconPen, x - 8, y + 9, x + 8, y + 9);
        var box = new Rectangle(55, 8, Math.Max(20, Width - 65), Height - 16);
        using var titleFont = new Font(Font.FontFamily, 9F, FontStyle.Bold);
        var visible = _selectedFile.Length > 0 ? _selectedFile : Text;
        TextRenderer.DrawText(e.Graphics, visible, titleFont,
            box, Enabled ? Ink : Muted, TextFormatFlags.Left | TextFormatFlags.VerticalCenter |
            TextFormatFlags.SingleLine | TextFormatFlags.EndEllipsis);
        if (Focused && ShowFocusCues)
            ControlPaint.DrawFocusRectangle(e.Graphics,
                Rectangle.Inflate(ClientRectangle, -5, -5), Hover, Base);
    }
}
