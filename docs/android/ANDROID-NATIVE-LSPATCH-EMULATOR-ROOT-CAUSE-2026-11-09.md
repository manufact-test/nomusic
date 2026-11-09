# CELIKOM Android · native Yandex LSPatch startup blocker · 2026-11-09

**Verdict:** We have a structural rootless-patched native Yandex build, **not a runtime-capable native replacement yet**. Isolated Android 11 x86 emulator with ARMv7 translation runs the original publisher-signed native Yandex but the modified native host crashes **before any CELIKOM code**, even if ZERO CELIKOM modules are embedded. This is an objective **LSPatch native loader / emulator compatibility NO-GO**, not evidence the FileInfo hook is wrong.

## Three independent controls (all on disposable, account-free AVDs)

| Build / condition | APK installation | Process after launch | Evidence |
| --- | --- | --- | --- |
| **Unmodified** Yandex `ru.yandex.music 2026.10.3 #170gpr`, 5 publisher-signed parts, same Android 11 Google Play x86 AVD (ARMv7 translation) | PASS | **PASS**, 5/5 consecutive samples alive | [run 42621833205 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42621833205) |
| **LSPatch + CELIKOM read-only libxposed observer**, same #170gpr 5 parts, all lab signed, explicit `sigbypass=0` | PASS | **FAIL**, 0/5 samples; no observer lifecycle | [run 42622523007 NO-GO](https://github.com/manufact-test/nomusic/actions/runs/42622523007) |
| **LSPatch-only / ZERO CELIKOM modules**, same host/version/splits and lab signer, `sigbypass=0` | PASS | **FAIL**, 0/5 samples | [run 42622723034 NO-GO](https://github.com/manufact-test/nomusic/actions/runs/42622723034) |

**Crash category:** `ExceptionInInitializerError` + `UnsatisfiedLinkError`; observed `dlopen failed`, **`liblspatch.so` / LIBRARY_NOT_FOUND**. This is an error in the native patch loader path on the tested emulator; the no-module control proves the CELIKOM observer is not responsible for the initial crash. Do not conclude yet whether the problem generalizes to real ARM hardware, because the host APK's native libs are **armeabi-v7a** and the AVD is x86 with ARM translation. A separate earlier Android 13 x86_64 AVD failed at install with `INSTALL_FAILED_NO_MATCHING_ABIS` [run 42614243825](https://github.com/manufact-test/nomusic/actions/runs/42614243825).

## Correct diagnostics / implementation

- `android/native-yandex-hooklab/diagnose_emulator.py`: fresh package/install/start/process checks; only anonymized lifecycle states, exception **types**, shared-object **basenames** and loader category; never raw logcat, account IDs, URLs, tokens or user data. Baseline mode and no-module control supported.
- `stage_original_baseline.py`: separately checks exact publisher-signed unmodified APK, 5 splits, before disposable AVD install; no password or phone.
- `ephemeral_patch_lab.py`: independently verifies original signer and version; patcher `JingMatrix/LSPatch v1.2-487`, ephemeral lab signing, `sigbypass=0`; optional **no-module** control, no APK distribution; includes read-only preflight for exact declared `sw7.y0/z0` signatures.
- `android-native-yandex-emulator.yml`, `android-native-yandex-baseline.yml`, `android-native-yandex-patcher-control.yml`: reproducible independent controls, no rooted device or disable-Play-Protect workaround.
- Next additional static check in `ephemeral_patch_lab.py`: verify each of four `liblspatch.so` ELF machine codes and ZIP_STORED 4096-byte alignment of embedded native runtime. **Do not claim PASS until corresponding CI passes.**

## Product constraints

CELIKOM should substitute approved alternate source **in original native Yandex player**, before `prepare`, matching catalog track+edition. `FileInfoApi → FileInfoDto.urls/codec/key → sw7.y0/z0 → eed` is verified *static* source candidate on exact #170gpr; actual runtime source hook, Yandex login, native pause/seek/next and Play Protect are **NOT tested**.

The official app on owner's HONOR, stable Test.50, production backend/catalog and unrelated projects remain intact. Rootless patching re-signs `ru.yandex.music`; it cannot update the publisher-signed app in place. User permitted separate test hardware/emulator **only**; do not install/replace on the primary HONOR or bypass signature and security checks. Until access to a native ARM Android test environment with Play Protect ON, further x86 emulator retries of the same LSPatch build without a concrete upstream fix are wasted work.

