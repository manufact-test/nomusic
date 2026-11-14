using Celikom.Companion;

namespace Celikom.UpdateSupervisor;

/// <summary>
/// W110 crash-independent coordinator. Production release pin must be embedded
/// in a signed binary before the outer executable can start this engine.
/// The GUI never supplies health results, signer keys or rollback paths.
/// </summary>
public sealed class UpdateSupervisorEngine(
    Guid expectedTransaction, ISupervisorJournal journal,
    ISupervisorHealthProbe probe, ISupervisorRollbackLauncher launcher)
{
    public enum Step { Waiting, NewApplicationSeen, NewApplicationHealthy,
        RollbackQueued, RollbackLaunched, PreviousVersionRestored,
        ManualRecovery, Completed }

    public async Task<Step> TickAsync(DateTimeOffset now, CancellationToken ct = default)
    {
        var state = journal.Read();
        if (state.Id != expectedTransaction)
            throw new IOException("SUPERVISOR_TRANSACTION_MISMATCH");
        if (state.Schema != 2)
            throw new IOException("SUPERVISOR_TRANSACTION_SCHEMA_UNSUPPORTED");
        if (!ValidSha(state.TargetApplicationSha256) ||
            !ValidSha(state.TargetNativeHostSha256) ||
            !ValidSha(state.TargetRendererSha256) ||
            !ValidSha(state.PreviousApplicationSha256) ||
            !ValidSha(state.PreviousNativeHostSha256) ||
            !ValidSha(state.PreviousRendererSha256) ||
            !ValidSha(state.TargetSupervisorSha256) ||
            !ValidSha(state.PreviousSupervisorSha256))
            throw new IOException("SUPERVISOR_PAYLOAD_WITNESS_MISSING");
        if (state.ExpectedSession && (state.SessionIdentitySha256 is not { Length: 64 } ||
            state.SessionIdentitySha256.Any(c => c is not
                (>= '0' and <= '9' or >= 'a' and <= 'f'))))
            throw new IOException("SUPERVISOR_SESSION_WITNESS_MISSING");

        switch (state.State)
        {
            case StableUpdateRollbackJournal.Phase.Healthy:
            case StableUpdateRollbackJournal.Phase.Restored:
                return Step.Completed;
            case StableUpdateRollbackJournal.Phase.ManualRecovery:
                return Step.ManualRecovery;
            case StableUpdateRollbackJournal.Phase.Prepared:
                return Step.Waiting;
            case StableUpdateRollbackJournal.Phase.InstallerStarted:
            {
                var health = await probe.CheckAsync(Version.Parse(state.TargetVersion),
                    state.SessionIdentitySha256, state.TargetApplicationSha256,
                    state.TargetNativeHostSha256, state.TargetRendererSha256,
                    state.TargetSupervisorSha256, ct);
                if (health.ExactSignedNewExe)
                {
                    journal.Advance(state.State, StableUpdateRollbackJournal.Phase.NewAppObserved);
                    return Step.NewApplicationSeen;
                }
                if (now.ToUnixTimeSeconds() >= state.DeadlineUnix)
                {
                    journal.Advance(state.State, StableUpdateRollbackJournal.Phase.RollbackNeeded);
                    return Step.RollbackQueued;
                }
                return Step.Waiting;
            }
            case StableUpdateRollbackJournal.Phase.NewAppObserved:
            {
                var health = await probe.CheckAsync(Version.Parse(state.TargetVersion),
                    state.SessionIdentitySha256, state.TargetApplicationSha256,
                    state.TargetNativeHostSha256, state.TargetRendererSha256,
                    state.TargetSupervisorSha256, ct);
                var decision = StableUpdateRollbackJournal.Decide(state, health, now);
                if (decision == StableUpdateRollbackJournal.Decision.AcceptNewVersion)
                {
                    journal.ConfirmNewHealthy(health, now);
                    return Step.NewApplicationHealthy;
                }
                if (decision == StableUpdateRollbackJournal.Decision.RequestRollback)
                {
                    journal.Advance(state.State, StableUpdateRollbackJournal.Phase.RollbackNeeded);
                    return Step.RollbackQueued;
                }
                return Step.Waiting;
            }
            case StableUpdateRollbackJournal.Phase.RollbackNeeded:
            {
                // If Yandex or CELIKOM is running, NEVER interrupt music or
                // terminate applications to force the version downgrade.
                if (!probe.SafeForRollback())
                {
                    if (now.ToUnixTimeSeconds() >= state.DeadlineUnix + 15 * 60L)
                    {
                        journal.Advance(state.State, StableUpdateRollbackJournal.Phase.ManualRecovery);
                        return Step.ManualRecovery;
                    }
                    return Step.Waiting;
                }

                // Re-check signed cached EXE immediately before arming one-shot
                // recovery. A missing/bad package is a hard stop, not a
                // reason to download/execute untrusted code.
                string previousInstaller;
                try { previousInstaller = journal.VerifiedPreviousInstaller(); }
                catch (Exception e) when (e is IOException or UnauthorizedAccessException or
                    System.Security.Cryptography.CryptographicException)
                {
                    journal.Advance(state.State, StableUpdateRollbackJournal.Phase.ManualRecovery);
                    return Step.ManualRecovery;
                }
                if (!probe.SafeForRollback())
                    return Step.Waiting;

                // Persist the attempt BEFORE invoking the installer. A crash of
                // this supervisor can never spawn a second rollback installer.
                journal.BeginRollback(now);
                try
                {
                    launcher.Launch(previousInstaller);
                    return Step.RollbackLaunched;
                }
                catch (Exception e) when (e is IOException or UnauthorizedAccessException or
                    System.ComponentModel.Win32Exception or InvalidOperationException)
                {
                    journal.Advance(StableUpdateRollbackJournal.Phase.RollbackStarted,
                        StableUpdateRollbackJournal.Phase.ManualRecovery);
                    return Step.ManualRecovery;
                }
            }
            case StableUpdateRollbackJournal.Phase.RollbackStarted:
            {
                var health = await probe.CheckAsync(Version.Parse(state.PreviousVersion),
                    state.SessionIdentitySha256, state.PreviousApplicationSha256,
                    state.PreviousNativeHostSha256, state.PreviousRendererSha256,
                    state.PreviousSupervisorSha256, ct);
                if (health.ExactSignedNewExe && health.BridgeResponds &&
                    (!state.ExpectedSession || health.SessionPreserved) &&
                    (!state.NativeWasInstalled || health.NativeIntegrationConsistent))
                {
                    journal.ConfirmPreviousHealthy(health);
                    return Step.PreviousVersionRestored;
                }
                if (now.ToUnixTimeSeconds() >= state.DeadlineUnix)
                {
                    journal.Advance(state.State, StableUpdateRollbackJournal.Phase.ManualRecovery);
                    return Step.ManualRecovery;
                }
                return Step.Waiting;
            }
            default: return Step.ManualRecovery;
        }
    }

    private static bool ValidSha(string? value) =>
        value is { Length: 64 } &&
        value.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');
}

