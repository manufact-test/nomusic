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

    // Kept to preserve the pre-existing property contract. A dropdown must
    // never grow wider than its visible compact owner just to satisfy this hint.
    private ContextMenuStrip? _activeMenu;

    private void ShowOptions()
    {
        if (IsDisposed || Disposing || !IsHandleCreated || Items.Count == 0) return;
        if (_activeMenu is { IsDisposed: false, Visible: true } open)
        {
            open.Close();
            return;
        }

        var owner = FindForm();
        var ownerRight = owner is null ? PointToScreen(Point.Empty).X + Width :
            owner.RectangleToScreen(owner.ClientRectangle).Right;
        var remaining = Math.Max(1, ownerRight - PointToScreen(Point.Empty).X - 4);
        // The old hardcoded DropDownWidth=300 pushed the 232px selector outside
        // the real 308px window. All row text wraps inside this exact bound.
        var menuWidth = Math.Max(1, Math.Min(Width, remaining));
        var menu = new ContextMenuStrip
        {
            AutoClose = true,
            AutoSize = false,
            Width = menuWidth,
            BackColor = ColorTranslator.FromHtml("#141B1F"),
            ForeColor = ForeColor,
            Font = Font,
            ShowImageMargin = false,
            ShowCheckMargin = false,
            Padding = new Padding(1, 3, 1, 3),
            Renderer = new ToolStripProfessionalRenderer(new DarkPalette())
        };
        var totalHeight = menu.Padding.Vertical;
        for (int i = 0; i < Items.Count; i++)
        {
            int index = i;
            var textAreaWidth = Math.Max(32, menuWidth - 30);
            var textHeight = TextRenderer.MeasureText(Items[i], Font,
                new Size(textAreaWidth, 120),
                TextFormatFlags.WordBreak | TextFormatFlags.NoPadding |
                TextFormatFlags.NoPrefix).Height;
            var item = new DarkOptionItem(Items[i], index == SelectedIndex)
            {
                AutoSize = false,
                Width = Math.Max(1, menuWidth - 4),
                Height = Math.Max(36, textHeight + 12),
                Margin = Padding.Empty,
                Padding = Padding.Empty,
                Font = Font,
                ForeColor = ForeColor
            };
            totalHeight += item.Height;
            item.Click += (_, _) =>
            {
                // WinForms itself is STILL inside ToolStripDropDown.OnItemClicked
                // here. Never rebuild the compact form or dispose the menu on
                // this stack. The 0.24.14 owner crash was ObjectDisposedException
                // in ToolStripDropDown.SetVisibleCore after premature Dispose.
                if (!IsHandleCreated || IsDisposed || Disposing) return;
                BeginInvoke(new Action(() =>
                {
                    if (IsDisposed || Disposing) return;
                    if (!menu.IsDisposed && menu.Visible) menu.Close();
                    SelectedIndex = index;
                }));
            };
            menu.Items.Add(item);
        }
        menu.Height = totalHeight;
        _activeMenu = menu;
        menu.Closed += (_, _) =>
        {
            if (ReferenceEquals(_activeMenu, menu)) _activeMenu = null;
            // Closing happens *inside* the WinForms item-click dispatch. Do
            // not dispose synchronously: native OnItemClicked still uses Handle.
            if (menu.IsDisposed) return;
            if (!IsDisposed && !Disposing && IsHandleCreated)
                BeginInvoke(new Action(() => { if (!menu.IsDisposed) menu.Dispose(); }));
            else
                menu.Dispose();
        };
        try { menu.Show(this, new Point(0, Height - 1)); }
        catch
        {
            _activeMenu = null;
            menu.Dispose();
            throw;
        }
    }

    private sealed class DarkOptionItem(string label, bool isCurrent) : ToolStripMenuItem(label)
    {
        protected override void OnPaint(PaintEventArgs e)
        {
            // Owner paint disables the native check-glyph gutter that previously
            // pushed the label/highlight sideways. All rows align consistently.
            var bg = Selected ? ColorTranslator.FromHtml("#19302D") :
                ColorTranslator.FromHtml("#141B1F");
            using (var fill = new SolidBrush(bg))
                e.Graphics.FillRectangle(fill, new Rectangle(Point.Empty, Size));
            if (Selected)
            {
                using var border = new Pen(ColorTranslator.FromHtml("#66E0BF"));
                e.Graphics.DrawRectangle(border, 1, 1,
                    Math.Max(0, Width - 3), Math.Max(0, Height - 3));
            }
            if (isCurrent)
            {
                using var accent = new SolidBrush(ColorTranslator.FromHtml("#66E0BF"));
                e.Graphics.FillRectangle(accent, 5, Height / 2 - 4, 3, 8);
            }
            TextRenderer.DrawText(e.Graphics, Text, Font,
                new Rectangle(15, 2, Math.Max(5, Width - 26), Height - 4),
                ForeColor, TextFormatFlags.Left | TextFormatFlags.VerticalCenter |
                TextFormatFlags.WordBreak | TextFormatFlags.NoPrefix);
        }
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
        path.AddArc(rect.Right - corner * 2, rect.Bottom - corner * 2, corner * 2, corner * 2, 0, 90);
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
