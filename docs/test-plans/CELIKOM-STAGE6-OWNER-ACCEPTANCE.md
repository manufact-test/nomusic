# CELIKOM — Stage 6.7 owner-only acceptance protocol

Authority: CELIKOM Master TZ MVP v1.5, Work Plan MVP v1.6. Stage 6 is not accepted based on CI alone. This document authorizes no live changes.

## Existing baseline

- Repo manufact-test/nomusic; feature/api-range; PR #6 open, never merge without permission.
- Stage 6.6 CI 37918863810 passed 78/78 JS, MySQL, concurrency, HTTP Range and native Chromium playback.
- Live Hostinger release 0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c (server package version 0.4.4, API 0.4.0); owner's Chrome extension still runs the previously installed 0.4.4 build. Previously observed private library 1 Track / 1 AudioAsset / 1 mapping, reviewed Yandex Track ID 144530503, Replacement ID 1, 180872ms.
- No new media or private credentials are required. Stage 5 on-host snapshot is not an independent offsite backup.

## Controlled gate

1. Read-only Hostinger /config and library-inspect, no DB writes: verify counts and flags unchanged, no private path or token exposed.
2. Confirm SHA-pinned server/extension CI artifact, checksums and actionable rollback/snapshot plan; keep reviewed MP3 and mapping unchanged.
3. Obtain explicit owner approval before deploying a new server release, altering the installed Chrome extension, or modifying the production catalog.
4. With the Stage 6 build installed under owner control, use TWO independent browser profiles/installations on the same existing approved Track ID. Verify proper signed Range playback, pause/play/seek/next, stop/manual-original, refresh after server cache TTL on a subsequent resolve, and unknown ID original fallback. Do not infer mid-track hot swapping from TTL.
5. Verify no per-500ms resolution requests, no leaks, safe fail-open after disabled extension/API failure, and readiness to roll back to existing 0.4.4.

Public uploads, account access, subscriptions and moderation admin remain later stages. Do not merge PR #6 without explicit permission.

## Stage 6.7 read-only baseline (2026-10-09)

