# CELIKOM Android A1 — native ARM13 merged logcat time-order A/B (11.11.2026)

**A1 native clone MAIN/UI: STILL NO-GO.** This reports one new Android read-only diagnostic gate, not a working APK, cause of the self-exit, or an actionable anti-tamper/signature bypass.

## Exact source and test

- Source commit: `df5037fb2cbbc74e440dae5d88964960f0589ddb` in `experiment/android-native-a1-lspatch-clone-loader0-20261111`.
- [CI #43003533643](https://github.com/manufact-test/nomusic/actions/runs/43003533643), native ARM64 Linux + ARMv7 Android13 Redroid disposable guest, all **54 tests passed** (20 + 7 new timeline + 17 + 6 + 4). The final CI result is **FAILURE by strict native MAIN gate** because all lab clones still self-exit, not because tests or boot failed.
- New `android/native-yandex-hooklab/native_arm13_timeline_origin.py` classifies ONE `adb logcat -d -b main -b events -v threadtime` stream, not separately concatenated buffers. The stream stays private. PID-scoped and timestamp-checked categories, never raw lines, exception text, tag strings, stack, credentials or PID, are reported. Same classifier is used against an alive, publisher-signed ORIGINAL MAIN process.

## Read-only true-ARM findings

| Subject | Time-order marker | Status |
| --- | --- | --- |
| Independently signed FIVE clone splits, zero loader | Both exact MAIN PIDs emitted E/F `IllegalStateException` **strictly between their exact main process start and death event** in the merged chronological stream; timestamps non-decreasing | MAIN two `EXIT_SELF(0)`, no UI persistence |
| Independently signed ONE merged clone, zero loader | Identical valid chronology: 2/2 exact MAIN self-exits with error marker between start and death | MAIN NO-GO |
| Independently signed ONE merged LSPatch0 clone, zero modules | Error markers still attributed to both exact MAIN PIDs, but merged logcat `threadtime` order was **not monotonic** in this run; **temporal ordering cannot be asserted** by the strict observer | MAIN NO-GO |
| Unchanged publisher-signed original, FIVE splits | Publisher MAIN alive/resumed. No same-PID `IllegalStateException` marker observed in this bounded window | Original control PASS (startup, not audio/login/Play Protect) |

The `IllegalStateException` marker came from an unrecognized arbitrary app/system logger tag. The privacy classifier emits only `OTHER_OR_UNKNOWN` rather than raw tag names. **Do not infer Yandex Music/Passport/DRM/identity code origin** from this. In no case was an exact Java exception stack frame available. Correlation and event ordering do **not establish** what invoked `System.exit` or why the throwable was logged.

## Decision

Repeating identical layouts or the same E/F marker counts no longer adds causal information. The next isolated diagnostic may use standard Android ART method tracing via `android:profileable android:shell=true` **only on separately signed, ephemeral CELIKOM research clone**; never the publisher original, user's HONOR, Test.50, or released APK. A trace must be processed privately and reduced to known `System.exit`/process-kill and coarse caller category, no raw symbol/payload disclosure. The clone could still self-exit before a trace is available; that result would remain inconclusive.

No signing/DRM/Passport/Play Protect protection bypass, root, account capture, external Yandex outreach, publisher APK distribution or delivery of unverified Android APK.

**Frozen backup of tested source before ART experiment:** `backup/android-a1-true-arm13-merged-timeline-pre-art-profile-20261111` @ `df5037fb2cbbc74e440dae5d88964960f0589ddb`. Approved Stage A remains NO-GO; Stage B remains locked.
