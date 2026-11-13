# CELIKOM Windows W76 — per-track parity and misleading status (2026-11-12)

## Scope and verified owner reports

Owner tested the existing CELIKOM Windows app **0.24.21.0**, with native module **0.24.20**. Global status said the integration worked, but some songs used the censored original while the browser extension used the approved audio.

- **тринадцать карат — «ты»** / Yandex track ID `106040459`: production catalog's approved, active MP3 is replacement **56** (asset 109,009 ms, listed 108,980 ms). Owner's first incident showed a local `LOCAL_HTTP_TIMEOUT` and failure to relay its approved grant; original stream was therefore not replaced for that request. App and native host had a fixed fast 1000 ms local timeout.
- **Триагрутрика — «Биг сити лайф»** / Yandex track ID `40371622`: approved active MP3 replacement **37** (asset 231,120 ms, listed 232,450 ms, within 1.5 s compatibility tolerance). Owner's 2026-11-12 11:18 UTC diagnostic contains a real native media request to resource 37 with `PLAYER_URL_EXPIRED_AT_REQUEST`, `PLAYER_NET_HTTP_FORBIDDEN` (403), then another GET with intact signed fields and 206, plus native `SOURCE_MAPPED` for track 40371622. **Neither 206 nor SOURCE_MAPPED proves which audio is audible.** The report that original audio was heard stands; do not infer the second 206 restored audible replacement.
- Other sampled catalog IDs `27323616` (CENTR — «Зима») and `144530503` (10AGE, Ramil' — «Ау») had active approved replacements.
- Remote read-only production audit confirmed current PHP release `browser-support-076-b807cd691074`: **1499** tracks recorded, **1493** with approved active replacement, no observed duplicate/partial catalog variants in the query. This is NOT a measurement of playback success for all 1493 tracks. Audit: [GitHub Actions #43206771868](https://github.com/manufact-test/nomusic/actions/runs/43206771868).

## W76 implementation, 0.24.23

Working branch: `experiment/windows-w76-track-parity-audit-20261112`.
Unchanged starting point backup: `backup/windows-w76-pre-track-specific-audit-20261112` at `94a743d3196f2bebc880360329a65a208ebc37f5`.

1. **Transient local timeout is not a missing song.** `host.cjs` and `BridgeServer.cs` distinguish a temporary local/HTTP 5xx failure from an authoritative not-found/denial. Foreground Next/source selection retains its fast deadline, while background recovery has a separately bounded transport budget and no negative-cache poisoning.
2. **Current-track-only retry.** `windows-companion/w23/transient-source-recovery.mjs` tries up to two bounded refreshes only while the exact observed Yandex track is still active. Once an approved signed grant arrives, invokes existing native `reloadEntity("QUALITY_CHANGE")` through `current-source-refresh`; no alternate music player, queue manipulation or account handling. Change/Stop/logout cancels the retry.
3. **Expired signed media link / 403.** The existing passive native CDP observer correlates an already-approved resource and an actual expired media GET 403, then requests recovery only for the corresponding currently playing Yandex track. A duplicate expired-range 403 cannot create more than one recovery cycle per track per minute. Never processes 403s for unrelated resources or blindly retries other tracks.
4. **Status wording truthful.** GUI now says CELIKOM is **enabled** rather than pretending each song is successfully replaced. `SOURCE_MAPPED` is described as the source **delivered but audible playback not proven**. `NATIVE_RECOVERING` and `NATIVE_SOURCE_FAILED` statuses describe expired-URL recovery and failure, rather than `CELIKOM работает` for every case.
5. Test files `native-resource-adapter.test.mjs`, `transient-source-recovery.test.mjs`, `renderer-relay.test.mjs` cover transient vs genuine miss, duplicate requests, Next, Stop, stale track, expired current source and preserving native player's position/pause. Existing Windows .NET/UI/native tests and a single Inno installer are built by `.github/workflows/windows-w76-track-recovery-installer.yml`.

## Production protection and remaining uncertainty

**No production PHP/API changes, no production DB writes, no audio files/uploads changed, no music library or payment changes.** Tests are synthetic on CI Windows. We do **not** have access to owner's actual audible Yandex output or local installation; the W76 repair must not be called owner-accepted until a human listens to both tracks on the upgraded application.

The owner's installed app 0.24.21/native 0.24.20 cannot use W76 fixes until a new build is applied and the native Yandex module is refreshed by the existing consented single-app update flow. W76 stays separate from the current stable branch and may be rolled back to the unchanged W75 starting point if needed.

## Manual acceptance

After green CI, install the exact W76 single-app artifact and allow its normal native-module refresh. Confirm app version **0.24.23** and matching native assets in GUI; press Start. Play «ты» (106040459), then «Биг сити лайф» (40371622) against the extension, especially where censorship was heard. Verify same song after normal Next, pause, seek, and repeat near a signed-link expiry. Test real songs with no catalog replacement stay original without repetitive reload. If a song remains censored, export fresh native diagnostic while playing; distinguish expired/403, transient/not-found, source-mapped/206 and actual audible result. Do not claim it is solved from CI alone.
