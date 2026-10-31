# CELIKOM Android 0.3.72 — HONOR audio and diagnostic audit

**Date:** 2026-11-01  
**Status:** read-only audio-engine audit; no runtime behavior changes  
**Audit branch:** `feature/android-0372-honor-audio-audit-staging`  
**Base:** production HEAD `5e18fd070dbf6115f643079b03637b0d180e9665`  
**Production remains:** `feature/android-unified-preparation-seek-gate`  
**Stable release:** 0.3.72 / versionCode 73

## 1. Scope and safety

This audit covers Android only: the native companion, Media3 source observation, CELIKOM's replacement MediaPlayer, session-scoped attenuation, seek handover, diagnostic events and the HONOR journal.

No audio-engine, gain, seek-threshold, crossfade, manifest, OTA, updater, backend, web, desktop-extension or account changes are made on this branch. The production branch and 0.3.72 APK remain untouched.

The 0.3.72 release commit `8115228aa9c10b6244166cb44fff1760f0d32f1b` changes the distribution/updater contour; it does not change the audio engine. The stable audio behavior in 0.3.72 is therefore the same audio base as 0.3.71.

## 2. Inputs inspected

- `ANDROID-0372-HONOR-OWNER-LISTENING-AND-DIAGNOSTIC-CHECKPOINT-2026-11-01.md`
- `NEXT-CHAT.md`
- `ANDROID-0371-HONOR-DIAGNOSTIC-AUDIT-2026-10-31.md`
- `REGRESSION-GATES-2026-10-29.md`
- `ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md`
- Owner journal `CELIKOM-combined-20261031-235928.txt` from the project Library. The raw private journal is not copied into GitHub.
- Production source at `5e18fd070dbf6115f643079b03637b0d180e9665`.
- Experimental branch `feature/android-0371-honor-diagnostic-audit-staging`, head `d183a4fb1b8442274f687ba7a00f12b88ce5bcb6`.
- Android platform/API references and the Android Oboe developer project notes listed below.

The experimental branch is **36 commits ahead and 11 behind** the production reference. It is a separate line of work, not a safe merge candidate. No files from it were copied into production.

## 3. Combined journal: version boundaries

The combined journal contains three independent runs. Counts must be scoped to each `run_start`; searching the combined file without version segmentation mixes old instrumentation with the current run.

| Run | Alignment seek callbacks | Warm-alignment starts | New-song joins | `replacement_join_clock_summary` |
|---|---:|---:|---:|---:|
| 0.3.70 | 38 | 4 | 7 | 7 |
| 0.3.71 | 41 | 1 | 7 | 0 |
| 0.3.72 | 37 | 2 | 9 | 0 |

The seven clock-summary records belong to the 0.3.70 run. They must not be attributed to 0.3.71 or 0.3.72.

### Why the join summary disappeared

The 0.3.70 experimental `ReplacementEngine` contained a passive summary around the existing join envelope. It sampled **transport-position drift** and emitted start/end/min/max values. That instrumentation is absent from the stable 0.3.71/0.3.72 `ReplacementEngine`; the 0.3.72 release did not reintroduce it.

The disappearance is therefore explained by a source-code rollback/removal of the passive logger, not by the join path stopping or by the diagnostic exporter dropping an event.

Even the old summary was not an acoustic measurement: its records explicitly marked PCM as unmeasured and phase as unverified. It could show how two player position reports moved during the join, not whether the samples arriving at the output were aligned.

## 4. What the diagnostic events actually measure

### Seek

