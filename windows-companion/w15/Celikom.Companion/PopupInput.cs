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
    private readonly Label _hint = new();
    private string _hintText = "";
    [System.ComponentModel.DesignerSerializationVisibility(
        System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    public string Hint
    {
        get => _hintText;
        set { _hintText = value ?? ""; _input.PlaceholderText = ""; UpdateHint(); }
    }
    private void UpdateHint()
    {
        _hint.Text = _hintText;
        _hint.Visible = _hintText.Length > 0 && _input.Text.Length == 0 && !_input.Focused;
    }

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
        _input.GotFocus += (_, _) => { UpdateHint(); Invalidate(); };
        _input.LostFocus += (_, _) => { UpdateHint(); Invalidate(); };
        _input.TextChanged += (_, _) => UpdateHint();
        Controls.Add(_input);
        _hint.BackColor = Background;
        _hint.ForeColor = ColorTranslator.FromHtml("#AAB8BE");
        _hint.Font = _input.Font;
        _hint.TextAlign = ContentAlignment.MiddleLeft;
        _hint.Click += (_, _) => _input.Focus();
        Controls.Add(_hint);
        _hint.BringToFront();
        Resize += (_, _) => ArrangeInput();
        ArrangeInput();
    }

    private void ArrangeInput()
    {
        _input.Width = Math.Max(15, ClientSize.Width - 28);
        _input.Location = new Point(14, Math.Max(6, (ClientSize.Height - _input.Height) / 2));
        _hint.SetBounds(_input.Left, _input.Top, _input.Width,
            Math.Max(_input.Height, 20));
        UpdateHint();
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