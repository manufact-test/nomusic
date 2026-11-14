using Celikom.Companion;
using Celikom.UpdateSupervisor;

var checks = 0;
void Check(bool condition, string why)
{
    checks++;
    if (!condition) throw new Exception("W110_SUPERVISOR_FAILED: " + why);
}
var start = new DateTimeOffset(2026, 11, 14, 8, 0, 0, TimeSpan.Zero);
var guid = Guid.NewGuid();

StableUpdateRollbackJournal.Record NewRecord(
    StableUpdateRollbackJournal.Phase phase) =>
    new(2, guid, phase, "0.24.36.0", "0.24.37.0",
        new string('a', 64), new string('b', 64),
        new string('c', 64), 40_000, 42, 43,
        start.AddMinutes(10).ToUnixTimeSeconds(), 0,
        ExpectedSession: true, NativeWasInstalled: true,
        SessionIdentitySha256: new string('d', 64),
        PreviousApplicationSha256: new string('1', 64),
        TargetApplicationSha256: new string('2', 64),
        PreviousNativeHostSha256: new string('3', 64),
        TargetNativeHostSha256: new string('4', 64),
        PreviousRendererSha256: new string('5', 64),
        TargetRendererSha256: new string('6', 64),
        PreviousSupervisorSha256: new string('7', 64),
        TargetSupervisorSha256: new string('8', 64));

var valid = new StableUpdateRollbackJournal.HealthEvidence(true, true, true, true);
var notReady = new StableUpdateRollbackJournal.HealthEvidence(false, false, false, false);
var signedNoNative = new StableUpdateRollbackJournal.HealthEvidence(true, true, true, false);
var signedNoBridge = new StableUpdateRollbackJournal.HealthEvidence(true, false, true, true);

// W110 is independently testable even when the GUI executable crashes.
// A failed new process queues a rollback only after the signed transaction's
// deadline, not just because a user hasn't clicked Start yet.
var journal = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.Prepared));
var probe = new FakeProbe { Evidence = notReady };
var installer = new FakeLauncher();
var engine = new UpdateSupervisorEngine(guid, journal, probe, installer);
Check(await engine.TickAsync(start) == UpdateSupervisorEngine.Step.Waiting &&
      journal.Current.State == StableUpdateRollbackJournal.Phase.Prepared &&
      installer.LaunchCount == 0,
      "staged old installer is not touched before update launch");

journal.Current = journal.Current with { State = StableUpdateRollbackJournal.Phase.InstallerStarted };
Check(await engine.TickAsync(start.AddMinutes(1)) == UpdateSupervisorEngine.Step.Waiting &&
      installer.LaunchCount == 0,
      "missing new app during bounded boot window is not immediately rolled back");
Check(await engine.TickAsync(start.AddMinutes(11)) == UpdateSupervisorEngine.Step.RollbackQueued &&
      journal.Current.State == StableUpdateRollbackJournal.Phase.RollbackNeeded,
      "new app can crash completely and independent helper schedules rollback");
probe.Safe = false;
Check(await engine.TickAsync(start.AddMinutes(11)) == UpdateSupervisorEngine.Step.Waiting &&
      installer.LaunchCount == 0 && journal.VerifyCount == 0,
      "cannot interrupt a still-running Yandex player or CELIKOM");
probe.Safe = true;
Check(await engine.TickAsync(start.AddMinutes(12)) == UpdateSupervisorEngine.Step.RollbackLaunched &&
      installer.LaunchCount == 1 && journal.VerifyCount == 1 &&
      journal.Current.RollbackAttempts == 1 &&
      journal.Current.DeadlineUnix == start.AddMinutes(22).ToUnixTimeSeconds(),
      "signed previous setup executes once after safe-stop checks; own health deadline");
Check(await engine.TickAsync(start.AddMinutes(13)) == UpdateSupervisorEngine.Step.Waiting,
      "rollback installer start is not mistaken for actual restored health");
probe.Evidence = valid;
probe.ObservedApplicationSha256 = new string('1', 64);
probe.ObservedNativeHostSha256 = new string('3', 64);
probe.ObservedRendererSha256 = new string('5', 64);
probe.ObservedSupervisorSha256 = new string('7', 64);
Check(await engine.TickAsync(start.AddMinutes(14)) ==
        UpdateSupervisorEngine.Step.PreviousVersionRestored &&
      journal.Current.State == StableUpdateRollbackJournal.Phase.Restored &&
      installer.LaunchCount == 1,
      "previous signed version and bridge/session/native evidence complete recovery");
