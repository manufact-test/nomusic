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
