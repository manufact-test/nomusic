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


## NAV13 final runner-gate result — 14 Nov 2026

Commit 5f683900b966673224babc2d6b684960dc8ea2ac (parent 4536ba75001050de17ae3e9cb5e1921548a33884) adds required runner parsing/gates for MASTER_TOKEN_HOOK and MASTER_TOKEN_DECRYPT_HOOK registration in both native verdict paths, plus source-contract assertions.

Verified latest no-suppression Android13 runs:
- #43583886782 clone-only — SUCCESS. Result-delivery, master-token read, master-token decrypt and onboarding writer hooks all REGISTERED; original key persisted; clone MAIN 75s stable; no uncaught exception. This is a clone-only startup differential.
- #43583886793 publisher-first paired — SUCCESS. Same registration/key results; original publisher's 16 splits installed first and retained; publisher stable 75s before clone; clone 25/25 stable; no Metrica fatal suppression; no uncaught exception. METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.

Neither run executes Passport login. No actual MASTER_TOKEN_READ/MASTER_TOKEN_DECRYPT callback, receiver result delivery, POSTLOGIN_PUBLISH, POSTLOGIN_CONSUME or POSTLOGIN_MAIN_ROUTE has been demonstrated. The REGISTERED fields prove observer installation only.

No owner APK was exported because CI still signs with DISPOSABLE_PER_CI_RUN; owner export remains fail-closed unless a dedicated persistent A1 signer is independently verified. Owner handset, account and onboarding state remain untouched. Stage A NO-GO / Stage B LOCKED.

Next: continue read-only exact route investigation and provision the stable signer through an owner-controlled secure process. Do not place private signing material in chat, request another OTP, or deliver a new APK before explicit readiness and a single bounded owner test.


## NAV13 persistent owner-signing transition — 14 Nov 2026

### Forensic finding: current owner APK is not update-signable

The owner-phone NAV9 diagnostic was built from source containing DIAGNOSTIC_BUILD=NAV_V9_POSTLOGIN_ROUTE_PREF_WITNESS. The closest matching original-first CI artifact is:
- workflow run #43518864593, artifact #14081618529;
- source commit e9cdd607e668304aa97371399464104242aca601;
- APK SHA-256 78f110eeadac9d313e2f9f2212dd0432a4dce0eac828b4defa3c9a6f2dfb8158;
- APK size 71,442,412 bytes;
- certificate SHA-256 03c2917442666c49d3d60466e0ed43077321ee472e7915d065b4bb4c1b3b6081;
- self-signed certificate serial DE11B5FF72C1ABF0, validity 13 Nov 22:27:23 UTC through 14 Nov 22:27:23 UTC.

The key was generated inside the CI job by the disposable same-name signing control and destroyed with its TemporaryDirectory. Only the public certificate remains in the APK. The private key cannot be reconstructed from the APK or certificate.

**Caution:** an earlier assistant note records a different APK SHA-256, 2d043de0fdabcd9ee4109d01c376d764d4e640b4a4dd07df1bffb6a0264f7e63. That hash does not match artifact #14081618529. The NAV9 diagnostic marker matches the source commit, but the exact file currently installed on the owner's phone has not been independently tied to a run-specific APK hash or certificate fingerprint. Do not set CELIKOM_A1_INSTALLED_CERT_SHA256 based on an assumption.

### Persistent signer implementation added to source

- android/native-yandex-hooklab/ci/a1_persistent_owner_signer.py imports an owner-controlled PKCS#12 keystore from Actions Secrets into the ephemeral runner temp directory, converts it to the exact temporary JKS alias/password format required by the existing signer, verifies its pinned certificate SHA-256, then deletes the source PKCS#12 temp file.
- owner_2025_same_name_own_key_arm13_control.py::sign_same_name() accepts an optional supplied keystore; its existing disposable-key behavior remains the default for isolated tests without owner secrets.
- The main ARM13 runner verifies the final APK certificate against both the pinned owner fingerprint and the signer used for the split set.
- APK export now requires PERSISTENT_OWNER_SIGNER, successful certificate verification, and an explicitly authorized install mode.
- workflow_dispatch adds authorize_fresh_clone_install, default false. Its description warns that uninstalling/reinstalling CELIKOM clone loses its saved clone account/data; the original Yandex app remains untouched.
- If the installed certificate fingerprint is not pinned and equal to the new owner signer, export is blocked unless the owner explicitly selects the fresh-clone-install authorization. No default or automatic uninstall exists.

### GitHub Actions configuration contract

Create the owner PKCS#12 locally only after the owner chooses the install transition. Never send the keystore, base64, or passwords in chat and never commit them.

Repository Actions Secrets:
- CELIKOM_A1_OWNER_KEYSTORE_BASE64
- CELIKOM_A1_OWNER_KEYSTORE_PASSWORD
- CELIKOM_A1_OWNER_KEY_ALIAS
- CELIKOM_A1_OWNER_KEY_PASSWORD

Repository Actions Variables:
- CELIKOM_A1_OWNER_CERT_SHA256 — SHA-256 fingerprint of the public certificate in the new owner PKCS#12, with or without colons.
- CELIKOM_A1_INSTALLED_CERT_SHA256 — only the verified fingerprint of the APK currently installed on the phone; currently unset because the exact installed binary is not proven.

The PKCS#12 source is expected to use alias celikom-a1-owner; using the same password for store and key is recommended. On Windows, with JDK keytool available:

