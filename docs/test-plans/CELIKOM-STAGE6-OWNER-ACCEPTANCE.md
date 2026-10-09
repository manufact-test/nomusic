# CELIKOM — Stage 6.7 owner-only acceptance protocol

Authority: CELIKOM Master TZ MVP v1.5, Work Plan MVP v1.6. Stage 6 is not accepted based on CI alone. This document authorizes no live changes.

## Existing baseline

- Repo manufact-test/nomusic; feature/api-range; PR #6 open, never merge without permission.
- Stage 6.6 CI 37918863810 passed 78/78 JS, MySQL, concurrency, HTTP Range and native Chromium playback.
- Current live Hostinger 0.4.4, extension 0.4.4. Previously observed private library 1 Track / 1 AudioAsset / 1 mapping, reviewed Yandex Track ID 144530503, Replacement ID 1, 180872ms.
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
