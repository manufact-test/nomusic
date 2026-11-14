# CELIKOM A1 — Owner NAV13 real post-login receipt, 14 November 2026

## Actual owner evidence, not product acceptance

Owner file: `CELIKOM-A1-Diagnostics-1794659649152.txt`, 525 populated events. The file's build marker is `NAV_V12_ONBOARDING_WRITER_WITNESS`. Signed diagnostic APK was exported by workflow #43593916246 (APK SHA-256 `66d4edc0f65206a788b89a0b2760674981e221028697379633e784b3e676058e`). The TXT has no APK digest; do not claim cryptographic binding of the installed binary from the TXT alone. MAIN and :passport logs are separate merged sections, not one chronological sequence.

**MAIN facts:** `ACCOUNT_STATE CLONE_OWN ZERO` then `ONE`; real `ACTIVITY_RESULT_DELIVERY ENTRY_ACTIVITY OK` twice; original `POSTLOGIN_PUBLISH ENTRY OTHER_RESULT` twice, once after the account became visible; `POSTLOGIN_CONSUME ENTRY RESULT_KEY_DELIVERED` twice. There is NO `REAL_USERINFO_SUCCESS`, NO `POSTLOGIN_MAIN_ROUTE`, and NO post-login Main creation. FragmentManager consumed an event but has no proved userInfo-backed success. `ONBOARDING_PREF UNSET` still resolves to TRUE in the unchanged vendor app and is not a proven blocker.

**:passport facts:** `ACCOUNT_ADD CLONE_OWN ADDED`; repeated `MASTER_TOKEN_READ PASSPORT PRESENT` and `MASTER_TOKEN_DECRYPT PASSPORT NO_EXCEPTION`. Decrypt's observed null exception field is NOT proof Music obtained a valid token/userInfo or completed sync. No Java fatal in this capture.

**Precise missing receipt:** the original Music LoginFragment does not publish `WS3$b Success(userInfo)`. The executed failing branch (token retrieval vs userInfo load vs sync) is still UNKNOWN. Do not fabricate success, write onboarding, jump to Main, or ask the owner to re-enter OTP.

## Verified unchanged original 2025.10.4 DEX

Read-only extracted `assets/lspatch/origin.apk` from existing NAV9 owner Library APK; SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Original `LeY5$a.emit(Object,Continuation)` maps `qY5$a$a` to non-success `WS3$a`, `qY5$a$b` to external handoff and non-success, `qY5$a$c` to genuine userInfo `WS3$b` success. `LqY5.if` has coroutine return stages after token request, userInfo request and sync. Static signatures are NOT owner runtime success.

## Source-only change, protected rollback

- Original known exact backup `backup/android-a1-owner-apk-final-docs-20261114` @ `8ea251e0a0e92ffecd32ebe9f8070f92034a241d`.
- `backup/android-a1-owner-postlogin-result-subtype-before-change-20261114` @ `8ea251e0a0e92ffecd32ebe9f8070f92034a241d`; commit `507cf32999514e50ac34b1d84e0200d37744b813` adds bounded read-only `LOGIN_FLOW_RESULT`.
- `backup/android-a1-owner-flow-subtype-before-pipeline-stage-20261114` @ `507cf32999514e50ac34b1d84e0200d37744b813`; commit `a2ae0a520f762b6b32f1a55495216e17eddb478a` adds original `qY5` coroutine-stage `LOGIN_PIPELINE_RESULT` (reads only continuation integer label and terminal result CLASS, never token/UID/userinfo/exception contents).
- `backup/android-a1-before-native-flow-hook-gates-20261114` @ `a2ae0a520f762b6b32f1a55495216e17eddb478a`.
- Native Android13 paired and clone-only acceptance now requires `POSTLOGIN_HOOK FLOW` and `POSTLOGIN_HOOK PIPELINE` both REGISTERED in actual logcat. This confirms hook registration only, not an executed OTP, accepted Music session or audio.

