# CELIKOM Android 0.3.71 — RED replay of HONOR seek residuals

**31.10.2026. Android-only, nonpublishing staging. No production audio code, signed APK, or immutable backup changed.**

## Finding

The private 0.3.71 journal has decoder seek callbacks up to 400ms. The diagnostic audit identified a 350ms `HANDOVER_DRIFT_MS` acceptance gate and observed subsequent transport drifts around 283ms and 336ms before exclusive transfer. The callback residual and later clock drift are distinct measurements; neither is PCM phase or a direct speaker measurement.

## New deterministic actual-engine replay

`android/native-companion/tests/TestHonor071SeekResidual.java` runs the real `ReplacementEngine` with the existing deterministic Android/Media3 adapters and partial-stream fixture. It recreates a slow seek with a 330ms residual, then advances the decoder only 40ms while preserving 283ms source/decoder transport difference. It confirms the current 350ms gate grants full replacement output (`REPLACEMENT`, decoder volume >0.99, original effect -100dB). This is an intentional **RED finding recorded as a green test**: the test passes only while it reproduces the known unsafe acceptance. It does not claim that a 283ms transport offset is the exact audible rewind.

The same test verifies a real pause revokes a pending muted handover and a track boundary/Next retires the old partial decoder and effect; a stale seek ACK cannot revive it. The fixture is synthetic and contains no user media IDs, titles, or raw journal lines.

## Why no production fix yet

Simply changing 350ms to 200ms is not approved. It can cause false fallback or break slow Range, rapid seek, Bluetooth offsets, pause/resume and automatic track changes. `ClockSupervisor` currently uses 700ms warning, 1.5s confirmation and bounded correction policy; the 350ms handover gate is a separate decision. A safe policy must distinguish post-seek residual confidence from normal steady Bluetooth/route offset and must fail open without creating a second seek spiral. That policy is not yet selected or validated against all historical HONOR regressions.

## Validation contract

- The test is wired into `tests/run_engine.py` and runs with the full host suite.
- Existing `TestHonor063SeekScrub`, `TestHonor066SeekBufferReplay`, `TestHonor067SlowStreamSeek`, `TestAudioOwnershipRegression`, `TestStreamingEngine`, `TestCarRecovery`, `TestClockSupervisor`, Media3 router and lifecycle gates remain mandatory.
- Next, pause, Stop, route loss and stale callbacks must remain safe.
- SDK36/D8 full Android CI must pass on this nonpublishing branch; `publish-stable` must remain skipped.
- No APK, version bump, desktop/backend/site/updater changes, or modifications to either backup branch.

## Next engineering decision

Design and compare a *seek-scoped confidence/fail-open rule* using deterministic timelines: residual 0–85ms, 179ms, 206ms Bluetooth-like steady offset, 254/283/330/336ms post-seek residual, 400ms, 826ms slow stream, 2792/933/17ms sparse Range sequence. The rule must avoid repeated decoder seeks and must not treat a stable route offset as seek error. Only after a proposed rule has RED/GREEN evidence against all cases should `ReplacementEngine` change.

Cold new-song join dips/repeats remain a separate issue. The 160ms complementary linear join uses two independently presented audio sessions and remains phase-unverified; transport tests cannot settle it. No mode switch or second algorithm is to be added.
