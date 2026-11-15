# W155 — CELIKOM Windows P-256 updater: current owner handoff

Date: 15 November 2026  
Repository: manufact-test/nomusic  
Only working branch: main  
Authority: W119 product/architecture rules + W150 owner-approved scope and order.

## 1. Latest exact checkpoint

- Application-code checkpoint: **c1afdd5fc9b3ec90bb760857bf584dc494d7774e**.
- Exact backup created before this handoff: **backup/windows-main-w155-owner-handoff-20261115** at the same SHA.
- Pre-Task-5 rollback point: backup/windows-main-pre-task5-signed-updater-20261115 @ 2864989bad9520738951cc28806feab6bc0d69c1.
- This checkpoint contains 65 commits after the previous 4abcfd5 checkpoint. The commits are W155 updater hardening and its regression coverage; no new product or branch was introduced.
- **Main CI:** run 43726310918 — SUCCESS on c1afdd5.
- **Windows integration CI (no installer):** run 43726310792 — SUCCESS on c1afdd5.
- **W155 signed-release verification:** 27/27 tests passed, including offline Hostinger promotion rehearsal, signed-baseline race rejection, oversized-package rejection, symlink rejection, exact origin/key constraints and publisher path guards.
- No installer was built. The two documentation updates after this checkpoint may move main HEAD; the next chat must fetch live main HEAD and latest checks before any code change.

## 2. Completed earlier work — do not reopen

W151 Task 1: current Yandex player/UI heartbeat and queue truth, conservative ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN.  
W152 Task 2: VPN A→B reconnect path and avoidance of redundant original/replacement reloads, preserving fast reconnect.  
W153 Task 3: autostart/tray behavior and persistence of deliberate Windows StartupApproved OFF.  
W154 Task 4: consolidated regression coverage and one grouped owner acceptance plan.

W151–W154 are code/test/CI-ready. **They are not owner-PC accepted yet.** The only owner test pass is the single grouped plan in docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md, to be run on the one final build. Do not make intermediate installers or ask the owner to test each small patch.

## 3. W155 — what is now implemented

- CELIKOM-owned P-256 signed manifest trust replaces the obsolete commercial Authenticode/PFX design. Future fixed origin: https://celikom.com/. Only the public P-256 SPKI pin is embedded in a reviewed release build; ordinary source defaults fail closed.
- Signed manifest remains **schema 2**. Required fields and JSON shape are checked explicitly; the URL must match the exact immutable versioned CELIKOM installer path. Do not confuse this with the separate **schema 3 DPAPI rollback journal**.
- Package and embedded payload SHA-256 checks, product/version identity checks, bounded file reads, and re-verification of cached/staged artifacts are in place.
- The schema 3 DPAPI journal binds the transaction to the manifest-key fingerprint and carries sequence/size/hash identity. Corrupt or mismatched journal data is rejected; rollback sequence replay is prevented.
- Independent Supervisor journal reads are bound to the exact transaction and pinned manifest key. Final installer launch is bound to the journaled transaction, signed payload hashes and expected package path. An abandoned Prepared transaction expires to ManualRecovery without launching an installer.
- Verified-image copy/launch boundaries, reparse-point ancestry and rollback image integrity have additional guards and regression coverage.
- Protected release tooling now includes offline P-256 key generation/provisioning, manifest and release verification, bounded signed-feed preflight, and guarded Hostinger publication. The publisher uses same-filesystem staging/atomic promotion and refuses changed prior feed bytes, unsafe paths and symlinks.
- The protected workflow has an explicit production-publish gate. Fixture/offline publication rehearsal is covered by CI; it did not publish to celikom.com.

## 4. Exact remaining work — stay inside W155

Do not start a new broad investigation. Continue with one bounded final pass through the actual runtime chain:

1. Follow the real call path from signed manifest fetch/verification → package staging and cache reuse → InstallCoordinator → AppUpdateManager launch → independent Supervisor READY/health → one-shot rollback. Confirm the new transaction/key/hash bindings are used by the real callers and that rollback cannot loop or execute a substituted image.
2. Patch only a concrete gap found in that path; add its focused regression test. Do not rework already-green keygen, manifest, publisher or path-hardening areas without a failing test or demonstrated defect.
3. Run both Main CI and Windows integration CI on the resulting exact code HEAD. Keep release fixture tests green. CI is not proof of a live production update or owner-PC acceptance.
4. Finish the owner-safe provisioning instructions: generate the P-256 private key on an owner-controlled machine and upload it directly to the protected GitHub Actions environment secret. Never ask for PEM in chat, print it, commit it, or place it in repository-level secrets. Embed only the public key in the final reviewed release build.
5. Only after Task 5 is code/test/CI-ready, proceed to Task 6: build **exactly one** final CELIKOM Windows EXE+ZIP for manual bootstrap over installed 0.24.37. Then the owner performs the single grouped W154 acceptance.

## 5. Not done — do not claim otherwise

- No owner private signing key has been provisioned to the protected GitHub environment.
- No production signed feed has been published; celikom.com DNS/TLS/feed activation remains deferred until infrastructure migration.
- No new EXE/ZIP has been built or delivered; no owner installation or owner-PC audio/UI acceptance has happened.
- CI success and offline publisher rehearsal do not prove a live update, Windows publisher identity, SmartScreen acceptance or a field rollback.

## 6. Permanent guardrails

- Work only on main. Before each substantial code block, create and verify an exact backup.
- Preserve one CELIKOM Windows product and the approved architecture. No Windows TEST product, experimental branches, Android/extension work or unrelated historical Issues #53, #54, #56, #57, #58. #52 remains open until owner-PC source-truth acceptance.
- Do not bypass SmartScreen, Defender, Smart App Control or UAC; do not request elevated execution.
- Preserve the 15-minute Yandex compatibility cache, fast VPN reconnect, strict current-decoder source proof, account/DPAPI state, original Yandex backup, native integration and user settings.
- No intermediate installers, no tiny-step owner chores, no unnecessary exploratory detours. Finish one bounded block, verify it, then move forward.


## 7. Final runtime-chain audit — W156

The bounded W155 runtime-chain audit is complete. No concrete runtime gap was found, so no application-code patch was made. The actual caller chain, transaction/key/hash propagation, Supervisor READY/health and one-shot rollback are recorded in `docs/windows/W156-W155-RUNTIME-CHAIN-AUDIT-AND-P256-PROVISIONING-20261115.md`.

The owner-side provisioning script is ready: `.github/scripts/windows-stable-provision-key.ps1`. Run it once from the repository root on the trusted Windows PC using PowerShell 7+, Node 24 and authenticated GitHub CLI. It validates the protected `windows-stable-production` environment, required reviewer and main-only policy; generates a P-256 keypair locally; stores the private PEM outside the repository with restricted ACL; sets the three public environment variables; and uploads only `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` as an environment secret. The exact command, prerequisites and handling rules are in W156. Never send the private PEM in chat.

**W155 code/test/CI work is complete, but production trust is not provisioned.** No production feed, final EXE/ZIP, owner installation or owner-PC acceptance exists yet. Task 6 remains one final pinned EXE+ZIP after owner-side key provisioning; the current W20 internal stage is not an approved final build path because it does not embed the P-256 pin. The protected `windows-stable-signed-release.yml` path must produce the single EXE, one-root-entry ZIP and SHA-256 checksums with production publication OFF.
