# Android 0.3.75 — HONOR bounded WARM callback latency (2026-11-01)

## Immutable recovery points

- Accepted old 0.3.72: `backup/android-0372-ota-accepted-before-transport-diagnostics-20261031` at `5e18fd070dbf6115f643079b03637b0d180e9665`.
- Accepted diagnostic 0.3.73: `backup/android-0373-honor-passive-transport-before-sync-guard-20261101` at `40bb482fdd60a35a4d65a0b700df3ec375aef3c5`.
- Published experiment 0.3.74: `backup/android-0374-honor-strict-gate-before-warm-latency-20261101` at `3e859ab17f8fc3b1c6d40800022d797fd69f70be`.
- Do not mutate any backup. Installing a historical APK over 0.3.75 requires reissuing its code with `versionCode>76` and the same signing certificate.

## Observed regression, not a speculative tuning preference

HONOR NTH-NX9, Android 13, owner `CELIKOM-combined-20261101-115648.txt`, 0.3.74 run at 11:55 +03:00:

- 9 cold joins, 26 same-item scrubs; 35 gated handovers; 37 original ALIGNMENT seeks plus **24 additional WARM seeks**; 20 handovers used WARM correction, 4 of those needed TWO warm corrections.
- All 35 strict transport gates passed, no `replacement_join_guard_fallback`. This did **not** mean acoustic playback was good: the owner heard substantial forward/back jumps and variable cold joins.
- 24 WARM ACK callback delays ranged **40–155ms** (median around 63ms). The prior estimator mistakenly used the earlier ALIGNMENT ACK delay `+40ms`, up to **250ms**, to target a **different** WARM seek. Slow ALIGNMENT can include network range wait and is not representative of WARM.
- All but one WARM ACK had replacement decoder **ahead** of the projected original (`rawResidualMs` **-177 to +6ms**); 5 were more than 100ms ahead.
- `Крылья`: ALIGNMENT ACK 207ms, lead chosen 247ms; WARM ACK 146ms, projected residual -102ms. Another scrub: ALIGNMENT 254ms, lead 250ms; WARM ACK 76ms, projected residual **-175ms**, followed by a second WARM correction. Other double corrections occurred on `Монпасье` and `Метамир`.
- The 9 cold-entry blend windows had source/decoder transport drift within roughly -74..+79ms, but matching transport counters is **not** proof of PCM or speaker phase alignment. Measured source/replacement durations differed up to 1354ms on one track, which may indicate legitimate different encoding/intro/outro trim; do not assume PCM-identical audio from matching metadata.

## Single-scope change in 0.3.75

- Use a fixed 70ms lead for WARM seeks, bounded to the measured WARM callback distribution, **independent of the previous ALIGNMENT ACK**. Do not use 250ms lead on an 80ms callback.
- Preserve exactly one audio mode, the 100ms stream join gate, max two muted corrections, 3s join deadline, the original-song restoration and all account/route/Next/pause fences.
- Preserve 0.3.74 diagnostics and add a `predictor=warm_callback_fixed_70ms` field to `replacement_warm_alignment`.
- Explicitly **do not** claim perfect acoustic phase or solved cold-transition loudness. Android `MediaPlayer.getCurrentPosition()` is a media timeline position; precise speaker signal timing requires different evidence. No audio bytes captured; no extra permissions or buttons.
- No changes to website, backend, user auth, updater interaction, diagnostic UI, unsupported A/B modes, or signing identity.

## Validation and next listening test

- Real-engine tests replay ALIGNMENT ACK 207/254/179ms followed by observed WARM 76/40/155ms and require **one** muted WARM seek, no second overshoot, with the same effect and decoder.
- Retain historical 0.3.74 strict-gate, asynchronous seek, buffering, source-boundary, local cached seek, pause, stale-callback and signed release negative regressions.
- Staging Android API36/JDK17/D8 build must pass and skip stable publication. Only then fast-forward guarded production; online publisher must verify stable manifest 0.3.75/versionCode76 and old signing cert `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Owner should test the same songs and send a new report; **do not interpret green host tests as a listening verdict**. A short external audio recording with approximate song/time would materially help measure the audible jump.
