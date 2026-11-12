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

## Eighth actual native ARM13 — #43239854803 — exact failing Push implementation and chronological order
- Exact TESTED code: `389b028b61fc554b0ab13e38c073f49fde1ae0f0`, immutable code backup `backup/android-a1-metrica-push-method-a-order-native-nogo-20261112`.
- GENUINE issuer Yandex first 16 splits, 75 sec 25/25 **PASS**. Independent signed CELIKOM ONE-APK installed alongside but main only 1/25, `IllegalStateException`, native NO-GO. Android fatal handler and all SDK methods remain fully original; suppression count **0**.
- Actual exact failing Throwable object: constructor stack `com.yandex.metrica.push.impl.*` (finite label `PUSH_IMPL`) in an **obfuscated method named `a`** (finite label `PUSH_METHOD_OBFUSCATED_A`). Message classified as modern AppMetrica not initialized.
- Bounded actual MAIN-PID timeline repeated across three startup attempts: `Application.onCreate ENTER → modern AppMetrica.activate ENTER/RETURN → Application.onCreate RETURN → modern ModulesFacade.isActivatedForApp TRUE, TRUE → error constructor in Push.impl / method a`. In second and third attempts the error also follows modern activation RETURNS and observed TRUE checks. Thus **not** simply "Push started before public AppMetrica.activate()" and **not** supported by the observed modern `ModulesFacade` predicate returning false.
- Public modern `AppMetrica.activate` 3/3 returned, `ModulesFacade.isActivatedForApp()` 6/6 TRUE, zero false. Legacy public facade hook NO_HOOK, public Push activate hooks NO_HOOK. A separate hidden SDK checker or internal lifecycle bug remains a hypothesis, NOT a finding.
- A previously publicly decompiled Yandex Music build has `com.yandex.metrica.push.impl` initialization that calls a composite facade predicate, but it is a **different APK/version**; do not assume its exact branch is the 2025.10.4 source.
- Android provider authority names were remapped for coinstallation; original service candidate present vs clone service candidate absent in a **post-crash** snapshot, which is not proof of causality.
- **NEXT:** inside an ephemeral GitHub runner inspect *the exact owner-provided 2025 XAPK* DEX method containing the specific Push exception string / method-a code, without committing or uploading DEX, APK, keys or raw vendor symbols. Emit ONLY finite structural categories and test whether it calls a different SDK state check. After a cause-proven fix, rerun original and clone real ARM13 75s/25 without suppressions. No Stage B until Stage A passes.
- Frozen A1 and Test.50 entirely untouched; no real authorization, hearing audio, pause, seek, Next, My Wave verification. Stage A **NO-GO** / B **LOCKED**.

## Ninth exact-source private DEX method check — pending
- Pure-Python offline read-only XAPK/Dex parser was added in `android/native-yandex-hooklab/ci/a1_private_push_dex_method.py`; it verifies exact publisher-uploaded SHA256/size, scans DEX string IDs, class_data/code_item, and produces **only fixed structural categories** for AppMetrica-not-initialized strings in Push implementation methods. No vendor code, paths, stack, keys, raw class/method names, APK, or DEX leave runner; no artifacts uploaded.
- The code-unit scan for calls is intentionally approximate (not a full instruction-flow disassembler). It cannot establish causality alone. Use results to decide a *narrow follow-up*, never silently force activation true or suppress the fatal.
- Workflow runs this before the real unsuppressed native ARM13 gate, retaining publisher-first installation and strict 75s 25/25 acceptance.

