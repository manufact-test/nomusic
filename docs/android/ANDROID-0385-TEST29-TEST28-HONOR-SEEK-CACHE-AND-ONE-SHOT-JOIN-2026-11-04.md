# CELIKOM Android Test.29 — Test.28 HONOR diagnosis, verified cache and one-shot cold join

Date: 2026-11-04. Candidate only; no physical audio acceptance yet.

## Source, real log and preserved baselines

- New experimental branch `feature/android-0385-test29-demand-cache-20261104` created from Test.28 docs HEAD `f85a62913a1b44a1467869e71336bfa1c5580d23`. Exact signed Test.28 source is `904ba52d5afbb5e77f4ee36e40d321d568896460`.
- **Only the fresh run** of private owner `CELIKOM-combined-20261104-181257.txt` was analyzed: combined JSONL lines 1–1436 = Test.26, 1437–3831 = Test.27, **fresh Test.28 from line3832**, UTC+03 `2026-11-04T18:09:52`. Correlated with `SVID_20261104_180949_1.mp4`. Never commit the private journal/video.
- Test.28: 17 source boundaries, 40 completed output transitions, 59 native seek ACK pairs, 27 `replacement_exclusive_soft_join_start` events (some incorrectly repeated after scrubs).
- RASKOL track `42884423`: first stream join +118057ms; after finger seeks an ACK took 516ms at +128803, then another 39ms correction. The *first-cold-only* 32/48ms source duck ran again +123915 and +128956. In video Yandex briefly shows its ▶ paused UI while Media3 still reports playing; CELIKOM receives no authoritative pause event.
- «Дым» track `39949113`: boundary +155867, prepared +157605, Yandex source buffering until +161311, first join +161888. User seek +166438 had a **1792ms** Range-blocked native ACK at +168203; source advanced, forcing more silent correction seeks +168252 (**565ms**) and +168820 (**44ms**) before handover +169016. A later +173914 seek ACK took 152ms. Repeated cold envelope +168898/+174174 is contrary to intent.
- Fast fully cached seeks in this same run complete in 9–105ms. Speed depends on byte availability and source event delivery, not a single global timer. Native ACK alone cannot measure the time from physical touch to audible sample.

## Test.29 integrated changes

1. Current-song `BufferedAudio` background fill groups up to **four adjacent 128-KiB missing blocks** into one verified **512-KiB Range** instead of one HTTP request per block. This reduces per-song VPN/TLS round trips and aims to complete the whole private cache sooner, helping subsequent random seeks.
2. Foreground decoder misses **still request exactly one block**. Real foreground reads disconnect/yield stale background transport off the decoder thread. Partial, interrupted or malformed batches expose zero unverified blocks; `206`, exact Content-Range, unchanged strong ETag/total and full bytes remain mandatory. If a CDN declines a wider background range with 200/416, one-way downgrade to the original single-block behavior rather than sacrificing playback. Add `replacement_stream_prefetch_batch` to diagnostics.
3. First cold 32ms source-only duck and 48ms replacement rise runs **at most once per media item** and never after a genuine same-song user seek. Subsequent verified seeks use the existing clock/owner-gated exclusive handover without repeating the 80ms initial envelope. No cross-session PCM-phase guess, extra source observer or permission.
4. Retain existing lookahead isolation, account/track fencing, same-song seek priority, original-source fail-open, source Media3 read-only state, safe original DSP restoration and full-file fallback. Do not change CELIKOM production, Hostinger or OTA.
5. Side-by-side test package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, `0.3.85-test.29`, versionCode **86114**, original signing certificate. CI must pass native host, Byte Range/cancellation/cache and exclusive seek regressions, API36/D8, signed package and certificate verification. Test code must not go to stable channel.

## Known limits and rollback

- A genuinely uncached seek still needs a network response. A slow or blocked VPN/CDN cannot be made instantaneous by Java. Batch prefetch aims to reduce *future* misses; physical HONOR results required.
- If Yandex UI state is not published through its Media3 session, the connected controller may keep showing `isPlaying=true` despite on-screen pause. The failed passive `MediaBrowser` and noisy anonymous audio-count callback are not reliable alternatives. Test.29 does **not** claim that missing event solved, nor add Notification Listener/Accessibility without a proven need and user-visible privacy tradeoff.
- Exclusive command-level gains are not a measurement of speaker PCM; sound quality must be judged by the owner, not CI.
- Preserved immutable Test.28 backup `backup/android-0385-test28-owner-selected-20261104` → `904ba52d5afbb5e77f4ee36e40d321d568896460`, original Library APK `libfile_dbc76474748481918f72b91a9eaea383`, SHA256 `973ee8565170d333c2ad7a8319f66c099c4afc2388228d3833562ffde7361b12`, rollback kit `libfile_ac28d52232748191b64a1847e2bcefb9`.
- Preserved owner-accepted Test.23 backup `backup/android-0385-test23-owner-accepted-20261104` → `251b6facc8739557ff962365da012d502ed3bac8`, original Library APK `libfile_301d98360e9c8191b8e05594f402d265`, SHA256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.
- Reinstalling original older Test.28/code86113 or Test.23/code86108 after Test.29/code86114 normally requires uninstalling **only** `pro.celikom.nativeprobe.test` (loses only isolated Test-app local data) and then installing the original preserved APK. Data-preserving rollback instead requires a separately named, signed higher-code recovery package from the exact frozen sources; it is not byte-identical to the original.

## CI and original signed APK, after successful build only

- Exact source SHA: **PENDING**.
- Full CI run: **PENDING**.
- Original signed APK direct ChatGPT Library link, byte size, SHA-256 and v3 signing proof: **PENDING**.
- Physical listening/owner acceptance: **PENDING**. Do not create accepted Test.29 backup before explicit owner selection.
