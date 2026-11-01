# CELIKOM Android — Current Status 2026-11-01 (0.3.82 staging)

## Owner listening retest — 2026-11-01 (latest status)

The owner has now tested the published 0.3.82 build and reports:
- song beginnings remain problematic on some songs;
- seeking remains inconsistent, varying from apparently clean to strongly audible defects by song;
- the owner suspects the problems may become apparent after pressing Next, but is uncertain whether they were initially absent.

**Current decision: keep 0.3.82 as the listening baseline. Do not roll back or make another audio-code change yet.** The diagnostic analysis is recorded in [ANDROID-0382-HONOR-DIAGNOSTICS-2026-11-01.md](ANDROID-0382-HONOR-DIAGNOSTICS-2026-11-01.md).

The latest log contains 47 discontinuities, 17 media-item transitions, 45 ALIGNMENT seeks and 25 WARM seeks. ALIGNMENT callback latency ranges from 19 to 797 ms (median 51 ms, p90 360 ms). Two stream seek-data waits reached 737 and 797 ms. This is objective evidence of variable seek timing, not direct measurement of speaker output.

The log does not prove the physical Next button was pressed: all 17 `source_media_item_transition` entries report `manualNextButtonObserved: false`, while `source_discontinuity` marks all 47 events as `userSeek: true`, including track changes. The Next-versus-automatic-boundary distinction therefore needs better instrumentation.

The local-file prewarm branch ran only once in the 0.3.82 segment (46 ms decoder motion after 214 ms). It is not enough evidence to explain or clear the song-start complaint. All output/phase flags remain transport-only.

Next engineering step: improve read-only attribution of physical Next, automatic boundaries, finger seek, buffering and per-song source path; correlate player/seek/owner generations. No seek, WARM, fade, gain, Next or prewarm behavior changes until a specific failure sequence is isolated. No further phone test should be requested until that instrumentation/replay work produces a concrete question.

Exact 0.3.82 release-tree snapshot: `backup/android-0382-stable-listening-baseline-20261101`, SHA `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`. Earlier 0.3.78 rollback remains untouched.


## Owner-approved rollback point

- Working version identified by the owner: **0.3.78 / versionCode 79**.
- Immutable backup branch: `backup/android-0378-original-before-cached-join-20261101`.
- Backup SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.
- Do not modify or force-push this backup.
- The 0.3.78 rollback point is not to be confused with later version numbers used for isolated test candidates.

## Current investigation

The recent 0.3.78 and 0.3.79 device traces indicate a local-file startup difference:

- CELIKOM reuses a validated cached audio **file**, not a cached MediaPlayer decoder. A new MediaPlayer is created for the local file.
- In 0.3.78, the complementary join began immediately after decoder start and completed in about 267 ms, but the measured transport drift reached about 224 ms.
- In 0.3.79, the strict decoder-motion gate reduced measured drift to about 85 ms, but the join took about 651 ms and needed an extra WARM correction.
- In the 0.3.79 trace, the local decoder advanced only about 46 ms during the first ~187 ms after start while the source continued playing.

The experiment addresses only this local-file decoder startup path.

## 0.3.82 staging change

Branch: `feature/android-0382-cache-prewarm-staging-20261101`

Code/build commit: `48ee326aa43b7dad0ba48d447d46757af38437e8`

Current branch HEAD after documentation: `2326ff6ec15809bf6fdfa95e9c5008bbf07786de`

Draft PR #31:
- Head: `feature/android-0382-cache-prewarm-staging-20261101`
- Base: `feature/android-0382-cache-path-evidence-staging-20261101`
- Not merged.

Behavior:
1. A new local-file decoder is started with replacement volume zero.
2. The original remains audible while CELIKOM waits for at least 40 ms of actual decoder-clock movement.
3. The wait is bounded by the existing 2-second seek budget.
4. Once movement is proven, the decoder is aligned to the current source position while already running.
5. The existing 100 ms handover gate and 160 ms complementary entry remain unchanged.
6. If the decoder never advances or the join remains unstable, the replacement is rejected and the original remains the only audible source.

StreamingAudio keeps its existing path. Manual seek after initial attachment remains on the existing same-decoder seek path.

## Explicitly unchanged