Check(await engine.TickAsync(start.AddMinutes(15)) == UpdateSupervisorEngine.Step.Completed &&
      installer.LaunchCount == 1,
      "finished recovery cannot launch installer again");

// Successful signed new app must first be detected by the external process.
var goodStore = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.InstallerStarted));
var goodProbe = new FakeProbe { Evidence = valid };
var goodLaunch = new FakeLauncher();
var good = new UpdateSupervisorEngine(guid, goodStore, goodProbe, goodLaunch);
Check(await good.TickAsync(start.AddSeconds(5)) ==
        UpdateSupervisorEngine.Step.NewApplicationSeen &&
      goodStore.Current.State == StableUpdateRollbackJournal.Phase.NewAppObserved,
      "actual signed running target EXE is observed before any success marking");
goodProbe.Evidence = signedNoNative;
Check(await good.TickAsync(start.AddSeconds(6)) == UpdateSupervisorEngine.Step.Waiting,
      "running signed target without native module is NOT healthy");
goodProbe.Evidence = signedNoBridge;
Check(await good.TickAsync(start.AddSeconds(7)) == UpdateSupervisorEngine.Step.Waiting,
      "running signed target without authenticated local bridge is NOT healthy");
goodProbe.Evidence = valid;
goodProbe.ObservedNativeHostSha256 = new string('f', 64);
Check(await good.TickAsync(start.AddSeconds(8)) == UpdateSupervisorEngine.Step.Waiting,
      "W112 a mismatched installed native host is not healthy");
goodProbe.ObservedNativeHostSha256 = new string('4', 64);
goodProbe.ObservedRendererSha256 = new string('f', 64);
Check(await good.TickAsync(start.AddSeconds(8)) == UpdateSupervisorEngine.Step.Waiting,
      "W112 a mismatched installed renderer is not healthy");
goodProbe.ObservedRendererSha256 = new string('6', 64);
goodProbe.ObservedSupervisorSha256 = new string('f', 64);
Check(await good.TickAsync(start.AddSeconds(8)) == UpdateSupervisorEngine.Step.Waiting,
      "W114 a mismatched installed supervisor is not healthy");
goodProbe.ObservedSupervisorSha256 = new string('8', 64);
goodProbe.ObservedApplicationSha256 = new string('f', 64);
Check(await good.TickAsync(start.AddSeconds(8)) == UpdateSupervisorEngine.Step.Waiting,
      "W112 a mismatched installed executable is not healthy");
goodProbe.ObservedApplicationSha256 = new string('2', 64);
goodProbe.ObservedSessionFingerprint = new string('e', 64);
Check(await good.TickAsync(start.AddSeconds(8)) == UpdateSupervisorEngine.Step.Waiting,
      "a new readable account is not the original DPAPI login");
goodProbe.ObservedSessionFingerprint = new string('d', 64);
Check(await good.TickAsync(start.AddSeconds(9)) ==
        UpdateSupervisorEngine.Step.NewApplicationHealthy &&
      goodStore.Current.State == StableUpdateRollbackJournal.Phase.Healthy &&
      goodLaunch.LaunchCount == 0,
      "fully checked target app stays installed and old setup never runs");

// Attempt to swap journal transaction ID must be rejected before any effect.
bool wrongTransactionRejected = false;
try
{
    var wrong = new UpdateSupervisorEngine(Guid.NewGuid(), goodStore, goodProbe, goodLaunch);
    await wrong.TickAsync(start.AddSeconds(9));
}
catch (IOException e) when (e.Message == "SUPERVISOR_TRANSACTION_MISMATCH")
{ wrongTransactionRejected = true; }
Check(wrongTransactionRejected, "wrong/replayed transaction cannot be supervised");

// No usable signed rollback image? Stop safely, don't download or execute.
var missing = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.RollbackNeeded))
    { VerifiedPackageAvailable = false };
var noLauncher = new FakeLauncher();
var failed = new UpdateSupervisorEngine(guid, missing,
    new FakeProbe { Safe = true }, noLauncher);
