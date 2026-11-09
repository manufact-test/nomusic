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
