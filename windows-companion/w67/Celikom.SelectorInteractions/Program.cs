// Real Win32 mouse/keyboard exercise on disposable Windows CI desktop.
// Does not contact support API, open the Yandex player or touch user installation.
using System.Drawing;
using System.Drawing.Imaging;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Celikom.Companion;

internal static class Program
{
    private const BindingFlags PrivateInstance = BindingFlags.Instance | BindingFlags.NonPublic;
    private const uint LeftDown = 0x0002;
    private const uint LeftUp = 0x0004;
    [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
    [DllImport("user32.dll")] private static extern IntPtr WindowFromPoint(Point p);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] private static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extraInfo);
    [StructLayout(LayoutKind.Sequential)]
    private struct Rect { public int Left, Top, Right, Bottom; }
    private static MainWindow _form = null!;
    private static object Get(string field)
        => typeof(MainWindow).GetField(field, PrivateInstance)?.GetValue(_form)
            ?? throw new InvalidOperationException("W67_FIELD_MISSING " + field);
    private static void Set(string field, object value)
        => typeof(MainWindow).GetField(field, PrivateInstance)!.SetValue(_form, value);
    private static void Call(string method, params object[] args)
        => typeof(MainWindow).GetMethod(method, PrivateInstance)!.Invoke(_form, args);
    private static void Pump()
    {
        for (int i = 0; i < 9; i++)
        {
            Application.DoEvents();
            Thread.Sleep(15);
        }
    }
    private static void Click(Point p)
    {
        if (!SetCursorPos(p.X, p.Y)) throw new InvalidOperationException("W67_SET_CURSOR_FAILED");
        Pump();
        mouse_event(LeftDown, 0, 0, 0, UIntPtr.Zero);
        Pump();
        mouse_event(LeftUp, 0, 0, 0, UIntPtr.Zero);
        Pump();
    }
    private static void KeyPress(Keys key)
    {
        // Physical Windows key-down/up injection with the GUI foregrounded.
        keybd_event((byte)key, 0, 0, UIntPtr.Zero);
        Pump();
        keybd_event((byte)key, 0, 2, UIntPtr.Zero);
        Pump();
    }
    private static void PositionSelector(PopupOptionSelect select)
    {
        Call("LayoutCompact");
        var positions = (Dictionary<Control, int>)Get("_compactPositions");
        var owner = (Control)select;
        while (!positions.ContainsKey(owner) && owner.Parent is not null)
            owner = owner.Parent;
        Call("SetCompactOffset", Math.Max(0, positions[owner] - 15));
        Pump();
        if (!select.Visible || select.Width < 100 || select.Height < 30)
            throw new InvalidOperationException("W67_SELECTOR_NOT_VISIBLE");
        var center = select.PointToScreen(new Point(select.Width / 2, select.Height / 2));
        if (!_form.Bounds.Contains(center))
            throw new InvalidOperationException("W67_SELECTOR_OFF_FORM " + center);
    }

    [STAThread]
    private static int Main()
    {
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.ThrowException);
        ApplicationConfiguration.Initialize();
        using var form = new MainWindow();
        _form = form;
        form.StartPosition = FormStartPosition.Manual;
        form.Location = new Point(100, 100);
        form.ClientSize = new Size(308, 560);
        form.Show();
        SetForegroundWindow(form.Handle);
        Pump();
        Set("_compactAccountOpen", false);
        Set("_compactUploadOpen", false);
        Set("_compactSuggestOpen", false);
        Set("_compactSupportOpen", true);
        Call("LayoutCompact");
        var support = (PopupOptionSelect)Get("_compactSupportKind");
        var category = (PopupOptionSelect)Get("_compactSupportCategory");
        var events = 0;
        support.SelectedIndexChanged += (_, _) => events++;
        Console.WriteLine("W67_BASELINE_START selected=" + support.SelectedIndex);
        for (int iteration = 0; iteration < 24; iteration++)
        {
            var target = iteration % 2 == 0 ? 1 : 0;
            PositionSelector(support);
            Click(support.PointToScreen(new Point(Math.Min(40, support.Width / 2), support.Height / 2)));
            var menu = (ContextMenuStrip?)typeof(PopupOptionSelect)
                .GetField("_activeMenu", PrivateInstance)?.GetValue(support)
                ?? throw new InvalidOperationException("W67_MENU_NOT_OPEN " + iteration);
            var item = menu.Items[target];
            Pump();
            var popupOrigin = menu.PointToScreen(Point.Empty);
            var formBounds = form.RectangleToScreen(form.ClientRectangle);
            var popupBounds = new Rectangle(popupOrigin, menu.Size);
            Console.WriteLine($"W67_MENU_OPEN cycle={iteration} rect={popupBounds} selector={support.Width} font={support.Font.Size}");
            if (popupBounds.Left < formBounds.Left || popupBounds.Right > formBounds.Right)
                throw new InvalidOperationException($"W67_MENU_SPILLS_OUT_OF_FORM {popupBounds} form={formBounds}");
            if (menu.ShowImageMargin || menu.ShowCheckMargin || menu.Items.OfType<ToolStripItem>()
                .Any(x => x.Margin.Horizontal != 0 || x.Width > menu.Width || x.Width < menu.Width - 8))
                throw new InvalidOperationException("W67_MENU_ITEM_GUTTER_OR_WIDTH_UNEVEN");
            // User-like mouse click on the actual second/first menu item,
            // not SelectedIndex assignment or PerformClick().
            var targetPoint = menu.PointToScreen(new Point(
                item.Bounds.Left + Math.Min(45, item.Width / 2),
                item.Bounds.Top + item.Height / 2));
            if (iteration == 0)
            {
                // Inspect the real OS-rendered popup (including hover style).
                SetCursorPos(targetPoint.X, targetPoint.Y);
                Pump();
                var screenshots = Path.GetFullPath("windows-companion/w67/out");
                Directory.CreateDirectory(screenshots);
                using var screenshot = new Bitmap(menu.Width, menu.Height);
                using (var g = Graphics.FromImage(screenshot))
                    g.CopyFromScreen(menu.PointToScreen(Point.Empty), Point.Empty, menu.Size);
                screenshot.Save(Path.Combine(screenshots, "support-kind-hover.png"), ImageFormat.Png);
            }
            Click(targetPoint);
            Pump(); // complete queued WinForms native menu Close and deferred layout
            if (support.SelectedIndex != target)
                throw new InvalidOperationException($"W67_MOUSE_SELECTION_FAILED cycle={iteration} expected={target} actual={support.SelectedIndex}");
            if (category.Visible != (target == 1))
                throw new InvalidOperationException("W67_SUPPORT_CONDITIONAL_CATEGORY_FAILED");
            if (form.IsDisposed || !form.Visible)
                throw new InvalidOperationException("W67_APP_CLOSED_DURING_SELECTION");
        }
        Console.WriteLine("W67_REAL_MOUSE_SELECTION_AND_WIDTH_PASS events=" + events);
        // Click outside and reopen repeatedly; no extra selection or dead menu.
        for (int i = 0; i < 8; i++)
        {
            PositionSelector(support);
            Click(support.PointToScreen(new Point(40, support.Height / 2)));
            Click(support.PointToScreen(new Point(50, -13)));
            Pump();
            var stale = typeof(PopupOptionSelect).GetField("_activeMenu", PrivateInstance)?.GetValue(support);
            if (stale is ContextMenuStrip { Visible: true })
                throw new InvalidOperationException("W67_CLICK_OUTSIDE_DID_NOT_DISMISS_MENU");
            if (form.IsDisposed || !form.Visible)
                throw new InvalidOperationException("W67_OUTSIDE_DISMISS_CLOSED_APP");
        }
        Console.WriteLine("W67_OUTSIDE_DISMISS_REOPEN_PASS");
        // Keyboard navigation with genuine WinForms focused control and OS keys.
        PositionSelector(support);
        form.Activate();
        SetForegroundWindow(form.Handle);
        support.Select();
        support.Focus();
        Pump();
        Console.WriteLine($"W67_KEYBOARD_FOCUS focused={support.Focused} foreground={GetForegroundWindow() == form.Handle}");
        if (!support.Focused) throw new InvalidOperationException("W67_SELECTOR_NOT_KEYBOARD_FOCUSED");
        var beforeKeys = support.SelectedIndex;
        KeyPress(beforeKeys == 0 ? Keys.Down : Keys.Up);
        if (support.SelectedIndex == beforeKeys)
            throw new InvalidOperationException("W67_KEYBOARD_ARROW_SELECTION_NOT_HANDLED");
        KeyPress(Keys.Enter);
        var keyboardMenu = (ContextMenuStrip?)typeof(PopupOptionSelect)
            .GetField("_activeMenu", PrivateInstance)?.GetValue(support)
            ?? throw new InvalidOperationException("W67_KEYBOARD_ENTER_DID_NOT_OPEN");
        KeyPress(Keys.Down);
        KeyPress(Keys.Enter);
        if (form.IsDisposed || !form.Visible)
            throw new InvalidOperationException("W67_KEYBOARD_MENU_CLOSED_APP");
        Console.WriteLine("W67_KEYBOARD_ARROWS_ENTER_PASS");
        // Same popup implementation is used for the song issue category menu.
        if (support.SelectedIndex != 1) support.SelectedIndex = 1;
        PositionSelector(category);
        Click(category.PointToScreen(new Point(45, category.Height / 2)));
        var categoryMenu = (ContextMenuStrip?)typeof(PopupOptionSelect)
            .GetField("_activeMenu", PrivateInstance)?.GetValue(category)
            ?? throw new InvalidOperationException("W67_CATEGORY_MENU_NOT_OPEN");
        var fourth = categoryMenu.Items[3];
        Click(categoryMenu.PointToScreen(new Point(
            fourth.Bounds.Left + 35, fourth.Bounds.Top + fourth.Height / 2)));
        Pump();
        if (category.SelectedIndex != 3)
            throw new InvalidOperationException("W67_CATEGORY_MOUSE_SELECTION_FAILED");
        Console.WriteLine("W67_CATEGORY_MOUSE_SELECTION_PASS");
        Console.WriteLine("W67_ALL_MENU_INTERACTION_NO_CRASH_PASS");
        return 0;
    }
}
