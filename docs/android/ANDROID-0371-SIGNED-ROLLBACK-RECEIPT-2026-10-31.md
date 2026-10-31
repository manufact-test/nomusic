# CELIKOM Android 0.3.71 / versionCode 72 — signed rollback of rejected 0.3.70

**31 October 2026. Status: published; acoustic quality on HONOR NOT YET reaccepted. Android only.**

## Verdict and source identity

The owner explicitly rejected Android 0.3.70 due to frequent finger-scrub lags, at times worsening across playback. Same version did not resolve cold join dips/micro-repeats or leave a clean Recents screen after the system installer update. Diagnostic analysis and what must not be repeated are in [ANDROID-0371-ROLLBACK-0369-OWNER-REJECTION-2026-10-31.md](ANDROID-0371-ROLLBACK-0369-OWNER-REJECTION-2026-10-31.md).

- Restored **exact functional Android 0.3.69 sources** from signed commit `a30f949b10a72f62977e70cba30767b7c382a249`. A GitHub compare of `a30f949` against rollback code `b624d5c062a6d6310459f9bb73cf5f9014eb8a54` proves **no difference** in `ReplacementEngine.java`, `UpdateInstallReceiver.java`, any other playback class or any behavior test. The only native Android source difference is the `AppVersion.java` string; separate release metadata/test changes allow `0.3.71/code72`.
- The entire 0.3.70-only long-pause re-alignment, join-clock logging and post-update task-card removal experiment are withdrawn. Original updater (the pre-0.3.70 `UpdateInstallReceiver`) restored unchanged.
- Immutable owner listening backup still `backup/android-0369-honor-listening-control-20261031` -> `a30f949b10a72f62977e70cba30767b7c382a249`. Never move or delete.
- Version bump from rejected `0.3.70/code71` to `0.3.71/code72` is required for non-destructive in-place update; normal Android installation rejects a code70 downgrade over code71. **The jump does not represent a new audio algorithm.**

## Gates and signed release

| Check | Verified result |
| --- | --- |
| Staging `feature/android-0371-rollback-0369-staging`, `b624d5c` | [SDK36/D8 CI 41228911611](https://github.com/manufact-test/nomusic/actions/runs/41228911611): SUCCESS, `publish-stable` SKIPPED |
| Production `feature/android-unified-preparation-seek-gate` | [CI/sign/publish 41229047756](https://github.com/manufact-test/nomusic/actions/runs/41229047756): SUCCESS |
| Android version | `0.3.71`, `versionCode=72`, package `pro.celikom.nativeprobe`, `minSdk=28` |
| Source of signed APK | `b624d5c062a6d6310459f9bb73cf5f9014eb8a54` |
| Original signer certificate SHA256 | `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` |
| v2/v3 signing, package/manifest, alignment, DEX and source provenance | PASS via existing signed `verify_release.py` in publishing CI |
| Size | `8,738,889` bytes |
| APK SHA256 | `e8a2095bac3cd71f83187a7002d4f37bcb4de2c60383830f34ac7a593b366e27` |
| Stable manifest | Live `/updates/android/stable.json` reports versionCode72, expected signer, exact size and APK SHA |
| Independent full APK HTTP GET | SHA256 `e8a2095bac3cd71f83187a7002d4f37bcb4de2c60383830f34ac7a593b366e27`, matches signed CI |

The release is available using the unchanged updater/button and download landing page:
`https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/`.
Immutable release:
`https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/72-e8a2095bac3cd71f83187a7002d4f37bcb4de2c60383830f34ac7a593b366e27.apk`.

The verified APK can in principle be installed over code71 because it has a higher versionCode and the same certificate. **No physical installation test was possible in this environment** (no connected HONOR/ADB). Do not claim install-on-HONOR or sound accepted from CI.

## Updater Recents UX: explicitly unresolved

The 0.3.70 post-install `finishAndRemoveTask()` callback failed the actual user acceptance test on HONOR. Android has system APIs to remove a task from Recents, but invoking them after self-upgrade relies on the app receiver/process surviving the package replacement; this was not demonstrated. Automatic activity relaunch from the background is constrained by Android's background-start policy. There is **no guaranteed post-install clear-or-reopen result demonstrated on this device**, so no additional attempt was made in the rollback. A Recents card is not by itself proof that the old app process is still executing. Per explicit owner instruction, be candid rather than promising a solution.

## HONOR acceptance / follow-up

Install once using in-app updater without deleting user data. Listen first to repeated finger seeks over a longer session, then normal pause, manual Next and first joins. The expectation is to recover the 0.3.69 behavior **including its known unsolved cold joins and rare long-pause repeat**; no claim those are fixed. On a future actual-device repro, collect one private diagnostic and investigate a reproducible mechanism before authorizing any new audio change. Do not publish private logs or media metadata; no desktop/backend/site/auth/catalog/stable distribution changes.
