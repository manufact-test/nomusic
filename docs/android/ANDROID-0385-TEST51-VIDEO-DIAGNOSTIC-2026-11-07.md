# Android Test.51 — HONOR screen recording vs combined journal (2026-11-07)

## Source and scope
- Video: user-provided screen recording `SVID_20261107_011133_1.mp4` (~113 s). Not committed: private captured media.
- Diagnostics: user-provided `CELIKOM-combined-20261107-011335.txt`. Only its latest `0.3.85-test.50` run from `2026-11-07T01:11:17+03:00` (lines ~3324–3831) is compared to the video. Previous runs are not counted as this test.
- Exact Test.50 accepted source and rollback remain `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1` (tree `bbdf43d78e04c6dc4562c5b0541049283f9109b0`). Test.51 uses a *separate* investigation branch. No stable release, Hostinger, production update, PC extension, joins, fades, or seek decoder logic change.

## Screen vs journal: unresponsive Pause/Seek
- Video shows RASKOL / Космонавты «Нас не понимают вообще» playing with several seeks; at ~31–36 s and ~44–46 s the yellow UI button changes to triangular Play (paused UI), while system-recorded music remains audible and continues. Video later shows the same on Лёша Свик «Дым» (~102–105 s).
- During RASKOL, Media3 `player_state` / `playback_health` continue reporting `isPlaying:true`, `playWhenReady:true`, and an advancing position: there is no authoritative pause state to send to the replacement engine. The engine must not invent UI touches or blindly stop its decoder using anonymized audio-player counts.
- RASKOL cached-source retarget requests at elapsed 31.196/36.293/44.735/55.230/67.255 s acknowledge in 66/52/44/73/57 ms. «Дым» (second visit, after reconnect) cached seeks at 111.173/115.757/123.692 s acknowledge in 36/47/57 ms. These timings start **after** the Media3 source position becomes visible; they DO NOT measure finger-to-response latency. The video shows UI seeking earlier than some corresponding Media3 updates. Root cause is missing/delayed trusted Yandex transport publication, not demonstrated slow CELIKOM decode.
- No permissionless, trustworthy evidence currently identifies Yandex UI Pause/Seek earlier than its public Media3 session. No Accessibility, notification-listener, root, injection, fake touch interpretation, or unsafe audio-player-count proxy will be introduced. Thus Test.51 explicitly does **not** claim Pause/Seek fixed.

## Separately proven connection-loss regression on «Дым»
- Latest run: new «Дым» alias 172 at 75.456 s in Media3 `STATE_BUFFERING=2`, `playWhenReady=true`, `isPlaying=false`. The replacement is prepared by 76.795 s and correctly silent during buffering.
- At 78.571 s source still reports benign quiet buffering; `SourceStateWatchdog.refresh` forces `ProbeService` to release its *connected* controller and reconnect. All five following attempts at 78.616, 79.640, 81.679, 84.713, 88.748 s return `SecurityException`; connection finally returns at 93.778 s, already on Johnyboy «Метамир». This is concrete evidence of an overly aggressive CELIKOM reconnect decision. No network loss event appears in this incident; server requests previously succeeded.
- Test.51 changes the quiet-buffering watchdog to **diagnostic only**. The connected controller is retained; `sample()` continues updating Yandex state and replacement receives `buffering` without detaching. Genuine disconnection (`!c.isConnected()`) and independent transition/end gates remain unchanged. It does *not* force Yandex to unbuffer faster.
- Java regression covers quiet buffering, 30-second diagnostic throttle, normal playback recovery and track changes. Structural regression requires no release/reconnect inside the quiet-buffering branch and preserves disconnection recovery. Existing full tests, immutable seek fingerprint and signed-APK contract still gate CI.

## Acceptance
- Code hypothesis: eliminates this specific self-inflicted reconnect. Not phone-verified.
- Video proves visible Pause inconsistency, **not** a working fix for it.
- Test.51 Android APK must only be called built/signed after GitHub Actions actually succeeds, with package `pro.celikom.nativeprobe.test`, and must never overwrite gold Test.50 source.
