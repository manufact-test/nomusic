# CELIKOM Android — Current Status 2026-11-01
## Current stable OTA: 0.3.83 / versionCode 84 — diagnostic-only release

**0.3.83 is published and available through CELIKOM's normal “Check for update” flow.** It adds read-only Media3 event attribution and source/decoder/seek correlation. It is not an audio-quality fix.

- Release workflow: [#41347349507](https://github.com/manufact-test/nomusic/actions/runs/41347349507) — SUCCESS.
- Live stable manifest: [stable.json](https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json) verified after publication; version 0.3.83 / code 84.
- Deployed APK SHA-256: `13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425`; size **8,763,465 bytes**.
- Original signing certificate SHA-256 retained: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- [Deployed APK](https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/84-13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425.apk).
- Release PR [#33](https://github.com/manufact-test/nomusic/pull/33) is open and unmerged pending owner diagnostic retest.

The separate earlier test-only artifact (#41346799079, SHA `08f43a8b39623f2ea574ef86d2c58bbbd8046dc3a8b4554d37145835d79f3e79`) is not the deployed binary. The deployed APK was rebuilt and signed by the release workflow above.

## Current task — inspect new 0.3.83 phone diagnostics

**Status: waiting for the owner to provide the new 0.3.83 diagnostic export and screen recording in the next chat. Those new materials have not yet been analyzed.**

The next chat must:
1. Read [HANDOFF-2026-11-01-ANDROID-0383-DIAGNOSTIC-REVIEW.md](HANDOFF-2026-11-01-ANDROID-0383-DIAGNOSTIC-REVIEW.md).
2. Inspect all new logs/video and isolate the 0.3.83 run.
3. Align visible start/Next/scrub/automatic-boundary moments with log events and generations.
4. Verify correlation fields against source code, not just trust log labels.
5. Explain which conclusions are proven, which are hypotheses, and whether additional instrumentation is needed.
6. Make no audio behavior changes until a concrete failure path is established.

## Problems still awaiting a root cause

A. Initial replacement join/song beginning sometimes sounds discontinuous.

B. Finger seeking is inconsistent by song, with occasional lag/jumps/desynchronization.

C. Seeking may become unstable after manual Next in Yandex Music; this is an owner observation, not yet a proven causal relationship.

The goal is stable behavior across songs and source types, not merely better diagnostic numbers.

## Diagnostic scope of 0.3.83

Read-only instrumentation records Media3 timeline changes, media-item transitions and position discontinuities, with source event sequence/generation, replacement generation, decoder instance, source kind, seek ticket/type/target/elapsed and owner generation/operation epoch.

It does **not** change audio join, fade/gain, ALIGNMENT/WARM, Next command, cache prewarm or seek behavior. Media3 callbacks do not expose a definitive physical Next-button tap; `manualNextAttribution` remains explicitly unavailable. Decoder/transport clocks do not measure speaker PCM or acoustic phase.

## Existing 0.3.82 evidence — historical, not a new-run diagnosis

The prior 0.3.82 run had:
- 47 source discontinuities, 17 media-item transitions;
- 70 seek requests (45 ALIGNMENT / 25 WARM);
- ALIGNMENT latency median 51 ms, p90 360 ms, max 797 ms;
- two stream seek-data waits of 737 ms and 797 ms;
- local-file prewarm executed once only (46 ms movement after 214 ms).

The old log marked all 47 discontinuities `userSeek: true`, including track changes, and all 17 media-item transitions had `manualNextButtonObserved: false`. Thus it did not reliably distinguish finger scrub, manual Next and automatic transitions. The initial “Солнца не видно” start used stream; local prewarm was seen only once. These facts do not prove a root cause.

## Safety / branches

- Diagnostic implementation branch: `feature/android-0382-playback-continuity-fix-20261101`.
- Source implementation commit before this docs-only handoff: `a084cff5fd9fde500a4fdc36222de7a5c826523f`.
- Release PR branch: `release/android-0.3.83-stable`; PR #33 remains open/unmerged. Avoid pushing to it casually because PR validation is connected to the stable publisher.
- Do not alter Hostinger manifest or updater manually.
- Do not change or force-push either immutable backup:
  - `backup/android-0382-stable-listening-baseline-20261101` — `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`.
  - `backup/android-0378-original-before-cached-join-20261101` — `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.

## Documents

- [Handoff](HANDOFF-2026-11-01-ANDROID-0383-DIAGNOSTIC-REVIEW.md)
- [Media3 diagnostic release details](ANDROID-0383-MEDIA3-EVENT-CORRELATION-DIAGNOSTICS-2026-11-01.md)
- [0.3.82 HONOR log analysis](ANDROID-0382-HONOR-DIAGNOSTICS-2026-11-01.md)
- [Local-file prewarm experiment](ANDROID-0382-CACHE-PREWARM-EXPERIMENT-2026-11-01.md)
- [Starter message for the next chat](START-NEXT-CHAT-ANDROID-0383-DIAGNOSTIC-REVIEW-2026-11-01.md)

