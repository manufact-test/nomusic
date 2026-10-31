# CELIKOM Android 0.3.71 — HONOR seek-baseline test APK receipt

**Date:** 31 October 2026  
**Purpose:** non-publishing real-device test of the seek-scoped transport-baseline correction.

## Artifact

- **File:** `CELIKOM-Android-0.3.71-SEEK-TEST-SIGNED.apk`
- **Package:** `pro.celikom.nativeprobe`
- **Version:** `0.3.71`
- **versionCode:** `72` (intentionally unchanged)
- **Size:** 8,742,985 bytes
- **SHA-256:** `444b6c230aaddf2995138c3ad85286433dd25b3994e8a2871fe53d97dba4cb14`
- **Signing certificate SHA-256:** `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`
- **Artifact:** [GitHub Actions artifact — signed HONOR seek-test APK](https://github.com/manufact-test/nomusic/actions/runs/41238844237/artifacts/13056871292)

The package name, signing identity and versionCode are deliberately identical to the installed 0.3.71 baseline. This allows an in-place same-signer update and avoids advancing the stable version code, preserving the ability to reinstall the archived 0.3.71 baseline. The APK filename distinguishes it as a test build; the Android app version remains 0.3.71.

## Source and CI provenance

- **Repository:** `manufact-test/nomusic`
- **Branch:** `feature/android-0371-honor-diagnostic-audit-staging`
- **Build commit:** `4d7904b156a5fe2b500f6ba97c2cff7be56a9861`
- **GitHub Actions:** [run 41238844237](https://github.com/manufact-test/nomusic/actions/runs/41238844237) — **SUCCESS**
- `native-android` — SUCCESS: full host regression suite, Android API 36 compilation, D8, provenance and release-contract checks.
- `build-honor-seek-test-apk` — SUCCESS: full source build, host regression replay, APK assembly, original signing identity and independent APK verification.
- `publish-stable` — **SKIPPED**.

The signed APK was built from the current staging source, against the SHA-pinned original base APK, with the original CELIKOM signing identity. The verifier confirmed APK v2/v3 signature, zip alignment, version/API, approved manifest boundary, unchanged original catalogue assets, exact compiled addon DEX, and absence of recovery source/signing files in the APK.

## Deployment boundary

- No upload to Hostinger.
- No stable manifest or update-channel change.
- No versionCode bump.
- No replacement of the immutable `backup/android-0371-honor-usable-baseline-20261031`.
- The test artifact is stored as a GitHub Actions artifact for seven days; the linked run is the canonical source.

## Installation on the HONOR phone

1. Keep the existing installation and its data. **Do not uninstall the app.**
2. Download the signed APK from the artifact link above and open it on the phone.
3. Install it over the existing CELIKOM app. It has the same package, original signing certificate and versionCode 72.
4. If Android reports a signature conflict, downgrade, parsing error or refuses the update, stop and send a screenshot. Do not uninstall or clear app data.
5. Open CELIKOM and test:
   - fast seek;
   - seek around the historical 204ms boundary;
   - residuals above 225ms (especially 283–336ms);
   - repeated quick scrubs;
   - pause/resume during or after seek;
   - Next during alignment;
   - partial-stream seek.

After the test, provide a fresh combined diagnostic and describe exactly where a rewind, gap, click or other audible artifact occurred. Transport-clock measurements are not a substitute for listening to the actual phone output.

## Evidence boundary

CI and the signed-APK verifier prove the staged code was compiled, packaged and signed with the pinned CELIKOM identity. They do **not** prove physical HONOR speaker/Bluetooth behavior, acoustic phase alignment or that the audible micro-rewind is eliminated. The test build is ready for device acceptance, not stable release approval.
