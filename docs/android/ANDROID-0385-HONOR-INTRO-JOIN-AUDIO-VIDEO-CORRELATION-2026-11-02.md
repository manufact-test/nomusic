# CELIKOM Android 0.3.85 — HONOR intro/join audio-video correlation (2026-11-02)

**Status: evidence review only. No source-code changes, APK build, OTA publication, or stable manifest change.** Preserve accepted seek implementation and golden guard.

## Inputs and run selection

- Owner journal: `CELIKOM-combined-20261102-105708.txt` (three runs: 0.3.84 at 00:52, 0.3.85 at 10:08, and the relevant last 0.3.85 run at **10:55:07 +03:00**).
- Owner screen recording: `SVID_20261102_105501_1.mp4`, 84.84 s, HONOR Android 13, 590×1280 video, mono AAC 48 kHz.
- All statistics below are from the **last 10:55:07 run only**, not the two earlier runs. It has 13 full-file experiment starts/downloads/prepares/joins, 12 confirmed source media-item transitions, 26 seek ACKs, and 38 source discontinuity events. The log ends without a `run_end` marker; do not claim a formally closed session.
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

In the video around **59.2–60.1 s**, the recorded AAC level is extremely low (about −100 dBFS RMS in the 59-second bin). The corresponding cover change is around 59.1 s, while the next CELIKOM join begins around 61.6–61.8 s. Thus this low-level interval is **before** the new replacement join starts. It cannot be caused by the later 160 ms CELIKOM blend.

This does not prove CELIKOM caused the quiet interval. It may be the actual intro/arrangement of the Yandex source, a source playback/buffering condition, or a recording-path artifact. Do not label it a CELIKOM crossfade bug without separate evidence. Similar low-level sections occur in other portions of the recording; song dynamics vary.

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

## Next controlled experiment — proposed, not performed

Before changing production behavior, inspect the relevant playback source boundary and capture evidence that distinguishes Yandex source audio from CELIKOM replacement audio. If the join blend itself remains the target, a narrow A/B can compare the existing 160 ms complementary-linear **cold/new-track** join with an exclusive cold-join handover after the same readiness/clock gate, keeping download, local decoder, prewarm, seek, Pause, Next, ownership fencing and all other timing unchanged. This is only a diagnostic experiment, not a presumed fix: exclusive switching may click or skip/repeat content if the two versions differ.

- Work only on `feature/android-0385-intro-join-investigation-20261102`.
- Keep Yandex Music crossfade OFF during phase one.
- Do not change the accepted same-song seek path or its guard.
- Add cold-join-specific automated regression tests; run host suite and Android CI.
- Do not publish to the live stable OTA channel without an explicit owner decision after test results. Do not create another stable APK merely because CI is green.
- Test only a short, representative intro on HONOR after the experiment is justified. No broad repeat seek test.

## Preservation

- Accepted 0.3.85 source SHA: `053b7d59beb53db5f30b942feba35e51a1ab256a`.
- Guard: `android/native-companion/tests/check_0385_seek_baseline.py`.
- Stable OTA remains 0.3.85 / versionCode 86.
- This report is documentation only; raw diagnostic/video/audio are not committed.
