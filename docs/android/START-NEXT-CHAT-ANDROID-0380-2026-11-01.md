# Next chat — CELIKOM Android 0.3.80

Continue from the release branch `feature/android-unified-preparation-seek-gate` in `manufact-test/nomusic`. The isolated investigation branch `feature/android-audio-regression-from-0378-20261101` remains available as a reference.

The branch was created directly from owner-approved 0.3.78 baseline commit `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`. Do not use 0.3.79 or its cached-decoder gate as the source baseline.

Published package identity: 0.3.80 / versionCode 81. Release source commit: `8d32237a1ebaeaf59ccea828f601a94a19901443`. This is a rollback-forward build: playback engine behavior is kept identical to 0.3.78. The only functional repository addition is the actual-engine regression `TestCachedAudioRollback`, wired into `tests/run_engine.py`.

The test protects:
- local cache hit: no additional streaming cold-decoder gate and no post-attach WARM seek;
- cached user seek: original remains audible during alignment, the same MediaPlayer/effect are reused, and no redundant audible reseek follows.

0.3.79 diagnostics showed the cached track 40371622 joining about 651 ms after prepare versus about 267 ms in 0.3.78, with an additional WARM correction. The 0.3.79 seek method itself was not modified. Transport-only logs did not prove the reported audible seek regression.

Next:
1. Verify the current branch HEAD and the full diff from the 0.3.78 baseline.
2. The normal production publisher has completed successfully. Run #41329361546 passed native tests, Android API 36 / D8, signed APK verification, Hostinger upload and live stable-manifest verification.
3. The app's stable OTA manifest now offers 0.3.80 / code 81. The owner must test it through CELIKOM → Check for updates.
4. Wait for the owner's report on track starts and repeated seeks. Do not change audio behavior again until the result is known.

Do not describe transport clock evidence as PCM, phase, or hardware-output proof.


Verified CI/build:
- Workflow run #341: `41328452631` — all native tests, API 36/D8 and signed-package verification passed.
- Signed test-only artifact: `celikom-android-0.3.80-signed-test`, artifact ID `13092536465`.
- APK SHA-256: `e37dc136525b80e492691700cafc3d2a45626d51b50c5100e19e3f7cdf00ff28`.
- Stable publish job was skipped; the artifact receipt records `stable_published: false`.

The signed APK is already published to the stable OTA channel and should appear in CELIKOM's in-app update check. Do not send manual APK-install instructions unless the in-app updater fails.


Published stable OTA receipt:
- CI run #342: `41329361546` — full host tests, Android API 36 / D8 and signed production publisher all **SUCCESS**.
- Live stable manifest verified: **0.3.80 / versionCode 81**.
- APK SHA-256: `ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee`.
- Immutable APK URL: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/81-ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee.apk
- Update manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json

Next action is owner validation through the app's Check for updates button, followed by track-start and repeated-seek listening checks.