- Finger-seek algorithm and tolerances.
- WARM lead (70 ms).
- Strict join drift threshold (100 ms).
- Join duration (160 ms) and gain law.
- Pause/Resume, Next, Bluetooth, AudioOwnership lifecycle rules, and source recovery.
- Android permissions, UI, switches, and modes.
- Desktop, Backend, website, CMS, and catalogue.

## Validation and signed candidate

Full workflow [#41337874853](https://github.com/manufact-test/nomusic/actions/runs/41337874853): **SUCCESS**.

- Full native Android host regression suite: PASS.
- Release contract and APK safety/provenance tests: PASS.
- Android API 36 compilation: PASS.
- D8: PASS.
- Offline packaging toolchain staging: PASS.
- Signed test-only APK rebuild and verification: PASS.
- Stable publication jobs: SKIPPED by design.

Candidate: **0.3.82 / versionCode 83**

- Package: `pro.celikom.nativeprobe`.
- APK size: **8,755,273 bytes**.
- APK SHA-256: `fb0aea25bcb8995ee3245e0aa3ffd80a8e0a1fbf34e1d978c9ebf30729f77223`.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` (matches the original signing identity).
- GitHub artifact: `celikom-android-0.3.82-signed-test.zip`.
- Artifact ID: `13095853584`.
- [Download signed test artifact](https://github.com/manufact-test/nomusic/actions/runs/41337874853/artifacts/13095853584).
- Receipt confirms `stable_published: false`.

The test-only artifact described above was initially kept off Hostinger. After the owner clarified that the release must appear in CELIKOM's in-app updater, the same candidate was published through the established owner-requested Hostinger release pipeline. The live stable manifest now advertises 0.3.82 / code 83; see the verified publication record below.

## Remaining acceptance

CI and APK verification do not prove acoustic continuity. The owner still needs to listen to the experimental candidate on the HONOR device, focusing on:
- initial replacement join at the beginning of a song;
- ordinary song changes;
- manual finger seek;
- Pause/Resume and Next;
- fail-open behavior when a local decoder does not become stable.

PR #31 is the superseded staging-only experiment. The actual release PR #32 remains open and unmerged pending owner listening acceptance.

## Repository safety note

During this work an accidental file addition was briefly committed to the repository default branch, then immediately removed in a follow-up commit. A GitHub compare from the pre-incident parent to the current default-branch HEAD reports **zero changed files**: the default-branch tree is restored. The two history-only commits remain in its history. No stable branch, Hostinger manifest, or release artifact was modified by that incident.


## Stable channel publication — VERIFIED

- Published by the existing owner-requested Hostinger release pipeline: [workflow #41339161550](https://github.com/manufact-test/nomusic/actions/runs/41339161550), **SUCCESS**.
- Release PR: [#32](https://github.com/manufact-test/nomusic/pull/32), remains open and unmerged pending owner listening retest.
- Published version: **0.3.82**, versionCode **83**.
- Live stable manifest: `/updates/android/stable.json` now advertises **0.3.82 / code 83**. The pipeline fetched the live endpoint after publication and verified exact JSON equality with the generated release manifest.
- Immutable Hostinger file: `celikom-private/android-updates/releases/83-27300b898c4fa93b942329b5d1647930bf5f37a8e8406c055d1479cf65081195.apk`.
- Public APK URL: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/83-27300b898c4fa93b942329b5d1647930bf5f37a8e8406c055d1479cf65081195.apk
- Deployed APK SHA-256: `27300b898c4fa93b942329b5d1647930bf5f37a8e8406c055d1479cf65081195`.
- APK size: **8,755,273 bytes**.
- Original signing certificate SHA-256 retained: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- The remote publisher verified the uploaded APK's SHA-256 and size before atomically moving the immutable APK and `stable.json` into place. The final live HTTP verification reported: `Stable Android version published: 0.3.82 83`.
- The earlier test-only artifact (SHA `fb0aea...`) is **not** the deployed file. Use the Hostinger release above.

The owner can now open CELIKOM and press **Check for update**; 0.3.82 should be offered through the normal in-app update flow. Listening acceptance remains pending: test the initial join, normal track changes, manual seek, Pause/Resume, Next, and fail-open to the original.
