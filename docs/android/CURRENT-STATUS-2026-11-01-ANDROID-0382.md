# CELIKOM Android — Current Status 2026-11-01 (0.3.82 staging)

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

The candidate is **not** published to Hostinger and will not appear from the installed app's “Check for update” button. Publishing it to the stable updater would expose it to all stable-channel installations and requires separate explicit authorization.

## Remaining acceptance

CI and APK verification do not prove acoustic continuity. The owner still needs to listen to the experimental candidate on the HONOR device, focusing on:
- initial replacement join at the beginning of a song;
- ordinary song changes;
- manual finger seek;
- Pause/Resume and Next;
- fail-open behavior when a local decoder does not become stable.

Do not merge PR #31 or publish stable until owner listening acceptance.

## Repository safety note

During this work an accidental file addition was briefly committed to the repository default branch, then immediately removed in a follow-up commit. A GitHub compare from the pre-incident parent to the current default-branch HEAD reports **zero changed files**: the default-branch tree is restored. The two history-only commits remain in its history. No stable branch, Hostinger manifest, or release artifact was modified by that incident.
