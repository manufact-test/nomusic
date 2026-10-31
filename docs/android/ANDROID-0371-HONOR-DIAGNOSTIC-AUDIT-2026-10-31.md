# CELIKOM Android 0.3.71 HONOR diagnostic audit — do not interpret callbacks as sound

**31.10.2026. Owner's 0.3.71 is usable, not perfect. Android-only research checkpoint. NO new audible code and NO APK.**

## Frozen production baseline

- Exact signed source: `b624d5c062a6d6310459f9bb73cf5f9014eb8a54`; Android **0.3.71 / versionCode 72**. Signature, APK SHA and build receipt: [ANDROID-0371-SIGNED-ROLLBACK-RECEIPT-2026-10-31.md](ANDROID-0371-SIGNED-ROLLBACK-RECEIPT-2026-10-31.md).
- New **do-not-modify** reference: `backup/android-0371-honor-usable-baseline-20261031` pointing exactly to the signed source SHA above. Earlier `backup/android-0369-honor-listening-control-20261031` remains untouched.
- Keep `feature/android-unified-preparation-seek-gate` and live stable at 0.3.71/code72. Only investigate/add offline diagnostics on `feature/android-0371-honor-diagnostic-audit-staging`.
- Source parity was verified: 0.3.71 audio behavior classes are byte-for-byte those of 0.3.69; 0.3.70 experimental code is withdrawn. Never reintroduce 0.3.70 passive join polling, strict detached-pause seek or post-install task cleanup as an unproven cure.

## Correct partition of the owner's private combined journal

User attachment `CELIKOM-combined-20261031-214256.txt` was read locally and **must not be committed**, including track titles, IDs, identities or full JSON lines. The file has a human-readable preamble and three `run_start` segments; counting from its first line silently incorporates older runs:

| run_start | Start line | Version | Use |
| --- | ---: | --- | --- |
| first | 4 | 0.3.69 | historical comparison, not new 0.3.71 evidence |
| second | 1811 | 0.3.70 | rejected historical comparison |
| **last** | **2652** | **0.3.71** | **sole current owner listening session** |

The last run holds 828 JSON events, roughly the first **85 seconds** of app runtime. It is an intense series of several songs and many seeks; the current sample cannot establish a long-session deterioration trend.

| Measured event subset, current 0.3.71 only | Observation | What it does NOT establish |
| --- | --- | --- |
| `replacement_seek_complete` | **41** callbacks, **12–400 ms**; six over 100ms, four over 200ms (327, 311, 400, 239), zero over 500ms | Not strictly 41 finger gestures; not time to audible output; one 327ms callback is near first attachment. |
| `source_discontinuity` | 41 events with Media3 `reasonCode=1, userSeek=true`; **35** have unchanged item index, **6** change index | Media3 SEEK includes seeking to a different item (e.g. Next), not proof of 41 finger scrubs or six real Next taps. Button observation explicitly unavailable. |
| `replacement_source_buffer` | 35 start events, **33** completed/resumed windows of **6–51 ms** | Two unmatched within this segment need not be leaks: may retire at track boundary. Short source BUFFERING does not explain all 400ms decoder latency. |
| `replacement_stream_prefetch_yield/resumed` | 30 / 29 | Asymmetric count alone cannot prove a dangling worker or broken recovery; source release/end can retire the worker. |
| `replacement_unified_join_start` | **7**, complementary linear 160ms; `phaseVerified:false`, `sourcePcmMeasured:false` | Nominal complementary gains are not speaker amplitude or alignment. |
| `replacement_decoder_advancing` immediately before each new-song join | Approximate transport drift **80–205 ms** | Media clock drift is **not** exact PCM/speaker phase or an identified cause of dips. |
| `replacement_transition_complete` | **7** linear joins with command delay 179–205ms; **34** seek-related exclusive transfers with command delay 2–30ms | Command-delay metric begins **after** decoder clock validation and does **not** include prior seek latency. This is not proof that each audible transition was 2–30ms. |
| `audio_command_anomaly` | **7** `overlap_commands` at intentional same-song joins, **0** `commanded_silence` in current segment | No physical microphone/BT capture: absence of command gap cannot exclude an audible dip/repeat; overlap command is not measured clipping. |

