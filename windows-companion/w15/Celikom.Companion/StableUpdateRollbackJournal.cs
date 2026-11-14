using System.Security.Cryptography;
using System.Text.Json;

namespace Celikom.Companion;

/// <summary>
/// W109 durable, user-scoped record of an in-place stable update.
/// No installer is executed by this class. Production callers must use
/// PrepareSigned, which checks both signed packages before retaining a
/// byte-identical previous installer. This is groundwork for the independent
/// supervisor, not a substitute for one.
/// </summary>
public static class StableUpdateRollbackJournal
{
    public enum Phase
    {
        Prepared, InstallerStarted, NewAppObserved, Healthy,
        RollbackNeeded, RollbackStarted, Restored, ManualRecovery
    }

    public enum Decision { Wait, AcceptNewVersion, RequestRollback, ManualRecovery }

    public sealed record HealthEvidence(
        bool ExactSignedNewExe, bool BridgeResponds,
        bool SessionPreserved, bool NativeIntegrationConsistent);

    public sealed record Record(
        int Schema, Guid Id, Phase State, string PreviousVersion,
        string TargetVersion, string PreviousSha256, string TargetSha256,
        string SignerSha256, long PreviousSize, long PreviousSequence,
        long TargetSequence, long DeadlineUnix, int RollbackAttempts,
        bool ExpectedSession, bool NativeWasInstalled);

    private const string TicketName = "stable-update-rollback.dpapi";
    private const string PreviousName = "previous-signed-setup.exe";
    private static readonly byte[] Purpose =
        System.Text.Encoding.UTF8.GetBytes("CELIKOM.Windows.StableRollback.W109.v1");

    /// <summary>
    /// Validates both signed installers before writing a transaction.
    /// A prior installed app is NOT automatically a trusted rollback package:
    /// retain a separate verified signed installer with the correct version.
    /// </summary>
    public static Record PrepareSigned(
        string privateRoot, StableUpdateManifestVerifier.VerifiedRelease previous,
        string previousInstaller,
        StableUpdateManifestVerifier.VerifiedRelease target, string targetInstaller,
        string pinnedSignerSha256, Version runningVersion,
        DateTimeOffset now, bool hasSession, bool nativeWasInstalled)
    {
        return PrepareCore(privateRoot, previous, previousInstaller, target,
            targetInstaller, pinnedSignerSha256, runningVersion, now,
            hasSession, nativeWasInstalled,
            StableUpdatePackageStager.VerifyInstaller);
    }

    // CI-only verifier seam; real entry point above always calls the full
    // SHA256 + Authenticode + signer pin + PE identity verifier.
    internal static Record PrepareCore(
        string privateRoot, StableUpdateManifestVerifier.VerifiedRelease previous,
        string previousInstaller,
        StableUpdateManifestVerifier.VerifiedRelease target, string targetInstaller,
        string pinnedSignerSha256, Version runningVersion,
        DateTimeOffset now, bool hasSession, bool nativeWasInstalled,
        Action<string, StableUpdateManifestVerifier.VerifiedRelease, string> verify)
    {
        RequireWindows();
        if (previous.Version != runningVersion ||
            target.Version <= previous.Version ||
            target.Sequence <= previous.Sequence ||
            target.RollbackFrom != null || previous.RollbackFrom != null ||
            !ValidSha(previous.Sha256) || !ValidSha(target.Sha256) ||
            !ValidSha(pinnedSignerSha256) ||
            previous.PackageSize is < 10_000 or > 125_000_000 ||
            now > target.ExpiresAt)
            throw new IOException("STABLE_ROLLBACK_PLAN_INVALID");
        verify(previousInstaller, previous, pinnedSignerSha256);
        verify(targetInstaller, target, pinnedSignerSha256);
        var root = FullRoot(privateRoot);
        Directory.CreateDirectory(root);
        using var exclusive = AcquireLock(root);
        if (File.Exists(JournalPath(root)))
        {
            // A completed, separately proven transaction may be superseded
            // by the next signed upgrade. Never discard a live/failed
            // rollback ticket, or silently overwrite an unreadable record.
            var previousTransaction = ReadRecord(root);
            if (previousTransaction.State is not (Phase.Healthy or Phase.Restored))
                throw new IOException("STABLE_ROLLBACK_PENDING_EXISTS");
        }

        var identifier = Guid.NewGuid();
        var snapshot = Path.Combine(root, identifier.ToString("N"));
        Directory.CreateDirectory(snapshot);
        var copied = Path.Combine(snapshot, PreviousName);
        try
        {
            using (var source = new FileStream(previousInstaller, FileMode.Open,
                FileAccess.Read, FileShare.Read, 65536, FileOptions.SequentialScan))
            using (var output = new FileStream(copied, FileMode.CreateNew,
                FileAccess.Write, FileShare.None, 65536, FileOptions.WriteThrough))
            {
                source.CopyTo(output);
                output.Flush(flushToDisk: true);
            }
            verify(copied, previous, pinnedSignerSha256);
            var record = new Record(1, identifier, Phase.Prepared,
                previous.Version.ToString(4), target.Version.ToString(4),
                previous.Sha256, target.Sha256, pinnedSignerSha256,
                previous.PackageSize, previous.Sequence, target.Sequence,
                now.AddMinutes(10).ToUnixTimeSeconds(), 0,
                hasSession, nativeWasInstalled);
            WriteRecord(root, record);
            return record;
        }
        catch
        {
            try { Directory.Delete(snapshot, recursive: true); } catch { }
            throw;
        }
    }

