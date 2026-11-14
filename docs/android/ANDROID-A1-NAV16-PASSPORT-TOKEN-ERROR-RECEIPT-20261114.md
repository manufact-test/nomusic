# CELIKOM Android A1 — NAV16, owner proves Passport SDK token exception (14 November 2026)

## Exact real-owner NAV15 evidence

Owner supplied `CELIKOM-A1-Diagnostics-1794676282236.txt` (1190 populated lines) after installing verified NAV15 signed APK. Saved original TXT in personal Library `/CELIKOM/CELIKOM-A1-NAV15-Owner-Diagnostics-1794676282236.txt`.

**Critical: multi-session diagnostic.** The TXT starts with persisted NAV14 log events (`DIAGNOSTIC_BUILD=NAV_V12...` stale legacy constant and `LOGIN_TOKEN_OUTCOME=OTHER_NONFAILURE_RESULT` at line 373), then records recent NAV15 process session `DIAGNOSTIC_BUILD=NAV_V15_EXACT_TOKEN_ENVELOPE` at line 596. Analyze **the NAV15 session** for current proof, not an earlier stale event.

Fresh original NAV15 authentic device events:
- line 835: `ACTIVITY_RESULT_DELIVERY ENTRY_ACTIVITY OK`;
- line 836: `LOGIN_PIPELINE_SOURCE ENTRY PASSPORT_LOGIN_RESULT`;
- line 842: `ACCOUNT_STATE CLONE_OWN ONE`;
- line 850: `LOGIN_TOKEN_OUTCOME ENTRY WRAPPED_FAILURE`;
- line 851: `LOGIN_TOKEN_ERROR_KIND ENTRY PASSPORT_OTHER`;
- line 854: `LOGIN_PIPELINE_RESULT AFTER_TOKEN_REQUEST NO_USERINFO_RESULT`;
- lines 855/858/861: `LOGIN_FLOW_RESULT ENTRY NO_USERINFO_RESULT`, `POSTLOGIN_PUBLISH OTHER_RESULT`, `POSTLOGIN_CONSUME RESULT_KEY_DELIVERED`.
- Passport subprocess: `ACCOUNT_ADD CLONE_OWN ADDED` line 957; master-token read `PRESENT`, decrypt `NO_EXCEPTION` repeatedly; does not imply token successfully issued to Music.
- No `USERINFO_READY`, no actual postlogin Main, no playable audio. `ONBOARDING_PREF UNSET` is an outcome, not immediate root cause.

**Proof:** the original Music coroutine called the token request and **resumed with a Kotlin failure result from Yandex Passport SDK**. The last NAV15 closed classifier `PASSPORT_OTHER` proves only class prefix `com.yandex.passport.*`, not the exact exception subtype or cause. It does NOT prove network, revoked auth, invalid signature, permission, missing client ID or which account was chosen. Do not guess. The preceding user description includes selecting one of two accounts in Passport ID, and the successful Passport UI/account-add does NOT prove Music-level login. The log is *not* evidence that the second account has been selected or stored; only one clone-owned account was observed.

## Single-scope NAV16 static repair to observation (NOT auth)

Exact pre-change backup: `backup/android-a1-nav15-owner-real-passport-failure-pre-nav16-20261114` @ `216c0b117346d722b9a5721d8a4438da51225f66`.
Same **only working Android branch** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. No new Android active branch, vendor code rewrite, native Main substitution, auth spoofing, AppMetrica changes, or Windows edits.

- `a98cbc85ac8273d1331e1fe41d6dc4b016ed323a`: classify original `zW8$b.default:Throwable` exception by closed SDK class enum. `PASSPORT_API_LOWER_{A...Y}` or `PASSPORT_API_UPPER_{A...F}` for known signed classes; known common/internal network variants or closed package-family fallback. This does not log exception class strings, messages, URLs, tokens, UIDs, names or any credential. Also classifies **one immediate Throwable cause** by `LOGIN_TOKEN_CAUSE_KIND` if present, without reading sensitive payload. Original coroutine remains untouched. Diagnostic build marker corrected to `NAV_V16_PASSPORT_EXCEPTION_KIND`.
- `6f132d886f56d617c8e690226f8a06e9207b0d4a`: static tests require new bounded classifiers, privacy invariants, unchanged pipeline return and NAV16 build marker.
- Paired Android13 native and clone-alone native CI were started automatically by source update, final verdicts must be checked before export. Do NOT imply green if not completed. No NAV16 signed owner APK yet at creation of this document.

## Next owner-stage work

