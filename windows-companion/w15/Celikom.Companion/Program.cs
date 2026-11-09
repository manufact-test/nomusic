using Celikom.NativeInstaller;

namespace Celikom.Companion;

internal static class Program
{
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
            catch
            {
                return 2;
            }
        }
        ApplicationConfiguration.Initialize();
        Application.Run(new MainWindow(args.Length == 1 && args[0] == "--complete-update"));
        return 0;
    }
}