    public static Record Read(string privateRoot)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        return ReadRecord(root);
    }

    /// <summary>
    /// Every phase change is an atomic DPAPI-protected journal rewrite.
    /// Unexpected transition, replayed phase or a second rollback is denied.
    /// </summary>
    public static Record Advance(string privateRoot, Guid expectedId,
        Phase expectedPhase, Phase nextPhase)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var current = ReadRecord(root);
        if (current.Id != expectedId || current.State != expectedPhase ||
            !Allowed(expectedPhase, nextPhase))
            throw new IOException("STABLE_ROLLBACK_TRANSITION_DENIED");
        var attempts = current.RollbackAttempts +
            (nextPhase == Phase.RollbackStarted ? 1 : 0);
        if (attempts > 1)
            throw new IOException("STABLE_ROLLBACK_ATTEMPT_LIMIT");
        var next = current with { State = nextPhase, RollbackAttempts = attempts };
        WriteRecord(root, next);
        return next;
    }

    /// <summary>Health success is NOT an arbitrary phase transition.</summary>
    public static Record ConfirmNewAppHealthy(string privateRoot, Guid id,
        HealthEvidence evidence, DateTimeOffset now)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var state = ReadRecord(root);
        if (state.Id != id || state.State != Phase.NewAppObserved ||
            Decide(state, evidence, now) != Decision.AcceptNewVersion)
            throw new IOException("STABLE_ROLLBACK_HEALTH_NOT_PROVEN");
        var next = state with { State = Phase.Healthy };
        WriteRecord(root, next);
        return next;
    }

    /// <summary>Restoring the old installer is not proof it booted correctly.</summary>
    public static Record ConfirmPreviousRestored(string privateRoot, Guid id,
        HealthEvidence evidence)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var state = ReadRecord(root);
        if (state.Id != id || state.State != Phase.RollbackStarted ||
            state.RollbackAttempts != 1 ||
            !evidence.ExactSignedNewExe || !evidence.BridgeResponds ||
            (state.ExpectedSession && !evidence.SessionPreserved) ||
            (state.NativeWasInstalled && !evidence.NativeIntegrationConsistent))
            throw new IOException("STABLE_ROLLBACK_RESTORE_NOT_PROVEN");
        var next = state with { State = Phase.Restored };
        WriteRecord(root, next);
        return next;
    }

    public static Decision Decide(Record record, HealthEvidence evidence,
        DateTimeOffset now)
    {
        if (record.Schema != 1 || record.Id == Guid.Empty ||
            record.RollbackAttempts is < 0 or > 1)
            return Decision.ManualRecovery;
        if (record.State is Phase.Healthy or Phase.Restored)
            return Decision.Wait;
        if (record.State is Phase.RollbackStarted or Phase.ManualRecovery)
            return Decision.ManualRecovery; // no automatic loop
        if (record.State == Phase.RollbackNeeded)
            return record.RollbackAttempts == 0
                ? Decision.RequestRollback : Decision.ManualRecovery;
        if (record.State == Phase.Prepared) return Decision.Wait;
        var allHealthy = evidence.ExactSignedNewExe && evidence.BridgeResponds &&
            (!record.ExpectedSession || evidence.SessionPreserved) &&
            (!record.NativeWasInstalled || evidence.NativeIntegrationConsistent);
        // Never certify an update from an installer launch alone: a separate
        // new-process/version observation must have been recorded first.
        if (record.State == Phase.NewAppObserved && allHealthy)
            return Decision.AcceptNewVersion;
        return now.ToUnixTimeSeconds() >= record.DeadlineUnix
            ? Decision.RequestRollback : Decision.Wait;
    }

    /// <summary>
    /// Re-verify the locally cached LAST KNOWN GOOD signed installer at the
    /// moment an eventual supervisor requests rollback. It must not execute
    /// stale, substituted, unsigned or wrong-version bytes.
    /// </summary>
    public static string VerifiedPreviousInstaller(
        string privateRoot, Guid transaction, string pinnedSignerSha256)
    {
        return VerifiedPreviousInstallerCore(privateRoot, transaction,
            pinnedSignerSha256, StableUpdatePackageStager.VerifyInstaller);
    }

    internal static string VerifiedPreviousInstallerCore(
        string privateRoot, Guid transaction, string pinnedSignerSha256,
        Action<string, StableUpdateManifestVerifier.VerifiedRelease, string> verify)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var state = ReadRecord(root);
        if (state.Id != transaction || state.State != Phase.RollbackNeeded ||
            state.RollbackAttempts != 0 ||
            !string.Equals(state.SignerSha256, pinnedSignerSha256,
                StringComparison.OrdinalIgnoreCase) ||
            !Version.TryParse(state.PreviousVersion, out var version) ||
            !ValidSha(state.PreviousSha256))
            throw new IOException("STABLE_ROLLBACK_NOT_AUTHORIZED");
        var previous = Path.Combine(root, state.Id.ToString("N"), PreviousName);
        if (!File.Exists(previous) ||
            new FileInfo(previous).Attributes.HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("STABLE_ROLLBACK_IMAGE_MISSING");
        // All fields here came from a previously signature-checked release and
        // a user-scoped DPAPI-protected record. Recheck bytes and cert on use.
        var release = new StableUpdateManifestVerifier.VerifiedRelease(
            version, state.PreviousSequence,
            new Uri("https://celikom.invalid/CELIKOM/Windows/Updates/stable/" +
                    version.ToString(3) + "/previous.exe"),
            state.PreviousSize, state.PreviousSha256,
            DateTimeOffset.MaxValue, false, "");
        verify(previous, release, pinnedSignerSha256);
        return previous;
    }

    private static bool Allowed(Phase from, Phase to) => (from, to) switch
    {
        (Phase.Prepared, Phase.InstallerStarted) => true,
        (Phase.Prepared, Phase.ManualRecovery) => true,
        (Phase.InstallerStarted, Phase.NewAppObserved) => true,
        (Phase.InstallerStarted, Phase.RollbackNeeded) => true,
        (Phase.NewAppObserved, Phase.RollbackNeeded) => true,
        (Phase.RollbackNeeded, Phase.RollbackStarted) => true,
        (Phase.RollbackStarted, Phase.ManualRecovery) => true,
        _ => false
    };

    private static void RequireWindows()
    {
        if (!OperatingSystem.IsWindows())
            throw new IOException("STABLE_ROLLBACK_WINDOWS_ONLY");
    }

    private static bool ValidSha(string? hash) =>
        hash is { Length: 64 } &&
        hash.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');

    private static string FullRoot(string root)
    {
        if (string.IsNullOrWhiteSpace(root))
            throw new IOException("STABLE_ROLLBACK_ROOT_INVALID");
        var path = Path.GetFullPath(root);
        if (!Path.IsPathFullyQualified(path) ||
            Directory.Exists(path) &&
            (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("STABLE_ROLLBACK_ROOT_INVALID");
        return path;
    }

    private static string JournalPath(string root) => Path.Combine(root, TicketName);

    private static FileStream AcquireLock(string root)
    {
        Directory.CreateDirectory(root);
        return new FileStream(Path.Combine(root, ".stable-update-lock"),
            FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }

    private static Record ReadRecord(string root)
    {
        try
        {
            var file = JournalPath(root);
            if (!File.Exists(file) || new FileInfo(file).Length is < 32 or > 8192)
                throw new IOException("STABLE_ROLLBACK_RECORD_MISSING");
            var plain = ProtectedData.Unprotect(File.ReadAllBytes(file), Purpose,
                DataProtectionScope.CurrentUser);
            var record = JsonSerializer.Deserialize<Record>(plain);
            CryptographicOperations.ZeroMemory(plain);
            if (record is null || record.Schema != 1 || record.Id == Guid.Empty ||
                !ValidSha(record.PreviousSha256) || !ValidSha(record.TargetSha256) ||
                !ValidSha(record.SignerSha256) ||
                !Version.TryParse(record.PreviousVersion, out var previous) ||
                !Version.TryParse(record.TargetVersion, out var target) ||
                previous >= target || record.PreviousSequence >= record.TargetSequence ||
                record.RollbackAttempts is < 0 or > 1 ||
                record.PreviousSize is < 10_000 or > 125_000_000 ||
                record.DeadlineUnix <= 0 ||
                !Enum.IsDefined(record.State))
                throw new IOException("STABLE_ROLLBACK_RECORD_INVALID");
            return record;
        }
        catch (Exception e) when (e is CryptographicException or JsonException)
        {
            throw new IOException("STABLE_ROLLBACK_RECORD_UNTRUSTED", e);
        }
    }

    private static void WriteRecord(string root, Record record)
    {
        var data = JsonSerializer.SerializeToUtf8Bytes(record);
        var protectedBytes = ProtectedData.Protect(data, Purpose,
            DataProtectionScope.CurrentUser);
        CryptographicOperations.ZeroMemory(data);
        var temp = Path.Combine(root, ".stable-journal-" + Guid.NewGuid().ToString("N"));
        try
        {
            using (var file = new FileStream(temp, FileMode.CreateNew,
                FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                file.Write(protectedBytes);
                file.Flush(flushToDisk: true);
            }
            File.Move(temp, JournalPath(root), overwrite: true);
        }
        finally { try { if (File.Exists(temp)) File.Delete(temp); } catch { } }
    }
}
