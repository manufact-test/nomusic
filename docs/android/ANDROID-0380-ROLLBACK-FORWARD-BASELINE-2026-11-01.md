# CELIKOM Android 0.3.80 — rollback-forward from 0.3.78

Date: 2026-11-01

## Decision

0.3.79 is rejected as an owner-tested build. Do not use its source as the next development baseline and do not promote it again.

The rollback-forward source was first isolated from the owner-approved 0.3.78 stable publication commit, then promoted through the normal release branch:

- Repository: `manufact-test/nomusic`
- Release branch: `feature/android-unified-preparation-seek-gate`
- Isolated investigation branch: `feature/android-audio-regression-from-0378-20261101`
- Baseline commit: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`
- Baseline tree: `afd1f8706fc35dbc272651f7f018effa2c6ded16`

## Diagnostic conclusion

The 0.3.79 production delta from the 0.3.78 baseline was narrow: it added a decoder-motion/clock gate to newly attached local-cache decoders. The user-facing seek method and AudioOwnership seek transaction were not changed.

The combined diagnostic contains a useful same-track comparison for the local-cache path (track ID 40371622, replacement ID 37):

- 0.3.78: prepared at 16967 ms; initial alignment at 16970–16980 ms; decoder start at 17006 ms; complementary entry began at 17027 ms; transition completed at 17234 ms. About 267 ms from prepare to completed transition, with no additional WARM correction.
- 0.3.79: prepared at 22963 ms; alignment at 22972–22982 ms; decoder start at about 23024 ms; a WARM correction was issued at 23212 ms and acknowledged at 23253 ms; clock gate verified at 23374 ms; entry began at 23394 ms; transition completed at 23614 ms. About 651 ms from prepare to completed transition.

This is a concrete explanation for the worse local-cache track start reported by the owner. The added gate delayed the cached path by roughly 384 ms in this comparison.

The same diagnostic does **not** prove that the seek regression was caused by 0.3.79. The 0.3.78 and 0.3.79 runs both recorded 16 native seek requests in the compared sessions. Median request-to-ack timing was 39 ms vs 47 ms, and maximum timing was 303 ms vs 161 ms. These are transport timings only, not acoustic/output measurements. The seek implementation itself has no direct code delta between these versions. Keep the owner's audible report as a real regression, but do not claim the logs have isolated its cause.

## 0.3.80 rollback-forward candidate

The published 0.3.80 release is intentionally based on 0.3.78 playback code, with no new audio-engine behavior. It advances Android package identity to version 0.3.80 / versionCode 81 so it can be installed over the rejected 0.3.79 / code 80.

A new actual-engine regression test, `TestCachedAudioRollback`, locks two behaviors:

1. A validated local cache hit keeps the 0.3.78 complementary-entry path and does not acquire the extra streaming cold-decoder gate or issue a post-attach WARM correction.
2. A user seek on the cached local decoder restores original output during alignment, reuses the same MediaPlayer and effect, and does not create repeated seeks after alignment.

The test is not a hardware/acoustic test. Passing CI does not replace the owner's listening test.

## Build and release safety

- CI must run the full native Android host suite and Android API 36 / D8 compilation.
- The final package was built by the normal signed production publisher. The immutable APK and `stable.json` were uploaded to Hostinger and the live manifest was re-fetched and verified.

## Owner test after candidate artifact is ready

Use the same songs and seek pattern that exposed the 0.3.79 regression. Check only:

1. Whether track starts return to the 0.3.78 behavior.
2. Whether repeated seeking is smooth again.
3. Whether the same decoder continues after a seek without audible pauses or jumps.

If the rollback-forward candidate behaves like 0.3.78, the 0.3.79 cache gate is confirmed as the source of the start regression. The seek complaint must then be investigated separately from transport-only logs if it remains audible.


## Verified build result

Verified source commit: `a4ccaddae311d638e7fe4f6026a9697e179c91ac`.

GitHub Actions run #341 (`41328452631`) completed successfully:

- Release-contract negative cases: passed.
- APK archive tamper/injection checks: passed.
- Source-to-DEX provenance and unsigned-inspection guard: passed.
- Full Android native host suite: passed, including `TestCachedAudioRollback` (13 checks).
- Android API 36 compilation and D8: passed.
- Signed test-only package rebuild and verification: passed.
- Stable publishing and live stable-manifest write: skipped.

Signed test artifact:

- Artifact: `celikom-android-0.3.80-signed-test`
- Artifact ID: `13092536465`
- Workflow run: `https://github.com/manufact-test/nomusic/actions/runs/41328452631`
- APK size: 8,755,273 bytes
- APK SHA-256: `e37dc136525b80e492691700cafc3d2a45626d51b50c5100e19e3f7cdf00ff28`
- Signing certificate SHA-256 matches the pinned release identity.
- Receipt confirms `stable_published: false`.

The signed APK is a test-only artifact and is not available through the app's stable Update Center. It can be installed manually for the owner's focused listening test. The release is now available through CELIKOM's in-app Check for updates flow. Owner listening validation remains pending.


## Final stable OTA publication

- Release branch: `feature/android-unified-preparation-seek-gate`
- Release source commit: `8d32237a1ebaeaf59ccea828f601a94a19901443`
- GitHub Actions run: [41329361546](https://github.com/manufact-test/nomusic/actions/runs/41329361546) — **SUCCESS**
- Published version: **0.3.80 / versionCode 81**
- APK SHA-256: `ef76f78c49f3e66852a2da56d43d16c3f15a47849f4ff93821ac59bddec806ee`
- APK size: 8,755,273 bytes
- Original signing certificate preserved.
- Hostinger immutable APK upload: PASS.
- Live `stable.json` comparison: PASS.
- The app's existing updater should now offer 0.3.80.

The owner must test the update through CELIKOM itself and report whether track starts and repeated seeks are back to the 0.3.78 behavior. No further audio-engine changes before that report.
