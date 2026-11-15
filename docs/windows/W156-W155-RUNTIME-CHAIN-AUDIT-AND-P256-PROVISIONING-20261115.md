# W156 — W155 runtime-chain final audit and owner key-provisioning handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 + W150 + W155.

## 1. Result

**W155 runtime implementation is code/test/CI-ready.** The final bounded call-path audit found no concrete implementation gap requiring another runtime patch. No Windows application code was changed by this audit.

- W155 code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact rollback backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- W156 package/draft-release checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- PowerShell-only provisioning / derived P-256 public pin checkpoint: `b165dc51d934db88cc18aaa0d68fed0c8dd82748`.
- Current release-workflow checkpoint: `bbf964512513cbf9e1942f6598534521c3b7aa69`.
- Exact backup before the provisioning change: `backup/windows-main-pre-powershell-only-p256-provision-20261115` @ `7c516ad69dbad3f56781a56cd9f7b4ae8c3d7870`.
- Exact backup before release-workflow repair: `backup/windows-main-pre-release-workflow-repair-20261115` @ `6c921032e7dd0d05718e150d9665eab52ba02c23`.
- Main CI run `43735322258`: **SUCCESS** on `bbf96451`.
- Windows integration CI run `43735322290`: **SUCCESS** on `bbf96451`.

CI proves code and regression contracts only. It does not prove production feed delivery, owner-PC installation, Windows trust UI, or real rollback.

## 2. Verified real runtime chain

1. **Entry and dormant trust:** `MainWindow.CheckStableUpdateIfSafeAsync` calls the single `StableUpdateInstallCoordinator`. The coordinator and scheduler both fail closed while the build-pinned production origin/public key are empty. No feed request, download, or installer launch occurs in the current source build.
2. **Manifest and anti-replay:** the coordinator authenticates the installed-version immutable manifest with the build-pinned P-256 key, compares installed GUI/native/renderer/Supervisor bytes, reads the DPAPI LKG sequence, then fetches and verifies the latest signed schema-2 manifest. The current-version bootstrap manifest is allowed to outlive its offer window; the latest offer is still expiry-checked.
3. **Package/cache/staging:** the coordinator calls `FetchOrReusePendingAsync`; the stager enforces the immutable official package URL, bounded size, SHA-256 and CELIKOM PE identity. Reused cache entries are reverified. The package is verified again before the transaction copy.
4. **Durable transaction:** `PrepareManifestVerified` captures the existing session fingerprint when present, verifies previous and target installers and all four payload hashes, copies both installers into a transaction-specific snapshot, and writes DPAPI journal schema 3 with transaction ID, manifest-key fingerprint, sequence, sizes, hashes and rollback state.
5. **Supervisor READY:** `StableUpdateSupervisorLauncher.StartAsync` checks the journal/key/transaction, verifies the installed previous Supervisor hash, snapshots that exact image and holds a no-write/no-delete verified handle through process creation. READY is accepted only from the exact launched process ID on the transaction-specific current-user pipe. The Supervisor independently reads DPAPI state and validates the same transaction, key fingerprint and running image before READY.
6. **Installer boundary:** after READY, the coordinator rechecks the no-playback-interruption safe point, advances `Prepared → InstallerStarted`, resolves the journaled target path, and re-verifies the package. `AppUpdateManager.LaunchManifestVerified` re-reads the journal and checks transaction, phase, path, version, sequence, size, package hash, key fingerprint and GUI/native/renderer/Supervisor hashes. It re-verifies and holds the exact package image without write/delete sharing through process creation.
7. **Independent health:** the Supervisor checks the installed GUI, native host, renderer and Supervisor against signed manifest hashes; confirms the expected running CELIKOM process, authenticated local bridge, preserved DPAPI session identity when one existed, and native integration when it was installed. Installer launch alone cannot mark the new version healthy.
8. **One-shot rollback:** after health timeout, rollback is queued only from the journal's allowed phases. The Supervisor refuses to interrupt Yandex or terminate a running CELIKOM process; it waits for a safe stop and then enters ManualRecovery after the bounded deferral rather than force-killing. The previous installer is reverified against the DPAPI-bound hash/size, rollback attempt 1 is persisted before launch, and the launcher hashes the exact image again at the execution boundary. A failed rollback becomes ManualRecovery; a second automatic attempt is impossible.

