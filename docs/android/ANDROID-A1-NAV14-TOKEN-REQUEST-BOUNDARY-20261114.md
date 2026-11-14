# CELIKOM Android A1 — owner token-request boundary, 14 November 2026

## Latest real owner diagnostic

Owner file: `CELIKOM-A1-Diagnostics-1794667528891.txt`, 535 populated events. Do not store any credential payload. The embedded `DIAGNOSTIC_BUILD=NAV_V12_ONBOARDING_WRITER_WITNESS` is a legacy constant in the current source, **not proof of a NAV12 APK**; this file contains both newer NAV13 `POSTLOGIN_HOOK PIPELINE/FLOW REGISTERED` and runtime `LOGIN_PIPELINE_SOURCE` events. The document does NOT cryptographically tie the installed APK to the Library APK; do not assume an installed-device hash/certificate from the filename.

Observed owner result:
- `:passport`: own account `ADDED`; master token reads `PRESENT`; decryptor `NO_EXCEPTION` (does not prove usable login token).
- MAIN: `ACCOUNT_STATE CLONE_OWN ONE`; `ACTIVITY_RESULT_DELIVERY ENTRY_ACTIVITY OK`; original `LOGIN_PIPELINE_SOURCE ENTRY PASSPORT_LOGIN_RESULT`; `LOGIN_PIPELINE_RESULT INITIAL NONTERMINAL_OR_OTHER` then `LOGIN_PIPELINE_RESULT AFTER_TOKEN_REQUEST NO_USERINFO_RESULT`; original `LOGIN_FLOW_RESULT ENTRY NO_USERINFO_RESULT`; `POSTLOGIN_PUBLISH ENTRY OTHER_RESULT` and `POSTLOGIN_CONSUME ENTRY RESULT_KEY_DELIVERED`.
- No `USERINFO_READY`, no original `WS3$b Success(userInfo)`, no post-login Main route or audio; `PREVIOUS_EXIT_INFO NONE`. An earlier non-userInfo event occurs before this real account success and is not the determining event.
- The **first failing original coroutine boundary is the token request `LEd5.this`**. No userInfo fetch `LiE6.public` or sync `Lol0.if` is proven for the owner's actual Passport result. This rules out a purely missing Android result delivery/FragmentManager delivery as the immediate break.
- **Unknown cause within this boundary**: `LEd5.this` may return a Kotlin failure or a null/otherwise unusable token. The original owner TXT does not distinguish those outcomes, and `MASTER_TOKEN_DECRYPT NO_EXCEPTION` does not establish them. Do not guess certificate/permissions/network or spoof successful login.

## Exact-original private DEX cross-check (read only)

The SHA-256 of the Library NAV13 APK was independently verified as `6e62b17aad4b9d7633a22880cceea02d39029cbe22bb663a7b302b5e9a8bc722`. The embedded original `assets/lspatch/origin.apk` was inspected read-only, without copying vendor payload into the repository. The original `qY5.if` resumes label 1 after `LEd5.this`, then chooses between Kotlin failure `zW8$b`, a nonfailure token object and a null token. The continuation `nY5.private:Object` contains the resume result and the original Kotlin failure `zW8$b.default:Throwable` contains only the failure object. No post-login response value, token, UID or error message was exported.

## Narrow follow-up instrumentation, no behavior changes

Protected pre-change exact backup:
`backup/android-a1-nav13-owner-token-boundary-before-readonly-fix-20261114` @ `0f4100c872f44174375ea52a607b7cf37521ff68`.

Source changes in the **same sole Android working branch**:
- `67a07c741d53981ed2681afb7257f479e753bb9a`: clone-only, read-only `LOGIN_TOKEN_OUTCOME` after original `AFTER_TOKEN_REQUEST` categorizes `NULL / FAILURE / STRING_RESULT / OTHER_NONFAILURE_RESULT / UNAVAILABLE`; on failure only, `LOGIN_TOKEN_ERROR_KIND` reports a fixed exception-family category, never values, messages or stack traces. Does not alter real coroutine arguments, token, results or navigation. Maximum 12 observations.
- `f0c86d278db7627c56f77060cacedb02be84a190`: exact signed vendor DEX gate pins the two fields used.
- `73f246187a6a9d678eeada8cb5e23a749613078c`: static tests for classifier bounds, no-secret policy and original pipeline behavior.

