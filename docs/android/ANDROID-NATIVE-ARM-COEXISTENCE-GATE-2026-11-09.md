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


## Emulator/runtime gate hard blocker — 09.11.2026

- Clean original Yandex ARM64 macOS GitHub Actions emulator: [run 42669152016](https://github.com/manufact-test/nomusic/actions/runs/42669152016) **FAIL** before any APK install. Full QEMU log: `HVF error: HV_UNSUPPORTED` / `failed to initialize HVF: Invalid argument`; then adb device absent and boot timeout. This is runner nested-virtualization failure, **not** evidence against original Yandex or clone.
- GitHub docs confirm nested virtualization unavailable on macOS arm64 hosted runners. Do NOT rerun default HVF configuration.
- First coexistence workflow [run 42671525588](https://github.com/manufact-test/nomusic/actions/runs/42671525588) and an incidental Phase2 rerun [42671525464](https://github.com/manufact-test/nomusic/actions/runs/42671525464) reported workflow-level failure **without any job records** (GitHub API `total_count:0`); root cause undetermined, do not attribute to code. Previously verified 5/5 structural PASS [42670648029](https://github.com/manufact-test/nomusic/actions/runs/42670648029) still stands at the exact tested commit.
- One bounded, technically different original ARM emulator retry uses `-accel off` (QEMU software emulation) in the isolated original-host workflow: [run 42672246229](https://github.com/manufact-test/nomusic/actions/runs/42672246229). Queued at handoff; no PASS claim. If this fails, treat hosted ARM runtime as unavailable and stop re-running it; do not ask owner to delete Yandex/disable Play Protect.
- **Hard boundary:** No Android PackageManager original+clone coexistence runtime PASS; no normal Passport login, read-only hook in authentic Yandex, native decoder/MediaSource, real source swap, acoustic RASKOL/«Дым» or Play Protect verdict. Next genuine test requires working authorized disposable ARM device/runtime, not a repeat of synthetic own-player smoke.
- IMPORTANT: current read-only `HookSpec.TARGET_PACKAGE = "ru.yandex.music"` is version-pinned to official package. It will **not** hook the separate clone package without a separately audited clone-specific observer binding; never assert it is installed/working.
