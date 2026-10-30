# CELIKOM Android 0.3.61 / code62 — HONOR 0.3.60 evidence-led correction · 31.10.2026

**Status:** candidate for real-phone evaluation; **not acoustically accepted**. This work only changes the Android native companion and its Android tests/version metadata. Desktop CELIKOM, backend, catalog, ad protection, Hostinger hosting/signing workflows are untouched.

## Evidence from attached HONOR 0.3.60 diagnostic

User file `CELIKOM-combined-20261031-004240.txt` was read privately and **not committed**. Third run in the combined file: 0.3.60, 817 events in 112.349s. 50 `replacement_seek_complete`, 42 output handovers, five verified next-track boundaries. Boundary-to-command-handover latencies: **5365, 724, 549, 1069, 1883ms**. Manual seek at 93.287s -> command handover at 94.034s: **747ms**. Decoder seek times reached 583ms. These are command/journal timings, **not Bluetooth speaker recordings**; `hardwareOutputMeasured=false`.

Three independent causes were isolated against the production source:

1. **User pause repeatedly triggered decoder seek.** Retained same-session, same-track pause offsets of 126/132/238/299ms exceeded `PAUSE_ALIGN_TOLERANCE_MS=85`, although the existing verified handover budget is 350ms. A seek/fade chain then recreated the audible delay. The first new red host replay `TestHonor060Journal.pauseRetainsDecoder()` failed on the unmodified 0.3.60 code in GitHub Actions **41141010547**.
2. **Network seek often triggered a needless second seek.** First-pass streaming completion at residual 204ms exceeded a special-case 80ms cutoff even though `HANDOVER_DRIFT_MS=350` is permitted. The old `TestStreamingEngine` expected another seek on a 179ms residual. Streaming completion now corrects only when residual exceeds 350ms; 540ms, 3s/1.8s residuals still require bounded inaudible correction/fallback.
3. **Transient Media3 reconnect canceled the cached audio transport.** During the 5.365s track transition the journal recorded `replacement_source_wait`, then `stream_prefetch_wait`, `stream_interrupted`, re-resolve and re-prepare. `ReplacementEngine.current(key)` became false for a brief `owner.current=null` snapshot, and `BufferedAudio` transport watcher closed the stream, even though `ReplacementEngine.update(null)` had a 1500ms retention grace. Audio bytes now use an independent **same-song/generation/account** transport lease, while every audible output grant continues to require a live current source/owner ticket. Confirmed track boundary, account change, STOP and service shutdown revoke the lease immediately.

## Change scope and safety

- `addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java`: use retained position with existing 350ms budget on **verified** same-track user pause and headphone-route return; source jumps/stale seek callback retain stricter checks. No new audio owner/controller/timer. Keep source owner and exclusive handover ordering.
- The 350ms residual threshold is common to streaming seek completion and handover gate; any greater drift still synchronizes or falls back to the original without audible mixed sessions.
- `api.stream` and `api.download` transport lifetime is fenced by generation, accountGeneration, identity, signed-in status, service and stop, but not by transient source `connected` snapshot.
- Updated `TestHonor059Journal`, `TestResumeClock`, `TestAudioOwnershipRegression`, `TestStreamingEngine` previous expectations that **mistakenly encoded audible delay as success**. Existing large-offset/headphone/identity/account/seek safety tests remain.
- New `TestHonor060Journal` covers four pause drifts, 204ms seek correction, transient Media3 snapshot, confirmed boundary and account revocation. `check_audio_architecture.py` fails if these defects are reintroduced.
- Baseline backup: `backup/android-0360-before-latency-fix-20261031` at `9f8d651b86318b5b8ec73b01487206fbfe96c40f`.
- Red regression commit `736b5f5599fd96b2fe5cf60373f153ab4c96267b`; Android fix commit `806d3df0b95e1f18487ec25448bf902e43e2095f`. Follow-up commits preserved route/headphone behavior and negative architecture gate.
- Initial legacy test failures on the feature branch revealed expected regression behavior (reseek at 206/220ms); correcting these tests did **not** remove coverage for genuine jumps or stale callbacks.

## Verification and release conditions

- Code-checkpoint Android Actions: https://github.com/manufact-test/nomusic/actions/runs/41141555854 — **SUCCESS both jobs**, Android host tests, Android API36/D8 compile and isolated build source/provenance artifacts..
- This release bumps `release-spec.json` and `AppVersion.java` to **0.3.61/code62** and updates the pinned negative version tests. Auto-publish checks `stable.json` versionCode, builds with the existing pinned signed source, and publishes only on full Android CI success. Do not configure a second upload path.
- Same permanent in-app updater and public distribution endpoint: https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/ ; the user should use the built-in **Проверить версию** button.
- **Device acceptance is still mandatory.** HONOR NTH-NX9 / Android 13 tests should include: pause/continue (short and long), 3 manual scrubs, 3+ transitions, Bluetooth/headphone route interruption, and a single fresh diagnostic. Observe whether audible gaps and duplicate seeks actually improved. `hardwareOutputMeasured=false` is not proof of acoustic silence or its absence.
- No proof yet that MediaPlayer network seeks themselves are faster; official Android guidance notes `seekTo` is asynchronous. A future targeted cache/preload investigation may be warranted if the measured long-tail remains, but do not migrate players blindly.
