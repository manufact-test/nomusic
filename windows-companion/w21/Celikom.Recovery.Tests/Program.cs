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
    Console.WriteLine("W21_RECOVERY_CONTRACT_PASS " + passed);
}
finally
{
    if (Directory.Exists(root)) Directory.Delete(root, true);
}
