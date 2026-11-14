using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Security.Cryptography;
using Celikom.Companion;

int checks = 0;
void Test(bool condition, string message)
{
    checks++;
    if (!condition) throw new Exception("W15_TEST_FAILED: " + message);
}
var folder = Path.Combine(Path.GetTempPath(), "celikom-w15-contract-" + Guid.NewGuid().ToString("N"));
try
{
    Test(!AppUpdateManager.CanLaunchWithoutPlaybackInterrupt(bridgeEnabled: true),
        "W108 manual in-place update must not interrupt active CELIKOM playback");

    // W109: snapshot the exact previous signed installer and journal the
    // single rollback attempt before a new app can be accepted as healthy.
    // Test verifier is intentionally synthetic; PrepareSigned in production
    // always requires Authenticode, pinned signer + exact PE checks.
    var rollbackFixtureRoot = Path.Combine(Path.GetTempPath(),
        "celikom-w109-contract-" + Guid.NewGuid().ToString("N"));
    var rollbackRoot = Path.Combine(rollbackFixtureRoot, "rollback-vault");
    Directory.CreateDirectory(rollbackRoot);
    var previousSetup = Path.Combine(rollbackFixtureRoot, "previous-fixture.exe");
    var nextSetup = Path.Combine(rollbackFixtureRoot, "next-fixture.exe");
    var previousBytes = new byte[12_345];
    var nextBytes = new byte[12_678];
    for (var n = 0; n < previousBytes.Length; n++) previousBytes[n] = (byte)(n % 251);
    for (var n = 0; n < nextBytes.Length; n++) nextBytes[n] = (byte)(n % 239);
    File.WriteAllBytes(previousSetup, previousBytes);
    File.WriteAllBytes(nextSetup, nextBytes);
    var prevHash = Convert.ToHexString(SHA256.HashData(previousBytes)).ToLowerInvariant();
    var nextHash = Convert.ToHexString(SHA256.HashData(nextBytes)).ToLowerInvariant();
    var prevAppHash = new string('1', 64);
    var nextAppHash = new string('2', 64);
    var prevHostHash = new string('3', 64);
    var nextHostHash = new string('4', 64);
    var prevRendererHash = new string('5', 64);
    var nextRendererHash = new string('6', 64);
    var prevSupervisorHash = new string('7', 64);
    var nextSupervisorHash = new string('8', 64);
    var rollbackAt = new DateTimeOffset(2026, 11, 14, 9, 0, 0, TimeSpan.Zero);
    var previousRelease = new StableUpdateManifestVerifier.VerifiedRelease(
        new Version(0, 24, 36, 0), 40,
        new Uri("https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.36/previous.exe"),
        previousBytes.Length, prevHash, rollbackAt.AddDays(7), false, "",
        ApplicationSha256: prevAppHash, NativeHostSha256: prevHostHash,
        RendererSha256: prevRendererHash, SupervisorSha256: prevSupervisorHash);
    var targetRelease = new StableUpdateManifestVerifier.VerifiedRelease(
        new Version(0, 24, 37, 0), 41,
        new Uri("https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.37/new.exe"),
        nextBytes.Length, nextHash, rollbackAt.AddDays(7), false, "",
        ApplicationSha256: nextAppHash, NativeHostSha256: nextHostHash,
        RendererSha256: nextRendererHash, SupervisorSha256: nextSupervisorHash);
    var testSignerPin = new string('b', 64);
    var verifiedImages = 0;
    void VerifySyntheticSetup(string file,
        StableUpdateManifestVerifier.VerifiedRelease expected, string signerPin)
    {
        Test(signerPin == testSignerPin &&
             new FileInfo(file).Length == expected.PackageSize &&
             Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file)))
                .Equals(expected.Sha256, StringComparison.OrdinalIgnoreCase),
             "W109 verified rollback snapshot/installer matches signed manifest hash");
        verifiedImages++;
    }
    var tx = StableUpdateRollbackJournal.PrepareCore(
        rollbackRoot, previousRelease, previousSetup, targetRelease, nextSetup,
        testSignerPin, previousRelease.Version, rollbackAt,
        hasSession: true, nativeWasInstalled: true, VerifySyntheticSetup,
        sessionIdentitySha256: new string('d', 64));
    Test(tx.State == StableUpdateRollbackJournal.Phase.Prepared &&
         tx.RollbackAttempts == 0 && verifiedImages == 3 &&
         tx.SessionIdentitySha256 == new string('d', 64) && tx.Schema == 2 &&
         tx.PreviousApplicationSha256 == prevAppHash &&
         tx.TargetApplicationSha256 == nextAppHash &&
         tx.PreviousNativeHostSha256 == prevHostHash &&
         tx.TargetNativeHostSha256 == nextHostHash &&
         tx.PreviousRendererSha256 == prevRendererHash &&
         tx.TargetRendererSha256 == nextRendererHash &&
         tx.PreviousSupervisorSha256 == prevSupervisorHash &&
         tx.TargetSupervisorSha256 == nextSupervisorHash &&
         StableUpdateRollbackJournal.Read(rollbackRoot) == tx,
         "W109 DPAPI journal roundtrip and byte-identical previous EXE snapshot");
    bool missingPayloadDenied = false;
    try
    {
        StableUpdateRollbackJournal.PrepareCore(
            Path.Combine(rollbackFixtureRoot, "missing-payload"),
            previousRelease with { ApplicationSha256 = "" }, previousSetup,
            targetRelease, nextSetup, testSignerPin, previousRelease.Version,
            rollbackAt, true, true, VerifySyntheticSetup,
            sessionIdentitySha256: new string('d', 64));
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_PLAN_INVALID")
    { missingPayloadDenied = true; }
    Test(missingPayloadDenied,
        "W112 rollback journal cannot be prepared from a release without signed payload identity");

    bool overlappingDenied = false;
    try
    {
        StableUpdateRollbackJournal.PrepareCore(rollbackRoot, previousRelease,
            previousSetup, targetRelease, nextSetup, testSignerPin,
            previousRelease.Version, rollbackAt, true, true, VerifySyntheticSetup,
            sessionIdentitySha256: new string('d', 64));
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_PENDING_EXISTS")
    { overlappingDenied = true; }
    Test(overlappingDenied, "W109 overlapping update cannot overwrite last-known-good snapshot");
    tx = StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
        StableUpdateRollbackJournal.Phase.Prepared,
        StableUpdateRollbackJournal.Phase.InstallerStarted);
    var noneHealthy = new StableUpdateRollbackJournal.HealthEvidence(
        ExactSignedNewExe: true, BridgeResponds: false,
        SessionPreserved: false, NativeIntegrationConsistent: false);
    Test(StableUpdateRollbackJournal.Decide(tx, noneHealthy, rollbackAt.AddMinutes(1)) ==
         StableUpdateRollbackJournal.Decision.Wait &&
         StableUpdateRollbackJournal.Decide(tx,
             new StableUpdateRollbackJournal.HealthEvidence(true, true, true, true),
             rollbackAt.AddMinutes(1)) == StableUpdateRollbackJournal.Decision.Wait,
         "W109 mere installer start is never enough even with optimistic health flags");
    tx = StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
        StableUpdateRollbackJournal.Phase.InstallerStarted,
        StableUpdateRollbackJournal.Phase.NewAppObserved);
    Test(StableUpdateRollbackJournal.Decide(tx,
        new StableUpdateRollbackJournal.HealthEvidence(true, true, true, false),
        rollbackAt.AddMinutes(2)) == StableUpdateRollbackJournal.Decision.Wait,
        "W109 native integration status must be verified before successful upgrade");
    Test(StableUpdateRollbackJournal.Decide(tx,
        new StableUpdateRollbackJournal.HealthEvidence(true, true, true, true),
        rollbackAt.AddMinutes(2)) == StableUpdateRollbackJournal.Decision.AcceptNewVersion,
        "W109 signed new EXE + bridge + DPAPI + native checks all required");
    bool fakeHealthBlocked = false;
    try
    {
        StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
            StableUpdateRollbackJournal.Phase.NewAppObserved,
            StableUpdateRollbackJournal.Phase.Healthy);
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_TRANSITION_DENIED")
    { fakeHealthBlocked = true; }
    Test(fakeHealthBlocked, "W109 generic phase change cannot forge health acceptance");
    bool deniedMissingNativeHealth = false;
    try
    {
        StableUpdateRollbackJournal.ConfirmNewAppHealthy(rollbackRoot, tx.Id,
            new StableUpdateRollbackJournal.HealthEvidence(true, true, true, false),
            rollbackAt.AddMinutes(2));
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_HEALTH_NOT_PROVEN")
    { deniedMissingNativeHealth = true; }
    Test(deniedMissingNativeHealth, "W109 health acceptance requires all prior-state evidence");
    var acceptedRoot = Path.Combine(rollbackFixtureRoot, "rollback-happy");
    var accepted = StableUpdateRollbackJournal.PrepareCore(
        acceptedRoot, previousRelease, previousSetup, targetRelease, nextSetup,
        testSignerPin, previousRelease.Version, rollbackAt,
        hasSession: true, nativeWasInstalled: true, VerifySyntheticSetup,
        sessionIdentitySha256: new string('d', 64));
    accepted = StableUpdateRollbackJournal.Advance(acceptedRoot, accepted.Id,
        StableUpdateRollbackJournal.Phase.Prepared,
        StableUpdateRollbackJournal.Phase.InstallerStarted);
    accepted = StableUpdateRollbackJournal.Advance(acceptedRoot, accepted.Id,
        StableUpdateRollbackJournal.Phase.InstallerStarted,
        StableUpdateRollbackJournal.Phase.NewAppObserved);
    accepted = StableUpdateRollbackJournal.ConfirmNewAppHealthy(acceptedRoot,
        accepted.Id,
        new StableUpdateRollbackJournal.HealthEvidence(true, true, true, true),
        rollbackAt.AddMinutes(2));
    Test(accepted.State == StableUpdateRollbackJournal.Phase.Healthy &&
         StableUpdateRollbackJournal.Read(acceptedRoot).State ==
             StableUpdateRollbackJournal.Phase.Healthy,
         "W109 only explicitly verified signed app health closes transaction");
    var thirdRelease = new StableUpdateManifestVerifier.VerifiedRelease(
        new Version(0, 24, 38, 0), 42,
        new Uri("https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.38/new.exe"),
        previousBytes.Length, prevHash, rollbackAt.AddDays(8), false, "",
        ApplicationSha256: new string('7', 64),
        NativeHostSha256: new string('8', 64),
        RendererSha256: new string('9', 64),
        SupervisorSha256: new string('a', 64));
    var nextTransaction = StableUpdateRollbackJournal.PrepareCore(
        acceptedRoot, targetRelease, nextSetup, thirdRelease, previousSetup,
        testSignerPin, targetRelease.Version, rollbackAt.AddHours(1),
        hasSession: true, nativeWasInstalled: true, VerifySyntheticSetup,
        sessionIdentitySha256: new string('d', 64));
    Test(nextTransaction.State == StableUpdateRollbackJournal.Phase.Prepared &&
         nextTransaction.Id != accepted.Id &&
         StableUpdateRollbackJournal.Read(acceptedRoot).Id == nextTransaction.Id,
         "W109 completed upgrade allows future signed upgrades without overwriting active rollback");
    Test(StableUpdateRollbackJournal.Decide(tx, noneHealthy, rollbackAt.AddMinutes(11)) ==
         StableUpdateRollbackJournal.Decision.RequestRollback,
        "W109 timeout requests exact last-known-good package instead of fake success");
    tx = StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
        StableUpdateRollbackJournal.Phase.NewAppObserved,
        StableUpdateRollbackJournal.Phase.RollbackNeeded);
    var beforeReverify = verifiedImages;
    var retained = StableUpdateRollbackJournal.VerifiedPreviousInstallerCore(
        rollbackRoot, tx.Id, testSignerPin, VerifySyntheticSetup);
    Test(File.Exists(retained) && verifiedImages == beforeReverify + 1,
        "W109 previous installer re-verified immediately before rollback");
    var corrupted = File.ReadAllBytes(retained);
    corrupted[31] ^= 1;
    File.WriteAllBytes(retained, corrupted);
    bool corruptedRollbackRefused = false;
    try
    {
        StableUpdateRollbackJournal.VerifiedPreviousInstallerCore(
            rollbackRoot, tx.Id, testSignerPin, VerifySyntheticSetup);
    }
    catch (Exception e) when (e.Message.StartsWith("W15_TEST_FAILED",
        StringComparison.Ordinal) || e is IOException)
    { corruptedRollbackRefused = true; }
    Test(corruptedRollbackRefused, "W109 tampered retained rollback image cannot be used");
    tx = StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
        StableUpdateRollbackJournal.Phase.RollbackNeeded,
        StableUpdateRollbackJournal.Phase.RollbackStarted);
    Test(tx.RollbackAttempts == 1 &&
         StableUpdateRollbackJournal.Decide(tx, noneHealthy,
             rollbackAt.AddHours(1)) == StableUpdateRollbackJournal.Decision.ManualRecovery,
         "W109 rollback is at-most-once; never create an automatic install loop");
    bool replayDenied = false;
    try
    {
        StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
            StableUpdateRollbackJournal.Phase.RollbackNeeded,
            StableUpdateRollbackJournal.Phase.RollbackStarted);
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_TRANSITION_DENIED")
    { replayDenied = true; }
    Test(replayDenied, "W109 repeated rollback request is refused");
    bool fakeRestoreDenied = false;
    try
    {
        StableUpdateRollbackJournal.Advance(rollbackRoot, tx.Id,
            StableUpdateRollbackJournal.Phase.RollbackStarted,
            StableUpdateRollbackJournal.Phase.Restored);
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_TRANSITION_DENIED")
    { fakeRestoreDenied = true; }
    Test(fakeRestoreDenied, "W109 arbitrary phase transition cannot forge restored app health");
    bool missingSessionDenied = false;
    try
    {
        StableUpdateRollbackJournal.ConfirmPreviousRestored(rollbackRoot, tx.Id,
            new StableUpdateRollbackJournal.HealthEvidence(true, true, false, true));
    }
    catch (IOException e) when (e.Message == "STABLE_ROLLBACK_RESTORE_NOT_PROVEN")
    { missingSessionDenied = true; }
    Test(missingSessionDenied, "W109 rollback confirmation must preserve encrypted login");
    tx = StableUpdateRollbackJournal.ConfirmPreviousRestored(rollbackRoot, tx.Id,
        new StableUpdateRollbackJournal.HealthEvidence(true, true, true, true));
    Test(tx.State == StableUpdateRollbackJournal.Phase.Restored,
        "W109 verified previous EXE, bridge, session and native state finish recovery");
    var dpapiJournal = Path.Combine(rollbackRoot, "stable-update-rollback.dpapi");
    var ciphertext = File.ReadAllBytes(dpapiJournal);
    // Mutate the authenticated ciphertext tail, not merely a DPAPI header
    // byte that Windows may ignore during decryption.
    ciphertext[^16] ^= 1;
    File.WriteAllBytes(dpapiJournal, ciphertext);
    bool tamperedJournalDenied = false;
    try { StableUpdateRollbackJournal.Read(rollbackRoot); }
    catch (IOException e) when (e.Message is "STABLE_ROLLBACK_RECORD_UNTRUSTED"
        or "STABLE_ROLLBACK_RECORD_INVALID")
    { tamperedJournalDenied = true; }
    Test(tamperedJournalDenied, "W109 encrypted rollback transaction rejects modification");
    // Isolate all W109 fixtures from legacy W15 SessionStore tests that
    // explicitly require the account folder to contain only session.dpapi.
    Directory.Delete(rollbackFixtureRoot, recursive: true);

    // W105: exact byte stream, SHA256 and signature all have to succeed
    // before a staged installer may ever be considered executable.
    var updateBytes = new byte[32_768];
    for (var j = 0; j < updateBytes.Length; j++)
        updateBytes[j] = (byte)(j % 251);
    var updateHash = Convert.ToHexString(SHA256.HashData(updateBytes)).ToLowerInvariant();
    var updateRelease = new StableUpdateManifestVerifier.VerifiedRelease(
        new Version(0, 24, 37, 0), 47,
        new Uri("https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.37/CELIKOM-Windows-0.24.37-SIGNED.exe"),
        updateBytes.Length, updateHash, DateTimeOffset.UtcNow.AddDays(1),
        false, "Safe updater test",
        ApplicationSha256: new string('a', 64),
        NativeHostSha256: new string('b', 64),
        RendererSha256: new string('c', 64),
        SupervisorSha256: new string('d', 64));
    // W112: exact installed payload bytes must match the signed feed,
    // independently of the installer package hash and PE version metadata.
    var payloadFolder = Path.Combine(folder, "payload-fixture");
    Directory.CreateDirectory(payloadFolder);
    var payloadExe = Path.Combine(payloadFolder, "CELIKOM.Companion.exe");
    var payloadHost = Path.Combine(payloadFolder, "host.cjs");
    var payloadRenderer = Path.Combine(payloadFolder, "renderer.js");
    var payloadSupervisor = Path.Combine(payloadFolder, "CELIKOM.UpdateSupervisor.exe");
    File.WriteAllText(payloadExe, "signed-exe-payload-fixture");
    File.WriteAllText(payloadHost, "native-host-payload-fixture");
    File.WriteAllText(payloadRenderer, "renderer-payload-fixture");
    File.WriteAllText(payloadSupervisor, "supervisor-payload-fixture");
    var payloadExeHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(payloadExe))).ToLowerInvariant();
    var payloadHostHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(payloadHost))).ToLowerInvariant();
    var payloadRendererHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(payloadRenderer))).ToLowerInvariant();
    var payloadSupervisorHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(payloadSupervisor))).ToLowerInvariant();
    Test(StableUpdatePayloadVerifier.MatchesFile(payloadExe, payloadExeHash) &&
         StableUpdatePayloadVerifier.MatchesFile(payloadHost, payloadHostHash, 32_000_000) &&
         StableUpdatePayloadVerifier.MatchesFile(payloadRenderer, payloadRendererHash, 32_000_000) &&
         StableUpdatePayloadVerifier.MatchesFile(payloadSupervisor, payloadSupervisorHash),
         "W114 exact signed manifest payload hashes accept all four installed files");
    Test(!StableUpdatePayloadVerifier.MatchesFile(payloadExe, new string('0', 64)) &&
         !StableUpdatePayloadVerifier.MatchesFile(payloadHost, "not-a-hash") &&
         !StableUpdatePayloadVerifier.MatchesFile(Path.Combine(payloadFolder, "missing.cjs"),
             payloadHostHash),
         "W112 wrong hash, malformed hash and missing payload fail closed");
    File.AppendAllText(payloadHost, "tampered");
    File.AppendAllText(payloadExe, "tampered");
    Test(!StableUpdatePayloadVerifier.MatchesFile(payloadExe, payloadExeHash),
         "W112 executable tamper cannot be hidden by unchanged PE version");
    Test(!StableUpdatePayloadVerifier.MatchesFile(payloadHost, payloadHostHash, 32_000_000),
         "W112 native bridge tamper cannot be hidden by unchanged EXE version");
    File.AppendAllText(payloadRenderer, "tampered");
    Test(!StableUpdatePayloadVerifier.MatchesFile(payloadRenderer, payloadRendererHash, 32_000_000),
         "W112 renderer tamper cannot be hidden by unchanged EXE version");
    var updateStage = Path.Combine(folder, "stable-stage");
    using (var updateClient = new HttpClient(new FakeHandler(req =>
        new HttpResponseMessage(HttpStatusCode.OK)
            { RequestMessage = req, Content = new ByteArrayContent(updateBytes) })))
    {
        var untrusted = await StableUpdatePackageStager.DownloadUntrustedAsync(
            updateRelease, updateStage, updateClient);
        Test(File.Exists(untrusted) && File.ReadAllBytes(untrusted).SequenceEqual(updateBytes),
            "W105 bounded HTTP200 content and exact SHA256 stage without execution");
        bool missingPayloadRejected = false;
        try
        {
            StableUpdatePackageStager.VerifyInstaller(untrusted,
                updateRelease with { RendererSha256 = "" }, new string('a', 64));
        }
        catch (IOException e) when (e.Message == "STABLE_UPDATE_PAYLOAD_IDENTITY_MISSING")
        { missingPayloadRejected = true; }
        Test(missingPayloadRejected,
            "W112 staged installer is never considered verified without all signed payload hashes");

        bool unsignedRejected = false;
        try { StableUpdatePackageStager.VerifyInstaller(
                untrusted, updateRelease, new string('a', 64)); }
        catch (IOException e) when (e.Message == "STABLE_UPDATE_AUTHENTICODE_INVALID")
        { unsignedRejected = true; }
        Test(unsignedRejected, "W105 unsigned fixture must fail Authenticode even with signed-feed hash");
        var tamperedBytes = (byte[])updateBytes.Clone();
        tamperedBytes[3] ^= 1;
        File.WriteAllBytes(untrusted, tamperedBytes);
        bool tamperRejected = false;
        try { StableUpdatePackageStager.VerifyInstaller(
                untrusted, updateRelease, new string('a', 64)); }
        catch (IOException e) when (e.Message == "STABLE_UPDATE_SHA256_MISMATCH")
        { tamperRejected = true; }
        Test(tamperRejected, "W105 post-stage byte tamper is rejected before launch");
    }
    using (var badClient = new HttpClient(new FakeHandler(req =>
        new HttpResponseMessage(HttpStatusCode.OK)
            { RequestMessage = req, Content = new ByteArrayContent(updateBytes.AsSpan(0, 25_000).ToArray()) })))
    {
        bool shortRejected = false;
        try { await StableUpdatePackageStager.DownloadUntrustedAsync(
                updateRelease, updateStage, badClient); }
        catch (IOException e) when (e.Message is "STABLE_UPDATE_HTTP_INVALID" or
            "STABLE_UPDATE_HASH_OR_LENGTH") { shortRejected = true; }
        Test(shortRejected, "W105 interrupted transfer cannot leave an executable staged file");
    }
    using (var redirectClient = new HttpClient(new FakeHandler(req =>
        new HttpResponseMessage(HttpStatusCode.Redirect)
            { RequestMessage = req, Headers = { Location = new Uri("https://evil.example/install.exe") } })))
    {
        bool redirectRejected = false;
        try { await StableUpdatePackageStager.DownloadUntrustedAsync(
                updateRelease, updateStage, redirectClient); }
        catch (IOException e) when (e.Message == "STABLE_UPDATE_HTTP_INVALID")
        { redirectRejected = true; }
        Test(redirectRejected, "W105 no redirects permitted for signed release package");
    }
    Test(StableUpdateInstallSafety.CanInstall(false, false, true, false) &&
         !StableUpdateInstallSafety.CanInstall(true, false, true, false) &&
         !StableUpdateInstallSafety.CanInstall(false, true, true, false) &&
         !StableUpdateInstallSafety.CanInstall(false, false, false, false) &&
         !StableUpdateInstallSafety.CanInstall(false, false, true, true),
         "W105 never interrupt Yandex audio or install with unknown playback state");

    // W101: signed stable update contracts are read-only and fail closed.
    // No unattended updater is enabled while signing/rollback gates are missing.
    using (var releaseKey = ECDsa.Create(ECCurve.NamedCurves.nistP256))
    {
        var signedFeedOrigin = new Uri("https://celikom.example.test");
        var signedFeedNow = new DateTimeOffset(2026, 11, 14, 0, 0, 0, TimeSpan.Zero);
        var pub = releaseKey.ExportSubjectPublicKeyInfo();
        byte[] ManifestBytes(string channel = "stable",
            string version = "0.24.37", long sequence = 42,
            string? url = null, int schema = 2,
            string? applicationHash = null, string? nativeHostHash = null,
            string? rendererHash = null, string? supervisorHash = null) =>
            JsonSerializer.SerializeToUtf8Bytes(new {
                schema, channel, version, sequence,
                packageUrl = url ?? "https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.37/CELIKOM-Windows-0.24.37-SIGNED.exe",
                packageSize = 500000L,
                sha256 = new string('a', 64), publisher = "CELIKOM",
                applicationSha256 = applicationHash ?? new string('1', 64),
                nativeHostSha256 = nativeHostHash ?? new string('2', 64),
                rendererSha256 = rendererHash ?? new string('3', 64),
                supervisorSha256 = supervisorHash ?? new string('4', 64),
                publishedAt = "2026-11-14T00:00:00Z",
                expiresAt = "2026-11-20T00:00:00Z",
                minimumVersion = "0.24.20", mandatory = false, notes = "Safe update"
            });
        StableUpdateManifestVerifier.VerifiedRelease VerifyManifest(byte[] bytes,
            byte[]? signature = null, long previousSequence = 41) =>
            StableUpdateManifestVerifier.Verify(bytes,
                signature ?? releaseKey.SignData(bytes, HashAlgorithmName.SHA256,
                    DSASignatureFormat.Rfc3279DerSequence),
                pub, signedFeedOrigin, new Version(0, 24, 36, 0), previousSequence, signedFeedNow);
        var signedDocument = ManifestBytes();
        // W107: do not trust TLS alone; both the JSON and its detached
        // signature must be fetched from the exact official HTTPS origin.
        var detachedSignature = releaseKey.SignData(signedDocument,
            HashAlgorithmName.SHA256, DSASignatureFormat.Rfc3279DerSequence);
        using (var feedHttp = new HttpClient(new FakeHandler(req =>
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                RequestMessage = req,
                Content = new ByteArrayContent(req.RequestUri!.AbsolutePath.EndsWith(".sig",
                    StringComparison.Ordinal) ? detachedSignature : signedDocument)
            })))
        {
            var feed = await StableUpdateManifestFetcher.FetchSignedWithClientAsync(
                signedFeedOrigin, pub, new Version(0, 24, 36, 0), 41,
                signedFeedNow, feedHttp);
            Test(feed.Version == new Version(0, 24, 37, 0) &&
                 feed.Sequence == 42 && feed.RollbackFrom == null,
                 "W107 exact-origin signed feed is verified before displaying a version");
        }
        using (var tamperFeedHttp = new HttpClient(new FakeHandler(req =>
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                RequestMessage = req,
                Content = new ByteArrayContent(req.RequestUri!.AbsolutePath.EndsWith(".sig",
                    StringComparison.Ordinal) ? new byte[70] : signedDocument)
            })))
        {
            bool signatureRejected = false;
            try { await StableUpdateManifestFetcher.FetchSignedWithClientAsync(
                    signedFeedOrigin, pub, new Version(0, 24, 36, 0), 41,
                    signedFeedNow, tamperFeedHttp); }
            catch (InvalidDataException e) when
                (e.Message == "STABLE_MANIFEST_SIGNATURE_INVALID")
            { signatureRejected = true; }
            Test(signatureRejected, "W107 signed feed refuses substituted signature");
        }
        using (var redirectFeedHttp = new HttpClient(new FakeHandler(req =>
            new HttpResponseMessage(HttpStatusCode.Redirect)
            {
                RequestMessage = req,
                Headers = { Location = new Uri("https://evil.example/latest.json") }
            })))
        {
            bool feedRedirectRejected = false;
            try { await StableUpdateManifestFetcher.FetchSignedWithClientAsync(
                    signedFeedOrigin, pub, new Version(0, 24, 36, 0), 41,
                    signedFeedNow, redirectFeedHttp); }
            catch (InvalidDataException e) when
                (e.Message == "STABLE_FEED_HTTP_INVALID")
            { feedRedirectRejected = true; }
            Test(feedRedirectRejected, "W107 stable feed never follows redirects");
        }
        var signedRelease = VerifyManifest(signedDocument);
        Test(signedRelease.Sequence == 42 &&
             signedRelease.Version == new Version(0, 24, 37, 0) &&
             signedRelease.PackageUri.Host == signedFeedOrigin.Host &&
             signedRelease.ApplicationSha256 == new string('1', 64) &&
             signedRelease.NativeHostSha256 == new string('2', 64) &&
             signedRelease.RendererSha256 == new string('3', 64) &&
             signedRelease.SupervisorSha256 == new string('4', 64),
             "W101 pinned P256 stable manifest permits only newer exact-origin release");
        bool Reject(byte[] bytes, byte[]? signature = null, long lastSequence = 41)
        {
            try { VerifyManifest(bytes, signature, lastSequence); return false; }
            catch (InvalidDataException) { return true; }
        }
        Test(Reject(signedDocument, new byte[70]) &&
             Reject(ManifestBytes(channel: "beta")) &&
             Reject(ManifestBytes(version: "0.24.36")) &&
             Reject(ManifestBytes(sequence: 41)) &&
             Reject(ManifestBytes(schema: 1)) &&
             Reject(ManifestBytes(applicationHash: "bad")) &&
             Reject(ManifestBytes(nativeHostHash: "")) &&
             Reject(ManifestBytes(rendererHash: new string('Z', 64))) &&
              Reject(ManifestBytes(supervisorHash: "")) &&
             Reject(signedDocument, lastSequence: 42),
             "W101 unsigned, wrong-channel, same-version and replayed updates fail closed");
        Test(Reject(ManifestBytes(url:
                "https://evil.example/CELIKOM/Windows/Updates/stable/0.24.37/bad.exe")) &&
             Reject(ManifestBytes(url:
                "http://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.37/bad.exe")) &&
             Reject(ManifestBytes(url:
                "https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.38/bad.exe")),
             "W101 package origin, HTTPS and immutable version path are required");

        byte[] RollbackManifest(string from = "0.24.36",
            string target = "0.24.35", bool mandatory = true, long sequence = 48) =>
            JsonSerializer.SerializeToUtf8Bytes(new
            {
                schema = 2, channel = "stable", version = target, sequence,
                packageUrl = "https://celikom.example.test/CELIKOM/Windows/Updates/stable/"
                             + target + "/CELIKOM-Windows-" + target + "-SIGNED.exe",
                packageSize = 500000L, sha256 = new string('a', 64),
                publisher = "CELIKOM",
                applicationSha256 = new string('1', 64),
                nativeHostSha256 = new string('2', 64),
                rendererSha256 = new string('3', 64),
                supervisorSha256 = new string('4', 64),
                publishedAt = "2026-11-14T00:00:00Z",
                expiresAt = "2026-11-20T00:00:00Z",
                minimumVersion = "0.24.20", mandatory, notes = "Bad version rollback",
                rollback = new { fromVersion = from, toVersion = target }
            });
        var exactRollback = VerifyManifest(RollbackManifest(), previousSequence: 47);
        Test(exactRollback.RollbackFrom == new Version(0, 24, 36, 0) &&
             exactRollback.Version == new Version(0, 24, 35, 0) &&
             exactRollback.Mandatory && exactRollback.Sequence == 48,
             "W106 signed mandatory rollback is scoped to one exact bad version");
        Test(Reject(RollbackManifest(from: "0.24.34"), lastSequence: 47) &&
             Reject(RollbackManifest(target: "0.24.37"), lastSequence: 47) &&
             Reject(RollbackManifest(mandatory: false), lastSequence: 47) &&
             Reject(RollbackManifest(sequence: 47), lastSequence: 47) &&
             Reject(ManifestBytes(version: "0.24.35", url:
                 "https://celikom.example.test/CELIKOM/Windows/Updates/stable/0.24.35/CELIKOM-Windows-0.24.35-SIGNED.exe")),
             "W106 wrong source, downgrade without directive, replay and optional rollback fail closed");
    }

    // W104: explicit bridge failure / missing startup handshake triggers a
    // read-only compatibility refresh, never on a per-track 403 or originals.
    Test(YandexFailureRecheckGate.IsNativeHostFailure("HOST_ERROR") &&
         !YandexFailureRecheckGate.IsNativeHostFailure("NATIVE_SOURCE_FAILED") &&
         !YandexFailureRecheckGate.IsNativeHostFailure("ORIGINAL"),
        "W104 only native HOST_ERROR triggers immediate vendor recheck");
    Test(YandexFailureRecheckGate.IsMissingStartupHandshake("UNAVAILABLE") &&
         YandexFailureRecheckGate.IsMissingStartupHandshake("NOT_CONNECTED") &&
         !YandexFailureRecheckGate.IsMissingStartupHandshake("NATIVE_CONNECTED") &&
         !YandexFailureRecheckGate.IsMissingStartupHandshake("ORIGINAL") &&
         !YandexFailureRecheckGate.IsMissingStartupHandshake("NATIVE_SOURCE_FAILED"),
        "W104 do not interpret working native or audio source failure as bridge startup failure");
    var failureGate = new YandexFailureRecheckGate();
    var failureAt = new DateTimeOffset(2026, 11, 14, 0, 0, 0, TimeSpan.Zero);
    Test(failureGate.TryStart(failureAt) &&
         !failureGate.TryStart(failureAt.AddMinutes(3)),
        "W104 concurrent bridge failures coalesce while check is running");
    failureGate.Finish();
    Test(!failureGate.TryStart(failureAt.AddSeconds(119)) &&
         failureGate.TryStart(failureAt.AddSeconds(120)),
        "W104 compatibility requests throttle for two minutes after start");
    failureGate.Finish();
    Test(!failureGate.TryStart(failureAt.AddSeconds(359)) &&
         failureGate.TryStart(failureAt.AddSeconds(360)),
        "W104 repeated native failures back off to four minutes");
    failureGate.Finish();
    Test(YandexFailureRecheckGate.IsNativeHandshakePresent("ORIGINAL") &&
         YandexFailureRecheckGate.IsNativeHandshakePresent("NATIVE_CONNECTED") &&
         YandexFailureRecheckGate.IsNativeHandshakePresent("NATIVE_SOURCE_FAILED") &&
         !YandexFailureRecheckGate.IsNativeHandshakePresent("HOST_ERROR"),
        "W104 native heartbeat presence is separate from successful alternative playback");
    failureGate.ConfirmNativeHealthy();
    Test(failureGate.TryStart(failureAt.AddSeconds(361)),
        "W104 valid native handshake clears repeated-failure backoff");
    failureGate.Finish();

    // W74: first Start must not confuse an in-flight host scan with an
    // unsupported vendor version. Existing active native integration is valid
    // without checking the original ASAR hash of the modified host.
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.NotInstalled,
            null)!.Contains("ещё не завершена"),
        "W74 pending host scan never reports unsupported Yandex");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.Active,
            null) == null,
        "W74 existing native integration bypasses original-host hash probe");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.NotInstalled,
            new YandexHostResult(YandexHostStatus.OfficialBaselineVerified, "5.126.1.0")) == null,
        "W74 only verified official baseline permits first integration");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.NotInstalled,
            new YandexHostResult(YandexHostStatus.InspectionUnavailable, "")) is { } temporarily &&
         !temporarily.Contains("не поддерживается"),
        "W74 interrupted inspection never shows false unsupported modal");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.NotInstalled,
            new YandexHostResult(YandexHostStatus.UnsupportedVersion, "9.9.9"))!.Contains("не поддерживается"),
        "W74 genuine unsupported version still blocked");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.Changed,
            new YandexHostResult(YandexHostStatus.OfficialBaselineVerified, "5.126.1.0")) != null,
        "W74 changed patched host never bypasses backup safety gate");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.Changed,
            new YandexHostResult(YandexHostStatus.UnsupportedVersion, "5.128.0.r24000000"))!
            .Contains("Новая версия пока проходит проверку"),
        "W80 newly updated unsupported Yandex reports calm pending compatibility without changing files");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.VerifiedVendorUpdate,
            new YandexHostResult(YandexHostStatus.OfficialBaselineVerified, "5.127.0.r22015925")) == null,
        "W80 fully reviewed new vendor pair is startable even with previous snapshot");
    Test(StartupHostPreflight.BlockReason(Celikom.NativeInstaller.NativeInstallState.Changed,
            new YandexHostResult(YandexHostStatus.UntrustedExecutable, "5.128.0.r24000000"))!
            .Contains("заблокировано"),
        "W80 unknown tampered host remains blocked, never mistaken for verified update");
    // W82: transition-only native heartbeats cannot prove an outage.
    // Successful handoff is normal, not a yellow warning; true explicit
    // source failures are the only per-track red error.
    Test(UserFacingPlaybackHealth.Host(Celikom.NativeInstaller.NativeInstallState.Active,
        null, true).Level == UserFacingPlaybackHealth.Severity.Good,
        "W82 verified integrated host has good connectivity only");
    Test(UserFacingPlaybackHealth.Host(Celikom.NativeInstaller.NativeInstallState.Changed,
        new YandexHostResult(YandexHostStatus.UnsupportedVersion, "5.128.0.r24000000"), false)
        .Level == UserFacingPlaybackHealth.Severity.Error,
        "W82 genuinely unsupported official Yandex build remains actionable");
    Test(UserFacingPlaybackHealth.Track("NATIVE_SOURCE_FAILED", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Error,
        "W82 explicit failed track replacement remains red");
    Test(UserFacingPlaybackHealth.Track("NATIVE_SOURCE_FAILED", true, "approved").Message
        .Contains("оригинал"),
        "W82 explicit song error correctly distinguishes working original playback");
    Test(UserFacingPlaybackHealth.Track("NATIVE_MAPPING_ACCEPTED", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Neutral,
        "W82 normal audio source accepted has no false warning");
    Test(UserFacingPlaybackHealth.Track("NATIVE_CONNECTED", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Neutral,
        "W82 steady track and transition-only heartbeat must not report connection loss");
    Test(!PlaybackSourceEvidence.Verified(true, "NATIVE_MAPPING_ACCEPTED", "approved") &&
         PlaybackSourceEvidence.MappedButUnverified(true, "NATIVE_MAPPING_ACCEPTED", "approved") &&
         !PlaybackSourceEvidence.Verified(true, "SDK_MAPPING_ACCEPTED", "approved") &&
         !PlaybackSourceEvidence.Verified(true, "NATIVE_CONNECTED", "approved"),
         "W89 mapping or Yandex connection alone must never paint the current track green");
    Test(PlaybackSourceEvidence.Verified(true, "NATIVE_SOURCE_VERIFIED", "approved") &&
         !PlaybackSourceEvidence.Verified(false, "NATIVE_SOURCE_VERIFIED", "approved") &&
         !PlaybackSourceEvidence.Verified(true, "NATIVE_SOURCE_VERIFIED", "none") &&
         !PlaybackSourceEvidence.MappedButUnverified(true, "NATIVE_SOURCE_VERIFIED", "approved"),
         "W89 only exact current decoder proof while enabled with approved version may paint green");
    Test(UserFacingPlaybackHealth.Track("HOST_ERROR", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Error,
        "W82 explicitly reported host failure remains visible");
    Test(UserFacingPlaybackHealth.Track("NATIVE_RECOVERING", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Neutral,
        "W82 normal transient source recovery is not a customer warning");
    Test(UserFacingPlaybackHealth.Track("RESOLVING", true, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Neutral,
        "W82 normal resolving status is not a customer warning");
    Test(UserFacingPlaybackHealth.Track("ORIGINAL", true, "approved").Message.Contains("оригинал"),
        "W82 known original source is surfaced quietly, not alarm");
    Test(UserFacingPlaybackHealth.Track("OFF", false, "approved").Level ==
        UserFacingPlaybackHealth.Severity.Neutral,
        "W82 explicitly stopped service is not a failure");
    // W83: recurring entitlement checks must not flash the promo label.
    const string lifetime = "Промокод · доступ навсегда";
    Test(CompactAccessRefresh.WhileChecking(lifetime, "install-1",
        "owner@example.test", "install-1", "OWNER@example.test") == lifetime,
        "W83 15s repeated entitlement request keeps confirmed lifetime promo visible");
    Test(CompactAccessRefresh.WhileChecking("Подписка до 1 января",
        "install-1", "owner@example.test", "install-1", "owner@example.test") ==
        "Подписка до 1 января",
        "W83 subscription label stays steady through server revalidation");
    Test(CompactAccessRefresh.WhileChecking(lifetime, "install-1",
        "owner@example.test", "install-2", "owner@example.test") ==
        CompactAccessRefresh.Checking,
        "W83 different device never sees previous lifetime promo");
    Test(CompactAccessRefresh.WhileChecking(lifetime, "install-1",
        "owner@example.test", "install-1", "another@example.test") ==
        CompactAccessRefresh.Checking,
        "W83 account switch never sees old account's entitlement");
    Test(CompactAccessRefresh.WhileChecking("Доступ не подтверждён", "",
        "", "install-1", "owner@example.test") == CompactAccessRefresh.Checking,
        "W83 unverified access always displays checking until server responds");
    Test(!CompactAccessRefresh.NeedsLabelChange(lifetime, lifetime) &&
        CompactAccessRefresh.NeedsLabelChange(lifetime, "Подписка завершена"),
        "W83 no text repaint for identical label but real revocation must repaint");
    // W88: one-time default-on enrollment is a preference, never
    // a playback entitlement. A recorded opt-out must survive upgrades.
    Test(WindowsLaunchSettings.ShouldEnableDefault(false),
        "W88 initial clean install enables tray autostart by default");
    Test(!WindowsLaunchSettings.ShouldEnableDefault(true),
        "W88 explicit autostart choice must never be overwritten on later launch");
    // W87: Windows login persistence is only a remembered user preference.
    // It can never replace server entitlement or grant access by itself.
    const string loginInstallation = "94e77e24-9abc-4c68-b3c0-a3e7aa1bb516";
    const string loginEmail = "owner@example.test";
    var loginFingerprint = WindowsLaunchSettings.FingerprintForTest(
        loginInstallation, loginEmail);
    Test(WindowsLaunchSettings.ShouldResume(true, true, loginFingerprint,
        loginInstallation, "OWNER@example.test"),
        "W87 explicit autostart and same signed-in account can request a server check");
    Test(!WindowsLaunchSettings.ShouldResume(false, true, loginFingerprint,
        loginInstallation, loginEmail),
        "W87 disabling autostart prevents all automatic playback attempts");
    Test(!WindowsLaunchSettings.ShouldResume(true, false, loginFingerprint,
        loginInstallation, loginEmail),
        "W87 last user Stop prevents silent resume across reboot");
    Test(!WindowsLaunchSettings.ShouldResume(true, true, loginFingerprint,
        "c6e77e24-9abc-4c68-b3c0-a3e7aa1bb516", loginEmail),
        "W87 new installation never inherits another installation's Start");
    Test(!WindowsLaunchSettings.ShouldResume(true, true, loginFingerprint,
        loginInstallation, "other@example.test"),
        "W87 another account never inherits previous user's Start");
    Test(!WindowsLaunchSettings.ShouldResume(true, true, null,
        loginInstallation, loginEmail),
        "W87 missing saved intent cannot enable background");
    var runCmd = WindowsLaunchSettings.BuildRunCommand(
        @"C:\Program Files\CELIKOM\CELIKOM.Companion.exe");
    Test(runCmd.StartsWith('"') && runCmd.EndsWith(" --background") &&
        runCmd.Contains(@"C:\Program Files\CELIKOM\CELIKOM.Companion.exe"),
        "W87 HKCU Run command quotes paths with spaces and starts quietly");
    Test(UserFacingPlaybackHealth.Host(
        Celikom.NativeInstaller.NativeInstallState.Active, null,
        moduleMatches:false).Level == UserFacingPlaybackHealth.Severity.Neutral,
        "W87 normal new-app module refresh is a neutral Start hint, not red alarm");
    Test(UserFacingPlaybackHealth.Host(
        Celikom.NativeInstaller.NativeInstallState.Active, null,
        moduleMatches:false).Message.Contains("Старт"),
        "W87 repair instruction references the real Start button");

    // W75: a temporary /auth/me failure must never hide an already
    // verified owner's diagnostics button, but never authorizes export.
    var temporaryError = new HttpRequestException("synthetic unreachable");
    Test(DiagnosticsAccessRecovery.KeepButtonOnFailure(
        true, true, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-1", "OWNER@example.test", temporaryError),
        "W75 existing verified owner keeps diagnostics control visible during transient network failure");
    Test(!DiagnosticsAccessRecovery.KeepButtonOnFailure(
        false, true, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-1", "owner@example.test", temporaryError),
        "W75 never shows developer diagnostics for unverified user");
    Test(!DiagnosticsAccessRecovery.KeepButtonOnFailure(
        true, true, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-1", "other@example.test", temporaryError),
        "W75 account switch always hides previous owner's diagnostics");
    Test(!DiagnosticsAccessRecovery.KeepButtonOnFailure(
        true, true, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-2", "owner@example.test", temporaryError),
        "W75 device change never reuses prior owner identity");
    Test(!DiagnosticsAccessRecovery.KeepButtonOnFailure(
        true, false, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-1", "owner@example.test", temporaryError),
        "W75 logout always revokes diagnostics");
    Test(!DiagnosticsAccessRecovery.KeepButtonOnFailure(
        true, true, "https://example.test", "installation-1", "owner@example.test",
        "https://example.test", "installation-1", "owner@example.test",
        new ApiFailure(403, "ACCESS_DENIED")),
        "W75 real server permission denial hides owner diagnostics");

    Test(YandexHostProbe.VerifiedVersion == "5.126.1.0", "pinned official host version");
    Test(YandexHostProbe.VerifiedAsarSha256.Length == 64, "pinned official ASAR fingerprint");
    Test(YandexHostProbe.Inspect(Path.Combine(folder, "yandex-not-installed")).Status ==
        YandexHostStatus.NotInstalled, "missing host does not prompt for patching");
    var incomplete = Path.Combine(folder, "broken-yandex");
    Directory.CreateDirectory(incomplete);
    File.WriteAllText(Path.Combine(incomplete, "Яндекс Музыка.exe"), "not an app");
    Test(YandexHostProbe.Inspect(incomplete).Status == YandexHostStatus.IncompleteInstallation,
        "incomplete install is never treated as compatible");
    Directory.Delete(incomplete, true);

    Test(BridgeServer.ValidNativeOrigin("https://desktop.app.music.yandex.net"),
        "native Yandex renderer is allowed");
    Test(!BridgeServer.ValidNativeOrigin("https://evil.yandex.net"),
        "unrelated renderer is denied");
    Test(!BridgeServer.ValidNativeOrigin("null"),
        "opaque origin denied without native capability");
    Test(BridgeServer.ValidNativeProtocolOrigin("null"),
        "custom Electron scheme can serialize an opaque origin");
    Test(BridgeServer.ValidNativeProtocolOrigin("musicapplication://desktop"),
        "exact official native protocol accepted for capability checking");
    Test(!BridgeServer.ValidNativeProtocolOrigin("file://local"),
        "arbitrary local protocol is not a native host");
    using (var native = new NativeTokenPublisher(Path.Combine(folder, "native-test")))
    {
        var key = new string('a', 64);
        native.Publish(key);
        Test(File.ReadAllText(native.FilePath) == key, "native bridge capability published");
        native.Publish(new string('b', 64));
        Test(File.ReadAllText(native.FilePath) == new string('b', 64),
            "native pairing capability rotates");
    }
    Test(!File.Exists(Path.Combine(folder, "native-test", "native-bridge.key")),
        "native bridge capability removed on shutdown");
    var store = new SessionStore(folder);
    var first = store.LoadOrCreate();
    Test(Guid.TryParse(first.InstallationId, out _), "device ID");
    Test(SessionStore.IsHexToken(first.BridgeToken), "bridge token");
    Test(first.AccessToken == "", "off by default");
    Test(Directory.GetFiles(folder).Length == 1, "only DPAPI session file");
    Test(!Encoding.UTF8.GetString(File.ReadAllBytes(Path.Combine(folder, "session.dpapi"))).Contains(first.BridgeToken),
        "bridge token is encrypted at rest");

    // W111: an updater must prove the SAME account and installation survived,
    // not merely that some new DPAPI file is decryptable after reinstall.
    var witnessDir = Path.Combine(folder, "session-identity-fixture");
    var witnessFile = Path.Combine(witnessDir, "session.dpapi");
    Test(SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile) is null &&
         !File.Exists(witnessFile),
         "W111 checking for preserved session never creates a fresh login");
    var witnessStore = new SessionStore(witnessDir);
    var originalLogin = witnessStore.LoadOrCreate() with
    {
        Email = "owner@example.test",
        AccessToken = "old-access-token"
    };
    witnessStore.Save(originalLogin);
    var originalWitness = SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile);
    Test(originalWitness is { Length: 64 } &&
         SignedUpdateSessionIdentity.ReadExisting(witnessFile)?.Email == "owner@example.test",
         "W111 original signed-in account identity can be read without mutation");
    witnessStore.Save(originalLogin with { AccessToken = "rotated-access-token" });
    Test(SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile) == originalWitness,
         "W111 normal access-token refresh does not fake a session reset");
    witnessStore.Save(originalLogin with { InstallationId = Guid.NewGuid().ToString("D") });
    Test(SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile) != originalWitness,
         "W111 newly recreated installation is not falsely marked preserved");
    witnessStore.Save(originalLogin with { Email = "other@example.test" });
    Test(SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile) != originalWitness,
         "W111 different account is not falsely marked preserved");
    File.WriteAllBytes(witnessFile, new byte[256]);
    Test(SignedUpdateSessionIdentity.ReadExistingFingerprint(witnessFile) is null,
         "W111 corrupted DPAPI session never counts as healthy");

    var now = DateTimeOffset.UtcNow;
    var unix = now.ToUnixTimeSeconds() + 200;
    var audio = "/api/v1/audio/42?token=" + new string('a', 64) + "&expires=" + unix + "&sid=7";
    JsonElement Parse(object source) { using var json = JsonDocument.Parse(JsonSerializer.Serialize(source)); return json.RootElement.Clone(); }
    // W74: retry only an idempotent activation once after a bounded transient
    // network failure. A denial, throttle, or cancelled user intent is never
    // blindly replayed. The retry can authorize only from a fresh server JSON.
    var activationCalls = 0;
    var activationCodes = new List<string>();
    var freshAccess = Parse(new { allowed = true, source = "promo",
        valid_until = (string?)null, reason = "promo_lifetime" });
    var recoveredAccess = await StartupActivationRecovery.ActivateAsync(
        _ => {
            activationCalls++;
            return activationCalls == 1
                ? Task.FromException<JsonElement>(new HttpRequestException("synthetic route failure"))
                : Task.FromResult(freshAccess);
        }, () => true, activationCodes.Add);
    Test(activationCalls == 2 && recoveredAccess.GetProperty("allowed").GetBoolean() &&
         activationCodes.SequenceEqual(new [] {
             "ACTIVE_ENTITLEMENT_NETWORK_ERROR", "START_ENTITLEMENT_RETRY",
             "START_ENTITLEMENT_RETRY_OK"
         }), "W74 one network failure retries activation exactly once");
    activationCalls = 0;
    try {
        await StartupActivationRecovery.ActivateAsync(
            _ => {
                activationCalls++;
                return Task.FromException<JsonElement>(new ApiFailure(403, "ACCESS_DENIED"));
            }, () => true);
        throw new Exception("W74_DENIAL_MUST_THROW");
    } catch (ApiFailure denied) when (denied.HttpStatus == 403) { }
    Test(activationCalls == 1 && !StartupActivationRecovery.SafeToRetry(
        new ApiFailure(429, "RATE_LIMITED")), "W74 no retry for denial or throttle");
    activationCalls = 0;
    try {
        await StartupActivationRecovery.ActivateAsync(
            _ => {
                activationCalls++;
                return Task.FromException<JsonElement>(new HttpRequestException("synthetic"));
            }, () => false);
        throw new Exception("W74_INVALID_START_MUST_THROW");
    } catch (HttpRequestException) { }
    Test(activationCalls == 1, "W74 Stop/account change vetoes retry");
    var payload = Parse(new { found = true, audio_url = audio, expires_at = unix,
        duration_ms = 200_000, mime_type = "audio/mpeg", gain_db = 5.5 });
    var origin = GrantValidator.NormalizeOrigin("https://api.celikom.example");
    var grant = GrantValidator.FromResolve(payload, "123", origin, now);
    Test(grant != null, "real PHP ResolveService grant accepted");
    Test(grant!.ExpiresAt == unix * 1000, "server Unix seconds to JS milliseconds");
    Test(grant.MimeType == "audio/mpeg", "source mime survives bridge to native decoder");
    Test(grant.GainDb == 5.5, "W90 saved admin boost must survive typed Windows grant");
    Test(grant.GainApplied == false, "W91 raw grant cannot claim DSP applied");
    var gainWire = JsonSerializer.Serialize(grant, new JsonSerializerOptions(JsonSerializerDefaults.Web));
    Test(gainWire.Contains("gainDb"), "W90 native localhost grant includes camelCase gainDb");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" }),
        "123", origin, now)?.GainDb == 0,
        "W90 missing gain defaults to zero for older server contracts");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg", gain_db = -9.0 }),
        "123", origin, now)?.GainDb == -9.0,
        "W90 negative admin gain survives grant as well");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg", gain_db = 12.1 }),
        "123", origin, now) == null,
        "W90 rejects out-of-range admin gains");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg", gain_db = "6" }),
        "123", origin, now) == null,
        "W90 rejects string gain and never guesses dB");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg", gain_db = 1.25 }),
        "123", origin, now) == null,
        "W90 rejects unapproved fractional precision");
    var processedUrl = audio + "&variant=windows_gain_v1";
    var processed = GrantValidator.FromResolve(Parse(new { found = true,
        audio_url = processedUrl, expires_at = unix, duration_ms = 200000,
        mime_type = "audio/mpeg", gain_db = 11.5, gain_applied = true }),
        "123", origin, now);
    Test(processed?.GainApplied == true && processed.GainDb == 11.5 &&
         processed.AudioUrl.EndsWith("&variant=windows_gain_v1"),
         "W91 scoped offline render accepted only with explicit gain_applied");
    Test(GrantValidator.FromResolve(Parse(new { found = true,
        audio_url = processedUrl, expires_at = unix, duration_ms = 200000,
        mime_type = "audio/mpeg", gain_db = 11.5, gain_applied = false }),
        "123", origin, now) == null,
        "W91 raw and rendered source may never be confused");
    Test(GrantValidator.FromResolve(Parse(new { found = true,
        audio_url = audio, expires_at = unix, duration_ms = 200000,
        mime_type = "audio/mpeg", gain_db = 11.5, gain_applied = true }),
        "123", origin, now) == null,
        "W91 an unprocessed source cannot claim gain already applied");
    Test(grant.AudioUrl == "https://api.celikom.example" + audio, "exact HTTPS signed URL");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio.Replace("&sid=7", ""),
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "W68 legacy sid-less audio grants rejected before native SDK");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio + "&sid=8",
        expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "duplicate sid rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix + 1, duration_ms = 200000, mime_type = "audio/mpeg" }), "123", origin, now) == null,
        "mismatched expiry rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = true, audio_url = audio,
        expires_at = unix, duration_ms = 200000, mime_type = "text/html" }), "123", origin, now) == null,
        "unsupported audio rejected");
    Test(GrantValidator.FromResolve(Parse(new { found = false }), "123", origin, now) == null,
        "missing track returns original");
    Test(!GrantValidator.IsTrackId("123:42"), "no fuzzy album ID");
    Test(!GrantValidator.IsTrackId("01"), "no ambiguous leading zeros");
    // W64: Only validate audio locally BEFORE a multipart request can begin.
    // Deterministic 128kbps 44.1kHz MPEG1 Layer III frames, no real music.
    var frames = new byte[417 * 90];
    for (var i = 0; i < 90; i++)
    {
        var at = i * 417;
        frames[at] = 0xff; frames[at + 1] = 0xfb;
        frames[at + 2] = 0x90; frames[at + 3] = 0x64;
    }
    var duration = AudioPreflight.Mp3DurationMs(frames);
    Test(duration is > 2300 and < 2400, "MP3 frames determine actual duration");
    var testAudio = Path.Combine(folder, "wrong_artist_wrong_song.mp3");
    Directory.CreateDirectory(folder);
    await File.WriteAllBytesAsync(testAudio, frames);
    var okDuration = await AudioPreflight.CheckAsync(testAudio, duration);
    Test(!okDuration.Blocked,
        "matching duration permits any filename regardless of title");
    var unicodeAudio = Path.Combine(folder, "中文-💿-неизвестно.mp3");
    File.Copy(testAudio, unicodeAudio);
    var unicodeOk = await AudioPreflight.CheckAsync(unicodeAudio, duration);
    Test(!unicodeOk.Blocked, "unicode filenames cannot trigger name-based rejection");
    File.Delete(unicodeAudio);
    var wrongDuration = await AudioPreflight.CheckAsync(testAudio, 223000);
    Test(wrongDuration.Blocked && wrongDuration.DurationMessage.Contains("Допуск подмены"),
        "large duration mismatch is rejected BEFORE any upload");
    var unknownOriginal = await AudioPreflight.CheckAsync(testAudio, null);
    Test(unknownOriginal.Blocked, "unverified original duration fails closed");
    var invalidAudio = Path.Combine(folder, "fake.mp3");
    await File.WriteAllBytesAsync(invalidAudio, new byte[2048]);
    var fake = await AudioPreflight.CheckAsync(invalidAudio, 2350);
    Test(fake.Blocked && fake.DurationMs == null,
        "fake MP3 is rejected locally (not just filename validation)");
    File.Delete(testAudio);
    File.Delete(invalidAudio);


    // GitHub Windows installer workflow injects the built ZIP after Inno Setup.
    var zipFixture = Environment.GetEnvironmentVariable("CELIKOM_UPDATE_TEST_PACKAGE");
    if (!string.IsNullOrWhiteSpace(zipFixture))
    {
        var staged = AppUpdateManager.Stage(zipFixture, new Version(0, 24, 16, 0));
        Test(staged.Version == new Version(0, 24, 36, 0),
            "ZIP one-click updater accepts new CELIKOM version");
        Test(Path.GetFileName(staged.Path).StartsWith("CELIKOM-W100-",StringComparison.Ordinal),
            "ZIP extraction stages only CELIKOM installer");
        bool oldRejected = false;
        try { AppUpdateManager.Stage(zipFixture, AppUpdateManager.RunningVersion); }
        catch (IOException e) when (e.Message == "UPDATE_NOT_NEWER") { oldRejected = true; }
        Test(oldRejected, "update button rejects already-installed version");
        Test(!File.Exists(Path.Combine(AppUpdateManager.RunningVersion.ToString(), "fake")),
            "upgrade acceptance never modifies Yandex");
    }
        var expectedAccess = new string('b', 64);
    var expectedRefresh = new string('c', 64);
    var backendCalls = new List<string>();
    using var api = new CelikomApi(store, new FakeHandler(request =>
    {
        var path = request.RequestUri!.AbsolutePath;
        backendCalls.Add(path);
        if (path == "/api/v1/auth/login")
            return JsonResponse(new { user = new { id = 1, email = "test@example.com", status = "active" },
                access_token = expectedAccess, refresh_token = expectedRefresh, expires_in = 900 });
        if (path == "/api/v1/auth/activate")
        {
            Test(request.Method == HttpMethod.Post &&
                request.Headers.Authorization?.Parameter == expectedAccess,
                "W68 trial activation uses POST with current user bearer");
            return JsonResponse(new { ok = true, trial = new { activated = true, trial_seconds = 259200 },
                entitlement = new { allowed = true, source = "trial",
                    valid_until = now.AddDays(3).ToString("O"), reason = "trial_active" } });
        }
        if (path == "/api/v1/entitlement")
        {
            Test(request.Method == HttpMethod.Get && request.Headers.ConnectionClose == true &&
                 request.Headers.CacheControl?.NoStore == true &&
                 request.Headers.CacheControl?.NoCache == true,
                 "W72 entitlement GET bypasses stale cached VPN route and cache");
            return JsonResponse(new { allowed = true, source = "promo",
                valid_until = (string?)null, reason = "promo_lifetime" });
        }
        if (path == "/api/v1/promos/redeem")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "promo uses CELIKOM bearer only");
            return JsonResponse(new { revoked = false, already_activated = false,
                entitlement = new { allowed = true, source = "promo",
                    valid_until = (string?)null, reason = "promo_lifetime" } });
        }
        if (path == "/api/v1/support")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "support uses CELIKOM bearer only");
            var content = request.Content!.ReadAsStringAsync().GetAwaiter().GetResult();
            Test(!content.Contains("refresh_token") && !content.Contains("access_token"),
                "support does not leak tokens");
            using var payload = JsonDocument.Parse(content);
            var body = payload.RootElement;
            Test(body.GetProperty("request_key").GetString()!.Length == 36,
                "support idempotent request key");
            if (body.GetProperty("kind").GetString() == "song")
            {
                if (body.GetProperty("report").GetProperty("diagnostics")
                    .TryGetProperty("windows", out var songWindows) &&
                    songWindows.ValueKind == JsonValueKind.Object)
                    Test(songWindows.GetProperty("platform").GetString() == "windows" &&
                         songWindows.GetProperty("events").ValueKind == JsonValueKind.Array,
                         "W70 song ticket automatically carries bounded Windows diagnostic payload");
                Test(body.GetProperty("report").GetProperty("category").GetString() == "audio_issue",
                    "song report category matches extension");
                Test(body.GetProperty("report").GetProperty("track").GetProperty("id").GetString() == "144530503",
                    "only exact owner track ID reported");
            }
            else if (body.TryGetProperty("diagnostics", out var generalWindows) &&
                     generalWindows.ValueKind == JsonValueKind.Object)
            {
                Test(generalWindows.GetProperty("platform").GetString() == "windows" &&
                     generalWindows.GetProperty("scopeSeconds").GetInt32() == 900,
                     "W70 general ticket automatically carries bounded diagnostics");
            }
            return JsonResponse(new { ticket_id = 3 });
        }
        if (path == "/api/v1/auth/me")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "diagnostic permission asks server using CELIKOM authorization");
            return JsonResponse(new { user = new { id = 1, email = "test@example.com", status = "active" } });
        }
        if (path == "/api/v1/resolve")
        {
            Test(request.Headers.Authorization?.Parameter == expectedAccess,
                "backend receives own CELIKOM session only");
            Test(request.RequestUri.Query.Contains("track_id=123"), "exact track ID query");
            return JsonResponse(new { found = true, audio_url = audio,
                expires_at = unix, duration_ms = 200000, mime_type = "audio/mpeg" });
        }
        if (path == "/api/v1/auth/logout") return JsonResponse(new { ok = true });
        return JsonResponse(new { error = "not_found" }, 404);
    }));

    await api.LoginAsync("https://api.celikom.example", "test@example.com", "own_password");
    Test(api.IsLoggedIn, "CELIKOM auth session accepted");
    Test(api.Email == "test@example.com", "account displayed");
    Test(store.LoadOrCreate().RefreshToken == expectedRefresh, "session retained through DPAPI");
    var authenticatedBridgeToken = store.LoadOrCreate().BridgeToken;
    Test(authenticatedBridgeToken != first.BridgeToken,
        "sign-in rotates prior add-on bridge capability");
    var resolved = await api.ResolveAsync("123", CancellationToken.None);
    Test(resolved?.AudioUrl == "https://api.celikom.example" + audio, "live-contract resolve mapping");
    Test(backendCalls.SequenceEqual(new [] { "/api/v1/auth/login", "/api/v1/resolve" }),
        "only expected private backend endpoints");
    // W68 launch gate: trial begins on explicit first Start, never on login,
    // preview, or local session load. The server is the only clock/authority.
    var beforeTrialCalls = backendCalls.Count;
    var started = await api.ActivatePlaybackAsync();
    Test(backendCalls.Count == beforeTrialCalls + 1 &&
        backendCalls[^1] == "/api/v1/auth/activate",
        "W68 explicit server trial activation, not local timestamp");
    Test(PlaybackEntitlement.Allowed(started, now),
        "W68 active 72h trial accepted only after server response");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "trial", valid_until = now.AddSeconds(-1).ToString("O"),
        reason = "trial_active" }), now), "W68 expired trial blocked");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = false,
        source = "subscription", valid_until = now.AddDays(10).ToString("O"),
        reason = "subscription_inactive" }), now), "W68 unpaid account blocked");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "subscription", valid_until = (string?)null,
        reason = "subscription_active" }), now), "W68 malformed forever subscription denied");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "none", valid_until = (string?)null,
        reason = "trial_not_started" }), now), "W68 unknown perpetual source denied");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = false,
        source = "trial", valid_until = now.AddHours(10).ToString("O"),
        reason = "service_incident" }), now), "W68 incident not marked active");
    Test(PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "promo", valid_until = (string?)null,
        reason = "promo_active" }), now), "W68 genuine lifetime promo accepted");
    Test(!PlaybackEntitlement.Allowed(Parse(new { allowed = true,
        source = "trial", valid_until = "invalid-date", reason = "trial_active" }), now),
        "W68 unparseable expiry fails closed");
    // W71: only fresh, positive authenticated entitlement may resume after a network flap.
    Test(EntitlementCheckRecovery.IsTransient(new HttpRequestException()) &&
         EntitlementCheckRecovery.IsTransient(new TaskCanceledException()) &&
         EntitlementCheckRecovery.IsTransient(new ApiFailure(429, "RATE_LIMITED")) &&
         EntitlementCheckRecovery.IsTransient(new ApiFailure(503, "API_ERROR")),
         "W71 temporary network, 429 and 5xx errors retryable");
    Test(EntitlementCheckRecovery.IsTransient(new ApiFailure(0, "INVALID_API_JSON")) &&
         EntitlementCheckRecovery.IsTransient(new ApiFailure(302, "REDIRECT_FORBIDDEN")) &&
         EntitlementCheckRecovery.FailureCode(new ApiFailure(0, "INVALID_API_JSON")) ==
             "ACTIVE_ENTITLEMENT_BAD_RESPONSE" &&
         EntitlementCheckRecovery.FailureCode(new TaskCanceledException()) ==
             "ACTIVE_ENTITLEMENT_TIMEOUT",
         "W72 captive-portal HTML, VPN redirect and timeout are classified safely");
    Test(EntitlementCheckRecovery.PollIntervalMs(false) == 15_000 &&
         EntitlementCheckRecovery.PollIntervalMs(true) == 3_000,
         "W89 suspended VPN recovery checks bounded to three seconds, healthy 15s unchanged");
    Test(EntitlementCheckRecovery.FastRouteCheck(true, now, DateTimeOffset.MinValue) &&
         EntitlementCheckRecovery.FastRouteCheck(false, now, now.AddSeconds(-4)) &&
         !EntitlementCheckRecovery.FastRouteCheck(false, now, now.AddMinutes(-2)) &&
         !EntitlementCheckRecovery.FastRouteCheck(false, now, DateTimeOffset.MinValue) &&
         EntitlementCheckRecovery.QuickRecheckTimeout == TimeSpan.FromSeconds(3),
         "W89 short request deadline applies only after a network route change or suspension");
    // W94: multiple network-address events during VPN switch are NOT skipped.
    // The last event owns the only new revalidation after the quiet period.
    var firstRouteEpoch = NetworkRouteBurstPolicy.NextEpoch(0);
    var secondRouteEpoch = NetworkRouteBurstPolicy.NextEpoch(firstRouteEpoch);
    var lastRouteEpoch = NetworkRouteBurstPolicy.NextEpoch(secondRouteEpoch);
    Test(firstRouteEpoch == 1 && secondRouteEpoch == 2 && lastRouteEpoch == 3 &&
         !NetworkRouteBurstPolicy.Latest(firstRouteEpoch, lastRouteEpoch) &&
         !NetworkRouteBurstPolicy.Latest(secondRouteEpoch, lastRouteEpoch) &&
         NetworkRouteBurstPolicy.Latest(lastRouteEpoch, lastRouteEpoch),
         "W94 VPN bursts invalidate stale scheduled route checks, last signal wins");
    Test(NetworkRouteBurstPolicy.LogDue(now, DateTimeOffset.MinValue) &&
         !NetworkRouteBurstPolicy.LogDue(now.AddMilliseconds(100),
             now) &&
         NetworkRouteBurstPolicy.LogDue(now.AddMilliseconds(1400), now) &&
         NetworkRouteBurstPolicy.NextEpoch(int.MaxValue) == 1,
         "W94 1.4s coalescing suppresses only diagnostics, not actual route checks");
    Test(!EntitlementCheckRecovery.IsTransient(new ApiFailure(401, "INVALID_SESSION")) &&
         !EntitlementCheckRecovery.IsTransient(new ApiFailure(403, "ACCESS_DENIED")) &&
         !EntitlementCheckRecovery.IsTransient(new InvalidOperationException()),
         "W71 denied session and local errors not retryable");
    var freshAllowed = Parse(new { allowed = true, source = "promo",
        valid_until = (string?)null, reason = "promo_active" });
    var freshDenied = Parse(new { allowed = false, source = "trial",
        valid_until = now.AddHours(1).ToString("O"), reason = "service_incident" });
    Test(EntitlementCheckRecovery.MayResume(true, true, true, true, freshAllowed, now),
         "W71 approved server entitlement may restore suspended playback");
    Test(!EntitlementCheckRecovery.MayResume(false, true, true, true, freshAllowed, now) &&
         !EntitlementCheckRecovery.MayResume(true, false, true, true, freshAllowed, now) &&
         !EntitlementCheckRecovery.MayResume(true, true, false, true, freshAllowed, now) &&
         !EntitlementCheckRecovery.MayResume(true, true, true, false, freshAllowed, now) &&
         !EntitlementCheckRecovery.MayResume(true, true, true, true, freshDenied, now),
         "W71 manual stop, logout, mismatch and denied never auto-restart");
    var accessPreview = await api.GetEntitlementAsync();
    Test(accessPreview.GetProperty("source").GetString() == "promo" &&
         accessPreview.GetProperty("valid_until").ValueKind == JsonValueKind.Null,
        "W62 lifetime promo access is server-backed (not hardcoded)");
    var redeemed = await api.RedeemPromoAsync("TESTPROMO123");
    Test(redeemed.GetProperty("entitlement").GetProperty("allowed").GetBoolean(),
        "W62 promo redeems via existing service");
    var automaticDiagnostics = DiagnosticLog.ExportSupportSnapshot(
        "5.126.1.0", "ACTIVE", true, true, "0.24.19", true, "144530503");
    var support = await api.SendSupportAsync("Проверка поддержки", Guid.NewGuid(),
        diagnostics: automaticDiagnostics);
    Test(support.GetProperty("ticket_id").GetInt32() == 3, "W62 general support real API");
    var songSupport = await api.SendSongSupportAsync("Звук прерывается", Guid.NewGuid(),
        "144530503", "audio_issue", true, true,
        windowsDiagnostics: automaticDiagnostics);
    Test(songSupport.GetProperty("ticket_id").GetInt32() == 3,
        "W62 typed song support real API");
    Test(!await api.CanExportDiagnosticsAsync(),
        "regular active user cannot export owner diagnostics");
    Test(backendCalls[^1] == "/api/v1/auth/me",
        "diagnostics access revalidates server user, not UI email alone");

    await using (var bridge = new BridgeServer(api, store))
    {
        await bridge.StartAsync();
        using var http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:21471") };
        async Task<HttpResponseMessage> Request(string route, HttpMethod method,
            object? body = null, string? token = null, string originHeader = "https://addon-1024.pulsesync.invalid")
        {
            using var req = new HttpRequestMessage(method, route);
            req.Headers.TryAddWithoutValidation("Origin", originHeader);
            if (token != null) req.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
            if (body != null) req.Content = JsonContent.Create(body);
            return await http.SendAsync(req);
        }
        using (var bad = await Request("/v1/health", HttpMethod.Get,
            originHeader: "https://evil.example"))
            Test(bad.StatusCode == HttpStatusCode.Forbidden, "foreign site blocked");
        using (var bad = await Request("/v1/state", HttpMethod.Get))
            Test(bad.StatusCode == HttpStatusCode.Unauthorized, "unpaired state forbidden");
        using (var preflight = await Request("/v1/state", HttpMethod.Options))
            Test(preflight.StatusCode == HttpStatusCode.NoContent, "CORS preflight");
        using var paired = await Request("/v1/pair", HttpMethod.Post, new { code = bridge.PairCode });
        Test(paired.IsSuccessStatusCode, "one-time code pairs");
        using var pairJson = JsonDocument.Parse(await paired.Content.ReadAsStringAsync());
        var token = pairJson.RootElement.GetProperty("bridgeToken").GetString();
        Test(SessionStore.IsHexToken(token), "isolated bridge token issued");
        bridge.SetEnabled(true);
        foreach (var nativeOrigin in new[] { "null", "musicapplication://desktop" })
        {
            using (var nativePreflight = new HttpRequestMessage(HttpMethod.Options, "/v1/state"))
            {
                nativePreflight.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                nativePreflight.Headers.TryAddWithoutValidation(
                    "Access-Control-Request-Headers", "x-celikom-bridge-token, x-celikom-native-host");
                using var response = await http.SendAsync(nativePreflight);
                Test(response.StatusCode == HttpStatusCode.NoContent,
                    "native custom-protocol preflight permitted");
                Test(response.Headers.GetValues("Access-Control-Allow-Origin").Single() == nativeOrigin,
                    "native preflight scoped to actual origin");
            }
            using (var nativeState = new HttpRequestMessage(HttpMethod.Get, "/v1/state"))
            {
                nativeState.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                nativeState.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
                nativeState.Headers.TryAddWithoutValidation("X-Celikom-Native-Host", "1");
                using var response = await http.SendAsync(nativeState);
                Test(response.IsSuccessStatusCode, "native Yandex renderer reads authorized state");
            }
            using (var foreign = new HttpRequestMessage(HttpMethod.Get, "/v1/state"))
            {
                foreign.Headers.TryAddWithoutValidation("Origin", nativeOrigin);
                foreign.Headers.TryAddWithoutValidation("X-Celikom-Bridge-Token", token);
                using var response = await http.SendAsync(foreign);
                Test(response.StatusCode == HttpStatusCode.Forbidden,
                    "opaque-origin request without native marker refused");
            }
        }
        using (var state = await Request("/v1/state", HttpMethod.Get, token: token))
        {
            Test(state.IsSuccessStatusCode, "paired can read state");
            var body = await state.Content.ReadAsStringAsync();
            Test(body.Contains("\"enabled\":true"), "start action reaches addon");
            Test(!body.Contains(expectedAccess), "no CELIKOM access token leaked");
            Test(!body.Contains(expectedRefresh), "no CELIKOM refresh token leaked");
        }
        using (var response = await Request("/v1/resolve?track_id=123", HttpMethod.Get, token: token))
        {
            var json = await response.Content.ReadAsStringAsync();
            Test(response.IsSuccessStatusCode && json.Contains("https://api.celikom.example"),
                "paired route emits authorized signed media");
            Test(!json.Contains(expectedAccess) && !json.Contains(expectedRefresh),
                "audio grant never exposes API credentials");
        }
        bridge.SetEnabled(false);
        using (var response = await Request("/v1/resolve?track_id=123", HttpMethod.Get, token: token))
            Test((await response.Content.ReadAsStringAsync()).Contains("\"found\":false"),
                "stop disables future source replacement");
    }

    // W72: extension's refresh-race regression ported to real Windows DPAPI.
    // An old 401 can spawn a refresh that finishes AFTER a user's logout.
    // The late successful POST must never resurrect that earlier login.
    var raceFolder = Path.Combine(folder, "refresh-race");
    var raceStore = new SessionStore(raceFolder);
    var refreshEntered = new TaskCompletionSource<bool>(
        TaskCreationOptions.RunContinuationsAsynchronously);
    var releaseRefresh = new TaskCompletionSource<HttpResponseMessage>(
        TaskCreationOptions.RunContinuationsAsynchronously);
    var raceRefreshCalls = 0;
    using (var raceApi = new CelikomApi(raceStore,
        new AsyncFakeHandler(async (request, cancel) =>
        {
            var route = request.RequestUri!.AbsolutePath;
            if (route == "/api/v1/auth/login")
                return JsonResponse(new { user = new { id = 91, email = "race@example.invalid", status = "active" },
                    access_token = new string('1', 64), refresh_token = new string('2', 64), expires_in = 900 });
            if (route == "/api/v1/entitlement")
                return JsonResponse(new { error = "invalid_session" }, 401);
            if (route == "/api/v1/auth/refresh")
            {
                ++raceRefreshCalls;
                refreshEntered.TrySetResult(true);
                return await releaseRefresh.Task.WaitAsync(cancel);
            }
            if (route == "/api/v1/auth/logout") return JsonResponse(new { ok = true });
            return JsonResponse(new { error = "not_found" }, 404);
        })))
    {
        await raceApi.LoginAsync("https://api.celikom.example",
            "race@example.invalid", "test_password");
        var pendingOldRefresh = raceApi.GetEntitlementAsync();
        await refreshEntered.Task.WaitAsync(TimeSpan.FromSeconds(5));
        await raceApi.LogoutAsync();
        releaseRefresh.SetResult(JsonResponse(new {
            user = new { id = 91, email = "race@example.invalid", status = "active" },
            access_token = new string('3', 64), refresh_token = new string('4', 64), expires_in = 900 }));
        var oldRefreshRejected = false;
        try { await pendingOldRefresh; }
        catch (ApiFailure ex) when (ex.HttpStatus == 401) { oldRefreshRejected = true; }
        Test(oldRefreshRejected && !raceApi.IsLoggedIn &&
             raceStore.LoadOrCreate().RefreshToken == "" &&
             raceStore.LoadOrCreate().AccessToken == "" &&
             raceRefreshCalls == 1,
             "W72 stale in-flight refresh cannot restore access after logout");
    }
    await api.LogoutAsync();
    Test(!api.IsLoggedIn, "only Windows CELIKOM session logged out");
    Test(store.LoadOrCreate().RefreshToken == "", "local refresh token cleared");
    Test(store.LoadOrCreate().BridgeToken != authenticatedBridgeToken,
        "logout invalidates old add-on pairing without touching Yandex account");
    var safeTimestamp = "2026-11-09T17:06:00.000Z";
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|SOURCE_MAPPED|track=123"),
        "safe numeric track event passes export");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|SOURCE_MAPPED|track=123?token=SECRET"),
        "signed URL cannot appear in diagnostic event");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|LOGIN_EMAIL=test@example.com"),
        "email cannot appear in diagnostic event");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=139"),
        "W53 native resource id survives export allowlist");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=139"),
        "W53 typed 403 event survives export allowlist");
    Test(DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_URL_QUERY_CHANGED|resource_id=89"),
        "W53 signed URL mismatch classification survives export");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_URL_MATCH|resource_id=139?token=SECRET"),
        "W53 rejects URLs and query leakage in signed request log");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_403_HTML|resource_id=139|token=secret"),
        "W53 rejects extra log fields");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=0139"),
        "W53 rejects ambiguous leading-zero resource IDs");
    Test(!DiagnosticLog.IsSafeEntry(safeTimestamp + "|PLAYER_NET_REQUEST|resource_id=139\nSECRET"),
        "W53 rejects multiline log injection");
    Test(DiagnosticLog.IsIncidentCode("NATIVE_ELECTRON_EVENT_LOOP_STALL") &&
         DiagnosticLog.IsIncidentCode("NATIVE_ELECTRON_MEMORY_HIGH") &&
         DiagnosticLog.IsIncidentCode("PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING") &&
         DiagnosticLog.IsIncidentCode("PLAYER_CURRENT_NATIVE_VOLUME_DROP") &&
         DiagnosticLog.IsIncidentCode("PLAYER_CURRENT_SOURCE_LEFT_CELIKOM") &&
         !DiagnosticLog.IsIncidentCode("WEB_CONTENTS_PRESENT"),
        "W53/W54 performance, gain and volume/source warnings are durable incidents, ordinary status is not");
    var fixtureLogsDirectory = Path.Combine(folder, "owner-export-isolated");
    var nativeFixture = Path.Combine(fixtureLogsDirectory, "native-events.log");
    Directory.CreateDirectory(fixtureLogsDirectory);
    var when = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
        System.Globalization.CultureInfo.InvariantCulture);
    File.AppendAllText(nativeFixture,
        when + "|PLAYER_NET_REQUEST|resource_id=739209\n" +
        when + "|PLAYER_NET_HTTP_FORBIDDEN|resource_id=739209\n" +
        when + "|PLAYER_URL_QUERY_CHANGED|resource_id=739209\n" +
        when + "|PLAYER_URL_SIGNED_FIELDS_INTACT|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=739209\n" +
        when + "|PLAYER_403_HTML|resource_id=739209\n" +
        when + "|PLAYER_403_PHP_ACCESS_DENIED|resource_id=739209\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209?token=SENSITIVE\n" +
        when + "|PLAYER_NET_REQUEST|resource_id=739209|sid=SENSITIVE\n" +
        when + "|NATIVE_ELECTRON_EVENT_LOOP_STALL\n" +
        when + "|NATIVE_ELECTRON_MEMORY_HIGH\n" +
        when + "|PLAYER_CURRENT_GAIN_VARIANT_URL_SELECTED|track=739209\n" +
        when + "|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING|track=739209\n" +
        when + "|PLAYER_CURRENT_NATIVE_VOLUME_DROP|track=739209\n" +
        when + "|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM|track=739209\n");
    File.AppendAllText(Path.Combine(fixtureLogsDirectory, "companion-events.log"),
        when + "|OWNER_DIAG_TEST|track=123\n");
    DiagnosticLog.Record("OWNER_DIAG_TEST", "123");
    var snapshot = DiagnosticLog.ExportText("5.126.1.0", "ACTIVE", true, true, true,
        diagnosticDirectory: fixtureLogsDirectory);
    Test(snapshot.Contains("OWNER_DIAG_TEST|track=123"), "diagnostic export has observed event");
    Test(snapshot.Contains("DiagnosticScope=LAST_15_MINUTES"), "recent sessions only");
    Test(snapshot.Contains("ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING"),
        "successful MP3 probe never implies audio replacement");
    Test(snapshot.Contains("CodeBaseline=W54_GAIN_VARIANT_AND_W53_PERFORMANCE_EXPORT_SAFE"), "W54 truthful diagnostics baseline");
    Test(snapshot.Contains("PLAYER_URL_QUERY_CHANGED|resource_id=739209"),
        "W53 native URL mismatch reaches actual exported TXT");
    Test(snapshot.Contains("PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=739209"),
        "W53 real PHP denial category reaches owner export");
    Test(snapshot.Contains("NativeAudio403Observed=true") &&
         snapshot.Contains("PlayerNetworkRequestObserved=true") &&
         snapshot.Contains("NativeMediaUrlQueryMismatchObserved=true") &&
         snapshot.Contains("NativeMediaUrlSignedFieldsIntactObserved=true") &&
         snapshot.Contains("Native403PhpSignatureRejectionObserved=true") &&
         snapshot.Contains("Native403PhpAccessDenialObserved=true") &&
         snapshot.Contains("Native403HtmlResponseObserved=true") &&
         snapshot.Contains("ElectronEventLoopStallObserved=true") &&
         snapshot.Contains("ElectronMemoryHighObserved=true") &&
         snapshot.Contains("PlayerGainVariantUrlSelectedObserved=true") &&
         snapshot.Contains("PlayerGainVariantUrlMissingObserved=true") &&
         snapshot.Contains("PlayerNativeVolumeDropObserved=true") &&
         snapshot.Contains("PlayerCelikomSourceLeftObserved=true"),
        "W54 owner summary correctly reflects native resource and current-player events");
    Test(!snapshot.Contains("SENSITIVE"),"W53 malformed native lines cannot leak signed query or sid");
    var importedNativeIncidents = DiagnosticLog.ReadIncidentHistory(fixtureLogsDirectory);
    Test(importedNativeIncidents.Any(x => x.Contains("|NATIVE_ELECTRON_EVENT_LOOP_STALL")) &&
         importedNativeIncidents.Any(x => x.Contains("|NATIVE_ELECTRON_MEMORY_HIGH")) &&
         importedNativeIncidents.Any(x => x.Contains("|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING|track=739209")) &&
         importedNativeIncidents.Any(x => x.Contains("|PLAYER_CURRENT_NATIVE_VOLUME_DROP|track=739209")) &&
         importedNativeIncidents.Any(x => x.Contains("|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM|track=739209")),
        "W53/W54 native Electron and current-player incidents are imported into the 7-day archive on export");
    var importedCount = importedNativeIncidents.Count;
    DiagnosticLog.ExportText("5.126.1.0", "ACTIVE", true, true, true,
        diagnosticDirectory: fixtureLogsDirectory);
    Test(DiagnosticLog.ReadIncidentHistory(fixtureLogsDirectory).Count == importedCount,
        "repeated owner exports do not duplicate native incident history");
    var auto = DiagnosticLog.ExportSupportSnapshot("5.126.1.0","ACTIVE", true, true,
        "0.24.20", true, "123", fixtureLogsDirectory);
    var autoJson = JsonSerializer.Serialize(auto);
    using (var parsedAuto = JsonDocument.Parse(autoJson))
    {
        var root = parsedAuto.RootElement;
        Test(root.GetProperty("platform").GetString() == "windows" &&
            root.GetProperty("scopeSeconds").GetInt32() == 900,
            "W70 auto-attachment includes version, bounded scope and platform");
        var events = root.GetProperty("events");
        Test(events.GetArrayLength() <= 64 &&
             events.EnumerateArray().Any(x => x.GetProperty("code").GetString() ==
                "PLAYER_NET_HTTP_FORBIDDEN" &&
                x.GetProperty("resourceId").GetString() == "739209"),
             "W70 auto-support includes recent error and safe numeric resource id");
    }
    Test(!autoJson.Contains("SENSITIVE") && !autoJson.Contains("token=") &&
         !autoJson.Contains("test@example.com") && !autoJson.Contains("sid="),
         "W70 automatic customer attachment is free of tokens, email and signed URLs");
    // W71: flood of status polls cannot hide three intermittent network outages.
    var pollingFlood = string.Concat(Enumerable.Repeat(when + "|NATIVE_STATE_RECEIVED\n" +
        when + "|LOCAL_STATE_OK\n" + when + "|RENDERER_STATE_DELIVERED\n", 200));
    File.AppendAllText(Path.Combine(fixtureLogsDirectory, "companion-events.log"),
        pollingFlood + when + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n" +
        when + "|ACTIVE_ENTITLEMENT_RECOVERED\n" +
        when + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n" +
        when + "|ACTIVE_ENTITLEMENT_RECOVERED\n" +
        when + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n");
    var outageJson = JsonSerializer.Serialize(DiagnosticLog.ExportSupportSnapshot(
        "5.126.1.0", "ACTIVE", true, false, "0.24.20", true, "123", fixtureLogsDirectory));
    using (var outageDoc = JsonDocument.Parse(outageJson))
    {
        var incidents = outageDoc.RootElement.GetProperty("events").EnumerateArray().ToArray();
        Test(incidents.Length <= 64 &&
             incidents.Count(x => x.GetProperty("code").GetString() ==
                 "ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED") == 3 &&
             incidents.Count(x => x.GetProperty("code").GetString() ==
                 "ACTIVE_ENTITLEMENT_RECOVERED") == 2,
             "W71 three network disconnects survive 600 polling messages");
        Test(incidents.All(x => x.GetProperty("code").GetString() is not
                 ("NATIVE_STATE_RECEIVED" or "LOCAL_STATE_OK" or "RENDERER_STATE_DELIVERED")),
             "W71 noisy status polling never floods hidden support attachment");
    }
    Test(!outageJson.Contains("SENSITIVE") && !outageJson.Contains("token="),
         "W71 intermittent outage report remains secret-free");
    // W72 regression: the owner-export TXT keeps only 1600 recent rows,
    // whereas hidden support must retain an event from thirteen minutes ago
    // even after 2500 harmless native status polls.
    var oldIncidentStamp = DateTimeOffset.UtcNow.AddMinutes(-13)
        .ToString("yyyy-MM-ddTHH:mm:ss.fffZ");
    File.AppendAllText(Path.Combine(fixtureLogsDirectory, "companion-events.log"),
        when + "|NATIVE_ELECTRON_EVENT_LOOP_STALL\n" +
         when + "|NATIVE_ELECTRON_MEMORY_HIGH\n" +
         when + "|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING|track=123\n" +
         when + "|PLAYER_CURRENT_NATIVE_VOLUME_DROP|track=123\n" +
         when + "|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM|track=123\n" +
         oldIncidentStamp + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n" +
        string.Concat(Enumerable.Repeat(when + "|NATIVE_STATE_RECEIVED\n", 2_500)) +
        when + "|ACTIVE_ENTITLEMENT_RECOVERED\n");
    var fullWindowJson = JsonSerializer.Serialize(DiagnosticLog.ExportSupportSnapshot(
        "5.126.1.0", "ACTIVE", true, false, "0.24.20", true, "123",
        fixtureLogsDirectory));
    using (var fullWindowDoc = JsonDocument.Parse(fullWindowJson))
    {
        var history = fullWindowDoc.RootElement.GetProperty("events")
            .EnumerateArray().ToArray();
        Test(history.Length <= 64 && history.Any(x =>
            x.GetProperty("code").GetString() == "ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED" &&
            x.GetProperty("ageSeconds").GetInt32() >= 720),
            "W72 13-minute-old disconnect survives more than 2500 later status polls");
         Test(history.Any(x => x.GetProperty("code").GetString() == "PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING" &&
              x.GetProperty("trackId").GetString() == "123") &&
              history.Any(x => x.GetProperty("code").GetString() == "PLAYER_CURRENT_NATIVE_VOLUME_DROP" &&
              x.GetProperty("trackId").GetString() == "123") &&
              history.Any(x => x.GetProperty("code").GetString() == "PLAYER_CURRENT_SOURCE_LEFT_CELIKOM" &&
              x.GetProperty("trackId").GetString() == "123"),
             "W54 gain, volume and source transitions survive later native status polling");
         Test(history.Any(x => x.GetProperty("code").GetString() == "NATIVE_ELECTRON_EVENT_LOOP_STALL") &&
              history.Any(x => x.GetProperty("code").GetString() == "NATIVE_ELECTRON_MEMORY_HIGH"),
             "W53 performance incidents survive later native status polling in support attachment");
        Test(!history.Any(x => x.GetProperty("code").GetString() ==
             "NATIVE_STATE_RECEIVED") &&
             !fullWindowJson.Contains("SENSITIVE") && !fullWindowJson.Contains("token="),
             "W72 full-window incident report is bounded, filtered and redacted");
    }

    // W75: persistent incident file survives noisy rolling event logs and
    // remains entirely allowlisted without storing log strings or tokens.
    var archiveDir = Path.Combine(folder, "w75-persistent-incidents");
    Directory.CreateDirectory(archiveDir);
    DiagnosticLog.Record("ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED", null, archiveDir);
    DiagnosticLog.Record("ACTIVE_ENTITLEMENT_RECOVERED", null, archiveDir);
    DiagnosticLog.Record("NATIVE_ELECTRON_EVENT_LOOP_STALL", null, archiveDir);
    DiagnosticLog.Record("NATIVE_ELECTRON_MEMORY_HIGH", null, archiveDir);
     DiagnosticLog.Record("PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING", "123", archiveDir);
     DiagnosticLog.Record("PLAYER_CURRENT_NATIVE_VOLUME_DROP", "123", archiveDir);
     DiagnosticLog.Record("PLAYER_CURRENT_SOURCE_LEFT_CELIKOM", "123", archiveDir);
    DiagnosticLog.Record("NATIVE_STATE_RECEIVED", null, archiveDir);
    var preserved = DiagnosticLog.ReadIncidentHistory(archiveDir);
    Test(preserved.Count == 7 &&
         preserved.Any(x => x.Contains("|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED")) &&
         preserved.Any(x => x.Contains("|ACTIVE_ENTITLEMENT_RECOVERED")) &&
          preserved.Any(x => x.Contains("|NATIVE_ELECTRON_EVENT_LOOP_STALL")) &&
          preserved.Any(x => x.Contains("|NATIVE_ELECTRON_MEMORY_HIGH")) &&
          preserved.Any(x => x.Contains("|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING|track=123")) &&
          preserved.Any(x => x.Contains("|PLAYER_CURRENT_NATIVE_VOLUME_DROP|track=123")) &&
          preserved.Any(x => x.Contains("|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM|track=123")),
        "W75/W53/W54 outage, performance and missing-gain incidents are durably archived, not native poll chatter");
    var noisy = string.Concat(Enumerable.Repeat(
        DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ") +
        "|NATIVE_STATE_RECEIVED\n", 3000));
    File.WriteAllText(Path.Combine(archiveDir, "companion-events.log"), noisy);
    var historic = DiagnosticLog.ExportText("5.126.1.0", "ACTIVE",
        true, false, true, "0.24.22", true, archiveDir);
    Test(historic.Contains("PERSISTENT INCIDENT HISTORY") &&
         historic.Contains("|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED") &&
         historic.Contains("|ACTIVE_ENTITLEMENT_RECOVERED"),
        "W75 owner export still contains incident even after thousands of native polls");
    Test(!DiagnosticLog.IsIncidentCode("NATIVE_STATE_RECEIVED") &&
          historic.Contains("|NATIVE_ELECTRON_EVENT_LOOP_STALL") &&
          historic.Contains("|NATIVE_ELECTRON_MEMORY_HIGH") &&
          historic.Contains("|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING|track=123") &&
          historic.Contains("|PLAYER_CURRENT_NATIVE_VOLUME_DROP|track=123") &&
          historic.Contains("|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM|track=123") &&
         !historic.Contains("token=") && !historic.Contains("password="),
        "W75 archived incidents never carry polling chatter or credentials");
    var savedPast = DateTimeOffset.UtcNow.AddHours(-3).ToString("yyyy-MM-ddTHH:mm:ss.fffZ");
    File.WriteAllText(Path.Combine(archiveDir, "incident-events.log"),
        savedPast + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n");
    Test(DiagnosticLog.ReadIncidentHistory(archiveDir).Any(x =>
        x.Contains(savedPast) && x.Contains("|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED")),
        "W75 owner can recover outage history hours after disconnect");
    var stale = DateTimeOffset.UtcNow.AddDays(-8).ToString("yyyy-MM-ddTHH:mm:ss.fffZ");
    File.AppendAllText(Path.Combine(archiveDir, "incident-events.log"),
        stale + "|ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED\n" +
        savedPast + "|ACCESS_TOKEN=SECRET\n");
    Test(DiagnosticLog.ReadIncidentHistory(archiveDir).Count == 1,
        "W75 seven-day cutoff and allowlist reject stale and tampered incident archive");

    Test(snapshot.Contains("EngineFastPauseObserved=") &&
        snapshot.Contains("PlayerAudibleEventObserved=") &&
        snapshot.Contains("DecoderErrorObserved="), "typed owner playback evidence summary");
    Test(snapshot.Contains("PlayerNetworkRequestObserved=") &&
        snapshot.Contains("PlayerNetworkCorsFailureObserved=") &&
        snapshot.Contains("FastPauseTrackAttribution=NOT_AVAILABLE_WITHOUT_PLAYER_TRACK_ID"),
        "real Yandex network evidence remains distinct from playable audio");
    Test(!snapshot.Contains("yandex-drm") && !snapshot.Contains("token="),
        "owner export never leaks native crypto or signed URLs");
    Test(!snapshot.Contains(expectedAccess) && !snapshot.Contains(expectedRefresh) &&
        !snapshot.Contains("test@example.com"), "diagnostics exclude credentials and email");
    Console.WriteLine("W15_NATIVE_CONTRACT_PASS " + checks);
}
finally
{
    if (Directory.Exists(folder)) Directory.Delete(folder, true);
}

static HttpResponseMessage JsonResponse(object value, int status = 200) =>
    new((HttpStatusCode)status) { Content = JsonContent.Create(value) };

sealed class FakeHandler(Func<HttpRequestMessage, HttpResponseMessage> reply) : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken cancellationToken) =>
        Task.FromResult(reply(request));
}

sealed class AsyncFakeHandler(
    Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> reply) : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken cancellationToken) =>
        reply(request, cancellationToken);
}

