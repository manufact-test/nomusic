# CELIKOM Android A1 — new lead handoff after AppMetrica read-only native ARM13 controls, 12.11.2026

## Read first
- `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md`.
- `docs/android/ANDROID-A1-2025-DISTINCT-ONEAPK-NATIVE-75S-LAB-LEAD-HANDOFF-20261112.md` and prior `docs/android/NEXT-CHAT-ANDROID-A1-2025-METRICA-LAB75S-20261112.md` (restored here from doc-only HEAD `9de7a2f50ddba92476cffcf3e69e83ff9c5e035c`).
- **Most recent truth:** `docs/android/ANDROID-A1-METRICA-INIT-STATE-OBSERVER-20261112.md`.
- GitHub issues #41 and #42, source-only audio contract `android/native-audio-contract/source-contract.mjs` merged by lead and already tested, **NOT live Android audio**.

## Repository state, do not restart
- Experimental branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112` (the latest HEAD contains this handoff; consult GitHub for final exact SHA).
- Last exact SOURCE tested in actual native ARM13: `66a36f2fa0f7fab718582f8c98efbc7bfb37f61c`, immutable backup `backup/android-a1-metrica-readonly-v2-actual-arm13-nogo-source-20261112`.
- Pre-work immutable source `5891ee655061d2049d1e0b9fa7a83927f3b563d2`, backup `backup/android-a1-2025-distinct-oneapk-native-75s-metrica-lab-pass-20261112` (LAB ONLY, fatal suppressed).
- Accepted Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`; frozen A1 `cc4cb0f93489168db21502f3ef195855ae9fb743`, DO NOT CHANGE.

