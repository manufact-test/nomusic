# CELIKOM Android — Test.19 rejected, Test.20 bounded transport-clock recovery (2026-11-04)

## Immutable baseline and release safety
- **Accepted Test.18**: backup `backup/android-0385-test18-best-owner-20261103`, SHA `1a19ccec674d41b7417f29715d853eb693595687`, signed ZIP https://github.com/manufact-test/nomusic/actions/runs/41704016656/artifacts/13265222571 . Preserve and use as one-click rollback.
- **Production 0.3.85/code86** unaffected. Production package `pro.celikom.nativeprobe` and OTA/publish pipeline unchanged.
- **Rejected Test.19** functional `39c4abf5c369772adc9f8864fe546b8df7c75642` (CI 41719786549). No promotion. Its transient DSP `source_effect_next_track_recovery` behavior is completely absent from Test.20.
- **Test.20**: independent installation `pro.celikom.nativeprobe.test`, update over Test.19, version `0.3.85-test.20/code86105`, signed ZIP built only after full CI; source branch `feature/android-0385-test15-permissionless-recovery-20261103`. No extra permissions, no second listener/controller, no parallel audible owner.

## What the user's latest diagnostic *actually* shows
File `CELIKOM-combined-20261104-110556.txt` has **three captures in one attachment**: Test.18 run A up to line 2186, Test.18 run B 2187–2972, Test.19 from line 2973. Compare runs explicitly; avoid blaming features introduced only in Test.19 for events already present in Test.18.
- Test.18 run A: 50 joins, 19 lookahead decoder primes, one `replacement_drift_unstable` (10AGE “Пушка”, track 85025192) at source 23010ms, drift 851ms. Test.18 run B: 18 joins, 5 primes, zero drift fallbacks.
- Test.19: 15 joins, 7 primes, two `replacement_drift_unstable` fallbacks. (1) “Пушка” 10AGE, track 85025192, ~1034ms drift at +8936ms of source. Exclusive join initially measured ~37ms; drift already ~931ms at earlier sample. (2) “Старые фото”, track 107389859, ~747ms drift at +6704ms. Exclusive join initially ~67ms; drift already ~707ms earlier.
- **Not one** `replacement_original_mute_failed` or `replacement_source_effect_next_track_recovery` in Test.19. The new DSP code was not exercised in the recording and therefore did not fix or cause these documented drift stops. Regression in RASKOL / Dym auditory scrubbing must be treated seriously, but transport ACK alone proves only the decoder command, NOT that the intended replacement reached speaker.
- Test.19 RASKOL track 42884423: seek ~188655ms from source, own `replacement_seek_request`, accepted ACK and completion, follow-up join. Dym track 39949113: user scrub requested ~186146ms, seq16 accepted and completed with 69ms residual, joined, later observed ~180ms transport drift. The user still heard incorrect playback in both. Screen recording is not frame-locked PCM evidence. Test.18 user had reported Dym finger scrub better; this perceived improvement was lost in Test.19.
- Zero proof from logs that a song has a defective replacement file. Do **not** invent track-specific patches. Investigate systematic timeline versus effective decoder/output.

## Found code-level gap, Test.20 hypothesis
In accepted Test.18 `ClockSupervisor`, a sustained drift in the **700–1500ms** range always selected `RESTORE_SOURCE` after 1500ms; only a **>1500ms** severe gap qualified for a correction after 500ms. Thus repeated medium-magnitude drifts go directly to user-visible “Большой рассинхрон замены — играет оригинал до следующей песни.” The observed 851ms, 1034ms, 747ms fallbacks fit this deterministic code path. This is a gap in the fallback policy, not proof of the ultimate source of the decoder mismatch.

Test.20 restores the **exact Test.18 audio engine, runners, harness and build workflow** before one tightly scoped change:
1. For live aligned source where drift exceeds 700ms but not 1500ms continuously for 750ms, allow **one** existing silent original-audible decoder `seek()` realignment per track, reusing the verified AudioOwnership seek/ACK path. Severe >1500ms existing one-correction policy retained.
2. If drift persists after that correction for a new 1500ms confirmation window, **restore original** and stop replacement until next song as before. Single bounded allowance shared by moderate and severe drift and **not rearmed on a transient single healthy (<700ms) sample**; it resets only on track/safety reset.
3. Log passive MediaPlayer output timestamp snapshots before medium correction and original fallback (`replacement_output_clock_sample`, stages `sustained_drift_before_bounded_realign` and `sustained_drift_restore_original`) and a `replacement_bounded_drift_realign` event, without changing output timing.
4. Add deterministic host tests: 550ms jitter unaffected; medium drift one seek; persistent moderate fallback; healthy sample cannot rearm budget; previous severe, user seek, pause tests retained.
5. Unmodified: cold join, no new independent observer, lookahead prime, user finger seek selection, seek ACK/hash, prewarm, DSP source muting and stable core. In particular, do not claim the root cause of decoder drift has been fixed until phone listening confirms it.

## Owner regression run after installing Test.20
1. Confirm **separate CELIKOM Test** icon and package; accepted original is still installed unchanged. Use signed Test.20 archive only after CI passes.
2. In Yandex, play Pушка (10AGE) and Старые фото: do they maintain replacement beyond the prior +7–10s threshold? Any `replacement_bounded_drift_realign` followed by clean rejoin? If it falls back, note song/time and do not retry countless times.
3. Finger-scrub **Раскол** and **Дым** separately; test play/pause on Dym later (previous Test.18 pause button was not verified). Listen for replaced versus original audio, not just moving time.
4. Audit abrupt-note first syllables on Триагрутрика / Джоннибой (quality may be unchanged — Test.20 specifically targets mid-song drift).
5. Test ordinary automatic song transitions; opening admin and approving a track while another plays must remain smooth per later stable acceptance.
6. Export combined diagnostics with video once at end. If worse, reinstall accepted signed **Test.18** and report Test.20 rejected. Preserve new log before rollback when practical.

## Evidence limits
Media3 source timestamps + MediaPlayer timestamps can show **transport** alignment, not microphone output or Bluetooth speaker PCM. A prior seek accepted status is not an acoustic guarantee. Further work should correlate source position sample freshness, decoder motion, seek actual audible effect, and lookahead activity **without a second independent audio owner**. No instrumentation requiring consumer-facing accessibility, notification-reader, ADB, or extra permissions.
