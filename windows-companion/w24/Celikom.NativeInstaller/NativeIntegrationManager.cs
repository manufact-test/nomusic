using System.Diagnostics;
using Celikom.WindowsRecovery;

namespace Celikom.NativeInstaller;

public enum NativeInstallState
{
    NotInstalled, Active, Restored, Prepared, Interrupted, Changed
}

/// <summary>
/// Local Windows install lifecycle. Builds images from the user's exact
/// original Yandex files, records a durable backup, and can restore them.
/// All installation happens only after an explicit UI consent and with normal
/// Windows protections left enabled.
/// </summary>
public static class NativeIntegrationManager
{
    public const string SupportedVersion = "5.126.1.0";
    public const string SupportedAsarSha256 =
        "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215";

    public static string DefaultYandexDirectory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Programs", "YandexMusic");
    public static string DefaultIntegrationAssets => Path.Combine(
        AppContext.BaseDirectory, "integration");
    public static string DefaultBackupDirectory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows", "NativeHost", "snapshot");

    public static NativeInstallState Inspect(string? root = null, string? backup = null)
    {
        root ??= DefaultYandexDirectory;
        backup ??= DefaultBackupDirectory;
        if (!Directory.Exists(backup)) return NativeInstallState.NotInstalled;
        try
        {
            var info = PairRecovery.Inspect(root, backup);
            string exeHash = PairRecovery.Hash(Path.Combine(root, PairRecovery.ExeName));
            string asarHash = PairRecovery.Hash(Path.Combine(root, PairRecovery.AsarName));
            if (info.State == "RESTORED" &&
                info.OriginalExe == exeHash && info.OriginalAsar == asarHash)
                return NativeInstallState.Restored;
            if (info.State == "ACTIVE" &&
                info.AppliedExe == exeHash && info.AppliedAsar == asarHash)
                return NativeInstallState.Active;
            if (info.State == "PREPARED" &&
                info.OriginalExe == exeHash && info.OriginalAsar == asarHash)
                return NativeInstallState.Prepared;
            if (info.State is "APPLYING" or "RESTORING") return NativeInstallState.Interrupted;
            return NativeInstallState.Changed;
        }
        catch { return NativeInstallState.Changed; }
    }

