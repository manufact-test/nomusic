# CELIKOM Android — HONOR Test.74: confirmed root mechanism of selective native transport failure

**2026-11-08, user test at 23:18:56+03:00.** Sources: owner-provided `CELIKOM-combined-20261108-232025.txt` (latest segment `0.3.85-test.74`, `run_start` at 23:18:56+03:00, ~1068 events) and `SVID_20261108_231903_1.mp4` (73.68s). Do not commit raw owner diagnostics or full video.

**RESULT: SOURCE-OF-TRUTH PROBLEM IS REPRODUCED AND ISOLATED.** Android framework *system media session* `android.media.session.MediaController` (accessed from user-authorized NotificationListener) receives same-item scrubs about 3.1–3.3 **seconds** before our current Yandex `androidx.media3.session.MediaController` bound to `Media3LibraryService`. The same system controller correctly sees user native PAUSE/PLAY, while our existing external Media3 controller reports `playing=true`, `playWhenReady=true` and increments its stale clock. Independent witness title/artist and duration match source item on every compared sample. **This proves what transport interface is unreliable, not why Yandex internally diverges for these specific songs.**

## Timings from Test.74
| Track | Native Android framework PlaybackState callback | CELIKOM observes via external Media3 | Exact delta |
|---|---:|---:|---:|
| **«Дым»**, ID 39949113, seek to ~1:01 | t=30.876s, state PLAYING @61,552ms; t=30.901 state BUFFERING | t=34.130s `replacement_hot_cached_seek_request` @64,527ms | **3.254s** |
| **«Дым»**, seek to ~2:38 | t=35.309s, PLAYING @158,017ms; t=35.338 BUFFERING | t=38.551s hot seek @160,960ms | **3.242s** |
| **RASKOL «Нас не понимают вообще»**, ID 42884423, seek to ~0:52 | t=65.237s PLAYING @52,185ms; t=65.273 BUFFERING | t=68.339s hot seek @55,017ms | **3.102s** |
| **RASKOL**, seek to ~2:29 | t=69.240s PLAYING @149,441ms | t=72.522s hot seek @152,440ms | **3.282s** |
| **Good control «Холодно»** | t=24.277s framework event, same-item seek to zero | t=24.279s **source_discontinuity SAME_ITEM_SEEK** | **0.002s** |

**Pause proof:**
- «Дым»: framework callback at t=39.929s `PlaybackState.STATE_PAUSED(2)`, raw position **162,313ms**. Framework remains PAUSED for **3.603s** until t=43.532s returns PLAYING(3). At t=40.117–43.205 witness samples, `remoteMedia3Playing=true`, remote position continues 162519→165611ms while framework is frozen @162313ms; after play resumes remote remains **~3.4s ahead**.
- RASKOL: platform PAUSED at t=73.690s, raw position **153,584ms**. PLAYING resumes at t=75.521s, **1.831s** later. Media3 keeps `playing=true` and current position advances throughout, leaving remote clock **~1.6s ahead**.
- Owner's corresponding screen recording shows native Yandex Play triangle during these holds, vs usual Pause glyph when active. This corroborates framework state, not the old external Media3 view.
- After the old media3 finally observes seek position, CELIKOM's own `MediaPlayer` hot seek ACK takes **32–58ms** in all four named cases. The long latency is **before** the decoder sees the target, and pause never crosses the old transport on these tracks. Previous seek/buffer tuning CANNOT fix it.

**Control comparisons:**
- All six tracked songs, including «Дым», RASKOL, «Холодно», «Было давно», «Моя игра», «Розовое вино», report `metadataSeekable=true`, `metadataDynamic=false`, `metadataLive=false`, `remoteSeekCommandAvailable=true`, `remotePauseCommandAvailable=true` (no differentiating metadata flags).
- Framework `yandexSessions=1` during report; `witnessTitleMatches=true` on all **172** witness samples. No wrong artist/song confusion. Basic source durations agree. No evidence that MP3, server, duplicate artist, Yandex catalogue, file range or duration mismatch caused these specific transport failures.
- During bad-track seeks platform sends `STATE_BUFFERING(6)` callbacks immediately, while external Media3 lacks corresponding `onPositionDiscontinuity(SAME_ITEM_SEEK)`. Good control does receive it.

## Product / privacy / security decision
Owner says Android / Google Play Protect blocked installing Test.74 unless they disabled protection. This is **not acceptable for production** or recurring owner testing. **Re-enable Google Play Protect immediately** and manually **revoke CELIKOM Test Notification Access after the diagnostic**. System notification-listener permission gives broad notification-access capability even though Test.74's listener reads only Yandex media session: it is privacy-sensitive. Do not infer exact Play Protect blocking rationale from logs; may be app's sensitive permission or sideload reputation, but no system warning text was supplied.

The framework route is proven to fix **observation**; **it does not fix transport until integrated**. A permanent implementation using `MediaSessionManager.getActiveSessions()` normally requires either user-enabled NotificationListener or system-only `MEDIA_CONTENT_CONTROL` permission (Android official API). Prior permission-free `android.media.browse.MediaBrowser` attempt against Yandex `Media3LibraryService` failed (`legacy_position_source_unavailable` stage `browser_connect`). Do NOT silently sneak in protected notification access in shipped APK or misrepresent as permission-free.

## Next engineering step
1. **First: find a permission-free fresh Yandex source** suitable for Android 13: research platform MediaSession Token availability from already connected *public* Yandex Media3 service, or a supported public browser endpoint that actually returns the platform token. Use only public APIs; no root, accessibility scraping, private app storage, decryption, signature bypass, overlay intercept or notification-permission tricks.
2. If genuinely no permission-free route exists, present a **transparent user opt-in alternative** (Notification Access) alongside an explicit Original-only fallback when not granted. The goal is still natural native Yandex pause/seek on all tracks, not requiring disabled Play Protect.
3. A proposed pause/seek integration MUST require verified same-title/artist (and duration) on fresh framework metadata, one active Yandex session, lifecycle-bound read-only observation, real PAUSED(2) vs BUFFERING(6) distinction, re-anchor source clock after resume, stale-session fail closed, and no cross-track seek/track-ID confusion. In contrast, current `LegacySourcePositionPolicy.reconcile` explicitly requires `samePlaybackState`, so it **discards the reliable platform pause on bad tracks**; it cannot be reused unchanged.
4. Regression tests must cover four ~3.2s delayed remote seeks and two missed pauses, plus normal «Холодно» immediate seek, resume without drift, switching tracks, false attribution, revoked permission, and backward seek. **Preserve Test.73 audio stability, Quest and source session boundaries.**
5. Do not build Test.75 that requires the owner to disable Play Protect again merely to collect the same evidence; diagnose and solve distribution/security before another permission-dependent APK. Physical HONOR confirmation is mandatory.

**No server, audio, stable Android, OTA, source library or user data changed.** Latest verified audio candidate remains Test.73 / Test.74, not a proven fix for native controls.
