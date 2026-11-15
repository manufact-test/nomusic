# W155 — CELIKOM Windows P-256 updater: latest owner handoff

Date: 15 November 2026  
Repo: `manufact-test/nomusic`  
Active branch: `main` ONLY  
Task authority: `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md` and `docs/windows/W150-OWNER-CONFIRMED-SCOPE-AND-SEQUENTIAL-WORK-ORDER-20261115.md`.

## Exact verified checkpoint

- Final application-code HEAD before this documentation-only update: `4abcfd5ad389363f4b954eaa578615be91140bee`.
- **Backup created and confirmed:** `backup/windows-main-w155-p256-ci-green-owner-handoff-20261115` @ `4abcfd5ad389363f4b954eaa578615be91140bee`.
- Pre-Task-5 rollback: `backup/windows-main-pre-task5-signed-updater-20261115` @ `2864989bad9520738951cc28806feab6bc0d69c1`.
- Historical pre-last-fix rollback: `backup/windows-main-w155-p256-handoff-pre-ci-fix-20261115` @ `512e18ebefb0e72bc9897fb444c7bc96c956274f`.
- **Current verified CI ON application HEAD:** Main CI `43715919526` SUCCESS; Windows integration CI (no installer) `43715919617` SUCCESS. Prior Windows CI failure `43714007098` at `512e18e` was caused by `CS1501` — a three-argument `IsTrustedRunningImage` call left after the method changed to two arguments. This is fixed in `4abcfd5` and both CI systems pass on that SHA.
- Updating this document changes only handoff documentation; always fetch the new live HEAD before the next engineering commit.

## Completed prior work — do not reimplement

W151 Task 1: current Yandex player/UI heartbeat and queue truth, conservative ORIGINAL/ACTIVE_REPLACEMENT/UNKNOWN; W152 Task 2: VPN A→B redundant original/replacement reload avoidance, retaining fast reconnect; W153 Task 3: autostart/tray and Windows StartupApproved OFF; W154 Task 4: consolidated CI regression and **one grouped owner acceptance plan**. These are code/test/CI-ready, **not yet accepted on the owner's machine**. Plan is `docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md`.

## What Task 5 already implemented

- P-256 manifest-signature trust replacing obsolete Authenticode/PFX; fixed future origin `https://celikom.com/`, public P-256 SPKI pin within release build; empty normal source pins fail closed.
- Immutable signed release manifest **schema 2**, package/payload SHA-256 and same-product/version identity validation; cached/staged artifacts must be re-verified before execution.
- Rollback journal **schema 3**, a separate DPAPI-protected local transaction schema recording the manifest-key fingerprint. Schema 3 is **not** a change to the signed manifest schema.
- AppUpdateManager, Bootstrapper, PackageStager, InstallCoordinator, RollbackJournal, independent UpdateSupervisor and health checks refactored to avoid commercial code-signing and to retain safe-point, supervisor READY and one-shot rollback architecture.
- P-256 keygen, manifest, verifier, protected stable release workflow and publisher scripts changed to use the private key only in protected signing context; workflow has nonpublishing default/explicit `publish_to_production` gate.
- Current code compiles and automation passes both Main and Windows integration CI after the Supervisor call fix. **Do not confuse this with an end-to-end proven live update.**

## Work remaining — strict order

1. **ONLY Task 5.** Re-fetch live main and both latest CI checks; review the entire *actual execution chain*, not just isolated helpers. Check exact P-256 key pin and HTTPS origin, manifest-signature verification, schema 2 vs journal schema 3, SHA-256 of every installer and embedded payload, all cached-package reuse paths, PE identity, downgrade/replay prevention, no ability to run unsigned/tampered code, lock and DPAPI transaction safety.
2. Inspect Supervisor READY/health/rollback with real launch arguments, no-loop rollback and preservation of prior version, account/DPAPI, original Yandex backup, autostart and installed native integration. Add negative and recovery regression cases where needed. Every changed final code HEAD must pass **both** Main and Windows integration CI; code/test/CI completion is prerequisite to Task 6.
3. Validate GitHub protected release pipeline with fixture/offline dry-runs only, no production publisher invocation and no early DNS/TLS activation. Confirm old W148 PFX/Authenticode gates are not required in code, tests, installer scripts or workflow.
4. Prepare owner-controlled offline P-256 private-key generation and secure GitHub protected secret upload. **Never request PEM in chat, log private key material, upload PEM in repo or create public production feed from a fixture.** Only the P-256 public key is embedded in a reviewed final release checkout. Owner's domain is purchased but live HTTPS/feed setup waits for infrastructure migration.
5. **Task 6 only after above:** produce *exactly one* final CELIKOM Windows EXE+ZIP for owner manual bootstrap in place over installed `0.24.37`. Keep existing AppId and Windows warning with option to continue where Windows allows; do not disable security or request admin access. The next signed automatic release will work only after the real production HTTPS feed is live.
6. Owner performs one grouped manual acceptance from W154 on the final build. No intermediate package, no tests requested per tiny change, no claim of field success based solely on CI.

## Guardrails

Only `main`, exact backup before substantial further changes, original architecture and single CELIKOM Windows product. Do not touch Android, extension or unrelated issues #53, #54, #56, #57, #58. #52 remains open until owner-PC current-source acceptance. Preserve 15-minute Yandex version-cache, fast VPN reconnect, sound/source proof, no Yandex autolaunch and no elevated execution. Windows TEST branches/apps prohibited.

**Current overall status:** W151–W154 code/CI-ready; W155 Task 5 **CI green but engineering security audit and production provisioning pending**; Task 6 **not started**. No final EXE/ZIP delivered, no owner-PC change or public feed deployment.
