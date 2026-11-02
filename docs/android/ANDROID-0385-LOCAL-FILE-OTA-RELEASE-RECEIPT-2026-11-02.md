# CELIKOM Android 0.3.85 — local-file experiment OTA receipt (2026-11-02)

## Deployment verified; owner listening verdict recorded (2026-11-02)

- Version **0.3.85**, versionCode **86**, package `pro.celikom.nativeprobe`.
- Owner expressly requested the experiment via CELIKOM's normal **Проверить обновление** button. This updater only reads the existing Hostinger `stable.json`, so the test candidate was distributed through the established stable **transport channel**; it is **not** acoustically approved.
- Experimental PR [#35](https://github.com/manufact-test/nomusic/pull/35), merged into the existing Android publish branch; source HEAD at merge: `053b7d59beb53db5f30b942feba35e51a1ab256a`.
- [GitHub Actions release run #41358568513](https://github.com/manufact-test/nomusic/actions/runs/41358568513): full native host suite, negative release contract, Android SDK 36/D8 and signed Hostinger publish **SUCCESS**.
- Live manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json — confirmed `versionName=0.3.85`, `versionCode=86`, `channel=stable`.
- Immutable APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/86-e23c962d969129c5b839ed3676e36d6a337342e2761bde852e2048bbf1bda88a.apk
- Manifest APK SHA256: `e23c962d969129c5b839ed3676e36d6a337342e2761bde852e2048bbf1bda88a`.
- Manifest APK bytes: `8,763,465`.
- Original signer certificate SHA256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- No change to `UpdateInstallReceiver`, updater code, network publishing workflow, site, catalogue, account data, or audio ownership/gain/Next/Pause algorithms.
- Delivery caveat: a separate full-APK GET attempted from this execution environment returned 504, and subsequent HEAD requests to **both** old 0.3.84 and new 0.3.85 APK URLs timed out through the same external network path. This does **not** establish a new Hostinger or updater defect; CI independently verified the immutable server file and live manifest. Actual HONOR in-app download/install must still be confirmed by the owner. Do not modify the updater on this evidence alone.

## What the test actually changes

Only a cache-miss replacement source-selection path: after a fresh authorized resolve, download the whole validated replacement to a bounded internal temporary file (20-second experimental validity, 30 MiB existing transfer cap) and initialize the same `MediaPlayer` from the local path. Existing local-file prewarm, join, seek, Pause, Next, Stop and restoration rules are unchanged. No hybrid/second decoder implementation, toggle or manual song downloads. Details and limitations: [ANDROID-0385-CONTROLLED-LOCAL-FILE-SEEK-EXPERIMENT-2026-11-02.md](ANDROID-0385-CONTROLLED-LOCAL-FILE-SEEK-EXPERIMENT-2026-11-02.md).

## Preserve exact rollback points

- `backup/android-0384-before-local-seek-experiment-20261102` → `d434d442aeed7a84f17126da48c6a08b752c825d`.
- `backup/android-0382-stable-listening-baseline-20261101` → `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`.
- `backup/android-0378-original-before-cached-join-20261101` → `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.
- Previous `release/android-0.3.84-stable` and `release/android-0.3.83-stable` branches remain untouched.

## Owner listening result — 2026-11-02

The owner installed 0.3.85 through the in-app update flow and listened on HONOR:

- **Seeking: ACCEPTED for the tested scenarios.** Ordinary finger seeking, including after Next, now sounds smooth; the owner reports no remembered seek lag in this retest.
- **Beginnings/new-track joins: IMPROVED, NOT ACCEPTED.** They are much better and sometimes nearly imperceptible, but remain audibly uneven on some songs.
- Yandex Music's own crossfade is currently OFF. First solve CELIKOM's beginning/join with it OFF; only after owner acceptance, enable Yandex crossfade and run a separate interaction test.
- The owner estimates the overall work at approximately 70% complete; this is a subjective project estimate, not a measured metric.

Do not ask for another generic seek retest. The next owner evidence will be a focused diagnostic and video/recording of problematic beginnings. Use those exact materials first. The journal and transport clocks do not measure original-source PCM or speaker phase; correlate the actual recording with the diagnostic and do not claim an acoustic fix from CI alone.
