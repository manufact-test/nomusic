# W156 — W155 runtime-chain final audit and owner key-provisioning handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 + W150 + W155.

## 1. Result

**W155 runtime implementation, W156 package workflow and owner provisioning route are code/test/CI-ready.** The final bounded caller-chain audit found no concrete implementation gap requiring another runtime patch. No Windows application-code change is needed.

- Current `main` documentation HEAD before this handoff update: `0a2df7d5d104854c492dc7114ec6c4175a195df8`.
- Current code/release-workflow checkpoint with the one-shot trigger: `44a3e55ed9e70a4f2aa4b3ac562c122575f0a189`.
- W155 application-code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- W156 package/draft-release checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- Exact backup before this documentation handoff: `backup/windows-main-pre-final-handoff-docs-20261115` @ `0a2df7d5d104854c492dc7114ec6c4175a195df8`.
- Main CI run `43736028010`: **SUCCESS**. Windows integration CI run `43736027854`: **SUCCESS** on `0a2df7d5`.
- The Windows integration CI includes the Windows PowerShell 5.1 P-256 key-generation smoke test, verifies the generated PKCS#8/SPKI pair, parses the protected release workflow and runs the full Windows integration suite.

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

## 4. Final release result and remaining owner acceptance

- Owner-side P-256 key provisioning is **complete**. The private key is stored only in the protected Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` under `windows-stable-production`. The workflow derived the public pin and matched the owner's public fingerprint. Never request or expose the private PEM.
- The first protected release attempt failed only because the generated expiry timestamp omitted the milliseconds required by canonical `Date.toISOString()`. The workflow now generates/parses UTC timestamps with exactly three fractional digits. A precise backup was kept before the fix, and the existing one-shot marker was updated once to trigger the corrected workflow; no version or sequence change was made.
- Final release workflow run `43741752502`: **SUCCESS** on source commit `bc59e0c7e4db749d616b318beb89369245811b44`. Main CI run `43741752582` and Windows integration CI run `43741752579`: **SUCCESS**.
- Final bootstrap: Draft Release `celikom-windows-v0.24.38-owner-bootstrap`, release ID `446239144`, version `0.24.38`, sequence `1`, automatic seven-day UTC expiry, `publish_to_production=false`.
- GitHub verified exactly these three Draft Release assets:
  - `CELIKOM-Windows-0.24.38.exe` — 85,140,627 bytes.
  - `CELIKOM-Windows-0.24.38.zip` — 84,660,767 bytes.
  - `SHA256SUMS.txt` — 198 bytes.
- The owner-package helper verifies that the ZIP has exactly one entry named `CELIKOM-Windows-0.24.38.exe` at the archive root, that its length and SHA-256 match the installer, and that the checksum file records the EXE and ZIP hashes. The successful protected workflow and release contract also verify the exact three-asset set and asset sizes. The public Actions artifact upload was skipped.
- **Only remaining work:** the owner downloads and installs this single bootstrap over 0.24.37, then completes the one grouped W154 acceptance. No intermediate packages or additional engineering tasks.
- `celikom.com` DNS/TLS and signed production-feed activation remain deliberately deferred. Keep this release as an unpublished Draft; no production feed was published and no production automatic update delivery is claimed.

## 5. Guardrails

Only `main`; exact backup before substantial changes; one CELIKOM Windows product; no Authenticode/PFX; no SmartScreen/Defender/UAC bypass; no early DNS/TLS/feed publication; no Android/extension work; no historical Issues #53/#54/#56/#57/#58. #52 remains open until owner-PC acceptance.
