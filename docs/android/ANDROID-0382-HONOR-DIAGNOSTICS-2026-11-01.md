# CELIKOM Android 0.3.82 — HONOR listening retest and diagnostic analysis

Date: 2026-11-01
Device: HONOR NTH-NX9, Android 13 / API 33
Yandex Music: 2026.09.5 #167.1gpr
Installed release under test: 0.3.82 / versionCode 83

## Owner decision

The owner reports that 0.3.82 is not fully correct, but prefers to retain it because it is likely the best currently available build. The audible defects remain:
- song beginnings still sometimes sound wrong;
- seeking still behaves inconsistently;
- severity varies by song: some appear clean, others show a strong defect;
- the owner suspects that problems became apparent after pressing Next, but is not certain whether the beginning was initially clean.

**Decision: freeze 0.3.82 as the current listening baseline. Do not roll back, modify audio behavior, or publish another APK at this stage.**

## Diagnostic file and run boundaries

Input: `CELIKOM-combined-20261101-220637.txt` (2,705 lines).

The file contains three run segments:
- 0.3.80 — 64.486 s, 840 events.
- 0.3.81 — 56.172 s, 545 events.
- 0.3.82 — 95.099 s, 1,317 events.

The analysis below focuses on the final 0.3.82 segment. Earlier runs are context only; they are not a controlled A/B comparison because track sequences and actions differ.

## 0.3.82 run: observed facts

- 47 `source_discontinuity` events.
- 30 discontinuities keep the same media alias; 17 change track alias.
- All 47 discontinuities are logged with `userSeek: true`, including track changes. This field therefore does not distinguish finger scrubbing from track navigation.
- 17 `source_media_item_transition` events were logged. Each reports `manualNextButtonObserved: false`.
- The next-track observer is explicitly read-only: `audioCommandSent: false`, `prefetchStarted: false`. It observes source timeline/media-item changes; it does not issue the Next command.
- 40 `audio_decoder_start` events and 41 `replacement_transition_complete` events.
- 70 seek requests: 45 ALIGNMENT and 25 WARM.
- ALIGNMENT callback latency: median 51 ms, p90 360 ms, maximum 797 ms. WARM callback latency: median 65 ms, p90 75 ms, maximum 136 ms.
- 31 source-buffer events and 30 source-buffer-resumed events.
- Six `replacement_stream_retry` events; two `replacement_stream_seek_data_wait` events.
- 93 replacement output-clock samples all report a replacement MediaPlayer timestamp, but every sample remains transport/decoder-clock evidence only. `sourcePcmMeasured`, `phaseVerified`, `hardwareOutputMeasured` remain false.
- 11 `audio_command_anomaly` entries are all classified `expected_same_song_blend` and `expectedByOwnerState: true`; these are not evidence of 11 unexpected simultaneous-playback bugs.
- 41 transition completions: 11 `unified_complementary_linear` joins with commanded 160 ms ramp; 30 `exclusive_single_turn` transitions with rampMs 0. These are different handover paths, not necessarily audible failures by themselves.

## What the log says about local-file prewarm

The new local-file prewarm path is present, but it is sparsely exercised in this run:
- exactly one `replacement_local_decoder_prewarm_start`;
- exactly one `replacement_local_decoder_prewarm_motion`;
- exactly one `replacement_local_decoder_prewarm_seek`;
- exactly one `replacement_local_decoder_prewarm_aligned`.

That one observed case is for “Солнца не видно” (track ID 48591644), around 68.7 seconds into the run:
- local file, cache hit, newly created decoder;
- original remained audible and replacement muted;
- decoder advanced 46 ms in 214 ms;
- alignment seek callback took 40 ms;
- prewarm alignment completed with original still audible.

This proves the prewarm branch executed once. It does **not** prove it was responsible for all song starts, nor that it removed the audible beginning defect. The first observed start of “Солнца не видно” at the beginning of this run used the stream path, not the local-file prewarm path. Most of the run therefore cannot be treated as a repeated test of the prewarm change.

