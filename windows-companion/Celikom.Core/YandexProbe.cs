using System.Diagnostics;
using Microsoft.Win32;

namespace Celikom.Companion.Core;

/// <summary>Read-only discovery. Does not open, patch, inject or control Yandex Music.</summary>
public static class YandexProbe
{
    private static readonly string[] ExecutableNames =
    {
        "Яндекс Музыка.exe", "Яндекс.Музыка.exe", "Yandex Music.exe", "YandexMusic.exe"
    };

    public static YandexSnapshot Scan()
    {
        string? executable = FindExecutable(GetInstallRoots());
        if (executable is null)
        {
            return new(false, false, null, null, false, "NOT_INSTALLED",
                "Не удалось найти установленное приложение. При нестандартном пути потребуется ручная проверка.");
        }

        bool running = IsKnownProcessRunning(executable);
        string? version = null;
        try
        {
            var info = FileVersionInfo.GetVersionInfo(executable);
            version = string.IsNullOrWhiteSpace(info.ProductVersion) ? info.FileVersion : info.ProductVersion;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or ArgumentException)
        {
            // The installation may be partially updated or inaccessible.
        }

        bool asar = File.Exists(Path.Combine(Path.GetDirectoryName(executable)!, "resources", "app.asar"));
        return new(true, running, executable, version, asar,
            running ? "RUNNING" : "CLOSED",
            running ? "Приложение обнаружено и запущено. Подмена пока не подключена."
                    : "Приложение обнаружено, но сейчас не запущено.");
    }

    /// <summary>Deterministic candidate finder, also used by isolated temporary-directory tests.</summary>
    public static string? FindExecutable(IEnumerable<string> installRoots)
    {
        foreach (var root in installRoots)
        {
            if (string.IsNullOrWhiteSpace(root)) continue;
            try
            {
                // A registry DisplayIcon may point straight at the installed executable.
                if (File.Exists(root) && IsAllowedExecutableName(Path.GetFileName(root)))
                    return Path.GetFullPath(root);

                foreach (var name in ExecutableNames)
                {
                    var candidate = Path.Combine(root, name);
                    if (File.Exists(candidate)) return Path.GetFullPath(candidate);
                }
            }
            catch (Exception ex) when (ex is ArgumentException or IOException or UnauthorizedAccessException
                                       or NotSupportedException)
            {
                // Never write to or attempt to repair an unknown installation.
            }
        }
        return null;
    }

    public static bool IsAllowedExecutableName(string filename) =>
        ExecutableNames.Contains(filename, StringComparer.OrdinalIgnoreCase);

    public static string RedactPersonalPath(string? path)
    {
        if (string.IsNullOrWhiteSpace(path)) return "not found";
        string redacted = path;
        foreach (var pair in new[]
        {
            (Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "%LOCALAPPDATA%"),
            (Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "%APPDATA%"),
            (Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "%USERPROFILE%")
        }.OrderByDescending(p => p.Item1.Length))
        {
            if (string.IsNullOrWhiteSpace(pair.Item1)) continue;
            if (redacted.StartsWith(pair.Item1, StringComparison.OrdinalIgnoreCase))
                return pair.Item2 + redacted[pair.Item1.Length..];
        }
        // No arbitrary usernames or directories are exported.
        return "<custom installation path>";
    }

    private static IEnumerable<string> GetInstallRoots()
    {
        var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        var programFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);

        yield return Path.Combine(local, "Programs", "YandexMusic");
        yield return Path.Combine(local, "Programs", "Yandex Music");
        yield return Path.Combine(programFiles, "YandexMusic");
        yield return Path.Combine(programFilesX86, "YandexMusic");

        // Registry read is limited to normal uninstall records. No credentials or Yandex account data.
        foreach (var hive in new[] { Registry.CurrentUser, Registry.LocalMachine })
        {
            foreach (var keyName in new[]
            {
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                @"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            })
            {
                RegistryKey? uninstall = null;
                try { uninstall = hive.OpenSubKey(keyName); }
                catch (Exception ex) when (ex is System.Security.SecurityException or UnauthorizedAccessException) { }
                if (uninstall is null) continue;
                using (uninstall)
                {
                    string[] names;
                    try { names = uninstall.GetSubKeyNames(); }
                    catch (Exception ex) when (ex is System.Security.SecurityException or UnauthorizedAccessException) { continue; }

                    foreach (var name in names)
                    {
                        RegistryKey? app = null;
                        try { app = uninstall.OpenSubKey(name); }
                        catch (Exception ex) when (ex is System.Security.SecurityException or UnauthorizedAccessException) { }
                        if (app is null) continue;
                        using (app)
                        {
                            string displayName = app.GetValue("DisplayName") as string ?? "";
                            if (!displayName.Equals("Яндекс Музыка", StringComparison.OrdinalIgnoreCase)
                                && !displayName.Equals("Yandex Music", StringComparison.OrdinalIgnoreCase))
                                continue;

                            if (app.GetValue("InstallLocation") is string dir && !string.IsNullOrWhiteSpace(dir))
                                yield return dir.Trim('"');

                            if (app.GetValue("DisplayIcon") is string icon && !string.IsNullOrWhiteSpace(icon))
                            {
                                // DisplayIcon often includes an icon-index suffix ",0".
                                var candidate = icon.Trim().Trim('"');
                                if (candidate.EndsWith(",0", StringComparison.Ordinal))
                                    candidate = candidate[..^2];
                                yield return candidate.Trim('"');
                            }
                        }
                    }
                }
            }
        }
    }

    private static bool IsKnownProcessRunning(string executable)
    {
        string expectedName = Path.GetFileNameWithoutExtension(executable);
        Process[] processes;
        try { processes = Process.GetProcessesByName(expectedName); }
        catch (Exception ex) when (ex is InvalidOperationException or System.ComponentModel.Win32Exception)
        {
            return false;
        }

        foreach (var process in processes)
        {
            using (process)
            {
                try
                {
                    string? runningFile = process.MainModule?.FileName;
                    if (runningFile is not null &&
                        Path.GetFullPath(runningFile).Equals(Path.GetFullPath(executable),
                            StringComparison.OrdinalIgnoreCase))
                        return true;
                }
                catch (Exception ex) when (ex is System.ComponentModel.Win32Exception or InvalidOperationException
                                               or UnauthorizedAccessException)
                {
                    // Process exists, but access to its executable path was restricted.
                    // Do not claim it is the official installation without matching the path.
                }
            }
        }
        return false;
    }
}
