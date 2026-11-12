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

## Fourth no-suppression causal probe (pending)
- The constructor observer classifies the first AppMetrica SDK stack frame into a fixed family: modern/public/internal/crash/service/startup/proxy/reporter or legacy SDK.
- Also classifies coroutine vs executor/handler and thread context-classloader compared to the clone Application loader.
- The source family is stored in-process and matched by identity to the exact fatal Throwable (FATAL_THROW_SITE); no raw stack, vendor symbols or credentials in logs.
- Hypothesis under test: 3 successful modern SDK activations may precede a failure in a distinct legacy SDK path, alternate classloader, or asynchronous worker. Test it before making any behavioral fix.

## Fourth actual no-suppression native ARM13: #43228744229
- Exact tested source: affbbf7a45e54ee6d9bf21302b7e4588af11451f; immutable pretrial backup: backup/android-a1-metrica-fatal-legacy-namespace-proven-20261112.
- Publisher original remains 75s/25 PASS; clone ONE APK still co-installs but native 1/25 JAVA_CRASH. No suppressed exceptions.
- Crucial identity-matched observation: the exact `IllegalStateException` is constructed with nearest stack family `com.yandex.metrica.*` (SDK_LEGACY), NOT `io.appmetrica.analytics.*`. Context thread classloader matches clone app classloader. The text class remains DETAIL_NOT_INITIALIZED. Three modern AppMetrica activate enter/return, zero throws; zero legacy activate observed.
- Important ambiguity: `com.yandex.metrica.*` might be an **internal implementation package** called by the modern SDK, not a second public API needing its own activate. This result is a namespace differential, not proof of a missing legacy activate call.
- Next no-suppression probe distinguishes legacy public vs internal stack frame, checks existence of the legacy public class/activate signature without invoking it, and classifies error text mention into fixed enum. No blind activate or modification of Android fatal handling.

## Fifth actual no-suppression native ARM13: #43230162000
- Code tested: `e46da1f3c5199347b0cf8aa2b90bd3d47935821a`, immutable exact backup `backup/android-a1-metrica-modern-only-public-legacy-internal-nogo-20261112`.
- Real original issuer 16/16 co-installed first: native 75s **25/25 PASS**. Independent ONE-APK clone: **1/25 resumed**, `JAVA_CRASH` and direct AppMetrica `DETAIL_NOT_INITIALIZED`; suppression **0**.
- Exact fatal constructor stack nearest namespace: `com.yandex.metrica.*`, **not** the declared public `YandexMetrica` class and **not** the conventional `com.yandex.metrica.impl.*` prefix. Class probe for `com.yandex.metrica.YandexMetrica` reported `CLASS_MISSING`; the probe exception handler also covers reflective hook failures, so treat this as **not successfully discovered**, not definitive absence from every possible classloader. No legacy activate signature registered or invocation observed.
- Modern `io.appmetrica.analytics.AppMetrica` public class and `activate(Context,...)` signature were found; all 3 public `activate` calls returned. The exact fatal message contains a fixed `HINT_MODERN_API` lexical reference, never the original raw text. SDK thread context classloader matches clone Application. Therefore **do not blindly invoke legacy activate**.
- Official AppMetrica 6 migration guidance (https://appmetrica.yandex.ru/docs/ru/sdk/android/analytics/migration-io-6-0-0) explains `com.yandex.metrica` old and `io.appmetrica.analytics` new namespaces can be present together and explicitly cautions against activating both with one API key.
- Root still UNKNOWN: modern public `activate()` returning does not prove asynchronous initialization has finished; SDK internal state must be established with a targeted service/provider/worker causal check. No merge or live audio authorization. Stage A NO-GO, B LOCKED.

## Sixth read-only causality check (pending native ARM13)
- Narrow the exact fatal SDK frame from `com.yandex.metrica.*` into fixed component subpackages (coreutils, coreapi, push, network, identifiers, etc.), never raw class or method.
- Capture two **read-only**, bounded Android process/service snapshots: original after passing 75s; independent clone after its 75s observation. No process IDs, raw service names, accounts, stack traces or APK content leave the runner. A Metrica process/service record candidate does **NOT** prove SDK readiness; absence is inconclusive when a dump is missing/partial.
- No fatal masking, no calls to any AppMetrica activate or internal API, no user session or audio; Stage A NO-GO/B LOCKED until a genuine no-suppression clone 25/25.

## Sixth no-suppression ARM13 result — #43232182558
- Exact source `91efb19a8446bf0a0d84bfd14fb9167a734317f3`; original 75s 25/25 PASS; clone ONE-APK beside it 1/25, direct `IllegalStateException` `DETAIL_NOT_INITIALIZED`, suppression 0. Clone app may die while auxiliary process lives.
- The nearest exact fatal SDK code is **`SDK_PUSH` = `com.yandex.metrica.push.*`**. Text remains `HINT_MODERN_API` (modern AppMetrica), confirming the push subsystem rather than the bare analytics public API.
- Original snapshot: 3 original processes, including 1 metrica auxiliary process; service record candidate true. Clone snapshot: 1 matching process (metrica auxiliary), service record candidate false. Guest process/service snapshots are *late observations*, not proof of historical absence or faulty binding; do not equate with definitive root cause.
- Public source `appmetrica/push-sdk-android` has `AppMetricaPushCore` throwing `IllegalStateException` when `ModulesFacade.isActivatedForApp()` is false. This is a **strong source-level hypothesis**, not yet proved that the exact deployed vendor version uses that same branch.
- Seventh experiment instruments existing `ModulesFacade.isActivatedForApp` calls (modern and legacy variants) and actual public Push activate calls **read-only**, preserving exceptions. No extra activate and no service removal. Only if real clone produces the predicted FALSE at the fatal point can ordering or duplicate SDK state be considered a confirmed cause.

## Seventh no-suppression ARM13: #43238265378
- Exact tested `e09d7dc61f914e7cc1250c39f7d82ddb1298ba3a`, immutable backup `backup/android-a1-metrica-push-predicate-true-arm13-nogo-source-20261112`.
- Genuine Yandex original 75s 25/25 PASS; separate CELIKOM ONE-APK installed alongside but still 1/25 JAVA_CRASH, direct `SDK_PUSH` `DETAIL_NOT_INITIALIZED`; suppressions 0.
- Key negative test: instrumented **modern `io.appmetrica.analytics.ModulesFacade.isActivatedForApp()` returned TRUE on all 6 calls**, never false. Legacy ModulesFacade hook NO_HOOK. Neither known public `AppMetricaPush.activate` class/name hook registered, so the Push callsite is still not established.
- This **does not confirm** the initial theory of an unactivated modern AppMetrica flag; do not add blind activate or falsify a predicate. Earlier public `AppMetrica.activate` 3/3 returned.
- Source `appmetrica/push-sdk-android` and older independent Yandex Music reverse-engineered version have a Push-initialization predicate, but exact packaged 2025 path may differ. Next targeted observation classifies only nearest SDK_PUSH subpackage/method type and the bounded ordering of successful activation and ModulesFacade observations. All raw symbols/threads/private payloads remain inside the ephemeral runner.
