# CELIKOM Test.9 — promoted-prime race after playlist switch (2026-11-03)

## Owner evidence

HONOR NTH-NX9, Yandex Music 2026.09.5, installed CELIKOM Test.8/code86093. Owner supplied private `CELIKOM-combined-20261103-140429.txt` and `SVID_20261103_140258_1.mp4` and reported that song starts initially sounded close to perfect, then became audibly worse after switching or tapping songs. The combined log includes Test.6 and Test.7 history; **only the run starting 14:02:45 +03:00 with version `0.3.85-test.8` is new**. Do not double-count earlier runs.

Test.8 shows 11 source boundaries through elapsed 87.5s. New source sessions did not appear: broadcasts retain trusted session 75561. The video's playlist taps around its second 58/59 align with the source event at elapsed 72.08s: `PLAYLIST_CHANGED`, `SEEK_TO_OTHER_ITEM`, new alias 64 ("Толер"). This was a *different user-selected current song*, not the previously primed successor alias 46. Correct fail-closed invalidation of the old successor occurred at 72.16s. The new song needed an unprefetched full-file download (2112ms) and reached exclusive replacement at elapsed 75.15s, about 2992ms after the boundary. This first exceptional delay cannot be eliminated by an ordinary one-next-track prefetch when the user selects an arbitrary nonprefetched song; do not bypass fresh resolve or the full-file source selection to pretend otherwise.

**Actual additional race:** At elapsed 87.48s, the queued candidate alias 76 became current, and cached audio was available; at 87.528s `replacement_lookahead_decoder_prime_discarded(reason=prepared_stale)` occurred **because** `primingNextCurrent()` explicitly rejected a decoder once its own alias became current, despite a matching promoted live track. A fresh resolve arrived at 87.631s; preparation unnecessarily recreated the decoder, then muted prewarm and alignment ran to 87.926s; exclusive output finished at 88.011s (527ms after boundary). Several prior fast joins of Test.8 used correctly primed decoders and took roughly 265–340ms to output. The recording corroborates active playlist navigation; it does not isolate original/replacement PCM nor prove all future tracks share the same acoustic defect.

## One combined Test.9 candidate

Branch `feature/android-0385-intro-join-investigation-20261102`. Separate test package `pro.celikom.nativeprobe.test`, version `0.3.85-test.9`, code **86094**.

1. Keep the silently priming MediaPlayer valid during transition from *next candidate* to *same live current track*, only when the existing speculative lease, candidate track ID, account generation and current identity remain consistent. The decoder remains volume zero and cannot authorize playback.
2. After a **fresh current resolve** with exactly matching audio key and cached full-file path, wait at most **150ms** for an already-in-progress promoted muted prime to finish motion/pause/rewind, then adopt it. If it is stale, mismatched, interrupted or slow, use the existing normal file decoder fallback. This avoids destroying a nearly ready prime at the boundary.
3. Add deterministic host regression cases for promoted `onPrepared` after boundary, resolve arriving before prime readiness, and bounded fallback when priming stalls. Continue all existing prefetch mismatch/timeout, owner/exclusive audio, seek golden and full Android/D8/signature/OTA checks.

The new code does **not** alter user seek/ACK, pause/resume, session mute/gain, drift guard, 70ms muted cold lead or arbitrary playlist selection. In particular, the first uncached manual selection still needs a download; do not misrepresent that as fixed.

## Release and safety

Produce one signed isolated CELIKOM Test.9 via existing validation-first GitHub Actions workflow; stable publishing jobs must remain SKIPPED. No changes to original stable CELIKOM 0.3.85/code86, source checkpoint `053b7d59beb53db5f30b942feba35e51a1ab256a`, accepted-seek backup refs, Hostinger/OTA `stable.json` or PR #37 merge state. At this commit CI and real phone acoustic verification are pending. Require successful validation, original signer and confirmed artifact before distributing ZIP.

Owner next check: ordinary listening, particularly whether manually changed playlist is followed by quick subsequent song starts; send one combined log. No dedicated seek test. The loudness-dependent audible seam is still an open physical-phone acceptance issue, because transport logs cannot measure PCM phase.
