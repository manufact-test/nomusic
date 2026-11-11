> **ARM NativeBridge limitation is bypassed by testing on proper ARM Android13, not patched:** [CI 42987483624](https://github.com/manufact-test/nomusic/actions/runs/42987483624) proves original upstream LSPatch works with OWN ARMv7 Android13 and onCreate hook, no signature bypass. This supersedes any assumption that ARMv7 loader universally crashes. Report: [true ARM13 test](ANDROID-A1-TRUE-ARM13-REDROID-LSPATCH-OWN-HOOK-VERIFIED-20261111.md). Native Yandex clone MAIN/UI and audio still NO-GO.

# CELIKOM Android A1 — decisive vendor-free differential: ARMv7 NativeBridge fails, native x86 LSPatch runs (11.11.2026)

**VERDICT:** LSPatch v1.2-487 with `sigBypassLevel=0` demonstrably boots in a permissionless **OWN native x86 application** on our pinned Android 11 x86 emulator. The **same pinned upstream LSPatch** fails with `SIGSEGV` when the same emulator must translate an **OWN ARMv7 application** through NativeBridge, even after we correct the proven `EM_386` vs `EM_ARM` library-selection mismatch. This isolates the current emulator blocker from Yandex code. **No Yandex clone native UI, login or audio replacement has been achieved.**

## Test matrix (both are *actual* disposable Android 11 API30 google_apis x86 emulators)

| Variant (no Yandex installed) | Baseline | LSPatch 0, zero modules | Observed native failure |
| --- | --- | --- | --- |
| OWN ARMv7 `pro.celikom.armv7loaderhost` with existing native `libcelikom_host_probe.so` | MAIN alive, Activity resumed; `window_focused=false` in scoped snapshot | Corrected ARMv7 `liblspatch.so` in the x86-named resource (CI-only mirror) fails | `SIGSEGV`, first debuggerd frame group LIBART; NativeBridge within first 12 groups |
| OWN native x86 `pro.celikom.armv7loaderhost.x86control`, JNI compiled for EM_386 | MAIN alive, Activity resumed; `window_focused=false` in scoped snapshot | MAIN alive, Activity resumed; `window_focused=false`; **no ARM resource mirror** | No `dlopen`, no SIGSEGV in scoped crash buffer |

**Exact CI evidence:**
- [OWN ARMv7 bridge control #42982872899, SUCCESS as *diagnostic*](https://github.com/manufact-test/nomusic/actions/runs/42982872899), code `08c033e6ed4d53a8d5ca4bbd12faf2a67cdd9f52`: baseline `main_alive=true, activity_resumed=true`; mirrored LSPatch `main_alive=false, native_signal=SIGSEGV, native_first_frame_group=LIBART, native_bridge_in_first_12_frames=true`. `sigbypass=0`, modules=0, Yandex APK not installed/executed. The workflow SUCCESS means its comparative test completed, **not** that LSPatch on ARMv7 works.
- [OWN x86 native control #42983717005, SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42983717005), code `d305f32dabb4e4209d2fa3fbf51bd55edec09db4`: baseline and LSPatch `main_alive=true, activity_resumed=true`; `native_signal=NOT_OBSERVED`, `dlopen_seen=false`. Correct x86 `EM_386` loader was signed, stored/page-aligned, no mirror, module=0, `sigbypass=0`; no original Yandex present.
- [Vendor clone ARM bridge after mirror #42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329): same first LIBART + deeper NativeBridge SIGSEGV, original 5 publisher-signed split packages can coexist at installation, but clone UI still FAIL. This is consistent with the new OWN-only control without implying the exact faulting instruction is known.

## Root-cause limits

The evidence supports **an incompatibility in this emulator's LSPatch+NativeBridge execution path**. It does **not** isolate a precise ART/bridge defect or prove a defect on a physical ARM CPU. We deliberately do not change the original Yandex APK, user signature, Passport, DRM, Play Protect settings, or original account.

The direct unwrapped independent Yandex clone's earlier `EXIT_SELF(0)` is a **separate, unresolved** vendor-startup problem; even if LSPatch runs on physical ARM, genuine Yandex UI may still not boot under a different independent package/signature. Don't claim 5+1 install proves runtime.

These tests never verify user-facing native UI window focus (all OWN snapshots showed `window_focused=false`), Yandex login, MyWave, current track identity, selected active decoder, server entitlement, trial or audible replacement. The x86 OWN control's resumed Activity is intentionally **not** counted as native Yandex MAIN/UI pass.

## Next engineering gate — do not waste more x86 ARMv7-translator cycles

1. Establish a **true native ARM Android runtime** with a compatible 32-bit ARMv7 ABI and safely controlled installation (or approved cloud ARM test). Linux ARM64 JVM is not Android; x86-to-ARM NativeBridge is not native ARM. No second personal phone is required or requested.
2. Validate pinned upstream LSPatch **zero bypass** on the permissionless OWN host **before** touching the separately cloned Yandex APK. An actual native ARM in-process boot is required; passing class/ZIP/unit tests isn't enough.
3. Only after native OWN succeeds, attempt the independent clone MAIN/Activity/window with original Yandex untouched and Play Protect on. If original host checks publisher identity and exits, do **not** turn on signature spoof, sigBypass 1/2, Passport/DRM bypass, or distribute a broken experiment. Mark product architecture blocked pending permitted integration path.
4. After clone UI works without account-data exposure, own read-only hook → exact current source/decoder witness → licensed single-player source replacement → audible pause/seek/Next/MyWave owner acceptance. Never call this A1 success before those gates.
5. Once **audible Stage A has been accepted by owner and exact source APK/hash/rollback frozen**, proactively remind about Stage B: replacing LSPatch with an independently written injection mechanism. Not due now.

## Safety and backup

- No Yandex binaries, login data, audio or phone have been accessed by these OWN-only differential tests. All compiled OWN APKs, temporary signing keys and pinned LSPatch jar remain isolated in GitHub ephemeral CI and are deleted.
- Experimental branch: `experiment/android-native-a1-lspatch-clone-loader0-20261111`.
- Exact rollback before own controls: `backup/android-a1-before-own-armv7-bridge-control-20261111` @ `5cc3bc3cef16d938c33339e851d91100e89774e2`.
- First OWN ARMv7 result: `backup/android-a1-owned-armv7-vendor-free-sigsegv-reproduced-20261111` @ `08c033e6ed4d53a8d5ca4bbd12faf2a67cdd9f52`.
- **Both controls final exact code backup:** `backup/android-a1-owned-armbridge-fails-native-x86-pass-20261111` @ `d305f32dabb4e4209d2fa3fbf51bd55edec09db4`.
- Test.50, Windows, extension, production/backend, master TZ, user's one HONOR 50 and official installed Yandex are unchanged.
