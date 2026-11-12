using System.Diagnostics;

namespace Celikom.WindowsRecovery;

/// <summary>
/// Replaces an already-registered native patch without the unsafe
/// ACTIVE -> RESTORED -> (possibly failing) fresh install window.
/// Every previous patched pair is archived beside the immutable originals.
/// </summary>
public static partial class PairRecovery
{
    public static Manifest PrepareUpgrade(string installDirectory, string backupDirectory,
        string stagedExe, string stagedAsar)
    {
        var root = Full(installDirectory);
        var backup = Full(backupDirectory);
        var record = ReadVerified(root, backup);
        if (record.State != "ACTIVE" || record.AppliedExe is null || record.AppliedAsar is null)
            throw new IOException("UPGRADE_REQUIRES_ACTIVE_PATCH");
        if (OperatingSystem.IsWindows() &&
            Process.GetProcessesByName("Яндекс Музыка").Length > 0)
            throw new IOException("YANDEX_MUST_BE_CLOSED_FOR_UPGRADE");

        // Verify the candidate BEFORE writing any host file or upgrade intent.
        var nextExe = Hash(stagedExe);
        var nextAsar = Hash(stagedAsar);
        if (nextExe == record.AppliedExe || nextAsar == record.AppliedAsar)
            throw new IOException("UPGRADE_MUST_CHANGE_BOTH_FILES");
        AssertHostMatches(root, record.AppliedExe, record.AppliedAsar);
        var archiveRoot = Path.Combine(backup, "upgrades");
        Directory.CreateDirectory(archiveRoot);
        EnsureSafe(archiveRoot);
        var archiveId = Guid.NewGuid().ToString("N");
        var pending = Path.Combine(archiveRoot, ".pending-" + archiveId);
        var completed = Path.Combine(archiveRoot, archiveId);
        Directory.CreateDirectory(pending);
        try
        {
            File.Copy(HostPath(root, ExeName), Path.Combine(pending, "previous.exe"));
            File.Copy(HostPath(root, AsarName), Path.Combine(pending, "previous.asar"));
            VerifyBackupFilesForUpgrade(pending, record.AppliedExe, record.AppliedAsar);
            AssertHostMatches(root, record.AppliedExe, record.AppliedAsar);
            // Same-volume rename publishes a complete, immutable recovery pair.
            Directory.Move(pending, completed);
            var upgrading = record with
            {
                State = "UPGRADING",
                PreviousAppliedExe = record.AppliedExe,
                PreviousAppliedAsar = record.AppliedAsar,
                PreviousArchive = archiveId,
                AppliedExe = nextExe,
                AppliedAsar = nextAsar
            };
            WriteManifest(backup, upgrading); // durable intent BEFORE host writes
            return upgrading;
        }
        finally
        {
            if (Directory.Exists(pending)) Directory.Delete(pending, recursive: true);
        }
    }

    public static Manifest ApplyUpgradeStaged(string installDirectory, string backupDirectory,
        string stagedExe, string stagedAsar)
    {
        var record = PrepareUpgrade(installDirectory, backupDirectory, stagedExe, stagedAsar);
        try
        {
            var root = Full(installDirectory);
            ApplyOne(HostPath(root, ExeName), stagedExe, record.AppliedExe!,
                record.PreviousAppliedExe!);
            ApplyOne(HostPath(root, AsarName), stagedAsar, record.AppliedAsar!,
                record.PreviousAppliedAsar!);
            return CommitUpgrade(root, backupDirectory);
        }
        catch
        {
            try { RollbackUpgrade(installDirectory, backupDirectory); }
            catch { /* Unknown vendor files must never be overwritten. Keep UPGRADING intent. */ }
            throw;
        }
    }

    public static Manifest CommitUpgrade(string installDirectory, string backupDirectory)
    {
        var record = ReadVerified(installDirectory, backupDirectory);
        if (record.State != "UPGRADING")
            throw new IOException("NO_UPGRADE_TO_COMMIT");
        AssertHostMatches(Full(installDirectory), record.AppliedExe!, record.AppliedAsar!);
        var active = record with
        {
            State = "ACTIVE",
            PreviousAppliedExe = null,
            PreviousAppliedAsar = null,
            PreviousArchive = null
        };
        WriteManifest(Full(backupDirectory), active);
        return active;
    }

    /// <summary>
    /// Recovery from a crash or an error during in-place upgrade. Both actual
    /// host files must be exactly old or new known hashes; third-party updates
    /// are never replaced. The original vendor snapshot is left untouched.
    /// </summary>
    public static Manifest RollbackUpgrade(string installDirectory, string backupDirectory)
    {
        var root = Full(installDirectory);
        var backup = Full(backupDirectory);
        var record = ReadVerified(root, backup);
        if (record.State != "UPGRADING")
            throw new IOException("NO_UPGRADE_TO_ROLL_BACK");
        if (OperatingSystem.IsWindows() &&
            Process.GetProcessesByName("Яндекс Музыка").Length > 0)
            throw new IOException("YANDEX_MUST_BE_CLOSED_FOR_ROLLBACK");

        var exe = HostPath(root, ExeName);
        var asar = HostPath(root, AsarName);
        var exeNow = Hash(exe);
        var asarNow = Hash(asar);
        if ((exeNow != record.PreviousAppliedExe && exeNow != record.AppliedExe) ||
            (asarNow != record.PreviousAppliedAsar && asarNow != record.AppliedAsar))
            throw new IOException("HOST_UPDATED_DURING_UPGRADE_NO_AUTOREPAIR");

        var previous = UpgradeArchive(backup, record);
        RestoreOne(exe, Path.Combine(previous, "previous.exe"),
            record.PreviousAppliedExe!, record.AppliedExe!);
        RestoreOne(asar, Path.Combine(previous, "previous.asar"),
            record.PreviousAppliedAsar!, record.AppliedAsar!);
        AssertHostMatches(root, record.PreviousAppliedExe!, record.PreviousAppliedAsar!);
        var active = record with
        {
            State = "ACTIVE",
            AppliedExe = record.PreviousAppliedExe,
            AppliedAsar = record.PreviousAppliedAsar,
            PreviousAppliedExe = null,
            PreviousAppliedAsar = null,
            PreviousArchive = null
        };
        WriteManifest(backup, active);
        return active;
    }

    private static string UpgradeArchive(string backup, Manifest record)
    {
        if (record.PreviousArchive is not { Length: 32 } name ||
            name.Any(c => c is not (>= '0' and <= '9' or >= 'a' and <= 'f')))
            throw new IOException("UNSAFE_UPGRADE_ARCHIVE_ID");
        var folder = Path.Combine(backup, "upgrades", name);
        EnsureSafe(folder);
        return folder;
    }

    private static void VerifyUpgradeArchive(string backup, Manifest record)
    {
        RequireHash(record.PreviousAppliedExe);
        RequireHash(record.PreviousAppliedAsar);
        VerifyBackupFilesForUpgrade(UpgradeArchive(backup, record),
            record.PreviousAppliedExe!, record.PreviousAppliedAsar!);
    }

    private static void VerifyBackupFilesForUpgrade(string folder, string exeHash, string asarHash)
    {
        var exe = Path.Combine(folder, "previous.exe");
        var asar = Path.Combine(folder, "previous.asar");
        if (Hash(exe) != exeHash || Hash(asar) != asarHash)
            throw new IOException("PREVIOUS_PATCH_BACKUP_HASH_MISMATCH");
    }
}
