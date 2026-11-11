# CELIKOM Android A1 — ChromaSync exact APK: 75-second FULL-vs-unwrapped native Android13 A/B

**Date:** 2026-11-11. **Outcome:** confirmed genuine native-app differential, **not** proof CELIKOM Android itself works. Approved Stage A remains **NO-GO**.

## Exact input and immutable research prerequisites

- Original owner-provided `ChromaSync-Clone-3.0.1.apk`: **102,572,843 bytes**, SHA256 `4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`. Independently checked both in the chat runtime and ARM CI.
- GitHub source: existing PUBLIC repository `manufact-test/nomusic`. Binary lives only in an **UNPUBLISHED GitHub Release DRAFT**, exact tag `a1-chromasync-301-unpublished-test`; `draft=true`. **Do not click Publish**, upload to Git code/issues/artifacts, or remove the draft before research finishes.
- Embedded `assets/lspatch/origin.apk`: **59,511,238 bytes**, SHA256 `d54e58c6b7720a2d161758f41ce8d3c08d7d5cc6e9587b3976383ee2f829905b`. Extracted byte-identically at runtime only; not modified, re-signed, uploaded or patched. 6 DEX, manifest, native libs; no outer LSPatch config/loader embedded.
- **Important distinction:** this nested file is a **third-party, separately signed and renamed 2025 host**, NOT a verified pristine issuer-signed APK of Yandex 2025.10.4 #120.1rur. It cannot be used to infer behavior of the official 2025 release without separate publisher-certificate verification.

## New real hardware-architecture CI — NOT synthetic

