using System.ComponentModel;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Dark fully-owner-drawn select, unlike native ComboBox white nonclient chrome.</summary>
public sealed class PopupOptionSelect : Control
{
    public sealed class ItemList : List<string>
    {
        public void AddRange(object[] values)
        {
            base.AddRange(values.Select(item => Convert.ToString(item) ?? ""));
        }
    }

    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    [Browsable(false)]
    public ItemList Items { get; } = new();
    private int _selectedIndex = -1;
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    [Browsable(false)]
    public int SelectedIndex
    {
        get => _selectedIndex;
        set
        {
            if (value < -1 || value >= Items.Count) return;
            if (_selectedIndex == value) return;
            _selectedIndex = value;
            Invalidate();
            SelectedIndexChanged?.Invoke(this, EventArgs.Empty);
        }
    }
    public event EventHandler? SelectedIndexChanged;
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int DropDownWidth { get; set; } = 0;

    public PopupOptionSelect()
    {
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw |
            ControlStyles.Selectable, true);
        TabStop = true;
        Cursor = Cursors.Hand;
        BackColor = ColorTranslator.FromHtml("#141B1F");
        ForeColor = ColorTranslator.FromHtml("#F4F7F8");
        Font = new Font("Segoe UI", 9F);
        Height = 39;
        KeyDown += (_, e) =>
        {
            if (e.KeyCode is Keys.Down or Keys.Up)
            {
                if (Items.Count > 0)
                    SelectedIndex = Math.Clamp(SelectedIndex +
                        (e.KeyCode == Keys.Down ? 1 : -1), 0, Items.Count - 1);
                e.Handled = true;
            }
            else if (e.KeyCode is Keys.Enter or Keys.Space)
            {
                ShowOptions();
                e.Handled = true;
            }
        };
    }

    protected override void OnClick(EventArgs e)
    {
        base.OnClick(e);
        Focus();
        ShowOptions();
    }

    private void ShowOptions()
    {
        if (Items.Count == 0) return;
        var menu = new ContextMenuStrip
        {
            AutoSize = false,
            Width = Math.Max(Width, DropDownWidth),
            BackColor = ColorTranslator.FromHtml("#141B1F"),
            ForeColor = ForeColor,
            Font = Font,
            ShowImageMargin = false,
            Padding = new Padding(0, 4, 0, 4),
            Renderer = new ToolStripProfessionalRenderer(new DarkPalette())
        };
        for (int i = 0; i < Items.Count; i++)
        {
            int index = i;
            var item = new ToolStripMenuItem(Items[i])
            {
                AutoSize = false,
                Width = menu.Width - 4,
                Height = 31,
                BackColor = menu.BackColor,
                ForeColor = ForeColor,
                Checked = index == SelectedIndex
            };
            item.Click += (_, _) => { SelectedIndex = index; menu.Close(); };
            menu.Items.Add(item);
        }
        menu.Height = menu.Items.Count * 31 + 8;
        menu.Closed += (_, _) => menu.Dispose();
        menu.Show(this, new Point(0, Height - 1));
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent?.BackColor ?? BackColor);
        if (Width < 20 || Height < 15) return;
        var rect = new RectangleF(.8f, .8f, Width - 2f, Height - 2f);
        using var path = new GraphicsPath();
        const float corner = 8f;
        path.AddArc(rect.Left, rect.Top, corner * 2, corner * 2, 180, 90);
        path.AddArc(rect.Right - corner * 2, rect.Top, corner * 2, corner * 2, 270, 90);
        path.AddArc(rect.Right - corner * 2, rect.Bottom - corner * 2, corner * 2, 0, 90);
        path.AddArc(rect.Left, rect.Bottom - corner * 2, corner * 2, corner * 2, 90, 90);
        path.CloseFigure();
        using var fill = new SolidBrush(BackColor);
        using var pen = new Pen(Focused ? ColorTranslator.FromHtml("#66E0BF") :
            ColorTranslator.FromHtml("#55666D"), 1f);
        e.Graphics.FillPath(fill, path);
        e.Graphics.DrawPath(pen, path);
        var value = SelectedIndex >= 0 && SelectedIndex < Items.Count
            ? Items[SelectedIndex] : "Выбрать";
        TextRenderer.DrawText(e.Graphics, value, Font,
            new Rectangle(12, 0, Math.Max(10, Width - 40), Height), ForeColor,
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter |
            TextFormatFlags.SingleLine | TextFormatFlags.EndEllipsis);
        var mid = Width - 16;
        using var arrow = new Pen(ColorTranslator.FromHtml("#AAB8BE"), 1.6f);
        e.Graphics.DrawLines(arrow,
            [new Point(mid - 4, Height / 2 - 2), new Point(mid, Height / 2 + 2),
             new Point(mid + 4, Height / 2 - 2)]);
    }

    private sealed class DarkPalette : ProfessionalColorTable
    {
        public override Color MenuBorder => ColorTranslator.FromHtml("#45565F");
        public override Color MenuItemBorder => ColorTranslator.FromHtml("#66E0BF");
        public override Color MenuItemSelected => ColorTranslator.FromHtml("#19302D");
        public override Color MenuItemSelectedGradientBegin => MenuItemSelected;
        public override Color MenuItemSelectedGradientEnd => MenuItemSelected;
        public override Color ToolStripDropDownBackground => ColorTranslator.FromHtml("#141B1F");
        public override Color ImageMarginGradientBegin => ToolStripDropDownBackground;
        public override Color ImageMarginGradientMiddle => ToolStripDropDownBackground;
        public override Color ImageMarginGradientEnd => ToolStripDropDownBackground;
    }
}
