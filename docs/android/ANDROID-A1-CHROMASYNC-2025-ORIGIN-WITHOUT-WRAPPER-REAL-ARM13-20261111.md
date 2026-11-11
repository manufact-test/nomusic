# CELIKOM Android A1 — exact ChromaSync 2025 host WITHOUT wrapper: native ARM13 lifecycle contrast

**Date:** 2026-11-11. **Research result: reproducible Java MAIN crash without ChromaSync's outer LSPatch/module runtime.** This is not evidence that bypassing a security check is safe, necessary, allowed or sufficient. CELIKOM Stage A remains **NO-GO**.

## Source provenance and controls

- Owner-uploaded exact original `ChromaSync-Clone-3.0.1.apk`, 102,572,843 bytes, outer SHA256 `4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`. Stored only in an **UNPUBLISHED GitHub Release draft**; no binary committed, published or attached to Actions.
- Extracted **byte-identical** `assets/lspatch/origin.apk` only to disposable CI, without rewriting or re-signing: 59,511,238 bytes; SHA256 `d54e58c6b7720a2d161758f41ce8d3c08d7d5cc6e9587b3976383ee2f829905b`. Actual nested ZIP contains six DEX, manifest, native libraries, and **no outer LSPatch config/loader asset**. It retains the independent competitor signature/package identity from the supplied archive, **not the official Yandex publisher signature**. We **did not** independently prove the embedded vendor code's original provenance or unchanged bytecode, so do not call this a publisher-signed clean 2025 Yandex original.
- In both modes, exact test app package is `app.chromasync.yamclone`; user account, audio, MyWave, Play Protect and owner HONOR 50 are not involved. No new signature/Passport/DRM bypass was applied.

## True Android13 live A/B, not mocked

| Real ARM13 setup | Installation | MAIN launcher | Lifecycle | Strict PASS? |
| --- | --- | --- | --- | --- |
| **Complete exact ChromaSync 3.0.1 outer APK** | INSTALLED | ACCEPTED | Same MAIN PID resumed 16/16 seconds | **YES — native lifecycle only** |
| **Exact nested `origin.apk` alone; no outer wrapper/module/loader** | INSTALLED | ACCEPTED | Same MAIN PID **not** preserved; initially alive/resumed 12 snapshots, then dies/restarts | **NO** |

