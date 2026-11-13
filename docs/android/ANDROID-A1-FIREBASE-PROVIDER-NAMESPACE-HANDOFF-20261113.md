# CELIKOM Android A1 — confirmed Push/Firebase failure and resource-namespace handoff (13 Nov 2026)

## Scope and acceptance

Repository `manufact-test/nomusic`, working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Stage A: **NO-GO**, Stage B: **LOCKED**. Goal remains one independently signed CELIKOM APK with the native Yandex.Music player via LSPatch, installed alongside unmodified publisher Yandex.Music. No alternate player, no SDK exception suppression, no bypass of publisher signature, no client/owner device tests. Test.50 and all production, Windows and frozen A1 branches untouched.

Original publisher XAPK: private draft release `a1-yandex-2025-gpr-private-test`, 16 APK splits, exact size 45,961,661 bytes and SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`. Input and extracted publisher binaries only inside private ephemeral CI; never upload raw code, string values, accounts, tokens, signing keys or APKs to output artifacts. Never print third-party class names from private DEX.

## Verified causal investigation (not guesses)

1. Original Yandex stays **25/25** on Android 13 ARM, cloned CELIKOM repeatedly fails **1/25** with AppMetrica Push `NOT_INITIALIZED`. Fresh standalone clone fails too; having the original alongside is not the cause. The specific `Push.impl.a` guard returns TRUE in its own method invocation before fatal error is constructed.
2. Private exact DEX static analysis narrowed the TRUE-normal branch to 21 catch-covered candidate invokes and one modeled catch handler. Direct signature-permission API involvement was **not established**. Later `PushServiceFacade.initPushService(Context)` hook successfully registered but **never executed** (0 ENTER).
3. **FIRST REAL DYNAMIC THROW SITE FOUND:** exact privately resolved concrete Firebase implementation of `PushServiceControllerProvider.getPushServiceController()`. Native ARM13 [standalone #43390402242](https://github.com/manufact-test/nomusic/actions/runs/43390402242) and [original-first #43390402317](https://github.com/manufact-test/nomusic/actions/runs/43390402317): hook REGISTERED, **3 ENTER, 0 RETURN, 3 THROW**, all `IllegalStateException`, all **AFTER_TRUE**, original 25/25, clone 1/25. No exceptions swallowed or SDK state forced.
4. [Standalone #43391762535](https://github.com/manufact-test/nomusic/actions/runs/43391762535) and [original-first #43391762610](https://github.com/manufact-test/nomusic/actions/runs/43391762610): exact Throwable cause in the **same `Push.impl.a` call frame** 3/3 (`SAME_CALL_PROVIDER_THROW`), not object-allocation inference.
5. [Standalone #43392888448](https://github.com/manufact-test/nomusic/actions/runs/43392888448) and [original-first #43392888420](https://github.com/manufact-test/nomusic/actions/runs/43392888420): specific error classified `PROVIDER_NO_VALID_CONTROLLER` 3/3; cloned app's three Android runtime Firebase configuration routes read as `PAIR_NONE`: custom manifest metadata, default manifest metadata, and clone-package string resources. In public AppMetrica Firebase provider source, this is precisely the branch after no nonempty/valid identifiers are found. Public source is supporting context, not a claim that vendor DEX is identical.
6. **IMPORTANT CORRECTION: Resource names are NOT physically missing.** Exact original-16-split private XAPK audit [#43394300293](https://github.com/manufact-test/nomusic/actions/runs/43394300293) found publisher `google_app_id` and `gcm_defaultSenderId` resource **names BOTH**, metadata routes NONE. Read-only aapt table comparison [#43394905599](https://github.com/manufact-test/nomusic/actions/runs/43394905599) and [#43394905597](https://github.com/manufact-test/nomusic/actions/runs/43394905597) found those resource **names BOTH in original and in final merged APK**. The first aapt parser returned namespace UNKNOWN, not evidence of the old/new package. The earlier statement that resources were dropped during merge was **incorrect**; distinguish package namespace vs missing/empty value.
7. One isolated Android 13 runtime comparison of `Resources.getIdentifier` for **clone package vs original package** was added on the active A1 branch. First CI attempts #43396834340/#43396834467 and #43397201895/#43397201887 had **synthetic parser test failures before any native test**, not product failures. Fix was committed `f6da04c8415ec760acbda633b4d92194042c7849`. Latest actual native checks: [original-first #43397534391](https://github.com/manufact-test/nomusic/actions/runs/43397534391), [standalone #43397534368](https://github.com/manufact-test/nomusic/actions/runs/43397534368). **Retrieve completed results before inferring resource namespace.**

## Current code and safety

- Runtime own app: `android/native-yandex-hooklab/ci/owner_2025_lspatch2_namespaced_clone_arm13.py`; only exact private source-generated enum read-only hooks. Android witness: `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`.
- Native parser: `android/native-yandex-hooklab/ci/a1_metrica_witness_private_parser.py`, with bounded PID-scoped `exact_post_true_provider_config_presence`, `exact_post_true_provider_namespace_lookup`, and matching synthetic tests. No raw Throwable messages/keys are logged; only whitelisted categories.
- Private DEX source preflight `android/a1-permission-catch-sourcecheck/permission_catch.py`, generating private class name only on ephemeral CI. No private class names in GitHub.
- Research helper `android/native-yandex-hooklab/ci/a1_resource_package_rename.py` plus `test_a1_resource_package_rename.py`: **NOT WIRED OR ENABLED**. Designed to rewrite only exactly one fixed UTF-16LE 256-byte ARSC package-name field in a *copied independently signed clone*, never the publisher source, IDs, key values, nested publisher origin or SDK. Synthetic preflight [#43398010746](https://github.com/manufact-test/nomusic/actions/runs/43398010746) passed. **This is NOT a verified correction or APK.**

## Next concrete step — no broad tracing

Read the two completed CI results #43397534391 and #43397534368. Inspect `scoped_own_readonly_witness.exact_post_true_provider_namespace_lookup`:

- If `CLONE_RESOURCE_ID=PAIR_NONE`, `PUBLISHER_NAMESPACE_ID=PAIR_BOTH` and `PUBLISHER_NAMESPACE_VALUE=PAIR_BOTH`: proven package-name mismatch. In **one disposable CI experiment only**, explicitly opt into renaming exactly the old package-name field to CELIKOM on the copied unsigned/own-signed *outer* resource table, preserve 100% other ZIP members (especially nested original), zipalign and own-resign. Before running compare `resources.arsc` except exactly one package-header name; verify aapt package namespace and runtime lookup. Then original-first native Android 13 25/25 for **both** apps. Do not claim success on build tests alone.
- If publisher namespace is also NONE, or IDs present but values blank: **do not rename** resource package blindly. Need one exact source-grounded difference in value/overlay or app context; don't scan entire SDK. Existing public SDK suggests all-Firebase-identifiers-empty path.
- On any native failure, keep Stage A NO-GO and Stage B LOCKED. No releasable APK or user install request until original and clone 25/25 and later audio/account signoff.

## Backups and boundaries

- Before recent namespace test: `backup/android-a1-before-firebase-namespace-lookup-20261113` @ `7b2d73d137c62dd5a6ce8ee7de2c75aa92ce6e47`.
- First real provider throw tests exact backup: `backup/android-a1-provider-throws-after-true-paired-arm13-20261113` @ `4858381b247130ca7758b358ba3a3c8a22524586`.
- Same-frame correlation backup: `backup/android-a1-provider-same-frame-correlation-20261113` @ `3f7aa3f9f1c41125e4c7eed9c307448f33f0b038`.
- Old clean JDI baseline: `backup/android-a1-jdi-eventonly-v2-complete-clean-20261113` @ `25c185a6ab1d860d56bdb92009461d0f069dad5e`.
- Do not touch Test.50 accepted backup `backup/android-test50-exact-source-owner-accepted-20261108`, frozen A1, Windows, production, API, publisher app, or device. One hypothesis and bounded native test at a time; backup before changes.

**No native 25/25 clone acceptance achieved as of this document's initial creation.** Subsequent updates should append exact run IDs, SHA, verified verdict and new clean backup; don't silently replace the findings above.
