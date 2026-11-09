# Android native Yandex — x86_64 API35 ARM translation coexistence gate (09.11.2026)

Prior Mac ARM emulator runs 42669152016 / 42672246229 FAILED before any APK
installation: QEMU HVF_UNSUPPORTED on GitHub-hosted macOS. Do not repeat.

Distinct bounded experiment (NO rootless LSPatch or audio hook):
- Ubuntu-latest with KVM and Android 15 (API35) Google APIs x86_64 emulator
  which may support ARM64 binary translation via a native bridge.
- Before installing any APK, assert `ro.product.cpu.abilist` contains both
  `x86_64` and `arm64-v8a`, and a native bridge is configured.
  Otherwise emit a clear NO-GO rather than attempt an unsupported ABI.
- Fetch and verify 5 exact publisher-signed original #170gpr splits, produce
  5 ephemeral nonconflicting clone split APKs with already static-PASS
  package/provider transformations. Attempt original+clone side-by-side
  Android PackageManager install (5+5) and clone process launch.
- No login, media, hook, second player, DRM or certificate spoofing,
  token/header collection, protected-content access, phone changes or
  distribution of vendor APK artifacts.
- Even a PASS verifies only install/initial process launch on translated
  **Android 15, NOT HONOR Android 13**. Dynamic Yandex account, Play Protect
  reputation, audio decoder/trackId association and real replacements
  remain untested and cannot be inferred from translation.

Independent benchmark inspiration: community reports suggest API35 x86_64
images have ARM translation, but not guaranteed for our exact CI image.
The workflow MUST confirm native bridge from the running virtual device;
if missing, this path is NO-GO and must not be silently worked around.

Workflow: `.github/workflows/android-native-x64-arm-translation-coexistence.yml`
Uses existing narrow Phase2 clone script's opt-in
`CELIKOM_CLEAN_ANDROID_TRANSLATION=1` mode.