- Full competitor including stock-first 2026 original: [CI #43072904573](https://github.com/manufact-test/nomusic/actions/runs/43072904573), strict Android ARM13 **SUCCESS** for both.
- Standalone nested first run [CI #43078292795](https://github.com/manufact-test/nomusic/actions/runs/43078292795): package `INSTALLED`, `MAIN_LAUNCH_ACCEPTED`, first 12/16 samples MAIN alive+resumed, initial MAIN PID then disappears or changes; verdict `UNWRAPPED_2025_HOST_MAIN_NOT_SUSTAINED` (intentional CI failure).
- Independent nested second run [CI #43078765202](https://github.com/manufact-test/nomusic/actions/runs/43078765202): original process restart reproduced; Android exact MAIN `ApplicationExitInfo.reason=4` (**Java crash**), `am_crash_main=true`, `am_proc_died_main=true`, `am_proc_start_main=true`, `exit_self=false`, no native crash signal seen; strict native lifecycle **FAILURE** by design.
- Independent nested third run [CI #43079253843](https://github.com/manufact-test/nomusic/actions/runs/43079253843): same 12/16 initial live samples then MAIN dies/restarts, Java crash reason 4, real crash buffer PID-scoped `fatal_category=APPLICATION_STATE`. No native `dlopen`, missing `.so`, class-resolution, resource, DEX verification, appComponentFactory or Activity launch failure was detected in the bounded classifier. **APPLICATION_STATE** aggregates exception categories including IllegalStateException, NullPointerException and IllegalArgumentException; do not infer which specific exception or security policy caused it. 5 structural unit tests + exact observer tests PASS.

### Additional native UI findings

- [CI #43077478927](https://github.com/manufact-test/nomusic/actions/runs/43077478927) for **complete competitor**: `global_focus_clone=true`, `clone_window_record_present=true`, real native screenshot 720×1280 available, MAIN stable 16 seconds; this is stronger than mere process presence.
- `uiautomator dump` returned exit code 0 but did **not** produce a readable XML file at either guest path in that Redroid environment. No actual tree/pixel-content/Passport login/audio proof. A Java GUI window and OS focus are proven, but full Yandex UI interaction is NOT.
- Prior `dumpsys window windows` lacked the focus fields, but **`dumpsys window`** (without the subcommand) proved clone OS focus. This fixes a diagnostics false negative; it was not a vendor-side change.

## What it means and does not mean

1. This exact third-party package's **standalone 2025 nested host** can install and initially start but does NOT pass the lifecycle gate when the outer wrapper/module/loader is removed. Thus the idea that simply selecting Yandex 2025 will certainly fix our independent 2026 CELIKOM exit is contradicted by a live test.
2. **The older host has a JAVA APPLICATION_STATE crash**, different from the already-confirmed independent CELIKOM 2026 `IllegalStateException` followed by `Lxx0.run(mode2)` and `EXIT_SELF(0)`. These are different observed exit mechanisms; they may have related initialization prerequisites, but causation is not proven.
3. Stable full competitor vs unstable naked nested origin differs by **the entire outer LSPatch loader, injected ChromaSync module, app factory/lifecycle integration and signature compatibility configuration**. This A/B does NOT isolate which individual difference prevents Java crash. Do not claim `sigBypassLevel=2` alone fixes anything. CELIKOM remains at approved `sigBypassLevel=0` and must never silently copy signature, publisher identity, rights or protected auth/DRM bypass.
4. The tested nested `origin.apk` is still a **competitor-modified/resigned archive**, NOT independently verified 2025 RuStore issuer-signed input. A clean original signed 2025.10.4 #120.1rur would be a distinct control, requiring a trustworthy source and verified publisher certificate before using it. 4PDA historical post identifies that release with build 24025542 and a published MD5, but the exact full original APK and signature are **not** independently available in the current connected tools.
5. None of these checks prove user-level native Yandex UI fidelity, Spotify/MyWave behavior, acoustic source swap, pause/seek, Play Protect or distributable CELIKOM. The product has NOT passed.

## Exact code, checks and preservation

- Scoped experiment: `experiment/android-a1-chromasync-origin-without-wrapper-20261111` (latest read-only origin/unwrapped & crash-observer code); source tested in [CI #43079253843](https://github.com/manufact-test/nomusic/actions/runs/43079253843) @ `0d11d896568dd9583bd7be8e8f9e13112a889a3c`.
- Frozen backup: `backup/android-a1-unwrapped-2025-appstate-crash-20261111` @ `0d11d896568dd9583bd7be8e8f9e13112a889a3c`. Precrash analysis backup `backup/android-a1-unwrapped-2025-main-restarts-20261111`.
- Full competitor positive backup: `backup/android-a1-chromasync-exact-live-arm13-both-pass-20261111` @ `6a6786ec34e7a9580b39dac56f226e44a256f5f4`.
- Focus diagnostic backup: `backup/android-a1-chromasync-focus-os-confirmed-20261111` @ `23b9e2e6b8ecb7a986524e44b3afdc848c1cdf93`.
- **Approved A1 MAIN remains unchanged** `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`. Test.50, Windows, extension, backend, original owner's Yandex/HONOR/production untouched.

## Next practical checkpoint

1. Avoid repackaging the **same 2026 zero-bypass host** or repeating generic hooks; three prior A/B paths already reproduce its signed-origin Java exception and normal self-exit. We now have a stable positive reference but no permitted shortcut to copy its trust bypass.
2. When a legitimate publisher-signed 2025 original APK becomes verifiable, test it unchanged as a control and compare version-specific lifecycle to publisher-signed 2026 original. A **2025 independently signed clone** would separately require approved rights and no security bypass; do not assume version alone resolves identity trust.
3. For the already approved CELIKOM A1 architecture, any vendor signature/auth trust dependency needs publisher authorization or another explicitly approved lawful integration; do not silently replace the product with a WebView, secondary player, patched official install or switching UX.
