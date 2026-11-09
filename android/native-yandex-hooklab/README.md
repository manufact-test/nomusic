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
