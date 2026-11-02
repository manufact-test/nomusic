# CELIKOM Test.4 — owner diagnostics, current-track prefetch race, Test.5 candidate (2026-11-02)

## Scope and baseline

- Repository `manufact-test/nomusic`, experimental branch `feature/android-0385-intro-join-investigation-20261102`.
- Tested APK: `0.3.85-test.4`, versionCode `86089`, package `pro.celikom.nativeprobe.test`, functional source `d0b418d0173207b4900f27af365e87595301c4b1`.
- Owner's ZIP contains two overlapping combined snapshots (`CELIKOM-combined-20261102-231119.txt`, `CELIKOM-combined-20261102-231157.txt`) and `SVID_20261102_230920_1.mp4`. The later snapshot is a continuation of the same Test.4 run; it also embeds older Test and Test.2 runs. Do not double-count them.
- Raw diagnostics, audiovisual recording, album/customer details, credentials and user data are **not** committed.
- Stable original `0.3.85`/code86, SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`, and both accepted seek backup branches remain untouched.

## Real-device findings

Latest Test.4 run starts 2026-11-02 23:09:24 +03, HONOR NTH-NX9 / Android 13; 16 `replacement_source_boundary` events and 15 next-track prefetch starts. Of these prefetches 13 become ready, with 12 `cache_consumed` events. There are 12 observed cold-join starts after source boundaries: 10 happen within 321–610 ms, and two are late (2,060 ms and 5,172 ms). Four boundaries have no cold-join start before the next boundary or log end; some are quick skipped items, and the last is stuck.

For context, the older `0.3.85-test` run embedded in the same export had five post-boundary cold joins at 1,880–4,668 ms (median 3,932 ms). The embedded Test.2 run had six cold joins at 410–638 ms (median 559 ms). Different sessions and track selections cannot prove controlled acoustic improvement over Test.2, although Test.4 clearly removes the multi-second download latency on many transitions compared with the first Test.

The video contains mono AAC capture with brief low/silent intervals, including one around 4.77 seconds. This is mixed/captured output, not isolated Yandex and CELIKOM PCM or calibrated speaker output: it cannot independently attribute every gap to the replacement engine. Some short boundaries, buffering and content silence are still possible. The owner has **not** acoustically accepted intros.

## Reproduced logical failure: GUF / current track alias 80

Timestamps are `elapsed_ms` of the Test.4 run (seconds below), independent of screen-recording offsets.

| Time | Logged event | Meaning |
| --- | --- | --- |
| 96.651 s | `replacement_lookahead_prefetch_start`, alias 80 | Full-file prefetch starts before the next source boundary. |
| 100.822 s | `replacement_source_boundary` → generation 17 | Alias 80 becomes the playing source. |
| 100.940 s | `replacement_lookahead_prefetch_current_wait` | Fresh resolve agrees with the prefetch audio key; the current song waits on the in-flight download. |
| 103.007 s | `replacement_lookahead_prefetch_cancelled`, alias 80, `new_next_item` | The program discovers alias 81 and steals the same single prefetch slot while alias 80 is still waiting. |
| 103.100 s | `replacement_download_failure`, `download_cancelled` | The old current-prefetch download is aborted. |
| 105.508 s | `replacement_lookahead_prefetch_ready`, alias 81 | The *following* track file is prepared instead. |
| 151.423 s | service heartbeat/player state | Alias 80 is still playing original audio; `replacementPreparing=true`, `replacementReady=false`, `replacementOwnerState=PREPARING`, no player/effect session. |

This is **not** a process death, Media3 disconnect or network-loss event: the 250 ms observer, 15 s heartbeats, Media3 controller and signed-in backend checks continue while Yandex source audio remains active.

In `ReplacementEngine.prefetchLookahead()`, the new next candidate unconditionally calls `invalidateLookaheadPrefetch("new_next_item")`. `invalidateLookaheadPrefetch()` clears `lookaheadPrefetchCurrentDescriptor` and `lookaheadPrefetchWait`, but does not use the already fresh-resolved current descriptor to start ordinary `downloadFull()`. With `preparing` still true, the current track has no remaining completion callback and cannot recover automatically. This exactly matches the lasting PREPARING state.

## Test.5 correction

One local change in `ReplacementEngine.java`, without touching the accepted seek/Pause/Resume/ownership/clock gate:

1. When a current-track handoff is actively waiting, defer any new next-track prefetch and retry that candidate only if it is still the actual next item. Keep the current in-flight lease and file intact.
2. If any other path invalidates the promoted current wait, invoke the existing fresh-descriptor full-download fallback **before the descriptor is lost**. Late stale callbacks remain invalid.
3. Bound a promoted current wait to 10 seconds; if it cannot complete, release the prefetch and run the ordinary current-track full-file fallback.
4. Add deterministic host regressions for next-candidate collision, cancellation fallback and wait timeout.

Candidate test package `pro.celikom.nativeprobe.test`; version `0.3.85-test.5`/code `86090`; existing original signer; OTA absent. Keep separate from the stable original. Full host suite, unchanged `check_0385_seek_baseline.py`, API 36/D8, signed Test artifact, package/signature/receipt and owner audio review remain mandatory. No stable publishing, `stable.json`, Hostinger write or PR #37 merge.

**Status at time of analysis:** source patch/test candidate prepared, CI and physical listening not yet established. This document is not acoustic acceptance.
