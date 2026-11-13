# W98 — Integrated Windows QA and live gain activation (2026-11-13)

## Current branch and rollback

- Repository: `manufact-test/nomusic`.
- Work branch: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
- Current documented HEAD at this handoff: `df49afe6b725b2c6b977a6ea2c9d9638f0785223` (always re-fetch the branch before continuing).
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

**Live session safety gate:** the live Range check must use one explicit owner-approved CELIKOM test account with an active authenticated session. Do not scan/select an arbitrary customer's active session. Before running the live stage, change the helper/workflow to accept an explicit test user ID via a protected Actions secret and query only that user, then require a valid active session and current server entitlement. If no dedicated test account exists, ask the owner which account is explicitly authorized. Do not run the current broad session-selection code.

## CI evidence

- W93 disposable MariaDB/FFmpeg integration: [43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979) SUCCESS (synthetic audio only; not live Hostinger media).
- W93 CLI syntax/dry-run audit: [43455603847](https://github.com/manufact-test/nomusic/actions/runs/43455603847) SUCCESS.
- W91 signed-sidecar contract CI: [43456768892](https://github.com/manufact-test/nomusic/actions/runs/43456768892) SUCCESS.
- Full W98 integration CI [43457943838](https://github.com/manufact-test/nomusic/actions/runs/43457943838) SUCCESS on code SHA `65c2aba287183c655cbb89deed05f3029addca15`: Linux extension/server package build, Windows repo checks, W23 bundle, W22/W23/W60 audio regressions, W21 recovery, W24 ASAR/catalog, W15 entitlement/login/native-state tests, GUI warnings-as-errors compile.
- The first W98 CI failures were runner-only: the Unix `zip` executable was invoked on Windows, then PowerShell's reserved `$Host` variable was overwritten. The pipeline was split so packaging runs on Linux; the reserved variable was renamed. Both corrections are covered by the successful W98 run above.
- After the final Hostinger-workflow CI-gate changes, exact-current-head W98 run [43458387990](https://github.com/manufact-test/nomusic/actions/runs/43458387990) was queued at `df49afe6b725b2c6b977a6ea2c9d9638f0785223`. Verify its final conclusion before continuing.
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

1. Verify exact current W98 CI run [43458387990](https://github.com/manufact-test/nomusic/actions/runs/43458387990) is SUCCESS.
2. Obtain explicit owner approval and exact test account ID; modify live verification to query only that account and fail closed if it has no active session/current entitlement.
3. Add PHP/Bash syntax checks for all W98 remote helpers to the no-deploy CI, then run the deployment verify job.
4. Update `.github/deploy/hostinger-request.json` to a fresh one-shot request only after the account gate is in place; trigger the private Hostinger deployment from the exact current branch SHA.
5. Confirm Stage 5 snapshot/restore checks, migration 020 checksum, all active nonzero-gain sidecars, offline audio measurements, and real signed HTTPS Range 206 for each row. Confirm rollback path remains usable.
6. Wait for exact-commit W98 Windows CI success; build the single 0.24.35 EXE + ZIP; verify ZIP CRC and both SHA256 values; upload to `/CELIKOM/Windows/Test/`.
7. Update this document, `W97-FINAL-READY-RELEASE-HANDOFF-20261113.md`, and `NEXT-CHAT.md` with final exact commits, CI, artifacts, checksums, and rollback. Owner then performs one combined real-PC listening/functional QA pass.
