# W155 — CELIKOM Windows P-256 updater: checkpoint / next developer

Date: 2026-11-15
Repo: manufact-test/nomusic
Working branch: main ONLY
Owner product: one CELIKOM Windows app; installed owner version 0.24.37

## Priority and current truth

W119 product contract + W150 task order are authoritative. W151 (player/UI), W152 (VPN), W153 (autostart), W154 (consolidated code regression/acceptance plan) are code/test/CI-ready from before the updater refactor, but not owner-PC field accepted. W150 Task 5 is the ONLY current work. Task 6 (single final owner EXE+ZIP) has NOT begun.

Current Task-5 development:
- Baseline: 2864989bad9520738951cc28806feab6bc0d69c1.
- Backup of clean Task-5 baseline: backup/windows-main-pre-task5-signed-updater-20261115 at that SHA.
- P-256 refactor commit: 206cc917bb1460757605069d6df6f1b147b5bd99, then f613525d07619b07c449d0d7fd061a8d835bd1ab, 5a4ab4267a35bc911845656970f84a37f7ca1f7b, 86359f8a0f092f48c7bb8003b78314d46a10c674, 5046c5fc35480cef2d0e941f47313a8bfbb57bcb, 512e18ebefb0e72bc9897fb444c7bc96c956274f.
- Exact before last CI-fix handoff: backup/windows-main-w155-p256-handoff-pre-ci-fix-20261115 @ 512e18ebefb0e72bc9897fb444c7bc96c956274f.
- Pre-fix CI for 512e18e: Main CI 43714007399 SUCCESS; Windows integration 43714007098 FAILURE. The first blocking compiler error: Program.cs:33: CS1501: IsTrustedRunningImage call passed 3 arguments while refactored method takes 2. Fixed in the checkpoint containing this handoff by removing the obsolete signer-fingerprint third argument. This fix is NOT yet independently CI-verified at the time of writing. Check latest HEAD and its NEW CI first. Other errors may be hidden by the first compiler failure.

## Code changes implemented, not yet accepted

- StableUpdateTrustConfiguration.cs: build-time public P-256 SPKI, exact https://celikom.com/ origin and SHA-256 public-key fingerprint; no PFX or Authenticode signer pin. Empty checkout production constants deliberately disable auto-update.
- StableUpdateManifestVerifier.cs: signed release manifest remains SCHEMA 2; signature / product / version / sequence / payload hashes must still be verified.
- StableUpdatePackageStager.cs: staged EXE verified against signed manifest's SHA-256, size, PE product/version and exact payload identity fields; no Authenticode trust requirement. Every cached installer must be rechecked before execute. A signed manifest is the authorization, not a download URL alone.
- StableUpdateRollbackJournal.cs / Bootstrapper / InstallCoordinator / AppUpdateManager / Supervisor: switched journal signer pin field to manifest public-key fingerprint; rollback journal SCHEMA 3 (NOT manifest schema); persisted cached previous/target installer hashes, independent supervisor READY, health checks and one-shot rollback remain core. New verified setup filenames used; review every cross-component call for consistency.
- .github/scripts/windows-stable-trust-embed.mjs, windows-stable-manifest.mjs, windows-stable-release-verify.mjs, associated tests: public P-256 key and official origin; release signing via protected PEM only, never in repo/chat/log. Publisher origin fixed to celikom.com.
- .github/workflows/windows-stable-signed-release.yml: outdated commercial PFX/Authenticode stages removed; intended protected signing workflow now has publish_to_production gate, false for offline/fixture preparation. No production execution was performed.
- W150 mandates original app architecture, 15-minute Yandex compatibility feed cache, fast VPN recovery, no automatic Yandex launch, no elevation, strict current-decoder source proof. None may be weakened.

## Remaining engineering — DO NOT SKIP

1. Check live main HEAD and latest CI triggered by this checkpoint. Fix compile errors/tests until BOTH Main CI and Windows integration CI pass on exact final Task-5 source. Do not interpret Main CI alone as completion.
2. Audit the entire production update chain, not just build: signed immutable installed-version bootstrap, signed latest anti-downgrade, exact current version/4 payload hashes, download/re-use revalidation, safe point, DPAPI transaction, Supervisor READY/health, rollback no-loop and retention of login/installed native integration. Journal schema 3 is deliberate; manifest schema 2 remains unchanged. Test negative tampering/unsigned installer cases under the new signature model.
3. Validate protected release workflow and tests with nonproduction fixtures; no real public feed until DNS/TLS migration. P-256 public pin must be embedded only in approved final release checkout. The private key must be generated offline on owner's trusted machine and uploaded to a protected GitHub Actions secret using an authenticated workflow; don't request it in chat.
4. Review release packaging: one installer AppId, coherent GUI/Supervisor/Inno versions, SHA-256 for every payload, rollback per-user, no Authenticode/PFX. Keep the owner's existing Windows warnings (Windows policies may still block unsigned executables).
5. Only when Task 5 passes engineering + CI move to Task 6: produce exactly ONE owner EXE+ZIP for manual bootstrap in-place over 0.24.37. Do not produce test/intermediate installers. No claim of auto delivery until live signed HTTPS feed exists.
6. Single grouped owner manual acceptance is already in docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md. Field tests, including VPN audible click and rollback, remain pending.

## Explicit exclusions

Don't work on #53, #54, #56, #57, #58 or unrelated open issues. #52 remains open for owner validation of source truth. Do not touch Android or browser extension, create Windows TEST, experiment branches, deploy DNS/TLS or weaken Windows security. Keep exact backup and main-only working rules.

## First action

Fetch live main and CI. Inspect compiler error from 43714007098 and verify the new Program.cs fix. Continue Task 5 only, using W150 authority. Save progress with a precise backup and document any new CI failure before any packaging.
