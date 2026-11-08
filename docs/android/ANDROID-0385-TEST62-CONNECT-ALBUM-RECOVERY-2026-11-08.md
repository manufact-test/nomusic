# CELIKOM Android Test.62 — connectivity wake-up and regional-album retry reduction (2026-11-08)

## Verified source and build
- Source: `6cc77df3a9fcc632c36975dc9fb68ffd853c5b36` on `feature/android-0385-test62-connect-album-recovery-20261108` based exactly on signed Test.61 source `1b949adb8b0246ea3116aff124bd3980e1ab512a`.
- CI and signed isolated APK: https://github.com/manufact-test/nomusic/actions/runs/42474972271 (native host, Android API36/D8, original signature verification PASS).
- Signed APK: `CELIKOM-Android-0.3.85-TEST-62-CONNECT-ALBUM-RECOVERY-SIGNED.apk`, SHA-256 `54d300247ca80de4466d7fe5e578d4fca997cbeb71f5d2d1a21bc093311ab244`, version `0.3.85-test.62` code `86148`, package `pro.celikom.nativeprobe.test`.
- GitHub artifact `CELIKOM-Test-0.3.85-test.62-code-86148`, id `13615535354`. No original app/OTA/backend modification.

## Actual phone evidence from CELIKOM-combined-20261108-140315(1).txt
- Test.61 live approved catalogue succeeded: 130 rows, HTTP 200. Test.60 previously had 404.
- Test.61 Media3 connection failed 5 times with SecurityException, then succeeded at 15.207 s. The same failure sequence already existed in Test.58, so not attributable to the catalogue.
- In Test.61, platform audio media count first rose 0→1 at about 14.735 s; the successful scheduled retry occurred 15.207 s. When audio activity rises during a previous retry backoff, attempt a bounded **read-only** connection immediately if none is connected/in-flight. No new permissions, no transport commands, no Yandex identity claim from the activity callback.
- Album requests repeatedly returned HTTP 451; the current network session now remembers definitive 451 per album and uses existing strict approved-metadata fallback without repeating that blocked request. Clear the cache on network change/manual retry.
- Test.61 audio transitions 13 completed, no recorded replacement preparation failures. RASKOL/«Дым» were NOT played in that Test.61 segment; their failures are verified in previous Test.58/Test.60 videos/logs.
- Previous RASKOL Play/Pause/Seek: Yandex Media3 did not publish expected seek/pause state changes for affected source, whereas local CELIKOM seek was fast once position arrived. «Дым» entered extended source BUFFERING even with playWhenReady=true. **Unresolved**. Fixing these via timer guesses, forced second Media3 session or unapproved privileged permissions is prohibited.

## Acceptance / next step
- Installation over Test.61, confirm improved startup after Yandex playback becomes active and no broken ordinary song switching. Confirm 130+ rows catalogue refresh. Recheck RASKOL/«Дым» only if owner willing; no claim those bugs were fixed by Test.62.
- If Test.62 regresses, reinstall signed Test.61 (code86147 requires uninstall/downgrade handling; preserve owner data) or restore frozen Test.50 in separately approved manner; do not modify Test.50 backup.
- Stable Android 0.3.92 and staged 0.3.93 remain unchanged; do not promote to stable until owner approves.
