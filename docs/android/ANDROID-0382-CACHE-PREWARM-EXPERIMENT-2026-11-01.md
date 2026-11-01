# CELIKOM Android 0.3.82 — muted local-file decoder prewarm experiment

Date: 2026-11-01

## Baseline and safety

- Owner-approved playback baseline: CELIKOM 0.3.78 / versionCode 79.
- Immutable backup: `backup/android-0378-original-before-cached-join-20261101`.
- Backup SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.
- Exact restored runtime tree is carried by `feature/android-unified-preparation-seek-gate` as 0.3.81 / versionCode 82.
- This experiment is isolated in `feature/android-0382-cache-prewarm-staging-20261101`; it is not merged and cannot publish stable.

## Device evidence motivating the experiment

The same local-file cache-hit join was observed with two different behaviors:

- 0.3.78 started the complementary join immediately after decoder start. The join completed in about 267 ms, but the transport drift reached about 224 ms.
- 0.3.79 added the strict decoder-motion gate to new local-file entries. It reduced the measured transport drift to about 85 ms, but the join took about 651 ms and required an extra WARM correction.

The decoder is not reused from cache. CELIKOM reuses the validated audio file, then constructs a new `MediaPlayer`. The suspected difference is the startup behavior of that new MediaPlayer when its data source is a local file rather than `StreamingAudio`.

In the 0.3.79 trace, the local decoder made only about 46 ms of reported progress during the first ~187 ms after `start()`. The source continued advancing. The strict gate correctly detected this late decoder clock, but then needed a WARM correction and a longer wait.

## Experiment

For a new local-file decoder only (cache hit or full-download fallback):

1. Keep the replacement volume at zero.
2. Attach the already-verified source effect at unity gain; the original remains audible.
3. Start the local MediaPlayer muted **before** issuing its initial alignment seek.
4. Wait until the muted decoder clock has advanced at least 40 ms. This reuses the existing movement criterion.
5. If it never advances within the existing 2-second seek budget, reject the join and restore/retain the original.
6. Once movement is observed, align to the current projected source position while the decoder is already running.
7. Use the existing 100 ms handover clock gate before the unchanged 160 ms complementary entry.
8. If later alignment is still unstable, the existing bounded WARM correction/fallback policy remains in force.

StreamingAudio keeps its existing path and gate. Manual user seek after the initial join remains on the existing same-decoder seek path; it does not repeat local prewarm.

## What this deliberately does not change

- No change to finger-seek algorithm or seek tolerances.
- No change to WARM lead (70 ms), strict join drift threshold (100 ms), join duration (160 ms), or gain law.
- No change to Pause/Resume, Next, Bluetooth, AudioOwnership lifecycle rules, or source recovery.
- No new UI, switches, permissions, or app modes.
- No Desktop, Backend, website, CMS, or catalogue changes.

## Regression coverage

`TestCachedAudioRollback` now replays a local-file cache hit with a deliberately delayed fake decoder clock:
- the original remains audible while the replacement is muted;
- no alignment seek is sent until the local decoder has moved;
- the initial seek occurs while the decoder is already running;
- the existing handover gate then validates movement and drift before the complementary entry;
- a decoder that never moves is rejected and leaves the original as the only output;
- subsequent manual seek still pauses/resumes the same decoder and retains the same source effect.

These are actual-engine host tests using deterministic fakes. They do not prove speaker, Bluetooth, PCM phase, or acoustic continuity.

## Validation and release policy

Run the complete Android validation: native engine suite, Android application tests, API 36 compilation, and D8. Keep the PR draft and unmerged. No Hostinger manifest write and no stable publication. A test APK may be considered only after CI passes; owner listening acceptance remains mandatory before any stable release.


## Candidate build and CI result

- Candidate: **0.3.82 / versionCode 83**.
- Staging branch HEAD: `48ee326aa43b7dad0ba48d447d46757af38437e8`.
- Draft PR #31: `feature/android-0382-cache-prewarm-staging-20261101` → `feature/android-0382-cache-path-evidence-staging-20261101`.
- Full validation workflow [#41337874853](https://github.com/manufact-test/nomusic/actions/runs/41337874853): **SUCCESS**.
  - Release-contract negative tests: PASS.
  - APK structure/provenance/signing-boundary tests: PASS.
  - Full native Android host regression suite: PASS.
  - Android API 36 compilation and D8: PASS.
  - Offline packaging toolchain staging: PASS.
  - Signed test-only APK rebuild and verification: PASS.
- Signed APK: `CELIKOM-Android-0.3.82-SIGNED.apk`, 8,755,273 bytes.
- APK SHA-256: `fb0aea25bcb8995ee3245e0aa3ffd80a8e0a1fbf34e1d978c9ebf30729f77223`.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` (expected original signing identity).
- Test-only artifact: `celikom-android-0.3.82-signed-test.zip`, artifact ID `13095853584`.
- Receipt confirms `stable_published: false`. Both stable publication and live stable-endpoint verification were skipped. No Hostinger stable manifest was changed.

The signed candidate is available as a private GitHub Actions artifact at:
https://github.com/manufact-test/nomusic/actions/runs/41337874853/artifacts/13095853584

It will **not** appear in the installed app's “Check for update” button while kept staging-only. Publishing to the stable updater would expose the candidate to all stable-channel installations and is not authorized by this staging instruction.

## Owner acceptance still required

The CI and signing pipeline prove the candidate is structurally valid and the regression suite passes. They do not prove the audible result on the HONOR device. The remaining acceptance is a listening test of the initial replacement join, ordinary song changes, manual finger seek, Pause/Resume, Next, and fallback to the original if a local decoder does not become stable.