- **`replacement_seek_complete`** is emitted for `SeekKind.ALIGNMENT`. `elapsedMs` is the elapsed-realtime interval from issuing that native seek to receiving MediaPlayer's completion callback. `residualMs` is the difference between the projected Media3 source position and `MediaPlayer.getCurrentPosition()` when the callback is handled.
- It does **not** measure the time until a sample reaches the speaker/Bluetooth device, nor the duration of an audible gap.
- **`SeekKind.WARM` is not included in that counter.** In `ReplacementEngine.completeSeek()`, the WARM acknowledgement is consumed and returns before the `replacement_seek_complete` log statement. The `replacement_warm_alignment` event is logged before issuing that extra seek, but its callback duration is not recorded.
- Consequently, the 0.3.72 count of 37 is 37 logged ALIGNMENT callbacks, not a complete count of all native seek commands. The two WARM starts mean at least 39 known native seek starts in that run; the two WARM callback durations are unavailable.
- **`replacement_warm_alignment`** means the running, muted decoder was still more than the 350 ms handover threshold from the projected source position. The engine issues a WARM seek and waits for the decoder to advance again.
- **`replacement_decoder_advancing`** is logged after the decoder has advanced by at least 40 ms and the transport drift is within the 350 ms handover gate. Its `waitMs` is measured from the current phase start (which is reset after a WARM correction); it is not the full seek duration.
- **`replacement_transition_complete.commandDelayMs`** is measured from `fadeStarted`. The clock gate resets `fadeStarted` when it validates the decoder. For a new-song join this value includes the nominal 160 ms envelope plus handler scheduling; for an exclusive seek handover it covers only the short post-gate grant. It is not the full source-seek-to-audible-output time.

### Buffering and data waits

These are two different pipelines:

- **`replacement_source_buffer` / `replacement_source_buffer_resumed`** come from the Media3 source player's `buffering` state. They describe the original Yandex source timeline.
- **`replacement_stream_seek_data_wait`** comes from CELIKOM's own `BufferedAudio` MediaDataSource. Its `stalled()` condition becomes true after a foreground read has waited at least 250 ms for a missing range/cache block. It describes the replacement decoder's HTTP/range read, not Yandex buffering.

The two event families must never be merged into one generic “buffering” duration.

### Audio command monitoring

`AudioContinuityMonitor` observes commands and player state, not PCM:

- `overlap_commands` means both sources were commanded to have non-zero output. It is expected during the existing bounded new-song join; it does not prove that both waveforms were physically audible at the same time.
- `commanded_silence` is a command-state interval of at least 40 ms where Media3 reports the source as playing while neither source nor replacement is commanded audible. It is not a microphone/loopback measurement. If Media3 reports the source as not playing/buffering, the monitor does not classify that interval as commanded silence.
- The state fields on the event-closing tick describe that closing tick, not necessarily the entire preceding interval.

### Source discontinuities

`source_discontinuity.userSeek` is derived from Media3's `DISCONTINUITY_REASON_SEEK`. It means the player reported a seek discontinuity; it does not identify a physical finger gesture, the seek-bar UI, or a specific button.

In 0.3.72 there are 35 discontinuities: 27 same-index and 8 changed-index. Same-index events are consistent with in-item scrubs; changed-index events are item navigation/boundary cases. The log cannot prove that all 27 were finger drags or that all 8 were taps on CELIKOM's Next button.

There is an additional instrumentation limitation: production `Media3SourceRouter` currently writes `manualNextButtonObserved: false` as a literal. The experimental offline parser's test with a synthetic `true` value tests parser behavior only; it does not mean the running app observed a Next-button tap.

### Position projection

`PlaybackSource.position()` projects the last Media3 position forward using elapsed realtime. The current implementation adds elapsed milliseconds without multiplying by the reported playback speed. The 0.3.72 run reports speed 1.0, so this does not explain this run, but transport estimates would be wrong if playback speed were changed.

## 5. Concrete 0.3.72 evidence

### Seek cases

The 0.3.72 run has:

- 37 logged ALIGNMENT callbacks.
- 6 callbacks over 200 ms; 4 over 300 ms.
- Maximum logged callback: 679 ms.
- 5 absolute callback residuals over 225 ms.
- 2 WARM-alignment starts whose callbacks are not timed by the current event.

