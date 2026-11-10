# CELIKOM Android Test.51 — isolated signed HONOR seek timeout verification (2026-11-10)

## Purpose

Test.51 is a **separate candidate build**, derived from owner-accepted Test.50 plus the four-path timeout recovery audit. It is **not** an accepted stable release or a verified fix for the original Yandex decoder transport.

- Source baseline: `backup/android-test50-exact-source-owner-accepted-20261106` @ `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`; remains immutable.
- Audit source: `backup/android-test50-seek-timeout-four-paths-ci-green-20261110` @ `ca22fc91fc2658a2f3aed597cd128caf1b9c285f`.
- Dedicated build branch: `experiment/android-test51-seek-failopen-honor-20261110`.
- Package: `pro.celikom.nativeprobe.test`, version `0.3.85-test.51`, code `86136`.
- Artifact: `CELIKOM-Android-0.3.85-TEST-51-SEEK-FAILOPEN-SIGNED.apk`.
- Build is **signed through the existing original certificate only**, with package, signature, DEX, manifest, original base-asset and isolation verification. No new certificate, no signature or Play Protect bypass.
- Existing `CELIKOM Test` installation uses the **same test package name**. Installing Test.51 updates Test.50 in that test package; it does not install as a third parallel app. Stable `pro.celikom.nativeprobe` is isolated and untouched.
- Test APK has no OTA updater or package installer permission; no updates to server, Hostinger, production, stable channels, Yandex APK, Windows or the owner's phone during CI.

## Exact verification protocol after signed build

1. Save prior Test.50 original APK and its logs; the branch and signed old artifact remain available. Install Test.51 only in the existing separate `CELIKOM Test` app slot, never over stable. Preserve stable login and source.
2. Verify a normal known replacement plays, pauses, resumes, seeks and survives Next and shuffle/radio before provoking known failure. No pre-confirmation of audio quality.
3. Check **Раскол**, ID `42884423`, and **Дым**, ID `39949113`: start a replacement, seek forward/backward, pause while seek is outstanding, resume. Watch for audio freezing or the original being muted. Collect CELIKOM diagnostic archive.
4. Only if timeouts actually occur: ensure first event logs `replacement_seek_timeout_failopen` with `timeoutCount=1`, a second timeout of either `seek_timeout` or `hot_cached_seek_timeout` on the **same key** within 60 s logs `originalUntilBoundary=true`. After latch, rewind should **not** reconnect secondary decoder. Next should permit normal source lookup again. If fewer than two timeouts occur, do **not** call this part of the change proven.
5. Also verify real pause and Seek in original Yandex after fail-open. The fail-open guard **does not send** native play/pause/seek commands to Yandex and cannot repair a Yandex internal transport hang.

## CI and evidence boundary

Production original Test.50 implementation of `seek()` and `completeSeek()` is preserved byte-for-byte (golden baseline check). Host/CI tests cover 106 025 circuit-breaker assertions and 36 replacement-engine fake-player checks, source/owner boundaries, Android D8 and packaging security gates. Signing and phone playback are **separate gates**. CI success means only the signed APK is structurally valid, **not** that «Дым»/«Раскол» are acoustically corrected.

Build uses the existing reusable `android-0385-test-app-build.yml` workflow, callable **only after** the Test.51 validation `native-android` succeeds, downloads its exact offline kit, reads the pinned original base read-only and signs on the restricted runner. The signing secret never goes to source or uploaded artifacts. Test.51 branch is explicitly allowlisted. After CI, capture workflow run, artifact SHA-256, v2/v3 signer and release receipt. Do not publish or install automatically.

At any uncertainty or red CI, stop: do not claim an APK ready and do not mutate owner-accepted Test.50, stable, Windows, user HONOR, signed Yandex, DRM, Play Protect, production or API.