[GitHub Actions 37919329751](https://github.com/manufact-test/nomusic/actions/runs/37919329751) completed successfully using pinned SSH and the read-only private library inspection: **1 Track, 1 AudioAsset, 1 TrackReplacement**; public API replacements enabled, analytics disabled. No database writes, music uploads or Hostinger deploy were performed. The workflow request has been returned to safe local-only `validate`. This alone does **not** constitute full 6.7 acceptance; private deployment/upgrade and owner-observed two-installation browser tests remain gated by express authorization.

## Stage 6.7 authorized deployment and browser handoff (2026-10-09)

- Fresh private owner-only backup: [37919980695](https://github.com/manufact-test/nomusic/actions/runs/37919980695) — copied env + 1 media object + six SQL tables; stored outside public_html.
- Separate file/SQL restore drill: [37920125314](https://github.com/manufact-test/nomusic/actions/runs/37920125314) — private files and disposable MySQL restore verified; live tables untouched.
- Owner-authorized immutable Hostinger deployment: [37920299328](https://github.com/manufact-test/nomusic/actions/runs/37920299328) — active server 0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c, PHP 8.3, HTTPS/API/CORS check passed. Previously active 0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d retained for rollback.
- Post-deploy integrity: [37920496968](https://github.com/manufact-test/nomusic/actions/runs/37920496968) — shared env SHA-256, every audio SHA-256, six SQL table counts and approved mapping match the pre-deploy snapshot; replacements on, analytics off.
- Actual approved 180872ms MP3: [37920657691](https://github.com/manufact-test/nomusic/actions/runs/37920657691) — authorized HTTPS resolve, signed 206 bytes 0–1023/4345176, CORS for Yandex, HEAD and feature flags passed. No media/SQL writes.
- Owner-only Hostinger-configured Chrome package: [37920985864](https://github.com/manufact-test/nomusic/actions/runs/37920985864) — build from b81fec2f171d99a48d789ed04219da7c3a57becb, baseUrl and host permissions verified, ZIP SHA-256 check passed. Artifacts retained 14 days; ZIP contains no API bearer token.

**No final owner-browser acceptance yet.** Download the private ZIP artifact from Actions run 37920985864. Extract the outer GitHub Actions archive, then extract `celikom-extension-0.4.4.zip` into a private folder containing `manifest.json`. Use a separate Chrome profile, open `chrome://extensions`, enable Developer mode, choose Load unpacked and select the inner extracted folder. Confirm only one CELIKOM is active per profile. Keep the existing signed API token inside the browser extension's own UI; never put it in GitHub/ChatGPT. Refresh the Yandex Music tab after installing. Test both profiles on the existing approved Track 144530503; also test an unmapped track (original playback), play/pause/seek/next, Stop and Return original. Positive/negative cache changes require a subsequent resolve after TTL and do not hot-swap mid-track.

The private on-host snapshot is not off-provider disaster recovery. Installed Chrome code does not update automatically from GitHub Actions; do not infer owner acceptance from green CI or server tests. PR #6 stays open/unmerged.

## 2026-10-09 — Chrome History hook recursion hotfix (owner validation pending)

Owner reported three `Uncaught RangeError: Maximum call stack size exceeded` entries in Chrome extension Errors, traced to `player/main-world-bundle.js` `celikomObservedHistory` around line 1044 and intermittent Yandex Music SPA blank `Application error` / frozen page when returning to an old tab. Root cause identified in `YandexMusicAdapter` lifecycle: wrapper used mutable `adapter.nativeHooks[name]` as its native target. If a third-party/Yandex wrapper retained CELIKOM's wrapper through unmount, on remount the registry could point back into the old wrapper chain and recurse. The source also used this mutable-hook pattern for media, fetch and XHR.

Fix [1d69906](https://github.com/manufact-test/nomusic/commit/1d69906aa04cf7704a89eab9342dd5d73ab936e0): each wrapper closes over its immutable original target and has a per-installation `lifecycle.active` flag; retained stale wrappers stay callable but no longer emit snapshots or inspect the network after unmount. Two regression tests reproduce third-party History wrap/unmount/remount and retained fetch/media functions. [CI 37926905183](https://github.com/manufact-test/nomusic/actions/runs/37926905183) green: **80/80 JS** plus PHP/disposable MySQL/native Chromium. [Hostinger-configured hotfix package 37927113445](https://github.com/manufact-test/nomusic/actions/runs/37927113445) assembled with valid ZIP SHA and exact private API origin; no server redeploy. Workflow/last documentation CI [37927119332](https://github.com/manufact-test/nomusic/actions/runs/37927119332) green.

**Next:** owner replaces files in existing unpacked CELIKOM folder, uses Reload in `chrome://extensions`, closes/reopens Yandex Music tabs, clears past Chrome Errors and exercises navigation, tab-background/foreground, play/pause/seek, Stop/Return original. A blank-page error in Yandex is a plausible consequence of History recursion, not conclusively attributed until owner reproduces or confirms gone. Stage 6.7 browser acceptance remains **pending**; do not merge PR #6 or change existing music/DB. Extension manifest version remains `0.4.4` to preserve established unpacked-install identity; the hotfix is distinguished by Git commit and artifact.

## Closure decision and carry-over (2026-10-09)

Stage 6.1–6.6 code and automated security/regression gates are complete. Stage 6.7 server deployment / private data integrity and signed Range playback checks passed. The owner installed the configured Chrome extension and tested normal playback for ~30 minutes with no visible SPA freezes. **The formal Stage 6 owner acceptance remains OPEN**: two independent profiles have not been demonstrated in this chat. After clearing old errors, the owner also observed another `Uncaught RangeError: Maximum call stack size exceeded` in `player/main-world-bundle.js`, now highlighted near `YandexMusicAdapter.restorePrototypeHooks()` (~bundle line 1044). No observed playback failure in that session, but root cause is unknown. Track and investigate [GitHub issue #7](https://github.com/manufact-test/nomusic/issues/7); do not dismiss as harmless or blame Yandex without evidence.

The user agreed to proceed with Stage 7 planning and development on isolated/synthetic fixtures while this non-blocking-in-current-playback observation is tracked. This **does not waive the required two-profile Stage 6 gate, authorize production uploads, or close issue #7**. Stage 7 plan: [CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md](CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md).