**[GitHub Actions #43081123928](https://github.com/manufact-test/nomusic/actions/runs/43081123928)**: native Ubuntu ARM64 runner with Redroid Android **13 (API 33)** supporting arm64-v8a and armeabi-v7a. Two **independently clean** Android guests (first guest stopped and data removed before second). The *same exact outer APK* was downloaded privately from the draft and hash-checked. No owner phone/account, WebView/client redesign, hook injection, bypass change, audio session, DRM, Play Protect or backend involved.

Observer `android/native-yandex-hooklab/ci/chromasync_extended_lifecycle_arm13.py` sampled **25 times at 3-second intervals, over 75 seconds**. Each sample required exact MAIN PID and resumed Activity; focus sampled at first and final points. The gate requires **the same PID throughout all 25 observations**, not mere `pidof` presence (rejects crash/restart false positives). Sampling cannot prove every millisecond between samples; do not call this infinite uptime or audible playback.

| True Android ARM13 gate | Full exact ChromaSync outer APK | Byte-identical nested origin.apk only |
| --- | --- | --- |
| Input hash and install | PASS / INSTALLED | PASS / INSTALLED |
| Exact resolved native launcher | MAIN_LAUNCH_ACCEPTED | MAIN_LAUNCH_ACCEPTED |
| Same exact MAIN PID throughout 25 samples | **PASS** (25/25 PID alive, no switch) | **FAIL** (only 13/25 PID samples present; original MAIN changed/missing) |
| Native Activity resumed | **25/25** | **5/25** |
| Clone window focus first/last | **2/2** | **1/2** |
| Scoped OS application exit | No observed restart in this 75s window | Android exact MAIN `reason=4` Java crash, `am_crash_main=true`, `am_proc_died_main=true` |
| Bounded private crash buffer category | Not needed; MAIN stayed stable | `APPLICATION_STATE`, fatal runtime marker seen, NOT native linker or missing DEX indication |
| Final 75s A/B | `LONG_NATIVE_MAIN_STABLE` | `LONG_NATIVE_MAIN_NOT_STABLE` |

**Strict A/B CI job: SUCCESS**, because the native expected difference was truly observed. Its green result means **only that differential test passed**. Tests of classifiers also green. No screenshot contents, diagnostic text, process IDs, user credentials, proprietary binary or stack traces were uploaded in GitHub logs/artifacts.

## What this materially changes

1. The full ChromaSync is now **not just a 16-second accidental startup**. In this exact unattended Android13 lab it has a real native launcher, 25/25 same-PID observations, resumed Activity and foreground focus at the start/end across **75 seconds**.
2. The nested 2025 host **does not** become equivalently stable by removing the outer setup. The Java `APPLICATION_STATE` crash (exact subtype unknown) reproduces in both shorter and longer trials. Simple downgrade to a 2025 release is **not a supported fix** for our independently signed CELIKOM clone.
3. Causal isolation is **still incomplete**. Full outer ChromaSync differs in several bundled factors (native wrapping, injected proprietary module, application factory, signatures, package-compatible setup, and `sigBypassLevel=2`). The A/B does **not prove any one** is necessary/sufficient. Do NOT copy foreign binary/module, signature spoofing or bypass level 2 into CELIKOM.
4. In a separate real control, [CI #43072904573](https://github.com/manufact-test/nomusic/actions/runs/43072904573) proved full competitor alongside the pinned **issuer-signed Yandex 2026.10.3 #170gpr** with a stable 16-second competitor lifecycle. The *75-second test was standalone full versus unwrapped origin,* not an additional 75-second stock coexistence test; do not conflate them.
5. Separate OS window/focus probe [CI #43077478927](https://github.com/manufact-test/nomusic/actions/runs/43077478927) proved real clone-owned foreground WindowManager focus and a real 720×1280 PNG header, but `uiautomator dump` did **not** expose readable XML. That is NOT verified all-screen UI, login, MyWave, library, playlists, or audible playback.

## CELIKOM A1 remains blocked

Approved main experiment `experiment/android-native-a1-lspatch-clone-loader0-20261111` at `cc4cb0f93489168db21502f3ef195855ae9fb743` demonstrates the independent 2026 separately signed clone reaches a signature-related `IllegalStateException`/mode2 and `EXIT_SELF(0)`, while a valid publisher-signed original runs normally. That failure differs from **Java crash** of the competitor's naked origin, and is not fixed by this 75-second competitor pass. Rights to modify/commercially distribute a native Yandex copy remain a separate approval requirement. Owner has explicitly prohibited unsolicited contact with Yandex. No authorization to bypass publisher trust, login/DRM, Play Protect or re-sign/redistribute vendor code is implied.

Accepted Android **Test.50** branch, Windows, browser extension, API/backend, server/production, official Yandex on owner's HONOR 50 and approved product architecture are **untouched**. No working CELIKOM consumer APK was produced. User should not install anything.

## Frozen research and recommended next lead work

- Code: `experiment/android-a1-chromasync-extended-lifecycle-20261111`, actual test SHA `5bff1888bdd86494ca922199351a8eba52691077`.
- Precise pre-experiment rollback: `backup/android-a1-pre-extended-lifecycle-20261111` @ `37272c053d4214ca1db906c3eebac9a1a80f7e61`.
- Existing positive native full-competitor checkpoint: `backup/android-a1-chromasync-exact-live-arm13-both-pass-20261111` @ `6a6786ec34e7a9580b39dac56f226e44a256f5f4`.
- Nested independent Java application-state crash checkpoint: `backup/android-a1-2025-unwrapped-crash-report-final-20261111` @ `37272c053d4214ca1db906c3eebac9a1a80f7e61`.
- Issue [#41](https://github.com/manufact-test/nomusic/issues/41) stays OPEN. Parallel B42 source contract is source-only, not native audio (see established A/B protocol).
- **Next**: do not re-run the same tests for cosmetic counters. Investigate *legitimate*, independently **publisher-signed** 2025.10.4 #120.1rur sample, validating signer/version before any use. If not verifiable, pursue only publisher-supported/native authorized options, and record a concrete no-go blocker. No ad-hoc module transplantation, signature bypass/permission spoof, login hooks, fake player, WebView or phone install.
