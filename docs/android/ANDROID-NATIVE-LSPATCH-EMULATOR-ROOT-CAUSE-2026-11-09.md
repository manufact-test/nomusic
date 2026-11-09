# FINAL STATIC ELF VERDICT — 09.11.2026

**[CI #42623602723 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42623602723)** verified actual patched native Yandex *base.apk* embeds LSPatch `liblspatch.so` **for all four** ABIs: `armeabi-v7a` (ELF32 EM_ARM 40), `arm64-v8a` (ELF64 EM_AARCH64 183), `x86` (ELF32 EM_386 3), `x86_64` (ELF64 EM_X86_64 62). All entries `ZIP_STORED`, and the actual ZIP local-file payload offsets are **4096-byte aligned**. The file is NOT simply omitted, compressed, or built for a wrong ELF ISA. It is present but native `System.load` **cannot resolve/load it in the tested Android 11 x86→ARMv7 translated process**. Android 11 and 13 x86 emulators are not equivalent to native ARM hardware.

Read upstream [JingMatrix LSPatch metaloader](https://github.com/JingMatrix/LSPatch/blob/master/meta-loader/src/main/java/org/lsposed/lspatch/metaloader/LSPAppComponentFactoryStub.java): it uses `VMRuntime.vmInstructionSet`, loads `assets/lspatch/so/<ISA>/liblspatch.so` via `System.load` very early. Tested with `sigbypass=0` (no signature impersonation). Android NDK supports direct ZIP .so loading only if stored and aligned; our static preflight meets these prerequisites but runtime still fails, indicating another loader/ABI/namespace/translator issue. **Do not assert a universal LSPatch bug on native Android ARM** without ARM runtime proof.

**Stop repeating the Android 11 x86/ARM-bridge injection test unchanged.** The next meaningful test requires a *native ARM* Android 13 disposable device/emulator with proper ABI, Google Play Protect ON, no owner-account data or primary HONOR modification, and explicit experimental signing/installation consent. No valid CELIKOM source replacement APK is deliverable from these results. Keep Yandex's native player goal; no WebView or dual player.

---

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

