# CELIKOM Test.26 — Test.25 field evidence, first-join Range fix, invisible Yandex scrub

Date: 2026-11-04. Status: **experimental, NOT owner-accepted**. Test.26 has no HONOR acoustic acceptance yet.

## Absolute rollback freeze

- The ONLY owner-accepted rollback is **Test.23**, branch `backup/android-0385-test23-owner-accepted-20261104`, original source SHA `251b6facc8739557ff962365da012d502ed3bac8`.
- The untouched original signed Test.23 APK is [in ChatGPT Library](https://chatgpt.com/library?file_id=libfile_301d98360e9c8191b8e05594f402d265&account_id=personal), SHA-256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.
- Test.25 source SHA `19f19725718710b36e0e9c2d74a325b7b5b6cc8f`, signed [Test.25 APK in Library](https://chatgpt.com/library?file_id=libfile_93b91a6576508191a2f4674df8255b8a&account_id=personal), SHA-256 `eedb39f0f356f7e490b6d04b4bf7b7e12f9b5eb2903aadb2cc6d4a3bf3673fea`. Owner said **Test.25 is better, but not perfect**; no new backup designation was given.
- Test.26 branch `feature/android-0385-test26-cold-hint-observation-20261104` branches from Test.25 **documentation HEAD** `a38bd4af343af6f3e51c0d49b78d5d556580ac49`, inheriting its audio changes, not from a rejected old experiment. This does not affect Test.23 backup, stable `pro.celikom.nativeprobe` / 0.3.85/code86, Hostinger, OTA or `stable.json`.

## Fresh Test.25 HONOR evidence (do not combine historical runs)

User supplied `CELIKOM-combined-20261104-160728.txt` plus `SVID_20261104_160444_1.mp4` on HONOR NTH-NX9, Android 13, Yandex Music 2026.09.5. **Only the run beginning at JSON line 3260** (`run_start`, `0.3.85-test.25`, local `2026-11-04T16:04:05+03:00`) belongs to Test.25. The earlier Test.23/24 journal segments are overlapping historical material.

The 200.764-second Test.25 run has **22 track boundaries and 27 transition-complete events** (the latter includes several same-item seek re-joins). Boundary-to-next-handover delays were 416, 381, 271, 340, 443, 568, 411, 266, 3065, 1753, 896, 514, 1130, 2284, 819, 228, 384, 2463, 461, 272, 1976, 1309 ms. Thus **3/22 exceed 2 seconds; 0/22 exceed 5 seconds**, worst 3065 ms. This explains the owner seeing fewer dropouts than before without claiming flawless audio. A 26-second interval between completed songs around +131–157s included Yandex playlist interaction; it must NOT be misclassified as one slow replacement handover.

### First Start — measured Range miss, not just network slowness

- Track 10AGE «Пушка», id `85025192`: backend resolve at +574ms; sparse preflight started +575ms and validated 316,027 bytes (blocks 0, 1 and tail) at **+1960ms**.
- Native `MediaPlayer` prepared +2074ms and first alignment seek requested +2079ms to source position **9704ms**. The initial sparse blocks did not include its demanded audio Range: `replacement_stream_seek_data_wait` at +2343ms.
- Seek acknowledged only at **+3647ms** (callback 1570ms and `rangeWaitObserved=true`). A second alignment seek took 105ms, warm alignment 68ms; full handover completed **+4332ms** after Start.
- This is an objective source of startup delay even though perceived waiting can be longer. It **must not** be represented as a 10-second native audio operation: the measured first commanded join is 4.332s. Avoid promising a new specific startup time until measured on HONOR.

### RASKOL: upstream source position is missing from the one controller

- «Нас не понимают вообще», Космонавты / RASKOL, id `42884423`, replacement joined +107805ms from already complete local cache.
- Screen recording shows Yandex scrubber moving to approximately **0:46, 2:45 and 3:41** while this track is visible, but the connected, polled Media3 controller still reported approximately **5.5 seconds** at `playback_health` +112706ms; **no `SAME_ITEM_SEEK`** was published during this item. It next published a **different item boundary** +113645ms. The decoder cannot infer the unseen desired target from a moving UI alone.
- This is NOT evidence that `MediaPlayer.seekTo()` hung; it was never asked to seek to those UI positions. A second Media3 controller, sensitive Android permission, screen scraping, unverified legacy MediaBrowser, or invented target are NOT permitted fixes. Do not claim this issue fixed.

### «Дым»: seek is published, native transport is fast; finger-to-publication may lag

- «Дым», Лёша Свик id `39949113`, joined +165191ms (1309ms from boundary). Visible Yandex progress-bar drag precedes committed events in the recording.
- Three `SAME_ITEM_SEEK` events reached CELIKOM: targets **211506, 106988 and 165073 ms**; native `MediaPlayer.seekTo()` ACK latencies approximately **43, 29 and 19 ms**, and re-join finished in ~124, 108 and 78 ms after request.
- The user's subjective 2–3s wait cannot be attributed to those native seek callbacks. Most likely Yandex commits position when the finger drag ends, or publishes late; there is no measured independent touch-down timestamp. Do not claim the UI delay is definitely caused by a particular upstream implementation without device instrumentation.

### Remaining stall class

- Track id `48591644` had an in-flight lookahead that exceeded the 1.2s current budget; Test.25 canceled the speculative transfer at +123679ms, prepared verified sparse bytes by +124250ms and handed over at +124846ms (2463ms after boundary). The original remained audible during handover. Test.26 does NOT alter this owner-controlled fallback without further evidence.
- Test.25 showed 2 source-buffer/resume pairs and four speculative `download_cancelled` events. There was **no** `replacement_drift_unstable` or replacement recovery in this fresh run; this matches the owner's fewer mid-song dropouts. A full real acoustic assessment is still needed.

## Test.26 narrowly scoped improvement

1. `BufferedAudio.initializeForCurrentPosition(sourcePositionMs,durationMs)` verifies initial block zero first to establish **strong ETag and exact length**, then requests validated metadata tail, prefix block one and **at most one predicted current-position block** in a bounded 3-worker pool. The hint only selects a **prefetch block**; actual seeking remains owned by MediaPlayer, never by byte-ratio guessing.
2. The hint is derived from source Media3 position (+1.6s preparation headroom) and verified media duration. A missing, out-of-range or nonsensical source position disables the speculative hint. Every returned block still requires exact `206`, Content-Range, bytes, consistent strong ETag; concurrent tasks use the same ownership/cancellation lease and `1,800ms` startup budget. If initialization cannot validate its needed blocks, the existing fail-open **full-file fallback** applies.
3. `NativeApi.stream` receives current-position hint through a separate overload used only by Test.26's progressive cold path. The pre-existing signature and frozen local-file baseline remain available. No changes to `ReplacementEngine.seek()/completeSeek()`, source event router, DSP gain/pauses, auth or Android permissions.
4. Host range tests cover the chosen cache block and data byte-exactness, changed ETag rejection under parallel Range, untouched old preparation path, fake API hint forwarding, cancellation and seek baseline. SDK36/D8/original signer/package isolation require full GitHub CI.

## Honest acceptance status

This is **a targeted hypothesis about the measured cold-start range miss**, not a claim that finger seek on RASKOL is fixed. Only a new paired HONOR listening run can establish whether startup and audible transitions improve. Test.23 is still the sole owner-accepted recovery point, and Test.25 remains the last field-tested experimental APK.

Test.26 version `0.3.85-test.26`, code `86111`, package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, original signer must be verified. One complete signed APK, not individual microbuilds. Record final exact source SHA, CI, original signer, APK SHA-256 and direct Library link **after** the build exists; do not invent these values.
