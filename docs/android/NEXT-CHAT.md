# CELIKOM Android — NEXT CHAT HANDOFF (31.10.2026)

**READ FIRST:** [ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md](ANDROID-0371-RESIDUAL-RED-REPLAY-2026-10-31.md), then [ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md](ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md), [ANDROID-0371-SEEK-TEST-APK-RECEIPT-2026-10-31.md](ANDROID-0371-SEEK-TEST-APK-RECEIPT-2026-10-31.md), [REGRESSION-GATES-2026-10-29.md](REGRESSION-GATES-2026-10-29.md), and the previous owner baseline handoff [START-NEXT-CHAT-2026-10-31-AFTER-0369-OWNER.md](START-NEXT-CHAT-2026-10-31-AFTER-0369-OWNER.md).

## Immutable production baseline / scope

- Signed Android baseline: 0.3.71/code72.
- Source SHA: `b624d5c062a6d6310459f9bb73cf5f9014eb8a54`.
- Immutable backup: `backup/android-0371-honor-usable-baseline-20261031`.
- Previous backup `backup/android-0369-honor-listening-control-20261031` also untouched.
- Live stable remains 0.3.71. Never overwrite or rewrite either backup.
- Android only. One mode only. No desktop, backend, website, catalogue, auth, updater, UI buttons or A/B mode changes.
- No stable release, stable versionCode bump or Hostinger publish until real-device acceptance. A separate signed same-versionCode test APK is now available; it does not change the stable channel.

## Current engineering branch

`feature/android-0371-honor-diagnostic-audit-staging`

Start from its actual HEAD, not a remembered SHA. Previous checkpoint: `60e78db25c2847d71431be890fdd6a3b0e9c95ba`. **Seek-baseline implementation commit:** `58f1111dade3a15cc6e6bc2b4cdb648623dc933f`. **Validated code commit:** `032bd8f2c77d6deb069155923a602bf242aebdf1`. **Signed test APK build commit:** `4d7904b156a5fe2b500f6ba97c2cff7be56a9861`. Documentation now includes the signed APK receipt, updated regression gates and this handoff; inspect the actual branch HEAD before making further changes. The implementation adds the seek-scoped stable transport-baseline policy in `ReplacementEngine`, `SeekAlignmentPolicy.java`, and actual-engine tests for 0.3.71 residuals plus 0.3.63/0.3.64 scrub regressions.

## Policy now under CI validation

A flat 350ms gate could grant output while a new seek residual was still audible. The staged policy learns a stable source/decoder transport offset (3 samples, ≥250ms span, ≤45ms spread, ≤700ms magnitude, ≤1.2s age), freezes it at seek start, preserves it in the decoder seek target, and compares only the new residual. New residuals up to 225ms are accepted; larger residuals receive at most two silent same-decoder corrections before fail-open to the original. Initial trusted offsets are capped at 700ms; a validated offset plus an accepted residual may derive a stable offset up to 925ms. Stable baseline-normalized drift is also passed to ClockSupervisor. Baseline resets on pause, route loss, release and track boundary.

This is transport timing only, **not acoustic or Bluetooth phase measurement**. Cold initial join and route-resume paths are intentionally left on their existing behavior.

## Final CI and signed test APK

- Algorithm code commit: `032bd8f2c77d6deb069155923a602bf242aebdf1`.
- Final build/workflow commit: `4d7904b156a5fe2b500f6ba97c2cff7be56a9861`.
- [GitHub Actions run 41238844237](https://github.com/manufact-test/nomusic/actions/runs/41238844237) — **SUCCESS**.
- `native-android` — SUCCESS: full host suite, API36 compile, D8, source/DEX provenance and release guards.
- `build-honor-seek-test-apk` — SUCCESS: rebuilt, signed with the original CELIKOM certificate and independently verified the APK.
- `publish-stable` — **SKIPPED**. No Hostinger upload or stable manifest mutation occurred.

**Signed test APK is ready:** [download artifact](https://github.com/manufact-test/nomusic/actions/runs/41238844237/artifacts/13056871292). Full receipt: [ANDROID-0371-SEEK-TEST-APK-RECEIPT-2026-10-31.md](ANDROID-0371-SEEK-TEST-APK-RECEIPT-2026-10-31.md).

- File: `CELIKOM-Android-0.3.71-SEEK-TEST-SIGNED.apk`
- Version/package: `0.3.71`, `pro.celikom.nativeprobe`, versionCode `72`.
- SHA-256: `444b6c230aaddf2995138c3ad85286433dd25b3994e8a2871fe53d97dba4cb14`.
- Signer SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.

The test APK deliberately retains package, original signer and versionCode 72 so it can replace the current 0.3.71 in place without advancing the stable channel or blocking rollback to the archived baseline. Do not uninstall the existing app. If Android reports a signature conflict, downgrade or install error, stop and send a screenshot; do not clear data.

## Next action — real HONOR acceptance

1. Download and install the signed test APK over the existing CELIKOM 0.3.71; preserve app data.
2. Test fast seek, the 204ms legacy boundary, 226ms+, 283–336ms residuals, repeated scrubs, pause/resume, Next during alignment and partial-stream seek.
3. Listen for an actual micro-rewind, gap, click or level dip. Do not equate transport milliseconds with acoustic phase.
4. Send one fresh combined diagnostic plus the exact reproduction sequence. Keep the original baseline backup untouched.
5. If a new symptom appears, preserve the journal and create a deterministic RED test before changing thresholds.

**No stable release has been published.** The APK is signed and ready for device testing, but physical HONOR speaker/Bluetooth behavior is not yet verified.

**Important test cases:** stable 206ms offset + 77ms new seek error (283ms raw) should preserve the offset; stable 206ms + 250ms new error should correct silently; no baseline + 283ms should correct; 179ms fast seek remains accepted; slow Range 2792/933/17ms remains bounded; repeated finger scrubs, pause, Stop, route loss, real Media3 Next, stale callbacks and automatic successor must not regress.

Cold next-song dip/micro-repeat remains separate. The 160ms complementary linear join uses two independent output sessions; transport tests cannot establish PCM phase. Do not reintroduce A/B controls, equal-power fading, or claim the join is acoustically proven.



