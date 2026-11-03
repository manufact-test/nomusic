> **Исторический промежуточный кандидат. Test.10 отдельно тестировать НЕ НУЖНО.** Его исправление вошло в единый Test.11/code86096 вместе с ускорением подключений и защитой после паузы. Актуальная подписанная сборка, SHA, CI и задачи следующего чата — в [ANDROID-0385-TEST-11-VERIFIED-HANDOFF-2026-11-03.md](ANDROID-0385-TEST-11-VERIFIED-HANDOFF-2026-11-03.md).

# CELIKOM Test.10 — recovery of silent seek events (2026-11-03)

## Evidence from owner's installed Test.9

Inputs: private owner report `CELIKOM-combined-20261103-150348.txt` and `SVID_20261103_150238_1.mp4`. Only the **Test.9 run beginning at log line 3557, elapsed 0, approx. 15:02 local** is new. Earlier Test.7/8 runs in combined history are not Test.9 evidence.

- The owner caught a reproducible **finger scrub on “Дым” (Лёша Свик)**. Video shows the Yandex scrubber toward ~3:16/3:39, but the CELIKOM-replaced audio continues from the beginning. Reaching the end in Yandex can still advance the song.
- “Дым”, source alias **77**, current at elapsed **23769ms**, replacement cold/warm alignment approximately **23950–24417ms**. While Yandex UI scrubber moves to the late position, CELIKOM's direct Media3 controller still reports approximately **9695ms at 34042ms**, **11503ms at 35855ms**. During the entire source interval 23769–38081ms there is **no** `source_discontinuity(SAME_ITEM_SEEK)` and **no** replacement seek request. The original platform/app timeline and Media3 remote observer diverge. The accepted MediaPlayer seek/ACK implementation is not the cause on these samples.
- The next item “Животные” at ~38231ms does emit user seek events and CELIKOM correctly issues/already ACKs range seeks at 42742ms and 43876ms. Likewise later alias 55 seeks at 69220ms and 76551ms. Existing seek transport works whenever Media3 supplies the new source position.
- Test.9: 8 quiet primed decoders adopted, no instance of new 150ms live-prime waiting path; Test.9 still had initial-song `replacement_drift_unstable` at 19314ms (+1087ms) and recovery at 19399ms. Owner subjectively found this run slightly worse than Test.8; no acoustic acceptance and no proven regression attributable to a specific Test.9 code line. Do not blindly revert another join correction.

## Android API research

Primary Android documentation:
- https://developer.android.com/media/media3/exoplayer/listening-to-player-events : `Player.onPositionDiscontinuity` with `DISCONTINUITY_REASON_SEEK` is the expected signal for exposed media seeks.
- https://developer.android.com/media/media3/exoplayer/migration-guide : `MediaLibraryService` can provide backward-compatible `android.media.browse.MediaBrowserService` session connection when its legacy interface is registered.
- https://developer.android.com/reference/android/media/browse/MediaBrowser : read-only retrieval of a service's media session token.
- https://developer.android.com/reference/android/media/session/PlaybackState : position, speed and last-position-update time are exposed via the legacy platform media session.

## Isolated Test.10 implementation

Test package `pro.celikom.nativeprobe.test`, version `0.3.85-test.10`, code **86095**, signed side-by-side APK. Test.9 retained as previous fallback; stable 0.3.85/code86 untouched. This release adds a **passive independent position observer** in `ProbeService` using platform `MediaBrowser` (same exact Yandex service) and `MediaController`. There are no playback transport calls, no notification listener, no Accessibility API and no new Android permission.

A self-contained `LegacySourcePositionPolicy` allows recovery only when Yandex title/artist and duration agree, legacy PlaybackState is playing, reports recent position updates, differs from Media3 by >=4 seconds, and the disagreement lasts >=250ms across observations. Only then does the existing engine receive a corrected `PlaybackSource.position` and the existing seek notification; **accepted `ReplacementEngine.seek()` / `completeSeek()` remain byte-identical** and golden hash regression is run. Upon loss of trustworthy legacy evidence after recovery, CELIKOM restores the original (fail closed) instead of jumping back to an unreliable Media3 position. No change at all when the platform browser is unsupported/unavailable.

New deterministic host test `TestLegacySourcePositionPolicy` covers missing event recovery, agreement, title/artist/duration mismatch, old state, source change reset and fail-closed expiry. Android CI compiles and runs it. Field acoustic/seek validation on HONOR still required; the new observer **may be rejected by Yandex's exported service** or reflect the same stale position. Never claim rare seek is fixed without a live trace `source_seek_platform_recovered` and successful actual audio seek.

## Owner test

Install Test.10 over separate CELIKOM Test app only. Test repeated finger seeking on “Дым”/any song, then automatic and manual Next, verify first-note transitions and no duplicate/original audio. Upload combined diagnostic and brief screenshot/video when anomalous. Look for `legacy_position_source_connected` or `legacy_position_source_unavailable`; when actually recovered, `source_seek_platform_recovered`. Compare Test.8 vs Test.9 vs Test.10 without double-counting combined historical runs. Preserve Test.8/Test.9 APK and prior backup/stable branch references.

## Frozen scope

No changes to stable `0.3.85/code86`, OTA/Hostinger, trusted session control, pause/resume, read-only lookahead rules, accepted seek implementation or PR#37 (do not merge). No production rollout before real HONOR acoustic acceptance.
