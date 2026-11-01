# Android 0.3.76 — output-clock evidence, persistent update state and stable publication

**Date:** 2026-11-01  
**Status:** signed 0.3.76 release published to Hostinger stable; in-app update detection is ready for owner retest  
**Code branch:** `feature/android-076-output-clock-update-state-staging-20261101`  
**Base branch:** `feature/android-unified-preparation-seek-gate`  
**Merged PR:** [#24](https://github.com/manufact-test/nomusic/pull/24), merge commit `712e7226052419647b46a16086921e4b82732051`  
**Rollback branch:** `backup/android-0375-before-output-clock-and-update-state-20261101`  
**Pre-change HEAD:** `0867c83c692cdc2dbfd74662476cb181ea2e9d51`  
**Final code HEAD:** `4d83c3fd5b79642d97b3616b5997ec343ece3bd3`  
**Staging CI:** [41298221548 PASS](https://github.com/manufact-test/nomusic/actions/runs/41298221548)  
**Production build + Hostinger publish:** [41299061730 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41299061730)  
**Local reproduction APK SHA-256 (not the server copy):** `6a1f502d3590f89aa1cb4e49772bf9df1a87e197ad2d327286563164e763c56c`  
**Published Hostinger APK SHA-256:** `76e1086dc6a38d5b5c5186475babbfd16c959c06a573775e3c264b3b63cdcf40`  
**Published APK size:** `8755273` bytes

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


## 9. Signed 0.3.76 diagnostic test APK — ready for owner check

A signed test APK was built from the final staging source (version `0.3.76`, versionCode `77`) using the original recovered signing identity. It is not a stable release and was not deployed to Hostinger.

- File: `CELIKOM-Android-0.3.76-OUTPUT-DIAGNOSTICS-FINAL.apk`
- SHA-256: `6a1f502d3590f89aa1cb4e49772bf9df1a87e197ad2d327286563164e763c56c`
- Library backup: `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.76-OUTPUT-DIAGNOSTICS-SIGNED-20261101.apk`
- Verification record: `/CELIKOM/Android/Diagnostics/CELIKOM-0.3.76-verification-20261101.json`
- Final code HEAD: `4d83c3fd5b79642d97b3616b5997ec343ece3bd3`
- CI: [41298221548 PASS](https://github.com/manufact-test/nomusic/actions/runs/41298221548)
- Compiled addon DEX SHA-256: `28da54fc3699d740e886e803db7307b5d45ddab36e7012fb892450ffda7e7ef5`, identical to the DEX artifact produced by the final CI run.

The local signed build ran the complete engine regression suite, all 18 Android addon host gates, Android API 36 source compilation, D8, all update-state tests, and the strict signed-APK verifier. The APK verifier confirms the original signer, package/version, allowed manifest changes, archive integrity, exact DEX, and unchanged catalogue assets.

**Owner test:** install over the existing app (do not uninstall), play the affected songs, exercise the usual Next/seek/pause/resume paths, then export the diagnostic through the existing UI. No new diagnostic button or permission was introduced.

**Not proven by this APK:** actual speaker/Bluetooth continuity, source Yandex PCM, and phase alignment. The verifier deliberately records `source_pcm_measured=false`, `phase_verified=false`, `hardware_output_measured=false`, and `physical_phone_playback_verified=false`. Do not describe the audio as fixed until the owner listening test supports that conclusion.


## 10. Stable publication completed

The PR was merged into `feature/android-unified-preparation-seek-gate` at `712e7226052419647b46a16086921e4b82732051`. The production pipeline completed successfully: [GitHub Actions 41299061730](https://github.com/manufact-test/nomusic/actions/runs/41299061730).

- Live stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json
- Published APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/77-76e1086dc6a38d5b5c5186475babbfd16c959c06a573775e3c264b3b63cdcf40.apk
- Version `0.3.76`, code `77`, size `8755273` bytes
- Published APK SHA-256: `76e1086dc6a38d5b5c5186475babbfd16c959c06a573775e3c264b3b63cdcf40`
- The remote Hostinger upload was checked server-side for exact SHA-256 and byte size before the immutable APK was moved into place. Only after that check did the workflow atomically replace `stable.json`.
- The workflow then fetched the public stable manifest over HTTP and confirmed it exactly matched the expected manifest: `0.3.76 / 77`.

**Owner action:** open CELIKOM, press the existing `Проверить обновление` button, and install 0.3.76 over the existing app. Then run the affected-track listening test and export a fresh diagnostic. No uninstall or new diagnostic button is required.

The local reproduction APK stored earlier in Library has a different file SHA because it was separately packaged; it is not the binary published to Hostinger. Both use the same source version, addon DEX and original signer. Use the in-app update for the production release.
