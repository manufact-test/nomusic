# CELIKOM Android Test.15 — serial priority and cached decoder grace (2026-11-03)

## Scope and source of regression

HONOR NTH-NX9, Android 13. Owner checked isolated Test.14 with private combined log `CELIKOM-combined-20261103-191658.txt` (4,905 JSON events, fresh Test.14 run begins at line 3,519, contains Test.11/Test.13 history) and `SVID_20261103_191454_1.mp4` (~113 seconds). These files contain private listening history; **do not commit them**.

The owner says Test.14 is perceptually worse than Test.13, even for formerly clean first chords. Measured boundary→guard times on shared tracks (different listening sessions, so comparisons are indicative, not causal proof):

| Track | Test.13 | Test.14 |
| --- | --- | --- |
| «Солнца не видно» 48591644 | 239ms | 491ms, 768ms |
| «Биг сити лайф» 40371622 | 267ms | 613ms |
| «Крылья» 50163052 | 215ms | 299ms |
| Johnyboy «Метамир» 42601865 | 2981ms (cold) | 404ms (prewarmed) |

Test.14 registered three `replacement_cached_current_prime_live_wait_done ready=false` after 150-198ms and discarded three matching primed current decoders (`not_ready_or_live_key_mismatch`). Some repeat selections therefore rebuilt the decoder. 18 join guards in Test.14, 13 primed next adoptions; 18 downloads (16 lookahead, 2 current), `queueWaitMs` near 0 on both parallel lanes. **No proof** that parallel networking alone caused every audible seam: traffic, timing, track selection, and cold/warm state differ. Its introduced competition is an unnecessary variable given owner regression.

On «Дым» 39949113, video shows UI seek through approximately 0:42, 1:19, and 3:34, but observed Media3 `player_state` remains ~10.3s with no `SAME_ITEM_SEEK` before the next song. This is a missing observable source position in the authorized API, not proof that the frozen seek handler is wrong. Do not claim repair; do not add Accessibility or NotificationListener permissions or hook another app without explicit separate approval.

## Test.15 implementation

- Revert speculative and current full-file transfers to **one** `NativeApi.audioWork` executor (Test.13-compatible), removing separate `prefetchAudioWork`. Keep `priority` and `queueWaitMs` logs to measure actual queue impact.
- Allow the foreground current transfer to enqueue first: the speculative `downloadLookahead` is posted 1,100ms later on the existing main handler before joining the same serial audio queue. The normal `valid`/account lease is still checked by `enqueueDownload`; stale candidates abort. This cannot preempt a long speculative download that already started, but avoids racing immediately after a new current song begins. It may defer the next preload on rapid manual skipping — measure objectively.
- Current-cache priming gets 340ms bounded grace after fresh resolve versus the prior 150ms, **only** when `c.currentCache==true`; an already promoted next-track decoder stays on original 150ms. Existing single-flight and stale-key guards remain unchanged. New host regression covers adoption after 230ms and bounded timeout.
- Test package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, version `0.3.85-test.15/code86100` remains separate; no stable publisher, Hostinger or `stable.json` changes.
- No changes to `ReplacementEngine.seek()/completeSeek()`, PCM/duration validation, source mutation permissions, `ClockSupervisor`, global volume or audio ownership.

## Verify and future direction

**Validation complete:** full native host tests (including late cached-prime adoption), static architecture guard, Android API36/D8, frozen accepted seek, separate APK signing/certificate and release-contract checks all passed. Stable publisher was SKIPPED. Tested functional SHA `4838ccee4aa4628dce68437ebbf00d4dfc30ce27`. [Full CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41674369584); [direct signed Test.15 ZIP](https://github.com/manufact-test/nomusic/actions/runs/41674369584/artifacts/13248949184); artifact `13248949184` (`CELIKOM-Test-0.3.85-test.15-code-86100`), expires 2026-11-10. No physical acoustic acceptance yet. Owner should run one complete normal listening pass, send a single combined log/video and opinion on transitions, repeats, cold starts and «Дым».

Do **not** spin further micro-builds from isolated observations. Remaining real tasks are inaccessible seek on «Дым» (needs a different consented source of true position), musical seam on «Биг сити лайф» (PCM alignment/edition validation), long `Крылья` drift after output route changes, and Johnyboy timing requiring additional field evidence. Stable original and user-accepted seek remain frozen.

## Official Android API cross-check (2026-11-03)

- https://developer.android.com/media/media3/exoplayer/listening-to-player-events — `Player.Listener.onPositionDiscontinuity` carries seek position only for source-reported `Player.seekTo` discontinuities. No supported promise of reflecting an external app's independent UI scrub.
- https://developer.android.com/reference/android/media/session/MediaSessionManager — reading arbitrary active platform media sessions via `getActiveSessions` requires `MEDIA_CONTENT_CONTROL` or enabled `NotificationListenerService`. Not an invisible permission-free fallback. Existing rejected legacy Browser cannot be treated as an approved position source.
- https://developer.android.com/reference/android/media/MediaPlayer — `getTimestamp()` maps the **replacement player's own** media clock to system time; it does not expose Yandex source PCM phase. https://developer.android.com/reference/android/media/MediaTimestamp cautions that actual presentation time is best-effort. This constrains any “perfect zero-audible-seam” claim for different editions.

These source statements plus the Test.14 track/seek traces rule out a safe blind timing or fade adjustment. Further investigation of «Дым» should first establish a consented, accurate position source; do not silently add notification access, capture or accessibility.
