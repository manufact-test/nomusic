# CELIKOM Android A1 — true ARM13 exact-MAIN read-only startup error witness (11 Nov 2026)

**Status: A1 native UI/audio NO-GO.** This is a concrete engineering diagnostic improvement, not a vendor bypass, APK deliverable or root-cause proof. No Yandex outreach or user action requested.

## New read-only code and CI

Working branch: `experiment/android-native-a1-lspatch-clone-loader0-20261111`. Final diagnostic source commit `b4ba630adbe6d5f73549059c035c672767a37c23`.

New files:
- `android/native-yandex-hooklab/native_arm13_startup_observer.py`: Android main-process-only public log buffer and ApplicationExitInfo classification with fresh-launch PID filtering; no raw log, PID, stack, path or user data emitted.
- `android/native-yandex-hooklab/tests/test_native_arm13_startup_observer.py`: 11 privacy, scoping and regression tests.
Updated:
- `android/native-yandex-hooklab/clone_native_arm13_redroid_gate.py`: connects public events/main-log observations to **real native ARM13** for all three previous clone layouts, compares the unchanged signed original, ensures old exit history cannot be attributed to a new launch.
- `.github/workflows/android-native-a1-arm13-clone-main-ab.yml`: requires these tests before launching the disposable Android guest.

**[New CI 42999367827](https://github.com/manufact-test/nomusic/actions/runs/42999367827)**: 11+17+6+4 = **38 tests PASS**, native ARM Android13 guest boots; private five-split, merged-direct, and merged-LSPatch0 experimental clones all again finish MAIN with `EXIT_SELF`, exit status `ZERO`. CI overall **FAILURE by strict native product gate**, not a syntax or unit-test failure. **Original publisher-signed five splits still launch and remain alive/resumed**. No change to original bytes, package-signing bypass, account use, user phone, Play Protect, production or uploaded APK artifacts.

## New evidence, carefully scoped

Across all THREE independent clone layouts:
- Only **new/current exact MAIN** ApplicationExitInfo records included. No historical exact-MAIN exits attributed to this run; no helper-process PID or original process was classified as clone MAIN.
- MAIN log buffer contains E/F/W messages for current process; bounded throwable marker **`ILLEGAL_STATE`** (matches `IllegalStateException`) and general `OTHER_THROWABLE` observed for all three. `ILLEGAL_ARGUMENT`, `SECURITY`, `NATIVE_LINK`, `CLASS_LOADING`, `NULL_STATE` **not observed by this classifier**.
- No AndroidRuntime fatal marker, no observed `uncaughtException` marker, and no crash-buffer fatal or native signal. There are **zero scoped Java stack frames** following those logged exception markers, so **no stack subsystem** can be assigned. The mere presence of logged `IllegalStateException` **does not prove it caused EXIT_SELF(0)**.
- Events buffer contains ~82–99 event lines but **none of the expected AOSP am_* lifecycle tags**, even for original Yandex that demonstrably stayed alive. Therefore the empty lifecycle arrays are an **unsupported diagnostic signal in this Redroid environment**, **NOT** evidence that no activity events occurred. Exact app token and helper references were seen, but lifecycle parser must not be used for an inference here.
- Headless Redroid has no GMS/Play Protect. Original activity resume is a lifecycle observation, not a full foreground UI/audio/login acceptance.

## Concrete conclusions and remaining gate

This independently confirms the nearest presently observable clue is **MAIN-scoped logged IllegalStateException before its self-exit**. The precise initiating condition and subsystem are still **unknown**. Do not label the result a verified signature check, Passport failure, anti-tamper mechanism or decoder issue.

The clone's APK layout and LSPatch0 are again non-necessary causes. Repeating the same 3 layouts, changing ABI/ZIP alignment or merely collecting the same log fields cannot solve native MAIN. Next engineering is only a **new evidence-bearing and safe investigation** of the startup exception in a controlled copy or own instrumentation, without accessing user secrets, modifying publisher authentication/DRM or bypassing Play Protect. No user APK until full native UI, same original decoder and audible owner acceptance are validated.

**Existing reference samples:** [ChromaSync uploaded APK offline comparison](ANDROID-A1-CHROMASYNC-APK-OFFLINE-COMPARISON-20261111.md) confirms an older host and configured bypass level 2, not evidence that the competitor works side-by-side without bypass. Do not copy its module or signing/security bypass. [Stage-A evidence JSON](CELIKOM-ANDROID-A1-STAGE-A-EVIDENCE-20261111.json) remains unchanged and NO-GO.

**Exact backup BEFORE new diagnostics:** `backup/android-a1-before-arm13-readonly-startup-diagnostics-20261111` @ `da87689e70ca2b268b066b3dd2f9e78b5c7085f1`.
**Exact backup of first successful MAIN error witness:** `backup/android-a1-arm13-fresh-main-error-witness-20261111` @ `e611c230a54ffb7160287846ff86fa50488028f5`.

**Explicit owner direction (11 Nov):** Do **not** contact Yandex or present partnership outreach as an engineering action. The approved one-APK native UI/single-decoder product and no-bypass/Play-Protect constraints remain unchanged. Do not start Stage B before audible accepted Stage A.
