# CELIKOM Test 0.3.85-test.4 — intro prefetch and current-track handoff (2026-11-02)

## Current deliverable

**The current main task is the beginning/join of each replacement song.** Test.4 implements an actual preparation-path change; it is not merely a diagnostic build.

- Test app: **CELIKOM Test**, package `pro.celikom.nativeprobe.test`.
- Version: **0.3.85-test.4**, versionCode **86089**.
- Source commit used for this APK: `d0b418d0173207b4900f27af365e87595301c4b1`.
- Work branch: `feature/android-0385-intro-join-investigation-20261102`.
- PR [#37](https://github.com/manufact-test/nomusic/pull/37) is open and unmerged.
- Validation/build run [#41514473466](https://github.com/manufact-test/nomusic/actions/runs/41514473466): **SUCCESS**.
- Artifact ID: `13174867024`.
- APK SHA-256: `c62e93a73e48e949e112ceea4c4af38b83e7c889c3eecab3faa57df0c9d59702`.
- Size: 8,767,641 bytes.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; signer matches original; APK v3 signature verified.
- APK copied to Library, materialized back, and SHA-256 matched byte-for-byte.
- Library:
  - `/CELIKOM/Android/Test/CELIKOM-Android-0.3.85-TEST-INTRO-PREFETCH-SIGNED.apk`
  - matching `.verification.json`
  - matching `-RECEIPT.json`

## Stable/test separation and release safety

- Stable original remains **0.3.85 / code 86**, package `pro.celikom.nativeprobe`, source checkpoint `053b7d59beb53db5f30b942feba35e51a1ab256a`. Accepted-seek backup refs remain untouched.
- Test.3/code86088 remains available as the immediate previous test build; Test.2/code86087 also remains available.
- Test.4 uses the same separate test package as Test.2/Test.3 and installs over **CELIKOM Test**. It does not replace stable CELIKOM.
- `ota_updater_absent=true`, `stable_manifest_reference_absent=true`, `request_install_packages_absent=true`.
- `stable_published=false`, `stable_ota_touched=false`, `hostinger_write_performed=false`.
- No stable publisher ran; no production manifest or Hostinger file was written.

## What Test.4 changes for song beginnings

The previous Test.2/Test.3 path could see the next Media3 item but fail to prefetch it if album metadata was incomplete or marked as a timeline placeholder. Then the full replacement file download began only after the source-track boundary, so the original could continue for the download duration before the replacement joined.

Test.4 addresses that specific delay:

1. **Stable metadata fallback:** title, artist and duration are sampled. Two consistent samples may authorize identity lookup even when the album ID is absent or the timeline still marks the item as a placeholder.
2. **Conservative identity:** `AlbumProbe` tries the fresh own catalogue and previously learned album rows when strict album matching is unavailable or an album request is skipped/fails. Ambiguous, stale or conflicting identity evidence still fails closed. This only nominates a prefetch candidate; it does not authorize playback.
3. **Early full-file prefetch:** while the current source is still playing, CELIKOM resolves and downloads the next replacement file. Prefetch itself does not create a decoder, alter audio ownership, mute, seek or play anything.
4. **Promote the same in-flight download:** when the candidate becomes current, the prefetch lease is promoted. The normal current-track path still performs a fresh server resolve. If its audio key matches the prefetch descriptor, the same in-flight download/cache file is adopted instead of starting a second full download.
5. **Fail-safe mismatch:** if the fresh current resolve differs, the prefetch is invalidated and the current track uses its own fresh descriptor; stale prefetch output is discarded. No unverified file is played.
6. **Late identity response:** if the candidate is still the current source when delayed album/identity work finishes, it may still begin prefetch for that current item. If the source has moved on, the candidate is rejected.

The current join/handover gate itself remains unchanged. The accepted seek implementation and the frozen full-file source-selection block remain unchanged; `check_0385_seek_baseline.py` passed. The 250 ms service observer and Test.3 background diagnostics are retained.

## CI results

The successful run reports:

- Full native host regression suite: passed.
- `TestLookaheadPrefetchPolicy`: strict album gate and stable metadata fallback passed.
- `TestLookaheadPrefetchHandoff`: **22 checks passed** for promotion, fresh resolve, cache reuse, mismatch cancellation and late response after the source boundary.
- Cold-join exclusive experiment: passed.
- Accepted 0.3.85 seek/source golden baseline unchanged: passed.
- Background/service diagnostics remain read-only: passed.
- Android API 36 compilation and D8: passed.
- Separate package, original signer, launcher icon/label, OTA isolation and immutable receipt: passed.

Physical phone playback and acoustic acceptance are still **not** verified. Do not claim the sound is fixed until the owner listens.

## Owner test — no need to do this tonight

1. Install **CELIKOM Test 0.3.85-test.4 / code 86089** over the existing CELIKOM Test 0.3.85-test.3. Do not uninstall stable CELIKOM.
2. Stop stable CELIKOM during the listening session so two engines do not compete for the same Yandex session.
3. Keep Yandex Music `Плавный переход` OFF, matching the accepted baseline.
4. Play music normally, with CELIKOM Test running in the background. Focus on the **first 3–5 seconds after each new song starts**: whether the replacement is ready at the boundary, whether the beginning is cut, and whether the original continues too long.
5. No special seek test is required. Seeking is accepted and the golden guard is unchanged.
6. If the beginning still sounds wrong, save the combined diagnostics and a short screen recording. Do not change Start/Stop or settings before capture unless needed to restore playback.

The owner explicitly said testing can happen tomorrow; there is no need to test tonight.

---

