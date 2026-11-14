## Final NAV12 onboarding-writer pass — 14 Nov 2026

A read-only writer observer now tracks only the clone's exact `Yandex_Music` SharedPreferences object and editor. It records `putBoolean("onboarding", value)`, a sanitized vendor caller class/method, and the real `commit/apply` return. It does not mutate the preference. The editor map was corrected so unrelated edits to the same file do not create false persistence events.

The coarse private original-DEX inventory passed in #43576640113. Strict Android13 registration gates are now complete: clone-alone #43577067135 and publisher-first paired #43577366277 both report ONBOARDING_WRITER_HOOK=REGISTERED and ORIGINAL_KEY_PERSISTED. This proves hook compatibility in both native layouts, not a real login writer invocation.

**NAV9's existing account is deliberately untouched by NAV11 key preinitialization.** No token/key rotation, onboarding write, fabricated result, APK export or owner login attempt. The fresh-install Passport key write itself is already proven by paired and clone-alone runs #43574754550 and #43574754576. User's post-login loop remains unverified and Stage A NO-GO / Stage B LOCKED.

## Exact DEX writer refinement — 14 Nov 2026

The first scanner counted literal/API co-occurrence, not argument dataflow. Manual exact instruction review of the embedded publisher-signed 2025.10.4 DEX identified three direct, persisted writers:
- Lf67;->if: exact Yandex_Music → edit → putBoolean("onboarding", …) → apply; its caller chain is upgrade/initialization, not Passport success.
- Lru/yandex/music/profile/ProfileActivity$b;->emit and ProfileActivity$c;->emit: exact direct writes and apply, belonging to profile coroutine handlers.
- LVj1;->transient is a configuration-map value, and LUc1$b;->emit contains unrelated notification timestamp preference calls; both are co-occurrence false positives.

The scanner now adds a strict direct register-chain classifier for Context/SharedPreferences/Editor calls and emits direct-writer and persisted-writer method lists. Tests cover correct file/key, wrong file/key, co-occurrence-only candidates and missing persistence. Classifier commits: 9592930 and 4297bbe; in paired Android13 CI #43578243485 the exact onboarding scan/test and private DEX classifier steps completed SUCCESS, while later native ARM13 stages were still running at handoff.

Runtime interpretation remains open: no idle CI run invokes Passport login. None of the three static writers is proven to run during Success(userInfo); do not invoke one or mutate onboarding to force Main.

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

## Final NAV12 onboarding writer witness (read-only, no auth/state mutation)

NAV9's owner diagnostic confirms `ONBOARDING_PREF / ENTRY_ACTIVITY / UNSET` four times, including after `ACCOUNT_STATE / CLONE_OWN / ONE`. Exact DEX says Main reads `getBoolean("onboarding", true)`, so absence resolves to TRUE. **UNSET is not a demonstrated cause or blocker.** `f67` is an app upgrade/initialization writer, not a proven post-Passport callback.

The final source pass adds a strictly read-only observer around Android 13's `ContextImpl.getSharedPreferences("Yandex_Music")`, its `SharedPreferencesImpl.edit()`, and the corresponding `EditorImpl.putBoolean("onboarding", value)`, followed by the real `commit()` or `apply()`. It logs only the boolean, the first non-framework caller class/method (sanitized by the existing finite-token logger), and the real persistence method return. It does not write any preference, change the onboarding state, call the login success callback, or launch Main. This will answer whether the original vendor ever attempts to set the onboarding key during a real login, and which code path does so. The hook is armed at package load in the isolated clone scope only; no system/stock process is targeted.

The paired native idle test cannot prove an auth-time writer exists; no owner APK is exported because the NAV9 certificate is not updatable. If static scan finds no writer candidate, the onboarding key may be an incidental read, not the root cause. If the runtime observer reports no write during real login, continue upstream through `MASTER_TOKEN_READ`, `MASTER_TOKEN_DECRYPT`, `POSTLOGIN_PUBLISH/CONSUME/MAIN_ROUTE` rather than forcing the preference.

### Exact onboarding DEX inventory result

