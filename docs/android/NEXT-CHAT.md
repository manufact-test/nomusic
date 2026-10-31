# 31.10.2026 — NEXT CHAT: 0.3.71 seek residual RED reproduced; no production fix/APK

**READ FIRST:** [ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md](ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md), then [ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md](ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md) and [REGRESSION-GATES-2026-10-29.md](REGRESSION-GATES-2026-10-29.md).

**Immutable owner-preferred signed baseline:** Android 0.3.71/code72, source SHA `b624d5c062a6d6310459f9bb73cf5f9014eb8a54`, backup `backup/android-0371-honor-usable-baseline-20261031`. Do not move, rewrite or delete it. Previous `backup/android-0369-honor-listening-control-20261031` also untouched. Live stable remains 0.3.71. No APK is to be built or published from this task. One mode only; Android only; desktop, backend, site, catalogue, auth and updater are out of scope.

**Current nonpublishing branch:** `feature/android-0371-honor-diagnostic-audit-staging`. Start from its actual HEAD, not an old copied SHA. The previous documentation/diagnostic checkpoint is `44f96ecaccf344b035ed46db9b7590849d36f7af`; this task adds `TestHonor071SeekResidual.java`, wires it into `tests/run_engine.py`, and adds the residual replay document. New commit/CI receipt will be added after CI finishes.

## New confirmed code-level risk

`ReplacementEngine.HANDOVER_DRIFT_MS` is 350ms. In the latest private 0.3.71 run, a few slow seek callbacks (311/400ms) had residuals 254/330ms, then later transport drifts around 283/336ms before the exclusive handover. The decoder can therefore be granted while still up to 350ms behind the source clock. This is a plausible micro-rewind mechanism, not an acoustic proof. Do not reduce the constant blindly.

`TestHonor071SeekResidual` deliberately reproduces current behavior in the real `ReplacementEngine` fake-adapter harness: after a 330ms callback residual, a 40ms decoder advance leaves 283ms transport residual and the current gate grants full replacement. It records this as an intentional RED finding (the test passes when the defect is reproduced), while also checking pause, Next/boundary and stale ACK safety. No user journal contents or track metadata are committed.

## Next task

Do **not** jump to a patch. Design a seek-scoped confidence/fail-open policy that distinguishes:
- post-seek residuals 0–85ms and 179ms;
- 206ms stable Bluetooth-like offset (must not be mistaken for a failed seek);
- 254/283/330/336ms residuals near the current limit;
- 400ms and 826ms residuals;
- 2792/933/17ms slow sparse Range callbacks;
- repeated finger scrubs, pause/resume, real Media3 Next, Stop, route loss, stale callbacks and automatic successor.

A naive lower threshold can create fallback or repeated-seek loops and regress the already improved scrub path. Keep the original audible whenever alignment confidence is insufficient; do not issue audible corrections. Preserve the same prepared decoder and one in-flight untagged seek discipline. Validate against all existing tests, not only the new replay. Production change only after a documented policy and RED/GREEN proof.

Cold next-song dip/micro-repeat remains separate: complementary linear 160ms uses two independently presented audio sessions; no PCM phase or speaker output is measured. Do not resurrect A/B modes, equal-power fade, or claim that seek fixes join acoustics.

**Hard constraints:** no APK/no version bump/no production stable push; don't touch backup refs; no computer version; no extra UI buttons; don't commit private combined logs. Run full `python3 android/native-companion/tests/run_engine.py`, addon host suite, SDK36/D8 and ensure `publish-stable` is skipped.