## Ninth exact-XAPK parser infrastructure fixes
- [CI #43243546438](https://github.com/manufact-test/nomusic/actions/runs/43243546438): private DEX classification failed **before** native work; the error was in the diagnostic parser, not Android product.
- [CI #43244032782](https://github.com/manufact-test/nomusic/actions/runs/43244032782): fixed safe-enum failure reporting identified `STR_END`: a vendor DEX string longer than the parser's 4KiB cap. This is normal for large embedded strings, not evidence of malformed APK.
- Updated parser to ignore non-target overlong strings, preserving a strict bounds cap and sanitized outputs. Added a synthetic regression case, then rerun original exact XAPK analysis.

## Tenth experiment — ephemeral exact Push boolean helpers (pending native ARM13)
- Fast static [#43249305119](https://github.com/manufact-test/nomusic/actions/runs/43249305119) succeeded: generated **3 narrowly scoped BOOLEAN helper targets** inside ephemeral CI from the exact verified publisher XAPK, without publishing names, APK, DEX or any generated Java source. The previous workflow strictly cleaned the generated file.
- ARM13 experiment now generates the same `PrivatePushTargets.java` transiently into the **own observer module during CI**, recompiles own diagnostic APK in-run, and registers only read-only boolean return hooks on the private helper method targets in **independent CELIKOM clone MAIN**. No target names are committed or logged.
- Every helper invocation proceeds the unmodified method once and returns exact value/exception. Bounded results `ENTER / TRUE / FALSE / THROW` are scoped to MAIN PID. Android original fatal handler never suppressed.
- A `NO_HOOK` result may indicate classloader mismatch or method mismatch and is not proof that no private SDK helper exists.
- Product Stage A remains NO-GO until original+clone same native ARM13 75s/25 without suppression; no audio/login/controls validated.

## 2026-11-12 — exact publisher DEX analysis, isolated static CI and transient private Push boolean observer
- Working experiment: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Stable base prior to the new probe: `a4d3cd53d189b62abd8d5019a487af24e2bc92bb` (full immutable backup: `backup/android-a1-metrica-push-8arm13-diagnostics-full-handoff-20261112`).
- Current new instrumented source: `95d3c86e13693cf7cabb3642ecba9f3170267699` (exact pre-handoff backup: `backup/android-a1-private-push-boolean-observer-exact-prehandoff-20261112`). This HEAD contains observer Java, parser regression tests, exact XAPK DEX static classifier and CI workflows. **It is not certified stable** until its unsuppressed ARM13 result is checked.
- Native [#43244588445](https://github.com/manufact-test/nomusic/actions/runs/43244588445) @ `398a21594ab87c0ca4a4312a315bf20f159db812`: issuer original **25/25 PASS**, separate ONE-APK clone **1/25 FAIL** (direct `PUSH_IMPL` AppMetrica `DETAIL_NOT_INITIALIZED`, no fatal suppression). A private offline scanner successfully read six DEX files in the original uploaded 2025.10.4 XAPK and found two Push implementation methods referencing initialization error, including obfuscated `a`. These methods called Push implementation helpers rather than the modern ModulesFacade directly.
- Changed CI topology: `.github/workflows/android-a1-private-push-dex-triage.yml` is fast static-only, separate from expensive `.github/workflows/android-a1-metrica-init-state-observer-arm13.yml`. The latter still runs on ARM hardware and verifies publisher original then independent CELIKOM clone with 75 seconds/25 samples and **no suppressions**.
- Static-only [#43246459482](https://github.com/manufact-test/nomusic/actions/runs/43246459482) **PASS**: direct helper chain only.
- Static-only [#43246880309](https://github.com/manufact-test/nomusic/actions/runs/43246880309) **PASS**: followed Push helpers including an interface implementor; within 3 levels, there is a **modern ModulesFacade predicate**. That does NOT contradict real earlier 6/6 TRUE or prove what occurs at fatal point.
- Static-only [#43247213000](https://github.com/manufact-test/nomusic/actions/runs/43247213000) **PASS**: separately classified methods `a` with Push error text. Both contained helper references and an interface-dispatch path leading to the modern predicate. Approximate bytecode scanning, not control-flow proof.
- Static-only [#43247769734](https://github.com/manufact-test/nomusic/actions/runs/43247769734) and [#43248034379](https://github.com/manufact-test/nomusic/actions/runs/43248034379) **PASS**: nearest forward guard call categorizes as Java runtime (likely constructing exception) and does NOT independently establish condition producing the error. **Do not edit or bypass original condition based on this**.
- Static-only [#43249305119](https://github.com/manufact-test/nomusic/actions/runs/43249305119) **PASS**: generated **3 boolean-returning Push helper method targets** from exact owner-uploaded source, names and generated Java held **only transiently inside private CI runner**, never committed/uploaded/logged.
- Current native [#43249731641](https://github.com/manufact-test/nomusic/actions/runs/43249731641) source `95d3c86e13693cf7cabb3642ecba9f3170267699`: installs read-only hooks for just those private Push helpers and records bounded `ENTER/TRUE/FALSE/THROW` and hook availability, preserving original return and thrown exceptions. It is **in progress when documenting this note**; check actual completed CI sanitized report before stating outcome. Android APK/DEX, keys, names, full stacks and user data must never appear publicly. Workflow removes private generated `PrivatePushTargets.java`.
- Always preserve accepted Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`, frozen A1 `cc4cb0f93489168db21502f3ef195855ae9fb743`; no merges, no release, no live Yandex account/audio or security-workaround claims. Product **Stage A NO-GO / Stage B LOCKED**, regardless of diagnostic CI unit PASS, until unsuppressed native clone `25/25` alongside original stock.
