# CELIKOM Android 0.3.71 — seek-scoped transport baseline policy

**31.10.2026. Android-only, nonpublishing staging.** Immutable signed baseline 0.3.71/code72 and both backup refs remain untouched. No APK/version bump or stable release.

## What the 0.3.71 audit established

The real-device journal contained slow seek callbacks and post-seek transport residuals in the 283–336ms range. The old handover gate was a flat 350ms. That gate did not distinguish a newly introduced seek error from a stable pre-existing offset between the Yandex and replacement transport clocks.

A transport offset is not proof of acoustic/Bluetooth latency. These values come from player position reports; no PCM waveform, speaker output or physical route latency is measured.

## Staged policy

New helper: `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/SeekAlignmentPolicy.java`.

1. While the same replacement owns output, gather up to five source-vs-decoder drift samples.
2. An initial baseline is considered stable only after at least three samples spanning 250ms, with no more than 45ms spread. Samples must be at least 100ms apart; a gap over 600ms restarts accumulation.
3. Initial offsets up to 700ms are eligible. The frozen baseline expires after 1,200ms. A baseline derived from an already trusted offset plus an accepted residual can reach 925ms; a fresh untrusted 925ms offset is never learned.
4. On a user seek, freeze the most recent stable offset. Seek the same prepared decoder to `sourcePosition - baselineOffset`, preserving the existing clock relationship rather than resetting it to zero.
5. At callback/handover, calculate `adjustedResidual = rawResidual - baselineOffset`. Accept only when the new residual is within 225ms.
6. If the new residual exceeds 225ms, keep the original audible and retarget the same decoder to the latest source position while preserving the baseline. Do not predict a second callback's latency: sparse Range callback timing is not stable enough, and speculative prediction can overshoot. At most two corrections are allowed; if confidence still is not sufficient, restore/keep the original for that track.
7. During steady playback, ClockSupervisor receives drift normalized against the stable baseline. This avoids treating a persistent route-like transport offset as a newly growing clock error.
8. Reset baseline on real pause/buffering pause, route loss, decoder release, source boundary and track change. Repeated scrubs while a native seek is in flight retain the frozen baseline and the existing one-in-flight untagged callback discipline.

The policy is seek-scoped. Cold initial join and route-resume legacy paths retain their existing thresholds and behavior; the 160ms complementary cold join is not changed.

## Deterministic coverage added/updated

- `TestSeekAlignmentPolicy`: 204ms acceptance boundary, 226ms correction boundary, 206ms stable offset, 550ms stable offset, median/stability sampling, 45ms spread, age/gap expiry, frozen baseline, correction target and normalized clock supervision.
- `TestHonor071SeekResidual`: actual `ReplacementEngine` replay. A 206ms stable baseline plus 77ms new error produces 283ms raw drift and is accepted. A 206ms baseline plus 250ms new error is corrected silently. With no baseline, a 283ms residual is corrected. Pause, Next, decoder retirement and stale callback protections remain asserted.
- `TestHonor063SeekScrub`: 280ms callback residual now triggers a same-decoder silent correction; fast 65ms scrub remains unchanged.
- `TestHonor064ManualNext`: repeated partial-stream scrubs include the second correction ACK and verify the same decoder/effect, no re-download and no cold-join restart.
- `TestHonor060Journal` retains the historical 204ms no-extra-seek contract. Existing 0.3.67 2792/933/17ms slow Range sequence remains mandatory, as do 0.3.66 buffering, 0.3.65 Media3 continuity, pause/Next/Stop/route ownership, car recovery, lifecycle and architecture tests.

## Safety / release boundary

- All seek corrections remain silent on the replacement; Yandex/source is restored to unity during alignment.
- One prepared decoder and one untagged native seek at a time; no new audio session or effect attachment.
- No changes to the single production mode, no extra user/admin controls, no desktop/backend/site/updater changes.
- SDK36/D8 CI must pass on the staging branch. `publish-stable` must be skipped because the branch is not the release branch.
- No private combined journal or personal track metadata is committed.

## What this proves — and what it does not

The tests prove deterministic transport-clock behavior and owner lifecycle under synthetic callback timing. They do not prove that a given millisecond residual maps directly to audible rewind, and they do not measure phase alignment between Android output sessions. Real HONOR listening verification remains required before any APK is considered.
