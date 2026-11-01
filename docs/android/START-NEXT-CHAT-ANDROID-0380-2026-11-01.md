# Next chat — CELIKOM Android 0.3.80

Continue only from branch `feature/android-audio-regression-from-0378-20261101` in `manufact-test/nomusic`.

The branch was created directly from owner-approved 0.3.78 baseline commit `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`. Do not use 0.3.79 or its cached-decoder gate as the source baseline.

Current intended package identity: 0.3.80 / versionCode 81. This is a rollback-forward build: playback engine behavior is kept identical to 0.3.78. The only functional repository addition is the actual-engine regression `TestCachedAudioRollback`, wired into `tests/run_engine.py`.

The test protects:
- local cache hit: no additional streaming cold-decoder gate and no post-attach WARM seek;
- cached user seek: original remains audible during alignment, the same MediaPlayer/effect are reused, and no redundant audible reseek follows.

0.3.79 diagnostics showed the cached track 40371622 joining about 651 ms after prepare versus about 267 ms in 0.3.78, with an additional WARM correction. The 0.3.79 seek method itself was not modified. Transport-only logs did not prove the reported audible seek regression.

Next:
1. Verify the current branch HEAD and the full diff from the 0.3.78 baseline.
2. Run GitHub Actions: full native tests, API 36 javac/D8, release-contract and archive checks.
3. Confirm the signed test-only APK artifact is present. Do not publish stable or merge the branch.
4. Give the owner the test APK only after all checks pass.
5. Ask for a focused phone test of track starts and repeated seeking. Do not change audio behavior again until the result is known.

Do not describe transport clock evidence as PCM, phase, or hardware-output proof.
