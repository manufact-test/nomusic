using System.Text;
using Celikom.Companion.Core;

Console.OutputEncoding = Encoding.UTF8;
if (args.Contains("--help", StringComparer.OrdinalIgnoreCase))
{
    Console.WriteLine("CELIKOM Windows Probe — read-only preliminary Yandex Music installation check.");
    Console.WriteLine("Usage: CELIKOM-Windows-Probe.exe [--help]");
    Console.WriteLine("This tool does not modify Yandex Music, connect to an account, or transmit any data.");
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
    Console.WriteLine("Это только диагностика: подмена музыки пока не реализована.");
    return snapshot.IsInstalled ? 0 : 2;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
                              System.ComponentModel.Win32Exception or ArgumentException)
{
    Console.Error.WriteLine("Не удалось проверить приложение. Файлы Яндекс.Музыки не изменены.");
    return 3;
}
