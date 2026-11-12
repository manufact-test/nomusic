using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;

namespace Celikom.WindowsRecovery;

/// <summary>
/// Two-file, restartable recovery protocol. Does NOT patch or start Yandex.
/// This engine is not wired to the consumer installer. Caller must first
/// establish trusted official Yandex identity, explicit consent and a legal adapter.
/// </summary>
public static partial class PairRecovery
{
    public const string ExeName = "Яндекс Музыка.exe";
    public const string AsarName = "resources/app.asar";
    private const string ManifestName = "recovery.json";

    public sealed record Manifest(
        int Schema, string InstallRoot, string OriginalExe, string OriginalAsar,
        string? AppliedExe, string? AppliedAsar, string State,
        string? PreviousAppliedExe = null, string? PreviousAppliedAsar = null,
        string? PreviousArchive = null);

    public static Manifest Capture(string installDirectory, string backupDirectory,
        string expectedOriginalExeSha256, string expectedOriginalAsarSha256)
    {
        var root = Full(installDirectory);
        var backup = Full(backupDirectory);
        if (Overlaps(root, backup)) throw new IOException("BACKUP_OVERLAPS_HOST");
        if (Directory.Exists(backup) || File.Exists(backup))
            throw new IOException("BACKUP_ALREADY_EXISTS");
        RequireHash(expectedOriginalExeSha256);
        RequireHash(expectedOriginalAsarSha256);
        EnsureSafe(root);
        var exe = HostPath(root, ExeName);
        var asar = HostPath(root, AsarName);
        RequireFile(exe); RequireFile(asar);
        if (Hash(exe) != expectedOriginalExeSha256 ||
            Hash(asar) != expectedOriginalAsarSha256)
            throw new IOException("ORIGINAL_IDENTITY_CHANGED");

        var parent = Path.GetDirectoryName(backup)!;
        Directory.CreateDirectory(parent);
        EnsureSafe(parent);
        var pending = Path.Combine(parent, ".celikom-pending-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(pending);
        try
        {
            // Copy original bytes only. Never touch the host installation.
            File.Copy(exe, Path.Combine(pending, "original.exe"));
            File.Copy(asar, Path.Combine(pending, "original.asar"));
            VerifyBackupFiles(pending, expectedOriginalExeSha256, expectedOriginalAsarSha256);
            // Detect a concurrent Yandex update during the snapshot.
            if (Hash(exe) != expectedOriginalExeSha256 ||
                Hash(asar) != expectedOriginalAsarSha256)
                throw new IOException("ORIGINAL_CHANGED_DURING_SNAPSHOT");
            var record = new Manifest(1, root, expectedOriginalExeSha256,
                expectedOriginalAsarSha256, null, null, "PREPARED");
            WriteManifest(pending, record);
            Directory.Move(pending, backup); // same-volume atomic directory rename
            return record;
        }
        finally
        {
            if (Directory.Exists(pending)) Directory.Delete(pending, true);
        }
    }

    /// <summary>
    /// Write the planned post-modification hashes BEFORE changing either host
    /// file. If installation is interrupted, Restore accepts a mix of known
    /// original and known patched bytes. Requires the app to be closed.
    /// </summary>
    public static Manifest PrepareApply(string installDirectory, string backupDirectory,
        string expectedAppliedExe, string expectedAppliedAsar)
    {
        RequireHash(expectedAppliedExe);
        RequireHash(expectedAppliedAsar);
        var record = ReadVerified(installDirectory, backupDirectory);
        if (record.State != "PREPARED") throw new IOException("SNAPSHOT_NOT_PREPARED");
        if (OperatingSystem.IsWindows() && Process.GetProcessesByName("Яндекс Музыка").Length > 0)
            throw new IOException("YANDEX_MUST_BE_CLOSED_FOR_APPLY");
        AssertHostMatches(Full(installDirectory), record.OriginalExe, record.OriginalAsar);
        if (record.OriginalExe == expectedAppliedExe ||
            record.OriginalAsar == expectedAppliedAsar)
            throw new IOException("EXPECTED_BOTH_FILES_TO_CHANGE");
        var next = record with {
            AppliedExe = expectedAppliedExe, AppliedAsar = expectedAppliedAsar,
            State = "APPLYING"
        };
        WriteManifest(Full(backupDirectory), next);
        return next;
    }

    public static Manifest CommitApply(string installDirectory, string backupDirectory)
    {
        var record = ReadVerified(installDirectory, backupDirectory);
        if (record.State != "APPLYING" ||
            record.AppliedExe is null || record.AppliedAsar is null)
            throw new IOException("NOT_AN_APPLYING_PATCH");
        AssertHostMatches(Full(installDirectory), record.AppliedExe, record.AppliedAsar);
        var next = record with { State = "ACTIVE" };
        WriteManifest(Full(backupDirectory), next);
        return next;
    }

    /// <summary>
    /// Applies two already built, fully hash-verified images. Automatically
    /// attempts byte-identical restore when a write fails. Both files remain
    /// independently replaceable; the durable intent handles interrupted runs.
    /// </summary>
    public static Manifest ApplyStaged(string installDirectory, string backupDirectory,
        string stagedExe, string stagedAsar)
    {
        RequireFile(stagedExe);
        RequireFile(stagedAsar);
        var exeHash = Hash(stagedExe);
        var asarHash = Hash(stagedAsar);
        PrepareApply(installDirectory, backupDirectory, exeHash, asarHash);
        try
        {
            var root = Full(installDirectory);
            ApplyOne(HostPath(root, ExeName), stagedExe, exeHash,
                ReadVerified(root, backupDirectory).OriginalExe);
            ApplyOne(HostPath(root, AsarName), stagedAsar, asarHash,
                ReadVerified(root, backupDirectory).OriginalAsar);
            return CommitApply(root, backupDirectory);
        }
        catch
        {
            try { Restore(installDirectory, backupDirectory); }
            catch { /* Leave durable APPLYING/RESTORING state for manual retry. */ }
            throw;
        }
    }

    private static void ApplyOne(string target, string staged, string expected,
        string original)
    {
        if (Hash(target) != original) throw new IOException("HOST_CHANGED_DURING_APPLY");
        var temp = target + ".celikom-apply-" + Guid.NewGuid().ToString("N");
        try
        {
            File.Copy(staged, temp);
            if (Hash(temp) != expected) throw new IOException("STAGED_IMAGE_CHANGED");
            if (Hash(target) != original) throw new IOException("HOST_CHANGED_DURING_APPLY");
            File.Move(temp, target, true);
            if (Hash(target) != expected) throw new IOException("IMAGE_APPLY_CHECKSUM_MISMATCH");
        }
        finally { if (File.Exists(temp)) File.Delete(temp); }
    }

    /// <summary>
    /// Called ONLY by a separately approved adapter after a known patch has
    /// been fully applied and both resulting fingerprints are known.
    /// Never guesses a modification from arbitrary current bytes.
    /// </summary>
    public static Manifest RegisterApplied(string installDirectory, string backupDirectory,
        string expectedAppliedExeSha256, string expectedAppliedAsarSha256)
    {
        RequireHash(expectedAppliedExeSha256);
        RequireHash(expectedAppliedAsarSha256);
        var record = ReadVerified(installDirectory, backupDirectory);
        if (record.State != "PREPARED") throw new IOException("SNAPSHOT_NOT_PREPARED");
        if (record.OriginalExe == expectedAppliedExeSha256 &&
            record.OriginalAsar == expectedAppliedAsarSha256)
            throw new IOException("NO_MODIFICATION_TO_RECORD");
        var root = Full(installDirectory);
        AssertHostMatches(root, expectedAppliedExeSha256, expectedAppliedAsarSha256);
        var next = record with
        {
            AppliedExe = expectedAppliedExeSha256,
            AppliedAsar = expectedAppliedAsarSha256,
            State = "ACTIVE"
        };
        WriteManifest(Full(backupDirectory), next);
        return next;
    }

    /// <summary>
    /// Restores ONLY our registered patch, or one file already restored.
    /// A third-party update/unknown modified file causes a safe refusal.
    /// The state RESTORING survives process termination and allows a retry.
    /// This is per-file atomic, NOT a false claim of cross-file ACID atomicity.
    /// </summary>
    public static Manifest Restore(string installDirectory, string backupDirectory)
    {
        var root = Full(installDirectory);
        var backup = Full(backupDirectory);
        var record = ReadVerified(root, backup);
        if (record.State == "UPGRADING")
        {
            RollbackUpgrade(root, backup);
            record = ReadVerified(root, backup);
        }
        if (record.State == "RESTORED")
        {
            AssertHostMatches(root, record.OriginalExe, record.OriginalAsar);
            return record;
        }
        if (record.State is not ("APPLYING" or "ACTIVE" or "RESTORING") ||
            record.AppliedExe is null || record.AppliedAsar is null)
            throw new IOException("NOT_AN_ACTIVE_RECOGNIZED_PATCH");
        if (OperatingSystem.IsWindows() && Process.GetProcessesByName("Яндекс Музыка").Length > 0)
            throw new IOException("YANDEX_MUST_BE_CLOSED_FOR_RESTORE");

        var exe = HostPath(root, ExeName);
        var asar = HostPath(root, AsarName);
        var presentExe = Hash(exe);
        var presentAsar = Hash(asar);
        if (presentExe != record.AppliedExe && presentExe != record.OriginalExe ||
            presentAsar != record.AppliedAsar && presentAsar != record.OriginalAsar)
            throw new IOException("HOST_UPDATED_OR_UNKNOWN_MODIFICATION");

        if (record.State is "APPLYING" or "ACTIVE")
        {
            record = record with { State = "RESTORING" };
            WriteManifest(backup, record); // crash marker BEFORE touching either target
        }
        // Stage on each host file's volume so each replacement is atomic.
        RestoreOne(exe, Path.Combine(backup, "original.exe"),
            record.OriginalExe, record.AppliedExe);
        RestoreOne(asar, Path.Combine(backup, "original.asar"),
            record.OriginalAsar, record.AppliedAsar);

        AssertHostMatches(root, record.OriginalExe, record.OriginalAsar);
        record = record with { State = "RESTORED" };
        WriteManifest(backup, record);
        // Retain backup, including provenance, after successful restore.
        return record;
    }

    public static Manifest Inspect(string installDirectory, string backupDirectory) =>
        ReadVerified(installDirectory, backupDirectory);

    private static void RestoreOne(string destination, string original,
        string expectedOriginal, string expectedApplied)
    {
        RequireFile(destination);
        var current = Hash(destination);
        if (current == expectedOriginal) return;
        if (current != expectedApplied) throw new IOException("TARGET_CHANGED_BEFORE_RESTORE");
        var tmp = destination + ".celikom-restore-" + Guid.NewGuid().ToString("N");
        try
        {
            File.Copy(original, tmp);
            if (Hash(tmp) != expectedOriginal) throw new IOException("RESTORE_STAGING_HASH_MISMATCH");
            if (Hash(destination) != expectedApplied)
                throw new IOException("TARGET_CHANGED_DURING_RESTORE");
            File.Move(tmp, destination, true);
            if (Hash(destination) != expectedOriginal)
                throw new IOException("RESTORED_FILE_HASH_MISMATCH");
        }
        finally { if (File.Exists(tmp)) File.Delete(tmp); }
    }

    private static Manifest ReadVerified(string installDirectory, string backupDirectory)
    {
        var root = Full(installDirectory);
        var backup = Full(backupDirectory);
        if (Overlaps(root, backup)) throw new IOException("BACKUP_OVERLAPS_HOST");
        EnsureSafe(root);
        EnsureSafe(backup);
        var manifestPath = Path.Combine(backup, ManifestName);
        RequireFile(manifestPath);
        var manifest = JsonSerializer.Deserialize<Manifest>(File.ReadAllText(manifestPath))
            ?? throw new IOException("INVALID_BACKUP_MANIFEST");
        if (manifest.Schema != 1 ||
            !string.Equals(manifest.InstallRoot, root, StringComparison.OrdinalIgnoreCase) ||
            manifest.State is not ("PREPARED" or "APPLYING" or "ACTIVE" or "RESTORING" or "RESTORED" or "UPGRADING"))
            throw new IOException("BACKUP_PROVENANCE_MISMATCH");
        RequireHash(manifest.OriginalExe);
        RequireHash(manifest.OriginalAsar);
        if (manifest.State != "PREPARED")
        {
            RequireHash(manifest.AppliedExe);
            RequireHash(manifest.AppliedAsar);
        }
        VerifyBackupFiles(backup, manifest.OriginalExe, manifest.OriginalAsar);
        if (manifest.State == "UPGRADING") VerifyUpgradeArchive(backup, manifest);
        return manifest;
    }

    private static void AssertHostMatches(string root, string exeHash, string asarHash)
    {
        if (Hash(HostPath(root, ExeName)) != exeHash ||
            Hash(HostPath(root, AsarName)) != asarHash)
            throw new IOException("HOST_FINGERPRINT_CHANGED");
    }

    private static void VerifyBackupFiles(string folder, string exeHash, string asarHash)
    {
        var exe = Path.Combine(folder, "original.exe");
        var asar = Path.Combine(folder, "original.asar");
        RequireFile(exe); RequireFile(asar);
        if (Hash(exe) != exeHash || Hash(asar) != asarHash)
            throw new IOException("BACKUP_HASH_MISMATCH");
    }

    private static void WriteManifest(string folder, Manifest value)
    {
        var destination = Path.Combine(folder, ManifestName);
        var pending = Path.Combine(folder, ".recovery-" + Guid.NewGuid().ToString("N"));
        try
        {
            File.WriteAllText(pending, JsonSerializer.Serialize(value, new JsonSerializerOptions { WriteIndented = true }));
            File.Move(pending, destination, true);
        }
        finally { if (File.Exists(pending)) File.Delete(pending); }
    }

    private static string HostPath(string root, string relative)
    {
        var full = Path.GetFullPath(Path.Combine(root, relative));
        if (!full.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
            throw new IOException("PATH_ESCAPES_HOST");
        var parent = Path.GetDirectoryName(full)!;
        EnsureSafe(parent);
        return full;
    }

    private static string Full(string path) =>
        Path.TrimEndingDirectorySeparator(Path.GetFullPath(path));

    private static bool Overlaps(string a, string b) =>
        a.Equals(b, StringComparison.OrdinalIgnoreCase) ||
        a.StartsWith(b + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) ||
        b.StartsWith(a + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);

    private static void EnsureSafe(string path)
    {
        var walk = Full(path);
        while (Directory.Exists(walk) || File.Exists(walk))
        {
            if ((File.GetAttributes(walk) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("SYMLINK_OR_REPARSE_POINT_REFUSED");
            var parent = Path.GetDirectoryName(walk);
            if (string.IsNullOrEmpty(parent) || parent == walk) break;
            walk = parent;
        }
    }

    private static void RequireFile(string path)
    {
        if (!File.Exists(path)) throw new IOException("REQUIRED_FILE_MISSING");
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("SYMLINK_OR_REPARSE_POINT_REFUSED");
    }

    private static void RequireHash(string? hash)
    {
        if (hash is not { Length: 64 } ||
            hash.Any(c => c is not (>= '0' and <= '9' or >= 'a' and <= 'f')))
            throw new IOException("INVALID_EXPECTED_SHA256");
    }

    public static string Hash(string file)
    {
        RequireFile(file);
        using var stream = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.Read);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }
}
