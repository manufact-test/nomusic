# W155 — CELIKOM Windows P-256 updater and final owner package handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 product/architecture rules + W150 owner-approved scope and order.

## 1. Latest verified checkpoint

- W155 application-code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact W155 backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- Final owner release-version checkpoint before this documentation update: `718861a6b9a1ee3e01c190f49d7d7b75a3062465`.
- Exact backup before the 0.24.38 version block: `backup/windows-main-pre-final-owner-release-02438-20261115` at `e3714f8c169ff95a59c6a973e6cdeed8bd2f9bde`.
- Target one-time bootstrap version: **0.24.38**. GUI, Supervisor and Inno installer metadata are aligned.
- Main CI run `43728931911`: **SUCCESS** on `718861a6`.
- Windows integration CI run `43728931891`: **SUCCESS** on `718861a6`.
- W155 signed-release verification: 27/27 at the W155 code checkpoint. The current Windows CI also passes the P-256 key-provisioning script parse, owner EXE/ZIP fixture, GUI/Supervisor compile and the full existing Windows integration suite.
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
- It embeds only the protected environment's public P-256 pin into the release build; private PEM is read from the protected environment secret and removed from the runner workspace after signing.
- The workflow builds the installer with the already-committed version, signs/verifies the schema-2 manifest and payload hashes, then runs `.github/scripts/windows-stable-owner-package.ps1`.
- For version 0.24.38, the output is exactly one `CELIKOM-Windows-0.24.38.exe`, one `CELIKOM-Windows-0.24.38.zip` containing that EXE as its sole root entry, and `SHA256SUMS.txt`.
- The package helper refuses overwrite, validates the ZIP entry and byte-for-byte SHA-256 equality, and writes checksums only after successful verification.
- The helper is covered by Main CI contract tests and a Windows PowerShell fixture. The release workflow contract includes the helper. Both CI workflows passed on `718861a6`.
- The workflow's production publish input defaults to `false`; leave it false. This creates an owner bootstrap artifact only and does not publish to `celikom.com`.

**Artifact visibility note:** `manufact-test/nomusic` is a public GitHub repository. GitHub Actions artifacts are downloadable by anyone with repository read access; do not describe this artifact as private. The artifact contains no private signing key—only the installer, ZIP, signed manifest material and public key. If owner-only distribution is required, stop before dispatch and arrange separate private storage; no such storage is currently configured.

## 6. One remaining owner action — provision P-256 once

Run this once on the trusted Windows PC, from the updated repository root:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .github/scripts/windows-stable-provision-key.ps1
```

Prerequisites: PowerShell 7+, Node.js 24, GitHub CLI authenticated with admin access, and the protected `windows-stable-production` environment with at least one required reviewer and a custom deployment policy allowing exactly `main`.

The script checks the environment and refuses unsafe policy, generates P-256 locally only when no key exists, stores the private PEM outside the repository under `%LOCALAPPDATA%\CELIKOM\StableManifestKey` with ACL restricted to the current user and SYSTEM, sets the public origin/key/deploy-root variables, and uploads the PEM only as the environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`. It prints only the public fingerprint.

Send back only the success line and public fingerprint. **Never send the PEM in chat, issue, commit or artifact.** Keep an encrypted offline backup of the private key.

After successful provisioning, run the protected workflow on `main` with:
- version: `0.24.38`
- sequence: `1`
- expiry: a valid UTC ISO timestamp within 30 days
- `publish_to_production: false`

The workflow requires the protected environment approval. Download its one artifact after success; it contains the single EXE, ZIP and checksums.

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
