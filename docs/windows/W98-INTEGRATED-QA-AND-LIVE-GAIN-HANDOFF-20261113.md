> **OPERATIONAL STATUS SUPERSEDED BY W100 — 2026-11-13.** This file is retained for W98 design history and implementation details. Its opening W99 note saying the owner secret is missing is obsolete: `CELIKOM_W98_TEST_EMAIL` is now present and the owner-only preflight passed in run [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358). Do not ask the owner to add or disclose it again. GUI 0.24.35 details below are historical; current candidate is GUI 0.24.36 / native 0.24.29. Read [W100 final release handoff](W100-0.24.36-FINAL-TEST-RELEASE-HANDOFF-20261113.md) first.

---

## W99 current status — 2026-11-13

This document records the W98 design and is now superseded operationally by [W99-0.24.36-INTEGRATED-QA-STATUS-20261113.md](W99-0.24.36-INTEGRATED-QA-STATUS-20261113.md). Current branch HEAD is `b1f9064edfc33b83e08abe22e7d38a0a87298e59`; GUI 0.24.36 / native 0.24.29 / W23 0.24.10. Exact Windows CI [43470332842](https://github.com/manufact-test/nomusic/actions/runs/43470332842) and W91 sidecar CI [43469841569](https://github.com/manufact-test/nomusic/actions/runs/43469841569) passed. Hostinger verify/package passed, but deploy stopped at the owner-account preflight because `CELIKOM_W98_TEST_EMAIL` is not configured. No snapshot, deploy, migration 020, sidecar registration or audio write occurred. Owner must add the repository Actions secret with the primary CELIKOM account email before the guarded deployment can continue. No final installer has been published.

---

# W98 — Integrated Windows QA and live gain activation (2026-11-13)

## Current branch and rollback

- Repository: `manufact-test/nomusic`.
- Work branch: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
- Last code HEAD with full W98 CI SUCCESS: `696e36b65c2a5accaa0e5c6c8aeb7548611932f1` (always re-fetch the branch before continuing).
- Exact pre-W98 backup: `backup/windows-w98-pre-integrated-gain-and-original-vpn-20261113` @ `5ce1ec127009ba4a86a8e5ee1d129ec86623fd54`.
- W95 input branch remains unchanged: `experiment/windows-w95-02434-qa-candidate-20261113` @ `5ce1ec127009ba4a86a8e5ee1d129ec86623fd54`.
- Do not reset or modify W95/W89 backups. Browser extension source under `extension/` was not modified by W98.

## Version prepared

- Windows GUI candidate: **0.24.35**.
- Native bridge version: **0.24.28**.
- W23 package version: **0.24.9**.
- The installer definition keeps the existing AppId and installs only CELIKOM GUI + W23 host/renderer. It does not bundle or replace Yandex vendor files.
- A single final workflow is prepared to build EXE + updater ZIP + SHA256 manifest, run in-place W89→0.24.35 DPAPI-preservation checks, and upload one GitHub artifact. It does not install on the owner's PC.

## Implemented in W98

### Issue #58 — original track transparency during VPN/entitlement transitions

- W22 now tracks per-track source classification: `ORIGINAL`, `UNKNOWN`, replacement candidate, and actual mapped replacement.
- W23 no longer reloads/recreates a current original track merely because VPN or entitlement state changed. A confirmed original or unknown source remains untouched.
- If the exact current track had actually been mapped to a CELIKOM replacement, the existing narrow source-refresh path can restore Yandex original on disable/denial. On re-enable, the authenticated resolver is queried first; only a fresh replacement grant permits replacement reload.
- Async state transitions are generation-guarded so stale route responses cannot act on a later track/state.
- Added W22 and W23 regression coverage for authoritative original/no-match, transient unknown, no `QUALITY_CHANGE` on original VPN disable/re-enable, and pause/position preservation.
- W23 also bounds passive Chromium Network buffers and briefly caches the bridge capability-file read to reduce repeated synchronous disk work. This is passive diagnostics/performance work, not an audio-source rewrite.

CI regression is not owner acoustic QA. The owner must still verify #58 on «Моей волне» and ordinary original songs.

### #56 — Windows-only private gain sidecar pipeline

- Kept the Chrome extension and original browser audio path unchanged.
- Reuses W91 signed Windows-only `audio_profile=windows_gain_v1`, source/version/gain/hash/duration-bound sidecars, scoped HMAC, and signed Range delivery.
- Added private Hostinger operator helper to re-inventory active approved nonzero-gain rows, verify original SHA, stream source bytes only to ephemeral runner scratch, and run the offline FFmpeg renderer there. Private rendered files are uploaded only to private Hostinger staging; they are not committed, placed in ordinary artifacts, or printed in logs.
- Added batch rollback CLI with explicit rollback authorization. The batch runner records every attempted insert and rolls back newly created variants if a later render/stage/live verification fails.
- Hostinger snapshot/restore gates include the additive `windows_gain_variants` table.
- Live inventory is not hardcoded to Big City Life: all currently active approved rows with nonzero gain are discovered at run time. Prior read-only audits found one active nonzero-gain track, Big City Life / Триагрутрика `40371622` at +11.5 dB; the disabled «Папиросы» row at +12 dB is not staged.
- The workflow verifies live signed HTTPS Range (206), entitlement, variant identity, ETag and `gain_applied=true` before allowing the final installer job.

**Important: production migration 020 and real sidecars have NOT been activated yet.** The first Hostinger attempt, run [43454991506](https://github.com/manufact-test/nomusic/actions/runs/43454991506), stopped at the pre-deploy snapshot with “Stale workflow revision” because the branch advanced while that run was starting. The deploy step and gain-staging job were skipped. No production migration or media rows were changed by that run. Re-trigger only from a fresh exact branch HEAD after all gates are satisfied.

**Owner account explicitly authorized:** the owner approved using his own primary CELIKOM account identified by email. The exact address is intentionally not committed to the repository or written to logs. The remote helper reads it from SSH stdin, resolves only the matching `users.email`, selects only that user's non-revoked, unexpired session, and then checks the current server entitlement. It never enumerates or borrows another customer's session.

- GitHub Actions requires the repository secret `CELIKOM_W98_TEST_EMAIL` containing the owner's CELIKOM email address. The GitHub connection used for this work cannot create repository secrets; the owner must add it once in **Settings → Secrets and variables → Actions → New repository secret**.
- The Hostinger deploy job checks that the secret is present before snapshot/deploy/migration. The private staging job passes the value over SSH stdin, not as a command-line argument. The remote helper validates the email and queries `users.email = ?`.
- No numeric user ID is needed. If the account has no current active session or server entitlement, the live check fails closed. No migration or media staging should run until the secret is configured and the preflight passes.

## CI evidence

- W93 disposable MariaDB/FFmpeg integration: [43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979) SUCCESS (synthetic audio only; not live Hostinger media).
- W93 CLI syntax/dry-run audit: [43455603847](https://github.com/manufact-test/nomusic/actions/runs/43455603847) SUCCESS.
- W91 signed-sidecar contract CI: [43456768892](https://github.com/manufact-test/nomusic/actions/runs/43456768892) SUCCESS.
- Full W98 integration CI [43457943838](https://github.com/manufact-test/nomusic/actions/runs/43457943838) SUCCESS on code SHA `65c2aba287183c655cbb89deed05f3029addca15`: Linux extension/server package build, Windows repo checks, W23 bundle, W22/W23/W60 audio regressions, W21 recovery, W24 ASAR/catalog, W15 entitlement/login/native-state tests, GUI warnings-as-errors compile.
- The first W98 CI failures were runner-only: the Unix `zip` executable was invoked on Windows, then PowerShell's reserved `$Host` variable was overwritten. The pipeline was split so packaging runs on Linux; the reserved variable was renamed. Both corrections are covered by the successful W98 run above.
- Latest owner-email-scoped W98 run [43462340493](https://github.com/manufact-test/nomusic/actions/runs/43462340493) **SUCCESS** on code SHA `696e36b65c2a5accaa0e5c6c8aeb7548611932f1`: Hostinger workflow YAML parsed, private gain PHP/Bash syntax and email-only session guard passed, Linux extension/server package build passed, and all Windows W22/W23/W60, W21, W24, W15 tests plus GUI warnings-as-errors compile passed.
- The Hostinger final installer job now waits for the W98 Windows CI run for the exact same commit SHA; it must not package a different or unverified source revision.

## Still open — do not claim solved from CI

- #52 «Ты» / Yandex track `89285816`: decoder/source proof still requires owner listening.
- #53 Brave/Windows lag: passive diagnostics and reduced buffer retention are present; no measured owner profile proves the root cause fixed.
- #54 Big City Life mid-track volume drop: separate from admin gain parity; no owner trace has proven why the alternative suddenly gets quieter.
- #56 admin gain: sidecar pipeline is prepared but live migration, media rendering, registration and signed Range verification remain pending.
- #57 hiss after CELIKOM 403→206: W96 guard remains; owner acoustic QA is pending.
- #58 original-track VPN pop: regression is covered in code/CI, but owner field QA remains pending.
- VPN reconnect speed: no owner A→B timing confirmation yet.
- Do not install anything on the owner's computer or issue a partial installer.

## Next actions

1. Owner adds the one-time GitHub Actions repository secret `CELIKOM_W98_TEST_EMAIL` containing the already-authorized primary CELIKOM email. The GitHub connection cannot create repository secrets; use **Settings → Secrets and variables → Actions → New repository secret**. Do not commit the email or print it in logs.
2. Confirm the owner-account preflight passes. It runs before Hostinger snapshot, deploy, or migration; if the secret is absent/invalid, the live workflow stops without changing production.
3. After the secret exists, update `.github/deploy/hostinger-request.json` to a fresh one-shot request and trigger private Hostinger deployment from the exact current branch SHA.
4. Confirm Stage 5 snapshot/restore checks, migration 020 checksum, every active nonzero-gain sidecar, offline audio measurements, and real signed HTTPS Range 206 for each row. Confirm rollback remains usable.
5. Wait for exact-commit W98 Windows CI success; build the single 0.24.35 EXE + ZIP; verify ZIP CRC and both SHA256 values; upload to `/CELIKOM/Windows/Test/`.
6. Update this document, `W97-FINAL-READY-RELEASE-HANDOFF-20261113.md`, and `NEXT-CHAT.md` with final exact commits, CI, artifacts, checksums, and rollback. Owner then performs one combined real-PC listening/functional QA pass.
