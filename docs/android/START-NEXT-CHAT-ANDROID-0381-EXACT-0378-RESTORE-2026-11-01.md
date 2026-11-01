# CELIKOM Android — next chat handoff after exact 0.3.78 restore

Date: 2026-11-01

## Current state

- Owner asked to restore the saved original Android project version, not combine individual files or carry later audio changes.
- Protected original branch: `backup/android-0378-original-before-cached-join-20261101`.
- Protected original SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.
- Original app version: 0.3.78 / versionCode 79.
- Restored source was built as **0.3.81 / versionCode 82** solely because Android will not install versionCode 79 over the already installed 0.3.80 / code81.
- Release branch: `feature/android-unified-preparation-seek-gate`.
- Release source commit: `ae1c9631091ad340be94f3f6705805aa17755bf8`.
- Compare against protected original: exactly three files differ — AppVersion.java, release-spec.json and tests/check_release_contract.py. No Android application/runtime source files differ from the original backup.
- Protected backup branch is unchanged.

## Publication

- GitHub Actions full CI + publisher: [41331639914 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41331639914).
- Full host tests, Android API 36, D8, signed APK verification, Hostinger upload and live stable-manifest verification all passed.
- Published version: **0.3.81 / code82**.
- APK SHA-256: `df77ca821b0319ac37ffb350e6c7478063b9c52cb3e033c279b7f884e29083ae`.
- APK size: 8,755,273 bytes.
- Stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json
- APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/82-df77ca821b0319ac37ffb350e6c7478063b9c52cb3e033c279b7f884e29083ae.apk

## Immediate next action

Wait for the owner to open CELIKOM → Check for updates and install 0.3.81.

Then listen to the same songs and reproduce the same seeking actions that exposed the 0.3.80 regression.

**Do not change ReplacementEngine, AudioOwnership, seek, transition, gain, WARM lead, Bluetooth, Pause/Resume, Next, or updater code before the owner reports the 0.3.81 result.** No cherry-picks from 0.3.79/0.3.80. If any symptom remains, inspect the new diagnostic first and compare actual installed package provenance to this release receipt before editing source.

## Exact release receipt

See `ANDROID-0381-EXACT-0378-RESTORE-RECEIPT-2026-11-01.md`.
