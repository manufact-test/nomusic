# CELIKOM Android — next-track lookahead prefetch experiment — 2026-11-02

## Owner priority

Song beginnings and transitions are the primary task. Do not deliver or request a separate cosmetic login-text APK. This is an isolated audio experiment; the previous candidate remains available for comparison.

## Evidence

Latest diagnostic pair: CELIKOM-combined-20261102-172508.txt and SVID_20261102_172353_1.mp4. The run records six cold-join starts. Five replacement joins occur approximately 1.98–4.78 seconds after the next-item boundary; full-file downloads take approximately 1.18–3.99 seconds. The lookahead observer saw the next Media3 item roughly 7–14 seconds before several boundaries, but metadataComplete remained false and no prefetch was authorized. Media3 also reported brief STATE_BUFFERING periods near boundaries. The mixed system recording shows low/silent intervals but cannot attribute all of them exclusively to Yandex or CELIKOM.

## Experiment

Use only the current Media3 timeline already available to CELIKOM. Do not add Yandex MediaBrowser/library access, notification access, Accessibility, or account scraping.

1. Read the next item from the existing MediaController timeline and Timeline.Window.
2. Use MediaMetadata.durationMs when available; otherwise use Timeline.Window.durationMs.
3. Require a real non-placeholder window, non-empty title and artist, a validated album ID from artwork URI, and a positive duration.
4. Require CELIKOM armed and signed in, current source playing, a distinct next item, and at least 3 seconds remaining.
5. Resolve the album using the existing public album endpoint and existing strict title/artist/duration match. Only UNIQUE_CANDIDATE can continue.
6. Resolve the replacement and download its full file into the existing bounded recentAudio cache.
7. Prefetch is network/file work only. It must not create MediaPlayer, touch AudioOwnership, alter source/replacement gain, pause, seek, or change transport.
8. The boundary path still performs its normal fresh resolve. Existing prepare() consumes a prefetched file only if the full key matches: catalogue track ID, replacement ID, version, duration, and MIME. Any mismatch uses the original fallback.
9. If the candidate changes, the request/download is invalidated. Partial files are deleted. Completed files remain inside the existing 3-file / 60 MiB cache.

## Safety and seek preservation

No accepted seek method is intentionally changed. The existing prepare() already checks the same recentAudio cache after a fresh resolve; prefetch writes only the exact key that prepare() will look up. The mandatory check_0385_seek_baseline.py remains unchanged and must pass. Do not modify Pause/Resume, seek transactions, decoder alignment, or the accepted seek source snapshot.

## Test and release boundary

- Branch: feature/android-0385-next-track-prefetch-20261102
- Test package: pro.celikom.nativeprobe.test
- Version: 0.3.85-test.2
- versionCode: 86087
- Existing Test signing certificate retained; OTA disabled.
- One combined audio APK only after host tests, seek baseline, Android API 36/D8, packaging and signature verification pass.
- Stable CELIKOM 0.3.85/code86 and all backup branches remain unchanged.
- No stable release, OTA, stable.json, Hostinger write, contract or publisher action.

## If timeline metadata remains incomplete

The test log must show individual availability of title, artist, album ID, MediaMetadata duration, Timeline.Window duration and placeholder state. If the current timeline still lacks the necessary fields, stop and ask the owner before introducing a separate Yandex MediaBrowser/library metadata query. Do not silently widen permissions.

## Owner test

One combined listening test through several consecutive track transitions in the same Yandex Music session. Verify prefetch start, download completion before boundary, cache hit after fresh resolve, and whether the first seconds still come from the original version. No separate seek/Pause/Resume test unless diagnostics show a regression.
