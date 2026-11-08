using System.Text;
using Celikom.Companion.Core;

Console.OutputEncoding = Encoding.UTF8;
if (args.Contains("--help", StringComparer.OrdinalIgnoreCase))
{
    Console.WriteLine("CELIKOM Windows Probe W1 — read-only Yandex Music Electron archive inspection.");
    Console.WriteLine("Usage: CELIKOM-Windows-Probe.exe [--help]");
    Console.WriteLine("No files or accounts are modified. Report has only redacted installation metadata.");
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
        var archive = AsarInspector.Inspect(asarPath);
        Console.WriteLine();
        Console.WriteLine(archive.SafeReport());
    }

    Console.WriteLine();
    Console.WriteLine("ЭТО ТОЛЬКО ЧТЕНИЕ: никакие файлы Яндекса не изменены.");
    Console.WriteLine("Аудиоподмена и интеграционный хук пока не установлены.");
    return snapshot.IsInstalled ? 0 : 2;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
                              System.ComponentModel.Win32Exception or ArgumentException)
{
    Console.Error.WriteLine("Не удалось проверить приложение. Файлы Яндекс.Музыки не изменены.");
    return 3;
}
