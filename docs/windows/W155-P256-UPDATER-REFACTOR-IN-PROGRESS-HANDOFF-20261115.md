# W155 — CELIKOM Windows P-256 updater and final owner package handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 product/architecture rules + W150 owner-approved scope and order.

## 1. Latest verified checkpoint

- W155 application-code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact W155 backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- W156 owner-package/draft-release code checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- PowerShell-only P-256 key provisioning and runtime public-pin derivation: `b165dc51d934db88cc18aaa0d68fed0c8dd82748`.
- Final workflow-input defaults and release-workflow YAML repair: `bbf964512513cbf9e1942f6598534521c3b7aa69`.
- Exact backup before the PowerShell-only provisioning block: `backup/windows-main-pre-powershell-only-p256-provision-20261115` @ `7c516ad69dbad3f56781a56cd9f7b4ae8c3d7870`.
- Exact backup before release-workflow repair: `backup/windows-main-pre-release-workflow-repair-20261115` @ `6c921032e7dd0d05718e150d9665eab52ba02c23`.
- Exact backup before this documentation update: `backup/windows-main-pre-powershell-owner-handoff-docs-20261115` @ `bbf964512513cbf9e1942f6598534521c3b7aa69`.
- Target one-time bootstrap version: **0.24.38**. GUI, Supervisor and Inno installer metadata are aligned.
- Main CI run `43735322258`: **SUCCESS** on `bbf96451`.
- Windows integration CI run `43735322290`: **SUCCESS** on `bbf96451`.
- W155 signed-release verification: 27/27 at the W155 code checkpoint. Latest Windows integration also passes the Windows PowerShell 5.1 P-256 key-generation smoke test, verifies the generated PKCS#8/SPKI pair, parses the protected release workflow, and runs the full Windows integration suite.
- No final EXE/ZIP has been built or delivered.

## 2. Completed earlier work — do not reopen

W151 Task 1: current Yandex player/UI heartbeat and queue truth, conservative ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN.  
W152 Task 2: VPN A→B reconnect path and avoidance of redundant original/replacement reloads, preserving fast reconnect.  
W153 Task 3: autostart/tray behavior and persistence of deliberate Windows StartupApproved OFF.  
W154 Task 4: consolidated regression coverage and one grouped owner acceptance plan.

W151–W154 are code/test/CI-ready. **They are not owner-PC accepted yet.** The only owner test pass is the single grouped plan in `docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md`, to be run on the one final build. Do not make intermediate installers or ask the owner to test each small patch.

## 3. W155 — updater implementation

- CELIKOM-owned P-256 signed manifest trust replaces the obsolete commercial Authenticode/PFX design. Future fixed origin: `https://celikom.com/`. Only the public P-256 SPKI pin is embedded in a reviewed release build; ordinary source defaults fail closed.
- Signed manifest is schema 2. The separate DPAPI rollback journal is schema 3.
- Package and embedded payload SHA-256 checks, product/version identity checks, bounded file reads, and re-verification of cached/staged artifacts are in place.
- The DPAPI journal binds the transaction to the manifest-key fingerprint and carries sequence/size/hash identity. Corrupt or mismatched journal data is rejected; rollback sequence replay is prevented.
- Independent Supervisor journal reads are bound to the exact transaction and pinned manifest key. Final installer launch is bound to the journaled transaction, signed payload hashes and expected package path.
- Verified-image copy/launch boundaries, reparse-point ancestry and rollback image integrity have focused guards and regression coverage.
- Protected release tooling includes offline P-256 key generation/provisioning, manifest and release verification, bounded signed-feed preflight, and guarded Hostinger publication. Publication uses same-filesystem staging/atomic promotion and refuses changed prior feed bytes, unsafe paths and symlinks.
- Production publication is gated separately and remains OFF. No feed has been published.

## 4. W155 runtime-chain audit — complete

The bounded real caller-chain audit is complete; no concrete runtime gap was found, so no Windows application-code patch was needed. The verified path is recorded in `W156-W155-RUNTIME-CHAIN-AUDIT-AND-P256-PROVISIONING-20261115.md`:

manifest fetch/verification → package/cache/staging → DPAPI transaction → Supervisor READY → installer boundary → independent health → one-shot rollback.

Do not repeat this audit or expand into new research without a concrete failure.

## 5. W156 final owner EXE+ZIP packaging — implemented and CI-tested

