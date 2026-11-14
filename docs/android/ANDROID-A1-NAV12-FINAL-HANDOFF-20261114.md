# CELIKOM Android A1 — NAV12 final handoff (14 Nov 2026)

## Repository state

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- Source snapshot before this documentation refresh: 4297bbeaf0d0913fbd6f1944827a33b8cba7043e. Exact pre-classifier backup: backup/android-a1-nav12-post-dex-writer-dataflow-20261114 at 4297bbe. Previous docs-stage checkpoint: backup/android-a1-nav12-exact-writer-classification-handoff-20261114 @ a459fbeab64832038b515dc4f70e64e71f59db28. Final handoff backup branch: backup/android-a1-nav12-final-handoff-r3-20261114; verify that it matches the working HEAD before continuing. Earlier NAV12 handoff backup backup/android-a1-nav12-final-handoff-r2-20261114 remains at 01eed9cd9c4214680cb52d3f10ce442b1976ee3a.
- Pre-NAV12 exact rollback: `backup/android-a1-nav12-pre-onboarding-writer-trace-20261114` @ `00f9e4485a2814aa81ed9b089fc40c83e02d96f8`
- Earlier stable source checkpoints: `backup/android-a1-nav9-pre-token-callback-witness-20261114` @ `50fc7ca`; `backup/android-a1-nav10-pre-master-token-crypto-status-20261114` @ `a0410c5`; `backup/android-a1-nav10-postlogin-crypto-witness-before-key-init-20261114` @ `a0a4565`; `backup/android-a1-nav11-key-order-before-native-event-gate-20261114` @ `9c141f5`.

## What the last pass accomplished

### 1. Fresh-install Passport key order — runtime proven, not owner-login proven

The independently signed CELIKOM clone uses the original 2025.10.4 Passport AES master-token path. The vendor's own `v.try()` generates and persists `yandex_am_storage/master_token_key`; the key is cached through `LY7a`. NAV11 invokes this original SDK method in clone MAIN before Passport starts **only when both the clone-owned AccountManager account and key are absent**. It never rotates an existing key or touches an existing account.

