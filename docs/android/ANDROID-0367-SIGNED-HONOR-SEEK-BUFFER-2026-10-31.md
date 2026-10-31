# CELIKOM Android 0.3.67 / code68 — signed HONOR seek-buffer test release

**2026-10-31 — RELEASED via existing in-app updater.** Real HONOR sound **NOT ACCEPTED** until the owner's new listening comparison. Android only: no backend, catalogue, desktop, website, account/auth or updater implementation changes.

## Verified release receipt

- Production branch: `feature/android-unified-preparation-seek-gate`, source commit **`525fcb4e39cc077c1eaf7f8ba4172c3fa18d2cf0`**, nine changed paths (Android Java/version/host tests and Android documentation only). The staging-only workflow trigger was **not** copied to production.
- Nonpublishing Android 0.3.67 staging CI **[41201973900](https://github.com/manufact-test/nomusic/actions/runs/41201973900)**: SUCCESS, signed publication SKIPPED.
- Production Android SDK36/D8, regression tests, integrity/contract/provenance checks, original-signature signed build and publish: **[41202070588](https://github.com/manufact-test/nomusic/actions/runs/41202070588)** SUCCESS (native-android and publish-stable/publish both SUCCESS).
- Live manifest: `https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json`, checked after production CI: `versionName=0.3.67`, `versionCode=68`, `packageName=pro.celikom.nativeprobe`, same signer SHA256 **`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`**.
- Signed immutable APK: `https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/68-47812898733722005f15e5ea79d05995169a2b54aa55e3fb7a1e752bd58deec2.apk`.
- APK size **8,738,889 bytes**, SHA256 **`47812898733722005f15e5ea79d05995169a2b54aa55e3fb7a1e752bd58deec2`**. Direct HTTP HEAD returned **200**, `application/vnd.android.package-archive`, correct content-length; a fresh full HTTP GET was independently piped through SHA256 and matched the published manifest exactly.
- Stable download path remains `https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/`. Existing in-app **«Проверить обновление»** installs the new signed APK without uninstalling or data reset.

## Changes and exact scope

1. The two private 0.3.66 HONOR reports were analysed separately, only their own `run_start(version=0.3.66)` sections. See [`ANDROID-0366-DUAL-HONOR-DIAGNOSTICS-2026-10-31.md`](ANDROID-0366-DUAL-HONOR-DIAGNOSTICS-2026-10-31.md) for counts, ordering, limits and causality.
2. New real-engine regression `TestHonor066SeekBufferReplay` failed on the signed 0.3.66 source after `seek ACK -> muted handover -> short Media3 BUFFERING`: the old engine entered a redundant PAUSED transaction, interrupted clock validation and started the decoder again. The repair retains the current *still-silent* handover ticket while the original is fully enabled and a short play-intent buffer is pending. The in-progress runnable remains scheduled and verifies live clock/drift again when READY. The pre-existing long-buffer bound is **unchanged**. 24 new tests include both admin modes, long buffers, true user pause and Next/stale callbacks.
3. The **default** cold join remains the existing 500ms exclusive non-overlap dip; it can still sound like a sag. The **admin linear** cold join remains the phase-unverified 160ms complementary-gain diagnostic. No PCM measurements or new permission; the lab may sound seamless on some songs and imperfect on others. **The tested fix applies to the shared seek handover, not to the blend gain law.**
4. No change to previously improved pause/resume, Bluetooth route-loss and Stop owner gates, account/edition/source validation, natural track transition, or existing update publication mechanism.

## HONOR test protocol for the owner

1. From the installed CELIKOM, tap **«Проверить обновление»**; install **0.3.67**. Do not delete 0.3.66 data or clear Yandex cache. Confirm the displayed version.
2. First keep **«0.3.65: без наложения (контроль)»** as the *default* cold-join mode and test several *known songs*: start song → manual Yandex **Next** → 5–6 finger seeks → allow a **natural** next track → another 5–6 seeks. Listen for jumps, repeats, lag and any drop on cold join. Save diagnosis A.
3. Long-press the existing **«Сохранить диагностику»** button on a verified admin account; choose **«Линейный переход (эксперимент)»**. The setting applies to **future cold joins**, not an already-fading song. Repeat **the same songs** and sequence with similar output route, volume and caching; distinguish normal/full download from slow/partial stream. Save diagnosis B.
4. In **both** modes additionally test Yandex pause/resume, Bluetooth reconnect/route loss, Stop, and manual Next close to a pending transition. An acoustic comparison with timecodes and a short consented speaker recording (if practicable) is more probative for the seam than command logs.
5. In the new log, look for `replacement_muted_handover_buffer_hold`: a short post-ACK buffer was held without a second owner PAUSE. Compare subsequent `replacement_resume_fast`, `audio_decoder_start`, `replacement_transition_complete` after each seek. **No telemetry event certifies audible smoothness.** If linear scrubbing still fails, note the exact song, hand movement and audible time; do not label all glitches phase interference from these logs alone.

**Acceptance criterion:** only if the same-song HONOR listening and the combined natural → manual Next → seeks → natural successor → seeks and safety regressions pass. If track-dependent cold joins remain audible, this APK is a controlled diagnostic step, not an acoustic cure. Do not blindly apply another 40/100/160/260ms fade tweak; phase/output-path feasibility remains open.
