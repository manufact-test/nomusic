# CELIKOM Android Test.71 — native transport witness (signed experiment, HONOR pending)
**Date:** 2026-11-08. **Status:** isolated signed Test.71 APK; automated tests PASS, field/acoustic acceptance NOT established. **Do not promote to stable.**

## Source of truth and rollback
- Test.71 **source used for signed APK:** `e620fbc05425e87574a2150bb174ae9641d8da92` on `feature/android-0385-test71-native-state-witness-20261108`, derived exclusively from `feature/android-0385-test70-safe-rollback-source-buffer-status-20261108`.
- GitHub Actions full validation + isolated signed test: [run 42508087622](https://github.com/manufact-test/nomusic/actions/runs/42508087622), **success** (native host suite, API36 Java+D8, real Test APK package/sign/verification, SHA receipt); stable publish jobs SKIPPED.
- Package `pro.celikom.nativeprobe.test`, version `0.3.85-test.71`, code `86157`, size **8,861,849 bytes**.
- Signed APK SHA256: `2be7d394dc40c3ee465e82fcb3539bc18577d9c9aa4b1c43d481d74e72199aa8`.
- Signer SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` matches original. APK signature **v3 verified**, v2 not claimed (original also v3). Verified `separate_android_sandbox=true`, OTA absent, no stable APK/OTA modifications.
- **Direct APK in ChatGPT Library:** [CELIKOM Test.71 APK](https://chatgpt.com/library?file_id=libfile_e520e40f3fe48191abda9fd79bbb4d84&account_id=personal), folder `/CELIKOM/Android/Test/`. Verification: `libfile_21e9266ce1148191ae637382f9db428c`; build receipt: `libfile_6e2ab18500408191b7535e0991785956`.
- Prior **Test.70** remains independent rollback: `0.3.85-test.70`, `code86156`, [original APK](https://chatgpt.com/library?file_id=libfile_0b137e3fe3388191b372296f24f4d7fe&account_id=personal). Stable Android 0.3.92, servers, Hostinger (build reads pinned APK+catalogue but does not write), OTA, desktop, main and other work untouched.

## Evidence / problem
Previous full postmortem: [ANDROID-TEST70-HONOR-203805-ARCHITECTURE-2026-11-08.md](ANDROID-TEST70-HONOR-203805-ARCHITECTURE-2026-11-08.md).

The combined `CELIKOM-combined-20261108-203805.txt` contains Test.68, Test.69 and Test.70. **Only latest Test.70 run** (start 20:36:29 +03, 828 events, elapsed 94.573s) is current evidence. Screen recording: `SVID_20261108_203636_1.mp4`; the video starts later than the log, so video zero is not log zero.

- Control 10AGE `85025192` / `78608850`: seek triggers Media3 BUFFERING -> READY and `isPlaying false -> true`.
- RASKOL `42884423` and Дым `39949113`: position discontinuity observed, but **no fresh corresponding Media3 BUFFERING/READY or playing transition**. Separate CELIKOM MediaPlayer reported fast seek callback (57/66/82ms), NOT measured speaker output/PCM/latency. Full files completed after relevant seeks. There is no objectively verified pause press in the last Test.70 run.
- AudioManager AudioPlaybackCallback was already registered in Test.70: **anonymized aggregate active playback counts** do not securely identify Yandex, specific song, position, pause or speaker time; no authority can be inferred.
- A legacy Android `MediaBrowser` + `android.media.session.MediaController` read-only candidate already existed in Test.70; on this HONOR, `legacy_position_source_unavailable` /`browser_connect` occurred in all three combined runs. It is therefore **NOT a demonstrated available alternative source**.
- Even if legacy session connects, Media3 and legacy controllers may reflect the same Yandex backing session; two synchronized positions do not prove independent physical clocks. `MediaPlayer.getTimestamp()` is CELIKOM-owned only. Android public APIs do not give an ordinary third-party app access to another app's decoder PCM clock or arbitrary audio file injection via DynamicsProcessing. New permissions, root, Accessibility, NotificationListener, capture, app patching and transport-command injection are out of scope.

## Implementation — explicitly bounded experiment
- New `NativeTransportWitness.java` is a pure, side-effect-free decision gate; **ONLY** RASKOL `42884423` and Дым `39949113`, no effect on normal tracks.
- `ProbeService` records a **single passive legacy MediaBrowser reconnection attempt** when a watched track is active and no legacy controller is available; logs `native_transport_legacy_retry`, no transport commands.
- When legacy remains unavailable, log `native_transport_witness_unavailable` **once per watched song**; retain Test.70 playback behavior.
- When available, log `native_transport_witness` stages (initial, 300ms/1400ms-after-seek snapshots) including track match, `PlaybackState` state/age/update timestamp, Media3 event age and playback state, both estimated positions, seek target age, and `sourcePcmMeasured=false`, `hardwareOutputMeasured=false`.
- **Only fail-safe action**: if a fresh legacy `STATE_PAUSED` (≤1800ms old) has title+artist+duration match, while Media3 reports READY/playing/wantsToPlay and its event age ≥350ms, and discrepancy persists ≥300ms, log `native_transport_fail_closed`, release CELIKOM's replacement safely, restore original, and quarantine that item until next item. No play/pause/seek/next command is sent to Yandex.
- The guard is deliberately **not** an automatic correction for absent/delayed seek events, nor an acoustic delay fix. If legacy cannot connect, there is no alternate evidence and Test.71 will exhibit baseline Test.70 behavior. The safeguard might expose a real mismatch if the HONOR system publishes a fresh trusted legacy state after retry. This must be verified on phone, not claimed as already true.
- Existing decoder seek, own audio ownership, gains, transitions, notifications, permissions, login, catalogue behavior unchanged. No new experimental UI buttons or repeated remote commands.

## Automated verification
[CI run 42508087622](https://github.com/manufact-test/nomusic/actions/runs/42508087622) passed both full native host + real Android API 36 Java compilation/D8 and signed APK builder. New `TestNativeTransportWitness.java` tests watched/control scope, metadata mismatch, stale timestamps, current Media3 events, post-seek trace, confirmation threshold, original quarantine and next watched item.
Signing receipt confirms unchanged original signer, separate package, test update disabled, stable/OTA publish false and physical acoustic acceptance false.
**These checks establish build integrity, not real Yandex/Android acoustic correctness.**

## HONOR test protocol (owner)
1. Keep original Yandex Music installed/unmodified. Install **Test.71** over Test.70; do not delete app data. Force stop Test and Yandex before reopening if needed. Ensure 0.3.92 stable remains separate.
2. Native Yandex UI (not CELIKOM shade) on `42884423` / `39949113`: pause/resume, forward/back scrub several times (incl. after file is fully cached), next. Compare with `85025192` and `78608850`.
3. Record audible finger-to-sound behavior and screen plus a fresh combined diagnostic. Inspect `native_transport_legacy_retry`, `native_transport_witness_unavailable`, `native_transport_witness`, `native_transport_fail_closed`, pre-existing `source_discontinuity` / `replacement_hot_cached_seek_ack`, and any hung/stale session or state.
4. If legacy remains unavailable, classify architecture **not fixed** and revert Test.70 when needed. If guard restores original, verify the original can be natively paused/seeked and that normal track changes reconnect correctly. Never treat seek callback latency as acoustic timing.

## Implications
**A guaranteed same-player replacement is not achievable by merely sharing an audio session ID or tweaking Media3/MediaPlayer delays.** A truly unified transport/output clock would require a proven Yandex-provided integration/SDK or a player integration route changing the current constraints (e.g. modification of Yandex or privileged OS integration). None is currently proven under unmodified Yandex + no root/new permissions. If Test.71 is silent on the legacy witness, stop repeating timing/remote commands and evaluate product/architecture options instead.
