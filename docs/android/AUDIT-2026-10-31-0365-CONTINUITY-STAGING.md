# CELIKOM Android 0.3.65 — independent audit and experimental seek-continuity checkpoint

Date: 2026-10-31. **QA remains RED. This is NOT an approved build and there is NO new APK.**
Read this after `HANDOFF-2026-10-31-AFTER-0365-HONOR-REVIEW.md`. The installed signed release remains 0.3.65 / versionCode 66 at source anchor `37d7ff699a7cae0e051cf5dfcb63ca7a7f23c90f`. Documentation HEAD before the current work was `63411b9142ba3b1ff3f49e575ec663db155e91fc`.

## Isolation / publication safety

- Changes are limited to `android/native-companion/` and `docs/android/`. Desktop, browser extension, backend, catalog, site, authentication, and updater were not changed. The version and signing identity were not touched.
- The production Android validation workflow **automatically publishes a signed APK** after successful native-code pushes to `feature/android-unified-preparation-seek-gate` when `CELIKOM_ANDROID_AUTO_PUBLISH=true`. Therefore, DO NOT push these experimental native changes to that original branch until both audio problems and complete release gates are satisfied. Keep them in a separate non-publishing staging branch.
- The old 500ms cold join is intentionally still present and audibly flawed. The changes below solve a command-ownership conflict in scrubbing; they do **not** claim to solve cold-entry acoustics.

## Evidence: original HONOR 0.3.65 log

The private user file `CELIKOM-combined-20261031-130513.txt` was found and read directly from the user's diagnostics. Do not copy the raw log to a public repository. Only the third run, file lines 1487–2335, version 0.3.65 (849 JSON events, ~140.58s), was used here.

Observed: 41 decoder seek completions, 22 timed source-muted scrub holds, 21 `audio_command_anomaly: commanded_silence` intervals of 43–194ms, 18 cold/stream `replacement_exclusive_dip_start`, and 7 accepted position-transition source boundaries. No `replacement_scrub_fallback` is required for the gap to exist. The command monitor is not a microphone and never verifies hardware/Bluetooth sound.

Concrete cached example, track `48592143` («Не стесняйся»): Media3 seek notification 10171ms; `ReplacementEngine.seek()` enters at 10184ms and keeps the original muted; seek callback at 10240ms (58ms); decoder starts at 10242ms; clock finally advances at 10327ms; at 10331ms monitor closes a **147ms commanded-silence** interval. The decoder's seek callback was not the full delay. `ReplacementEngine.seek()` / `AudioOwnership` explicitly created a both-muted command window.

Partial-stream example, `48591846` («Каменные цветы»): cold dip at 116017ms followed by additional dips at 120148, 121430, 122583, 124139 and 124938ms before full cache at 125669ms. The `pendingStreamScrubJoin` flag turned scrubs into repeated cold-style handovers.

All seven inter-item `source_discontinuity` notifications had reasonCode 1 (`DISCONTINUITY_REASON_SEEK`), but their alias and index both changed and `SourceEventArbiter` correctly yielded BOUNDARY. This does not prove each physical Next press: Media3's reason describes a position change, not user touch telemetry. `onMediaItemTransition(reason)` had not been recorded in the old journal. The accepted boundaries reset `sourceSeekedThisTrack`, `explicitSourceSeek`, `pendingStreamScrubJoin`, decoder/effect, and identity. A long-lived stuck flag after Next is **not established** by these data.

## Real callback routing / red test

`ProbeService` now uses one pure `Media3SourceRouter` shared with the host replay to forward **actual production** `onPositionDiscontinuity` and `onMediaItemTransition` decisions from `SourceEventArbiter` to boundary/seek events. The prior `TestHonor064ManualNext` made a synthetic direct `sourceBoundary("manual_next_button")` call, bypassing this classification. No Yandex controller code or simulated human button claims were added.

`TestHonor065Media3Continuity` drives the production router and actual `ReplacementEngine` with the following host timeline:

1. Initial playing track and completed cold attachment.
2. Cross-item Media3 reason SEEK plus changed index (manual Next-like), then duplicate/stale `onMediaItemTransition` and stale discontinuity.
3. Six cached finger seeks after Next, including a mocked 55ms native decoder callback.
4. Cross-item automatic transition and six more cached seeks.
5. Partial HTTP stream, three seeks and a check that a new cold dip is never scheduled.
6. Assert no observed command anomaly and no stale decoder/effect after a boundary.

