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
        RollbackNeeded, RollbackStarted, Restored, ManualRecovery, Seeded
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
        bool ExpectedSession, bool NativeWasInstalled,
        string SessionIdentitySha256 = "",
        string PreviousApplicationSha256 = "", string TargetApplicationSha256 = "",
        string PreviousNativeHostSha256 = "", string TargetNativeHostSha256 = "",
        string PreviousRendererSha256 = "", string TargetRendererSha256 = "",
        string PreviousSupervisorSha256 = "", string TargetSupervisorSha256 = "",
        long TargetSize = 0);

    private const string TicketName = "stable-update-rollback.dpapi";
    public static string DefaultPrivateRoot => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows", "StableRollback");
    private const string PreviousName = "previous-signed-setup.exe";
    private const string TargetName = "target-signed-setup.exe";
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
        // Capture the EXISTING account/installation identity before the
        // installer can replace any files. Never create a new DPAPI session.
        var identity = hasSession
            ? SignedUpdateSessionIdentity.ReadExistingFingerprint()
            : "";
        if (hasSession && identity is null)
            throw new IOException("STABLE_ROLLBACK_EXISTING_SESSION_UNREADABLE");
        return PrepareCore(privateRoot, previous, previousInstaller, target,
            targetInstaller, pinnedSignerSha256, runningVersion, now,
            hasSession, nativeWasInstalled,
            StableUpdatePackageStager.VerifyInstaller, identity ?? "");
    }

    // CI-only verifier seam; real entry point above always calls the full
    // SHA256 + Authenticode + signer pin + PE identity verifier.
    internal static Record PrepareCore(
        string privateRoot, StableUpdateManifestVerifier.VerifiedRelease previous,
        string previousInstaller,
        StableUpdateManifestVerifier.VerifiedRelease target, string targetInstaller,
        string pinnedSignerSha256, Version runningVersion,
        DateTimeOffset now, bool hasSession, bool nativeWasInstalled,
        Action<string, StableUpdateManifestVerifier.VerifiedRelease, string> verify,
        string sessionIdentitySha256 = "")
    {
        RequireWindows();
        // When there was an existing login, its identity witness is
        // mandatory even for synthetic CI transactions. No silent bypass.
        if (hasSession && !ValidSha(sessionIdentitySha256) ||
            !hasSession && sessionIdentitySha256.Length != 0)
            throw new IOException("STABLE_ROLLBACK_SESSION_FINGERPRINT_INVALID");
        if (previous.Version != runningVersion ||
            target.Version <= previous.Version ||
            target.Sequence <= previous.Sequence ||
            target.RollbackFrom != null || previous.RollbackFrom != null ||
            !ValidSha(previous.Sha256) || !ValidSha(target.Sha256) ||
            !ValidSha(pinnedSignerSha256) ||
            !ValidSha(previous.ApplicationSha256) || !ValidSha(target.ApplicationSha256) ||
            !ValidSha(previous.NativeHostSha256) || !ValidSha(target.NativeHostSha256) ||
            !ValidSha(previous.RendererSha256) || !ValidSha(target.RendererSha256) ||
            !ValidSha(previous.SupervisorSha256) || !ValidSha(target.SupervisorSha256) ||
            previous.PackageSize is < 10_000 or > 125_000_000 ||
            target.PackageSize is < 10_000 or > 125_000_000 ||
            previous.Sequence <= 0 || target.Sequence <= 0 ||
            now > target.ExpiresAt)
            throw new IOException("STABLE_ROLLBACK_PLAN_INVALID");
        verify(previousInstaller, previous, pinnedSignerSha256);
        verify(targetInstaller, target, pinnedSignerSha256);
        var root = FullRoot(privateRoot);
        Directory.CreateDirectory(root);
        using var exclusive = AcquireLock(root);
        Guid? supersededSnapshotId = null;
        if (File.Exists(JournalPath(root)))
        {
            // A completed, separately proven transaction may be superseded
            // by the next signed upgrade. Never discard a live/failed
            // rollback ticket, or silently overwrite an unreadable record.
            var previousTransaction = ReadRecord(root);
            if (previousTransaction.State is not (Phase.Seeded or Phase.Healthy or Phase.Restored))
                throw new IOException("STABLE_ROLLBACK_PENDING_EXISTS");
            supersededSnapshotId = previousTransaction.Id;
        }

        var identifier = Guid.NewGuid();
        var snapshot = Path.Combine(root, identifier.ToString("N"));
        Directory.CreateDirectory(snapshot);
        var copiedPrevious = Path.Combine(snapshot, PreviousName);
        var copiedTarget = Path.Combine(snapshot, TargetName);
        try
        {
            CopyVerifiedImage(previousInstaller, copiedPrevious, previous.PackageSize);
            CopyVerifiedImage(targetInstaller, copiedTarget, target.PackageSize);
            verify(copiedPrevious, previous, pinnedSignerSha256);
            verify(copiedTarget, target, pinnedSignerSha256);
            var record = new Record(2, identifier, Phase.Prepared,
                previous.Version.ToString(4), target.Version.ToString(4),
                previous.Sha256, target.Sha256, pinnedSignerSha256,
                previous.PackageSize, previous.Sequence, target.Sequence,
                now.AddMinutes(10).ToUnixTimeSeconds(), 0,
                hasSession, nativeWasInstalled, sessionIdentitySha256,
                previous.ApplicationSha256, target.ApplicationSha256,
                previous.NativeHostSha256, target.NativeHostSha256,
                previous.RendererSha256, target.RendererSha256,
                previous.SupervisorSha256, target.SupervisorSha256,
                TargetSize: target.PackageSize);
            WriteRecord(root, record);
            // The new transaction now owns a byte-identical previous package
            // and a verified target package. Only after its DPAPI journal is
            // durable may the superseded snapshot be discarded.
            if (supersededSnapshotId is Guid oldId && oldId != identifier)
            {
                var oldSnapshot = Path.Combine(root, oldId.ToString("N"));
                try
                {
                    if (Directory.Exists(oldSnapshot) &&
                        (File.GetAttributes(oldSnapshot) & FileAttributes.ReparsePoint) == 0)
                        Directory.Delete(oldSnapshot, recursive: true);
                }
                catch { /* The new journal and snapshot are already complete. */ }
            }
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
    /// Seeds the first signed rollback package for this exact installed build.
    /// The signed immutable manifest, Authenticode pin and installed payload
    /// hashes must all agree. This does not run an installer or touch Yandex.
    /// </summary>
    public static Record SeedInitialLastKnownGoodSigned(
        string privateRoot, StableUpdateManifestVerifier.VerifiedRelease release,
        string signedInstaller, string pinnedSignerSha256,
        string installedApplicationPath, string installedNativeHostPath,
        string installedRendererPath, string installedSupervisorPath) =>
        SeedInitialLastKnownGoodCore(privateRoot, release, signedInstaller,
            pinnedSignerSha256, AppUpdateManager.RunningVersion,
            installedApplicationPath, installedNativeHostPath,
            installedRendererPath, installedSupervisorPath, DateTimeOffset.UtcNow,
            StableUpdatePackageStager.VerifyInstaller,
            (path, hash) => StableUpdatePayloadVerifier.MatchesFile(path, hash));

    internal static Record SeedInitialLastKnownGoodCore(
        string privateRoot, StableUpdateManifestVerifier.VerifiedRelease release,
        string signedInstaller, string pinnedSignerSha256, Version runningVersion,
        string installedApplicationPath, string installedNativeHostPath,
        string installedRendererPath, string installedSupervisorPath,
        DateTimeOffset now,
        Action<string, StableUpdateManifestVerifier.VerifiedRelease, string> verify,
        Func<string, string, bool> payloadMatches)
    {
        RequireWindows();
        if (release is null || release.Version != runningVersion ||
            release.Sequence <= 0 || release.RollbackFrom != null ||
            release.PackageSize is < 10_000 or > 125_000_000 ||
            !ValidSha(release.Sha256) || !ValidSha(pinnedSignerSha256) ||
            !ValidSha(release.ApplicationSha256) ||
            !ValidSha(release.NativeHostSha256) ||
            !ValidSha(release.RendererSha256) ||
            !ValidSha(release.SupervisorSha256) ||
            release.PackageUri is null ||
            release.PackageUri.Scheme != Uri.UriSchemeHttps ||
            release.PackageUri.UserInfo.Length != 0 ||
            release.PackageUri.Query.Length != 0 ||
            release.PackageUri.Fragment.Length != 0 ||
            !release.PackageUri.AbsolutePath.StartsWith(
                "/CELIKOM/Windows/Updates/stable/" + release.Version.ToString(3) + "/",
                StringComparison.Ordinal) ||
            !release.PackageUri.AbsolutePath.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_PLAN_INVALID");

        verify(signedInstaller, release, pinnedSignerSha256);
        if (!payloadMatches(installedApplicationPath, release.ApplicationSha256) ||
            !payloadMatches(installedNativeHostPath, release.NativeHostSha256) ||
            !payloadMatches(installedRendererPath, release.RendererSha256) ||
            !payloadMatches(installedSupervisorPath, release.SupervisorSha256))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_PAYLOAD_MISMATCH");

        var root = FullRoot(privateRoot);
        Directory.CreateDirectory(root);
        using var exclusive = AcquireLock(root);
        if (File.Exists(JournalPath(root)))
            throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_ALREADY_INITIALIZED");

        var identifier = Guid.NewGuid();
        var snapshot = Path.Combine(root, identifier.ToString("N"));
        Directory.CreateDirectory(snapshot);
        var copiedTarget = Path.Combine(snapshot, TargetName);
        try
        {
            CopyVerifiedImage(signedInstaller, copiedTarget, release.PackageSize);
            verify(copiedTarget, release, pinnedSignerSha256);
            if (!payloadMatches(installedApplicationPath, release.ApplicationSha256) ||
                !payloadMatches(installedNativeHostPath, release.NativeHostSha256) ||
                !payloadMatches(installedRendererPath, release.RendererSha256) ||
                !payloadMatches(installedSupervisorPath, release.SupervisorSha256))
                throw new IOException("STABLE_ROLLBACK_BOOTSTRAP_PAYLOAD_CHANGED");

            // Seeded is deliberately not an update transaction. Previous*
            // fields are a strict 0.0.0.0/sequence-0 sentinel; the target image
            // is the exact currently installed signed release.
            var record = new Record(2, identifier, Phase.Seeded,
                "0.0.0.0", release.Version.ToString(4),
                release.Sha256, release.Sha256, pinnedSignerSha256,
                release.PackageSize, 0, release.Sequence,
                now.AddYears(10).ToUnixTimeSeconds(), 0,
                false, false, "",
                release.ApplicationSha256, release.ApplicationSha256,
                release.NativeHostSha256, release.NativeHostSha256,
                release.RendererSha256, release.RendererSha256,
                release.SupervisorSha256, release.SupervisorSha256,
                TargetSize: release.PackageSize);
            WriteRecord(root, record);
            return record;
        }
        catch
        {
            try { Directory.Delete(snapshot, recursive: true); } catch { }
            throw;
        }
    }

    public sealed record CachedSignedPackage(
        string InstallerPath, StableUpdateManifestVerifier.VerifiedRelease Release);

    /// <summary>
    /// Returns the currently accepted signed installer for the next update's
    /// rollback base. Healthy means the target is current; Restored means the
    /// previous package was successfully restored. In-progress or failed
    /// transactions never seed a future rollback.
    /// </summary>
    public static CachedSignedPackage GetLastKnownGood(
        string privateRoot, string pinnedSignerSha256) =>
        GetLastKnownGoodCore(privateRoot, pinnedSignerSha256,
            StableUpdatePackageStager.VerifyInstaller);

    internal static CachedSignedPackage GetLastKnownGoodCore(
        string privateRoot, string pinnedSignerSha256,
        Action<string, StableUpdateManifestVerifier.VerifiedRelease, string> verify)
    {
        RequireWindows();
        if (!ValidSha(pinnedSignerSha256))
            throw new IOException("STABLE_ROLLBACK_SIGNER_UNPINNED");
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var state = ReadRecord(root);
        if (state.Schema != 2 || state.RollbackAttempts is < 0 or > 1 ||
            (state.State is Phase.Seeded or Phase.Healthy) && state.RollbackAttempts != 0 ||
            state.State == Phase.Restored && state.RollbackAttempts != 1 ||
            !string.Equals(state.SignerSha256, pinnedSignerSha256,
                StringComparison.OrdinalIgnoreCase) ||
            state.State is not (Phase.Seeded or Phase.Healthy or Phase.Restored))
            throw new IOException("STABLE_ROLLBACK_LAST_KNOWN_GOOD_NOT_READY");

        var useTarget = state.State is Phase.Seeded or Phase.Healthy;
        var versionText = useTarget ? state.TargetVersion : state.PreviousVersion;
        var sequence = useTarget ? state.TargetSequence : state.PreviousSequence;
        var packageSize = useTarget ? state.TargetSize : state.PreviousSize;
        var packageHash = useTarget ? state.TargetSha256 : state.PreviousSha256;
        var applicationHash = useTarget ? state.TargetApplicationSha256 : state.PreviousApplicationSha256;
        var nativeHostHash = useTarget ? state.TargetNativeHostSha256 : state.PreviousNativeHostSha256;
        var rendererHash = useTarget ? state.TargetRendererSha256 : state.PreviousRendererSha256;
        var supervisorHash = useTarget ? state.TargetSupervisorSha256 : state.PreviousSupervisorSha256;
        if (!Version.TryParse(versionText, out var version) ||
            sequence <= 0 || packageSize is < 10_000 or > 125_000_000 ||
            !ValidSha(packageHash) || !ValidSha(applicationHash) ||
            !ValidSha(nativeHostHash) || !ValidSha(rendererHash) ||
            !ValidSha(supervisorHash))
            throw new IOException("STABLE_ROLLBACK_LAST_KNOWN_GOOD_IDENTITY_INVALID");

        var packageName = useTarget ? TargetName : PreviousName;
        var installer = Path.Combine(root, state.Id.ToString("N"), packageName);
        var info = new FileInfo(installer);
        if (!info.Exists || info.Attributes.HasFlag(FileAttributes.ReparsePoint) ||
            info.Length != packageSize)
            throw new IOException("STABLE_ROLLBACK_LAST_KNOWN_GOOD_IMAGE_MISSING");
        var release = new StableUpdateManifestVerifier.VerifiedRelease(
            version, sequence,
            new Uri("https://celikom.invalid/CELIKOM/Windows/Updates/stable/" +
                version.ToString(3) + "/cached.exe"),
            packageSize, packageHash, DateTimeOffset.MaxValue, false, "",
            ApplicationSha256: applicationHash,
            NativeHostSha256: nativeHostHash,
            RendererSha256: rendererHash,
            SupervisorSha256: supervisorHash);
        verify(installer, release, pinnedSignerSha256);
        return new CachedSignedPackage(installer, release);
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
        if (current.Schema != 2 || current.Id != expectedId ||
            current.State != expectedPhase || !Allowed(expectedPhase, nextPhase))
            throw new IOException("STABLE_ROLLBACK_TRANSITION_DENIED");
        var attempts = current.RollbackAttempts +
            (nextPhase == Phase.RollbackStarted ? 1 : 0);
        if (attempts > 1)
            throw new IOException("STABLE_ROLLBACK_ATTEMPT_LIMIT");
        var next = current with { State = nextPhase, RollbackAttempts = attempts };
        WriteRecord(root, next);
        return next;
    }

    /// <summary>
    /// W110: mark the ONLY automatic rollback attempt before launching the
    /// prior signed installer. Restarting this helper cannot grant a second
    /// attempt. The old-version health timeout starts at rollback launch,
    /// not at the original update's preparation time.
    /// </summary>
    public static Record BeginRollback(string privateRoot, Guid id, DateTimeOffset now)
    {
        RequireWindows();
        var root = FullRoot(privateRoot);
        using var exclusive = AcquireLock(root);
        var state = ReadRecord(root);
        if (state.Schema != 2 || state.Id != id ||
            state.State != Phase.RollbackNeeded || state.RollbackAttempts != 0)
            throw new IOException("STABLE_ROLLBACK_ALREADY_ATTEMPTED");
        var next = state with
        {
            State = Phase.RollbackStarted,
            RollbackAttempts = 1,
            DeadlineUnix = now.AddMinutes(10).ToUnixTimeSeconds()
        };
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
        if (state.Schema != 2 || state.Id != id ||
            state.State != Phase.RollbackStarted || state.RollbackAttempts != 1 ||
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
        if (record.Schema != 2 || record.Id == Guid.Empty ||
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
        if (state.Schema != 2 || state.Id != transaction ||
            state.State != Phase.RollbackNeeded || state.RollbackAttempts != 0 ||
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
            DateTimeOffset.MaxValue, false, "",
            ApplicationSha256: state.PreviousApplicationSha256,
            NativeHostSha256: state.PreviousNativeHostSha256,
            RendererSha256: state.PreviousRendererSha256,
            SupervisorSha256: state.PreviousSupervisorSha256);
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
        (Phase.RollbackNeeded, Phase.ManualRecovery) => true,
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
            if (record is null || record.Schema is not (1 or 2) || record.Id == Guid.Empty ||
                !ValidSha(record.PreviousSha256) || !ValidSha(record.TargetSha256) ||
                !ValidSha(record.SignerSha256) ||
                (record.ExpectedSession && !ValidSha(record.SessionIdentitySha256) ||
                 !record.ExpectedSession && record.SessionIdentitySha256 != "") ||
                (record.Schema == 2 &&
                 (!ValidSha(record.PreviousApplicationSha256) ||
                  !ValidSha(record.TargetApplicationSha256) ||
                  !ValidSha(record.PreviousNativeHostSha256) ||
                  !ValidSha(record.TargetNativeHostSha256) ||
                  !ValidSha(record.PreviousRendererSha256) ||
                  !ValidSha(record.TargetRendererSha256) ||
                  !ValidSha(record.PreviousSupervisorSha256) ||
                  !ValidSha(record.TargetSupervisorSha256))) ||
                !Version.TryParse(record.PreviousVersion, out var previous) ||
                !Version.TryParse(record.TargetVersion, out var target) ||
                previous >= target || record.PreviousSequence >= record.TargetSequence ||
                record.RollbackAttempts is < 0 or > 1 ||
                record.PreviousSize is < 10_000 or > 125_000_000 ||
                record.TargetSize != 0 &&
                    (record.TargetSize is < 10_000 or > 125_000_000) ||
                record.DeadlineUnix <= 0 ||
                !Enum.IsDefined(record.State) ||
                record.State == Phase.Seeded &&
                    (record.RollbackAttempts != 0 ||
                     record.PreviousVersion != "0.0.0.0" ||
                     record.PreviousSequence != 0 ||
                     record.TargetSize != record.PreviousSize ||
                     !string.Equals(record.PreviousSha256, record.TargetSha256, StringComparison.Ordinal) ||
                     !string.Equals(record.PreviousApplicationSha256, record.TargetApplicationSha256, StringComparison.Ordinal) ||
                     !string.Equals(record.PreviousNativeHostSha256, record.TargetNativeHostSha256, StringComparison.Ordinal) ||
                     !string.Equals(record.PreviousRendererSha256, record.TargetRendererSha256, StringComparison.Ordinal) ||
                     !string.Equals(record.PreviousSupervisorSha256, record.TargetSupervisorSha256, StringComparison.Ordinal)))
                throw new IOException("STABLE_ROLLBACK_RECORD_INVALID");
            return record;
        }
        catch (Exception e) when (e is CryptographicException or JsonException)
        {
            throw new IOException("STABLE_ROLLBACK_RECORD_UNTRUSTED", e);
        }
    }

    private static void CopyVerifiedImage(string sourcePath, string destinationPath,
        long expectedSize)
    {
        var sourceInfo = new FileInfo(sourcePath);
        if (!sourceInfo.Exists ||
            sourceInfo.Attributes.HasFlag(FileAttributes.ReparsePoint) ||
            sourceInfo.Length != expectedSize)
            throw new IOException("STABLE_ROLLBACK_IMAGE_INVALID");
        using (var source = new FileStream(sourcePath, FileMode.Open,
            FileAccess.Read, FileShare.Read, 65536, FileOptions.SequentialScan))
        using (var output = new FileStream(destinationPath, FileMode.CreateNew,
            FileAccess.Write, FileShare.None, 65536, FileOptions.WriteThrough))
        {
            source.CopyTo(output);
            output.Flush(flushToDisk: true);
        }
        var copied = new FileInfo(destinationPath);
        if (!copied.Exists || copied.Length != expectedSize ||
            copied.Attributes.HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("STABLE_ROLLBACK_IMAGE_COPY_INVALID");
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
