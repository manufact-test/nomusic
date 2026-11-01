# CELIKOM Android 0.3.78 — cached-file decoder join investigation

Date: 2026-11-01  
Status: controlled staging investigation. The 0.3.78 / versionCode 79 stable baseline and its immutable backup are unchanged.

## Immutable baseline and experiment

- Stable owner baseline: **0.3.78 / versionCode 79**.
- Immutable recovery branch: \`backup/android-0378-original-before-cached-join-20261101\`.
- Immutable recovery SHA: \`bf011dcf1a70c504883a8e5e742e0b038f41d9b0\`.
- Staging branch: \`feature/android-0379-cached-decoder-join-staging-20261101\`.
- Staging candidate identity: **0.3.79 / versionCode 80**, same package and signing certificate.
- Stable publication is prohibited for this branch. The CI staging signer is called with \`test_only: true\`; its artifact receipt must say \`stable_published: false\`.

## Terminology: the decoder is not cached

The in-memory cache stores a validated audio **file**, not a reusable MediaPlayer decoder. Every cache hit creates a fresh \`MediaPlayer\`.

- \`ReplacementEngine.prepare()\` checks \`recentAudio.remove(audioKey(j))\`.
- A hit calls \`acceptAudio(key, j, g, cached, null)\`.
- A streaming result calls the same \`acceptAudio\` method with a \`BufferedAudio\` source.
- \`acceptAudio()\` creates a new \`MediaPlayer\` in both cases. The source differs: local file path for a cache hit, \`StreamingAudio\` / \`MediaDataSource\` for a range stream.
- Both paths share the same \`OnPreparedListener\`, measured-duration and audio-session validation, and the subsequent \`update()\` state machine.
- Cache reuse still requires a new live authenticated resolve. The cached file alone never authorizes playback.

## Confirmed cache-hit / streaming difference

The first position-alignment path is shared. The final cold-attach gate is not.

- Streaming sets \`streaming != null\`; \`fade()\` therefore enables \`AudioOwnership.handoverWaitForClock(true)\`.
- That gate waits for at least 40ms of decoder-position movement, checks projected source/decoder transport drift against the existing 100ms limit, permits at most two existing muted WARM corrections, and preserves the original on timeout or unstable alignment.
- A local cache hit sets \`streaming == null\`. In the 0.3.78 source, \`fade()\` passed \`false\` to \`handoverWaitForClock()\`, even for a newly created decoder. The 160ms complementary entry could therefore begin without proving that the local decoder had advanced.
- \`ClockSupervisor\` does not replace this missing check: once the local decoder has been seek-aligned, a small transport residual can be accepted without a post-start movement observation.

This is a confirmed source-code path discrepancy. It is a plausible explanation for cache-hit join instability, but it does not by itself prove that it caused the owner's audible incident. MediaPlayer transport position is not PCM, speaker, or Bluetooth presentation measurement.

## Narrow correction under test

For a **new/coherent attachment**, require the existing decoder-motion and transport-alignment gate for both local-file and streaming sources. Retained non-coherent pause/resume paths keep their existing behavior.

The experiment must not alter:
- seek timing or the existing 70ms WARM lead;
- the 100ms drift threshold, 40ms motion requirement, correction count, 2s decoder-start timeout or 3s join budget;
- 160ms complementary entry, gain law or fade duration;
- Pause/Resume, Next, Bluetooth or AudioOwnership semantics.

If the local decoder never advances or cannot settle within the existing gate, the original remains audible and the replacement is released. No speculative timing changes.

## Regression coverage

\`TestCachedDecoderJoin\` is added to the full native host suite. It covers:
1. a true \`recentAudio\` cache hit after a fresh live resolve, with a newly constructed MediaPlayer and no download;
2. a playing-but-frozen cached decoder, proving the original stays at full gain until timeout and then remains the only audible source;
3. the existing muted 70ms WARM correction for a cache hit with transport drift, followed by gate verification and the unchanged complementary entry.

Existing \`TestStreamingEngine\`, HONOR strict-join/WARM replays, lifecycle, ownership, pause, seek, Next, buffering, route and long-run regressions remain mandatory.

## Validation and acceptance

- Full Android native host suite.
- Android API 36 source compilation and D8.
- Existing release-contract, archive-integrity, provenance and signing checks.
- Signed staging artifact only, with the original package and signing certificate.
- No Hostinger stable manifest update, no production APK publication and no changes outside Android source/docs/Android CI.

A green CI build proves code and packaging regressions only. It does not establish acoustic phase or owner listening acceptance.
