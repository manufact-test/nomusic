# CELIKOM Android 0.3.72 — signed OTA release receipt

**Date:** 31 October 2026  
**Status:** published to the existing stable Android update channel; physical HONOR acceptance is pending.

## Release identity

- **Version:** 0.3.72
- **versionCode:** 73
- **Package:** `pro.celikom.nativeprobe`
- **APK:** `CELIKOM-Android-0.3.72-SIGNED.apk`
- **APK size:** 8,742,985 bytes
- **APK SHA-256:** `b8db7f596e20f4a38852f375e41aa3caba7fff2f0111a96e69b969be06cd147f`
- **Compiled addon DEX SHA-256:** `a3e95c2b49f5309ba24086a3ba5f1b4d1c4876556d33a7fc8ca7f04b33adfbc1`
- **Pinned signing certificate SHA-256:** `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`

## Published endpoints

- **Stable manifest:** https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json
- **Immutable signed APK:** https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/73-b8db7f596e20f4a38852f375e41aa3caba7fff2f0111a96e69b969be06cd147f.apk
- The APK was uploaded to the existing private release store. The remote publisher verified the uploaded file's SHA-256 and byte size before atomically moving it into the immutable release path and switching the stable manifest.
- The final CI step fetched the live stable manifest and compared it byte-for-byte as JSON with the release manifest. Result: **Stable Android version published: 0.3.72 / 73**.

## Git and CI provenance

- **Repository:** `manufact-test/nomusic`
- **Production branch:** `feature/android-unified-preparation-seek-gate`
- **Release commit:** `8115228aa9c10b6244166cb44fff1760f0d32f1b`
- **PR:** [#23 — Android 0.3.72 OTA release](https://github.com/manufact-test/nomusic/pull/23)
- **Staging branch:** `feature/android-0372-ota-release-staging`
- **Staging validation:** [run 41240323493](https://github.com/manufact-test/nomusic/actions/runs/41240323493) — SUCCESS; stable publish correctly skipped.
- **Production build + publish:** [run 41240453908](https://github.com/manufact-test/nomusic/actions/runs/41240453908) — SUCCESS.
  - Full native host regression suite — SUCCESS.
  - Android API 36 Java compilation and D8 — SUCCESS.
  - Source-to-DEX provenance and release-contract negative cases — SUCCESS.
  - Signed APK verifier — SUCCESS: original signer, APK v2/v3 signature, alignment, package/version/API, approved manifest boundary, unchanged catalogue assets, exact compiled addon DEX, and no signing/recovery files in the APK.
  - Stable publisher — SUCCESS; live manifest verified at 0.3.72 / versionCode 73.
- The existing backup `backup/android-0371-pre-0372-stable-release-20261031` preserves the pre-release production HEAD `ca31f09b71b65890a020e5b3688fdf6061fa008c`. The separate owner-approved 0.3.71 baseline backup remains untouched.

## What changed in the app

This release is intentionally based on the current production audio source at 0.3.71. It does **not** include the experimental seek-alignment staging patch.

The only runtime behavior change is in `UpdateInstallReceiver`:

1. On `STATUS_PENDING_USER_ACTION`, CELIKOM opens the Android system confirmation UI as before.
2. On `STATUS_SUCCESS`, the receiver checks that the installed package version is at least the expected versionCode from the install request.
3. Only after that verification, it calls `ActivityManager.getAppTasks()` and `AppTask.finishAndRemoveTask()` to close CELIKOM tasks and remove them from Recents.
4. If installation is cancelled, fails, the installed version cannot be verified, or task removal fails, it does not claim success or relaunch CELIKOM.

**Chosen behavior:** after a successful update, CELIKOM stays closed and is removed from the recent-apps list. The owner opens it manually. It does not auto-reopen.

No audio engine, seek, pause, Next, Stop, Bluetooth, buffering, decoder, or audio-session code was changed. No update backend, website PHP, endpoint implementation, or signing identity was changed; only the existing stable manifest pointer was advanced by the established publisher.

## Owner's HONOR test — still required

The pipeline proves the release was built, signed, uploaded, and advertised by the live manifest. It does **not** prove the physical install/Recents behavior on the HONOR phone.

1. Open the existing CELIKOM 0.3.71 app.
2. Press **Проверить обновления**. It should find 0.3.72.
3. Press **Скачать и установить**, then confirm Android's system **Обновить** prompt.
4. After Android reports a successful install, CELIKOM should disappear from the screen **and** from the recent-apps list.
5. Open CELIKOM manually. Confirm version 0.3.72 and press **Проверить обновления** again; it should report that the latest version is installed.
6. If the app reports no update, send a screenshot of the result and a fresh diagnostic. Do not uninstall the existing app or clear its data.
7. If the app closes but remains in Recents, send a screenshot/video of the Recents screen. That is the exact device-level acceptance case for the new receiver behavior.

Do not use the test as evidence that any audio transition or seek artifact is fixed. The release is an OTA/updater lifecycle test plus a version increment; acoustic acceptance remains separate.

## Owner acceptance update — 01.11.2026

**ACCEPTED on HONOR:** The owner confirmed the in-app updater discovered and downloaded 0.3.72, the system installed it, CELIKOM closed, and no CELIKOM card remained in Android Recents. The owner explicitly chose to keep this successful exit behavior; **do not redesign or reopen this task**.

**Audio NOT ACCEPTED:** The owner separately listened to 0.3.72 and reported no perceptible improvement from 0.3.71. Finger scrubbing sometimes produces repeated tiny skips and cold song-attach can still sound like a volume dip or micro-repeat. This release did not contain an audio patch. Diagnostic evidence and the next chat audit plan: [ANDROID-0372-HONOR-OWNER-LISTENING-AND-DIAGNOSTIC-CHECKPOINT-2026-11-01.md](ANDROID-0372-HONOR-OWNER-LISTENING-AND-DIAGNOSTIC-CHECKPOINT-2026-11-01.md).

The device acceptance result supersedes the earlier “HONOR acceptance pending” status in this receipt; it does not imply acoustic acceptance.
