# CELIKOM Android — owned ARMv7 loader-only APK

Testing LSPatch's loader on the owner's ARMv7-capable HONOR **without
uninstalling or modifying official Yandex** requires a separate Android
package with no relationship to the proprietary music client.

Source-only owned host: android/native-yandex-hooklab/armv7-loader-host/
Separate package: pro.celikom.armv7loaderhost.
Native .so: 32-bit armeabi-v7a, our own JNI_OnLoad only.
No app permissions, audio, Yandex, accounts, files, tokens, networking.
Build-patcher script: android/native-yandex-hooklab/build_owned_loader_host.py.
CI: .github/workflows/android-native-armv7-owned-host.yml.

JingMatrix LSPatch v1.2-487 has pinned JAR SHA256 and explicit sigbypass=0;
ZERO CELIKOM modules are embedded. Current result is **static packaging only**.
The self-owned tiny APK can be kept in an internal artifact, unlike proprietary
repackaged Yandex binaries. Ensure GPLv3 notice/obligations for LSPatch when
sharing outside this internal lab. The lab cert is ephemeral and updates
may require removing only this *own* separate package. No Yandex uninstall.

If tester installs it with Google Play Protect ON, a displayed Activity
shows that the 32-bit host + loader survived, but says NOTHING about
FileInfoDto, signed alternate audio, audible native Yandex playback,
or Play Protect acceptance unless independently confirmed.

Stop if Android/Play Protect blocks install. No bypass, signature spoofing,
root, downgrade or main HONOR Yandex changes. Owner permission to install
this independent app is a distinct step; we have not installed it.

## CI accepted, owner runtime STILL not verified

- **CI SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/42638725850
- **Exact source commit:** a54af5fbd51cee4fa71b0afda023c351fd6fcdbf
- **Internal artifact:** https://github.com/manufact-test/nomusic/actions/runs/42638725850/artifacts/13683314600
- Artifact contains a ZIP with own-source `CELIKOM-ARMv7-LOADER-ONLY-Test.apk`. No original/modified Yandex.
- Artifact archive size ~2.03 MB, SHA-256 archive digest `fac3d09fbd8af7c47ce0ca016ebbc780eb5a830bca72a0d69748a53c35677027` (NOT necessarily the inner APK hash).
- Package: `pro.celikom.armv7loaderhost`. Native: only `armeabi-v7a`; checks confirmed ELF32 ARM, same package ID after patch, separate lab signature, no permissions, sigbypass=0, zero embedded modules.
- **Real ARM runtime, Play Protect acceptance, CELIKOM observer and Yandex audio are all unverified.** CI validates static packaging only. Owner HONOR, official Yandex/music and Test.50 unchanged.
- Test is optional and can be delayed; after owner consent, keep Play Protect ON, install **only this standalone APK**, open app `CELIKOM ARM Loader Lab` and report whether screen appears or app exits. If Play Protect blocks, STOP, do not override. No replacement/deletion of Yandex; on uninstall delete only standalone test app.
- The APK is re-signed by an ephemeral lab key and cannot be upgraded by another CI with a new key; test-only. Artifact retention is seven days. It contains upstream LSPatch; verify redistribution obligations before sharing beyond the internal developer/owner test.