1. Check real final CI results and exact source SHA. Fix failures; never bypass suite.
2. If green, use established assistant-driven one-shot self-cleaning GitHub Actions owner-export flow to produce **one** signed NAV16 APK with same permanent owner signer (public cert `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`). Verify APK SHA, signer, original embedded vendor unchanged, and module DEX NAV16 marker; upload to owner Library `/CELIKOM`, provide actual sandbox download. Preserve existing account through in-place update; if cannot install, stop, never uninstall. No need to click Actions or wipe data.
3. Avoid repeated manual Passport OTP/account selection for diagnostics. An ordinary app launch after in-place update may not execute the same post-login token request; if no new `LOGIN_TOKEN_ERROR_KIND` appears, tell the truth and do not force another OTP. Owner can report failure without repeated login.
4. Once subtype/inner cause is known, implement a **data-driven underlying correction** to the original Yandex API/account/client contract without faking userInfo or bypassing account ownership/signature security. Preserve the existing LSPatch A1 native architecture.
5. Stage A **NO-GO**, Stage B **LOCKED** until genuine Music userInfo, native Main and track playback on owner's device, not just native CI success.


## NAV16 FINAL signed owner artifact — verified and uploaded, 14 Nov 2026

**Supersedes the CI-pending/no-APK statements above.**
- Original-signature Android source change that broadened all known signed-Passport Throwable subclasses: `bf527b28fc3f94bfaa3036f626e8e4c23058a84f`. Final static-test commit `a528e3db5eafea21e4106f55d2532e7f6f72eafb` (same runtime source). Bounded observation `LOGIN_TOKEN_ERROR_KIND` and at most one `LOGIN_TOKEN_CAUSE_KIND` (type-only); no auth changes and no secrets.
- Android13 native acceptance: clone-alone run **#43620797411 SUCCESS** at `bf527b28`; paired stock-Yandex-first co-install **#43620797428 SUCCESS** at `bf527b28`; final paired + static tests **#43620816851 SUCCESS** at `a528e3db`. These are not proof of real owner login or audio.
- Assistant one-shot signed-export dispatcher **#43621673004 SUCCESS**, signed owner APK full run **#43621685870 SUCCESS**. Helpers removed automatically; same sole Android working branch.
- Artifact ID **#14124413138**, ZIP SHA256 `14a18760fc113bebd4d0922c5d095da478b86f3d436dc64b9326c4795ce99423`.
- Extracted signed APK `CELIKOM-A1-NAV16-PassportError-Diagnostic-20261114.apk` exact size **71,450,604 bytes**, SHA256 **`f0b7052986aa61d502a1e8c4f79e037dee42070da7ce5f08868d754a0025a3a6`**. APK v2 owner certificate SHA256 **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**, matches NAV15. Embedded original publisher Yandex APK SHA256 **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`**, byte-for-byte identical to NAV15. Independently read module `classes2.dex`: markers `NAV_V16_PASSPORT_EXCEPTION_KIND`, `WRAPPED_FAILURE`, `PASSPORT_DATA_EXC_I` present.
- Owner Library uploads **verified succeeded**: `/CELIKOM/CELIKOM-A1-NAV16-PassportError-Diagnostic-20261114.apk` and `/CELIKOM/NAV16-Инструкция-проверки-CELIKOM-A1-20261114.txt`. Owner NAV15 real receipt TXT also uploaded in `/CELIKOM`.
- Protected exact pre-change backup `backup/android-a1-nav15-owner-real-passport-failure-pre-nav16-20261114` @ `216c0b117346d722b9a5721d8a4438da51225f66`. Pre-export green backup `backup/android-a1-nav16-owner-passport-exception-subtypes-ci-green-pre-export-20261114` @ `a528e3db5eafea21e4106f55d2532e7f6f72eafb`. Post-export/pre-final-docs `backup/android-a1-nav16-signed-apk-green-pre-final-handoff-20261114` @ `9d298df4d8b957d60a0a901dc9c7c73f20f3c435`.
- Owner next: signed in-place update only, no deletion, OTP or GitHub Actions clicks required. Simply launch CELIKOM; if existing Passport account selection appears, no repeated manual login solely for diagnostics. If token fails and app returns onboarding, export one TXT. If error update, stop and report without uninstalling. **This NAV16 is diagnostic, NOT login fix**. Continue only after actual new `LOGIN_TOKEN_ERROR_KIND` and optionally `LOGIN_TOKEN_CAUSE_KIND` from the owner's `NAV_V16` block. Stage A NO-GO, Stage B LOCKED; genuine Music userInfo/native Main/audio not yet observed.
