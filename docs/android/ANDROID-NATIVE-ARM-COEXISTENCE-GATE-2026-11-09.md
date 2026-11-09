# CELIKOM Android — clean ARM original+clone coexistence gate (09.11.2026)

Source structural milestone: [CI 42670648029](https://github.com/manufact-test/nomusic/actions/runs/42670648029) exact scoped 5/5-split rebuild/sign/hash PASS. This is **not** a native app runtime PASS.

New isolated emulator experiment:
- `macos-15` ARM64 Android 13 clean Google-APIs emulator, NO owner account, no original owner device connection.
- Download exact pinned original publisher-signed five splits and generate the ephemeral five-split alternate package via the same verified Phase2 code.
- Android PackageManager installs original `ru.yandex.music` first, then `pro.celikom.yandex.nativeclonelab`, without removing the first. Check `pm path` yields 5+5 splits.
- Attempt clone's ordinary launcher and inspect only process alive boolean. Never sign in, interact with private data, play audio, hook native decoder, suppress Play Protect or alter a signature check.
- Hard stop on failure and print sanitized failure stage. No vendor binaries or keys uploaded; temporary files deleted.
- Even coexistence PASS means ONLY install and initial launch in an emulator, not normal login, Play Protect on HONOR, decoder/MediaSource or audible replacement.

Script opt-in mode `CELIKOM_CLEAN_ARM_EMULATOR=1` in
`android/native-yandex-hooklab/clone_native_identity_phase2_ephemeral.py`.
New workflow: `.github/workflows/android-native-clone-arm-coexistence-ephemeral.yml`.
No changes to production, user phone, stable Test.50, Windows or extension.
