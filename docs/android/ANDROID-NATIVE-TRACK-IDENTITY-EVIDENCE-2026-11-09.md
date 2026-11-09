# Track ID in native Yandex — evidence gate (09.11.2026)

Owner asks whether CELIKOM will be able to discover a track ID when the player
runs, without a separate player. This static gate distinguishes three claims:
(1) Yandex has a real `trackId` in its native API, (2) the currently audible
track+edition can be associated with the real FileInfo request, and (3) CELIKOM
can safely bind that identity to a single native source before prepare.

Evidence already shown for (1): signed #170gpr native `DownloadInfoApi` route
`tracks/{trackId}/download-info`. This is a *download endpoint*, NOT proof
that active playback FileInfo receives the same track ID.

New CI checks exact signed five-split APK, six DEX, Retrofit route annotations,
FileInfo/DownloadInfo method signatures, DTO model type shapes, and selected
static identifier names. No source values, account, URL, key, token, app-private
state, login, runtime hook, or vendor APK publication.

Accept (2) **ONLY** after real read-only, in-process source selection witness
provides strong correlation among playback request identity, edition, generation,
and the MediaSource that Yandex actually prepares. The currently installed
official Yandex is untouched. In particular, a MediaSession display ID alone
is not authoritative proof of `trackId` for source swap. No late transitions,
blind guessing or cross-edition fallback allowed.

Next after real Android native-host runtime: read-only counters and typed
identity shape match in exact #170gpr process; no request/token logging.
Only then integrate `NativeSourceGate` with exact trackId + edition before
prepare (single original Yandex player).

## Supplemental signed evidence and test implementation — 09.11.2026

Published-signer verified #170gpr static CI [42609347093](https://github.com/manufact-test/nomusic/actions/runs/42609347093) already showed real Retrofit routes and signatures:
- `DownloadInfoApi.b(String,Boolean,Boolean,String): Call` → `tracks/{trackId}/download-info`. This proves a typed download-path argument, but NOT that the same ID corresponds to the audible native source.
- `FileInfoApi.a(String,String,String,String,long,String,Integer,Integer,String): Call` → `resources/v2/file-info`.
- `OldFileInfoApi.a(String,String,String,String,long,String,Integer,Integer,String,String): Call` → `get-file-info`.
- `Lhee.a` calls the actual `FileInfoApi.a` in signed DEX [42609598200](https://github.com/manufact-test/nomusic/actions/runs/42609598200); the exact semantic meaning of those string arguments, track+edition pairing, and relation to a playing MediaSource remain NOT OBSERVED.

A new independent read-only static audit `android/native-yandex-hooklab/audit_native_track_identity_static.py` checks method signatures, matching routes, DTO shapes, static identifier labels and Retrofit parameter annotations **only for approved track/album/identity labels**. It deliberately ignores credentials, URLs, cookies, headers, arbitrary string values and files. Never confuse its PASS with native audio or live track-ID detection.

At handoff, first new action run [42673655477](https://github.com/manufact-test/nomusic/actions/runs/42673655477) marked FAILURE but had **zero jobs** according to GitHub REST (`total_count:0`), so there is no source test result and no error trace to attribute to code. Updated audit run [42674235050](https://github.com/manufact-test/nomusic/actions/runs/42674235050) was queued when recorded; do not claim a static PASS unless actual job logs show one. The repository code is saved. No need to re-run the already passed owner AUDIO SMOKE.

**Track ID product contract:** trackId + edition (and playback generation) must be correlated to native source-before-prepare. UI MediaSession display metadata or the download ID alone cannot be trusted as exact source identity; stale events after Next are rejected. Unknown identity => original native Yandex source, not an arbitrary CELIKOM match. A second MediaPlayer is forbidden.