No new APK export, phone change or further OTP. Check complete source CI + both native ARM13 verdicts at latest branch SHA before considering any further diagnosis. Any future owner test must be separately justified and bounded. No repair claimed yet.

Stage A **NO-GO**; Stage B **LOCKED**. Do not touch original Yandex/data, Test.50, Windows, backend, production or other working branches.

## Regex source-gate correction

A review before native CI acceptance found that the new regex had double-escaped the raw-string backslash classes. This would misclassify live logcat as NOT_OBSERVED. Fixed to the exact existing Android13 logcat parser convention in the next commit, with a regression that *executes the actual parser function* against synthetic FLOW and PIPELINE REGISTERED/NO_HOOK lines. The prior source snapshot is saved at `backup/android-a1-before-flow-regex-fix-20261114` @ `5cdf7ecb1e0fb64284cff528b4d67ceb746f0a33`. These are registration-only gates; Stage A remains NO-GO and Stage B LOCKED.

## 14 November — Entry-scoped native gate correction

The earlier strict CI runs #43597709855 and #43597709845 were FAILURE because they required the new original LoginFragment hooks to register during a MAIN-only 75-second idle acceptance test. Both observed stable 25/25 MAIN, ORIGINAL_KEY_PERSISTED and all four pre-existing registration gates REGISTERED. FLOW/PIPELINE returned NOT_OBSERVED (not NO_HOOK). These new observers are deliberately armed only on Entry Activity CREATED, which idle CI never reaches. Thus the unconditional gate was wrong; there was no proven startup regression.

The corrected source checks `postlogin_entry_created_observed`: if real Entry CREATED is logged, BOTH FLOW/PIPELINE must REGISTERED; if Entry is absent, NOT_OBSERVED is permitted but NO_HOOK/UNAVAILABLE still fails. The new synthetic source test executes the actual gate against idle and Entry examples. This remains registration-only startup acceptance; it cannot prove login or audio. Exact pre-correction backup `backup/android-a1-nav13-pre-entry-scoped-ci-gate-fix-20261114` @ e33a132f2eb0289d78cea885b62e03957a5be272.

## Final latest native CI (source SHA `26e952d1f6b0d980b10ed5c9d21310f6d20c0d20`)

Both native no-suppression Android 13 runs completed SUCCESS after correcting the Entry-scoped admission test:

- Clone-only #43598738033: `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`, `native_clone_main_75s=true`, `master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED`; new `FLOW` and `PIPELINE` statuses `NOT_OBSERVED`, `postlogin_entry_created_observed=false`, `postlogin_registration_accepted=true`. This is the correct classification when the real LoginFragment was not opened.
- Publisher-first paired #43598738007: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, original publisher stable 75s before clone and still installed after clone launch; clone native MAIN stable for 75s (25/25 observations); original key persisted, persistent owner signing certificate verified, no uncaught exception or Metrica fatal suppression. Same no-Entry FLOW/PIPELINE statuses and correct admission.

The previously failing runs #43597709855 and #43597709845 were false negatives caused by inappropriate unconditional hook registration admission. New CI runs passed only after exact Entry-scoped test fix; do not repeat these flawed expectations.

**The new LoginFragment FLOW/PIPELINE hooks are NOT yet observed REGISTERED on a real Entry run.** Their source compile and no-Entry native safety are verified; no user OTP/login or audio occurred in CI. No new APK was published, no owner handset affected, no original Yandex/Test.50/Windows/production modified. Signed owner APK from previous #43593916246 remains the only delivered binary.

Exact rollback backup for native CI-green source:
`backup/android-a1-nav13-owner-receipt-source-ci-green-20261114` @ `26e952d1f6b0d980b10ed5c9d21310f6d20c0d20`.

Actual owner-login root cause remains unresolved between original token API, userinfo fetch and synchronization, as real TXT lacks more granular result events. Stage A NO-GO, Stage B LOCKED. The next assistant should not ask for OTP or another install now: first verify source version and assess whether one more controlled owner login is truly justified, then seek explicit owner readiness before doing so.
