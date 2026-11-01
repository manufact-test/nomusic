# CELIKOM Android 0.3.81 — exact 0.3.78 source restore receipt

Date: 2026-11-01

## Source restoration

Protected original:
- Branch: `backup/android-0378-original-before-cached-join-20261101`
- SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`
- Original app identity: 0.3.78 / versionCode 79.

Restored release:
- Branch: `feature/android-unified-preparation-seek-gate`
- Commit: `ae1c9631091ad340be94f3f6705805aa17755bf8`
- App identity: 0.3.81 / versionCode 82.

The full release tree was built from the exact protected backup tree. GitHub compare confirms exactly three files differ from the backup:
1. `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java` — version label only.
2. `android/native-companion/release-spec.json` — version/versionCode only; package and signing identity retained.
3. `android/native-companion/tests/check_release_contract.py` — test expectations for new OTA version.

There are **no runtime/application source differences** from the protected backup. The versionCode increase to 82 is required to install the restored source over the already installed 0.3.80/code81 package. The original backup branch was not modified.

## CI and OTA publication

- GitHub Actions run: [41331639914](https://github.com/manufact-test/nomusic/actions/runs/41331639914) — **SUCCESS**.
- Release-contract negative tests: PASS.
- APK archive integrity tests: PASS.
- Source-to-DEX provenance tests: PASS.
- Full Android native host regression suite: PASS.
- Android API 36 compilation: PASS.
- D8: PASS.
- Signed APK rebuild/verification: PASS.
- Hostinger immutable APK upload: PASS.
- Live stable manifest exact-match verification: PASS.
- Publisher output: `Stable Android version published: 0.3.81 82`.

## Published APK

- Version: **0.3.81**
- versionCode: **82**
- Package: `pro.celikom.nativeprobe`
- APK size: **8,755,273 bytes**
- APK SHA-256: `df77ca821b0319ac37ffb350e6c7478063b9c52cb3e033c279b7f884e29083ae`
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`
- APK URL: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/82-df77ca821b0319ac37ffb350e6c7478063b9c52cb3e033c279b7f884e29083ae.apk
- Stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json

## Owner acceptance pending

The owner must install this release through CELIKOM's normal Check for updates button and test playback/seek behavior. No new audio-engine changes are authorized until the owner reports the result.
