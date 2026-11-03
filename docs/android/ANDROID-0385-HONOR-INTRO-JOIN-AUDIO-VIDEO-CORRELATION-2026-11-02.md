# CELIKOM Android 0.3.85 — HONOR intro/join audio-video correlation (2026-11-02)

**Status: evidence review plus isolated code-only cold-join experiment.** No APK build or OTA publication. Preserve accepted seek implementation and golden guard.

## Inputs and run selection

- Owner journal: `CELIKOM-combined-20261102-105708.txt` (three runs: 0.3.84 at 00:52, 0.3.85 at 10:08, and the relevant last 0.3.85 run at **10:55:07 +03:00**).
- Owner screen recording: `SVID_20261102_105501_1.mp4`, 84.84 s, HONOR Android 13, 590×1280 video, mono AAC 48 kHz.
- All statistics below are from the **last 10:55:07 run only**, not the two earlier runs. It has 13 full-file experiment starts/downloads/prepares/joins, 12 confirmed source media-item transitions, 26 seek ACKs, and **17** source discontinuity events. The log ends without a `run_end` marker; do not claim a formally closed session.
- The MP4 has an AAC audio track, so recorded signal level can be measured. It is a screen recording, not a calibrated microphone recording of the phone speaker and not separate PCM captures of Yandex and CELIKOM. No direct source-vs-replacement phase measurement is available.

## Main findings

### 1. The accepted seek path remains healthy in this run

- 26 replacement seek ACKs: 24 ALIGNMENT and 2 WARM.
- Callback latency range 25–78 ms; median 44.5 ms.
- Every ACK is `full_download_file`, `rangeWaitObserved=false`, `staleOperation=false`.
- This is consistent with the owner's accepted 0.3.85 seek verdict. Do not change seek submission, ACK completion, or full-file selection.

### 2. The new-song join is consistently delayed after the source item changes

- 13/13 replacement downloads completed: 655–3,804 ms, median 1,826 ms.
- 13/13 local decoder prewarm-motion observations.
- 13/13 `replacement_unified_join_start` events use the 160 ms complementary-linear blend.
- There are 12 source media-item transitions. From each transition to the following join start, the diagnostic records 1,073–4,379 ms, median 2,525 ms.
- During download/preparation the intended policy is to leave the original source audible. A delayed CELIKOM replacement is therefore not, by itself, proof of silence or an audio defect. The video/recorded audio must be evaluated independently.

### 3. A very low-level interval appears at one source boundary before CELIKOM joins

In the video at **59.1–60.0 s**, the recorded AAC level falls to approximately **−91.9 dBFS RMS** (about 64% of decoded samples in that interval are exactly zero). It returns abruptly to ordinary music level at about 60.0 s. This is a measurement of the screen-recording AAC track, not calibrated speaker output.

The approximate video-to-journal alignment is +6.1 s. On the `Хлоп-Хлоп` boundary, the journal sequence is:
- 53.751 s: source discontinuity classified `SEEK_TO_OTHER_ITEM` (`manualNextButtonObserved=false`).
- 53.763 s: CELIKOM silences its previous replacement decoder.
- 53.802 s: CELIKOM restores the original source effect.
- 53.852 s: Media3 reports the new media item (`PLAYLIST_CHANGED`).
- 53.922 s: source snapshot reports `isPlaying=false`, playback state 2.
- 53.931 s: source snapshot reports `isPlaying=true`, playback state 3.
- 54.063 s: CELIKOM starts the new full-file experiment; download completes at 55.892 s; the new replacement join begins at 56.318 s.

The low-level interval begins roughly 0.7 s before CELIKOM's previous-decoder silence/restore events and ends before the new replacement join. The later 160 ms blend cannot explain its onset. CELIKOM cleanup overlaps only the tail of the interval; the available evidence cannot assign the full gap conclusively to Yandex's transition versus the recording/output path.

The screen recording appears to show a touch indicator over Next near the start of the interval, consistent with a manual Next action. The diagnostic itself explicitly cannot verify a physical button tap, so this remains visual evidence rather than a Media3 attribution. The lookahead record for this item has `metadataComplete=false`, `authorizedForPrefetch=false`, and `prefetchStarted=false`; the current code correctly did not start a speculative download from incomplete next-item metadata.

### 4. The join gate is not an acoustic phase gate

