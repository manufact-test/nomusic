using System.Diagnostics;
using Celikom.WindowsRecovery;

namespace Celikom.NativeInstaller;

public enum NativeInstallState
{
    NotInstalled, Active, Restored, Prepared, Interrupted, VerifiedVendorUpdate, Changed
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
    // Official Yandex 5.127.0.r22015925, validated from YANDEX LLC signed
    // 5.127.0 installer and signed inner EXE on disposable Windows CI.
    public const string Official51270Version = "5.127.0.r22015925";
    public const string Official51270ExeSha256 =
        "de2849a1378daff16500fd5c8499634aab8d994c1ffb1b1d8a6bc264edd9aada";
    public const string Official51270AsarSha256 =
        "c176ff3cecdddfab76b2d0d90bf527bbed226919fab37f5723b46913084620cb";

    private static string? TrustedAsarForVersion(string? version) => version switch
    {
        "5.126.1" or "5.126.1.0" or
            "5.126.1.56270518164a6ebd4b974971490df41224a69d68" => SupportedAsarSha256,
        _ => OfficialYandexCatalog.TryGet(version, out var remote)
            ? remote.AsarSha256 : null
    };

    private static bool IsPinnedOfficialPair(string root, string exeHash, string asarHash) =>
        OfficialYandexCatalog.IsExactTrustedVendorPair(
            Path.Combine(root, PairRecovery.ExeName),
            Path.Combine(root, PairRecovery.AsarName), exeHash, asarHash);


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
            if (info.State == "RESTORED")
            {
                if (info.OriginalExe == exeHash && info.OriginalAsar == asarHash)
                    return NativeInstallState.Restored;
                // W78 owner state: original 5.126 snapshot still verified, but
                // Windows Yandex updated both files to signed official 5.127.
                // No blind adoption: exact independent signed package pins.
                if (IsPinnedOfficialPair(root, exeHash, asarHash))
                    return NativeInstallState.VerifiedVendorUpdate;
            }
            if (info.State == "ACTIVE")
            {
                if (info.AppliedExe == exeHash && info.AppliedAsar == asarHash)
                    return NativeInstallState.Active;
                // Yandex's own updater can replace BOTH of our patched files.
                // Only a fully official reviewed pair is adoptable; any mixed
                // EXE/ASAR remains Changed and cannot be overwritten.
                if (IsPinnedOfficialPair(root, exeHash, asarHash))
                    return NativeInstallState.VerifiedVendorUpdate;
            }
            if (info.State == "PREPARED" &&
                info.OriginalExe == exeHash && info.OriginalAsar == asarHash)
                return NativeInstallState.Prepared;
            if (info.State is "APPLYING" or "RESTORING" or "UPGRADING") return NativeInstallState.Interrupted;
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
        var expectedAsar = TrustedAsarForVersion(actualVersion) ??
            throw new IOException("UNSUPPORTED_YANDEX_VERSION");
        if (!NativeHostSignature.IsValid(exe))
            throw new IOException("OFFICIAL_YANDEX_EXE_NOT_TRUSTED");
        if (PairRecovery.Hash(asar) != expectedAsar)
            throw new IOException("UNSUPPORTED_ASAR_VERSION");
        if (OfficialYandexCatalog.TryGet(actualVersion, out _) &&
            !OfficialYandexCatalog.IsExactTrustedVendorPair(exe, asar))
            throw new IOException("UNSUPPORTED_YANDEX_BUILD");
        var host = Path.Combine(assets, "host.cjs");
        var renderer = Path.Combine(assets, "renderer.js");
        if (!File.Exists(host) || !File.Exists(renderer))
            throw new IOException("CELIKOM_NATIVE_MODULE_NOT_INSTALLED");

        CloseYandexGracefully();
        // Recheck after process exit to reject an updater modifying the files.
        if (!NativeHostSignature.IsValid(exe) ||
            PairRecovery.Hash(asar) != expectedAsar ||
            FileVersionInfo.GetVersionInfo(exe).FileVersion != actualVersion ||
            (OfficialYandexCatalog.TryGet(actualVersion, out _) &&
             !OfficialYandexCatalog.IsExactTrustedVendorPair(exe, asar)))
            throw new IOException("YANDEX_CHANGED_DURING_PREFLIGHT");
        var originalExe = File.ReadAllBytes(exe);
        var originalAsar = File.ReadAllBytes(asar);
        var images = NativeAsarImageBuilder.Build(
            originalExe, originalAsar, File.ReadAllBytes(host), File.ReadAllBytes(renderer),
            NativeAsarImageBuilder.Hash(originalExe), expectedAsar);

