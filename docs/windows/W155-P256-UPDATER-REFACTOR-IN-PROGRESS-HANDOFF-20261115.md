# W155 — CELIKOM Windows P-256 updater and final owner package handoff

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Authority: W119 product/architecture rules + W150 owner-approved scope and order.

## 1. Latest verified checkpoint

- W155 application-code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`.
- Exact W155 backup: `backup/windows-main-w155-owner-handoff-20261115` at that SHA.
- W156 owner-package/draft-release code checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd` (documentation-only delivery correction follows).
- Current `main` documentation HEAD before this update: `b876e26bb2bca0f18fe5947ebeafdc22925918fc`.
- Exact backup before this documentation correction: `backup/windows-main-pre-owner-workflow-clarification-20261115` @ `b876e26bb2bca0f18fe5947ebeafdc22925918fc`.
- Exact backup before the 0.24.38 version block: `backup/windows-main-pre-final-owner-release-02438-20261115` at `e3714f8c169ff95a59c6a973e6cdeed8bd2f9bde`.
- Target one-time bootstrap version: **0.24.38**. GUI, Supervisor and Inno installer metadata are aligned.
- Main CI run `43730989562`: **SUCCESS** on `b876e26b`.
- Windows integration CI run `43730989583`: **SUCCESS** on `b876e26b`.
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
- The helper is covered by Main CI contract tests and a Windows PowerShell fixture. The release workflow contract includes the helper. Both CI workflows passed on package checkpoint `23a4ec4a` and latest documentation HEAD `b876e26b`.
- The workflow's production publish input defaults to `false`; leave it false. With this setting the workflow creates the unpublished GitHub Draft Release `celikom-windows-v0.24.38-owner-bootstrap` containing exactly one EXE, one ZIP and `SHA256SUMS.txt`. It does not publish the draft or the `celikom.com` feed.
- The draft remains visible only to repository users with push access until it is published. The repository source itself remains public. The Actions artifact upload step is skipped when `publish_to_production=false`; it runs only for the separately approved live-feed publication path.

**Visibility correction:** the previous workflow revision uploaded the owner package as a GitHub Actions artifact, which would be downloadable by anyone because this repository is public. That was not the intended owner-only handoff. The workflow is now corrected to use an unpublished Draft Release for the owner package.

## 6. Key provisioning and owner interaction — do not request action yet

**No owner action is requested at this checkpoint.** Continue repository-side work and keep the updater fail-closed until a real P-256 key and protected environment configuration exist.

The current helper `.github/scripts/windows-stable-provision-key.ps1` is implementation scaffolding, not an approved owner instruction: it currently requires PowerShell 7+, Node.js 24 and GitHub CLI (`gh`) with repository administration access. Do not tell the owner to install Node.js/GitHub CLI or run this helper. The owner explicitly asked to keep the process on the familiar Windows/PowerShell path and to avoid unnecessary setup.

A protected GitHub Environment secret cannot be created by a normal source commit. Do not pretend it has been provisioned, do not place private material in source/artifacts, and do not ask for passwords, tokens or PEM in chat. Keep the private key unset and the production feed dormant.

Only if key provisioning becomes the single unavoidable external blocker after all repository-side work is finished, request one consolidated owner action. First establish the shortest safe route using the existing GitHub web UI and built-in Windows capabilities; explain each screen/step plainly. Do not require extra developer tooling unless it is proven unavoidable and the owner has agreed. Never ask the owner to disclose the private key to the assistant.

The first bootstrap package is a one-time manual installation over 0.24.37 because that installed version has no P-256 pin. After the bootstrap is installed and DNS/TLS plus the signed feed are activated, subsequent user updates must be detected, verified, downloaded and installed automatically. End users must never need Node.js, GitHub CLI, PowerShell commands, passwords, tokens or signing keys.

When provisioning is eventually complete, the protected workflow uses:
- version: `0.24.38`
- sequence: `1`
- expiry: a valid UTC ISO timestamp within 30 days
- `publish_to_production: false`

The workflow creates an unpublished Windows Draft Release with one EXE, one ZIP and `SHA256SUMS.txt`. Do not publish the draft or production feed.

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
