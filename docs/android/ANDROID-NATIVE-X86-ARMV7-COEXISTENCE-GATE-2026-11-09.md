# Android native Yandex — exact ARMv7 translated package-manager gate

[Native ABI audit SUCCESS 42679412679](https://github.com/manufact-test/nomusic/actions/runs/42679412679):
Publisher-signed #170gpr uses exactly 3 original `armeabi-v7a`
native .so libraries in `config.armeabi_v7a`, and **no arm64-v8a**.
This explains [CI 42678755544](https://github.com/manufact-test/nomusic/actions/runs/42678755544),
API35 x86_64 translated emulator: booted but *original signed Yandex*
failed first install with `INSTALL_FAILED_NO_MATCHING_ABIS`.
Nothing was learned about clone install there.

**One ABI-justified alternative**: Linux/KVM `api-level: 30`,
`target: google_apis`, `arch: x86`, where built-in native bridge may
translate `armeabi-v7a`. Code checks live emulator `abilist` explicitly
contains both x86 and armeabi-v7a plus nonempty native bridge;
otherwise returns clear no-go before install. No third-party ARM
translation packages are installed or Play Protect bypass attempted.

If ABI bridge is present, install original publisher-signed five splits first,
then five independent throwaway re-signed `pro.celikom.yandex.nativeclonelab`
splits, query PackageManager's 5+5 paths and attempt normal clone launcher.
No account, audio, LSPatch, password, token or persistent vendor APK artifacts.
Android 11 x86 native translation is NOT Android 13 ARM compatibility or
proof of audio, authorization, decoder, Pause/Seek/Next or Play Protect.

Do NOT install on owner HONOR; accepted Test.50 and original remain untouched.
This is bounded ONE emulator experiment, not an endorsement of further
repeated x86/LSPatch tests (earlier x86 LSPatch already known NO-GO).