Current corrected source/test commit: `423c401aa81d41bc35ef80bd0cddbb0dbc443135`. Its isolated source tests, the exact original DEX contract and module build passed. **Latest clone-only native Android13 CI #43607698877 completed SUCCESS.** Latest publisher-first paired CI #43607698917 was still executing the unsuppressed 75-second native acceptance at the last verified check (14 November, 15:07 UTC); treat its final verdict as UNKNOWN until read. Earlier paired #43607380238 failed at a wrong new static-test assertion, which was fixed by `67258f7`; do not confuse it with a native regression. None of these runs performs genuine owner Passport login or audio. No new APK exported, no owner phone interaction, no extra OTP.

## Next action

1. Verify latest paired and clone-only native verdicts against their actual tested source SHAs, and fix source/CI regressions if any. Do not confuse hook registration with real token acceptance.
2. Only after all gates pass, decide whether one narrow owner-side observation is necessary to distinguish the original token error from null; prefer an update retaining the permanent signer/account where independently supported, not a needless fresh installation. Never force OTP or ask for credentials in chat.
3. A data-driven actual auth fix must preserve original Yandex/data, CELIKOM A1 single architecture, Test.50 and Windows. Do not fake `Success(userInfo)`, write `onboarding`, jump to native Main, replace the original signed APK or bypass Android account ownership.
4. Stage A **NO-GO**; Stage B **LOCKED** until genuine login, native Main and audio are observed on the owner's device.


## FINAL NAV14 export and owner-facing proof — 14 November 2026

The following **supersedes the earlier pending-CI/no-new-APK lines in this document**:
- Corrected Android source/test commit `423c401aa81d41bc35ef80bd0cddbb0dbc443135` is source-green, and both final Android13 native checks completed **SUCCESS**: clone-only #43607698877 and publisher-first paired #43607698917. No owner login or audio was exercised by these CI checks.
- One-time self-cleaning dispatcher #43608660068 completed SUCCESS; the full signed owner-diagnostic workflow **#43608666946 SUCCESS**. Its temporary dispatcher + marker were removed automatically after dispatch; working Android source was unchanged.
- GitHub artifact **#14119497592** from run #43608666946 was downloaded and its ZIP independently read. ZIP SHA-256 `8107adf73ceb8ed95229265b8168747022ac3364e5bc5a18b526b1725f551e4e`.
- APK SHA-256 **`886dd088773d8a9c6e59499c4c1230dcd2bc97dd0b1645bc8a3e9437e9434fbe`**, exact size 71,446,508 bytes. Independently verified embedded APK public certificate SHA-256 **`048D76E1C4447FA4F3AC976C45D5A0F8427C087FA665C4FCA88CE5CAA068F9BF`**, matching permanent owner signer (RSA 3072, SHA256withRSA).
- Saved in the owner's personal Library, folder **/CELIKOM**:
  - `CELIKOM-A1-NAV14-TokenOutcome-Diagnostic-20261114.apk`
  - `NAV14-Инструкция-проверки-токена-CELIKOM-A1-20261114.txt`
- Protected pre-export exact source/docs backup: `backup/android-a1-nav14-paired-and-clone-native-green-pre-export-20261114` @ `46b6841e31b0bf2bd77a9691e4705c0a848afc3a`.
- Protected post-export/pre-final-docs backup: `backup/android-a1-nav14-owner-token-apk-exported-pre-handoff-20261114` @ `92ff739e8edcad53aa8e622c6201d7f8a8742537`.

**Next owner interaction**: NO reinstall/OTP loop is justified. The new APK is signed with the same permanent owner signer as the previous NAV13 export. Try an ordinary in-place update over the installed CELIKOM, without deleting the app or clearing the clone-owned account. If Android refuses to update, STOP; do not uninstall either CELIKOM or original Yandex. If update works, launch CELIKOM once, allow any normal automatic account recovery, export one `CELIKOM-A1-Diagnostics-....txt` using `Сохранить диагностику`. The new fixed-category `LOGIN_TOKEN_OUTCOME` / `LOGIN_TOKEN_ERROR_KIND` events should distinguish token failure versus null. No need to force a new OTP; if the app demands it, the owner can report that instead of retrying.

**This APK is diagnostic, not a proven login or audio fix. Stage A NO-GO, Stage B LOCKED.** Never imply the app is accepted until real successful `USERINFO_READY`, native postlogin Main and track playback are observed.
