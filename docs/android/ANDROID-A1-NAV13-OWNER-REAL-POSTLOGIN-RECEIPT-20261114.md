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


## 14 November — exact observer contract, caller origin and real Entry runtime smoke

Latest source commit: `cb6f5b6b00fa35b0c66d499e4e795229d198daae` on the single Android A1 working branch.

### Exact original DEX contract, privately checked

The private original-XAPK DEX gate now pins:
- Exact reflection descriptors for `LeY5$a.emit`, `LoY5$a.emit`, `LpY5$a.emit`, `LqY5.if`, and `LnY5.invokeSuspend`.
- The generated continuation hierarchy and `nY5.continue:I` field.
- Exact resume labels 1/2/3 at the original suspend boundaries: token request (`LEd5.this`), userInfo request (`LiE6.public`), sync (`Lol0.if`).
- The original EntryScreenActivity's explicit no-extra fallback-to-login path.

### Distinguishing the two original callers

Original DEX inspection confirms two callers of the same `qY5.if` pipeline:
- `oY5$a.emit`: Passport login-result flow (original log string `login result = `).
- `pY5$a.emit`: autologin UID flow (original log string `autologin result = `).

New bounded `LOGIN_PIPELINE_SOURCE` events emit only fixed categories:
`PASSPORT_LOGIN_RESULT`, `AUTOLOGIN_UID_RESULT`, or `OTHER_CALLER`. Only the first eight initial pipeline entries are classified. Stack contents, arbitrary class names, user data and auth payloads are never emitted.

Combined diagnostic meanings:
- `LOGIN_PIPELINE_SOURCE` identifies which of the two original caller paths entered `qY5.if`.
- `LOGIN_PIPELINE_RESULT` identifies INITIAL / AFTER_TOKEN_REQUEST / AFTER_USERINFO_REQUEST / AFTER_SYNC and only the fixed result class category.
- `LOGIN_FLOW_RESULT` independently classifies the original LoginFragment flow object as NO_USERINFO_RESULT, EXTERNAL_HANDOFF, USERINFO_READY, or OTHER_FLOW_STATE.
- If the flow result is present without a pipeline source event, the non-success path may have ended before entering `qY5.if`; do not infer a token/userInfo/sync failure from that alone.

### No-OTP Android 13 Entry smoke — PASS

The native runner now launches the real clone `EntryScreenActivity` with no extras, using the vendor's statically verified fallback-to-login route. It performs no tap, text entry, Passport approval or OTP. It then checks the real Entry lifecycle event and both hook registrations.

Both latest no-suppression ARM13 runs completed SUCCESS on source `cb6f5b6`:
- Clone-only #43602536005: main stability 75s PASS; Entry Activity created; FLOW and PIPELINE hooks both REGISTERED; `registration_pass=true`; no login interaction. Verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`.
- Publisher-first paired #43602536019: original publisher installed and stable 75s before clone, still installed after; persistent owner signer verified; clone main stable 75s; Entry Activity created; both hooks REGISTERED; `registration_pass=true`; no uncaught exception or Metrica fatal suppression. Verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.

This closes the previous gap: the new FLOW/PIPELINE hooks are now proven to register on a real Entry Activity inside Android 13, without any owner login or OTP. It does NOT prove a real Yandex Music userInfo success, Main navigation or audio playback.

### Protected rollback and current owner action

- Pre-source-origin backup: `backup/android-a1-nav13-before-login-source-origin-witness-20261114` @ `43ea6fe4e015cb0b888cb4673595eec14cdacb38`.
- Exact source + Entry-smoke backup: `backup/android-a1-nav13-entry-hook-smoke-before-ci-20261114` @ `cb6f5b6b00fa35b0c66d499e4e795229d198daae`.

No new owner APK was exported. No owner phone was changed. No OTP was requested. Original Yandex, Test.50, Windows, backend and production remain untouched.

**Next useful proof requires one controlled real owner login with this diagnostic code**, only after the owner explicitly confirms readiness. Before preparing or delivering an APK, verify the persistent signer against the currently installed diagnostic clone; do not assume an in-place update is possible. If signer differs, only the CELIKOM diagnostic clone may need a controlled reinstall; never uninstall or clear data for original Yandex. One login attempt is enough. Never request or collect the OTP itself.

Stage A **NO-GO**, Stage B **LOCKED** until a genuine `WS3$b Success(userInfo)`, native Main route and actual music playback are proven.


## 14 Nov 2026 — owner diagnostic APK exported after NAV13 native acceptance

Correction to the earlier status above: a private owner diagnostic APK HAS now been exported. The earlier statements "no new owner APK was exported" and "before preparing or delivering an APK" are superseded by this addendum.

- Native publisher-first Android13 workflow #43604192249: SUCCESS.
- Exact source under test: `cb6f5b6b00fa35b0c66d499e4e795229d198daae`; workflow head `bf3c67c96d4e723bae09e64bdc3e1b5edd4b6eb6`.
- Real Entry Activity created in native smoke; FLOW and PIPELINE observers REGISTERED. Token read/decrypt, Android result delivery and onboarding writer observers REGISTERED. Original master key persisted. Publisher-first original + clone coexistence passed; original 75s stable before/after, clone 25/25 lifecycle samples.
- Persistent signer verified: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
- APK SHA-256 `6e62b17aad4b9d7633a22880cceea02d39029cbe22bb663a7b302b5e9a8bc722`, 71,446,508 bytes. Certificate independently read from APK and matched the pinned owner fingerprint.
- Artifact #14117891265, run #43604192249; ZIP SHA-256 `dc6a1df7c421d785aba80cc96df3cef4bf9de35cb317e2853533d56e8cd89a27`.
- Library files: `/CELIKOM/CELIKOM-A1-NAV13-Entry-PostLogin-Diagnostic-20261114.apk` and `/CELIKOM/NAV13-Инструкция-реального-входа-CELIKOM-A1-20261114.txt`.
- `owner_phone_touched=false`; no real owner Passport login, OTP or audio playback was run. Verdict is still `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, Stage A NO-GO / Stage B LOCKED.
- Installed old clone signer remains unverified, so install mode is explicitly `FRESH_INSTALL_AUTHORIZED`. Delete only old CELIKOM diagnostic clone; preserve ordinary Yandex and its data. One genuine login reproduction and one TXT export are now the next required owner-side proof.

A one-time GitHub Actions dispatcher was used so the owner did not need to click Run workflow. It dispatched the existing workflow with the two previously approved one-time export/fresh-clone inputs and removed its own temporary helper files afterward. Backup before dispatch: `backup/android-a1-pre-one-shot-owner-diagnostic-dispatch-20261114` @ `37fd2f806afc8cd1e1739ef5c17d3f1e5381101b`; backup after cleanup: `backup/android-a1-nav13-owner-diagnostic-apk-43604192249-20261114` @ `8ab403e5c9d927af158bf606c17cbe387bcd2b46`.
