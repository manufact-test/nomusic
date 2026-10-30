# CELIKOM Android 0.3.61 HONOR positive QA / near-tail evidence — 31.10.2026

**Status:** first real-phone **positive** listening feedback. The user reports pause, manual seek and next-song transition now subjectively good; a possible one-off lag, one perceived overlap and perceived early/late song boundaries remain to investigate. **Keep 0.3.61 as the current accepted-in-part acoustic baseline; no runtime audio change is justified by this file yet.**

## Exact scope and provenance

- Repository: `manufact-test/nomusic`; branch `feature/android-unified-preparation-seek-gate`.
- Stable Android release: **0.3.61/code62**, published by [GitHub Actions 41141704750](https://github.com/manufact-test/nomusic/actions/runs/41141704750), native and signed-publish jobs both SUCCESS.
- Immutable APK SHA256: `2549495a5abe80462ade1fca975025dea4efdf122b93fbfe94744b7e1492383b`, size `8722505`; signing certificate unchanged.
- Backup branch pin: `backup/android-0361-honor-positive-listening-20261031` -> `3860db5b8c5fafb3afe200d47e36d56b8ae9db15`. Never overwrite/rebase the baseline.
- User diagnostic: private attached `CELIKOM-combined-20261031-021709.txt`; **do not commit raw journals**. It includes separately delimited runs of **0.3.59**, **0.3.60** and **0.3.61**. 0.3.61 begins at line 1838, contains 1102 captured JSON events, and has **no `run_end`** (export while active / incomplete run). Do not mix version statistics.

## Evidence: 0.3.61 improved the verified audio command path

| Diagnostic event/statistic | 0.3.60 | 0.3.61 |
| --- | ---: | ---: |
| Next-song boundaries | 5 | 6 |
| Boundary to CELIKOM replacement handover | 5365, 724, 549, 1069, 1883ms | 783, 1020, 637, 875, 1073, 711ms |
| `replacement_seek_complete` | 50 | 47 |
| Correction passes (`correctionPass>0`) | 6 | **1** |
| `replacement_resume_fast` | 13 | 20 |
| `replacement_resume_seamless` | 2 | **16** |
| `replacement_resume_aligned` | 5 | 20 |
| `replacement_recovery` | 1 (`stream_interrupted`) | 1 (`source_end`, at actual native end) |
| `audio_command_anomaly` | 0 | 0 |

*These are different user sessions and different durations, not a controlled equal-workload A/B experiment.* Handover timestamps are commands, not a microphone measurement. Source may be audible throughout pre-handover. Do **not** report zero overlap or zero silence as physically proven.

### Exact remaining end-of-track observations

- Outgoing native song still reported **6677, 3620, 5892, 6777ms** remaining at `replacement_outgoing_candidate`, but CELIKOM did **not** retire it at that event: `retainedUntilConfirmedBoundary=true`.
- Subsequent source player discontinuities were `reasonCode=1`, `automaticTransition=false`, `userSeek=true`, with different old/new aliases. Android Media3 defines `DISCONTINUITY_REASON_SEEK=1`, vs automatic transition 0. This is a *source-reported seek transition*, not proof that a human intentionally skipped or that the native player naturally completed. Important: source-next observer recorded `audioCommandSent=false`.
- CELIKOM then retired old decoder at verified `replacement_source_boundary`, restored original first and transferred to new replacement after **0.64–1.07s**. This wait is an ordinary authenticated resolve/stream/prepare/clock path. Do not speculate the whole interval was silent.
- There is **no** `replacement_early_completion` or `replacement_expected_tail` event in 0.3.61. The only `replacement_recovery` is `source_end` at 53.753s: logged player state source position **174568ms** / source duration **174500ms**, i.e. native end already passed.
- Two verified `replacement_bounded_tail_accepted` items have native/replacement measured lengths **232450/231096ms** (difference 1354ms) and **272700/272118ms** (difference 582ms); neither explains a 4–7s native timer difference. Existing safe policy returns original for a genuinely shorter replacement tail until the native song changes.
- One perceived physical overlap remains **unverified**: `AudioOwnership` command-level gates always retain a single output owner; diagnostics explicitly mark `hardwareOutputMeasured=false`. Do not “fix” Bluetooth/dynamic processing acoustics by looking only at event timestamps.

## Strong alternate hypothesis to test before an Android code change

[Yandex Music official help: «Плавные переходы между треками»](https://www.yandex.ru/support/music/ru/listening-and-settings/app-settings) says that **seconds before current song ends, the next song rises in volume while the previous fades, and both sound at once**. That exactly matches the user's description of 4 seconds remaining plus brief overlap. Yandex official instructions: Profile -> Settings -> «Плавные переходы между треками» OFF. Current CELIKOM journal does not expose that setting, so do not claim it was enabled.

[Android official Player docs](https://developer.android.com/reference/androidx/media3/common/Player) distinguish discontinuity reason 1 (SEEK) from 0 (AUTO_TRANSITION); the source-reported reason is not a proof of who invoked seek.

**Narrow acceptance test:** if the Yandex crossfade option is ON, temporarily disable it and let 3+ full songs finish *naturally*, without near-tail manual skips. Listen for residual cuts/overlap and export one short diagnostic. If the problem persists with option OFF and genuine automatic `reasonCode=0` boundaries, analyze exact transition windows and redesign only that mechanism with new red regression; keep all 0.3.61 pause/seek/reconnect tests hard gates.

## Regression and release rules

- `tests/TestHonor061EndTransitions.java` replays the four near-tail remaining offsets as *speculative observations*, asserts that no decoder/download/owner action occurs, then confirms that a real next-song boundary first silences and releases old output. Also tests true source end at native duration, not 1ms before.
- Full suite still requires `TestHonor059Journal`, `TestHonor060Journal`, 15 virtual hours/300 song changes, Media3 boundary arbitration, actual Android D8/source provenance and audio ownership.
- **Do not advance release version** for this QA/test/documentation change. `release-spec.json` remains `0.3.61/code62`; existing Hostinger stable APK bytes remain immutable. Automatic publisher version gate must skip any same-code deployment.
- No modifications to desktop, extensions, source catalog, API, Ads module, signing, Hostinger, or playback engine.
