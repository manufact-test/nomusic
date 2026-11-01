# CELIKOM Android 0.3.80 — stable OTA release receipt

Date: 2026-11-01

## Published release

- Version: **0.3.80**
- Android versionCode: **81**
- Package: `pro.celikom.nativeprobe`
- Release branch: `feature/android-unified-preparation-seek-gate`
- Source commit: `8d32237a1ebaeaf59ccea828f601a94a19901443`
- Previous stable: 0.3.79 / versionCode 80
- Previous approved audio baseline: 0.3.78 / versionCode 79

## Build and publication verification

- GitHub Actions run: [41329361546](https://github.com/manufact-test/nomusic/actions/runs/41329361546)
- Full native Android host suite: **PASS**
- New `TestCachedAudioRollback`: **13 checks PASS**
- Android API 36 compilation and D8: **PASS**
- Signed APK rebuild and verification: **PASS**
- Immutable APK upload to Hostinger: **PASS**
- Atomic stable manifest update: **PASS**
- Live `stable.json` re-fetch and exact manifest comparison: **PASS**
- Final publisher job: **SUCCESS**
- Stable channel: **published**

## Signed APK identity

- Size: **8,755,273 bytes**
- SHA-256: `ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee`
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`
- Immutable Hostinger path: `celikom-private/android-updates/releases/81-ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee.apk`
- Public APK URL: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/81-ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee.apk
- Update manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json

## Audio baseline and scope

0.3.80 is a rollback-forward release based on the owner-approved 0.3.78 audio implementation. It removes the 0.3.79 extra decoder-motion/clock gate for local-cache hits. The cached local-file start and cached user-seek behavior are covered by the new actual-engine regression test.

The release does not claim that transport diagnostics prove acoustic phase or physical speaker output. The owner's real-device listening check remains the acceptance gate for audible track starts and repeated seeking.

## Owner validation

The release is now available through CELIKOM's existing **Check for updates** flow. The owner should check for version 0.3.80 in the app and test the same tracks and seek pattern that exposed the 0.3.79 regression.

Do not change the audio engine again until the owner reports the real-device result.