Strict native Android13 reports confirmed `master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED` in BOTH:
- [#43574754576 — clone alone](https://github.com/manufact-test/nomusic/actions/runs/43574754576), SUCCESS
- [#43574754550 — original publisher installed first, then CELIKOM](https://github.com/manufact-test/nomusic/actions/runs/43574754550), SUCCESS

This proves the vendor's own key-generation method persisted the key on fresh Android13 in both layouts. It does **not** prove an OTP login, token retrieval, userInfo, screen transition or audio.

**Important for NAV9:** the owner device already has a clone-owned account. The fresh-install preinitializer therefore deliberately does not run for that state; if the key is absent it emits `ACCOUNT_EXISTS_NO_KEY_UNCHANGED`. Do not force-create or rotate a key against an existing encrypted account. The current NAV9 user data has not been modified.

### 2. Read-only post-login receipt chain

The clone-only module observes the real vendor path without manufacturing success:
- `MASTER_TOKEN_READ`: clone-owned `AccountManager.getPassword` result category only.
- `MASTER_TOKEN_DECRYPT`: real vendor decrypt result exception presence only.
- `POSTLOGIN_PUBLISH`: original `ZX5.if(WS3)`, including exact `REAL_USERINFO_SUCCESS` type only.
- `POSTLOGIN_CONSUME`: original `hT3.try(Bundle,String)` receives `EntryScreenCloseLoginKey`.
- `POSTLOGIN_MAIN_ROUTE`: original `YS3.if(lw4,boolean)` invocation and return/throw.

No password, account identifier, token, Bundle payload or userInfo fields are recorded. No result, preference, onboarding state or Activity launch is synthesized.

### 3. Final NAV12 onboarding writer investigation

NAV9 owner diagnostics show `ONBOARDING_PREF / ENTRY_ACTIVITY / UNSET` four times, including after the clone-owned account is visible. Exact original DEX inspection establishes that `MainScreenActivity.onCreate` reads `getBoolean("onboarding", true)`, so an absent key resolves to TRUE. The four UNSET observations are NOT evidence of a blocked Main route and must not be treated as the login-loop cause. `f67` is in the app upgrade/initialization family, not a proven Passport success callback.

The final source pass adds a read-only observer restricted to the clone's exact `Yandex_Music` SharedPreferences instance:
`ContextImpl.getSharedPreferences("Yandex_Music")` → `SharedPreferencesImpl.edit()` → `EditorImpl.putBoolean("onboarding", value)` → actual `commit()` or `apply()`.

It logs only the boolean, a sanitized first non-framework caller class/method and the real commit/apply result. It does not write the preference. Editor tracking was corrected so commit/apply is reported only when that editor actually received `putBoolean("onboarding", ...)`, not for unrelated edits to the same preference file.

A private, read-only exact-2025 DEX scanner was added:
- `android/native-yandex-hooklab/ci/a1_private_onboarding_contract.py`
- `android/native-yandex-hooklab/ci/test_a1_private_onboarding_contract.py`

It inventories methods containing the exact `onboarding` literal and preference API calls from the pinned signed 2025.10.4 base APK. It prints method identifiers/API names only, never DEX bytes, tokens, account data or credentials.

The native Android13 acceptance parser now also requires `ONBOARDING_WRITER_HOOK / ANDROID / REGISTERED`. Idle native CI can prove hook registration, but cannot prove that a real login invokes a writer.

## CI status at handoff

Previously confirmed:
- [#43574754576](https://github.com/manufact-test/nomusic/actions/runs/43574754576) — SUCCESS, `ORIGINAL_KEY_PERSISTED`.
- [#43574754550](https://github.com/manufact-test/nomusic/actions/runs/43574754550) — SUCCESS, `ORIGINAL_KEY_PERSISTED`.

Latest NAV12 strict Android13 gates completed SUCCESS:
- #43577067135 — clone alone: onboarding_writer_hook_status=REGISTERED, master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED.
- #43577366277 — publisher-first paired: same two runtime states; publisher remained installed and clone MAIN was stable 25/25.
Both runs prove read-only hook registration in the two Android13 layouts. They are idle startup tests, not login, token, userInfo, navigation or audio acceptance. Neither touched the owner phone or exported an APK.

The original DEX inventory in #43576640113 was a coarse co-occurrence scan. The stricter direct-call/dataflow classifier and its expanded unit tests are in commits 9592930 and 4297bbe. Paired Android13 workflow #43578243485 completed SUCCESS. Its exact onboarding scan/test and private DEX classifier passed; native clone lifecycle also reached 25/25 stable observations. Verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `stage_a: NO_GO`. This is not a real Passport login or audio acceptance. The classifier's static output is not runtime login evidence.

### Refined exact onboarding writer result — original signed DEX

The earlier five writer candidates were broad same-method co-occurrence matches. Private disassembly of the pinned original 2025.10.4 DEX confirms three actual direct SharedPreferences writers:

- Lf67;->if (classes6.dex) directly obtains Yandex_Music, calls edit().putBoolean("onboarding", value).apply(). Its previously traced caller chain is the app upgrade/initialization family via LNJb.invokeSuspend, not the demonstrated Passport success chain.
- Lru/yandex/music/profile/ProfileActivity$b;->emit and ProfileActivity$c;->emit (classes6.dex) also directly write the same preference and call apply(). These are profile coroutine handlers, not evidence of Passport completion.
- LVj1;->transient (classes3.dex) is a configuration-map setValue entry for the string onboarding, not a SharedPreferences write.
- LUc1$b;->emit (classes6.dex) contains the literal near unrelated notification-timestamp contains/getLong logic and a separate wrapper setValue; it is not a direct putBoolean("onboarding") writer.

The scanner now preserves the coarse inventory and additionally checks the direct register path Context.getSharedPreferences("Yandex_Music") → SharedPreferences.edit() → Editor.putBoolean("onboarding", …) → apply/commit. It emits confirmed_shared_preferences_onboarding_writers and confirmed_persisted_onboarding_writers. Added tests cover wrong preference file, wrong key, non-persisted write and co-occurrence false positives.

No one of these three writers is proven to run on Passport → Music Success(userInfo). The NAV12 runtime observer is registered, but idle CI has no real login, so only a future genuine bounded login receipt can identify whether any writer fires and which caller is involved. Do not call Lf67 manually or force the preference.

## What remains unresolved

The NAV9 owner report confirms:
- `ACCOUNT_ADD / CLONE_OWN / ADDED` and `ACCOUNT_STATE / CLONE_OWN / ONE`.
- Passport activities called `setResult(OK)`; this is not proof Android delivered a result to Entry.
- Four `ONBOARDING_PREF / UNSET` observations.
- No observed new Main screen and no observed process crash.

It does **not** establish whether `getPassword` returned a master token, whether decrypt succeeded, whether Music produced `Success(userInfo)`, whether FragmentManager delivered the close-login event, or whether `LYS3` ran.

## Release and owner-device safety

- NAV8 and NAV9 have different outer signing certificates; each research CI run currently creates a disposable signer.
- Do not produce or install another owner APK until a dedicated persistent A1 signing identity is provisioned and verified. Do not reuse the Test.50 production signing key without explicit owner approval.
- No APK was exported in this pass.
- Do not ask the owner to repeat OTP, reinstall, clear data, use ADB/cable, remove original Yandex, or change onboarding.
- Keep the embedded publisher-signed APK, original Yandex installation, Test.50 and all production paths untouched.

## Next developer's exact order

1. Read this file, `NEXT-CHAT-ANDROID-A1-LEAD-20261113.md`, `ANDROID-A1-POSTLOGIN-RECEIPT-WITNESS-AND-SIGNER-GATE-20261114.md`, and `ANDROID-A1-NAV9-SIGNED-2025-POSTLOGIN-CONTRACT-20261114.md`.
2. Verify the working branch HEAD and final handoff backup branch `backup/android-a1-nav12-final-handoff-r3-20261114` are identical. Do not reset to earlier NAV12 checkpoints.
3. Hook registration is already confirmed in both layouts: #43577067135 clone-alone and #43577366277 publisher-first paired both show `ONBOARDING_WRITER_HOOK=REGISTERED` and `ORIGINAL_KEY_PERSISTED`. Do not repeat this test unless source changes affect hook setup.
4. The exact onboarding scan/test steps in #43578243485 have passed; wait for the overall native ARM13 workflow conclusion and read its sanitized output. The manual DEX check confirms three direct persisted writers and two coarse false positives; none is proven on Passport success.
5. Continue the real Passport → master token read/decrypt → Success(userInfo) → FragmentManager → Main route investigation. Never invoke a writer, mutate onboarding, fake success or request another OTP.
6. Resolve dedicated persistent A1 signing before any owner delivery. Stage A remains NO-GO; Stage B remains LOCKED. Only consider one bounded owner test after a proven fix, stable signer and explicit readiness.

**Stage A: NO-GO. Stage B: LOCKED.** The fresh-install key write is technically proven; the owner's post-login loop is not fixed or owner-verified.


## NAV13 — actual Activity result delivery witness (14 Nov 2026)

The prior `ACTIVITY_RESULT` hook observes only the Passport Activity calling `setResult(OK)`; that is the producer side and does not prove Entry received the result. NAV13 adds a clone-MAIN-only, read-only hook on the Android framework `Activity.dispatchActivityResult(String,int,int,Intent)`. It filters strictly to the clone's real `EntryScreenActivity` receiver and records only `RESULT_OK|RESULT_CANCELED|OTHER`. It never reads `who`, request code, Intent, extras, token or payload and does not alter the result. Registration emits `ACTIVITY_RESULT_DELIVERY_HOOK=REGISTERED|NO_HOOK`; a real delivery emits `ACTIVITY_RESULT_DELIVERY/ENTRY_ACTIVITY/<category>`. This is the next discriminator before the existing genuine Music `Success(userInfo)` publisher hook. Source commit `9e723f3d404f1e78ac9fbf72a699a24cfaf7db1a`; exact source backup `backup/android-a1-nav12-final-handoff-r3-20261114` is advanced to the same commit. Android13 CI runs #43581081486 (paired) and #43581081611 (clone-alone) were queued at handoff; check both before any owner-facing APK or claim. This remains diagnostic-only, no APK export, no OTP, no account/data mutation.


## NAV13 follow-up hardening — independent event quota

Review found the Entry result-delivery observer initially shared the generic Activity-finish counter. That could allow unrelated finishes to consume the result-delivery observation budget before the decisive callback. Corrected in `1f2f0a77243bc9ba3b6dd7169eb7f86fad626073`: delivery now has its own independent atomic quota (48), preserving the event even during a noisy login flow. No event semantics or app behavior changed. New paired/clone-alone ARM13 runs: #43581508098 and #43581508085.


## NAV13 receiver-side Activity result observer — current checkpoint

Source commit `1f2f0a77243bc9ba3b6dd7169eb7f86fad626073` added a separate bounded counter for Entry receiver-side delivery so unrelated Activity finish events cannot consume its quota. Source contract test was added in `468fa14e8a6328e021968143afa8e00712c6ec73`, asserting exact framework signature, receiver filtering, independent bound, and no result/Intent/payload mutation. Standalone clone-only NAV13 CI #43581081611 and paired publisher-first CI #43581081486 both completed SUCCESS. Paired run confirms original publisher installs/launches and remains stable 75s before and after clone startup; clone is stable 25/25 and `ONBOARDING_WRITER_HOOK=REGISTERED`. Neither run performs Passport login, so neither establishes actual `Activity.dispatchActivityResult` invocation. Quota-fix clone-alone rerun #43581508098 has now completed SUCCESS: fresh native ARM13 clone MAIN remained stable for 75s, original SDK master key persisted, onboarding writer hook registered, and no uncaught exception/IllegalStateException was observed. This is a clone-alone differential gate only (publisher intentionally absent), not a Passport login or product pass. Paired quota-fix run #43581508085 was still in its 75s publisher-first test; source-test run #43581718989 was booting native ARM13.  Keep Stage A NO-GO and Stage B LOCKED. Do not export APK or request owner test until CI is green and stable signing + explicit test readiness are addressed.


## NAV13 quota-fix CI update — 14 Nov 2026

Quota-fix clone-alone rerun #43581508098 has now completed SUCCESS: fresh native ARM13 clone MAIN remained stable for 75s, original SDK master key persisted, onboarding writer hook registered, and no uncaught exception/IllegalStateException was observed. This is a clone-alone differential gate only (publisher intentionally absent), not a Passport login or product pass. Paired quota-fix run #43581508085 was still in its 75s publisher-first test; source-test run #43581718989 was booting native ARM13. 


## NAV13 Android 13 receiver-hook correction and verified CI — 14 Nov 2026

The first receiver-side observer used the four-argument Activity.dispatchActivityResult(String,int,int,Intent) signature. The strict runtime registration gate correctly reported NO_HOOK in #43582369283/#43582369302. Root cause: Android 13 API 33 declares the framework method with a fifth String reason parameter. The implementation now hooks the exact five-argument method and reads only argument index 2 (the result-code category); it does not inspect who, request code, Intent, extras, or reason. Android 13 AOSP source confirms the five-argument signature.

The Passport-side setResult producer observer now has its own counter and is filtered to actual PASSPORT_ACTIVITY instances, so unrelated Activity result calls cannot consume its quota.

The native runner now parses ACTIVITY_RESULT_DELIVERY_HOOK and requires REGISTERED for both clone-only and publisher-first paired verdicts. Source contract tests cover the exact API 33 signature, read-only argument handling, independent counters, and runtime-gate presence.

Verified on corrected source b565dc4d050f463397312c8f409b2450cc8bbc79:
- Clone-only #43582980401 — SUCCESS; ACTIVITY_RESULT_DELIVERY_HOOK=REGISTERED, ONBOARDING_WRITER_HOOK=REGISTERED, ORIGINAL_KEY_PERSISTED, clone MAIN stable 75s, no uncaught exception.
- Publisher-first paired #43582980390 — SUCCESS; same three registration/key results, original Yandex's 16 splits installed first and remained installed, publisher stable 75s before clone, clone stable 25/25, no uncaught exception. Verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.

These are startup/lifecycle and hook-registration checks only. No Passport login/OTP ran, no ACTIVITY_RESULT_DELIVERY callback was observed, and no POSTLOGIN_PUBLISH, POSTLOGIN_CONSUME, or POSTLOGIN_MAIN_ROUTE event was produced. No APK was exported; owner handset untouched; signer remains disposable per CI run. Stage A NO-GO; Stage B LOCKED.

Exact source backup backup/android-a1-nav12-final-handoff-r3-20261114 is synchronized with the working branch.


## NAV13 latest no-suppression Android13 CI — 14 Nov 2026

Source 5f683900b966673224babc2d6b684960dc8ea2ac adds hard native-runner acceptance gates for registration of both the original Passport account password-return observer and original Passport token decrypt-outcome observer. The regression test verifies both statuses are required in clone-only and paired verdict paths. Exact backup backup/android-a1-nav12-final-handoff-r3-20261114 is synchronized with the working branch.

- #43583886782 clone-only: SUCCESS; ACTIVITY_RESULT_DELIVERY_HOOK, MASTER_TOKEN_READ_HOOK, MASTER_TOKEN_DECRYPT_HOOK, and ONBOARDING_WRITER_HOOK all REGISTERED; original master key persisted; clone MAIN stable 75s and 25/25 lifecycle; no uncaught exception. Publisher intentionally absent. Verdict CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS.
- #43583886793 publisher-first paired: SUCCESS; same hook/key registration; original Yandex 16 splits installed first and retained; publisher stable 75s before clone; clone stable 75s and 25/25 lifecycle; no Metrica fatal suppression; no uncaught exception. Verdict METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.

Important distinction: these are registration and idle startup tests only. They do not execute Passport login, actual token read/decrypt, Entry result delivery, Success(userInfo), FragmentManager consumption or native Main routing. A REGISTERED status is not an observed callback.

No APK export, no owner-phone action, no account/onboarding mutation. CI signer is still disposable; artifact export remains blocked by the stable-signer gate. Stage A NO-GO / Stage B LOCKED.


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
