# CELIKOM Android 0.3.78 — cached-file decoder join investigation

Date: 2026-11-01  
Status: **implementation and CI verified; owner acoustic test pending**

## Immutable baseline and experiment

- Stable owner baseline: **0.3.78 / versionCode 79**.
- Immutable recovery branch: \`backup/android-0378-original-before-cached-join-20261101\`.
- Immutable recovery SHA: \`bf011dcf1a70c504883a8e5e742e0b038f41d9b0\`.
- Staging branch: \`feature/android-0379-cached-decoder-join-staging-20261101\`.
- Code SHA used for the verified APK: \`e04d5a7d5eafac2e03c61c885bbe86238e4638d9\`.
- Staging candidate: **0.3.79 / versionCode 80**, same package and signing certificate.
- Stable publication is prohibited for this branch. The staging signer is called with \`test_only: true\`; its receipt says \`stable_published: false\`.

## Terminology: the decoder is not cached

The in-memory cache stores a validated audio **file**, not a reusable MediaPlayer decoder. Every cache hit creates a fresh \`MediaPlayer\`.

- \`ReplacementEngine.prepare()\` checks \`recentAudio.remove(audioKey(j))\`.
- A hit calls \`acceptAudio(key, j, g, cached, null)\`.
- A streaming result calls the same \`acceptAudio\` method with a \`BufferedAudio\` source.
- \`acceptAudio()\` creates a new \`MediaPlayer\` in both cases. The source differs: local file path for a cache hit, \`StreamingAudio\` / \`MediaDataSource\` for a range stream.
- Both paths share the same \`OnPreparedListener\`, measured-duration and audio-session validation, and subsequent \`update()\` state machine.
- Cache reuse still requires a new live authenticated resolve. The cached file alone never authorizes playback.

## Confirmed original path difference

The first position-alignment path is shared. The final cold-attach gate was not.

- Streaming sets \`streaming != null\`; \`fade()\` therefore enabled \`AudioOwnership.handoverWaitForClock(true)\`.
- That gate waits for at least 40ms of decoder-position movement, checks projected source/decoder transport drift against the existing 100ms limit, permits at most two existing muted WARM corrections, and preserves the original on timeout or unstable alignment.
- A local cache hit sets \`streaming == null\`. In the 0.3.78 source, \`fade()\` passed \`false\` to \`handoverWaitForClock()\`, even for a newly created decoder. The 160ms complementary entry could therefore begin without proving that the local decoder had advanced.
- \`ClockSupervisor\` did not replace this missing check: once the local decoder had been seek-aligned, a small transport residual could be accepted without a post-start movement observation.

The source-code discrepancy was confirmed. The baseline regression test failed specifically because the cache-hit path did not acquire the decoder-motion gate. This establishes the code defect; it does not by itself prove that it caused the owner's audible incident. MediaPlayer transport position is not PCM, speaker, or Bluetooth presentation measurement.

## Final narrow correction

The final gate decision in \`ReplacementEngine.fade()\` is:

- Capture \`resumeFadePending\` before it is cleared.
- Always retain the existing gate for streaming.
- Require the same gate for a new/coherent local-file attachment, including a cache hit.
- Do not add the gate to retained local Pause/Resume or route-resume reattachment.

In source terms, the decision is \`streaming != null || (coherentEntry && !retainedResumeEntry)\`. The same \`AudioOwnership.handoverWaitForClock()\` authority is used. \`AudioOwnership\` itself was not modified.

The following remain unchanged:
- 40ms decoder-motion requirement and 100ms drift limit;
- maximum two muted WARM corrections and existing 70ms WARM lead;
- 2s decoder-start timeout and 3s overall join budget;
- 160ms complementary entry, transition duration and gain law;
- Pause/Resume, Next, Bluetooth routing and AudioOwnership semantics.

After a WARM seek acknowledgement, the movement baseline is reset. The decoder must then advance another 40ms from the corrected position before the join is granted.

While the gate is unresolved, the original remains at full gain and the replacement remains muted. If the decoder never advances or cannot settle, the replacement is released and the original is retained.

## Regression coverage

\`TestCachedDecoderJoin\` adds 13 checks covering:
1. a true \`recentAudio\` cache hit after a fresh live resolve, with a newly constructed MediaPlayer and no download;
2. a playing-but-frozen cached decoder, proving the original stays at full gain until timeout and remains the only audible source after fail-open;
3. the existing muted 70ms WARM correction, post-correction decoder movement, clock verification and unchanged complementary entry.

Existing native host coverage remains mandatory. Test fixtures that model already-running local decoders now explicitly advance decoder position before timing the unchanged transition. Historical Pause/Resume, Bluetooth, HONOR, Media3, seek, Next, buffering, lifecycle, ownership and long-run checks remain in the suite.

## Verified CI and signed staging artifact

GitHub Actions run: [41324403134](https://github.com/manufact-test/nomusic/actions/runs/41324403134)

- Full native host suite: PASS — 6,730 checks across 34 reported test groups.
- Android API 36 installation and source compilation: PASS.
- D8 compilation and source-to-DEX provenance: PASS.
- Signed APK rebuild and release verification: PASS.
- Same signing identity, APK v2/v3 signature, alignment, version/API, approved manifest boundary, unchanged catalogue assets and exact compiled addon DEX: PASS.
- Test-only signing job: PASS.
- \`publish-stable\`: skipped.
- \`publish-requested-0-3-78\`: skipped.

Artifact:
- Name: \`celikom-android-0.3.79-cached-decoder-join-signed-test\`
- Artifact ID: \`13090493627\`
- APK: \`CELIKOM-Android-0.3.79-SIGNED.apk\`
- Version code: \`80\`
- Package: \`pro.celikom.nativeprobe\`
- APK SHA-256: \`77d262ce9cbee85d5ec529e7c40bc9842209559eddda986003f73352cef9e66f\`
- Signing certificate SHA-256: \`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f\`
- Receipt branch: \`feature/android-0379-cached-decoder-join-staging-20261101\`
- \`stable_published: false\`

The artifact is a direct experimental APK. It was not copied to the Hostinger stable update directory and did not change the stable manifest.

## Owner acceptance still required

CI and signing prove code, tests and packaging only. They do not prove acoustic phase or device-output timing.

The next manual test is the cache-hit scenario on the owner device, especially **“Биг сити лайф”**: let its replacement enter the local cache, move to another track, return to it, and listen for a dip, silence, click or late join. Also compare a normal streaming first-load path. Do not change any audio constants based only on a diagnostic trace.
