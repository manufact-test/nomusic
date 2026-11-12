# W84 experimental — passive decoder source witness (2026-11-13)

**Status:** CI-green source investigation, NOT a release. Do NOT install over owner 0.24.28 before the scheduled listening QA.

## What was broken
W81 incorrectly treated no transition-only heartbeat for 30 sec as no connection; W82 fixed that visible false alarm. But W82 still only knows a signed grant **was handed off**, not whether Yandex's real media player selected and started decoding that exact source. Owner demanded reliable telemetry rather than false red/yellow messages. Issue [#52](https://github.com/manufact-test/nomusic/issues/52) remains **OPEN** until genuine host playback verification.

## W84 experiment in `experiment/windows-w84-readonly-player-source-evidence-20261113`

- Origin: W83 promo fix branch @ `bd9a01188d81fe470e0f1efaea8e98edfdaafc4a`; exact pre-experiment rollback `backup/windows-w84-pre-evidence-w83-green-20261113`.
- `windows-companion/w23/host.cjs`: extends existing **passive** CDP Media observer. Only record `PLAYER_DECODER_CELIKOM_SOURCE_MATCHED` if one exact CDP player's `kUrl` matches the **in-memory, signed, unexpired CELIKOM grant URL**, its `kIsPlaying` is true, AND the expected Yandex track ID matches the actual renderer current track ID. Not emitted for arbitrary HTTP 200/206, queued/prefetched next track, a stored grant, a mismatched signed token, unknown URL, or non-current audio player.
- Explicitly attributed `Media.playerErrorsRaised` for the same source/track emits `PLAYER_DECODER_CELIKOM_PIPELINE_ERROR`; generic unrelated error stays generic. These codes go only to allowlisted, bounded owner diagnostics. Never log URLs, tokens, player IDs, cookies, account data, or audio contents.
- No changes to player commands, pause/seek, grant transformation, native Yandex installer, original host/renderer interop. No new user-facing banners/colours.
- `native-host.test.mjs` tests signed current kUrl, no duplicate spam, no raw URLs, unknown original source, modified signature, prefetch different track, correlated pipeline errors and proofless generic failures.
- CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/43311056109 (CDP witness + renderer unchanged tests + native bundle build).

## What this does *not* prove
The CDP URL/`kIsPlaying` pair is stronger than file-info/HTTP activity but not proof of audible speakers; Yandex may use another decoder or hide `kUrl`, and crossfade/preload needs live owner testing. The app must stay **neutral/quiet** when no evidence exists. Do NOT change user UI green/red solely on one CDP network event. Keep issue #52 open.

## Next stage
After 0.24.28 owner confirms stable music:
1. Isolate native source witness experiment in disposable official Yandex builds; confirm CDP actually emits `kUrl` in relevant 2026 versions and that current-track attribution is robust.
2. Extend tests for pause, seek, crossfade, cache, next, offline, error, sleep/wake and multi-player.
3. Only after proved and reviewed, integrate a bounded minimal source-evidence indicator (or leave it in owner diagnostics) while retaining quiet UI.

The independently tested lifetime promo flicker fix lives in `experiment/windows-w83-promo-steady-entitlement-20261113`, doc `docs/windows/W83-PROMO-ENTITLEMENT-NO-BLINK-20261113.md`, CI https://github.com/manufact-test/nomusic/actions/runs/43310069470.
