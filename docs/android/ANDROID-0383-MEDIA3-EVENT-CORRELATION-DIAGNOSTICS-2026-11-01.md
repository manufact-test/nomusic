# CELIKOM Android 0.3.83 — Media3 event correlation diagnostic release

Date: 2026-11-01

## Purpose

This diagnostic-only release was prepared after the owner reported that the 0.3.82 listening baseline still had song-start and song-dependent seek defects, and the possible relationship to pressing Next was not established. The 0.3.82 binary remains preserved as the prior listening baseline; 0.3.83 is now the current stable OTA version.

The objective is to improve event attribution and correlate source, replacement decoder and seek operations. It is **not** an audio-quality fix and does not claim to measure speaker output or PCM phase.

## Source and release isolation

- Stable listening baseline: **0.3.82 / versionCode 83**.
- Exact baseline snapshot: **backup/android-0382-stable-listening-baseline-20261101**.
- Baseline SHA: **2e03aca1dad0f89b3d71f871270e09f8bb9f143f**.
- Earlier owner-approved rollback: **backup/android-0378-original-before-cached-join-20261101**, SHA **bf011dcf1a70c504883a8e5e742e0b038f41d9b0**.
- Diagnostic branch: **feature/android-0382-playback-continuity-fix-20261101**.
- Candidate source commit: **5a1178048a5aabdeb4cecfa19ee7db2abb797bda**.
- Candidate identity: **0.3.83 / versionCode 84**.
- Release PR: [#33](https://github.com/manufact-test/nomusic/pull/33), kept open and unmerged for the owner's diagnostic retest.
- The stable update manifest now publishes **0.3.83 / code 84**; final publication details are below.

## Instrumentation added

### Media3 source events

- **onTimelineChanged** records the timeline reason, window count, current item index, item count, live alias, event sequence and current source-item generation.
- **onMediaItemTransition** records the Media3 transition reason, event/live/current aliases, live position and item index.
- **onPositionDiscontinuity** distinguishes automatic transition, same-item seek, seek to another item and unclassified item/position changes.

Media3 reason values are classified as:
- transition 0 — repeat;
- transition 1 — automatic;
- transition 2 — seek to another item;
- transition 3 — playlist changed;
- timeline 0 — playlist changed;
- timeline 1 — source update.

The logs explicitly retain **manualNextButtonObserved: false** and **manualNextAttribution: not_exposed_by_media3_listener**. A Media3 listener callback does **not** prove that the user physically tapped the Next button. A SEEK_TO_OTHER_ITEM classification must not be presented as proof of a physical Next tap.

### Correlation across source, decoder and seek

The diagnostic now carries:
- sourceEventSequence;
- sourceItemGeneration;
- replacementGeneration;
- decoderInstanceId;
- audioSourceKind (stream, local_cache_file, or full_download_file);
- localPrewarmAttempted;
- ownerGeneration and ownerOperationEpoch;
- seek sequence, kind, target and elapsed time while a seek is in flight.

These fields are attached to seek request/completion, stream seek-data wait/resume, decoder preparation/start, local prewarm, synchronization, join guard, unified join and transition-completion records.

The existing seek single-flight ownership is preserved. The added context is captured with the seek ticket and returned with its completion record so a later callback can be attributed to the decoder and source generation that issued it.

## What was not changed

No tuning or redesign was made to:
- ALIGNMENT seek target or seek policy;
- WARM lead;
- stream range behavior;
- local-file prewarm conditions or alignment policy;
- fade duration or gain law;
- join drift thresholds;
- Next command behavior;
- pause/resume or route-recovery policy.

No source PCM, speaker presentation, hardware output or phase measurement was added. The related diagnostic flags remain false; transport and decoder clocks are not acoustic proof.

## Validation

GitHub Actions workflow [#41346799079](https://github.com/manufact-test/nomusic/actions/runs/41346799079): **SUCCESS**.

- Release identity and negative contract checks: PASS.
- APK archive and signing/provenance safety checks: PASS.
- Full Android native host regression suite: PASS.
- Android API 36 Java compilation: PASS.
- D8 compilation: PASS.
- Offline packaging toolchain staging: PASS.
- Signed test APK rebuild and verification: PASS.
- Stable publication jobs: **SKIPPED** by design.

## Final stable publication — COMPLETE

The owner authorized publication to CELIKOM's normal **Check for update** channel. The final release was rebuilt from the private pinned baseline with the original signing inputs; the test-only APK above is **not** the deployed binary.

- Release PR: [#33](https://github.com/manufact-test/nomusic/pull/33).
- Full release workflow: [#41347349507](https://github.com/manufact-test/nomusic/actions/runs/41347349507) — **SUCCESS**.
- Native Android validation, full host regression suite, API 36 compilation and D8: PASS.
- Pinned private baseline and original signing inputs: verified.
- Signed APK rebuild and archive/signature/provenance verification: PASS.
- Immutable APK upload and atomic stable-manifest update: PASS.
- Final live HTTP read of [stable.json](https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json) matched the expected release manifest exactly and reported **0.3.83 / 84**.
- Deployed APK size: **8,763,465 bytes**.
- Deployed APK SHA-256: **13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425**.
- Signing certificate SHA-256: **67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f** (original signing identity).
- Immutable deployed APK: [CELIKOM Android 0.3.83 / code 84](https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/84-13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425.apk).

The earlier test-only artifact from workflow #41346799079 has a different SHA-256 (**08f43a8b39623f2ea574ef86d2c58bbbd8046dc3a8b4554d37145835d79f3e79**) and was not deployed. The actual updater binary is the separately rebuilt APK with SHA-256 **13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425** above.

## Signed test candidate receipt

- Version: **0.3.83**.
- Version code: **84**.
- Package: **pro.celikom.nativeprobe**.
- APK size: **8,763,465 bytes**.
- APK SHA-256: **08f43a8b39623f2ea574ef86d2c58bbbd8046dc3a8b4554d37145835d79f3e79**.
- Signing certificate SHA-256: **67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f** (the original signing identity).
- GitHub artifact: **celikom-android-0.3.83-signed-test**.
- Artifact ID: **13100110442**.
- [Download signed test artifact](https://github.com/manufact-test/nomusic/actions/runs/41346799079/artifacts/13100110442).
- Receipt explicitly records **stable_published: false**.

This test artifact is retained only as the earlier CI candidate and is **not** the deployed OTA binary. The stable updater now offers the separately rebuilt and verified 0.3.83 release documented above.

## Owner retest — diagnostic purpose only

The purpose of the owner's phone retest is to capture a more useful event sequence, not to judge whether the sound has improved. The audio algorithm is intentionally unchanged. Install 0.3.83 through CELIKOM's normal **Check for update** action; the release is already live in the stable manifest.

Suggested short sequence:
1. Start playback and allow a replacement to attach.
2. Tap Next once and let the next track settle.
3. Perform one finger seek within a track.
4. If convenient, allow one natural end-of-track transition.
5. Export the diagnostic log and note which action was performed at each point.

The resulting log should show the Media3 reason and correlate the source item, replacement decoder and seek ticket. It still cannot independently prove the physical Next tap; the owner's action note is needed to interpret the event sequence.

## Next engineering decision

Inspect the new device trace first. Do not change audio behavior based only on a reason code or transport-clock residual. A behavior-changing patch requires a specific reproduced failure path and a separate owner listening acceptance.
