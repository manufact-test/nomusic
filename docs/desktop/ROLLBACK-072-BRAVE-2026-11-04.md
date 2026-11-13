# Desktop 0.4.72 — withdraw experimental live adoption after Brave closure

Owner reports on 2026-11-04 that approving an uploaded song while listening on 0.4.71 closed the entire Brave window and all tabs. Treat this as a severe regression report. No Brave crash report or failing full diagnostic is available; do not claim that native browser crash, memory exhaustion, or another precise cause is proven. Chrome CI success did not establish Brave compatibility.

0.4.71 is WITHDRAWN. Do not recommend another real-owner approval stress test or reuse its positive synthetic test result as release acceptance.
0.4.70 is accepted only for intro behavior; its live-approval changes had already failed owner testing. Do not recommend 0.4.70 as a complete rollback for this scenario.

## Conservative rollback

Restore `extension/src/player/replacement-player.ts` byte for byte from desktop 0.4.69 (local historical commit 78a2ec5, remote final 3e4371da38151f06cad52adbcf2317ef427ceee3).
Delete the controller's `prepareJoin` / `joinPrepared` branch and experimental retry classification. Restore legacy guard-then-sync adoption from before 0.4.70, including forced initial sync. No new decoder or speculative playback mechanism is substituted.
Keep 0.4.70 MAIN bounded-intro hold, adapter wrappers, lease renewal and all intro regressions unchanged. Sync engine, original guard, worker/auth and server are unchanged. Android is untouched.
Version bump to 0.4.72 permits clear identification of the rollback package. Isolated branch: `feature/desktop-072-revert-live-join-20261104`. Do not update stable server branch or deploy backend changes.

## Verification and limits

351 desktop regressions PASS locally. Byte comparison proves ReplacementPlayer equals the pre-experiment file; no MAIN/adaptor/sync/guard source changes. Replace rejected-method tests with a regression that forbids `prepareJoin` invocation and requires legacy guard/sync activation. All earlier startup/pause/seek/authority tests stay enabled.
Remove experimental Chrome live-join scenarios dependent on withdrawn method; retain existing native playback, seeking, original restore, and bounded intro checks. Dedicated CI must pass before delivery. This is a rollback of suspect code, not proof of the cause of the entire Brave closure.

## Owner recovery

First disable CELIKOM in `brave://extensions`. Install rollback by replacing the existing unpacked folder, reload extension, refresh Yandex, then enable deliberately; no uninstall or clearing account data. Do not ask owner to repeat approval while playing until the browser incident has been reviewed. If a local Brave crash entry exists in `brave://crashes`, its timestamp/status or report identifier can help establish whether the browser recorded a crash; no need to upload a raw memory dump.
