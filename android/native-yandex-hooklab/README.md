# CELIKOM Android native-Yandex hook lab (ISOLATED, READ-ONLY)

**Status:** Source code only; builds a *CELIKOM Xposed module APK* (not an independent music player). Owner authorized research and preparation for **a separate disposable test device only**. No package was installed, and **nothing** on the owner's HONOR, stable Test.50, catalog or server is touched.

## Exact target

- Native Yandex Music `ru.yandex.music`, **2026.10.3 #170gpr**, code **24026531**, exact original signer SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba` pinned in the offline host audit.
- Exact first-party API: `FileInfoApi` / `OldFileInfoApi` → `FileInfoDto.urls,codec,key,bitrate,quality` → `sw7.y0/z0` → `eed`. Static evidence and original source trace: `docs/android/ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md`.
- This module hooks **only the exact `sw7.y0(FileInfoDto,boolean):eed` and `sw7.z0(OldGetFileInfoDto,boolean):eed` after original conversion** and logs throttled **COUNTS ONLY**. A different name/signature/version fails shut. It passes all original arguments and original return value unchanged. Does not read `urls`, `key`, OAuth headers or account data; has **no network / accessibility / storage permissions**. No MediaPlayer, WebView, second clock or stream replacement.

## Build and verify source

Use Java 17, Android SDK 35, Gradle 8.11.1:

```bash
gradle -p android/native-yandex-hooklab :app:assembleDebug --no-daemon
```

Also run deterministic plain-JVM `HookSpecTest` with synthetic replacement DTO classes. CI intentionally does **not** retain a binary as a release artifact; the module APK alone cannot alter the unmodified Yandex app, and Play Protect/device startup cannot be verified by CI.

## Authorized isolated test path (NOT done automatically)

Use source-available **JingMatrix/LSPatch v1.2 build 487**, pinned upstream release, as a **tool** (GPL-3.0; evaluate licence obligations before any distribution). For a spare/emulator with Android 13 ARM64, patch the separately-verified original #170gpr **base plus splits** using embedded mode, with local lab signing. Never upload original/patched Yandex packages to GitHub, store logs containing account data, or share patch distribution. Verify after patch that all splits have matching lab signer, correct package/version, and modern module metadata. Original Yandex package cannot remain installed with same ID and a different signing certificate; do **not** try to upgrade/overwrite it, and **never delete the owner's official Yandex**. No special permission to switch off Play Protect has been given.

### Manual Gate 1 witness (spare device only)

- On a clean disposable test device with Play Protect ON, check unmodified Yandex baseline, then controlled patched test copy if safe and legally permitted.
- Confirm module logs `observer: native file-info converter hooks armed; read-only` and counters during native playback/seek/Next; verify original stream still plays. Record **only event categories, package version and aggregated counts**, never source URLs, user credentials, tokens or private files.
- **Counters are not enough** to release CELIKOM. Need identify exact track+edition and prove mapping from response model to *native* source/decoder before the next step. If original client fails login, package integrity, or Play Protect, stop—never bypass warnings or protections.

**No claim of working CELIKOM replacement:** actual audio source selector, account-safe broker, Google Play Protect verdict and native pause/seek continuity are still unverified. This is preparation for a genuine in-process test, not another user-facing fake player.

## Read-only spare ARM hardware preflight (09.11.2026)

Before considering any installation on a **separate disposable device**, run `python3 android/native-yandex-hooklab/probe_arm_device.py` from a PC with adb and exactly one authorized **spare** phone connected. It uses only `adb devices`, `getprop` and `pm path`; it never installs, removes, launches, roots or changes anything. It refuses the known owner HONOR 50, an existing Yandex package, Android below API 33, emulators, no Play Store and devices lacking `armeabi-v7a` (the exact native #170gpr host contains ARMv7 32-bit libraries). On a 64-bit-only Android device the official host is ABI-incompatible even if its CPU is arm64.

**A green preflight is NOT permission to install anything.** It is not proof that Play Protect is enabled, that the phone is an authorized spare, or that libxposed works. Those require explicit on-device checks and a separate lab installation decision. It never reports device serials, paths, account data or Play Protect status guesses. Unit tests run in the existing hooklab CI without adb.

## 10 Nov 2026: final source admission MODEL (not a live Yandex hook)

`NativePrePrepareAdmission.java` coordinates exact native track+edition+generation observation, FileInfo and the actual decoder-descriptor identity (only an approved future host may supply those values), plus a single pre-prepare source decision. Unknown identity, unsafe/stale candidate, edition mismatch, or missing real FileInfo → original source. Duplicate/stale prepare → no apply. No MediaPlayer or source mutation in the model.

[CI 42780177178](https://github.com/manufact-test/nomusic/actions/runs/42780177178) SUCCESS 2/2: 35,032 model admission assertions incl. 5,000 Next; 10,037 NativeSourceGate; 10,015 NativeTrackIdentityGate; read-only module APK built in CI but NOT released. **No live Yandex decoder/source replacement has been verified.** See `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md` and `docs/android/NEXT-CHAT.md`.