public interface ISupervisorJournal
{
    StableUpdateRollbackJournal.Record Read();
    void Advance(StableUpdateRollbackJournal.Phase expected,
        StableUpdateRollbackJournal.Phase next);
    void BeginRollback(DateTimeOffset now);
    void ConfirmNewHealthy(StableUpdateRollbackJournal.HealthEvidence evidence,
        DateTimeOffset now);
    void ConfirmPreviousHealthy(StableUpdateRollbackJournal.HealthEvidence evidence);
    string VerifiedPreviousInstaller();
}

public interface ISupervisorHealthProbe
{
    Task<StableUpdateRollbackJournal.HealthEvidence> CheckAsync(
        Version expected, string originalSessionFingerprint,
        string expectedApplicationSha256, string expectedNativeHostSha256,
        string expectedRendererSha256, string expectedSupervisorSha256,
        CancellationToken cancellationToken);
    bool SafeForRollback();
}

public interface ISupervisorRollbackLauncher
{
    void Launch(string signedPreviousInstaller);
}

public sealed class DurableSupervisorJournal(
    string privateRoot, Guid expectedId, string pinnedSignerSha256)
    : ISupervisorJournal
{
    private static bool ValidSha(string? value) =>
        value is { Length: 64 } &&
        value.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');

    public StableUpdateRollbackJournal.Record Read() =>
        StableUpdateRollbackJournal.Read(privateRoot);

    public void Advance(StableUpdateRollbackJournal.Phase expected,
        StableUpdateRollbackJournal.Phase next) =>
        StableUpdateRollbackJournal.Advance(privateRoot, expectedId, expected, next);

    public void BeginRollback(DateTimeOffset now) =>
        StableUpdateRollbackJournal.BeginRollback(privateRoot, expectedId, now);

    public void ConfirmNewHealthy(StableUpdateRollbackJournal.HealthEvidence evidence,
        DateTimeOffset now) =>
        StableUpdateRollbackJournal.ConfirmNewAppHealthy(
            privateRoot, expectedId, evidence, now);

    public void ConfirmPreviousHealthy(StableUpdateRollbackJournal.HealthEvidence evidence) =>
        StableUpdateRollbackJournal.ConfirmPreviousRestored(
            privateRoot, expectedId, evidence);

    public string VerifiedPreviousInstaller() =>
        StableUpdateRollbackJournal.VerifiedPreviousInstaller(
            privateRoot, expectedId, pinnedSignerSha256);
}
