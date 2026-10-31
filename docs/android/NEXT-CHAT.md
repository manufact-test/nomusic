# CELIKOM Android — NEXT CHAT HANDOFF (31.10.2026)

**READ FIRST:** [ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md](ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md), then [ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md](ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md), [REGRESSION-GATES-2026-10-29.md](REGRESSION-GATES-2026-10-29.md), and the previous owner baseline handoff [START-NEXT-CHAT-2026-10-31-AFTER-0369-OWNER.md](START-NEXT-CHAT-2026-10-31-AFTER-0369-OWNER.md).

## Immutable production baseline / scope

- Signed Android baseline: 0.3.71/code72.
- Source SHA: `b624d5c062a6d6310459f9bb73cf5f9014eb8a54`.
- Immutable backup: `backup/android-0371-honor-usable-baseline-20261031`.
- Previous backup `backup/android-0369-honor-listening-control-20261031` also untouched.
- Live stable remains 0.3.71. Never overwrite or rewrite either backup.
- Android only. One mode only. No desktop, backend, website, catalogue, auth, updater, UI buttons or A/B mode changes.
- No APK/version bump/stable publish until the owner explicitly asks after real-device testing.

## Current engineering branch

`feature/android-0371-honor-diagnostic-audit-staging`

Start from its actual HEAD, not a remembered SHA. Previous checkpoint: `60e78db25c2847d71431be890fdd6a3b0e9c95ba`. The current work stages a seek-scoped stable transport-baseline policy in `ReplacementEngine`, adds `SeekAlignmentPolicy.java`, and expands actual-engine tests for 0.3.71 residuals plus 0.3.63/0.3.64 scrub regressions.

## Policy now under CI validation

A flat 350ms gate could grant output while a new seek residual was still audible. The staged policy learns a stable source/decoder transport offset (3 samples, ≥250ms span, ≤45ms spread, ≤700ms magnitude, ≤1.2s age), freezes it at seek start, preserves it in the decoder seek target, and compares only the new residual. New residuals up to 200ms are accepted; larger residuals receive at most two silent same-decoder corrections before fail-open to the original. Stable baseline-normalized drift is also passed to ClockSupervisor. Baseline resets on pause, route loss, release and track boundary.

This is transport timing only, **not acoustic or Bluetooth phase measurement**. Cold initial join and route-resume paths are intentionally left on their existing behavior.

## Required next steps

1. Inspect the latest GitHub Actions run for the new commit. The previous run for `60e78db` was still executing the host regression suite at last check; do not treat that run as validation of the new code.
2. Run the full `python3 android/native-companion/tests/run_engine.py` suite and inspect any failing test before making another change.
3. Confirm the new `TestSeekAlignmentPolicy`, `TestHonor071SeekResidual`, modified `TestHonor063SeekScrub` and `TestHonor064ManualNext` all pass.
4. Confirm SDK36 Java compile + D8 succeeds and the `publish-stable` job is skipped on this staging branch.
5. Review the final diff for accidental changes. No user journals, track IDs/titles or raw diagnostics in Git.
6. Only after all CI gates pass, prepare a real-device test build if explicitly authorized. Keep 0.3.71 as the installed safe baseline until the user tests it.

**Important test cases:** stable 206ms offset + 77ms new seek error (283ms raw) should preserve the offset; stable 206ms + 250ms new error should correct silently; no baseline + 283ms should correct; 179ms fast seek remains accepted; slow Range 2792/933/17ms remains bounded; repeated finger scrubs, pause, Stop, route loss, real Media3 Next, stale callbacks and automatic successor must not regress.

Cold next-song dip/micro-repeat remains separate. The 160ms complementary linear join uses two independent output sessions; transport tests cannot establish PCM phase. Do not reintroduce A/B controls, equal-power fading, or claim the join is acoustically proven.
