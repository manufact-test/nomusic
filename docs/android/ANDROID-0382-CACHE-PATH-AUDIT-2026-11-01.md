# CELIKOM Android 0.3.82 staging — cached path audit

Date: 2026-11-01

## Purpose

Protect the owner-approved 0.3.78 playback behavior while auditing the local-file cache-hit and streaming preparation paths. This branch is non-publishing staging only.

## Recovery baseline

- Immutable owner baseline: `backup/android-0378-original-before-cached-join-20261101`
- Baseline SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`
- Restored runtime source branch: `feature/android-unified-preparation-seek-gate`
- Restored release: 0.3.81 / versionCode 82. Its runtime tree matches the protected 0.3.78 source; only release identity, release-contract expectation and documentation differ.
- This staging branch was created from the restored release branch. The immutable backup is untouched.

## Actual ReplacementEngine path audit

A cache hit does **not** reuse a prepared MediaPlayer decoder. The in-memory cache stores a validated audio file.

Cache hit:
1. `prepare()` removes the matching file from `recentAudio`.
2. It calls `acceptAudio(key, j, g, cached, null)`.
3. `acceptAudio()` creates a new `MediaPlayer` and sets the local file path as its data source.

Streaming:
1. `prepare()` calls `api.stream()`.
2. The callback calls the same `acceptAudio()` with a `BufferedAudio` source.
3. `acceptAudio()` creates a new `MediaPlayer` and wraps the stream in `StreamingAudio`.

Both paths share the same prepared callback, measured-duration and audio-session validation, and the subsequent `update()` state machine. A cache hit still requires a fresh authenticated resolve.

The real source-path difference is in `fade()`: baseline code sets `alignLive = streaming != null` and passes it to `AudioOwnership.handoverWaitForClock()`. A range stream requests the decoder-motion/clock gate; a local-file attachment (including cache hit) does not.

## Why the 0.3.79 gate is not being reapplied

The previous 0.3.79 experiment changed the gate to `streaming != null || coherentEntry`. That made new local-file attachments wait for decoder movement and allowed the existing muted WARM correction.

The recorded same-track comparison for track 40371622 / replacement 37 showed:
- 0.3.78: about 267 ms from prepare to completed join; no additional WARM correction.
- 0.3.79: about 651 ms; one additional WARM correction and a longer wait for clock verification.

This is evidence that the 0.3.79 gate caused a roughly 384 ms slower local-cache join in that trace. It does **not** establish the cause of the owner's separate audible seek complaint: the seek implementation itself had no direct code delta, and the logs are transport measurements rather than speaker/PCM evidence.

Therefore this branch does not reapply that gate or change any audio behavior.

## Regression guard added

`TestCachedAudioRollback` is wired into the full native engine suite. It protects:
- fresh authenticated resolve before cached-file reuse;
- local cache hit stays on the owner-approved 0.3.78 startup path;
- no additional post-attach WARM correction is introduced;
- the existing complementary entry completes;
- a cached user seek restores original output during alignment, reuses the same MediaPlayer and source effect, and does not issue a redundant audible reseek.

These are actual-engine host tests, not acoustic or hardware-output measurements.

## Scope and release safety

- No changes to `ReplacementEngine`, `AudioOwnership`, seek, WARM lead, transition duration, gain law, Pause/Resume, Next, Bluetooth or UI.
- No Desktop, Backend, website, CMS, catalogue or updater changes.
- No stable publication, no Hostinger manifest change.
- CI must pass the complete native host suite, Android API 36 compilation and D8 before any test artifact is considered.
- Owner listening acceptance remains separate from CI.

## Next

Run the full Android validation on this branch via a draft PR targeting `feature/android-unified-preparation-seek-gate`. Keep it draft and unmerged. Do not issue another phone-test request until a concrete, behavior-changing candidate is justified by the evidence.
