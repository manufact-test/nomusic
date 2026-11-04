# CELIKOM Android Test.25 — Test.24 rejected; bounded sparse cold join and one drift recovery

Date: 2026-11-04. Status: experimental Android Test APK; **not owner-accepted**.

## Owner rollback — absolute freeze

- **Only owner-accepted rollback:** `backup/android-0385-test23-owner-accepted-20261104`, exact SHA `251b6facc8739557ff962365da012d502ed3bac8`.
- Original signed **Test.23** APK: [ChatGPT Library](https://chatgpt.com/library?file_id=libfile_301d98360e9c8191b8e05594f402d265&account_id=personal), SHA-256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.
- Do not touch backup branch, stored APK, stable application `pro.celikom.nativeprobe` 0.3.85/code86, Hostinger, `stable.json`, production publish or OTA.
- **Test.24 was expressly rejected** by owner. It did not shorten cold full-file waits and aggravated first Start. Never present Test.24 as rollback reference.
- Test.25 separate isolated package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, version `0.3.85-test.25`, code **86110**, original signing certificate required. New branch `feature/android-0385-test25-progressive-continuity-20261104` created from exact Test.23 SHA, not Test.24.

## Fresh Test.24 field evidence (one run, no historical double-counting)

User supplied `CELIKOM-combined-20261104-152751.txt` and `SVID_20261104_152526_1.mp4` on HONOR NTH-NX9 / Android 13 / Yandex 2026.09.5. Test.24 run starts `2026-11-04T15:25:09+03:00`; earlier appended Test.23 journal segments are history.

- **First Start** «Пушка» id 85025192: foreground resolve + complete 8.18 MB transfer in 5,926ms, replacement audible handover at +7,875ms. Test.24 only preserved prefetch transfers, could not speed a first full-file download.
- **Source dropout mid-song** same «Пушка»: drift +124ms at +17,789ms, +813ms at +18,778ms, then +1,005ms at +20,305ms triggered `replacement_drift_unstable` and original-only for that song. This happened *before* the subsequent media seek event, and is a directly observed fault.
- **Long current handoff** id 106618982: boundary +60,338ms, lookahead retained through downloads; joined +76,082ms = **15,744ms**. Preserving bytes prevented duplicate download but did not help the user hear the replacement sooner.
- **RASKOL** id 42884423: full cold download 5,492ms and replacement join 6,193ms after boundary. Screen video shows Yandex scrubber around 1:23 while CELIKOM's one Media3 source reports seconds near the start, with no same-item discontinuity available to the decoder. This is an **upstream missing position event**, not slow native `MediaPlayer.seekTo`.
- **«Дым»** id 39949113: cold transfer 11,415ms, join 13,084ms. At +151,817ms a real Media3 seek became visible; native seek ACK in 128ms and completed. That does **not** prove the finger scrub was visible on time or audible.

## Test.25 engineering changes and scope

1. **Cold join tries verified sparse MediaDataSource first**, rather than waiting for all bytes. The existing `BufferedAudio.initializeForPlayback()` requires three validated HTTP 206 Range blocks, exact Content-Range, strong matching ETag and bounded size. The original remains audible during preparation and seeks. A strict 1,800ms startup deadline cancels unsupported/slow sparse probes; the **unchanged** full-local-file path then runs as fallback for that track. Successful sparse start continues the existing bounded cached Range prefetch; complete sparse files can be reused as local files on subsequent tracks.
2. A separate **foreground sparse initialization lane** prevents a slow speculative full-file lookahead from blocking the current verified sparse probe. No second audio controller, Android permission or speaker owner is introduced.
3. Promoted **incomplete** lookahead is given up to **1,200ms** to finish; then that speculative lease is invalidated before initiating the fast verified sparse start (with full-file fallback). Ready promoted files remain immediate local cache hits. This explicitly trades a possible abandoned partial transfer for a shorter current-track delay. Test.24's 45s retain experiment is **not** carried over.
4. Sustained **700–1,500ms** drift now receives at most **one muted existing decoder seek** after 650ms, while original source has unity gain. If drift persists through a new 1,500ms confirmation window, the original is restored and the song is marked unsupported. The one-per-track correction budget is **not reset** by a fleeting healthy reading. This addresses the observed Test.24 mid-song dropout; source ownership/fail-open is retained.
5. Existing native `seek(...)`, `completeSeek(...)`, golden local full-file selection, DSP pause and Android ownership logic are **unchanged**. New production Test-only opt-in is explicit in `ProbeService`. `check_0385_seek_baseline.py` still protects the original methods. Host gates include new Test25 sparse startup/Range fallback/cancel, clock medium drift and a real sanitized HONOR clock fixture.

### Known limitation — Yandex finger seek is not solved in all cases

If Yandex moves its UI progress bar but its Media3 session does not publish the position/discontinuity to CELIKOM, this permission-free app has no trustworthy target position for `seekTo`. A hidden/stale position cannot be guessed from audio activity. The existing one controller is retained; past second-controller and legacy-browser experiments did not solve this safely. **Do not tell the owner that «Дым» or RASKOL finger scrubbing is fixed until fresh paired video+diagnostics prove the Media3 event and audible output agree.** Better cold join / bounded drift recovery are real code changes but still require a real HONOR listening test.

## Verification and rollout rules

- Local full Java fake engine and regression suite (with pinned org.json jar), Test25 7 new checks, accepted golden seek hash, architecture and isolated APK policy: **PASS**. Mandatory Android SDK36/D8, full Android host suite, original signer and APK v3 checks must pass in GitHub CI before delivery.
- User receives **one** complete signed direct APK in Library, never many builds for individual fixes. Document exact functional SHA, CI URL, APK SHA-256 and Library link after signing.
- Test.25 may install over Test.24 with `versionCode` 86110. If it is worse, the original Test.23 signed APK remains available, but Android downgrade normally requires uninstalling only the **Test** package (loses Test-app data); an accurately labeled *repackaged exact Test.23 source* with a higher versionCode could preserve data if explicitly requested. Never call repackaged APK byte-identical to the original.
- Next field run: record (a) first Start join, (b) natural+rapid next, (c) RASKOL and «Дым» finger scrubs while replacement audible, (d) pause/resume, (e) «Пушка» mid-song drift, (f) whether sparse probe succeeds or falls back, (g) actual original-versus-replacement listening. Only owner can accept a replacement rollback baseline.
