# CELIKOM Android 0.3.72 — owner HONOR listening + combined-journal checkpoint

**Date:** 01.11.2026. **Scope:** Android only. **Status:** OTA/update lifecycle ACCEPTED by owner; acoustic quality NOT ACCEPTED, practically unchanged.

## Owner's direct findings (highest priority)

- OTA installation works. After the system update, CELIKOM closes and does not remain among recent apps. **Keep this implementation unchanged.**
- After listening on HONOR, 0.3.72 sounds essentially the same as the previous reference. Any improvement is too small to be confidently audible.
- Finger seeking is smooth in some songs, while others exhibit many small jumps/repetitions. Severity is song-dependent.
- At new-song replacement attach, the familiar brief loudness dip and/or tiny repeat/rewind is still heard in some songs.
- No claim of a completed audio fix. Do not request another release just to reproduce this unchanged engine.

## Immutable architecture and release reality

- **Exactly ONE unified Android audio implementation.** No linear/nonlinear modes, hidden toggles, A/B builds, or mode-selection UI. The log field `joinMode` refers to the *internal handover path* (cold same-song blend vs verified seek re-ownership), NOT a user-selectable audio mode.
- Stable release is **0.3.72/code73**, built from production `feature/android-unified-preparation-seek-gate` release source commit `8115228aa9c10b6244166cb44fff1760f0d32f1b`. See `ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md`.
- Audio behavior is carried forward from the owner-accepted-as-usable **0.3.71/code72**; 0.3.72 changed updater version/lifecycle, not the audio engine.
- Owner's pre-release backup: `backup/android-0371-pre-0372-stable-release-20261031`. Preserve older `backup/android-0371-honor-usable-baseline-20261031` and `backup/android-0369-honor-listening-control-20261031` too.
- A seek-clock baseline experiment exists separately under `feature/android-0371-honor-diagnostic-audit-staging`, with CI validation, but **was NOT incorporated into 0.3.72**. Do not confuse its tests/claims with phone playback. Do not merge it automatically.

## Uploaded diagnostic evidence

User provided `CELIKOM-combined-20261031-235928.txt` (private in conversation; **do not commit raw file to GitHub**). Combined export holds three runs, not one: `run_start.version = 0.3.70, 0.3.71, 0.3.72` (in that order). Comparison below was computed by grouping JSON records at `run_start`; per-run windows are different and log may rotate.

| Field | 0.3.70 | 0.3.71 | 0.3.72 |
| --- | ---: | ---: | ---: |
| Logged JSON records | 841 | 841 | 747 |
| `replacement_seek_complete` | 38 | 41 | 37 |
| Decoder seek callback elapsed >200ms | 14 | 4 | 6 |
| Decoder seek callback elapsed >300ms | 9 | 3 | 4 |
| Raw `abs(residualMs)` >225ms at seek callback | 11 | 3 | 5 |
| `replacement_warm_alignment` | 4 | 1 | 2 |
| `replacement_source_buffer` | 29 | 35 | 26 |
| Cold same-song `unified_complementary_linear` transitions | 7 | 7 | 9 |
| Seek `exclusive_single_turn` transitions | 28 | 34 | 26 |

**Important**: never equate counts from different-length / different-playback sequences with proof of improvement. Current 0.3.72 run ends without `run_end` in exported segment. The 0.3.70 segment has 7 `replacement_join_clock_summary` records; the 0.3.71 and 0.3.72 segments have NONE. This is a logging/coverage difference and must be reconciled before claiming absence of cold-join drift. Do not silently map missing values to zero.

0.3.72 slow seek observations (`elapsedMs / raw residualMs`, at `replacement_seek_complete`): `360/361`, `352/316`, `226/167`, `679/633`, `393/337`, `278/248`. Some warm alignment corrections occur; many user seeks complete with no correction. These *transport-side* measurements do not identify the exact audible location of any reported skip.

0.3.72 still logs two separate audio sessions; `replacement_unified_join_start` reports `durationMs=160`, `gainLaw=complementary_linear`, `oneMode=true`, `sourcePcmMeasured=false`, `phaseVerified=false`. The current production `ReplacementEngine.java` retains `HANDOVER_DRIFT_MS=350`. The output phase, gain at speaker/Bluetooth and actual acoustic waveform are **not measured**. It is incorrect to call a 160ms envelope or <350ms media-clock drift an acoustically seamless join.

## Diagnostic validity audit — first task for next chat

1. Trace each log event to its exact production source and timing. In particular: `replacement_seek_complete`, `replacement_decoder_advancing`, `replacement_warm_alignment`, `replacement_transition_complete`, `audio_owner_state`, `replacement_join_clock_summary`, `audio_command_anomaly` and `source_discontinuity`.
2. Distinguish asynchronous seek callback time, player-reported transport position, decoder presentation time, gain commands, real source session volume, and physical audible PCM phase. A callback is not proof of audible output alignment.
3. **Do not mistake `replacement_sync.state=seek` huge drift values for ordinary playback offset**: the seek target jumps while the decoder may still be at its old position.
4. Do not interpret `source_discontinuity.reasonCode=1` alone as a manual Next; validate same track identity vs track boundary.
5. Do not count every `replacement_source_buffer` as audible glitch; Yandex can briefly buffer while the original remains the selected audible owner.
6. Find why `replacement_join_clock_summary` exists only in the older 0.3.70 journal, despite 0.3.71/72 logging cold joins; compare instrumentation and whether log omission is due to code/version.
7. Align comparable per-track event timelines, including example slow seeks above, and separately cold-join timelines. Provide a table of **observed**, **inferred** and **not measurable** phenomena; require evidence before a patch.
8. Keep one admin-only diagnostics surface if additional instrumentation is truly needed; no buttons for ordinary users and no second hidden mode. Never collect sensitive data or audio without explicit permission.

## External technical documentation (reviewed 01.11.2026)

- Official Android `AudioTrack.getTimestamp()` documentation: https://developer.android.com/reference/android/media/AudioTrack — frame/presentation timestamps may be useful when an app owns the AudioTrack, but a timestamp need not equal actual speaker presentation and must be interpreted with care. It does NOT automatically expose Yandex's private output PCM clock.
- Official Android playback capture limits: https://developer.android.com/media/platform/av-capture — `AudioPlaybackCapture` requires user `MediaProjection` consent, `RECORD_AUDIO`, matching allowed media usage and source capture policy. It **cannot be assumed** that Yandex audio is capturable or that capture yields perfectly synchronized phases; validate feasibility before proposing it.
- Existing research: `docs/android/AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md` where available on research branch. Investigate code/data permission constraints before introducing any capture features.

## Next engineering strategy (NO AUDIO PATCH YET)

- First compare 0.3.71/72 production `ReplacementEngine` with staged `SeekAlignmentPolicy` and the negative/regression history. Do not carry over a staged experiment merely because its host tests are green.
- Research Android MediaPlayer/AudioTrack output timing, Media3 callback semantics, source-output capture restrictions and HONOR-specific audio route behaviors; mark hypotheses vs findings.
- Propose a deterministic timeline model and focused RED tests which reproduce a **specific** artifact mechanism. Strongly prioritize *instrumentation validity* over adjusting 160ms/350ms or other timing constants blindly.
- Preserve working Pause, Next, Stop, seek, Bluetooth, source original ownership, background fetch, audio sessions and OTA. Android only; no desktop/web/backend/auth/catalogue changes.
- Develop on a nonpublishing staging branch; preserve signed stable 0.3.72 and immutable backups; full host regressions + SDK36/D8 required for any later change. Publish only after owner approval. HONOR listening is final acceptance.