        var parent = Path.GetDirectoryName(Path.GetFullPath(backup))!;
        Directory.CreateDirectory(parent);
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

            // Only archive the old snapshot AFTER fully staging the next pair.
            // The prior 5.126.1 snapshot stays byte-for-byte intact forever.
            string? previousSnapshot = null;
            if (Directory.Exists(backup))
            {
                if (current is not (NativeInstallState.Restored or NativeInstallState.Prepared or
                    NativeInstallState.VerifiedVendorUpdate))
                    throw new IOException("BACKUP_STATUS_UNSAFE");
                previousSnapshot = Path.Combine(parent,
                    "previous-" + Guid.NewGuid().ToString("N"));
                Directory.Move(backup, previousSnapshot);
            }
            try
            {
                PairRecovery.Capture(root, backup, images.OriginalExeSha256,
                    images.OriginalAsarSha256);
            }
            catch
            {
                // If Yandex auto-updated before the new snapshot could be
                // captured, restore the old snapshot path without host writes.
                if (previousSnapshot != null && !Directory.Exists(backup))
                    Directory.Move(previousSnapshot, backup);
                throw;
            }
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


    /// <summary>
    /// Fully stage and verify new integration images BEFORE replacing an active
    /// installation. Never restore old vendor bytes as an intermediate step.
    /// If Yandex auto-updated outside our recorded pair, refuse without writes.
    /// </summary>
    public static NativeInstallState Upgrade(string? root = null, string? assets = null,
        string? backup = null)
    {
        if (!OperatingSystem.IsWindows()) throw new IOException("WINDOWS_ONLY");
        root ??= DefaultYandexDirectory;
        assets ??= DefaultIntegrationAssets;
        backup ??= DefaultBackupDirectory;
        if (Inspect(root, backup) != NativeInstallState.Active)
            throw new IOException("UPGRADE_REQUIRES_ACTIVE_PATCH");

        var record = PairRecovery.Inspect(root, backup);
        var originalExePath = Path.Combine(backup, "original.exe");
        var originalAsarPath = Path.Combine(backup, "original.asar");
        var version = FileVersionInfo.GetVersionInfo(originalExePath).FileVersion;
        var expectedAsar = TrustedAsarForVersion(version) ??
            throw new IOException("UNSUPPORTED_YANDEX_VERSION");
        if (!NativeHostSignature.IsValid(originalExePath))
            throw new IOException("OFFICIAL_YANDEX_EXE_NOT_TRUSTED");
        if (record.OriginalAsar != expectedAsar ||
            PairRecovery.Hash(originalAsarPath) != expectedAsar)
            throw new IOException("UNSUPPORTED_ASAR_VERSION");
        if (OfficialYandexCatalog.TryGet(version, out _) &&
            !OfficialYandexCatalog.IsExactTrustedVendorPair(originalExePath, originalAsarPath))
            throw new IOException("UNSUPPORTED_YANDEX_BUILD");

        var hostPath = Path.Combine(assets, "host.cjs");
        var rendererPath = Path.Combine(assets, "renderer.js");
        if (!File.Exists(hostPath) || !File.Exists(rendererPath))
            throw new IOException("CELIKOM_NATIVE_MODULE_NOT_INSTALLED");

        // The original snapshot is immutable; build the next pair from it,
        // not from already-patched host files or unsupported 5.127 bytes.
        var images = NativeAsarImageBuilder.Build(
            File.ReadAllBytes(originalExePath), File.ReadAllBytes(originalAsarPath),
            File.ReadAllBytes(hostPath), File.ReadAllBytes(rendererPath),
            record.OriginalExe, record.OriginalAsar);
        var parent = Path.GetDirectoryName(Path.GetFullPath(backup))!;
        Directory.CreateDirectory(parent);
        var staging = Path.Combine(parent, ".upgrade-stage-" + Guid.NewGuid().ToString("N"));
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
            CloseYandexGracefully();
            if (Inspect(root, backup) != NativeInstallState.Active)
                throw new IOException("YANDEX_CHANGED_DURING_UPGRADE_PREFLIGHT");
            PairRecovery.ApplyUpgradeStaged(root, backup, stagedExe, stagedAsar);
            if (Inspect(root, backup) != NativeInstallState.Active)
                throw new IOException("UPGRADED_FILES_FAIL_VERIFICATION");
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
        // Old manifest describes a RESTORED 5.126 host, but the actual files
        // are now verified official 5.127. No CELIKOM patch exists to remove.
        if (status == NativeInstallState.VerifiedVendorUpdate)
            return NativeInstallState.NotInstalled;
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