The no-force-kill behavior is intentional and covered by the W110 Supervisor contract. It is not a promise that a still-running hung process will be forcibly closed.

## 3. One-time P-256 key setup — built-in Windows PowerShell only

No owner action is requested while repository-side work remains. The approved local helper is `.github/scripts/windows-stable-provision-key.ps1`. Windows integration CI runs it under Windows PowerShell 5.1 and verifies the generated PKCS#8 private key against its SPKI public key.

- No Node.js, GitHub CLI, PowerShell 7, package manager, token or password is required on the owner PC.
- The helper saves the private key outside the repository under `%LOCALAPPDATA%\CELIKOM\StableManifestKey`, with the directory ACL restricted to the current Windows user and SYSTEM.
- It opens the GitHub Environment settings page and Notepad with the private PEM; the key is never printed to the console.
- The owner adds the PEM once as the protected Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`. The release workflow derives the public pin from that secret, so no public-key variable is needed.
- Exact owner steps and the PowerShell command are in section 6 of `W155-P256-UPDATER-REFACTOR-IN-PROGRESS-HANDOFF-20261115.md`. Never ask the owner to send the PEM, password or token in chat.

The GitHub Environment `windows-stable-production` must have at least one authorized required reviewer and a deployment branch policy allowing exactly `main`. Verify those settings in the GitHub UI before adding the secret. Do not weaken or bypass the protection.

## 4. Remaining external/release work

- Owner-side private-key provisioning has **not** yet been run.
- `celikom.com` DNS/TLS and public feed are still deliberately deferred.
- No production feed has been published.
- No final EXE/ZIP has been built or delivered; no owner-PC installation or field acceptance has happened.
- The current W20 internal staging workflow does not embed the production P-256 pin and must not be used for the final bootstrap. The protected `windows-stable-signed-release.yml` is the approved trust-embedding build path.
- W156 added the owner-package helper to that workflow. It produces one EXE, one root-entry ZIP containing the same EXE, and SHA256SUMS; the helper and release contract pass Main CI and Windows integration CI.
- Target bootstrap version is 0.24.38. GUI, Supervisor and Inno metadata are aligned. Main CI run 43735322258 and Windows integration CI run 43735322290 both SUCCESS on release-workflow checkpoint bbf96451.
- Repository visibility was rechecked: `manufact-test/nomusic` is public. Existing Releases are two unpublished Android test drafts; there is no Windows 0.24.38 release yet.
- The first workflow version incorrectly sent the owner package to a public Actions artifact. This has been corrected: with `publish_to_production=false`, the workflow creates the Draft Release `celikom-windows-v0.24.38-owner-bootstrap` with exactly `CELIKOM-Windows-0.24.38.exe`, `CELIKOM-Windows-0.24.38.zip` and `SHA256SUMS.txt`. GitHub draft releases are listed only for users with push access; the public repository itself remains public. The Actions artifact upload step is skipped for this owner-bootstrap path.
- Main CI run `43730538279` and Windows integration CI run `43730538242`: **SUCCESS** on code checkpoint `23a4ec4a232139b9cfea986dec629d1d9b8776dd`, including the new draft-release contract test.
- After the owner adds the one protected Environment secret using the PowerShell-only procedure, the assistant commits the one-shot marker `.github/release/owner-bootstrap-0.24.38.trigger` to `main`. The path-filtered workflow starts automatically with version 0.24.38, sequence 1, automatic 7-day UTC expiry and `publish_to_production=false`; the owner only approves the protected environment if GitHub requests it. It creates the unpublished Draft Release; then run the single grouped W154 owner acceptance. Do not click Run workflow manually, publish the draft or create intermediate packages.

## 5. Guardrails

Only `main`; exact backup before substantial changes; one CELIKOM Windows product; no Authenticode/PFX; no SmartScreen/Defender/UAC bypass; no early DNS/TLS/feed publication; no Android/extension work; no historical Issues #53/#54/#56/#57/#58. #52 remains open until owner-PC acceptance.
