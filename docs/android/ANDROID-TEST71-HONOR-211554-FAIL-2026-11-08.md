# CELIKOM Android — HONOR Test.71: rejected; Dym BUFFERING and stale media item after Back
**2026-11-08. Owner verdict:** Test.71 is **NOT ACCEPTED**. Native Yandex pause/seek has no improvement; previously working problem-track → problem-track transition regressed. Do **not** use Test.71 as a base for audio logic or release it as stable.

## Evidence
- Local owner-uploaded combined log: `CELIKOM-combined-20261108-211554.txt`, 895223 bytes, SHA-256 `55b6bde5d1f8bc9cb1ef5ce152d5c2f57b55a8d3bfea798a9a4d88cef78399bb`.
- Screen recording: `SVID_20261108_211432_1.mp4`, 37200585 bytes, SHA-256 `cb68a883bd532662691c7572e2cba57139017b2933fe24cd97f497091f52732e`.
- Combined log contains historical Test.69 and Test.70, then **Test.71 from 2026-11-08 21:13:52+03, 1019 events, total ~105 s**. All timestamps below elapsed from this fresh Test.71 run; video begins at a different time.
- Test.71 originally built/signed from source SHA `e620fbc05425e87574a2150bb174ae9641d8da92`, CI [42508087622](https://github.com/manufact-test/nomusic/actions/runs/42508087622) SUCCESS; CI **does not** establish Android phone acceptance.

## Confirmed Test.71 chronology
- **t=55.85 s:** Yandex Media3 alias `866` resolved as RASKOL «Нас не понимают вообще», track `42884423`; CELIKOM successfully prepared and handed over replacement at ~t=57.66.
- **t=57.00 s:** new Test.71 `native_transport_legacy_retry` executes exactly once. `legacy_position_source_unavailable / browser_connect` returns at t=57.06. Separate status `native_transport_witness_unavailable` is logged for RASKOL. No `native_transport_witness` (successful samples) or `native_transport_fail_closed` (guard triggered) occurs **anywhere** in fresh run.
- **t=83.21–83.27 s:** transition to «Дым», Media3 alias `929`, catalogue ID `39949113`, duration **219660 ms**. For a moment Yandex reports READY/isPlaying, then publishes BUFFERING=2, isPlaying=false and position zero, playWhenReady=true.
- **t=83.40–84.06 s:** CELIKOM backend successfully resolves `39949113` and prepares alternative audio. This is **not** a catalogue-missing or backend denial case.
- **t=86.31–95.16 s:** Yandex remains in BUFFERING; `source_controller_buffering_retained`; no READY transition before user skips. CELIKOM keeps replacement silent and publishes `Яндекс не обновляет трек · играет оригинал` at t=89.57. This matches owner's report: Dym does not play. Because the second observer could not connect, this change is **not** explained by a `native_transport_fail_closed` event. A causal link between one extra MediaBrowser retry and the subsequent Yandex stall is **not proven**.
- **t=95.16 s:** Next moves to «Розовое вино», alias `978`, track `69125202`, duration **246810 ms**; native READY resumes and replacement handover completes at t=96.64. Owner then presses Back to Dym in official Yandex UI.
- **t=103.46–103.55 s:** central identity-contamination evidence. Media3 still claims alias `978`, title «Розовое вино», artist «Элджей, FEDUK», album `11530439` but `MediaController.getDuration()` changes from **246810** to **219660 ms** — exactly the preceding Dym duration. Source code combines `getCurrentMediaItem()` metadata with `getDuration()` in a single `PlaybackSource`. Since duration participates in `PlaybackSource.key`, this contradictory snapshot looks like a new track, causes `source_track_transition` with **previousAlias=nextAlias=978**, releases replacement `69125202`, then `hybrid_identity no_unique_candidate` because RoseWine catalogue duration is 246810, not 219660. CELIKOM incorrectly says `Нет одобренной версии · играет оригинал`. Video shows the official Yandex UI on Dym around this point while remote CELIKOM source remains RoseWine. This is stale/mixed cross-field controller state, **not evidence that Dym has no replacement**.
- The final audio heard cannot be independently identified from transport logs: replacement is revoked, and owner reports hearing the subsequent song.

## Comparison with Test.70
Latest Test.70 run in the same combined file shows normal RASKOL→Dym transition: RASKOL alias 722, Dym alias 785 at t=69.3, replacement transition completed at t=72.0, no prolonged initial buffering in that run. The runs differ; this is **a real behavioral regression** but not a controlled proof that one specific added observer call directly caused the native Yandex buffering.

## What NOT to do
- Do not interpret Media3 `getCurrentPosition()` or separate MediaPlayer `getTimestamp()` as actual Yandex PCM/audible output.
- Do not trust a mixed `getCurrentMediaItem()`/ `getDuration()` sample across a track transition. No replacement/identification based on contradictory metadata.
- Do not use Test.71 guard as successful evidence: new legacy state source **was never available**.
- No repeated Yandex transport commands, shadow pause/seek buttons, forced reconnect during live BUFFERING (historically SecurityException loop), permission requests, root or changing official app.
- Do not change stable Android 0.3.92, OTA, server, desktop projects or prod.
 
## Safe next action
1. **Rollback to Test.70** (isolated Android test package; installing lower versionCode requires removing Test.71 first, so CELIKOM Test sign-in/data may need restoring; do not clear Yandex data).
2. New candidate must start from the **Test.70 sound/source branch**, not Test.71. Do not carry over `NativeTransportWitness` or its one-shot `connectLegacyPosition` retry.
3. First reproduce the mixed Media3 snapshot in a host regression using the exact sequence: `Dym 929/219660 (BUFFERING)` → `RoseWine 978/246810 (READY)` → Back user-visible Dym while Media3 still emits `978/RoseWine` but `duration=219660`. Fence this snapshot **before constructing/updating `PlaybackSource`**: with contradictory item metadata vs duration, do not produce an ID or mark the song missing. Hold old source safely or restore original; don't play stale replacement. Use event + matching item/metadata to release fence, not arbitrary time.
4. Investigate authoritative source identity and actual playback state separately, without assuming a rootless non-privileged PCM hook. A transient Media3 stall from the Yandex app must not create a false claim of missing CELIKOM replacement.
5. Run complete regressions + CI signed **new** candidate only after a demonstrable causality/guard; validate on HONOR; keep Test.70 available as rollback.

**Result:** Test.71 = **failed on device**, even though native CI and APK signing passed.