    public static NativeInstallState Install(string? root = null, string? assets = null,
        string? backup = null)
    {
        if (!OperatingSystem.IsWindows()) throw new IOException("WINDOWS_ONLY");
        root ??= DefaultYandexDirectory;
        assets ??= DefaultIntegrationAssets;
        backup ??= DefaultBackupDirectory;
        var current = Inspect(root, backup);
        if (current == NativeInstallState.Active) return NativeInstallState.Active;
        if (current == NativeInstallState.Interrupted)
            throw new IOException("PREVIOUS_INSTALL_INTERRUPTED_RESTORE_FIRST");
        if (current == NativeInstallState.Changed)
            throw new IOException("YANDEX_FILES_DIFFER_FROM_KNOWN_BACKUP");

        var exe = Path.Combine(root, PairRecovery.ExeName);
        var asar = Path.Combine(root, PairRecovery.AsarName);
        if (!File.Exists(exe) || !File.Exists(asar))
            throw new IOException("YANDEX_NOT_INSTALLED");
        var actualVersion = FileVersionInfo.GetVersionInfo(exe).FileVersion;
        if (actualVersion is not ("5.126.1" or "5.126.1.0"))
            throw new IOException("UNSUPPORTED_YANDEX_VERSION");
        if (!NativeHostSignature.IsValid(exe))
            throw new IOException("OFFICIAL_YANDEX_EXE_NOT_TRUSTED");
        if (PairRecovery.Hash(asar) != SupportedAsarSha256)
            throw new IOException("UNSUPPORTED_ASAR_VERSION");
        var host = Path.Combine(assets, "host.cjs");
        var renderer = Path.Combine(assets, "renderer.js");
        if (!File.Exists(host) || !File.Exists(renderer))
            throw new IOException("CELIKOM_NATIVE_MODULE_NOT_INSTALLED");

        CloseYandexGracefully();
        // Recheck after process exit to reject an updater modifying the files.
        if (!NativeHostSignature.IsValid(exe) ||
            PairRecovery.Hash(asar) != SupportedAsarSha256)
            throw new IOException("YANDEX_CHANGED_DURING_PREFLIGHT");
        var originalExe = File.ReadAllBytes(exe);
        var originalAsar = File.ReadAllBytes(asar);
        var images = NativeAsarImageBuilder.Build(
            originalExe, originalAsar, File.ReadAllBytes(host), File.ReadAllBytes(renderer),
            NativeAsarImageBuilder.Hash(originalExe), SupportedAsarSha256);

        var parent = Path.GetDirectoryName(Path.GetFullPath(backup))!;
        Directory.CreateDirectory(parent);
        if (Directory.Exists(backup))
        {
            if (current is not (NativeInstallState.Restored or NativeInstallState.Prepared))
                throw new IOException("BACKUP_STATUS_UNSAFE");
            var archive = Path.Combine(parent,
                "previous-" + Guid.NewGuid().ToString("N"));
            Directory.Move(backup, archive); // never overwrite previous originals
        }

        var staging = Path.Combine(parent, ".stage-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(staging);
        try
        {
            var stagedExe = Path.Combine(staging, "patch.exe");
            var stagedAsar = Path.Combine(staging, "patch.asar");
            File.WriteAllBytes(stagedExe, images.Executable);
            File.WriteAllBytes(stagedAsar, images.Asar);
            if (PairRecovery.Hash(stagedExe) != images.NewExeSha256 ||
                PairRecovery.Hash(stagedAsar) != images.NewAsarSha256)
                throw new IOException("STAGED_FILES_NOT_VERIFIED");
            PairRecovery.Capture(root, backup, images.OriginalExeSha256,
                images.OriginalAsarSha256);
            PairRecovery.ApplyStaged(root, backup, stagedExe, stagedAsar);
            if (Inspect(root, backup) != NativeInstallState.Active)
                throw new IOException("INSTALLED_FILES_FAIL_VERIFICATION");
            return NativeInstallState.Active;
        }
        finally
        {
            if (Directory.Exists(staging))
                Directory.Delete(staging, recursive: true);
        }
    }

    public static NativeInstallState Restore(string? root = null, string? backup = null)
    {
        if (!OperatingSystem.IsWindows()) throw new IOException("WINDOWS_ONLY");
        root ??= DefaultYandexDirectory;
        backup ??= DefaultBackupDirectory;
        var status = Inspect(root, backup);
        if (status == NativeInstallState.NotInstalled) return status;
        if (status is NativeInstallState.Restored or NativeInstallState.Prepared) return status;
        if (status == NativeInstallState.Changed)
            throw new IOException("YANDEX_UPDATED_OR_BACKUP_CHANGED");
        CloseYandexGracefully();
        PairRecovery.Restore(root, backup);
        if (Inspect(root, backup) != NativeInstallState.Restored)
            throw new IOException("RESTORE_NOT_VERIFIED");
        return NativeInstallState.Restored;
    }

    private static void CloseYandexGracefully()
    {
        var deadline = DateTime.UtcNow.AddSeconds(15);
        foreach (var process in Process.GetProcessesByName("Яндекс Музыка"))
        {
            using (process)
            {
                try { process.CloseMainWindow(); }
                catch (InvalidOperationException) { }
            }
        }
        while (Process.GetProcessesByName("Яндекс Музыка").Length > 0)
        {
            if (DateTime.UtcNow >= deadline)
                throw new IOException("CLOSE_YANDEX_AND_TRY_AGAIN");
            Thread.Sleep(350);
        }
    }
}
