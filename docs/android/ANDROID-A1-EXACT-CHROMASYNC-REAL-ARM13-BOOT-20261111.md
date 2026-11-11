# CELIKOM Android A1 — first real ARM13 run of EXACT owner-uploaded ChromaSync 3.0.1

Date: 2026-11-11. **Real observed result: native MAIN lifecycle PASS alone and alongside original**. This is **not** an audio/UI/login acceptance or CELIKOM product unlock.

## Source provenance / private handling

- Owner-provided unmodified `ChromaSync-Clone-3.0.1.apk`, exactly **102,572,843 bytes**, SHA256 `4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`.
- Uploaded by owner as an **UNPUBLISHED draft** asset (`draft=true`, tag `a1-chromasync-301-unpublished-test`) in public `manufact-test/nomusic`. This is not a public Release or Git blob. User was repeatedly told **not** to press Publish. Public Actions may run at no private-minutes charge. Credentials and APK bytes were not written to job logs, Git, or uploaded artifacts. Actual asset read using scoped GitHub token + SHA pin.
- Approved main Android A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`, Test.50, Windows, extension, backend, production and owner's HONOR 50 untouched.

## Actual CI experiments, strictly distinguish harness faults

### Run #1 — 43072068606 (TRUE guest, but harness mistakes)

[CI 43072068606](https://github.com/manufact-test/nomusic/actions/runs/43072068606) verified exact APK download/size/hash and real ARM64+ARMv7 Android13 Redroid boot. `mode=alone`: `clone_install=INSTALLED`, `MAIN_LAUNCH_REJECTED` from an *ambiguous blind implicit* `am start ... -p package` command; no live MAIN evidence. `mode=stock-first`: `stock_install=INSTALL_FAILED_OTHER` from INVALID TEST HARNESS calling `pm install-multiple` inside Android shell, where that command is **not valid** (it belongs to host ADB). Neither rejection proves an APK runtime defect.

Fix used our already-proven `native_arm13_signed_original_control.pm_session_install` native PackageManager `install-create/write/commit` for exact five publisher-signed APKs. For exact competitor, resolve launcher Activity via Android `cmd package resolve-activity` and explicitly `am start -n`, without altering vendor code/security.

### Run #2 — 43072904573 (FIRST TRUE POSITIVE native competitor boot)

[CI 43072904573](https://github.com/manufact-test/nomusic/actions/runs/43072904573) **BOTH native guest workflows PASS; strict runtime lifecycle gate PASS**.

- Host environment: genuine Ubuntu ARM64 CI Redroid Android **13 (SDK 33)**, native `arm64-v8a` and `armeabi-v7a`, original clean ephemeral data each test, no real user account or owner phone.
- `mode=alone`: SHA256 PASS, `clone_install=INSTALLED`, `launch=MAIN_LAUNCH_ACCEPTED`, `main_survives=true`, `stable_main_pid=true`, `activity_resumed_all_samples=true`, `verdict=NATIVE_MAIN_SAME_PID_RESUMED_16S`. **16 consecutive one-second snapshots** saw same MAIN PID alive and ChromaSync Activity resumed.
- `mode=stock-first`: pinned official issuer-signed Yandex **2026.10.3 #170gpr**, five splits passed prior signer and archive checks, `stock_install=INSTALLED`; then same original ChromaSync APK `clone_install=INSTALLED`, `launch=MAIN_LAUNCH_ACCEPTED`, `main_survives=true`, `stable_main_pid=true`, `activity_resumed_all_samples=true`, `verdict=NATIVE_MAIN_SAME_PID_RESUMED_16S` across 16/16 fresh samples.
- Product gate is still **Stage A NO-GO**: this test establishes short, genuine native MAIN Activity lifecycle and **real package coexistence** in this emulator configuration only. NO acoustic playback, native interface pixels/rendering, user auth, MyWave, Play Protect, longer run, original Yandex foreground after competitor launch, or independent CELIKOM hook source swap has been demonstrated.
- Static prediction of `com.yandex.preinstallsatellite.appmetrica.provider` collision did **not manifest in the tested original 2026 signed-stock + exact competitor pair**. Do not overgeneralize to every Yandex version/device.
- Competitor actual wrapper has **2025.10.4 #120.1rur** host + embedded private module + `sigBypassLevel=2`. CELIKOM research host uses **2026.10.3 #170gpr**, independent signer, `sigBypassLevel=0`, no private competitor module. Do NOT infer `sigBypassLevel=2` is the sole causal fix; host age and own module are confounded. Do NOT copy level-2 bypass/signature spoof/DRM or vendor auth code.
- CELIKOM independent 2026 clone previously had signature-related `IllegalStateException`, mode-2 `Lxx0.run` and exact `EXIT_SELF(0)` on fresh MAIN PIDs. The root cause of CELIKOM's publisher-trust rejection is still not solved by successful competitor boot.

## Frozen work

- Exact code run #2: `experiment/android-a1-public-draft-arm13-20261111` @ `6a6786ec34e7a9580b39dac56f226e44a256f5f4`.
- Immutable checkpoint branch: `backup/android-a1-chromasync-exact-live-arm13-both-pass-20261111` at that SHA.
- Pre-first-live backup: `backup/android-a1-chromasync-first-live-boot-failed-20261111` @ `7958c81c835b370689d87822562f9a02017e51b3`.

## Narrow next research

1. Add a bounded **native window focus/optional UI hierarchy witness** without logging screen content or recording user accounts. Avoid mislabeling MAIN resumed alone as fully rendered native UI.
2. In another bounded, non-bypass experiment, compare exact host-version-dependent startup and OS package permissions between signed 2025 official host and signed 2026 host; keep same source and no foreign module. If a no-bypass independently signed 2025 clone launches, host-version-dependent failure is supported. If not, only the combined competitor setup is known to work and signature-layer differences remain confounded.
3. Keep CELIKOM A1 product constraints unchanged: native Yandex player full functionality, one installed CELIKOM APK alongside stock Yandex, original single decoder with conditional source change; never own player/WebView/silently use competitor bypass. Authorization/commercial redistribution concerns still apply separately.
