# CELIKOM Android Test.33 — HONOR Test.32 owner feedback, long browsing and stopped-decoder seek rejoin (2026-11-04)

## Owner verdict on Test.32

**Strong improvement, NOT acoustic acceptance.** The owner heard almost imperceptible first transitions on approximately ten songs, including places where some original noise remained briefly before the replacement joined. The previously characteristic sharp «пшик» was largely absent. Later, after choosing arbitrary songs in an album rather than stepping through the preloaded queue, some joins became noticeably slower/glitchier. RASKOL «Нас не понимают вообще»/«Дым» finger-seek complaint remains unresolved. Do not present Test.32 as universally fixed or accepted; preserve its signed functional backup.

Private source: `CELIKOM-combined-20261104-233641.txt`, third JSON run starting line2168, Test.32 23:34:20 Minsk, 139.95s. The first two earlier runs in this combined file belong to Test.29 and Test.31 and MUST NOT be pooled with Test.32. Do not commit raw diagnostics, credentials or audio.

### Facts from fresh Test.32

* 19 completed handovers across 18 distinct track IDs (one same-track rejoin), 18 unified 160ms handovers and **one `exclusive_single_turn` 0ms** at 7.057s following `SAME_ITEM_SEEK` at 6.58s. That is a real remaining bypass in the `!player.isPlaying()` decoder restart branch; the earlier Test.32 regression only covered a **still-playing** decoder with original audible.
* Four new-song cold sparse streams (plus the same-song stream rejoin) and **14 locally cached handovers**. Most cached source-boundary→join intervals were roughly 0.4–0.8s. Cold selections included ~3.74s (`85025192`) and ~3.81s (`48591644`); these waits were before ownership, not proven post-grant stalls.
* Ten `replacement_audio_cache_evicted` events from 70.46s onward, **every one `entry_limit`** (8 complete files), with remaining cache bytes only roughly 50–64 MiB under the existing 96 MiB byte ceiling. This is a concrete cause of avoidable repeat/reorder cache misses in longer browsing, although there is no proof that it alone caused every perceived artifact.
* 18 lookahead prefetches started, 17 completed, 12 primed decoders adopted, 14 audio files reused. Arbitrary album selection cancels an anticipated successor (`next_item_changed` at 41.97s and 91.65s), requiring a genuinely new cold fetch. The current 1.2s speculative→current handoff timeout at 113.36s caused cancel/restart at 114.56s; subsequent cold join at 116.81s. Document this remaining inefficiency, **do not blindly increase delays**.
* Zero confirmed `replacement_stream_starvation`, `replacement_buffer_wait`, `replacement_recovery`, `replacement_join_guard_fallback`, or timeout of the new contiguous-runway gate. No measured progressive RAM exhaustion or stable-pipeline resource leak in this finite 140s sample. Command logs do **not** prove headset/speaker waveform quality.
* On RASKOL `Нас не понимают вообще` (`42884423`), once the public source position was observed, two cached seek callbacks completed in **62ms and 51ms** while replacement remained the sole commanded audible owner. No precise UI finger-drag timestamp is visible: this does **not** disprove the owner's UI→public Media3 publication lag. `Дым` was not in this Test.32 run; its earlier delayed position evidence still stands. Do not rewrite approved seek/completeSeek or promise a fix without another permissible position source.

## Test.33 scope

Branch `feature/android-0385-test33-longbrowse-seek-rejoin-20261104` starts from Test.32 documentation HEAD `12b9cf49d811f19243137d90c0c8be8a3d77599b`. It is isolated to the test package `pro.celikom.nativeprobe.test`, version `0.3.85-test.33` code `86118` (higher than Test.32 code86117), original signing certificate. No UI change, new Android permission, Account/OAuth or Track ID change. Stable `pro.celikom.nativeprobe`, PC, Hostinger writes, OTA and admin remain untouched.

1. **Seek-to-beginning decoder restart must blend.** In the existing `ReplacementEngine.update()` path when a same-item seek to the first 1.5s leaves the decoder paused, use coherent re-entry rather than an audible 0ms `exclusive_single_turn`. The 1.5s *position* classification identifies a beginning replay; it is not a new delay or fade constant. Preserve old `streaming != null` clock-gate default, verified retained-pause behavior, mid-song sparse finger-scrub timing, existing 160ms complementary command-law, and the independent Test.28 diagnostic opt-in. Do NOT change frozen `seek()` or `completeSeek()` or increase crossfade milliseconds. New `Test33LongBrowse` reproduces the previously untested stopped-decoder branch; Test.32's still-playing regrant test remains.
2. **Long-browse complete-file cache retention.** Increase bounded in-session `RecentAudioCachePolicy.MAX_ENTRIES` from 8 to 12, while **keeping the exact 96 MiB byte limit** and all file, auth/version, eviction and lifecycle checks. This can reduce unnecessary redownloads when revisiting earlier songs; it cannot prefetch an unpredictable new song or solve RASKOL position publication.
3. Retain Test.32's verified sparse runway, prefetch during handover, full-file starvation fallback, current lookahead/prime logic, and device command diagnostics untouched. Both old and new host tests and 300-song virtual long-run are required.

## Verification and sign-off

The test branch may build a single signed side-by-side APK only after full native host regression, frozen accepted seek hashes, Android API36/JDK17 compilation and D8, offline test packaging contract and original v3-signer verification succeed in GitHub Actions. A green CI **does not** mean acoustic approval on HONOR. The owner should install this one Test.33 APK over Test.32 and listen to (a) ordinary rapid Next, (b) arbitrary album/song browsing beyond 10 tracks, (c) one same-song seek, and (d) RASKOL UI issue; no repeated videos or separate micro-APKs requested.

### Immutable rollback and forbidden scope

* Test.32 signed functional backup `backup/android-0385-test32-signed-owner-pending-20261104` → `eb13afba0a63567a8e12e45f848b9616aaf7c749`, [original signed APK](https://chatgpt.com/library?file_id=libfile_dd79106ef740819197b3f36457d8b0c4&account_id=personal), SHA256 `d13a91dad30c57da4ce3c1d2968c99b028a61209bc53271c4b0cbde6531c505b`; source/history untouched.
* Test.28 owner-selected `backup/android-0385-test28-owner-selected-20261104` → `904ba52d5afbb5e77f4ee36e40d321d568896460`.
* Test.23 owner-accepted `backup/android-0385-test23-owner-accepted-20261104` → `251b6facc8739557ff962365da012d502ed3bac8`.
* Test.31 owner-rejected functional `8f3bce6bb049d66ae1e30316ab4365bbd7c9f66b`. No branch rewrite, rollback deletion, stable publication or Hostinger uploads.

_Test.33 functional source SHA, CI run ID, final signed APK SHA256 and permanent APK location must be filled **after** successful Actions build and byte verification. Until then Test.33 is not ready to install._
