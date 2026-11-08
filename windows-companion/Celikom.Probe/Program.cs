using System.Text;
using Celikom.Companion.Core;

Console.OutputEncoding = Encoding.UTF8;
if (args.Contains("--help", StringComparer.OrdinalIgnoreCase))
{
    Console.WriteLine("CELIKOM Windows Probe W2 — read-only Yandex Electron renderer topology.");
    Console.WriteLine("Usage: CELIKOM-Windows-Probe.exe [--help]");
    Console.WriteLine("No installation, account, sound or application files are changed.");
    return 0;
}
if (args.Length > 0)
{
    Console.Error.WriteLine("Unknown argument. Run with --help.");
    return 1;
}

try
{
    var snapshot = YandexProbe.Scan();
    Console.WriteLine(snapshot.SafeReport());
    Console.WriteLine();
    Console.WriteLine(snapshot.Detail);
    if (snapshot.IsInstalled && snapshot.ExecutablePath is { } executable)
    {
        var asarPath = Path.Combine(Path.GetDirectoryName(executable)!, "resources", "app.asar");
        var w1 = AsarInspector.Inspect(asarPath);
        Console.WriteLine();
        Console.WriteLine(w1.SafeReport());
        Console.WriteLine();
        Console.WriteLine(AsarTopology.Inspect(asarPath, w1.Sha256).SafeReport());
    }
    Console.WriteLine();
    Console.WriteLine("Read-only W2: подмена и модификация Яндекс.Музыки НЕ проводились.");
    return snapshot.IsInstalled ? 0 : 2;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException
    or System.ComponentModel.Win32Exception or ArgumentException)
{
    Console.Error.WriteLine("Ошибка диагностики. Официальная Яндекс.Музыка не изменялась.");
    return 3;
}