The six slow callback cases include one initial attachment and five same-index seek cases. Do not label the initial attachment as a finger scrub.

| Same-index case | ALIGNMENT callback | Callback residual | Follow-up transport evidence |
|---|---:|---:|---|
| A | 352 ms | 316 ms | WARM alignment at 414 ms; later decoder-advancing drift 98 ms |
| B | 226 ms | 167 ms | Decoder-advancing drift 179 ms |
| C | 679 ms | 633 ms | Second ALIGNMENT callback after correction: 35 ms / 38 ms residual; decoder-advancing drift 67 ms |
| D | 393 ms | 337 ms | WARM alignment at 417 ms; later decoder-advancing drift 110 ms |
| E | 278 ms | 248 ms | Decoder-advancing drift 312 ms; accepted by the current 350 ms gate |

The 679 ms and 393 ms cases coincide with `replacement_stream_seek_data_wait` events. In both, the replacement decoder was commanded silent, the source effect was retained, and a seek was in flight. This is strong evidence that missing replacement HTTP range data contributed to those callback delays. It does **not** prove an audible interruption during the wait, because the original source was intended to remain audible.

Case E is worth retaining as a replay target: the decoder-advancing transport drift was 312 ms, below the current 350 ms gate, so the engine proceeded without another correction. This is a transport risk worth measuring acoustically, not proof that the 312 ms difference was heard.

The initial attachment separately had a 360 ms ALIGNMENT callback with 361 ms residual, followed by a 15 ms correction callback with 16 ms residual; decoder-advancing drift before the new-song join was 250 ms.

### New-song joins

There are nine 0.3.72 new-song joins. The transport drift recorded immediately before their join starts was:

`250, 227, 201, 156, 200, 122, 124, 220, 191 ms`

The nine post-clock-gate command delays were 170–212 ms. Each join records `phaseVerified=false` and `sourcePcmMeasured=false`. The nine `overlap_commands` events are expected command-level overlap records, not nine proven acoustic faults.

A 122–250 ms player-position difference immediately before a 160 ms two-source envelope is a plausible contributor to a repeated word/note or a level dip. It is not proof: transport position does not establish PCM phase, and the two encoded editions may not contain sample-identical waveforms.

### Source-buffer intervals

The 0.3.72 run has 26 source-buffer starts and 25 resumes. One start is retired by an item boundary before a matching resume. It must not be paired with a resume from the next item; doing so creates a false multi-second buffering interval. The completed source-buffer intervals are short (7–37 ms).

## 6. Audio-session and gain architecture

The current engine uses one unified mechanism, not user-selectable audio modes:

- The original Yandex playback remains in the Yandex audio session. CELIKOM attaches a `DynamicsProcessing` insert effect to that session and changes its input gain.
- CELIKOM's replacement `MediaPlayer` has a different audio session. CELIKOM changes that player's gain with `MediaPlayer.setVolume()`.
- The existing new-song join is one bounded 160 ms complementary-gain envelope. Same-item seek recovery uses an exclusive handover after the transport clock gate; it does not run a second user-selectable audio engine.

The two gain commands are issued from the same service handler, but they travel through different session/effect and MediaPlayer control paths. There is no public Android API here that atomically schedules a gain change across two independent sessions for the same hardware output frame. Sending destination volume before reducing source gain is a sensible command-order safeguard; it does not guarantee that the framework, DSP and output route apply both changes on the same sample.

The code's “same song” decision is based on the app's identity/matching data, not waveform correlation. It does not prove that the two encoded editions have identical PCM, leading silence, mastering, edit points or sample phase.

## 7. Android platform research

### Seek and player timestamps

