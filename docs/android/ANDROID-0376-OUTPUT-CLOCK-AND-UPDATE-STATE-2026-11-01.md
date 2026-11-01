# Android 0.3.76 staging — output-clock evidence and persistent update state

**Date:** 2026-11-01  
**Status:** staging / draft PR; not merged, not signed, not released  
**Code branch:** `feature/android-076-output-clock-update-state-staging-20261101`  
**Base branch:** `feature/android-unified-preparation-seek-gate`  
**Draft PR:** [#24](https://github.com/manufact-test/nomusic/pull/24)  
**Rollback branch:** `backup/android-0375-before-output-clock-and-update-state-20261101`  
**Pre-change HEAD:** `0867c83c692cdc2dbfd74662476cb181ea2e9d51`

## 1. Re-analysis of the 0.3.75 diagnostic

Source: owner-provided `CELIKOM-combined-20261101-125049.txt` (three runs: 0.3.73, 0.3.74, 0.3.75).

The 0.3.75 ALIGNMENT group contained 47 seek ACKs. Eleven had absolute `rawResidualMs` above 100 ms; the maximum was 772 ms. For all eleven outliers, `decoderPositionMs` at ACK equalled `requestedPositionMs`, so the decoder landing error was 0 ms. The source position continued advancing while the replacement MediaPlayer was waiting for its asynchronous seek callback.

The 772 ms event illustrates the distinction:

| Measurement | Value |
|---|---:|
| Requested target | 221136 ms |
| Decoder position at ACK | 221136 ms |
| Source projected position at ACK | 221908 ms |
| Callback elapsed time | 816 ms |
| Old raw residual | 772 ms |
| Source advance minus callback | -44 ms |

Therefore the old residual was a current **transport skew at callback**, not a direct measurement of decoder landing error, cross-clock offset, or output presentation. The large values remain relevant: the replacement was behind the still-playing source while the asynchronous seek completed. The subsequent WARM gate/correction must be examined separately.

The 0.3.75 WARM group had 20 ACKs, 40–91 ms, with no result above 100 ms. This confirms that the existing WARM correction reduced the measured transport skew; it does not prove speaker/Bluetooth continuity.

## 2. Eight overlap events

The eight `overlap_commands` correspond to the eight command-level entries into `SAME_SONG_BLEND`. They are expected during the current 160 ms complementary linear blend, not eight asynchronous seek races. The event name `audio_command_anomaly` is retained for compatibility, but new fields classify the event:

- `classification=expected_same_song_blend`
- `expectedByOwnerState=true`

Overlaps outside `SAME_SONG_BLEND` remain classified as unexpected. This is still a command-state observation, not an acoustic measurement.

The owner previously selected the linear blend as the single production transition mode (see the 0.3.69 decision trail). That behavior was not changed. The code comment now accurately says that the blend is production behavior but does not prove same-edit identity, PCM phase alignment, or audible continuity.

## 3. Source/replacement duration differences

Three replacements were accepted by the existing bounded-tail allowance (maximum 1500 ms):

| Track | Yandex source | Replacement | Difference |
|---|---:|---:|---:|
| Биг сити лайф | 232450 ms | 231096 ms | -1354 ms |
| Крылья | 272700 ms | 272118 ms | -582 ms |
| Метамир | 286730 ms | 286067 ms | -663 ms |

The current policy can return to the original source for the shorter replacement tail. These duration deltas are real metadata/probe differences and can produce track-specific tail transitions. `automaticSourceIdVerified=false` means title/artist/album matching is not proof that the exact same edit/master was selected. No duration threshold was changed in this staging work.

## 4. Android clock and capture options

CELIKOM's replacement path uses Android `MediaPlayer`; it does not own the internal `AudioTrack` instance used by MediaPlayer. Calling `AudioTrack.getTimestamp()` on an unrelated track would not measure this output. The public `MediaPlayer.getTimestamp()` / `MediaTimestamp` API (API 23+) is the appropriate no-new-permission measurement available for the replacement player.

New passive samples record:
- stage: `pre_blend` / `pre_exclusive_grant`, `blend_midpoint`, `post_blend` / `post_exclusive_grant`;
- `System.nanoTime()` and `SystemClock.elapsedRealtimeNanos()`, their sampled offset and read window;
- decoder cursor, source transport projection and source snapshot age;
- MediaTimestamp anchor media time, anchor system nanoseconds, clock rate, estimated presented position, and deltas against decoder cursor/source transport.

These samples are explicitly scoped to the CELIKOM replacement MediaPlayer. The log still writes:
`sourcePcmMeasured=false`, `phaseVerified=false`, `hardwareOutputMeasured=false`, and `sourceOutputTimestampAvailable=false`.

For the Yandex source, `Media3` controller position remains a transport timeline, not an exposed output timestamp. `Visualizer` requires `RECORD_AUDIO` and is a limited visualization signal. `AudioPlaybackCapture` requires `RECORD_AUDIO`, user-approved `MediaProjection`, and an app/source capture policy that permits capture. Source capture feasibility is not proven. No permission or manifest change was made.

Official references:
- [MediaPlayer.getTimestamp](https://developer.android.com/reference/android/media/MediaPlayer#getTimestamp())
- [MediaTimestamp](https://developer.android.com/reference/android/media/MediaTimestamp)
- [AudioTrack.getTimestamp](https://developer.android.com/reference/android/media/AudioTrack#getTimestamp(android.media.AudioTimestamp))
- [Audio playback capture](https://developer.android.com/media/platform/av-capture)
- [Visualizer](https://developer.android.com/reference/android/media/audiofx/Visualizer)

## 5. Diagnostic implementation

New files:
- `SeekTimingEvidence.java`
- `OutputClockEvidence.java`

New seek ACK decomposition:
- `callbackElapsedMs`
- `sourcePositionAtSubmitMs`
- `sourceAdvanceDuringSeekMs`
- `decoderLandingErrorMs`
- `handoverSkewAtAckMs`
- `sourceAdvanceMinusCallbackMs`
- source snapshot ages at submit/ACK and decoder position before seek

The existing `rawResidualMs` remains for compatibility, but its semantics are now explicit: source transport minus decoder cursor at ACK, including source advance during asynchronous seek. `replacement_seek_complete`, WARM alignment and join-guard events are also explicitly labelled transport-timeline-only.

No audio playback behavior was tuned. No thresholds, WARM lead, 160 ms join duration, buffering policy, Pause/Resume, Next, or original-source restoration code was changed.

## 6. Update center persistence

The previous bug was confirmed: background `UpdateCheckJob` could notify about a release but did not persist the release candidate used by the in-app update screen.

The new Android-free `UpdateState` model persists:
- last successful check time;
- installed version code associated with that check;
- verified-latest state;
- available version code and the verified manifest JSON.

Foreground checks and background `UpdateCheckJob` now call the same `recordSuccessfulCheck()` path. On activity creation, the candidate is restored and re-parsed against the current installed version. Network failures preserve the previously verified candidate. “Позже” cancels the notification but does not clear the candidate. Once the installed version reaches the candidate code, the stale candidate is cleared.

Existing update section only:
- available: “Доступна новая версия CELIKOM 0.3.xx”, “Скачать обновление”, “Проверить обновление”, “Позже”;
- no update: “У вас последняя версия CELIKOM” and “Проверить обновление”.

No extra main-screen button was added.

## 7. Validation and release boundary

Commits:
- `068ddbc927ebbe86f1baa607b7764e807fc6ff83` — transport seek decomposition and MediaTimestamp diagnostics
- `544ec16ee4f7f064e78e33bc1f5f477d327709e1` — persistent update candidates across UI/background checks
- `a7b28fa8ebd6ed856e1ed9bfa02f0e7da612c06f` — clarify production blend limits and output clock timebases

Final CI: [41297330560 — PASS](https://github.com/manufact-test/nomusic/actions/runs/41297330560), on the final commit. It passed:
- all engine regression tests, including existing HONOR strict join, warm latency, join lab, seek-buffer replay, slow stream seek and unified audio transactions;
- 18 new async seek/MediaTimestamp evidence checks;
- 12 new update-state persistence/defer/freshness checks;
- all 18 native addon host gates;
- Android API 36 source compilation and D8;
- release-contract, APK archive, CI provenance and release-mode checks.

The `publish-stable` job was skipped because this is not the production branch. CI produced an unsigned DEX and offline packaging kit only. No signed APK, release version bump, stable manifest update, Hostinger deployment, or Android permission change was made.

## 8. Required next evidence

After a build containing this staging code is installed on the owner's device:

1. Repeat the affected-track listening check on the same device/output route.
2. Export the diagnostic and inspect `replacement_seek_ack` decomposition.
3. Inspect `replacement_output_clock_sample` availability, anchor, estimated position and deltas at pre/mid/post join.
4. Compare the three shorter replacement tracks and the songs the owner reports as better/worse.
5. Do not call this an audio fix unless the owner listening test improves and the output evidence supports it.

If MediaTimestamp is unavailable or insufficient, the next source-audio experiment must be a separately approved, diagnostic-only capture path after checking Yandex's capture policy. Do not add `RECORD_AUDIO` or MediaProjection to the shipping app without a demonstrated need and explicit approval.
