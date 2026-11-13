using System.Text;
using Celikom.Companion.Core;

Console.OutputEncoding = Encoding.UTF8;
if (args.Contains("--help", StringComparer.OrdinalIgnoreCase))
{
    Console.WriteLine("CELIKOM Windows Probe W10 — read-only executable integrity and ASAR identity.");
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
        // Do not re-run W2/W3's 1117-file source survey: the owner already
        // supplied the complete W3 result. Only revalidate archive identity
        // against the exact build before reading EXE fuse and PE resources.
        var w1 = AsarInspector.Inspect(asarPath);
        Console.WriteLine();
        Console.WriteLine("W10 owner ASAR identity: " +
            (string.Equals(w1.Sha256,
                "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215",
                StringComparison.OrdinalIgnoreCase) ? "MATCH_OWNER_W3" : "CHANGED_OR_UNVERIFIED"));
        Console.WriteLine();
        Console.WriteLine(ElectronIntegrityReadOnly.Inspect(executable, asarPath).SafeReport());
    }
    Console.WriteLine();
    Console.WriteLine("Read-only W10: EXE/ASAR не изменялись, подмена не подключалась.");
    return snapshot.IsInstalled ? 0 : 2;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException
    or System.ComponentModel.Win32Exception or ArgumentException)
{
    Console.Error.WriteLine("Ошибка диагностики. Официальная Яндекс.Музыка не изменялась.");
    return 3;
}
