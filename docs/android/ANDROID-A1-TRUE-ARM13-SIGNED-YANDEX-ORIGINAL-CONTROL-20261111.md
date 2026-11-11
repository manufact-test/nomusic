# CELIKOM Android A1 — publisher-signed original Yandex 5 splits BOOT on genuine ARM Android13 (11.11.2026)

**VALIDATED:** the unmodified **Yandex.Music 2026.10.3 #170gpr** publisher-signed five-split package installs and launches its MAIN Activity on native ARM Android13 Redroid with ARMv7 32-bit userspace. This is the first genuinely useful baseline for testing a separate native clone, alongside our already-confirmed own in-process ARM LSPatch hook.

## Evidence

- [Actual CI **42990078186 — SUCCESS**](https://github.com/manufact-test/nomusic/actions/runs/42990078186), source `06f2d237059c014c12548f85c5d67acf24e8ee00`: exact XAPK SHA, 5 split APKs, original publisher certificate, package/version code `24026531`, no modifications; real Android13 `sdk33=true` ARM64+ARMv7 guest. Installation uses **standard Android PackageInstaller multi-file session** `pm install-create/install-write/install-commit` with 5 intact original signed inputs; installed split count=5, MAIN process alive, Activity resumed, launch intent accepted.
- Fixed verdict: `ORIGINAL_SIGNED_NATIVE_ARM13_MAIN_ALIVE`; `window_focused=false` (headless container, focus not proved), `google_play_services_present=false`, `login_tested=false`, `audio_tested=false`, `play_protect_tested=false`, `clone_tested=false`.
- [CI 42987483624 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42987483624) separately proved an OWN ARMv7 test app with pinned upstream LSPatch `sigBypassLevel=0` and one LibXposed read-only module, real in-process `onCreate` callback.
- [PM capability CI 42989852792](https://github.com/manufact-test/nomusic/actions/runs/42989852792): official ADB host command `install-multiple` is **NOT** a guest Android shell `pm` command, while `pm install-create`, `install-write`, `install-commit`, `install-abandon` are available. Previous failures 42988755588–42989852792 were **test-harness misuse** and MUST NOT be reported as Yandex compatibility failures. The correction is only normal PackageInstaller use, not a security bypass.

## Safety and interpretation

- Original signature is the publisher's, verified for *every* split before the guest installation. Nothing in the original APK or runtime source is rewritten.
- All public vendor binaries are confined to ephemeral runner storage and guest Docker `/data`; none uploaded to GitHub artifacts, Library, releases, or user device.
- No Yandex account, Passport, DRM, entitlement, licensed track, sound or playback tested. The Redroid environment lacks Google Play Services and Play Protect, and is NOT equivalent to the physical HONOR 50.
- Neither a live MAIN Activity nor a working OWN test module separately proves a functioning **independent** clone, account login, Play Protect clearance, exact audio decoder or audible music swap.
- Window focus was not observed even for the untouched signed original, so the clone's future `window_focused=false` must be compared against this control, not mislabeled as the sole crash cause.

## Next strict gate — actual independent clone

[CI **42990746852**](https://github.com/manufact-test/nomusic/actions/runs/42990746852) now examines **one independent lab-signed `pro.celikom.yandex.nativeclonelab` APK** with `sigBypassLevel=0`, no LibXposed modules, original DEX preserved, and side-by-side installation next to the untouched five signed originals on **the same native ARM Android13**. It must report independent clone MAIN liveness/Activity, original MAIN control, clone background survival, and fixed-category crash markers. It is a **GO/NO-GO experiment**, not a downloadable Android app, and any hard publisher signature/session/permission enforcement remains respected.

**Stop conditions:** no Play Protect bypass, no issuer signature spoofing, no Passport credentials or DRM extraction, no automatic user-device installation, no artifact upload. Do not call the architecture finished until user acoustically accepts Stage A with single original decoder. Stage B independent patch later, after acceptance.

## Source checkpoints

- Experimental source after session correction `06f2d237059c014c12548f85c5d67acf24e8ee00`. Frozen checkpoint `backup/android-a1-true-arm13-signed-yandex-original-and-owned-hook-green-20261111`.
- True ARM clone research scripts (experimental only):
  - `android/native-yandex-hooklab/clone_native_arm13_redroid_gate.py`;
  - `android/native-yandex-hooklab/clone_native_identity_phase2_ephemeral.py`;
  - `.github/workflows/android-native-a1-arm13-clone-main-ab.yml`.
- Current clone research source `4e15a8d616d4acb1e86bbd8e5c723a2e9ba8a23a` (CI status MUST be checked before changing claim).
- Original publisher, Test.50, accepted Windows, browser extension, backend/production and owner's ONE HONOR remain untouched.
