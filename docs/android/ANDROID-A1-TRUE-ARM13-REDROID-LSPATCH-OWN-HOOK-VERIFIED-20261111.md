> **ARM Android13 publisher control verified 11.11.2026:** [CI 42990078186](https://github.com/manufact-test/nomusic/actions/runs/42990078186) signed original 5 APK MAIN alive and resumed. No sign-in, audio, Google Play Services, or Play Protect in Redroid. A/B clone research 42990746852 is running and is not yet proof of a working independent native Yandex client. Read [original control](ANDROID-A1-TRUE-ARM13-SIGNED-YANDEX-ORIGINAL-CONTROL-20261111.md).

# CELIKOM Android A1 — настоящий ARM Android 13 / ARMv7 LSPatch LibXposed hook подтверждён (11.11.2026)

**ГЛАВНЫЙ РЕЗУЛЬТАТ:** впервые есть реальный Android 13 в Linux/ARM64 контейнере с нативной поддержкой armeabi-v7a, в котором установлен и запущен **только наш** тестовый ARMv7 APK с LSPatch v1.2-487, `sigBypassLevel=0` и нашим LibXposed-модулем. Фактически исполнен перехват `MainActivity.onCreate` **внутри процесса**; фиксированная метка `OWN_NATIVE_ARMV7_LSPATCH_MODULE_ENTERED`. Никакой установленной Яндекс.Музыки и звукового теста.

## Ground truth / actual GitHub Actions

- [CI **42987483624** — оба job SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42987483624); source commit `1390990fe3086c5690a8f0b2c33e5cc5dc2b00b9`.
  - Build job: Android JNI host `pro.celikom.armv7loaderhost.witness` (ELF `EM_ARM`), own read-only LibXposed module scoped to CELIKOM-owned test package IDs, pinned LSPatch with no signature bypass. Signed laboratory APK `OWN_ARMV7_NORMALIZED_SIGNED_STATIC_PASS`; correct four signed embedded ELF layouts, unchanged own JNI and module bytes. A one-day **OWN-ONLY** internal CI artifact transfers the APK to ARM runner, no Yandex binary in artifacts.
  - Native ARM job on `ubuntu-24.04-arm`: load binder_linux, mount binderfs, start pinned official Redroid `redroid/redroid@sha256:41e5f0c1ff27a4a474c474e5595168cedf6c40fc5dd102c5617f48c80f511e9e`, verify `NATIVE_ARM_ANDROID_13_CONTAINER_BOOTED` (`sdk33=true`, `native64=true`, `native32=true`, `ready_for_armv7_lspatch=true`). Android guest ARM64 and 32-bit ARMv7 userspace run natively on ARM Linux kernel: **not** x86-to-ARM NativeBridge and not merely ARM64 Linux JVM.
  - Install **one own APK** and open OWN Activity. Actual result: `OWN_NATIVE_ARMV7_LSPATCH_MODULE_ENTERED`, `native_armv7_guest=true`, `main_alive=true`, `activity_resumed=true`, `oncreate_intercepted=true`, `signature_bypass=0`, `module_count=1`. No user credentials, music, or third-party APK; Play Protect not tested. Runtime and cleanup completed successfully, both jobs GREEN.
- Earlier [CI **42986774384**](https://github.com/manufact-test/nomusic/actions/runs/42986774384) first proved ARM Android 13 boot but final cleanup failed on root-owned Docker data; updated cleanup uses `sudo rm -rf` only for the dedicated runner temp directory. Its historical overall FAILURE was **cleanup only**, Android boot PASS.
- [CI **42986533457**](https://github.com/manufact-test/nomusic/actions/runs/42986533457): both ARM64 Ubuntu 24.04/26.04 runners load Binder and successfully mount binderfs.
- [CI **42985834348**](https://github.com/manufact-test/nomusic/actions/runs/42985834348): separately proved own in-process onCreate hook on native x86 API30; x86 witness isn't a substitute for this ARM pass.
- [CI **42985409076**](https://github.com/manufact-test/nomusic/actions/runs/42985409076): macOS native ARM Android emulator still fails `HVF error: HV_UNSUPPORTED` despite software TCG opt-in; stop macOS emulator attempts.

## What is proven and NOT proven

**PROVEN:** pinned upstream LSPatch level0 can load our 32-bit ARM JNI host and invoke our own LibXposed hook on genuine ARM Android13. The previous x86 emulator bridge `SIGSEGV` is NOT a universal ARMv7 LSPatch failure (confirmed independently by this real ARM runtime). Own-only main lifecycle and onCreate marker witnessed.

**NOT PROVEN:** native Yandex clone MAIN/UI, Yandex login/Passport, MyWave, exact selected decoder, alternative audio, Pause/Seek/Next, Play Protect on actual HONOR. Redroid lacks user Play Protect, Google Play certification; it is a **privileged, disposable Linux container test stand**, not a model of a stock phone. Do not compare passing OWN activity resumed to vendor native UI/window focus and do not distribute OWN test APK as CELIKOM.

**Separate outstanding blocker:** previous non-LSPatch independent Yandex clone crashed/exited `EXIT_SELF(0)` without original too. ARM LSPatch health does not change the host app's package-identity/signature trust semantics. Need strictly zero-bypass test of one-APK clone in true ARM Android and classify startup without logging secrets. Cannot 'solve' publisher signature checks by spoofing, sigbypass1/2 or accessing OAuth/DRM.

## Safe engineering continuation

1. Freeze this own native ARM green source/CI and updated handoff. Preserve Test.50 and Windows/W61 accepted exactly.
2. Next experiment: **separately signed independent clone MAIN/UI gate** on true native ARM Android13. Original 5 publisher-signed splits must remain untouched (if used as control); proprietary APK downloaded to ephemeral isolated workspace and never retained in Git/artifacts. Same `sigBypassLevel=0`; do not extrapolate from own module pass. First install/MAIN, then independent 5+1 coexistence; stop at vendor publisher/auth hard block.
3. Only if real native Yandex MAIN/UI and safe login succeed, observe own read-only module in process → selected current source and decoder → licensed alternative within same decoder → acoustic owner acceptance.
4. **Stage B reminder** AFTER owner audibly accepts exact archived Stage A: independently implemented replacement for LSPatch. Not due now.

## Source & rollback

- Experiment branch `experiment/android-native-a1-lspatch-clone-loader0-20261111`, exact verified code `1390990fe3086c5690a8f0b2c33e5cc5dc2b00b9`.
- Frozen `backup/android-a1-real-arm13-armv7-own-lspatch-hook-green-20261111` @ same SHA.
- Earlier Redroid boot-only backup `backup/android-a1-redroid-native-arm13-armv7-userspace-boot-20261111` @ `2557c06ac8a49f8e2bff38b3b0445271ea3a14a6`.
- OWN runtime source: `android/native-yandex-hooklab/ci/native_arm_redroid_boot_only.sh`, `android/native-yandex-hooklab/ci/native_arm_redroid_own_witness.sh`, `android/native-yandex-hooklab/finalize_owned_armv7_native_lab.py`.
- Workflow: `.github/workflows/android-native-a1-redroid-armv7-own-lspatch-witness.yml`.
- Owner HONOR 50, installed stock Yandex, Test.50, Windows, extension, production/backend unchanged.
