# CELIKOM A1 — Persistent owner signer and install transition

Date: 14 November 2026  
Repository: manufact-test/nomusic  
Working branch: experiment/android-a1-metrica-init-state-observer-arm13-20261112


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
