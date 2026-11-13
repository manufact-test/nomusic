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

## 13 November — JDI v2 caught-event-only control, completed NO-GO

- One narrow follow-up to the previous debugger's **0 exact method entries**: register one `ExceptionRequest(caught=true)` before allowing the disposable debug clone to resume; retain evidence ONLY where the handler location matches the unique privately verified `Push.impl.a` overload. No broad per-method hooks, no exception swallowing or modified vendor SDK bytecode.
- Native real [ARM13 #43381245799](https://github.com/manufact-test/nomusic/actions/runs/43381245799), exact tested commit `89e8cfa2757043ee6ce1a5078e3ce19ced51b70a`: original publisher **25/25 PASS**; clone **1/25 FAIL**, unchanged `METRICA_READONLY_NATIVE_MAIN_NO_GO`. Private DEX preflight verified **one exact method / 33 catch-covered potential invokes** (not runtime calls). JDI received **526 caught-event notifications**, but **0 events matched the exact fatal handler**; JDI terminal status `ATTACH_OR_RUNTIME_FAILURE`, not a clean causal trace.
- This establishes that debug transport emitted caught events; it **does not prove the exact catch handler was absent in ordinary no-debug execution**, nor that any earlier `IllegalArgumentException` triggered it. Throwing invocation remains **UNKNOWN**. No further generic JDI/Throwable sweeps are justified by this data.
- Before test: `backup/android-a1-before-caught-event-only-jdi-20261113` @ `8befb8eb2b7548f732e9b333eb5ac1dc838c19a5`; exact experimental source: `backup/android-a1-jdi-eventonly-throw-catch-trial-20261113` @ `89e8cfa2757043ee6ce1a5078e3ce19ced51b70a`. All temporary JDI Java/Python/test source, debug-only manifest changes and workflow flags removed from working A branch; original no-debug runtime/workflow restored byte-for-byte from pretrial baseline. No user phone, original installation, Test.50, frozen A1, production, Windows, backend or audio touched.
- Acceptance unchanged: **Stage A NO-GO / Stage B LOCKED**. Do not create user APK or make speculative SDK fixes. Next useful work requires one independent source-grounded causal state difference and an unsuppressed 25/25 original+clone acceptance test.