~~~powershell
$pw = Read-Host "Enter a long unique keystore password"
keytool -genkeypair -noprompt -storetype PKCS12 -keystore .\celikom-a1-owner.p12 -storepass $pw -keypass $pw -alias celikom-a1-owner -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=CELIKOM A1, O=MANUFACT, C=BY"
keytool -list -v -keystore .\celikom-a1-owner.p12 -storetype PKCS12 -storepass $pw -alias celikom-a1-owner | Select-String "SHA256"
[Convert]::ToBase64String([IO.File]::ReadAllBytes(".\celikom-a1-owner.p12")) | Set-Clipboard
~~~

Paste the base64 clipboard value directly into the GitHub Secret field, not into ChatGPT. Keep the original PKCS#12 and password in two secure offline backups; the signing key must never be rotated after the first stable-signer installation.

### Install-transition decision remains owner-controlled

The current NAV9 APK cannot be updated in place using a newly generated key unless its original private key is recovered (it has not been). The practical clean transition would remove only the diagnostic CELIKOM clone and reinstall it with the permanent signer. This loses the clone's local data and may remove its clone-owned Android account; the regular publisher Yandex must remain installed and untouched.

Do not request another OTP or uninstall the clone while the login loop remains unresolved. The new workflow's fresh-install input is an explicit authorization gate, not permission for the assistant or CI to touch the phone.

No APK was exported, no secrets were added, no owner phone or account was touched, and no original Yandex/Test.50/Windows/production files were changed. Stage A remains NO-GO; Stage B remains LOCKED.


## NAV13 final validation — 14 Nov 2026

### Source and CI

- Persistent signer implementation: commit f99a112b324a810d8690818d8c647e29e13ae629.
- Test-fixture cleanup: commit 75258871f52ffe8b0f5fc08d6c9bfc1c498d4df8.
- Signer-transition documentation: commit 6b12e56f866928f38b16f00cd46e764207346833.
- #43586620493 — clone-only native ARM13 SUCCESS; 25/25 lifecycle observations, master key persisted, all required read-only hook registration gates present, no uncaught exception. Verdict CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS.
- #43586813717 — publisher-first paired native ARM13 SUCCESS; original publisher stable 75s before clone and remained installed, clone MAIN stable 75s with 25/25 lifecycle observations, original key persisted, result-delivery/master-token-read/master-token-decrypt/onboarding-writer hooks all REGISTERED, no uncaught exception and no Metrica fatal suppression. Verdict METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.

The paired source-validation step passed, including:
- persistent PKCS#12 import/pinned-certificate tests: 5/5;
- diagnostic artifact export gate tests: 9/9;
- post-login receipt source-contract tests: 10/10;
- existing private DEX, Metrica, resource, account bridge and native source checks.

The first paired attempt #43586620480 stopped before native execution because the test fixture itself retained its original source PKCS#12 file. This was corrected in 7525887; the subsequent paired run #43586813717 passed. No production code or owner data was involved in that test-fixture failure.

### What the passing native report does and does not prove

The final paired report records:
- publisher stable before clone: true;
- publisher still installed after clone start: true;
- clone MAIN stable 75s: true; lifecycle 25/25;
- master key: ORIGINAL_KEY_PERSISTED;
- ACTIVITY_RESULT_DELIVERY_HOOK, MASTER_TOKEN_READ_HOOK, MASTER_TOKEN_DECRYPT_HOOK, ONBOARDING_WRITER_HOOK: REGISTERED;
- uncaught exception: false;
- owner phone touched: false; binary published: false.

The run had no owner signing secrets configured, so it correctly used DISPOSABLE_PER_CI_RUN. The reported certificate fingerprint 87923acc4fc13161807c74c1bcbde742850ffb9beecd1f69b682f93e9165f275 is only this CI run's temporary certificate. It is NOT the permanent owner certificate and must NOT be set as CELIKOM_A1_INSTALLED_CERT_SHA256. APK export steps were skipped. This validates the default no-secret path and the signer gates; the real owner PKCS#12 has not yet been provisioned or exercised in the main ARM13 pipeline.

### Correction to the old APK hash note

The previously noted APK hash 2d043de0fdabcd9ee4109d01c376d764d4e640b4a4dd07df1bffb6a0264f7e63 is confirmed in the output of older run #43450303301 (artifact #14050162270, source commit 1ddb7811c74dd2b298f21421f4a523659649bce5). It is not the APK from NAV9 artifact #14081618529. The NAV9 diagnostic marker is present in source commit e9cdd607e668304aa97371399464104242aca601, whose closest matching later artifact #14081618529 has APK SHA-256 78f110eeadac9d313e2f9f2212dd0432a4dce0eac828b4defa3c9a6f2dfb8158 and certificate fingerprint 03c2917442666c49d3d60466e0ed43077321ee472e7915d065b4bb4c1b3b6081.

The diagnostic TXT carries the NAV9 build marker but not the CI run ID or APK SHA. The #140816 artifact is the closest time/build match to the diagnostic session, not a cryptographic proof of the exact file on the phone. Keep CELIKOM_A1_INSTALLED_CERT_SHA256 unset until the installed APK itself is verified.

### Current gate and next action

- Working source remains one branch: experiment/android-a1-metrica-init-state-observer-arm13-20261112.
- No owner signing secrets or variables were created by CI.
- No APK was exported and no phone, Yandex account, or local app data was touched.
- Old exact rollback backup backup/android-a1-nav12-final-handoff-r3-20261114 remains at 833531f931cd3a8877bfc0e816dbaf4dbe6c808f.
- A new validated-source backup should point to the final NAV13 handoff commit after this documentation update.
- Do not uninstall the current diagnostic clone while the login loop is unresolved. The fresh-install workflow input remains false by default and requires explicit owner approval.
- Stage A remains NO-GO; Stage B remains LOCKED. No audio or successful Passport login is claimed.
