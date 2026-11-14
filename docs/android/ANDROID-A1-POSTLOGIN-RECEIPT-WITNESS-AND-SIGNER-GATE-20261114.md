## Confirmed Android 13 runtime key initialization — 14 Nov 2026

The **clone-alone** fresh native ARM Android 13 [workflow #43574754576](https://github.com/manufact-test/nomusic/actions/runs/43574754576) and **publisher-first paired** [workflow #43574754550](https://github.com/manufact-test/nomusic/actions/runs/43574754550) both completed **SUCCESS** with the new explicit runtime assertion. BOTH native reports contain `"master_key_init_runtime_status": "ORIGINAL_KEY_PERSISTED"`. Standalone verdict is `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`; paired verdict is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. This proves that the clone MAIN's original 2025 Passport `v.try()` really generated and persisted its key on fresh native Android13, with the signed original app still installed in paired mode. No token, no owner account and no OTP were involved. The protected origin APK is unchanged.

This is a **meaningful technical repair of first-run key-ordering**, but neither a demonstrated fix of the owner's already-observed login loop nor a product release. User data on NAV9 remains untouched; no binary exported because the old NAV9 ephemeral signature cannot be updated. Stage A NO-GO; Stage B LOCKED.

# CELIKOM A1 — bounded original login receipt witness (14 Nov 2026)

## What is implemented, not claimed

At saved baseline `50fc7caaaad250df4b1f5539c60f1ee7083cc70b`, the exact original signed 2025.10.4 DEX callback contract was verified 14/14, and native Android13 paired startup passed. **NAV9 phone still loops after real Passport `setResult(OK)` and AccountManager account commit.** The original post-login chain requires a usable master token and real `Success(userInfo)`; neither was measured. `onboarding=UNSET` is not proven causal.

This source change adds **one narrowly scoped, read-only, finite receipt trail** to the already-existing own clone module, with no changes to original 2025.10.4 bytes, Test.50, production, Windows or backend. It does **not** fix the loop or deliver an APK. Existing clone-owned account registration and constructor/query bridges are untouched.

- **`MASTER_TOKEN_READ`**: actual Android `AccountManager.getPassword(Account)` return for *clone-owned type only*, recording `PRESENT|NULL_OR_EMPTY|THREW`, in MAIN or PASSPORT. No account name, token bytes, token length, passwords, uid or extras are read into logs; result/exceptions returned unchanged.
- **`POSTLOGIN_PUBLISH`**: exact original `ZX5.if(WS3)` publishes `REAL_USERINFO_SUCCESS` or `OTHER_RESULT`; uses exact class identity only, no payload.
- **`POSTLOGIN_CONSUME`**: exact original `hT3.try(Bundle,String)` receives `EntryScreenCloseLoginKey`; never reads Bundle.
- **`POSTLOGIN_MAIN_ROUTE`**: exact original `YS3.if(lw4,boolean)` invoked with `MAIN_REQUESTED|OTHER_ROUTE`, and returns or throws unchanged. No navigation injected. The route observer is armed only when original `EntryScreenActivity` is actually created in CELIKOM MAIN and is bounded; if obfuscated callsites cannot be verified/loaded it reports `NO_HOOK` instead of guessing.

**One future bounded test is sufficient to distinguish:** no `MASTER_TOKEN_READ` (path never reached), `NULL_OR_EMPTY` (token retrieval), `PRESENT` + no `REAL_USERINFO_SUCCESS` (Music session/login pipeline), success + no consume (FragmentManager), or consume + no route (Entry handler). Presence of any diagnostic event alone is not evidence that a user can play music.

## Added original 2025 decryptor outcome (no token data)

The exact original 2025.10.4 `com.yandex.passport.internal.core.accounts.v.if(String)` decryptor returns an internal `v$c` result whose private `for` field is an Exception on cryptographic failure. The clone-only read-only witness now hooks the *naturally invoked* method in MAIN and `:passport`, and observes **only whether the exception field is null**, returning the original result unchanged. Finite `MASTER_TOKEN_DECRYPT/MAIN|PASSPORT/NO_EXCEPTION|DECRYPT_EXCEPTION|UNAVAILABLE|THREW` events distinguish an actual post-login crypto failure from a missing UI result. No token ciphertext, plaintext, key, Account fields or exception text are accessed. `NO_EXCEPTION` is **not** proof that a usable token or session exists.

The vendor's real encryption key is held as `yandex_am_storage/master_token_key` via a cached `LY7a` preferences delegate. That raises a theoretical cross-process cache risk, but **there is no owner-device evidence yet that either process generated or read a different key**. No preferences read, key generation, cache invalidation, encryption rewrite or signature bypass has been added. To avoid that race being created by the observer itself, it does not proactively call `getSharedPreferences`.

## Narrow fresh-install key-order repair (source candidate, NOT owner-verified)

Static inspection of the original signed 2025.10.4 issuer DEX shows that the independently signed clone enters the SDK's AES token-encryption path (the signature-dependent original method `v.new()` does not identify the own CELIKOM certificate as a publisher certificate). The original `v.try()` generates/stores `yandex_am_storage/master_token_key` and its `LY7a` delegate caches preference reads. Consequently, a first-login timing race across original MAIN and `:passport` is plausible: system account creation succeeds while the main process cannot decrypt the token with the same key. **This is a causal hypothesis based on exact bytecode, NOT yet confirmed by an owner runtime decrypt failure.**

The clone-only module now invokes the **original 2025 SDK's own key-initialization routine** once in MAIN `Application.onCreate`, before any Passport UI, **only if there is zero clone-owned AccountManager account AND `master_token_key` does not already exist**. The existing SDK writes its key, then an empty `SharedPreferences.Editor.commit()` provides a disk-write ordering fence. No key bytes read/modified, no account touched, no publisher signature check bypassed, no forced onboarding or fabricated authorization. If an account exists but the key is missing, this repair deliberately leaves both unchanged and logs `ACCOUNT_EXISTS_NO_KEY_UNCHANGED`. Errors fail open without changing the app's normal authentication route.

This is a **candidate fix**, not a verified successful login. The native Android13 start/co-install gate can ensure no startup regression but **cannot** certify cross-process post-OTP correctness without real owner-device result. The existing bounded `MASTER_TOKEN_DECRYPT` and `POSTLOGIN_*` witnesses remain to distinguish cryptographic failure from result delivery once a stable signer and a single genuine user test are available.

Exact original static DEX contracts were expanded from 14 to **18** to cover the vendor preference store, cached getter, original key generator and commit/apply APIs. No original APK bytes are changed.

## Signing blocker (separate, verified)

Both owner NAV8 and NAV9 APKs had different outer signing certificates, because ephemeral own JKS is regenerated per CI run. Android cannot update either clone in-place with a different signer and preserve its package data. Therefore owner export is now **fail-closed for disposable signing** even if idle native CI is green. It requires an independently verified, long-lived owner signer supplied to the pipeline; the current lab does not and cannot assert that condition. Push builds never export APKs automatically. The publisher's inner signed APK and its key are untouched.

## Checks and acceptance

Private exact-original static contract CI, module Gradle compile and publisher-first Android13 startup are required. These do **not** reproduce real Passport login, callback receipt or playback. Until a stable owner signer and a genuine session-return fix exist, deliver **no new APK**, request **no repeated OTP**, and leave Stage A **NO-GO**, Stage B **LOCKED**. User's saved NAV9 diagnostic and baseline remain in Library.

Source rollback: `backup/android-a1-nav9-pre-token-callback-witness-20261114` @ `50fc7caaaad250df4b1f5539c60f1ee7083cc70b`. 
