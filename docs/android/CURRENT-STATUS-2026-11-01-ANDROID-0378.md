# CELIKOM Android — current status at 0.3.78 baseline

Date: 2026-11-01

## Stable and rollback points

- Stable owner baseline: **0.3.78 / versionCode 79**.
- Stable source / immutable backup SHA: \`bf011dcf1a70c504883a8e5e742e0b038f41d9b0\`.
- Immutable branch: \`backup/android-0378-original-before-cached-join-20261101\`.
- Do not move, force-update or commit to the backup branch.
- Original package: \`pro.celikom.nativeprobe\`.
- Original signing certificate SHA-256: \`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f\`.

## Current experiment

- Branch: \`feature/android-0379-cached-decoder-join-staging-20261101\`.
- Candidate: **0.3.79 / versionCode 80** (installable over stable 0.3.78 with the same signer).
- Investigation: cache-hit local-file path bypasses the strict decoder-motion gate that streaming uses.
- Regression test is intentionally added before the implementation correction. The first staging CI run is expected to expose the regression.
- The implementation correction must enable the existing gate for new/coherent local-file attachments only. Do not change retained pause/resume behavior or any timing/gain constants.

## Mandatory constraints

- Android only: ReplacementEngine, Android tests, Android release metadata and Android CI.
- Do not change desktop, website, backend, CMS, catalogue, Hostinger files or stable manifest.
- Do not tune seek, WARM lead, transition duration, gain law, Pause/Resume, Next, Bluetooth or AudioOwnership.
- Do not add modes, controls, permissions or UI.
- Preserve original audio until the decoder has advanced and passed the existing transport gate. Unstable decoder startup must fail open to original.

## CI and artifact contract

The staging branch is explicitly included in Android API 36 / D8 validation. After the full suite passes, a separate reusable signing job runs with \`test_only: true\`.

Expected result:
- signed candidate APK, versionCode 80, original package and signer;
- GitHub Actions artifact only;
- receipt \`stable_published: false\`;
- stable publisher skipped;
- no Hostinger stable manifest or release-directory mutation.

## Remaining work

1. Confirm the baseline RED test fails specifically because a cache hit does not wait for decoder movement.
2. Apply the narrow shared-gate correction.
3. Run the complete native host suite, Android API 36 compilation and D8.
4. Verify the test-only signing workflow and artifact receipt.
5. Review the final diff against the immutable backup. Only then provide the experimental APK for owner listening.

CI success is not acoustic acceptance. The physical HONOR listening test remains the final gate.