## What the log says about seeking

The logs contain clear examples of variable seek cost:
- ALIGNMENT callback latencies range from 19 ms to 797 ms.
- A “Солнца не видно” seek waits for stream seek data; callback is 737 ms and residual reaches 679 ms before a corrective ALIGNMENT.
- A “Крылья” seek waits for stream seek data; callback is 797 ms and residual reaches 743 ms before correction.
- Other ALIGNMENT callbacks exceed 200–500 ms, with source advance during the asynchronous seek accounting for much of the observed transport residual.

These are strong indicators that seek completion timing is not consistent. They do not establish the exact waveform heard at the speaker, but they are consistent with why the same seek operation can feel clean on one song and rough on another.

The diagnostic defines residuals as source transport minus decoder cursor at callback, including source advance during the asynchronous seek. It is not output-presentation skew or PCM phase. Do not describe these values as exact audible delay.

## What the log can and cannot prove about Next

The owner suspects a correlation between pressing Next and the later onset of defects. The log does not capture a positive manual-Next-button event:
- the read-only observer says `manualNextButtonObserved: false`;
- the 17 media-item transition events report boundary changes, but not the physical UI-button press;
- the discontinuity event uses `userSeek: true` even for track changes.

Therefore the current log cannot establish whether the audible regression begins specifically after a physical Next tap, after any track boundary, or after a later seek/buffer/replacement lifecycle. This is a key instrumentation gap, not proof that the owner's observation is wrong.

## Interpretation

1. **Do not assume one universal cause for all songs.** The same run includes local-file cache reuse, streamed replacements, repeated seeks, stream buffering and different handover types. The owner also reports song-dependent severity.
2. **The prewarm experiment is not yet acoustically validated.** Only one prewarm execution appears, and all output/phase measurements remain transport-only.
3. **Seek timing is demonstrably variable.** Long ALIGNMENT callbacks and explicit stream-data waits are present. This is the clearest objective lead for the seek complaint.
4. **Next is not adequately instrumented.** The current data cannot isolate the physical Next action from automatic media-item transitions and seek discontinuities.
5. **No claim of acoustic continuity can be made from CI or these clocks.** Real listening on the HONOR remains the acceptance criterion.

## Recommended next step — investigation only

Keep the published 0.3.82 APK and the rollback point unchanged. Do not change seek, WARM, fade, gain law, Next, or prewarm yet.

The next engineering pass should be a focused instrumentation/replay task:
1. Add a truthful, read-only event for the actual CELIKOM/Media3 Next action if that action is available to the integration. Do not infer it from `source_discontinuity`.
2. Give every source item, replacement player, seek operation and owner generation a correlated ID in the diagnostic.
3. Record which path each affected song used: stream, local cache file, or full download; whether prewarm ran; and the exact state when Next or seek happened.
4. Separate physical Next, automatic track boundary, finger seek, buffering pause/resume, and repeat-to-start in the event classification.
5. Replay the same small set of songs and actions, comparing the event sequence with the owner's per-song listening notes. No algorithm changes until the sequence identifies a specific failure path.

Do not ask the owner to run another test merely to collect the same incomplete log. First improve the event attribution and inspect the exact source event handling in code. Only request a new phone retest if a concrete instrumentation build or behavior-changing candidate is ready and the owner knows exactly what it is meant to prove.

## Preserved source and rollback points

- Published stable listening baseline: 0.3.82 / versionCode 83.
- Immutable snapshot branch created for this exact 0.3.82 release tree: `backup/android-0382-stable-listening-baseline-20261101`.
- Snapshot SHA: `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`.
- Earlier owner-approved 0.3.78 rollback remains untouched: `backup/android-0378-original-before-cached-join-20261101`, SHA `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`.
- Stable release workflow: [#41339161550](https://github.com/manufact-test/nomusic/actions/runs/41339161550), SUCCESS.
- Release PR: [#32](https://github.com/manufact-test/nomusic/pull/32), open and unmerged.

No audio source code was changed while preparing this diagnostic record.
