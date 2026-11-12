# CELIKOM Android A1 — AppMetrica native ARM13 init-state observer, 2026-11-12

- New branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112` from exact lab-success source `5891ee655061d2049d1e0b9fa7a83927f3b563d2`.
- Immutable pretrial backup: `backup/android-a1-metrica-init-state-observer-pretrial-20261112`.
- Previous pair of green ARM13 runs used one **LAB ONLY** suppressed Android fatal exception, **not** releasable.
- This diagnostic patch uses prior known read-only activation hooks and classifies legacy/modern AppMetrica calls, activation return/throw, context namespace, SDK/context classloader match and execution phase relative to Android Application.onCreate. All outputs finite and MAIN-PID scoped. **No fatal suppression.**
- CI compiles the scoped observer privately on its ARM host and deletes all APK/key/test assets; no binary artifacts uploaded.
- Acceptance unchanged: original real ARM13 native 75s/25, independent ONE-APK clone co-installed side by side native 75s/25 **with no suppression**. Until that passes: Stage A NO-GO / B LOCKED. No real account, audio or playback controls proven.
- Test.50 and frozen main A1 untouched. No raw vendor messages, tokens, secrets, users' accounts, or third-party binaries exposed.

## First actual native no-suppression run: #43222681617 (FAIL, valid causal result)
- Stock publisher 16 split package installed first and held native MAIN 75s/25 PASS.
- Own independent ONE APK installs beside stock but Java MAIN dies; resumed 1/25.
- Exactly three **modern** AppMetrica public `activate` enter/return and zero throws, all DURING_ONCREATE; correct CLONE Context and matching SDK classloader; Application.onCreate returned.
- Exact AppMetrica SDK fatal Throwable still `DETAIL_NOT_INITIALIZED` and `DIRECT_IDENTITY`; suppressed count **0**.
- This rules out missing public modern activation and incorrect root Context/classloader equality as sufficient explanations. Effective SDK initialization and later reset/race remain **unproven**.
- Next diagnostic (read-only): optional internal AppMetricaFacade activation/full-init/reset transitions and public SDK reporter/event API call outcomes. Class obfuscation can prevent internal hooks, in which case **NO_HOOK is inconclusive**.
- Exact first-run code backup: `backup/android-a1-metrica-nosuppression-native-fail-exact-20261112` at `1a16d47701afcd2a1fd88b802e7fd5a9a3d924cf`.

## Second actual no-suppression native differential #43224344294
- Source at `66a36f2fa0f7fab718582f8c98efbc7bfb37f61c`; compiled own instrumentation, all static regressions, private source validation, Android13 native boot and original-first install all SUCCESS.
- Publisher official native MAIN **75s 25/25 PASS**, genuine independent ONE-APK clone co-installed but **1/25 resumed**, `JAVA_CRASH/ILLEGAL_STATE`; CI **FAIL** by strict NO-GO gate.
- Modern SDK public `activate` **ENTER=3 RETURN=3 THROW=0** during Application.onCreate, CLONE context, matching Context+SDK classloader, Application.onCreate returned.
- Own observer captured AppMetrica public calls: **14× getReporter() ENTER/RETURN**, **1× getDeviceId() ENTER/RETURN**, **1× reportEvent() ENTER/RETURN**; no observed public API THROW.
- SDK implementation `io.appmetrica.analytics.impl.AppMetricaFacade` **NO_HOOK** (likely minification/obfuscation, NOT proof that the SDK has no state transitions); internal initialized/reset state unknown.
- Actual fatal exact `DETAIL_NOT_INITIALIZED` created inside SDK and dispatched by Android, `DIRECT_IDENTITY`; **zero suppressed exceptions**. The public API returning is not proof that the later reporter implementation/backend is initialized.
- **NEXT**: identify concrete exception callsite and internal reporter lifecycle in a sanitized clone-only dynamic probe, or compare exact SDK initialization/service binding between original and clone; investigate provider/service identity with a proper A/B, not blind reactivation or crash handling replacement.
- No vendor/clone APK artifacts or signing keys uploaded. Test.50, frozen main, real phone, accounts and backend untouched. Product Stage A **NO-GO**, Stage B **LOCKED**.

## References/immutable sources
- Two old green laboratory-only 75s runs: #43217132456, #43217178231; they relied on one exact fatal suppression.
- First no-suppression: [#43222681617](https://github.com/manufact-test/nomusic/actions/runs/43222681617) @ `1a16d47701afcd2a1fd88b802e7fd5a9a3d924cf`; backup `backup/android-a1-metrica-nosuppression-native-fail-exact-20261112`.
- Second no-suppression: [#43224344294](https://github.com/manufact-test/nomusic/actions/runs/43224344294) @ `66a36f2fa0f7fab718582f8c98efbc7bfb37f61c`; backup `backup/android-a1-metrica-readonly-v2-actual-arm13-nogo-source-20261112`.

## Third read-only causal control preparation
After public `getReporter()` returned successfully 14 times in native #43224344294 and internal AppMetricaFacade state hooks did not register, the next bounded observation hooks only concrete reporter methods returned by public SDK, with finite event labels and no args/results/Throwable text. Android kill handler remains fully original. Any result **must** be checked on real ARM13, never extrapolated from unit tests.

## Third actual ARM13 no-suppression run — #43226144866
- Exact tested source `15b1c10338b25fdf0f41b7667cf67e160abc3fe0`; source-only immutable backup `backup/android-a1-metrica-readonly-reporter-native-nogo-source-20261112`.
- Public module builds with pinned AAPT2, static tests pass, source verified privately, native Android13 boots.
- Stock issuer app **75s 25/25 PASS**; clone ONE-APK installed beside original, native MAIN **1/25 resumed**, fatal Android Java crash; CI **NO-GO**, not technical infrastructure issue.
- Own dynamic observer successfully attached to **actual SDK reporter instances returned by `getReporter`**; concrete `reporter.resumeSession/pauseSession` 8 ENTER/8 RETURN, `reporter.reportEvent` 2 ENTER/2 RETURN, **no reporter THROW**.
- Public SDK `activate` 3 ENTER/3 RETURN, `getReporter` and other public calls also RETURN. The exact exception remains AppMetrica `DETAIL_NOT_INITIALIZED` with direct fatal Throwable identity and **zero suppression**.
- Therefore the error does **not** arise synchronously in the instrumented reporter methods. Investigate SDK asynchronous worker/internal lifecycle or service/provider initialization, not another activate call. Internal class state probe was NO_HOOK (obfuscation/unknown), no conclusion about state.
- No other app/audio/account touched, original XAPK/owned clone/artifact/key never uploaded. Product Stage A **NO-GO**, B **LOCKED**.
