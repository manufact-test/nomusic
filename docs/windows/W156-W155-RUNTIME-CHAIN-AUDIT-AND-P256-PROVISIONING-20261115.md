# W156 — W155 runtime-chain final audit and owner key-provisioning handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 + W150 + W155.

## 1. Result

**W155 runtime implementation is code/test/CI-ready.** The final bounded call-path audit found no concrete implementation gap requiring another runtime patch. No Windows application code was changed by this audit.

- Code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact rollback backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- Current documentation HEAD at audit: `ae92a973c9602ecb1f285f23d9968f5dd2a7cc2b`.
- Compare confirms exactly two commits after the code checkpoint, both documentation-only: `NEXT-CHAT.md` and this W155 handoff.
- Code-checkpoint Main CI: run `43726310918` SUCCESS.
- Code-checkpoint Windows integration CI: run `43726310792` SUCCESS.
- Current documentation-HEAD Main CI: run `43726850931` SUCCESS.
- Current documentation-HEAD Windows integration CI: run `43726850944` SUCCESS.
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

## 3. Owner-side P-256 provisioning — one command

The provisioning script already exists and is covered by regression tests:

`.github/scripts/windows-stable-provision-key.ps1`

Run once on the owner's trusted Windows PC, from the repository root, after updating `main`.

Prerequisites:
- PowerShell 7+.
- Node.js 24.
- GitHub CLI (`gh`) authenticated as an account with admin access to the repository's protected environment.
- `icacls.exe` (standard Windows component).
- The GitHub environment `windows-stable-production` must already have at least one required reviewer and a custom deployment branch policy allowing exactly `main`. The script checks this and refuses to proceed if it is not true.

Command:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .github/scripts/windows-stable-provision-key.ps1
```

The script:
- Generates one P-256 keypair locally only if no keypair/production pin already exists.
- Stores the private PEM outside the repository at `%LOCALAPPDATA%\CELIKOM\StableManifestKey\manifest-private.pem`, with ACL restricted to the current user and SYSTEM.
- Sets protected-environment variables `CELIKOM_STABLE_ORIGIN=https://celikom.com`, `CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64`, and `CELIKOM_STABLE_DEPLOY_ROOT`.
- Uploads the private PEM only as environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`. It refuses a repository-level secret and refuses silent key rotation.
- Verifies the public/private pair locally and confirms that the environment secret name and public variables exist. It prints only the public-key fingerprint, never the PEM.

Keep an encrypted offline backup of the private key. Do not paste, upload to chat, commit, or otherwise disclose the PEM. If the script reports an unprotected/missing environment, stop and have the repository administrator configure the required reviewer and main-only policy; do not weaken the check.

## 4. Remaining external/release work

- Owner-side private-key provisioning has **not** yet been run.
- `celikom.com` DNS/TLS and public feed are still deliberately deferred.
- No production feed has been published.
- No final EXE/ZIP has been built or delivered; no owner-PC installation or field acceptance has happened.
- The current W20 internal staging workflow does not embed the production P-256 pin and must not be used for the final bootstrap. The protected `windows-stable-signed-release.yml` is the approved trust-embedding build path.
- W156 added the owner-package helper to that workflow. It produces one EXE, one root-entry ZIP containing the same EXE, and SHA256SUMS; the helper and release contract pass Main CI and Windows integration CI.
- Target bootstrap version is 0.24.38. GUI, Supervisor and Inno metadata are aligned. Main CI run 43728931911 and Windows integration CI run 43728931891 both SUCCESS on checkpoint 718861a6.
- `manufact-test/nomusic` is public, so Actions artifacts are available to anyone with repository read access. Do not call the artifact private. It contains no private key. If owner-only distribution is required, arrange separate private storage before dispatch.
- After the owner provisions the key, run `windows-stable-signed-release.yml` on `main` with version 0.24.38, sequence 1, a valid UTC expiry within 30 days, and `publish_to_production=false`. Approve the protected environment, download the one artifact, then run the single grouped W154 owner acceptance. Do not create intermediate packages.

## 5. Guardrails

Only `main`; exact backup before substantial changes; one CELIKOM Windows product; no Authenticode/PFX; no SmartScreen/Defender/UAC bypass; no early DNS/TLS/feed publication; no Android/extension work; no historical Issues #53/#54/#56/#57/#58. #52 remains open until owner-PC acceptance.
