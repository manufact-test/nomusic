# CELIKOM Android Test.52 — transport and identity repair

Date: 2026-11-07  
Status: isolated test branch; no stable release or Hostinger application writes.

## Source baseline
- Test.52 is based directly on the exact owner-approved Test.50 source commit: `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`.
- Frozen Test.50 backup branch: `backup/android-test50-exact-source-owner-accepted-20261106`; verified identical to the exact commit.
- Test.51 (`e67fae931dc15baceb9822b21a4aebf895f4a5a4`) is rejected after phone replay. It is not the source baseline and is not merged.

## Evidence from the rejected Test.51 phone replay
- RASKOL «Нас не понимают вообще» entered the replacement path. The UI showed the paused triangle, while the long-lived Media3 controller continued to report `isPlaying=true` and `playWhenReady=true`. The existing controller snapshot therefore did not reflect the Yandex UI's pause.
- Existing anonymized `AudioPlaybackCallback` diagnostics show the active media-player count dropping to 1 during the pause interval and returning to 2 after playback resumes, while the replacement decoder is active. The count does not identify an app and is not used as a direct pause command; it is only a trigger for a second read-only Media3 snapshot.
- Cached decoder seeks acknowledged in 48–78 ms after the source position was published. This does not prove the user's end-to-end seek latency is fixed; it shows the local decoder seek is not the measured delay. Same-item seek callback/cursor disagreement is now eligible for a fresh read-only snapshot only when the fresh position matches the seek target.
- «Толер» album `26101881` returned Yandex HTTP 451 `REGION_RESTRICTION`. The embedded owner catalogue had only 12 rows and was marked stale/incomplete (generated 2026-10-12); no unique own-catalogue candidate was found, so CELIKOM correctly failed closed and kept the original. This was an identity/catalogue fallback issue, not a Media3 connection loss.

## Test.52 implementation
1. **Pause/resume observation:** `SourceActivityProbePolicy` debounces the existing anonymized media-player count for 500 ms. A count transition only requests a second read-only Media3 controller snapshot. The snapshot must match the current alias and available title/artist metadata. A confirmed fresh state is held in `SourceTransportOverride` until the primary controller catches up or a later fresh snapshot confirms resume. No Yandex play/pause/seek command is sent; no new Android permission is requested.
2. **Seek observation:** if a same-item seek callback conflicts with the long-lived controller cursor, a fresh controller is queried. Its position is accepted only when it matches the reported seek target within 2.5 seconds. Ordinary pause/resume probes preserve the primary cursor and cannot jump the song position.
3. **Non-destructive watchdog:** Test.50's quiet-buffering watchdog no longer releases the working controller and reconnects blindly. It requests a fresh read-only snapshot and retains the primary controller.
4. **Fresh owner catalogue:** the Test APK workflow executes `android/companion-probe/catalog-snapshot-remote.php` over SSH stdin. The script performs a read-only database transaction. A complete snapshot generated within 10 minutes is embedded as `assets/catalog-diagnostic.json`. The archive verifier allows exactly that one asset update and verifies every other base asset remains unchanged.
5. **Honest identity status:** the app now distinguishes `waiting_for_album_response` from a completed no-match. When identity lookup has finished without a unique candidate, it shows the song and states that the original is playing instead of displaying an endless «Определяем песню…».

## Build target and safety
- Package: `pro.celikom.nativeprobe.test`
- Version: `0.3.85-test.52`
- Version code: `86137`
- Stable package, stable OTA, audio-engine timing/decoder settings, and Hostinger application files remain untouched.
- No merge to `main`/stable. Phone acceptance is still required before treating pause/seek as fixed.