- Android `MediaPlayer.seekTo()` is asynchronous; `OnSeekCompleteListener` reports completion of the player's seek operation, not the moment a particular sample is heard at the output. Android documents that `SEEK_CLOSEST` can have greater performance overhead when the requested time is not a sync frame. CELIKOM currently uses this mode. This is a benchmark candidate, not a reason to switch modes blindly.
- `MediaPlayer.getTimestamp()` returns a media-time/system-time anchor for that MediaPlayer. CELIKOM can potentially inspect it for its own replacement player; it cannot call it on Yandex's private MediaPlayer.
- `AudioTrack.getTimestamp()` returns an estimated frame-position/time pair for an AudioTrack the caller owns. Android documents route/warm-up limitations and cautions that short-term polling differences are not meaningful. CELIKOM does not own Yandex's AudioTrack, so it cannot obtain the source app's AudioTrack timestamp through the audio session ID.
- Media3 documents `DISCONTINUITY_REASON_SEEK` as a player seek discontinuity, not as a touch-gesture identifier. A seek can also move to another media item.

### Actual output latency and PCM capture

Android's low-latency audio guidance states there is no API that determines latency over any output path at runtime; accurate round-trip latency requires a loopback measurement and varies by device/build/route. Input and output callback timing is not guaranteed to be synchronized.

`AudioPlaybackCapture` is a possible research path, not a capability to assume:

- It requires `RECORD_AUDIO` and user approval through `MediaProjection`.
- The source app must be capturable: supported usages and the source app's capture policy apply; the source app can disallow capture.
- The current CELIKOM manifest has no `RECORD_AUDIO` permission or MediaProjection foreground service, and the release verifier explicitly guards against adding `RECORD_AUDIO` to the product.
- Yandex's actual capture policy on the owner's installed version/device has not been measured.
- A digital playback-capture stream would still not prove the final acoustic/Bluetooth output after the downstream route.

Therefore no production permission change is proposed. If the owner approves, capture feasibility should be tested in a separate diagnostic-only package or with an external loopback/recording setup. If capture is denied, do not work around the source app's policy.

### Audio effects and sessions

Android's `AudioEffect` API attaches an insert effect to a specific AudioTrack/MediaPlayer audio session; the insert is after players in that session. Effect control can be transferred according to priority. `DynamicsProcessing` exposes per-session input-gain controls. This confirms that the Yandex attenuation and CELIKOM MediaPlayer volume are separate control paths; it does not provide a cross-session output-frame synchronization primitive.

