# CELIKOM Android — foreground HTTP Range priority during HONOR scrubbing

**31.10.2026 — nonpublishing staging experiment.** Installed **0.3.67/code68** remains the acoustic control; this is **not** an APK, an approved seam or a release. Branch: `feature/android-honor065-continuity-staging`. Android-only changes.

## Mechanism and why the previous fix was not enough

The 0.3.67 cellular+VPN log observed a 2792ms decoder seek followed by 933ms and 17ms corrections. The earlier 0.3.67 staging repair retained the source DSP effect while the original already played at full volume, and resumed a stopped prefetch after a validated demand read. Neither forced a background HTTP Range to yield when the actual decoder needed a different sparse block.

`BufferedAudio` fetched missing blocks on a background worker with up to three HTTP retries. A foreground `readAt()` could compete with that worker for bandwidth or wait on its `loading` bit when both addressed the same block. With high-latency cellular/VPN, this may unnecessarily delay the user-requested position. This is a **source-code mechanism**, not proof that any specific 2792ms packet wait in the private HONOR trace was background contention.

## Narrow repair

- A **missing** foreground decoder block marks foreground demand before entering `fetch`; previously cached reads never preempt downloads.
- If a background connection is active, its `disconnect()` is scheduled on the existing validity-watcher executor, **not on MediaPlayer's decoder thread**. This limits work on the latency-sensitive caller.
- Background fetch detects active demand, yields without burning its three ordinary network retries, releases its per-block `loading` lock, and records `replacement_stream_prefetch_yield`. Background work waits while demand is active.
- Once the demanded block completes a validated HTTP 206 + strong ETag + Content-Range read, the previous recovery gate resumes at most one background worker. An unsuccessful demand does not trigger an automatic retry storm; active network cancellation, tracker expiry and byte-identity checks are preserved.
- The `waitingSince` stall flag now remains active until the **last missing-block demand** finishes, avoiding a cached concurrent read erasing another live seek's wait state.
- Existing decoder single-flight, latest live Yandex position, muted seek, DSP effect retention and the 12-second stream seek guard stay unchanged. This patch **does not** guarantee a faster server response.

## Regression

`addon/TestBufferedAudio` has a deterministic server that blocks the background download of block #2 until its connection is disconnected, then asks the real `readAt` for block #6. The test requires demand completion while prefetch would otherwise remain blocked, one worker recovery, and exact bytes for the completed sparse file. The old code cannot complete that demand under the blocked prefetch in the same order with the new priority assertion.

`TestHonor067SlowStreamSeek` now drives the **production Media3 router**, with a manual Next encoded as a SEEK discontinuity across two media-item indices while decoder HTTP seek is pending. The stale callback cannot restore the old audio; a follow-on item event cannot cause duplicate boundaries. Existing 0.3.65 natural → manual Next → cached seeks → natural → seeks chain, 0.3.66 buffering replay, pause/BT/Stop and release contracts stay mandatory.

## Acoustic boundary and release gate

The current default cold join deliberately ducks source to zero and ramps up replacement over 500ms; its audible valley is **not fixed by HTTP priority**. The admin-only 160ms same-song linear blend can avoid the commanded zero valley, but it has no source PCM/sample-phase verification; the result is song-, route- and latency-dependent. No blind gain law or fade-time change is justified. On HONOR only, compare identical songs, route, cache state, Wi-Fi+VPN and cellular+VPN, and capture consented speaker-level observations, without copying recordings to GitHub.

Do **not** conflate green host tests with acoustic acceptance. A future single signed updater APK requires SDK36/D8 pass, 27+ negative release contracts, preserved original signing identity, DEX provenance, verified live SHA256 and publish-stable success. The owner then performs natural song → real manual Yandex Next → several finger seeks → natural successor → more seeks, plus partial/full cache, Bluetooth, pause, Stop and Next during slow seek. No other product subsystem is in scope.