Cross-run context: the earlier 0.3.69 segment had 33 seek callbacks at 21–95ms (0 over 200ms), rejected 0.3.70 had 38 at 20–990ms (14 over 200ms). **These are different durations/seek patterns/networks/cache states, not a controlled A/B.** A 400ms decoder callback on restored 0.3.69 code proves the rare slow path exists independently of the withdrawn 0.3.70 changes. It does not exonerate 0.3.70's much worse owner-observed experience, nor attribute an individual audible artifact to network vs native decoder.

## Two distinct, testable risks in the existing code

**A. Seek-to-replacement temporal jump, especially with a partially cached stream.** In `ReplacementEngine` the decoder is silenced and the original gain restored during seek (`seek()` around lines 290–312); the decoder seek callback can return with a **residual of hundreds of milliseconds** (`completeSeek()` logs `residualMs`). `HANDOVER_DRIFT_MS=350` allows subsequent `fade(false)` / `exclusive_single_turn` when the *transport* clocks differ by up to 350ms. In this run at about 50.5s and 51.6s, callbacks took **311/400ms**, logged residuals **254/330ms**, then the clock gate passed coarse drifts **283/336ms** and made an exclusive transfer shortly afterward. Another slow 239ms seek around 71.3s later passed with a coarse drift of about 262ms. This creates a **plausible** retrospective 0.25–0.34s sample-position discontinuity. It is not a proven audible rewind: Media3 `getCurrentPosition` and MediaPlayer `getCurrentPosition` are transport estimates, and no waveform phase/output was measured. The 350ms threshold is pre-existing and intertwined with slow Range, fast Next and seek races; **do not simply reduce the threshold, seek again or add a timer**. That could reproduce the catastrophic 0.3.70/earlier regressions. First create deterministic source-event/decoder-clock RED replay plus an explicit fail-open contract retaining the original if confidence is insufficient.

**B. New-song join dip or repetition.** The seven `fade(true)` joins run `AudioOwnership.blendSameSong()` on **two independently presented audio sessions**: `MediaPlayer.setVolume` on replacement and `DynamicsProcessing.setInputGainAllChannelsTo` on the original session, sampled on separate paths about every 20ms. Even complementary *commanded* gains do not promise presentation-synchronous gain and waveform position, especially when track editions / source DSP / hardware paths differ. The pre-join 80–205ms coarse drift does not resolve PCM phase. A song-dependent dip, coloration, transient duplication or perceived backward motion is consistent with this architecture, **but the source waveform/amplitude and exact onset were not captured**, so no single mechanism can yet be selected. Keep a single mode and do not resurrect equal-power fade or A/B menu.

## Why our earlier diagnostic interpretation failed

1. **Don't merge runs.** `run_start` resets event time: count only the selected final version. Never use whole combined TXT or compare raw event counts without duration/seek intensity.
2. **Don't call every `DISCONTINUITY_REASON_SEEK` a finger scrub.** The six changed item indices in this run are inter-item navigation; `manualNextButtonObserved:false` means the actual tap is not observed. The official Media3 event contract covers seek-to-another-item.
3. **Don't equate `replacement_seek_complete.elapsedMs` to the audible interruption.** This measures a MediaPlayer callback interval. Additional wait for advancing decoder clock, ownership and gain output follows it.
4. **Don't evaluate `commanded_silence` from the fields attached to the event at the instant it is logged.** `AudioContinuityMonitor.observe()` starts a gap on a prior tick, then emits a finding when the gap **ends**. The logged `sourceMutedCommand` at the closing tick may be `false`; it cannot retroactively disprove the gap. The monitor samples Java commands, **not the speaker**. Conversely 0 findings do not mean perfect sound.
5. **Don't interpret `replacement_original_muted` as an immediate full mute.** `prepareSourceEffect()` initializes original gain to **0 dB**. The actual attenuation occurs in `blendSameSong()` or exclusive grant. The logged nominal fade duration is not a measured silent interval.
6. **Don't equate nominal 160ms crossfade, clock drift or `sourcePcmMeasured:false` to gain/phase correctness.** The old mistaken equation "green ownership tests = acoustically fixed" led to unusable releases. Distinguish user hearing, commanded state, native callbacks and captured output.