Check(await failed.TickAsync(start.AddMinutes(12)) ==
        UpdateSupervisorEngine.Step.ManualRecovery &&
      missing.Current.State == StableUpdateRollbackJournal.Phase.ManualRecovery &&
      noLauncher.LaunchCount == 0,
      "missing or unsigned previous package never executes");
// Rollback launcher fails: journal remains at one attempt, never retries.
var refused = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.RollbackNeeded));
var rejects = new FakeLauncher { ThrowOnLaunch = true };
var refuseEngine = new UpdateSupervisorEngine(guid, refused,
    new FakeProbe { Safe = true }, rejects);
Check(await refuseEngine.TickAsync(start.AddMinutes(12)) ==
        UpdateSupervisorEngine.Step.ManualRecovery &&
      refused.Current.RollbackAttempts == 1 && rejects.LaunchCount == 1,
      "failed setup execution is manual recovery, not retry storm");
// Second app is still running: never terminate it for a forced downgrade.
var busy = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.RollbackNeeded));
var waiting = new UpdateSupervisorEngine(guid, busy,
    new FakeProbe { Safe = false }, new FakeLauncher());
Check(await waiting.TickAsync(start.AddMinutes(26)) ==
        UpdateSupervisorEngine.Step.ManualRecovery &&
      busy.VerifyCount == 0,
      "beyond bounded playback deferral remain safe, require manual recovery");
// W112 legacy schema-1 records have no signed payload witness and are
// never eligible for unattended install or rollback.
var legacy = NewRecord(StableUpdateRollbackJournal.Phase.RollbackNeeded) with
{
    Schema = 1,
    PreviousApplicationSha256 = "",
    TargetApplicationSha256 = "",
    PreviousNativeHostSha256 = "",
    TargetNativeHostSha256 = "",
    PreviousRendererSha256 = "",
    TargetRendererSha256 = "",
    PreviousSupervisorSha256 = "",
    TargetSupervisorSha256 = ""
};
bool legacyDenied = false;
try
{
    await new UpdateSupervisorEngine(guid, new FakeJournal(legacy),
        new FakeProbe { Safe = true }, new FakeLauncher()).TickAsync(start.AddMinutes(12));
}
catch (IOException e) when (e.Message == "SUPERVISOR_TRANSACTION_SCHEMA_UNSUPPORTED")
{ legacyDenied = true; }
Check(legacyDenied, "W112 legacy journal without exact installed-payload hashes is never auto-executed");

// Failed restoration must not claim success and stops after health timeout.
var incomplete = new FakeJournal(NewRecord(StableUpdateRollbackJournal.Phase.RollbackStarted)
    with { RollbackAttempts = 1, DeadlineUnix = start.AddMinutes(20).ToUnixTimeSeconds() });
var limitedLaunch = new FakeLauncher();
var incompleteEngine = new UpdateSupervisorEngine(guid, incomplete,
    new FakeProbe { Evidence = notReady }, limitedLaunch);
Check(await incompleteEngine.TickAsync(start.AddMinutes(21)) ==
        UpdateSupervisorEngine.Step.ManualRecovery &&
      limitedLaunch.LaunchCount == 0,
      "failed restore health never triggers another install loop");

if (OperatingSystem.IsWindows())
{
    var handshakeId = Guid.NewGuid();
    await using var readyPipe = StableUpdateSupervisorHandshake.CreateServer(handshakeId);
    using var handshakeTimeout = new CancellationTokenSource(TimeSpan.FromSeconds(5));
    var signal = StableUpdateSupervisorHandshake.SignalReadyAsync(
        handshakeId, handshakeTimeout.Token);
    var ready = await StableUpdateSupervisorHandshake.WaitForReadyAsync(
        readyPipe, handshakeTimeout.Token);
    await signal;
    Check(ready, "W122 same-user named-pipe handshake proves the Supervisor has validated its ticket before installer launch");
}
Console.WriteLine("W110_INDEPENDENT_SUPERVISOR_CONTRACT_PASS " + checks);

sealed class FakeJournal(StableUpdateRollbackJournal.Record initial) : ISupervisorJournal
{
    public StableUpdateRollbackJournal.Record Current { get; set; } = initial;
    public bool VerifiedPackageAvailable { get; set; } = true;
    public int VerifyCount { get; private set; }