## Proven real outcomes
- Previous LAB-ONLY two 75s green runs #43217132456 and #43217178231: original and single clone coinstalled, but one precise AppMetrica `IllegalStateException` fatal in Android kill handler was intentionally suppressed. Not product-ready.
- First no-suppression actual ARM13 [#43222681617](https://github.com/manufact-test/nomusic/actions/runs/43222681617) **FAIL**: original 16/16 stock 75s/25 PASS; one clone installed alongside but MAIN 1/25. MODERN `AppMetrica.activate` ENTER=3 RETURN=3 THROW=0 during Application.onCreate; Context CLONE, classloader MATCH; direct SDK `NOT_INITIALIZED` fatal; suppression 0.
- Second no-suppression actual ARM13 [#43224344294](https://github.com/manufact-test/nomusic/actions/runs/43224344294) **FAIL** same outcome, with extra observer: public AppMetrica `getReporter` 14/14 RETURNS, `getDeviceId` 1/1, `reportEvent` 1/1. No public API throw. Internal `AppMetricaFacade` state hook did NOT register (probable obfuscation). Fatal still SDK `DETAIL_NOT_INITIALIZED` `DIRECT_IDENTITY`.

## Next precise technical move
Find the **actual** reporter/async internal SDK callsite throwing the initialized-state exception after public activate returned; study SDK lifecycle and provider/service/process binding differential, ideally a safe bound-enum in-memory probe on the same disposable clone. Current code's own scoped observer and parser infrastructure is reusable; no user accounts/private messages/raw vendor stack or API keys in public logs.

Do NOT simply call activate again, delete AppMetrica manifest components, suppress fatal, rewrite Passport/DRM, fabricate an audio engine or mark ready. A successful independent ONE APK native 75s 25/25 **without** suppression remains mandatory before sound/seek/pause/Next/MyWave/B42 integration. Stage A NO-GO / Stage B LOCKED.

## Security and workflow
- Keep publisher-signed XAPK and own lab APK/signing keys in ephemeral GitHub runner only, **no uploaded artifacts**. Existing CI uses pinned SHA-256 ARM64 aapt2 and exact publisher private input verification.
- Preserve original signed publisher install FIRST then clone ONE-APK second in same genuine native ARM13 guest.
- Before edits create exact backup; save docs and issue #41 with accurate failure status. Do not merge into frozen A1, release or Test.50.

## Third experimental result — required update
Actual [ARM13 #43226144866](https://github.com/manufact-test/nomusic/actions/runs/43226144866), source `15b1c10338b25fdf0f41b7667cf67e160abc3fe0`: native original 25/25 PASS, independent clone 1/25 and direct SDK `NOT_INITIALIZED` fatal, suppression zero. Real reporter implementation hooks **registered** and saw 8 session operations + 2 reportEvent all RETURN and zero THROW. Public activation 3/3 returns. Error is therefore outside these synchronous APIs, likely downstream async SDK process (not yet proved). **Do not** infer Android native ready. Backups: `backup/android-a1-metrica-readonly-reporter-native-nogo-source-20261112`.

**Current follow-up:** classify actual SDK async work lifecycle/fatal callsite and service/provider/process identity safely on disposable ARM13, then make only a causal fix and rerun unsuppressed original+clone 75s/25. Do not merge or ship until PASS.

## Newer fifth ARM13 data — 12 Nov 2026
[#43230162000](https://github.com/manufact-test/nomusic/actions/runs/43230162000) at exact `e46da1f3c5199347b0cf8aa2b90bd3d47935821a`: original native **25/25 PASS**, independent clone **1/25, JAVA_CRASH**, zero suppression. Same Throwable originates in `com.yandex.metrica.*` code, but contains a *modern AppMetrica* initialization-message marker. Modern public class/activate exists and returns 3/3. Legacy public YandexMetrica class/signature not successfully resolved by observer (no legacy activation). Therefore DO NOT add legacy SDK activate or share the same analytics key. The `com.yandex.metrica` family can be internal legacy-package implementation/dependency; it does not prove separate public SDK.
Backup: `backup/android-a1-metrica-modern-only-public-legacy-internal-nogo-20261112`.
**Next**: classify exact failing SDK component/worker/service init and compare clone with stock under privacy-bounded native ARM13, then try only a cause-proven fix. Product A NO-GO / B LOCKED.

## Latest eighth native experiment supersedes earlier ordering hypotheses
Real [CI #43239854803](https://github.com/manufact-test/nomusic/actions/runs/43239854803) source `389b028b61fc554b0ab13e38c073f49fde1ae0f0` and immutable exact backup `backup/android-a1-metrica-push-method-a-order-native-nogo-20261112`:

Original Yandex 75s/25 PASS; independently signed coinstalled CELIKOM 1/25, JAVA_CRASH, SDK Push impl. `AppMetrica.activate` 3/3 RETURN, modern `ModulesFacade.isActivatedForApp()` 6/6 TRUE. Exception comes **after** `Application.onCreate` and activation, inside `com.yandex.metrica.push.impl.*` method `a`, from the exact object fatally dispatched. 0 crash suppression. This directly contradicts simple "Push before activate" and "modern ModulesFacade returns false" theories. Exact 2025 binary method has not been statically inspected. Don't assume an older YandexMusic reverse-engineered source is bytecode-identical.

The next most valuable move is private/offline XAPK DEX analysis on the disposable CI runner: detect only the exact failure string's method and its actual predicate/dependencies; never emit proprietary DEX, class names, credentials or raw logs, then make **a causal, product-grade fix**, not another observer-only experiment. Keep 75s 25/25 real ARM13 no-suppression gate strict and original app coinstalled. Stage A NO-GO/B LOCKED. Further proof logs in `docs/android/ANDROID-A1-METRICA-INIT-STATE-OBSERVER-20261112.md`.

## NEWEST HANDOFF — 12.11.2026 — exact Push helper target probe
**Most relevant source files:**
- `android/native-yandex-hooklab/ci/a1_private_push_dex_method.py` — exact SHA-verified private XAPK DEX structural scan; no original file published. Option `--private-java` generates `PrivatePushTargets.java` strictly transiently for ARM CI.
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java` — `installPrivatePushBoolWitness` runs three read-only boolean-return probes; does `chain.proceed()` and returns original value or rethrows same error.
- `android/native-yandex-hooklab/ci/a1_metrica_witness_private_parser.py` — fixed enum, MAIN PID scoped `PUSH_HELPER_HOOK`, `PUSH_HELPER_BOOL` and count/timeline. Its synthetic regression test is `test_a1_metrica_witness_private_parser.py`.
- `.github/workflows/android-a1-private-push-dex-triage.yml` — private static XAPK scan (quick). `.github/workflows/android-a1-metrica-init-state-observer-arm13.yml` — strict native ARM13 original+clone 75s 25/25 acceptance and private transient helper generator.

**Exact active branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Latest tested static-only `3231f20065063e8edf04b0c95154aa9097fc285a` (#43249305119 PASS); current native-probe code `95d3c86e13693cf7cabb3642ecba9f3170267699`, original private source unchanged, exact pre-handoff immutable backup `backup/android-a1-private-push-boolean-observer-exact-prehandoff-20261112`.

**Native real truth before current run:** Original signed 2025 Yandex **25/25 PASS**, independent one-APK clone **1/25 FAIL** without suppressions, same direct AppMetrica Push IllegalStateException; stock and clone can install side-by-side. Eighth actual #43239854803 and ninth #43244588445 confirm. Public modern `AppMetrica.activate` 3/3 RETURN, modern `ModulesFacade.isActivatedForApp` 6/6 TRUE. Exact Throwable constructed in Push impl obfuscated method `a` **after** app activation, so do NOT add another blind `activate()`, flip condition true, or mask Android exception. Private static call-chain found internal helper paths and interface dispatch; static output alone **is not** proof which private predicate returns false.

**Very first next step:** Read actual completed [native #43249731641](https://github.com/manufact-test/nomusic/actions/runs/43249731641) job sanitized JSON (test source `95d3c86e13693cf7cabb3642ecba9f3170267699`). Focus on `private_push_helper_bool_hook_registered`, `private_push_helper_bool_call_states`, `private_push_helper_bool_timeline`, `exact_fatal_sdk_throw_sites`, `lab_only_metrica_fatal_suppression_count_bounded`, `publisher_stable_75s_before_clone`, `native_clone_main_75s`. If `NO_HOOK`, diagnose classloader/dex extraction scope and do **not** claim that private predicate is true/false. If FALSE occurs, verify precise causal relation and fix actual SDK initialization source, not by suppressing fatal. If TRUE only, inspect state divergence and which untouched helper throws.

**Security:** release `a1-yandex-2025-gpr-private-test` is a private draft; binary, keys, generated method names, private Java, raw user data must never be committed/published as a GitHub artifact. No unauthorized login, music, or device manipulation. Preserve original publisher signature and Test.50/frozen A1 backups. Stage A **NO-GO**, Stage B **LOCKED** until real Android13 coinstall 75s 25/25 without suppression. B42 source-only contract already exists, but audio never proven live.

## FINAL RESULT AFTER COMPLETED NATIVE ARM13 #43249731641 (supersedes the "in progress" note)
- Tested source: `95d3c86e13693cf7cabb3642ecba9f3170267699`; [CI #43249731641](https://github.com/manufact-test/nomusic/actions/runs/43249731641) finished with **runtime NO-GO**.
- Publisher stock 75 sec: **25/25 PASS**. CELIKOM separate ONE-APK: **1/25 FAIL**, exact `SDK_PUSH` fatal `DETAIL_NOT_INITIALIZED`, suppression 0. CI-generated private Push helper hook `REGISTERED`, results **ENTER9/TRUE9/FALSE0/THROW0**. Modern ModulesFacade check TRUE6/FALSE0, modern public activate RETURN3/THROW0.
- This RULES OUT the simplistic theory that one of the three observed private Boolean helper methods returns FALSE. **Do not claim all Push predicates are TRUE or the root cause fixed** — the actual throw-site branch is not correlated with those three results, and static DEX scanning is approximate.
- NEXT DEVELOPMENT BLOCK: safely isolate the exact `com.yandex.metrica.push.impl` failing obfuscated `a` path at the exception constructor and identify the specific conditional/invocation responsible, with a privacy-bounded single-callsite probe. Compare service/provider and classloader state only if justified. Propose a causal initialization fix, then rerun unsuppressed original+clone ARM13 75s/25 and actual phone user testing when ready. Never remove analytics components, bypass a fatal return, add random activates, or publish original XAPK/DEX/private target Java.
- Accepted Test.50 and frozen A1 untouched. **STAGE A NO-GO / B LOCKED**. See `docs/android/ANDROID-A1-METRICA-INIT-STATE-OBSERVER-20261112.md` for numbered runs and sanitized evidence.
