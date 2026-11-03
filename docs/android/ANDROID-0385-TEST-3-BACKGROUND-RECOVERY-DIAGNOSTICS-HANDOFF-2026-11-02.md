# CELIKOM Test 0.3.85-test.3 — background/replacement recovery diagnostics (2026-11-02)

## Current result

A separate diagnostic build has been completed and saved in the owner's ChatGPT Library. This is **not an audio fix and not acoustic acceptance**. It adds read-only evidence around the intermittent return to the original Yandex track while preserving the accepted seek/transport implementation.

- Test app: **CELIKOM Test**, package `pro.celikom.nativeprobe.test`.
- Version: **0.3.85-test.3**, versionCode **86088**.
- Built source commit: `7166fb6c036bc86fb263ba96a407a25dcfea97e6`.
- Work branch: `feature/android-0385-intro-join-investigation-20261102`.
- PR [#37](https://github.com/manufact-test/nomusic/pull/37) remains open and unmerged.
- Validation/build run [#41508364518](https://github.com/manufact-test/nomusic/actions/runs/41508364518): **SUCCESS**.
- Test artifact ID: `13172970865`.
- APK SHA-256: `ce69bd40c1ff10bbf6703fc0466e34653e8a0d5805701eb5f2630771919ce62d`.
- Size: 8,763,545 bytes.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; original certificate match and APK Signature Scheme v3 verification passed.
- The APK was copied to Library and then materialized back; both SHA-256 values match exactly.
- Library:
  - `/CELIKOM/Android/Test/CELIKOM-Android-0.3.85-TEST-BACKGROUND-RECOVERY-SIGNED.apk`
  - matching `.verification.json`
  - matching `-RECEIPT.json`

## Hard separation and release status

- Stable original remains **0.3.85 / code 86**, package `pro.celikom.nativeprobe`, source checkpoint `053b7d59beb53db5f30b942feba35e51a1ab256a`. Its two accepted-seek backup refs remain untouched.
- Previous CELIKOM Test 0.3.85-test.2 / code 86087 remains available for rollback.
- Test.3 has the same separate test package as test.2 and can be installed **over the existing CELIKOM Test**. It does not replace stable CELIKOM.
- `ota_updater_absent=true`, `stable_manifest_reference_absent=true`, `request_install_packages_absent=true`.
- `stable_published=false`, `stable_ota_touched=false`, `hostinger_write_performed=false`.
- No stable publisher ran; no production manifest or Hostinger file was written.

## What changed

This build adds diagnostic observations only. It does not change the seek algorithm, join timing, decoder selection, volume policy, Pause/Resume, Next routing, or audio ownership decisions.

New evidence includes:

1. `service_heartbeat` every 15 seconds: service age, 250 ms observer tick/sample age and gaps, Media3 event age, current source alias/position, controller state, replacement state, audio-effect session/control/enabled state, replacement-player session/position/playing state, wake lock, and recent network availability/loss.
2. `activity_lifecycle` on Activity start/stop/new intent: a point-in-time snapshot taken when the owner opens or leaves CELIKOM Test.
3. `media3_connect_attempt`, `media3_connect_result`, and `media3_disconnect_state`: connection attempt number, generation, elapsed time, result, and replacement state.
4. Network availability records now distinguish validated Wi-Fi, cellular, and VPN transports; network loss gets a state snapshot.
5. `replacement_arm_state`, `replacement_stop_state`, `replacement_recovery`, and `audio_effect_control_status`: exact arm/stop/recovery reason, whether automatic mode remains armed, retry deadline/backoff, trusted/effect/player session IDs, and decoder state.

The 250 ms service observer cadence remains unchanged. `check_background_diagnostics.py` guards that lifecycle/snapshot logging does not issue audio commands; the accepted seek golden guard `check_0385_seek_baseline.py` is unchanged.

## Important interpretation of the owner's 21:09 recording

The recording `SVID_20261102_210917_1.mp4` shows the green `Подключён` status while the detail first says `Играет оригинал`, then `Версия песни CELIKOM доступна для подмены`. Green `Подключён` is not proof that the replacement decoder is currently audible. It describes the connection/readiness state. The new snapshot records the replacement player's actual session and playback state separately.

The Activity's `onStart` only logs a snapshot and resumes UI rendering; it does not call `beginTrial`, start a new service, or re-arm audio. Do not assume that opening the screen caused the replacement to return. The new event timeline should establish whether recovery happened just before, during, or after the UI was opened.

## Owner's next test

1. Install **CELIKOM Test 0.3.85-test.3 / code 86088** over the existing CELIKOM Test 0.3.85-test.2. Do not uninstall stable CELIKOM.
2. Stop/close stable CELIKOM before the listening session; do not run both audio engines against the same Yandex session.
3. Keep Yandex Music `Плавный переход` OFF, as in the accepted baseline.
4. Start CELIKOM Test and listen normally with it in the background. No special seek/Next test is needed; the owner has already accepted seeking.
5. If the original version returns, open CELIKOM Test as before, wait a few seconds, and save the combined diagnostics plus a short screen recording. Do not toggle Start/Stop or change settings before the snapshot unless needed to restore playback.
6. If the issue does not recur immediately, simply use it normally and save diagnostics after a meaningful session.

The next analysis must compare the exact timeline: last healthy heartbeat → source/controller changes → network events → replacement resolve/download/prepare → audio-effect control/session state → replacement recovery/stop → Activity onStart. Distinguish service/process death, Media3 disconnection, stale/replaced audio session, lookup/download backoff, decoder readiness, and mere UI refresh. Do not modify audio behavior until the evidence identifies a specific cause.

## CI receipt

The successful build receipt reports:

- Full native host suite: passed.
- Cold-join exclusive experiment: passed.
- Accepted seek baseline unchanged: passed.
- Test login input contrast contract: passed.
- Background lifecycle diagnostics: passed.
- Android API 36 compilation and D8: passed.
- Physical phone playback verified: **false**.
- Acoustic acceptance: **false**.

