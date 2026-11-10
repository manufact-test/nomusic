// Real Win32 mouse/keyboard exercise on disposable Windows CI desktop.
// Does not contact support API, open the Yandex player or touch user installation.
using System.Drawing;
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
        for (int iteration = 0; iteration < 10; iteration++)
        {
            var target = iteration % 2 == 0 ? 1 : 0;
            PositionSelector(support);
            Click(support.PointToScreen(new Point(Math.Min(40, support.Width / 2), support.Height / 2)));
            var firstItem = support.PointToScreen(new Point(30, support.Height + 15));
            var hwnd = WindowFromPoint(firstItem);
            if (hwnd == IntPtr.Zero || !GetWindowRect(hwnd, out var popupRect))
                throw new InvalidOperationException("W67_MENU_NOT_OPEN " + iteration);
            Console.WriteLine($"W67_MENU_OPEN cycle={iteration} rect={popupRect.Left},{popupRect.Top},{popupRect.Right},{popupRect.Bottom} selector={support.Width}");
            // On old 0.24.14 each item is 31 px tall, 4 px top menu padding.
            var rowY = target == 0 ? 19 : 50;
            Click(support.PointToScreen(new Point(35, support.Height + rowY)));
            if (support.SelectedIndex != target)
                throw new InvalidOperationException($"W67_MOUSE_SELECTION_FAILED cycle={iteration} expected={target} actual={support.SelectedIndex}");
            if (category.Visible != (target == 1))
                throw new InvalidOperationException("W67_SUPPORT_CONDITIONAL_CATEGORY_FAILED");
            if (form.IsDisposed || !form.Visible)
                throw new InvalidOperationException("W67_APP_CLOSED_DURING_SELECTION");
        }
        Console.WriteLine("W67_BASELINE_REAL_MOUSE_SELECTION_PASS events=" + events);
        return 0;
    }
}
