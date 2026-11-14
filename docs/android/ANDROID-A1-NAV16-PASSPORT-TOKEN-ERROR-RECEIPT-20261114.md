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