Developer references:
- [AudioTrack](https://developer.android.com/reference/android/media/AudioTrack)
- [MediaPlayer](https://developer.android.com/reference/android/media/MediaPlayer)
- [MediaTimestamp](https://developer.android.com/reference/android/media/MediaTimestamp)
- [Media3 Player](https://developer.android.com/reference/androidx/media3/common/Player)
- [AudioPlaybackCapture](https://developer.android.com/media/platform/av-capture)
- [AudioEffect](https://developer.android.com/reference/android/media/audiofx/AudioEffect)
- [DynamicsProcessing](https://developer.android.com/reference/android/media/audiofx/DynamicsProcessing)
- [Android low-latency audio guidance](https://developer.android.com/ndk/guides/audio/audio-latency)
- [Oboe project and developer guidance](https://github.com/google/oboe) — useful general Android audio context, not a direct diagnosis for CELIKOM's MediaPlayer path.

## 8. Review of the experimental seek-offset branch

The experimental branch remains separate and is not accepted for production.

The current `SeekAlignmentPolicy` code uses a learned stable transport offset. Its current source constants are not identical to the earlier narrative docs: the code/tests use a 225 ms accepted residual and a 925 ms derived-baseline ceiling, while older notes still describe 200/900 ms. The code also uses a three-sample baseline spanning at least 250 ms, a 45 ms spread limit, a 700 ms initial baseline ceiling and a 1200 ms freshness window.

The policy subtracts a learned difference between Media3's projected position and CELIKOM's MediaPlayer position from later transport drift/seek targeting. It does not measure PCM phase. The host tests are synthetic; they do not establish that the offset is stable on HONOR or acoustically meaningful. The source comment calls the trigger a “user scrub”, but the actual trigger is the Media3 SEEK discontinuity; the app does not verify a physical touch gesture.

A specific untested risk is baseline creep: after an accepted seek, `finish()` can relearn the raw post-seek offset. Repeated individually accepted residuals can move the learned baseline. The code permits `finish()` to store a derived offset up to 925 ms, while the next `observe()` clears samples/baseline when the observed drift exceeds the 700 ms initial-baseline ceiling; the current tests assert the immediate post-`finish()` state but do not exercise the next 250 ms observation or a sequence of incremental residuals. The policy also feeds its normalized drift into the clock supervisor. Before considering it, add regressions for repeated residual accumulation, the 700/925 ms interaction, route/timebase changes and baseline expiry, and require device evidence.

**Disposition:** do not cherry-pick `SeekAlignmentPolicy`, do not merge the experimental branch, and do not change the 225/350/160 ms thresholds based on transport-only tests.

## 9. Evidence classification

### Confirmed

- 0.3.72 did not change the audio engine from the 0.3.71 stable audio base.
- The 0.3.72 run contains 37 logged ALIGNMENT callbacks, two additional WARM seek starts, nine new-song joins and no join-clock-summary records.
- Two slow seek cases coincide with replacement HTTP range/cache waits.
- The source and replacement use independent audio sessions and different gain APIs.
- Current diagnostics do not measure source PCM phase or final hardware output.
- The old seven join summaries belong to the 0.3.70 run.

### Plausible, not proven

- Missing replacement range data contributes to some long seek callbacks.
- The accepted 312 ms transport difference in one same-index seek may be audible.
- A 122–250 ms transport offset before the new-song envelope, combined with independently applied session gains, may contribute to the reported dip/repeated word.
- Different encoded editions or route buffering may make a metadata-matched join less phase-coherent.

### Not measurable from the current journal

- Exact PCM phase at the source and replacement outputs.
- The time each session's gain change reaches the hardware mixer/output frame.
- Whether a particular logged seek callback corresponds to the exact audible defect.
- Actual speaker/Bluetooth arrival latency or acoustic silence/overlap.

## 10. Recommended next step — evidence first

1. Keep the audio engine and all current thresholds unchanged.
2. In a separate staging-only diagnostic build, record **both** ALIGNMENT and WARM seek request/completion pairs with a local sequence number, seek kind, target, callback elapsed time, projected source position, decoder position, raw residual, correction pass and range-wait reason. Do not log track titles or identity keys.
3. Restore passive join transport telemetry around the existing 160 ms envelope (start/end/min/max drift), explicitly labelled `transportOnly`, `phaseVerified=false`, `sourcePcmMeasured=false`. This improves transport visibility but is not the acoustic proof.
4. Evaluate `MediaPlayer.getTimestamp()` for CELIKOM's replacement player as an additional decoder-side clock observation. Do not pretend it provides Yandex's private AudioTrack timestamp; do not poll AudioTrack timestamps every 20 ms.
5. Separately test whether the installed Yandex version allows user-consented AudioPlaybackCapture. Do not add permissions to the production CELIKOM manifest. If capture is not permitted, use an owner-approved external loopback/recording method to inspect the actual output.
6. Use the 0.3.72 seek sequences above as deterministic host-test scenarios. Preserve the existing regression gates for pause, Next, Stop, Bluetooth, buffering, background prefetch and source restoration. No fix is accepted until the owner hears it on HONOR.

## 11. Changes on this branch

- Added a privacy-safe run-scoped diagnostic parser and seven synthetic regression checks.
- The checks cover version/run separation, WARM seek undercount, source-buffer retirement at item boundaries, same-index vs changed-index discontinuities, separation of source buffering from replacement range waits, and the distinction between transport/command telemetry and PCM evidence.
- No runtime audio code, Android manifest, release version, updater or production branch was changed.
