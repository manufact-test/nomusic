using System.ComponentModel;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>
/// Thin, dark, draggable scroll thumb inside the RIGHT GUTTER, unlike the
/// native VScrollBar which consumes 17px and touches the account card.
/// </summary>
public sealed class PopupThinScroll : Control
{
    private int _minimum, _maximum, _largeChange = 1, _smallChange = 30, _value;
    private bool _dragging;
    private int _dragAnchorY, _dragAnchorValue;
    private static readonly Color Track = ColorTranslator.FromHtml("#0B1013");
    private static readonly Color Thumb = ColorTranslator.FromHtml("#4B6267");

    public PopupThinScroll()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        Width = 5;
        Cursor = Cursors.Hand;
    }

    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int Minimum { get => _minimum; set { _minimum = Math.Max(0, value); Clamp(); } }
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int Maximum { get => _maximum; set { _maximum = Math.Max(0, value); Clamp(); } }
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int LargeChange { get => _largeChange; set { _largeChange = Math.Max(1, value); Clamp(); } }
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int SmallChange { get => _smallChange; set => _smallChange = Math.Max(1, value); }
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int Value
    {
        get => _value;
        set { _value = Math.Clamp(value, _minimum, TopValue); Invalidate(); }
    }
    private int TopValue => Math.Max(_minimum, _maximum - _largeChange + 1);
    private void Clamp() { _value = Math.Clamp(_value, _minimum, TopValue); Invalidate(); }
    public event ScrollEventHandler? Scroll;

    private (float top, float thumb) ThumbBounds()
    {
        var range = Math.Max(1, _maximum - _minimum + 1);
        var height = Math.Max(1, Height - 8);
        var thumb = Math.Min(height, Math.Max(24f, height * (_largeChange / (float)range)));
        var space = Math.Max(0, height - thumb);
        var fraction = TopValue == _minimum ? 0f :
            (_value - _minimum) / (float)(TopValue - _minimum);
        return (4 + fraction * space, thumb);
    }

    private void MoveFromPointer(int y, bool relative)
    {
        var (top, thumb) = ThumbBounds();
        var travel = Math.Max(1f, Height - 8 - thumb);
        var source = relative ? (_dragAnchorValue - _minimum) *
            travel / Math.Max(1, TopValue - _minimum) + y - _dragAnchorY :
            y - 4 - thumb / 2;
        var newValue = _minimum + (int)Math.Round(Math.Clamp(source / travel, 0f, 1f) *
            Math.Max(0, TopValue - _minimum));
        if (newValue == _value) return;
        Value = newValue;
        Scroll?.Invoke(this, new ScrollEventArgs(ScrollEventType.ThumbTrack, _value));
    }

    protected override void OnMouseDown(MouseEventArgs e)
    {
        base.OnMouseDown(e);
        if (e.Button != MouseButtons.Left) return;
        var (top, height) = ThumbBounds();
        _dragAnchorY = e.Y;
        _dragAnchorValue = _value;
        _dragging = true;
        Capture = true;
        if (e.Y < top || e.Y > top + height) MoveFromPointer(e.Y, false);
    }

    protected override void OnMouseMove(MouseEventArgs e)
    {
        base.OnMouseMove(e);
        if (_dragging) MoveFromPointer(e.Y, true);
    }

    protected override void OnMouseUp(MouseEventArgs e)
    {
        _dragging = false;
        Capture = false;
        base.OnMouseUp(e);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.Clear(Parent?.BackColor ?? Track);
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var (top, height) = ThumbBounds();
        var width = Math.Max(2, Width - 2);
        using var brush = new SolidBrush(Thumb);
        // Avoid WinForms/OS themed scrollbar chrome entirely.
        e.Graphics.FillRectangle(brush, new RectangleF(1, top, width, height));
    }
}