- Protected workflow: `.github/workflows/windows-stable-signed-release.yml`.
- The protected Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` is the only private-key source. `.github/scripts/windows-stable-key-public.mjs` derives the public P-256 SPKI pin from that secret at runtime; only the public DER pin is passed to the build and downstream publisher. No public-key Environment variable needs to be entered manually.
- The private PEM is exposed only to the dedicated derive/sign steps, written to a runner-temp file only for signing, then removed. It is never written to the repository, draft assets or job output.
- The workflow builds the installer with the already-committed version, signs/verifies the schema-2 manifest and payload hashes, then runs `.github/scripts/windows-stable-owner-package.ps1`.
- For version 0.24.38, the output is exactly one `CELIKOM-Windows-0.24.38.exe`, one `CELIKOM-Windows-0.24.38.zip` containing that EXE as its sole root entry, and `SHA256SUMS.txt`.
- The package helper refuses overwrite, validates the ZIP entry and byte-for-byte SHA-256 equality, and writes checksums only after successful verification.
- The helper is covered by Main CI contract tests and a Windows PowerShell fixture. The release workflow contract includes the helper. Both CI workflows passed on package checkpoint `23a4ec4a` and latest documentation HEAD `b876e26b`.
- The workflow defaults are version `0.24.38`, sequence `1`, blank expiry (automatically set to a 7-day UTC expiry), and `publish_to_production=false`; leave production publication OFF. With this setting the workflow creates the unpublished GitHub Draft Release `celikom-windows-v0.24.38-owner-bootstrap` containing exactly one EXE, one ZIP and `SHA256SUMS.txt`. It does not publish the draft or the `celikom.com` feed.
- The draft remains visible only to repository users with push access until it is published. The repository source itself remains public. The Actions artifact upload step is skipped when `publish_to_production=false`; it runs only for the separately approved live-feed publication path.

**Visibility correction:** the previous workflow revision uploaded the owner package as a GitHub Actions artifact, which would be downloadable by anyone because this repository is public. That was not the intended owner-only handoff. The workflow is now corrected to use an unpublished Draft Release for the owner package.

## 6. One-time owner key provisioning — no extra software

**No owner action is requested until the repository-side work is complete.** The production updater remains fail-closed and no feed is published.

The owner-facing helper is now `.github/scripts/windows-stable-provision-key.ps1`. It was executed in Windows integration CI under **Windows PowerShell 5.1** and its generated PKCS#8 private key / SPKI public key pair was verified. It uses built-in Windows PowerShell, Windows CNG, Notepad and the browser only. It does **not** require Node.js, GitHub CLI, PowerShell 7, a package manager, tokens or passwords.

Raw script: [windows-stable-provision-key.ps1](https://raw.githubusercontent.com/manufact-test/nomusic/main/.github/scripts/windows-stable-provision-key.ps1)

When this becomes the only remaining external prerequisite, the one consolidated owner action is:

1. Download the raw script above to the Windows **Downloads** folder.
2. Open the built-in Windows PowerShell (not as Administrator) and run:
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\windows-stable-provision-key.ps1"
   ```
3. The script creates one P-256 keypair in `%LOCALAPPDATA%\CELIKOM\StableManifestKey`, restricts the directory ACL to the current user and SYSTEM, opens the GitHub Environment settings page, and opens the private PEM in Notepad. The PEM is never printed to the PowerShell console.
4. In GitHub Environment `windows-stable-production`, verify that **Required reviewers** contains an authorized reviewer and deployment branches are restricted to the single branch `main`. If those protections already exist, leave them unchanged.
5. Add one **Environment secret** named exactly `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`; paste the complete PEM from Notepad into its value and save. Never paste the PEM into ChatGPT, an issue, a commit or a release asset.
6. Keep an encrypted offline backup of the local `StableManifestKey` folder. Close Notepad after the secret is saved.

The release workflow derives the public pin directly from this protected secret. No public-key variable or deploy-root variable is required for the owner bootstrap. `CELIKOM_STABLE_DEPLOY_ROOT` is only needed for the separately gated production-feed publisher after infrastructure migration.

After the secret exists, open [the protected Windows release workflow](https://github.com/manufact-test/nomusic/actions/workflows/windows-stable-signed-release.yml), keep the defaults (0.24.38 / sequence 1 / automatic 7-day expiry / `publish_to_production=false`), and click **Run workflow** on `main`. Approve the protected environment when GitHub requests it. The workflow creates the unpublished Draft Release with one EXE, one ZIP and `SHA256SUMS.txt`. Do not publish the draft or production feed.

The first bootstrap installation over 0.24.37 is necessarily manual because that installed version has no P-256 pin. After the bootstrap is installed and DNS/TLS plus the signed feed are activated, subsequent CELIKOM updates must be detected, verified, downloaded and installed automatically. End users must never need Node.js, GitHub CLI, PowerShell commands, passwords, tokens or signing keys.

## 7. Not done — do not claim otherwise

- Owner-side P-256 private-key provisioning has not yet been run.
- No final EXE/ZIP has been built or delivered; no owner installation or owner-PC acceptance has happened.
- `celikom.com` DNS/TLS and public feed activation remain deferred. No production feed has been published.
- CI and offline fixtures do not prove production update delivery, Windows publisher identity, SmartScreen acceptance, owner-PC installation or a real field rollback.

## 8. Permanent guardrails

- Work only on `main`. Before each substantial code block, create and verify an exact backup.
- Preserve one CELIKOM Windows product and the approved architecture. No Windows TEST product, experimental branches, Android/extension work or unrelated historical Issues #53, #54, #56, #57, #58. #52 remains open until owner-PC source-truth acceptance.
- Do not bypass SmartScreen, Defender, Smart App Control or UAC; do not request elevated execution.
- Preserve the 15-minute Yandex compatibility cache, fast VPN reconnect, strict current-decoder source proof, account/DPAPI state, original Yandex backup, native integration and user settings.
- No intermediate installers, no repeated broad audits, no unnecessary improvements. Finish the one approved owner package, then use the grouped W154 acceptance.
