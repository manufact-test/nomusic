# CELIKOM A1 — bounded original login receipt witness (14 Nov 2026)

## What is implemented, not claimed

At saved baseline `50fc7caaaad250df4b1f5539c60f1ee7083cc70b`, the exact original signed 2025.10.4 DEX callback contract was verified 14/14, and native Android13 paired startup passed. **NAV9 phone still loops after real Passport `setResult(OK)` and AccountManager account commit.** The original post-login chain requires a usable master token and real `Success(userInfo)`; neither was measured. `onboarding=UNSET` is not proven causal.

This source change adds **one narrowly scoped, read-only, finite receipt trail** to the already-existing own clone module, with no changes to original 2025.10.4 bytes, Test.50, production, Windows or backend. It does **not** fix the loop or deliver an APK. Existing clone-owned account registration and constructor/query bridges are untouched.

- **`MASTER_TOKEN_READ`**: actual Android `AccountManager.getPassword(Account)` return for *clone-owned type only*, recording `PRESENT|NULL_OR_EMPTY|THREW`, in MAIN or PASSPORT. No account name, token bytes, token length, passwords, uid or extras are read into logs; result/exceptions returned unchanged.
- **`POSTLOGIN_PUBLISH`**: exact original `ZX5.if(WS3)` publishes `REAL_USERINFO_SUCCESS` or `OTHER_RESULT`; uses exact class identity only, no payload.
- **`POSTLOGIN_CONSUME`**: exact original `hT3.try(Bundle,String)` receives `EntryScreenCloseLoginKey`; never reads Bundle.
- **`POSTLOGIN_MAIN_ROUTE`**: exact original `YS3.if(lw4,boolean)` invoked with `MAIN_REQUESTED|OTHER_ROUTE`, and returns or throws unchanged. No navigation injected. The route observer is armed only when original `EntryScreenActivity` is actually created in CELIKOM MAIN and is bounded; if obfuscated callsites cannot be verified/loaded it reports `NO_HOOK` instead of guessing.

**One future bounded test is sufficient to distinguish:** no `MASTER_TOKEN_READ` (path never reached), `NULL_OR_EMPTY` (token retrieval), `PRESENT` + no `REAL_USERINFO_SUCCESS` (Music session/login pipeline), success + no consume (FragmentManager), or consume + no route (Entry handler). Presence of any diagnostic event alone is not evidence that a user can play music.

## Signing blocker (separate, verified)

Both owner NAV8 and NAV9 APKs had different outer signing certificates, because ephemeral own JKS is regenerated per CI run. Android cannot update either clone in-place with a different signer and preserve its package data. Therefore owner export is now **fail-closed for disposable signing** even if idle native CI is green. It requires an independently verified, long-lived owner signer supplied to the pipeline; the current lab does not and cannot assert that condition. Push builds never export APKs automatically. The publisher's inner signed APK and its key are untouched.

## Checks and acceptance

Private exact-original static contract CI, module Gradle compile and publisher-first Android13 startup are required. These do **not** reproduce real Passport login, callback receipt or playback. Until a stable owner signer and a genuine session-return fix exist, deliver **no new APK**, request **no repeated OTP**, and leave Stage A **NO-GO**, Stage B **LOCKED**. User's saved NAV9 diagnostic and baseline remain in Library.

Source rollback: `backup/android-a1-nav9-pre-token-callback-witness-20261114` @ `50fc7caaaad250df4b1f5539c60f1ee7083cc70b`. 