## Android primary references and research boundary

- Media3 playlist transitions and seek callbacks: https://developer.android.com/media/media3/exoplayer/listening-to-player-events
- `MediaPlayer.OnSeekCompleteListener`, `MediaPlayer.getTimestamp()`: https://developer.android.com/reference/android/media/MediaPlayer
- `AudioTrack.getTimestamp()`: https://developer.android.com/reference/android/media/AudioTrack (own frame presentation time is route-sensitive; not access to Yandex's PCM)
- `DynamicsProcessing.setInputGainAllChannelsTo()`: https://developer.android.com/reference/android/media/audiofx/DynamicsProcessing
- Capture restrictions: https://developer.android.com/media/platform/av-capture
- Earlier project feasibility and permissions: [AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md](AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md). Product manifest/strict release guard do not permit silently adding RECORD_AUDIO; capturing another app requires owner consent and capture policy and cannot be assumed available.

## Next disciplined engineering gate — no owner time wasted on random APKs

1. Use the new **offline** `tests/honor_journal_audit.py` on one private file; synthetic negative gates in `tests/check_honor_journal_audit.py` enforce per-run scoping, separate inter-item Media3 SEEK, retrospective command-gap interpretation and no leaking media IDs. The helper is not shipped in Android DEX and prints only aggregate counts.
2. Build a **RED/green actual-engine replay** of the partially cached slow-seek episode: source audible while decoder seeks, callback with residual 254–330ms, clock drift >200ms, no premature audible replacement grant, no extra seek spiral, genuine Next/pause/Stop/BT and prefetch unaffected. The expected safe policy needs to be selected/proven against the old regressions **before** changing `ReplacementEngine`.
3. New-song dip is separate: investigate reproducible old/join phase and DSP command skew with permission-respecting physical capture or externally recorded phone speaker when owner wants to supply one. Do not claim that an anonymous clock log can solve speaker-level amplitude.
4. Only after a demonstrated RED mechanism and passing full Android host + SDK36/D8 **on nonpublishing staging** may a release candidate be considered. No new signed APK from this audit. Production and the immutable backups stay untouched.

## Verification receipt — synthetic tests and real-report audit

- Nonpublishing staging source: `0099284e75ba9080c7a666aefb66ee50d72994ae` on `feature/android-0371-honor-diagnostic-audit-staging`.
- [Android SDK36/D8 full workflow 41231844190](https://github.com/manufact-test/nomusic/actions/runs/41231844190): **SUCCESS** for Java host regressions, release contracts, D8 compile and the new synthetic `check_honor_journal_audit.py`; `publish-stable` **SKIPPED**. **No signed APK was built.**
- The new interpreter was also executed locally against the actual private owner's three-run export. It independently selected line 2652 / 828 current events and returned 41 seek ACK (12–400ms; 4 over 200), 35 same-index vs 6 changed-index Media3 discontinuities, seven joins (80–205ms coarse drift), 34 exclusive handovers, seven expected overlap-command findings, and no commanded-silence finding. For historical runs it separately returned 33 seek ACK max95ms on 0.3.69 and 38 max990ms on 0.3.70.
- No raw diagnostic bytes, user identifiers, track names, IDs, or licensed audio were stored in GitHub. The test fixture is entirely synthetic.
