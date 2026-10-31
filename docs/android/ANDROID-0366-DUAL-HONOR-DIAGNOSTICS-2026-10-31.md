# HONOR Android 0.3.66 — two on-device diagnostics, seek buffering replay

**Date:** 2026-10-31. **Scope:** Android audio only. **Status:** host fix verified, **physical sound NOT accepted**. A subsequent, independently verified signed 0.3.67 test release is documented in [`ANDROID-0367-SIGNED-HONOR-SEEK-BUFFER-2026-10-31.md`](ANDROID-0367-SIGNED-HONOR-SEEK-BUFFER-2026-10-31.md); the original technical audit preceded that release.

Read with `ANDROID-0366-ONE-APK-ADMIN-AB-2026-10-31.md`, `REGRESSION-GATES-2026-10-29.md` and `AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md`.

## Test input and comparison boundaries

Two locally supplied HONOR diagnostic files are **private and must not be committed or uploaded**. Each is a combined multi-run journal; counting its earlier 0.3.64/0.3.65 records as new evidence would be a critical error.

| Report | Selected 0.3.66 run | Device observation |
| --- | --- | --- |
| `CELIKOM-combined-20261031-151355.txt` | `run_start`, file line **1579**, 15:12:14 (+03:00) | Default **exclusive 500ms dip**; scrubbing and Next subjectively good, cold join still noticeably sags (~30% perceived, **not instrument-measured**). |
| `CELIKOM-combined-20261031-151722.txt` | `run_start`, file line **1558**, 15:15:24 (+03:00) | Admin **correlated linear 160ms lab** selected at run `elapsed_ms=14746`; some cold joins subjectively seamless, others audible, while scrubbing/Next subjectively jumps/lags. First song in this run joined with default mode *before* admin selection. |

The runs play **different collections of songs** (only one track ID overlaps, without comparable finger-seek series). Thus differences in seek performance cannot be attributed exclusively to the mode from these two logs. The command monitor cannot certify acoustic output or Bluetooth timing.

## Measured events (only selected 0.3.66 runs)

| Event | Default run | Admin linear run |
| --- | ---: | ---: |
| `replacement_sync` with `state=seek` | 37 | 29 |
| `replacement_seek_complete` | 37 | 29 |
| Same-alias Media3 position discontinuities | 31 | 21 |
| Confirmed inter-item boundaries | 6 | 7 |
| `replacement_transition_complete` after seek, `exclusive_single_turn` | 30 | 21 |
| Cold entry `exclusive_volume_dip` | 7 | 1 (before mode change) |
| Cold entry `admin_correlated_linear_lab` | 0 | 7 |
| `replacement_source_buffer` | 24 | 23 |
| `replacement_sync` with `state=buffering` | 5 | 14 |
| `replacement_resume_fast` | 6 | 15 |
| `audio_command_anomaly`: commanded silence | **0** | **0** |
| `audio_command_anomaly`: intentional overlap | 0 | 7, each reported duration 0ms |
| Median decoder-advancement gate `waitMs` (all joins and seeks) | 105ms | 84ms |
| Median absolute advancement `driftMs` (all joins and seeks) | 72ms | 46ms |

The last two aggregate metrics **do not support** claiming a slower decoder or larger measured drift in linear mode. All seven lab overlap reports are software command-state flags, **not seven measured audible artifacts**. There is no evidence that a linear 160ms overlap is run on finger seeks: those complete as `exclusive_single_turn` in both modes. There is also **no observed repeated 500ms dip after a scrub**.

Media3 records a discontinuity with `reasonCode=1` across some changing media-item indices. That is a true inter-item boundary (not an ordinary same-track seek), but the log explicitly says `manualNextButtonObserved:false`: user intent behind every track change cannot be inferred solely from the callback reason.

## Confirmed transport race

Representative *linear-run* seek at `elapsed_ms=20971` (`source_discontinuity`, same item), with events in actual order:

1. **20977** — `replacement_sync:seek`: replacement silent, original gain restored.
2. **21012** — asynchronous native `replacement_seek_complete` (38ms). **21016** — muted decoder starts, clock handover pending.
3. **21025** — Media3 switches to a very short `BUFFERING` frame **after** the decoder seek callback; **21031** — `AudioOwnership` enters `PAUSED`, cancels the pending muted handover and pauses the decoder.
4. **21044–21049** — source becomes READY, `replacement_resume_fast`/`replacement_resume_aligned` and a **second decoder start** occur.
5. **21131–21139** — replacement clock validates and a new instantaneous exclusive handover completes.

This event ordering occurs repeatedly in the linear run. The 0.3.66 `bufferSource()` special case held short buffers when an already **audible** replacement was stable, or while a native decoder seek was in flight. It did **not** hold short buffers after that callback while a **silent** decoder was awaiting a verified clock. It therefore manufactured a second PAUSE/RESUME transaction for one physical seek. This is a demonstrated *mechanical bug*, not a claim that every subjective jump originates here. Similar transitions occur less frequently in the default run.

### Red/green regression and narrowly scoped fix

New `TestHonor066SeekBufferReplay.java` drives actual `ReplacementEngine` with partial-stream fake, reproducing `seek -> native callback -> silent streaming handover -> short Media3 BUFFERING -> READY`, for **both** cold-join mode selections. On unchanged 0.3.66 it **failed** because a short buffer set `pausedAt` and cancelled handover. After the fix it **passes**:

- `bufferSource()` recognizes the existing **silent, current, still-awaiting-clock handover** with the original at full gain and retains that transaction through the existing short-buffer window; it does not start a second PAUSED transaction.
- The pending clock-validation runnable continues to wait through the short BUFFERING state and proceeds when the real source resumes. It still verifies drift and keeps the replacement silent until grant.
- New event `replacement_muted_handover_buffer_hold` records this exact case once per buffering episode; it does not log waveforms, audio, credentials or original metadata.
- The pre-existing buffer timeout/pause path is retained for longer stalls. A **genuine user pause** interrupts immediately, and **Next/track boundary** retires the old decoder and all stale callbacks.
- No new fade duration, mode switch, `RECORD_AUDIO` permission, backend modification or PCM phase inference was added.

The full local Java/fake Android host suite, architectural ownership checks and synthetic waveform tests passed, including **24 new replay assertions**. Local SDK36 is absent; full Android SDK36/D8 and release-contract checks still require the non-publishing CI gate. Host tests **cannot** prove elimination of the reported speaker stutter; on-device comparison remains mandatory.

## Cold join remains an independent acoustic problem

For seven experimental linear cold joins, `replacement_decoder_advancing` reported approximate source/replacement transport drift **82–218ms** before blend. This is *not sample phase*. `phaseVerified:false` and `sourcePcmMeasured:false` are logged explicitly on every lab start. Some user-reported seamless joins are plausible, but the same complementary linear gains can constructively/destructively interfere on other masters or offsets. The exclusive 500ms envelope, conversely, necessarily reduces audio energy at its zero-overlap midpoint. Neither can be honestly declared universally seamless from these logs.

**Do not automatically enable the lab as the default** or present the short-buffer fix as a solution to track-dependent cold-join sound. For an actual clean cold join, phase/output-path measurement or another proven single-owner acoustic approach is needed; Android Yandex PCM capture and permissions have unresolved restrictions (see feasibility document). Never use unauthorized capture or weaken existing audio ownership gates.

## Next gate before another signed production APK

1. Run Android SDK36/D8 tests and signing/release checks on a **non-publishing staging branch**, with the new regression active. Keep all other products unchanged.
2. Confirm the intended hybrid behavior by physical HONOR playback of the **same tracks in both modes**, with comparable cached/partially loaded seeks: natural song → manual Yandex Next → several finger seeks → natural successor → several seeks, plus pause/resume, Bluetooth, Stop, route loss and slow buffering. Compare command logs with what was actually heard.
3. Capture only consented *speaker-level* examples of seamless/bad cold joins when feasible, with song/time/event annotations, to distinguish blend phase/loudness from transport callbacks. Do not upload source songs or raw private diagnostics to GitHub.
4. If both seek and cold-join listening gates are acceptable, prepare **one** original-certificate-signed updater APK. Until then 0.3.66 remains the on-device control; no claim of final audio acceptance.
