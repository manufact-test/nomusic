# CELIKOM Android Test.67 — HONOR 50 real-run analysis (2026-11-08 17:51)

## Evidence and scope
User-supplied local **CELIKOM-combined-20261108-175130.txt** (do not commit private trace; contains three distinct runs), paired screen recording **SVID_20261108_174955_1.mp4** (81.73s; do not commit). Three runs:
- Test.65 begins 2026-11-08T16:46:54+03:00, 1244 JSON events; HISTORICAL.
- Test.66 begins 2026-11-08T17:19:19+03:00, 1131 events; HISTORICAL.
- **Test.67 begins 2026-11-08T17:49:40+03:00**, 1171 events; ONLY run used for new diagnosis.

Test.67 source is pinned **afb6124c495fb4f28959fe44f105c099f28621bd**, Android `0.3.85-test.67` code 86153, signed Library APK at `/CELIKOM/Android/Test/CELIKOM-Android-0.3.85-TEST-67-HONOR-TUNING-SIGNED.apk`. User's physical verdict: all nonproblematic tracks generally good; RASKOL pause and audible seek still delayed 3–5 sec; consecutive troublesome tracks now seem to connect instead of stopping; known-next is good, random current selection visibly slower.

## Observed speed
14 unique album observations: 13 unique current replacement joins plus one approved-catalog NO_MATCH original ("Он рядом"). `replacement_transition_complete` appears 15 times due to 2 later reacquisitions; **do not miscount as 15 different songs**.
- 13 unique joins: **median 802ms**. Test.66 12 unique joins median 691.5ms but different songs/conditions, NOT a controlled regression or performance claim.
- 9 reused/prepared lookahead tracks, median **720ms** (range roughly 400–1238ms). 4 non-reused/cold tracks, median **1658.5ms** (1262–2481ms).
- Random/unprepared: «Легенды (feat. 5Плюх)» **2481ms**, RASKOL «Нас не понимают вообще» **1670ms**, «Дым» **1647ms**. Next-aware examples: «Старые фото» 400ms, «ПОЛВТОРОГО» 470ms, «Сохранёнки» 494ms.
- Test.67's newly introduced guarded **200ms early long-track handoff did not fire at all**; single `replacement_lookahead_prefetch_current_wait` was «Биг сити лайф» 232450ms duration, **1200ms waitBudget**, phase downloading, prefetchAge 2081ms, and a cache-ready event after 39ms. This trace does not prove that Test.67 improved speed, nor that it harmed it. Do not tune it from these unmatched samples.
- 1 `replacement_download_failure` with reason `download_cancelled` at 46.058s belongs to abandoned speculative lookahead; no confirmed live current failure, repeated disconnection or source_controller_buffering_retained in Test.67.

## RASKOL — confirmed still broken, reason scoped
Observed sole RASKOL album song «Нас не понимают вообще» — Kosmonavty, RASKOL, live Yandex track ID **42884423**, source duration 232330ms, album ID 5685525, media alias 482, observation 68.832s; first joined 70.502s (1670ms).
- Exactly three `replacement_hot_cached_seek_request/ack/complete` at t=75.593 / 79.449 / 85.047s. Callback durations **37/59/51ms**, all using the existing decoder and source/audio owner, reported `sourcePcmMeasured=false`, `hardwareOutputMeasured=false`. **These measure MediaPlayer callback, not audible seek latency**; owner on video still hears lag.
- Full replacement sparse stream finished caching at t=77.317s (9,297,510 bytes, 8.394s elapsed). The second and third user seeks happened **after full cache completed** yet still felt slow; therefore cannot simply blame uncached Range/network.
- The video (~64s) shows Yandex's large center button display **Play** (UI paused) while the screen-recorded audio remains active, then returns to Pause (UI playing) ~2s later. However CELIKOM's public Media3 observer emitted **NO** `media3_fresh_is_playing_callback(false)` or `media3_fresh_play_when_ready_callback(false)` during the RASKOL sequence; `player_state` at 79.967s still `isPlaying=true,playWhenReady=true,playbackState=3`. Its periodic `ProbeService.sample()` also reads this Media3 `c.isPlaying()` and `c.getCurrentPosition()`, not the native Yandex UI. **The timely pause signal never reaches the permission-free app**. The Android generic playback-config counts cannot attribute playback to the Yandex session. Audio's continued waveform alone cannot identify source ownership, but in combination with UI/log confirms the visible pause vs CELIKOM playback mismatch.
- Past Test.10–11 passive legacy position fallback was tested and was unavailable/unreliable; Test.18 onward documents missing seek/pause events; Test.26–30 tried sparse wait and hot cached seek with regressions. Do not try equivalent timeout or DSP rework again. User previously forbade Accessibility/NotificationListener/MEDIA_CONTENT_CONTROL/root/patching Yandex, so no easy reliable alternate source.
- The video shows transition RASKOL -> «Дым» without the previous permanent stop. That success is **observed only in this one sequence**.

## «Дым» — limited good evidence
«Дым» Лёша Свик ID **39949113**, media alias 545, observation t=87.576s, first joined t=89.223s (**1647ms**); `replacement_stream_ready` at t=88.301s, `replacement_hot_cached_seek_ack` t=95.115s (**45ms**, transport only); `replacement_stream_cached` t=95.211s. No `source_controller_buffering_retained` or Media3 disconnect was observed. The startup briefly showed `Пауза` while Yandex was **BUFFERING**, later correctly showed `Играет версия CELIKOM`. This **does not prove** historic «Дым» pause/seek issues resolved.

## Decision: no new APK
**KEEP owner-acceptable Test.67 unchanged. DO NOT produce Test.68 or modify audio, source Media3 controller, UI, backend or stable** on this trace. There is no evidence-based, safe one-line engine fix. New speculative audio changes might sacrifice working fast next joins and still fail to observe RASKOL UI pause. In future, only isolated research with a genuinely new authoritative signal or a verified content-level hypothesis; never use CI seek callback timing as proof of audible correctness. Preserve immutable Test.67 source/Library reference. Documented only, no claim of on-device fix.
