using System.Drawing;
using System.Windows.Forms;

namespace Celikom.Companion;

/// <summary>Chrome popup palette for the actual Windows selection field.</summary>
public sealed class PopupSelect : ComboBox
{
    private static readonly Color Surface = ColorTranslator.FromHtml("#141B1F");
    private static readonly Color Fore = ColorTranslator.FromHtml("#F4F7F8");
    private static readonly Color Hover = ColorTranslator.FromHtml("#19302D");
    public PopupSelect()
    {
        DrawMode = DrawMode.OwnerDrawFixed;
        DropDownStyle = ComboBoxStyle.DropDownList;
        FlatStyle = FlatStyle.Flat;
        BackColor = Surface;
        ForeColor = Fore;
        Font = new Font("Segoe UI", 9F);
        ItemHeight = 25;
        DropDownHeight = 170;
    }
    protected override void OnDrawItem(DrawItemEventArgs e)
    {
        if (e.Index < 0 || e.Index >= Items.Count)
        {
            e.DrawBackground();
            return;
        }
        var selected = (e.State & DrawItemState.Selected) != 0;
        using var brush = new SolidBrush(selected ? Hover : Surface);
        e.Graphics.FillRectangle(brush, e.Bounds);
        var bounds = Rectangle.Inflate(e.Bounds, -8, 0);
        TextRenderer.DrawText(e.Graphics, GetItemText(Items[e.Index]), Font, bounds, Fore,
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter |
            TextFormatFlags.SingleLine | TextFormatFlags.EndEllipsis);
        if ((e.State & DrawItemState.Focus) != 0)
            e.DrawFocusRectangle();
    }
}