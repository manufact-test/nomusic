# CELIKOM Android — exact native ABI blocker investigation, 09.11.2026

Real API35 x86_64 + ARM-translation [CI 42678755544](https://github.com/manufact-test/nomusic/actions/runs/42678755544):
KVM emulator booted and full five-split structural clone preparation PASS,
but the **publisher-signed original** failed initial Android PackageManager
install: `INSTALL_FAILED_NO_MATCHING_ABIS` / `Failed to extract native libraries, res=-113`.
The clone was never installed, launched or tested. This is an ABI mismatch,
NOT proof the clone fails Android package identity, authentication or audio.

New CI-only signed original native-lib inventory checks exact #170gpr five
publisher-signed splits and reports which ABI directories are actually
present. Avoid assumptions that x86_64's ARM64 translation supports ARMv7.
No APK sharing, modification, installation or user data.

If signed inventory proves only `armeabi-v7a`, one bounded alternative:
Ubuntu/KVM Android 11 (API30) Google APIs `x86` 32bit system image with
built-in ARMv7 translation. This tests only package coexistence, with no
LSPatch, Play Protect bypass, login, media or decoder. It is NOT a HONOR
Android 13 compatibility verdict. Do not execute unless the ABI inventory
supports the rationale and the image confirms its native bridge/ABI set.
