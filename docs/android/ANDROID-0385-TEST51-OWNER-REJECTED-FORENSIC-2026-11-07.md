# CELIKOM Android Test.51 — owner rejected after HONOR 50 phone replay, 2026-11-07

## Exact captures
- User uploaded combined log: `CELIKOM-combined-20261107-121857.txt`, **latest** Test.51 run starts at line 2315 and `2026-11-07T12:17:04+03:00`, ends ~108.83s; earlier embedded Test.50 runs are not part of this new trial.
- User uploaded `SVID_20261107_121716_1.mp4`, ~84.8 s video recorded with official Yandex Music on HONOR 50 Android 13.
- Owner: "С отвалами ничего не поменялось ... теперь ещё хуже ... ищет оригинал ... Толер ... RASKOL ничего не поменялось". **Test.51 rejected by owner**, irrespective of CI pass.

## Facts from latest Test.51 log
- Media3 source controller connected at elapsed 0.056s; **one successful connection attempt only**, and remains `controllerConnected:true` to last heartbeat at ~106s. No `source_controller_refresh`, no `source_controller_quiet_buffering_observed`, no `media3_connect_result.connected:false`, no `network_lost`, no `replacement_recovery`. Thus the special quiet-BUFFERING reconnect path targeted by Test.51 **was not exercised**. DO NOT claim the prior Test.50 3s detach bug fixed on phone; neither claim this current "original" message is an actual disconnected Media3 session.
- At elapsed 34.364s the app pre-requests album `26101881` for upcoming **«Толер», ChipaChip, Лёша Стелит**; Yandex Music album API returns **HTTP 451 REGION_RESTRICTION** at 35.800s. Source track enters at 36.711s with source alias `68`, duration 174500 ms; `hybrid_identity.decision.method=NONE`, `no_unique_candidate`, no own/learned catalog match. Therefore CELIKOM **fails closed and plays original**. Notifications/status may read like "Определяем песню". That is a song identity / region restriction problem, not source connection failure. All other available next-album/resolve operations in this run generally succeed; don't conflate.
- **RASKOL «Нас не понимают вообще»**, album `5685525`, canonical track `42884423`, enters at 76.047s and CELIKOM replacement transitions complete at 78.126s. Video shows paused triangular button (~76s video timestamp) but replacement continues, while Media3 reports `isPlaying=true` and `playWhenReady=true` throughout later source snapshots. No trusted pause command is published via existing official no-extra-permission Media3 observations. User-reported Pause is still broken, confirmed. Cached decoder seeks at elapsed 81.761, 86.133 and 95.606s acknowledge in **78, 57, 48 ms** *after Yandex publishes the new position*. This does not measure UI-touch-to-publication delay. User-reported slow seek persists. Do not change decoder seek path (owner-approved frozen fingerprint), no speculative pseudo-command synthesis.
- Local Yandex observation + all other playback transitions mostly retain connection throughout. CI for Test.51 passed, but **phone acceptance failed**. Do not equate green CI with fixes for Pause/Seek/identity.

## Correct next decision
1. Exact frozen owner-approved Test.50 source commit `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`, tree `bbdf43d78e04c6dc4562c5b0541049283f9109b0`; permanent branch `backup/android-test50-exact-source-owner-accepted-20261106`. Test.51 branch commit `e67fae931dc15baceb9822b21a4aebf895f4a5a4` is **rejected, never merge or publish stable**.
2. Tell owner to revert to Test.50 if they wish, but warn Android blocks lower-version app over `0.3.85-test.51`; test-package uninstall first, then install Test.50 from **Library**, may lose test app local settings/login (not stable app).
3. For album 451 region restriction, never bypass region policy, never derive replacement authorization from ambiguous metadata and never claim a missing track exists. Future UX improvement may explicitly say "Оригинал — не удалось однозначно определить трек" and retain healthy Yandex connection. Diagnose backend catalogue freshness separately; do not alter identity safety to paper over the issue.
4. On Pause/Seek, current no-permissions passive Media3 signal is insufficient. Seek callback speed is not touch latency. Any future approach needs a confirmed authoritative transport signal via supported Android API and user-acceptable permission model, not a change to audio crossfade/timing/seek thresholds. No new APK until causally supported fix exists.

## Prior related frozen resources
- `docs/android/ANDROID-0385-TEST50-FROZEN-ETALON-ROLLBACK-2026-11-06.md`
- `docs/android/ANDROID-0385-TEST51-TRANSPORT-CONTROLS-FORENSIC-2026-11-07.md`
- `docs/android/ANDROID-0385-TEST51-VIDEO-DIAGNOSTIC-2026-11-07.md`

No engine/source/Hostinger/stable changes in this forensic documentation step.