The read-only scan completed in [#43576640113](https://github.com/manufact-test/nomusic/actions/runs/43576640113): **8 methods** contained the `onboarding` literal, **2 reader candidates**, **5 writer candidates**, and **0 undecodable methods skipped**. It identified:
- Reader candidates: `Lru/yandex/music/main/MainScreenActivity;->onCreate` (`contains/getBoolean`) and `LUc1$b;->emit` (`contains/getLong/setValue`).
- Writer candidates: `LVj1;->transient` (`clear/setValue`), `LUc1$b;->emit` (`contains/getLong/setValue`), `Lf67;->if` (`putBoolean/apply`), `Lru/yandex/music/profile/ProfileActivity$b;->emit` and `ProfileActivity$c;->emit` (`putBoolean/apply`).

These are **same-method literal/API co-occurrence candidates**, not a proven runtime call chain or proof that every candidate writes this specific key. Prior exact DEX callsite work places `f67` in app upgrade/initialization, not the demonstrated Passport success callback; profile writers are not evidence of login completion. The NAV12 runtime observer is the next discriminator.

The same #43576640113 paired Android13 run completed **SUCCESS** with `master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED` and verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. This source predates the new onboarding-writer registration gate, so it proves paired idle startup/key persistence only.

## Signing blocker (separate, verified)

Both owner NAV8 and NAV9 APKs had different outer signing certificates, because ephemeral own JKS is regenerated per CI run. Android cannot update either clone in-place with a different signer and preserve its package data. Therefore owner export is now **fail-closed for disposable signing** even if idle native CI is green. It requires an independently verified, long-lived owner signer supplied to the pipeline; the current lab does not and cannot assert that condition. Push builds never export APKs automatically. The publisher's inner signed APK and its key are untouched.

## Checks and acceptance

Private exact-original static contract CI, module Gradle compile and publisher-first Android13 startup are required. These do **not** reproduce real Passport login, callback receipt or playback. Until a stable owner signer and a genuine session-return fix exist, deliver **no new APK**, request **no repeated OTP**, and leave Stage A **NO-GO**, Stage B **LOCKED**. User's saved NAV9 diagnostic and baseline remain in Library.

Source rollback: `backup/android-a1-nav9-pre-token-callback-witness-20261114` @ `50fc7caaaad250df4b1f5539c60f1ee7083cc70b`. 


## NAV13 — Entry result receiver-side witness

Added `Activity.dispatchActivityResult(String,int,int,Intent)` observer in clone MAIN, filtered to exact `EntryScreenActivity`. It logs only the result category, with no Intent or extras inspection. This closes the gap between the already observed Passport-side `setResult(OK)` producer and actual framework delivery to Entry. Hook registration and Android13 compatibility are gated in paired run #43581081486 and clone-alone run #43581081611. Source: `9e723f3d404f1e78ac9fbf72a699a24cfaf7db1a`; rollback backup `backup/android-a1-nav12-final-handoff-r3-20261114`.


## NAV13 hardening

The Entry receiver-side result event now has an independent 48-event quota rather than sharing the generic Activity-finish quota, preventing unrelated finishes from exhausting the diagnostic budget. Fix: `1f2f0a77243bc9ba3b6dd7169eb7f86fad626073`. CI #43581508098 paired and #43581508085 clone-alone.


## NAV13 latest CI and source contract

- #43581081611 clone-only completed SUCCESS; this validates idle clone startup only, not Passport login or Entry result delivery.
- #43581081486 paired publisher-first completed SUCCESS: publisher install/launch accepted, stable 75s before/after clone; clone stable 25/25; onboarding writer hook registered. No Passport login was exercised, so Activity result delivery remains unobserved.
- Quota hardening commit `1f2f0a77243bc9ba3b6dd7169eb7f86fad626073` gives Entry delivery its own 48-event counter.
- Added source-contract regression test in `468fa14e8a6328e021968143afa8e00712c6ec73`; it checks exact Android dispatch signature, receiver filter, separate quota, and read-only behavior.
- #43581508098/#43581508085 and source-test run #43581718989 were still running/queued. No owner login evidence yet.


## NAV13 quota-fix CI update — 14 Nov 2026

Quota-fix clone-alone rerun #43581508098 completed SUCCESS with native clone MAIN stable 75s, `ORIGINAL_KEY_PERSISTED`, `ONBOARDING_WRITER_HOOK=REGISTERED`, and no uncaught exception. This is not a Passport login and does not establish Activity result delivery or `Success(userInfo)`. Paired run #43581508085 and source-test run #43581718989 were still in progress at this checkpoint.


## NAV13 Android 13 dispatch signature — corrected and registered

The initial four-parameter Activity.dispatchActivityResult lookup was invalid on Android 13. API 33's actual framework method is dispatchActivityResult(String,int,int,Intent,String reason). The observer now resolves that exact five-parameter signature, reads only result-code argument 2, and never inspects the other arguments. The producer-side setResult witness now filters to PASSPORT_ACTIVITY and uses an independent bounded counter.

The runner has a hard runtime gate for ACTIVITY_RESULT_DELIVERY_HOOK=REGISTERED; it cannot report a native pass if the observer failed to register. Corrected source: b565dc4d050f463397312c8f409b2450cc8bbc79.

- #43582980401 clone-only: SUCCESS; result-delivery hook REGISTERED, onboarding writer hook REGISTERED, original master key persisted, stable 75s.
- #43582980390 publisher-first paired: SUCCESS; result-delivery hook REGISTERED, onboarding writer hook REGISTERED, original master key persisted; original Yandex installed first and remained installed; publisher stable 75s before clone; clone stable 25/25. METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.

No Passport flow was run, so result delivery and Success(userInfo) remain unobserved at runtime. No APK, OTP, account mutation or owner handset activity. Disposable CI signer only. Stage A NO-GO / Stage B LOCKED.
