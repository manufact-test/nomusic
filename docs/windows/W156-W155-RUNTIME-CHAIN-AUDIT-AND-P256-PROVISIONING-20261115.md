# W156 — W155 runtime-chain final audit and owner key-provisioning handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 + W150 + W155.

## 1. Result

**W155 runtime implementation is code/test/CI-ready.** The final bounded call-path audit found no concrete implementation gap requiring another runtime patch. No Windows application code was changed by this audit.

- Code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact rollback backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- W156 package/draft-release code checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- Current `main` documentation HEAD before this update: `b876e26bb2bca0f18fe5947ebeafdc22925918fc`.
- Exact backup before this documentation correction: `backup/windows-main-pre-owner-workflow-clarification-20261115` @ `b876e26bb2bca0f18fe5947ebeafdc22925918fc`.
- Main CI run `43730989562`: **SUCCESS** on `b876e26b`.
- Windows integration CI run `43730989583`: **SUCCESS** on `b876e26b`.
- W155 release verification recorded at checkpoint: 27/27. The Windows integration run also reports `W15_NATIVE_CONTRACT_PASS 399` and `W110_INDEPENDENT_SUPERVISOR_CONTRACT_PASS 30`.

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

## 3. Key provisioning and owner interaction — pending, no action requested now

The current helper `.github/scripts/windows-stable-provision-key.ps1` exists and has regression coverage, but it is **not an approved owner-facing procedure**. It currently requires PowerShell 7+, Node.js 24 and GitHub CLI (`gh`) with repository administration access. Do not ask the owner to install these tools or run this helper.

No owner action is requested now. Keep the private P-256 key unset and production updater fail-closed while continuing all repository-side work. A protected GitHub Environment secret cannot be created by an ordinary source commit; do not claim otherwise, do not place private material in the repository or release assets, and never ask for passwords, tokens or PEM in chat.

If key provisioning remains the only unavoidable external blocker after repository-side work is complete, request one consolidated owner action only then. Prefer the existing GitHub web UI and built-in Windows/PowerShell capabilities; explain the exact screens and steps plainly. Do not require additional developer tooling unless it is proven unavoidable. The owner must never disclose the private key to the assistant.

The one-time bootstrap installation over 0.24.37 is unavoidable because that installed version has no P-256 pin. After that single bootstrap, and after DNS/TLS plus the signed feed are activated, all subsequent user updates must be automatic. End users must not install Node.js/GitHub CLI, run PowerShell commands, enter passwords/tokens, or handle signing keys.

When the protected key is eventually provisioned, the existing release workflow parameters remain version `0.24.38`, sequence `1`, a valid UTC expiry within 30 days, and `publish_to_production=false`.

## 4. Remaining external/release work

- Owner-side private-key provisioning has **not** yet been run.
- `celikom.com` DNS/TLS and public feed are still deliberately deferred.
- No production feed has been published.
- No final EXE/ZIP has been built or delivered; no owner-PC installation or field acceptance has happened.
- The current W20 internal staging workflow does not embed the production P-256 pin and must not be used for the final bootstrap. The protected `windows-stable-signed-release.yml` is the approved trust-embedding build path.
- W156 added the owner-package helper to that workflow. It produces one EXE, one root-entry ZIP containing the same EXE, and SHA256SUMS; the helper and release contract pass Main CI and Windows integration CI.
- Target bootstrap version is 0.24.38. GUI, Supervisor and Inno metadata are aligned. Main CI run 43730989562 and Windows integration CI run 43730989583 both SUCCESS on current documentation HEAD b876e26b.
- Repository visibility was rechecked: `manufact-test/nomusic` is public. Existing Releases are two unpublished Android test drafts; there is no Windows 0.24.38 release yet.
- The first workflow version incorrectly sent the owner package to a public Actions artifact. This has been corrected: with `publish_to_production=false`, the workflow creates the Draft Release `celikom-windows-v0.24.38-owner-bootstrap` with exactly `CELIKOM-Windows-0.24.38.exe`, `CELIKOM-Windows-0.24.38.zip` and `SHA256SUMS.txt`. GitHub draft releases are listed only for users with push access; the public repository itself remains public. The Actions artifact upload step is skipped for this owner-bootstrap path.
- Main CI run `43730538279` and Windows integration CI run `43730538242`: **SUCCESS** on code checkpoint `23a4ec4a232139b9cfea986dec629d1d9b8776dd`, including the new draft-release contract test.
- After a safe one-time provisioning route is agreed and completed, run `windows-stable-signed-release.yml` on `main` with version 0.24.38, sequence 1, a valid UTC expiry within 30 days, and `publish_to_production=false`. Approve the protected environment. The workflow creates the unpublished Draft Release; then run the single grouped W154 owner acceptance. Do not publish the draft or create intermediate packages.

## 5. Guardrails

Only `main`; exact backup before substantial changes; one CELIKOM Windows product; no Authenticode/PFX; no SmartScreen/Defender/UAC bypass; no early DNS/TLS/feed publication; no Android/extension work; no historical Issues #53/#54/#56/#57/#58. #52 remains open until owner-PC acceptance.