**Verified RED on unchanged 0.3.65 audio logic** after introducing the shared router: `AssertionError: RED 0.3.65: cached finger seek must never command both sources silent 2/0`. That is the required regression reproduction; router wiring alone had not changed output behavior.

The original complete host suite passed before this new test was introduced, demonstrating why the former green gates were insufficient.

## Experimental unified seek ownership correction

`ReplacementEngine.seek()` now makes an explicit choice for **all** decoder seeks, whether cached, partial or correction:

- Silence and pause the secondary decoder first via the existing `AudioOwnership` gateway, then immediately restore original source gain through its retained `DynamicsProcessing` instance. There is no both-muted 260ms hold waiting for an untagged MediaPlayer callback.
- Keep the same decoder, effect, download and authorization generation. An in-flight seek is not repeated before its callback; later source positions supersede earlier output permission. Existing clock/drift checks still gate replacement output.
- Never set `pendingStreamScrubJoin=true` on a scrub. A partial-file seek is no longer a fresh song attachment and does not retrigger the half-second dip. The original remains available while a slow HTTP seek waits.
- Existing pause, buffering, route loss, effect control loss, boundary, old-account callbacks and Stop still revoke stale output. No new UI or permission has been introduced.

**Caution:** Immediately restoring Yandex on finger seek may reveal a short piece of native audio before the player's actual output reaches its new position. Previously that was masked at the price of a 43–194ms commanded gap. Only a real HONOR/BT listen can decide whether the new native/replacement switch sounds cleaner; command-level tests cannot certify it. The absence of `audio_command_anomaly` does not prove acoustic perfection.

Older 0.3.59/0.3.63/0.3.64 test assertions that positively demanded a muted original for 260ms or a new 500ms dip after every partial seek were updated to the new continuous-owner invariant. Other pause/route/Stop protections are retained, not relaxed.

## Test result / limitations

- `python3 android/native-companion/tests/run_engine.py`: **PASS** all runnable local fake-engine suites, including new HONOR replay **71 assertions**, long-run 300 transitions / 15 virtual hours, pause/resume, source buffering, Bluetooth route loss, stale callback fencing, 0.3.51 journal and architecture check.
- `check_audio_architecture.py`: **PASS**; rejects re-introduction of muted-source scrub timer and repeated partial cold dips and confirms shared production Media3 router.
- Local **Android SDK 36 absent**, but the independent staging GitHub Actions run [41194035806](https://github.com/manufact-test/nomusic/actions/runs/41194035806) completed **SUCCESS**: pinned dependencies, release/archive/provenance negative cases, complete host tests, full Android API36 source compilation and addon host tests, D8 output, provenance and offline packaging kit. This validates compilation and fake/native host behavior, **not** physical `MediaController` instrumentation or audio quality.
- The `publish-stable` job in that run was explicitly **SKIPPED** because this was a nonpublishing staging branch. Neither signing nor deployment occurred.
- There was no signed artifact, no manifest update, no Android release, no HONOR audio recording, and no CI publication from this checkpoint.

## Cold attachment remains technically unresolved

The present `fade(true)` uses two exclusive 250ms phases that reach a commanded **zero+zero midpoint**. A continuous gain envelope with mutually exclusive audible sessions necessarily reaches zero at the crossing; removing the valley requires either an instantaneous discontinuous handoff or a period of overlapping output. An abrupt switch can click when independently clocked waveforms differ; earlier 40ms/160ms overlaps audibly beat or changed timbre even with decoder clock drift within budget.

`MediaPlayer.getCurrentPosition()` / Media3 position comparisons do **not** establish sample phase at the physical speaker. Android capture of another app's playback is permission- and capture-policy-gated; `Visualizer` requires `RECORD_AUDIO`, and neither path is currently implemented or authorized. References: https://developer.android.com/media/platform/av-capture and https://developer.android.com/reference/android/media/audiofx/Visualizer . Do not claim perfect phase correlation or make new permission requests silently.

**Next technical gate:** prove a nonzero energy-floor and low-artifact cold join with a reproducible signal-level experiment and a real HONOR capture/listen, or document which controlled compromise the platform permits. Do not replace `fade(true)` with another arbitrary 40ms/100ms crossfade. Only after the whole Android test matrix, SDK36/D8 CI, signing certificate, exact APK checksum/manifest check and physical device acceptance can the original publishing branch receive a new numbered release.

**Follow-up feasibility result:** `AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md` compares the permission/capture-policy/clock limits of Android Visualizer versus user-consented playback capture. The pure-signal counterexamples are enforced by `test_handover_signal_feasibility.py`. Neither is a HONOR PCM measurement; the production manifest and cold fade have not changed.