    public StableUpdateRollbackJournal.Record Read() => Current;

    public void Advance(StableUpdateRollbackJournal.Phase expected,
        StableUpdateRollbackJournal.Phase next)
    {
        if (Current.State != expected) throw new IOException("INVALID_TEST_JOURNAL_STATE");
        Current = Current with { State = next };
    }

    public void BeginRollback(DateTimeOffset now)
    {
        if (Current.State != StableUpdateRollbackJournal.Phase.RollbackNeeded ||
            Current.RollbackAttempts != 0) throw new IOException("REPEATED_ROLLBACK");
        Current = Current with
        {
            State = StableUpdateRollbackJournal.Phase.RollbackStarted,
            RollbackAttempts = 1,
            DeadlineUnix = now.AddMinutes(10).ToUnixTimeSeconds()
        };
    }

    public void ConfirmNewHealthy(StableUpdateRollbackJournal.HealthEvidence evidence,
        DateTimeOffset now)
    {
        if (StableUpdateRollbackJournal.Decide(Current, evidence, now) !=
            StableUpdateRollbackJournal.Decision.AcceptNewVersion)
            throw new IOException("NEW_APP_NOT_HEALTHY");
        Current = Current with { State = StableUpdateRollbackJournal.Phase.Healthy };
    }

    public void ConfirmPreviousHealthy(StableUpdateRollbackJournal.HealthEvidence evidence)
    {
        if (!evidence.ExactSignedNewExe || !evidence.BridgeResponds ||
            !evidence.SessionPreserved || !evidence.NativeIntegrationConsistent)
            throw new IOException("OLD_APP_NOT_HEALTHY");
        Current = Current with { State = StableUpdateRollbackJournal.Phase.Restored };
    }

    public string VerifiedPreviousInstaller()
    {
        VerifyCount++;
        if (!VerifiedPackageAvailable) throw new IOException("INVALID_ROLLBACK_PACKAGE");
        return "C:\\verified-old-setup.exe";
    }
}

sealed class FakeProbe : ISupervisorHealthProbe
{
    public StableUpdateRollbackJournal.HealthEvidence Evidence { get; set; } =
        new(false, false, false, false);
    public bool Safe { get; set; }
    public string ObservedSessionFingerprint { get; set; } = new string('d', 64);
    public string ObservedApplicationSha256 { get; set; } = new string('2', 64);
    public string ObservedNativeHostSha256 { get; set; } = new string('4', 64);
    public string ObservedRendererSha256 { get; set; } = new string('6', 64);
    public string ObservedSupervisorSha256 { get; set; } = new string('8', 64);

    public Task<StableUpdateRollbackJournal.HealthEvidence> CheckAsync(
        Version expected, string originalSessionFingerprint,
        string expectedApplicationSha256, string expectedNativeHostSha256,
        string expectedRendererSha256, string expectedSupervisorSha256,
        CancellationToken cancellationToken) =>
        Task.FromResult(Evidence with
        {
            ExactSignedNewExe = Evidence.ExactSignedNewExe &&
                string.Equals(ObservedSupervisorSha256, expectedSupervisorSha256,
                    StringComparison.Ordinal) &&
                string.Equals(ObservedApplicationSha256, expectedApplicationSha256,
                    StringComparison.Ordinal) &&
                string.Equals(ObservedNativeHostSha256, expectedNativeHostSha256,
                    StringComparison.Ordinal) &&
                string.Equals(ObservedRendererSha256, expectedRendererSha256,
                    StringComparison.Ordinal),
            SessionPreserved = Evidence.SessionPreserved &&
                string.Equals(ObservedSessionFingerprint, originalSessionFingerprint,
                    StringComparison.Ordinal)
        });

    public bool SafeForRollback() => Safe;
}

sealed class FakeLauncher : ISupervisorRollbackLauncher
{
    public int LaunchCount { get; private set; }
    public bool ThrowOnLaunch { get; set; }
    public void Launch(string signedPreviousInstaller)
    {
        LaunchCount++;
        if (ThrowOnLaunch) throw new IOException("INNO_ROLLBACK_REFUSED");
    }
}
