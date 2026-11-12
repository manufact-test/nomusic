using Celikom.WindowsRecovery;
using System.Text;

int passed = 0;
void Check(bool value, string name) { if (!value) throw new Exception("W21_FAIL: " + name); passed++; }
void Reject(Action call, string name)
{
    bool refused = false;
    try { call(); }
    catch (IOException) { refused = true; }
    Check(refused, name);
}
string Sha(string path) => PairRecovery.Hash(path);
var root = Path.Combine(Path.GetTempPath(), "celikom-w21-" + Guid.NewGuid().ToString("N"));
var host = Path.Combine(root, "YandexMusic");
var backups = Path.Combine(root, "backups");
Directory.CreateDirectory(Path.Combine(host, "resources"));
Directory.CreateDirectory(backups);
var exe = Path.Combine(host, PairRecovery.ExeName);
var asar = Path.Combine(host, "resources", "app.asar");
try
{
    void SetOriginal()
    {
        File.WriteAllText(exe, "test official executable " + new string('a', 1000));
        File.WriteAllText(asar, "test official asar " + new string('b', 1000));
    }
    SetOriginal();
    var originalExe = Sha(exe);
    var originalAsar = Sha(asar);
    var backupA = Path.Combine(backups, "snapshot-A");
    Reject(() => PairRecovery.Capture(host, Path.Combine(host, "inside-host"),
        originalExe, originalAsar), "no backup inside installation");
    Reject(() => PairRecovery.Capture(host, backupA, new string('0', 64), originalAsar),
        "cannot back up wrong source identity");
    var prepared = PairRecovery.Capture(host, backupA, originalExe, originalAsar);
    Check(prepared.State == "PREPARED", "initial snapshot is inert");
    Check(File.Exists(Path.Combine(backupA, "original.exe")), "original exe retained");
    Check(File.Exists(Path.Combine(backupA, "original.asar")), "original asar retained");
    Reject(() => PairRecovery.Capture(host, backupA, originalExe, originalAsar),
        "never overwrite original snapshot");
    Reject(() => PairRecovery.Restore(host, backupA),
        "cannot restore without a registered known patch");
    Reject(() => PairRecovery.RegisterApplied(host, backupA,
        originalExe, originalAsar), "no-op cannot mark active");

    File.WriteAllText(exe, "known-patched-exe");
    File.WriteAllText(asar, "known-patched-asar");
    var modifiedExe = Sha(exe);
    var modifiedAsar = Sha(asar);
    Reject(() => PairRecovery.RegisterApplied(host, backupA, modifiedExe,
        new string('a', 64)), "wrong after-patch asar cannot be registered");
    var active = PairRecovery.RegisterApplied(host, backupA, modifiedExe, modifiedAsar);
    Check(active.State == "ACTIVE", "known modification registered");
    File.WriteAllText(asar, "FOREIGN YANDEX UPDATE");
    Reject(() => PairRecovery.Restore(host, backupA),
        "unknown third-party update never overwritten");
    Check(File.ReadAllText(asar) == "FOREIGN YANDEX UPDATE",
        "foreign change preserved unchanged");
    File.WriteAllText(asar, "known-patched-asar");
    var restored = PairRecovery.Restore(host, backupA);
    Check(restored.State == "RESTORED", "restore completed");
    Check(Sha(exe) == originalExe && Sha(asar) == originalAsar,
        "both files returned byte-identical");
    Check(PairRecovery.Restore(host, backupA).State == "RESTORED",
        "safe repeated restore is idempotent");

    // A broken backup must fail BEFORE any installed host byte is changed.
    var backupB = Path.Combine(backups, "snapshot-B");
    var b = PairRecovery.Capture(host, backupB, originalExe, originalAsar);
    File.WriteAllText(exe, "patched-B");
    File.WriteAllText(asar, "patched-asar-B");
    var shaBexe = Sha(exe);
    var shaBasar = Sha(asar);
    PairRecovery.RegisterApplied(host, backupB, shaBexe, shaBasar);
    File.WriteAllText(Path.Combine(backupB, "original.exe"), "TAMPERED BACKUP");
    Reject(() => PairRecovery.Restore(host, backupB), "corrupted backup rejected");
    Check(Sha(exe) == shaBexe && Sha(asar) == shaBasar,
        "corrupt snapshot cannot affect host");

    // A simulated crash after the first original file was restored:
    // remaining known patched file may recover, but no foreign file may.
    var backupC = Path.Combine(backups, "snapshot-C");
    SetOriginal();
    PairRecovery.Capture(host, backupC, originalExe, originalAsar);
    File.WriteAllText(exe, "patched-C");
    File.WriteAllText(asar, "patched-asar-C");
    PairRecovery.RegisterApplied(host, backupC, Sha(exe), Sha(asar));
    File.WriteAllText(exe, "test official executable " + new string('a', 1000));
    var crashResumed = PairRecovery.Restore(host, backupC);
    Check(crashResumed.State == "RESTORED", "partial file restore resumed safely");
    Check(Sha(exe) == originalExe && Sha(asar) == originalAsar,
        "partial recovery yields exact originals");
    Check(Directory.GetFiles(backups, "*.celikom-restore-*", SearchOption.AllDirectories).Length == 0,
        "staged restore files cleaned");

    // Real installation transaction shape: durable intent precedes either write.
    var backupD = Path.Combine(backups, "snapshot-D");
    var stagedExeD = Path.Combine(root, "new-exe");
    var stagedAsarD = Path.Combine(root, "new-asar");
    SetOriginal();
    PairRecovery.Capture(host, backupD, originalExe, originalAsar);
    File.WriteAllText(stagedExeD, "integrated-exe-D");
    File.WriteAllText(stagedAsarD, "integrated-asar-D");
    var appliedD = PairRecovery.ApplyStaged(host, backupD, stagedExeD, stagedAsarD);
    Check(appliedD.State == "ACTIVE", "staged pair installed with durable recovery record");
    Check(Sha(exe) == Sha(stagedExeD) && Sha(asar) == Sha(stagedAsarD),
        "integrated pair equals staged image hashes");
    PairRecovery.Restore(host, backupD);
    Check(Sha(exe) == originalExe && Sha(asar) == originalAsar,
        "transactional apply restores byte-identical originals");

    // Crash between file writes: prepared intent allows safe restore.
    var backupE = Path.Combine(backups, "snapshot-E");
    PairRecovery.Capture(host, backupE, originalExe, originalAsar);
    PairRecovery.PrepareApply(host, backupE, Sha(stagedExeD), Sha(stagedAsarD));
    File.Copy(stagedExeD, exe, true); // Emulate power loss after EXE swap, before ASAR.
    Check(PairRecovery.Inspect(host, backupE).State == "APPLYING",
        "interrupted transaction intent survives restart");
    PairRecovery.Restore(host, backupE);
    Check(Sha(exe) == originalExe && Sha(asar) == originalAsar,
        "restore handles partial APPLYING state safely");

    // A foreign update after interrupted install is never overwritten.
    var backupF = Path.Combine(backups, "snapshot-F");
    PairRecovery.Capture(host, backupF, originalExe, originalAsar);
    PairRecovery.PrepareApply(host, backupF, Sha(stagedExeD), Sha(stagedAsarD));
    File.WriteAllText(asar, "a third-party change");
    Reject(() => PairRecovery.Restore(host, backupF),
        "foreign modification during pending apply blocks recovery");
    Check(File.ReadAllText(asar) == "a third-party change",
        "foreign ASAR preserved on refusal");
    // W79: upgrading from an already active, verified patch never requires
    // a destructive restore-then-install sequence.
    var stageNewExe = Path.Combine(root, "upgrade-new.exe");
    var stageNewAsar = Path.Combine(root, "upgrade-new.asar");
    File.WriteAllText(stageNewExe, "integrated-upgrade-new-exe");
    File.WriteAllText(stageNewAsar, "integrated-upgrade-new-asar");
    SetOriginal();
    var backupG = Path.Combine(backups, "snapshot-G");
    PairRecovery.Capture(host, backupG, originalExe, originalAsar);
    File.WriteAllText(exe, "integrated-old-exe");
    File.WriteAllText(asar, "integrated-old-asar");
    var oldExeHash = Sha(exe);
    var oldAsarHash = Sha(asar);
    PairRecovery.RegisterApplied(host, backupG, oldExeHash, oldAsarHash);
    var snapshotOriginalHash = Sha(Path.Combine(backupG, "original.exe"));
    var upgraded = PairRecovery.ApplyUpgradeStaged(host, backupG, stageNewExe, stageNewAsar);
    Check(upgraded.State == "ACTIVE" && upgraded.AppliedExe == Sha(stageNewExe) &&
        upgraded.AppliedAsar == Sha(stageNewAsar), "W79 fully staged active upgrade commits");
    Check(Sha(Path.Combine(backupG, "original.exe")) == snapshotOriginalHash &&
        Sha(Path.Combine(backupG, "original.asar")) == originalAsar,
        "W79 original vendor backup never overwritten by upgrade");
    Check(Directory.GetDirectories(Path.Combine(backupG, "upgrades")).Length == 1,
        "W79 previously active native files retained in separate durable archive");
    var restoreAfterUpgrade = PairRecovery.Restore(host, backupG);
    Check(restoreAfterUpgrade.State == "RESTORED" && Sha(exe) == originalExe &&
        Sha(asar) == originalAsar, "W79 upgraded host can restore original exact bytes");

    // A failure BEFORE the upgrade intent cannot strip an active host.
    SetOriginal();
    var backupH = Path.Combine(backups, "snapshot-H");
    PairRecovery.Capture(host, backupH, originalExe, originalAsar);
    File.WriteAllText(exe, "old-active-exe-H");
    File.WriteAllText(asar, "old-active-asar-H");
    var oldHExe = Sha(exe);
    var oldHAsar = Sha(asar);
    PairRecovery.RegisterApplied(host, backupH, oldHExe, oldHAsar);
    Reject(() => PairRecovery.ApplyUpgradeStaged(host, backupH, stageNewExe,
        Path.Combine(root, "nonexistent-staged.asar")),
        "W79 missing candidate refused before active host changes");
    Check(Sha(exe) == oldHExe && Sha(asar) == oldHAsar &&
        PairRecovery.Inspect(host, backupH).State == "ACTIVE",
        "W79 failed preflight preserves active pair and manifest");

    // Process dies halfway through the upgrade: one new file + one old file.
    var pendingH = PairRecovery.PrepareUpgrade(host, backupH, stageNewExe, stageNewAsar);
    Check(pendingH.State == "UPGRADING" && pendingH.PreviousAppliedExe == oldHExe,
        "W79 planned hashes and archived old patch are durable before writes");
    File.Copy(stageNewExe, exe, overwrite: true);
    var rolledH = PairRecovery.RollbackUpgrade(host, backupH);
    Check(rolledH.State == "ACTIVE" && Sha(exe) == oldHExe && Sha(asar) == oldHAsar,
        "W79 interrupted partial pair returns to previous active host");
    Check(Sha(Path.Combine(backupH, "original.exe")) == originalExe,
        "W79 rollback keeps vendor original byte identical");

    // In-flight vendor update (e.g., 5.127.0) is foreign: refuse repair
    // instead of overwriting it with stale 5.126.1 bytes.
    PairRecovery.PrepareUpgrade(host, backupH, stageNewExe, stageNewAsar);
    File.WriteAllText(asar, "third-party-yandex-5.127.0");
    var foreignHash = Sha(asar);
    Reject(() => PairRecovery.RollbackUpgrade(host, backupH),
        "W79 vendor update during in-flight upgrade prevents automatic rollback");
    Check(Sha(asar) == foreignHash && Sha(exe) == oldHExe &&
        PairRecovery.Inspect(host, backupH).State == "UPGRADING",
        "W79 unknown host untouched and durable warning survives restart");
    Reject(() => PairRecovery.Restore(host, backupH),
        "W79 explicit restore also refuses unknown 5.127.0 host");

    // Active manifest alone never authorizes updating unknown vendor bytes.
    SetOriginal();
    var backupI = Path.Combine(backups, "snapshot-I");
    PairRecovery.Capture(host, backupI, originalExe, originalAsar);
    File.WriteAllText(exe, "old-active-exe-I");
    File.WriteAllText(asar, "old-active-asar-I");
    PairRecovery.RegisterApplied(host, backupI, Sha(exe), Sha(asar));
    File.WriteAllText(exe, "different-vendor-exe-5.127.0");
    File.WriteAllText(asar, "different-vendor-asar-5.127.0");
    var changedIExe = Sha(exe);
    var changedIAsar = Sha(asar);
    Reject(() => PairRecovery.PrepareUpgrade(host, backupI, stageNewExe, stageNewAsar),
        "W79 unknown files refused even when manifest says ACTIVE");
    Check(Sha(exe) == changedIExe && Sha(asar) == changedIAsar &&
        PairRecovery.Inspect(host, backupI).State == "ACTIVE",
        "W79 upgrade refusal does not modify vendor update or snapshot");

    Console.WriteLine("W21_RECOVERY_CONTRACT_PASS " + passed);
}
finally
{
    if (Directory.Exists(root)) Directory.Delete(root, true);
}
