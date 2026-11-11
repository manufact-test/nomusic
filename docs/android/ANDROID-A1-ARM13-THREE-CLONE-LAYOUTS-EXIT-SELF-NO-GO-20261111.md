# CELIKOM Android A1 — native ARM13 three independent clone layouts EXIT_SELF(0)

Date: 2026-11-11. **Verified strict native Yandex clone MAIN/UI status: NO-GO**. No accepted Android APK has been produced.

## Verified CI evidence

- [Triple A/B native ARM13 CI 42991987803](https://github.com/manufact-test/nomusic/actions/runs/42991987803), successful completed rerun of experiment (workflow final failure is intentional because native clone failed its real startup gate). Exact source commit: 7c894ebe02e9b4ff1bc42f7a039e7f259e2e979d. The first attempt had a transient Redroid boot failure before executing the clone; rerun booted normally and tested all variants.
- Host: disposable GitHub ARM64 Linux, containerized Android13 API33 with genuine ARMv7 32-bit userspace, no x86 NativeBridge.
- **A, independent 5 lab-signed clone splits, no merge and no LSPatch:** Android installs exact five independently signed cloned splits; clone MAIN starts and its Activity is briefly resumed, then exact MAIN ApplicationExitInfo reports REASON_EXIT_SELF (1), status ZERO.
- **B, independently signed single merged clone APK, without LSPatch:** same transient app startup then exact MAIN EXIT_SELF with status ZERO.
- **C, same separately signed single APK wrapped with upstream LSPatch v1.2-487, signature bypass level 0, zero modules:** same transient app startup then exact MAIN EXIT_SELF with status ZERO. No Java or native crash observed in scoped crash buffer.
- **Unmodified publisher-signed original five APKs:** all five install without changes, original MAIN remains alive and Activity resumed after the clone trials; independent repeated original baseline [CI 42991987794](https://github.com/manufact-test/nomusic/actions/runs/42991987794) GREEN; previous baseline [CI 42990078186](https://github.com/manufact-test/nomusic/actions/runs/42990078186) GREEN.
- [Two-layout prior CI 42991348866](https://github.com/manufact-test/nomusic/actions/runs/42991348866) already showed matching direct clone vs LSPatch EXIT_SELF(0). [Initial true ARM13 clone CI 42990746852](https://github.com/manufact-test/nomusic/actions/runs/42990746852) detected clone MAIN not alive before proper self-exit classification.
- Unit/static checks PASS, but clone workflow is intentionally FAILURE because strict MAIN/UI gate fails. No audio tested; no account, cookies or tokens read; no APK or proprietary code uploaded to GitHub artifacts, Releases or Library.

## What this proves (and does not)

1. LSPatch itself cannot be the *necessary cause* of the observed shutdown: the unwrapped clone does the same.
2. Merging five splits into one APK cannot be the *necessary cause*: the five-split clone exits identically.
3. We have an **independent-app startup/identity-trust feasibility blocker**. Do NOT assert the exact Yandex check or responsible instruction has been found. Our clones differ from the publisher original in both Android package name and signing certificate; tests do not isolate these variables.
4. The genuine ARM test bed works: our owned ARMv7 JNI app with LSPatch and a real LibXposed hook entered its own process [CI 42987483624](https://github.com/manufact-test/nomusic/actions/runs/42987483624). The official signed original works on same platform. Neither makes the independent Yandex clone a working app.
5. Redroid is headless and has no GMS/Play Protect; no owner HONOR, real login or audible playback was used. Never claim device Play Protect compatibility or audio replacement from these gates.

## Strict next steps and prohibitions

- Do NOT repeat NativeBridge, APK merge, loader ABI/resource mirror or LSPatch tweaks trying to fix this EXIT_SELF; this matrix rules them out as necessary causes.
- Only legitimate **read-only** app lifecycle/configuration analysis and an official/publisher-supported native embedding feasibility assessment are now justified. No signature spoofing, signature bypass 1/2, re-signing/publishing issuer original, Passport authentication circumvention, DRM, device protection bypass or developer-key extraction. Stop and escalate if a publisher integrity requirement prevents a separately signed native clone.
- Preserve the user-approved product requirements: one independent CELIKOM APK, true native Yandex UI, one original decoder, authorized source replacement, intact official Yandex app. Do not silently switch to WebView, a second player, root or a second phone.
- Remain **NO-GO for any user test APK** until legitimate native UI/side-by-side safety/Play Protect checks, then login, decoder/audio and owner acoustic approval are actually verified. User's HONOR and accepted Test.50/Windows/extension/backend remain untouched.
- After the owner actually accepts a working and archived Phase A audio baseline, explicitly remind them of Phase B independent replacement for LSPatch. Phase B is NOT ready today.

## Exact source and backups

Tested SHA: 7c894ebe02e9b4ff1bc42f7a039e7f259e2e979d. Frozen backup branch: backup/android-a1-native-arm13-three-layout-clone-exit-self-proven-20261111 at the same SHA. Before-exit-probes branch: backup/android-a1-before-true-arm13-clone-exit-ab-diagnostics-20261111 at 61198d71c0f75cc1dd8e3ee20f51673458cb9cbc. Previous ARM original/own-hook green backup: backup/android-a1-true-arm13-signed-yandex-original-and-owned-hook-green-20261111 at 06f2d237059c014c12548f85c5d67acf24e8ee00.

Code: android/native-yandex-hooklab/clone_native_arm13_redroid_gate.py, clone_native_identity_phase2_ephemeral.py, clone_main_crash_buffer.py, native_arm13_signed_original_control.py. Workflow: .github/workflows/android-native-a1-arm13-clone-main-ab.yml.
