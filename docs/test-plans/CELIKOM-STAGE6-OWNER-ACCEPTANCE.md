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
