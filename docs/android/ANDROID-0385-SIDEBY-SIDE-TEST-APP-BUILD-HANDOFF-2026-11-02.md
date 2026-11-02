# CELIKOM Android 0.3.85 — side-by-side test app build handoff (2026-11-02)

**Owner decision:** build the cold-join experiment as a genuinely separate Android application installed alongside stable CELIKOM 0.3.85. Do not create an in-place update APK.

## Goal

Deliver one signed, installable **CELIKOM Test** APK so the owner can keep the currently installed stable **CELIKOM 0.3.85 / code 86** untouched and compare the new cold/new-track handover.

- Stable app remains installed as-is.
- Test app appears as a second launcher entry with label **CELIKOM Test**.
- Test app has its own Android application sandbox, app files, cache, SharedPreferences and local login state.
- Installing or uninstalling the test app must not replace or remove stable CELIKOM.
- The test app contains the exclusive prewarmed cold-join experiment from PR #37. Yandex Music crossfade stays OFF for the first listening check.
- The owner will stop/close stable CELIKOM before starting the test app. Do not run both CELIKOM engines simultaneously against the same Yandex playback session.

## Exact source checkpoint

- Repository: `manufact-test/nomusic`
- Work branch: `feature/android-0385-intro-join-investigation-20261102`
- Current branch HEAD at handoff: `93be328e4745ab727d9d910a8a985ec69d66d2d7`
- Draft experiment PR: [#37](https://github.com/manufact-test/nomusic/pull/37), open and unmerged.
- Experiment CI: [#41419113128](https://github.com/manufact-test/nomusic/actions/runs/41419113128), PASS (32 cold-join checks, full native host suite, accepted seek guard, Android API 36 and D8).
- Accepted 0.3.85 seek source: `053b7d59beb53db5f30b942feba35e51a1ab256a`.
- Stable release: 0.3.85 / versionCode 86 / package `pro.celikom.nativeprobe`.
- Stable signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.

## Required test application identity

Use a distinct Android package/application ID, proposed:

`pro.celikom.nativeprobe.test`

Use:
- Android application label: `CELIKOM Test`
- Test versionName: `0.3.85-test`
- Test versionCode: `86085` (or another explicitly test-only integer, recorded in the receipt; increment it for future upgrades of this same test package)
- The **same original signing key/certificate** as stable CELIKOM, SHA-256 above.
- A test-specific APK filename such as `CELIKOM-Android-0.3.85-TEST-COLD-JOIN-SIGNED.apk`.

The distinct package ID is the key to side-by-side installation and Android's separate app sandbox. A separate APK filename or version number alone is NOT sufficient. The package must be verified from the final signed APK with `aapt dump badging` / package inspection before delivery.

Do not relocate the Java class namespace. The existing Java classes may remain under `pro.celikom.nativeprobe...`; Android application ID and Java namespace are separate concepts in this reconstructed APK.

## Manifest identity collisions to audit and isolate

The pinned base manifest currently declares:
- package: `pro.celikom.nativeprobe`
- signature permission and uses-permission: `pro.celikom.nativeprobe.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
- FileProvider authority: `pro.celikom.nativeprobe.package-export`
- AndroidX Startup authority: `pro.celikom.nativeprobe.androidx-startup`

For the test APK, change the manifest package to the test application ID and give every app-unique permission/authority a test-specific value, e.g.:
- `pro.celikom.nativeprobe.test.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
- `pro.celikom.nativeprobe.test.package-export`
- `pro.celikom.nativeprobe.test.androidx-startup`

Audit any hard-coded FileProvider authority in base smali and Java before changing the manifest authority; patch only the identity-sensitive string(s) that actually need to match. Do not globally replace `pro.celikom.nativeprobe` throughout DEX/smali: that is also the Java class namespace and component class names, which should remain valid.

## Disable the stable OTA updater in the test app

This is mandatory. The stable updater is tied to the stable package and manifest:

- `UpdateCenter.MANIFEST` points to `/updates/android/stable.json`.
- `UpdateCenter.parse()` accepts only packageName `pro.celikom.nativeprobe`.
- `RecorderActivity.java` currently constructs `new UpdateCenter(this, updatesPanel)` at line 54; its constructor schedules a job and immediately checks the stable manifest.
- `build_release.py` currently adds `REQUEST_INSTALL_PACKAGES`, `UpdateCheckJob`, and `UpdateInstallReceiver` to the stable manifest.

For the test application:
1. Do not instantiate `UpdateCenter`; show a static note such as **«Тестовая сборка · автоматические обновления отключены»** instead.
2. Do not schedule `UpdateCheckJob`.
3. Do not add `REQUEST_INSTALL_PACKAGES`, `UpdateCheckJob`, or `UpdateInstallReceiver` to the test manifest.
4. The test app must never fetch the stable manifest, download the stable APK, or offer an install action.
5. Keep the stable updater source and behavior unchanged for the stable package.

The existing `android-auto-publish-hostinger.yml` `test_only` path is **not suitable as-is**: it still builds the package from stable `release-spec.json` (`pro.celikom.nativeprobe`) and would install over the current app. Do not use that path without a separate package-aware test builder and verifier.

## Build implementation requirements

Implement a dedicated, clearly separated test packaging mode on the work branch. Prefer a dedicated `test-app-spec.json` plus `build_test_release.py` / `verify_test_release.py`, or a strictly isolated explicit test mode in shared packaging code. Do not weaken the stable release contract.

The current stable build pipeline has important assumptions:
- `release-spec.json` pins stable package `pro.celikom.nativeprobe`, version 0.3.85/code86 and signer.
- `release_contract.py` validates that stable identity.
- `build_release.py` reconstructs the pinned base APK, compiles the Java addon, patches manifest/version, adds stable updater components, signs with the original key and calls `verify_release.py`.
- `verify_release.py` explicitly requires the stable package, label, manifest structure and updater components.

Therefore:
- Do not change stable `release-spec.json` package/version/code/signer.
- Do not weaken `release_contract.py` or `verify_release.py` to accept a second identity.
- Add test-specific build metadata and test-specific verification that prove the test package ID, test label/version, unique authorities/permission, absence of updater UI/jobs/receiver/install permission, correct DEX, v2/v3 signature and exact original signer.
- Preserve the pinned base APK SHA and dependency checks.
- Compile the current experimental source from the work branch; do not substitute an older DEX or stable 0.3.85 DEX.
- Keep the seek golden guard `android/native-companion/tests/check_0385_seek_baseline.py` unchanged and passing.
- Verify that stable and test APKs have different package IDs but the expected same signing certificate.
- Verify final APK archive/manifest and calculate SHA-256.

## Build and delivery channel

Create a dedicated manually dispatched GitHub Actions workflow restricted to this work branch (or another equally auditable nonpublishing build route). Reuse the repository's original signing secrets only inside the signed build job. Upload the signed test APK and a JSON build receipt as a GitHub Actions artifact with a practical retention period (e.g. 7 days).

**Do not:**
- run the stable publisher;
- call the Hostinger stable publish path;
- upload the test APK to the stable release directory;
- edit `/updates/android/stable.json`;
- edit the production update manifest or OTA endpoints;
- use the existing same-package `test_only` artifact as the side-by-side deliverable;
- merge PR #37 or publish stable.

The artifact must be installable and signed. An unsigned inspection APK is not an owner test build.

## Required verification before delivery

1. Existing full native host suite passes, including the 32 cold-join experiment checks.
2. `check_0385_seek_baseline.py` passes unchanged.
3. Android API 36 compile and D8 pass.
4. Test APK package is exactly `pro.celikom.nativeprobe.test`; stable package remains `pro.celikom.nativeprobe`.
5. App label is `CELIKOM Test`; test versionName/code are the declared test values.
6. All package-specific manifest authorities and signature permissions are unique; no provider authority collision remains.
7. Test APK has no update UI/constructor, no scheduled update job, no updater receiver, no `REQUEST_INSTALL_PACKAGES`, and no stable-manifest request.
8. Test APK signer matches stable certificate SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
9. Stable APK and stable release metadata are byte-for-byte untouched; no Hostinger request/write is performed.
10. Produce a receipt with source commit, package, label, versionName/code, signer SHA-256, APK SHA-256, file size, CI run URL, and `stable_published: false`.

## Owner's one device check after delivery

The owner installs the test APK normally. Android should show two apps:
- **CELIKOM** — existing stable 0.3.85, untouched.
- **CELIKOM Test** — experimental cold-join build.

No uninstall or replacement of stable CELIKOM is required. Before testing, stop/close stable CELIKOM; then open CELIKOM Test and sign in if its separate local state requires it. Keep Yandex Music crossfade OFF. Listen to one or two representative new-track starts only. Do not repeat the accepted seek test unless a regression is actually heard.

A successful build/CI is not acoustic acceptance. After the owner's listening verdict, decide whether the experiment is useful. Only then consider a later stable integration/release as a separate, explicitly approved task.
