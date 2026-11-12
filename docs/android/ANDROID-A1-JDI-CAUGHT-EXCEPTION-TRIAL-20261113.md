# CELIKOM A1 — exact caught exception JDI trial, 13 November 2026

## Outcome
**NO-GO.** No specific post-TRUE throwing invocation is proven. Original Yandex **25/25 PASS** and native clone CELIKOM **1/25 FAIL** remain reproducible. The fatal Push/AppMetrica `DETAIL_NOT_INITIALIZED` is genuine and was not swallowed.

## Why this experiment existed
Exact private DEX analysis allowed a path from the verified TRUE branch via an exceptional invoke and catch handler to the modeled error throw, but structural reachability did not identify which call actually failed. Rather than hooking dozens of SDK methods, a disposable debug clone carried a **single exact JDI method-entry + caught-exception event** experiment; no third-party SDK bytecode was modified.

## Tests
- [ARM13 #43319384496](https://github.com/manufact-test/nomusic/actions/runs/43319384496): first JDI trial inconclusive, original **25/25**, clone **1/25**.
- [ARM13 #43322408574](https://github.com/manufact-test/nomusic/actions/runs/43322408574): private exact method preflight PASS, **33** protected invokes (not runtime calls), clone **1/25**, JDI ADB stage inconclusive.
- [Isolated transport #43323861193](https://github.com/manufact-test/nomusic/actions/runs/43323861193): guest `adbd` **running**, ARM host adb **absent**. No vendor APK read or installed.
- [ARM13 #43324105516](https://github.com/manufact-test/nomusic/actions/runs/43324105516): native ARM apt adb installed, x86 Android SDK adb shadowed PATH and produced `Exec format error` before Android.
- [ARM13 #43324871739](https://github.com/manufact-test/nomusic/actions/runs/43324871739): native ADB selected, JDI launch stalled at streaming `adb jdwp` PID snapshot (`JDI_JDWP_PID_INCONCLUSIVE`); direct known-PID attach replaces it.
- [ARM13 #43325076715](https://github.com/manufact-test/nomusic/actions/runs/43325076715): **source-verified target**, original **25/25 PASS**, clone **1/25 FAIL**, exact debugger `VM_EXIT`, target entries **0**, caught events **0**, no causal location observed.

## Interpretation and cleanup
A running debugger with zero events before VM exit cannot identify the throwing call or disprove the hypothesized catch path. Do not classify the earlier allocations of IllegalArgumentException as causes. The temporary lab clone carried `android:debuggable` for this test only; it is not a valid product or release. No exception suppression, forced SDK success flags, live-user accounts, phone access or audio tests.

Full experiment source: `backup/android-a1-jdi-exact-catch-vmexit-nogo-20261113` @ `1cee2b2e999a74030a82ec0de4aa812c65fdf350`. Original exact clean reference: `4fff1f960a66a69432521fabe64a130142838362`, archived `backup/android-a1-pre-jdi-catch-identity-20261113`. Main A runtime and workflow restored byte-for-byte from that reference; this note and the handoff are the only intentional changes from the original baseline.

**Stage A NO-GO, Stage B LOCKED.** Only continue from an independently justified single causal hypothesis, with genuine unsuppressed 25/25 original + clone acceptance; static checks alone are insufficient.
