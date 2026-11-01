# CELIKOM Android 0.3.84 — superseded alignment seek

## Baseline and evidence

- Stable baseline: Android **0.3.83 / versionCode 84**, signed release branch `release/android-0.3.83-stable`.
- Protected 0.3.82 and 0.3.78 rollback branches are not modified.
- Owner diagnostic: `CELIKOM-combined-20261101-234206.txt`, run 0.3.83.
- The run recorded 77 native seek acknowledgements; 18 ALIGNMENT callbacks exceeded 300 ms, 10 foreground stream-data waits were observed, and the longest ALIGNMENT callback was 1173 ms.
- In the `Скажи` sequence, an ALIGNMENT seek was submitted for approximately 2.85 s. While it was pending, Media3 reported a new same-item seek to approximately 36.6 s. The old callback later arrived with `staleOperation:false`, even though it no longer represented the user's latest source position.
- Root cause: `sourceSeekRequested()` only set `explicitSourceSeek`. The main update loop returns while `seeking == true`, so the in-flight ALIGNMENT ticket was not invalidated when the newer source seek arrived.

## 0.3.84 change

- A newer same-item Media3 seek now increments the audio owner's operation epoch once per pending ALIGNMENT request.
- The original MediaPlayer seek is **not** cancelled or duplicated. Native callbacks have no request ID, so single-flight remains mandatory.
- The old callback is consumed as stale. After it drains, CELIKOM evaluates the latest source position and submits one new alignment seek if required.
- If the old decoder position is already within the existing 85 ms pause-position tolerance, the source-seek flag is cleared, the source snapshot baseline is refreshed, and the completed position is reused instead of issuing a redundant seek.
- A polling-detected source jump uses the same guard if a Media3 discontinuity callback was missed.
- Original-source gain, decoder silence, existing timeouts, WARM lead, fade law, Next handling, cache policy and stream block size are unchanged.

## Important limitation

The 0.3.83 journal also records genuine stream-data waits. This patch does not make remote HTTP Range responses faster and does not claim to eliminate all seek latency. It fixes the stale-operation ownership gap and prevents an obsolete ALIGNMENT callback from being accepted as current.

## Regression coverage

New test: `TestHonor068SupersededAlignmentSeek`.

It covers:
1. Multiple Media3 source seeks while the initial stream alignment callback is pending.
2. Polling-detected source-position jumps when a Media3 discontinuity callback was missed.
3. Reuse of a completed decoder position already within the existing tolerance.
4. Preservation of the single native seek flight and original-source ownership.

## Publication receipt — verified

- Published: **2026-11-01 21:16 UTC** through CI run [41350942716](https://github.com/manufact-test/nomusic/actions/runs/41350942716).
- Release PR: [#34](https://github.com/manufact-test/nomusic/pull/34), intentionally left open for owner device retest.
- Full Android host regression suite: PASS, including **8 HONOR 0.3.84 superseded-alignment checks**.
- Release-contract negative cases, APK structure/provenance checks, Android API 36 compilation and D8: PASS.
- Signed APK verification: original signer identity unchanged; v2/v3 signature, alignment, version/API, approved manifest boundary and exact addon DEX verified.
- Hostinger immutable APK upload: PASS. Live stable manifest was fetched again and matched the proposed release exactly.
- Stable endpoint reports **0.3.84 / versionCode 85**.
- APK size: **8,763,465 bytes**.
- APK SHA-256: `a64c562989d92749982ec979eb712fa8ba2fa12492c454ff7b1c54e9337f6bc2`.
- Direct APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/85-a64c562989d92749982ec979eb712fa8ba2fa12492c454ff7b1c54e9337f6bc2.apk
- Stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json

**Owner retest is now the only outstanding step.** Use CELIKOM's normal Check for updates button. Keep 0.3.83 and the 0.3.78 rollback untouched.

## Release identity

- Version: **0.3.84**
- versionCode: **85**
- Package: `pro.celikom.nativeprobe`
- Original signing certificate SHA-256 remains unchanged.
