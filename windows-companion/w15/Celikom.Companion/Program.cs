using Celikom.NativeInstaller;

namespace Celikom.Companion;

internal static class Program
{
    private const string MutexName = @"Local\CELIKOM.Windows.Companion.SingleInstance";
    private const string SignalName = @"Local\CELIKOM.Windows.Companion.Show";

    [STAThread]
    static int Main(string[] args)
    {
        if (args.Length == 1 && args[0] == "--restore-native")
        {
            try
            {
                NativeIntegrationManager.Restore();
                return 0;
            }
            catch { return 2; }
        }

        var background = args.Length == 1 && args[0] == "--background";
        var completedUpdate = args.Length == 1 && args[0] == "--complete-update";
        using var mutex = new Mutex(true, MutexName, out var firstInstance);
        if (!firstInstance)
        {
            // Opening the app manually while it runs in the tray brings up
            // the existing popup, rather than starting competing bridges.
            if (!background)
            {
                try
                {
                    using var other = EventWaitHandle.OpenExisting(SignalName);
                    other.Set();
                }
                catch (WaitHandleCannotBeOpenedException) { }
                catch (UnauthorizedAccessException) { }
            }
            return 0;
        }
        ApplicationConfiguration.Initialize();
        using var signal = new EventWaitHandle(false,
            EventResetMode.AutoReset, SignalName);
        using var app = new MainWindow(completedUpdate, background);
        var registration = ThreadPool.RegisterWaitForSingleObject(signal,
            (_, _) =>
            {
                if (!app.IsDisposed && app.IsHandleCreated)
                {
                    try { app.BeginInvoke(new Action(app.RestoreWindowFromSecondLaunch)); }
                    catch (InvalidOperationException) { }
                }
            }, null, Timeout.Infinite, executeOnlyOnce: false);
        try { Application.Run(app); }
        finally { registration.Unregister(null); }
        return 0;
    }
}