- The 13 initial join guards pass the configured transport threshold (100 ms); observed guard drift spans −48 to +88 ms.
- During the 160 ms commanded blend, passive transport summaries show source/decoder position drift reaching 108, 113, 117 and 101 ms in several joins.
- These are transport-clock values only. The log explicitly records `sourcePcmMeasured=false`, `phaseVerified=false`, and `hardwareOutputMeasured=false`. The output timestamp belongs to CELIKOM's MediaPlayer; source output timestamp is unavailable.
- Therefore neither a passing 100 ms transport gate nor `replacement_transition_complete` proves that the two audible waveforms are phase-aligned, same edit, or perceptually continuous.

### 5. Recorded level around some join moments varies, but cannot prove cancellation

The AAC recording has short level changes around some join times. Because the original source and replacement PCM were not captured separately, and because musical dynamics/editions can differ, those level changes cannot yet be attributed to destructive phase cancellation or the gain law. Keep this as a hypothesis, not a root-cause claim.

## Working diagnosis

There are at least two distinct things to keep separate:

1. **Quiet/near-silent part immediately after a Yandex track boundary**, while the original Yandex source is still expected to be audible and CELIKOM is downloading/preparing. CELIKOM's later 160 ms blend cannot explain an earlier interval. First establish whether the Yandex source itself contains that quiet opening or whether source playback is buffering.
2. **Audible seam when CELIKOM takes over**, 1–4.4 seconds after the source boundary. This is where the transport-only gate and two-session blend may still fail to guarantee waveform continuity.

Do not collapse both into one generic “Next lag” metric.

## Isolated cold-join experiment — code-only candidate

A narrow experiment is now implemented on `feature/android-0385-intro-join-investigation-20261102`:

- Only the **prewarmed local full-file cold/new-track join** changes from `fade(true,true)` (160 ms complementary-linear blend) to `fade(false,true)` (exclusive single-turn handover).
- The same decoder prewarm, alignment seek, existing handover clock gate, ownership ticket and 100 ms drift threshold remain in place.
- Source remains audible and replacement muted until the existing clock gate is validated. At the grant, CELIKOM switches to replacement as the sole commanded output; it does not intentionally overlap the two sessions.
- Streaming joins, non-prewarmed attachment, same-song seek/resume, Pause/Resume, Next routing, duration validation, and the accepted seek implementation are not changed.
- No user-facing toggle was added. The production constructor selects the experiment; the deterministic host harness retains the previous blend as a baseline and explicitly runs both variants.
- `TestColdJoinExclusiveExperiment.java` compares both variants under the same local-file prewarm/alignment/gate sequence and asserts no commanded overlap in the exclusive path. `run_engine.py` now includes this test.

This is a diagnostic candidate, not a presumed fix. Exclusive switching may click or expose a content/edition offset if source and replacement are not the same edit. The 59.1–60.0 s near-silence is a separate pre-join observation and is not expected to be repaired by this experiment.

- Work only on `feature/android-0385-intro-join-investigation-20261102`.
- Keep Yandex Music crossfade OFF during phase one.
- Do not change the accepted same-song seek path or its guard.
- Full host regression suite and Android API 36/D8 CI passed in [run #41419113128](https://github.com/manufact-test/nomusic/actions/runs/41419113128). The new cold-join replay passed **32 checks**; the 0.3.85 seek golden guard passed. `publish-stable` and test-candidate build jobs were skipped.
- CI produced only the offline build kit and unsigned DEX inspection artifact. No signed/installable APK was built and no stable OTA/manifest change was made. Do not publish to the live stable channel without explicit owner authorization.
- If CI passes, use only a short, representative HONOR listening test of the cold join. No broad repeat seek test.

## Owner-approved next delivery — side-by-side test app

The owner explicitly selected a **separate installed application**, not an in-place update. Build one signed `CELIKOM Test` APK with Android package `pro.celikom.nativeprobe.test`, separate app storage, original signing certificate, and all stable OTA/update behavior disabled. The detailed exact requirements are in [ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md](ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md). The existing same-package `test_only` path must not be used as-is. Deliver as a GitHub Actions artifact; do not publish to Hostinger or change stable 0.3.85/code86. The owner will stop stable CELIKOM before running the test app and listen to one or two cold/new-track starts with Yandex crossfade OFF.

## Preservation

- Accepted 0.3.85 source SHA: `053b7d59beb53db5f30b942feba35e51a1ab256a`.
- Guard: `android/native-companion/tests/check_0385_seek_baseline.py`.
- Stable OTA remains 0.3.85 / versionCode 86.
- This report is documentation only; raw diagnostic/video/audio are not committed.
