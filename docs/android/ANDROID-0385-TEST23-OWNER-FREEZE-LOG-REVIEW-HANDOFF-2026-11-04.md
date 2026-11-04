# CELIKOM Android — Test.23 owner-selected immutable rollback baseline and diagnostics

**Date:** 2026-11-04. **Status:** OWNER-SELECTED CURRENT REFERENCE, FUNCTIONALLY IMPERFECT. Do not confuse "reference" with "all acoustic problems solved".

## 1. The exact rollback — NOT just a version label

The owner explicitly chose **Test.23** as the new working baseline after failed attempts to return to Test.15/Test.18 and requested an actual guaranteed rollback reference. Preserve both the exact binary and its corresponding source independently:

| Identity | Exact immutable value |
| --- | --- |
| Source repo | `manufact-test/nomusic` |
| **FROZEN SOURCE BRANCH (do not write to it)** | `backup/android-0385-test23-owner-accepted-20261104` |
| **Frozen source commit** | `251b6facc8739557ff962365da012d502ed3bac8` |
| Working source branch at freeze | `feature/android-0385-test23-selective-merge-20261104` |
| Signed exact APK filename | `CELIKOM-Android-0.3.85-TEST-23-TEST15-SAFE-16-17-MERGE-SIGNED.apk` |
| **Signed APK SHA-256** | `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a` |
| APK byte count | `8796313` |
| **Permanent Library signed APK** | `libfile_301d98360e9c8191b8e05594f402d265`; https://chatgpt.com/library?file_id=libfile_301d98360e9c8191b8e05594f402d265&account_id=personal |
| Verified CI | https://github.com/manufact-test/nomusic/actions/runs/41818842620 |
| CI artifact (expires; SECONDARY only) | `13315749039`, `CELIKOM-Test-0.3.85-test.23-code-86108` |
| Package/label | `pro.celikom.nativeprobe.test` / `CELIKOM Test` |
| Version / versionCode | `0.3.85-test.23` / `86108` |
| Original signing cert SHA-256 | `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` |
| APK integrity / signing | ZIP good, signed checksum matches CI receipt, Android signature v3 valid, original signing cert matches |
| Stable app | `pro.celikom.nativeprobe`, `0.3.85/code86`, NOT CHANGED |
| OTA/Hostinger | NOT CHANGED; stable publish jobs skipped |

**Rollback procedure:** Download the EXACT already-signed APK from the above Library link. Verify the APK SHA-256 matches. Since future Test builds can have higher Android versionCode, directly installing an older Test.23 over them is normally blocked as downgrade. **Do not falsely promise in-place downgrades.** If preserving Test user data/settings is essential, produce a narrowly-scoped **new versionCode** build from exactly frozen Test.23 source, with **no audio-code changes**, using the original signing certificate; disclose it is repackaged and NOT byte-identical to the frozen APK. Otherwise, uninstall only the **separate test package** (losing its local data), then install the exact frozen APK. NEVER touch the stable `pro.celikom.nativeprobe` app, its data, Hostinger or OTA. Do not recommend installing one APK on top of an incompatible signature.

**Source freeze verification:** GitHub API read of the backup ref confirmed it resolves to exactly `251b6facc8739557ff962365da012d502ed3bac8`. The working branch may advance; the `backup/` branch must NOT. Test.15 backup `backup/android-0385-test15-best-owner-20261103` remains separate at `6fde1e48179ecb812f1def16067f18bf0d9c3003`; Test.18 backup also remains separate. Do not force-push, reset or delete any of these.

## 2. Test.23 content and limits

- Exact audio base Test.15; carried from Test.16: read-only 15/30ms bounded fast-join polling and permissionless `AudioPlaybackCallback` diagnostics.
- Carried from Test.17: complete-file lookahead cache reuse after fresh resolve and retaining finished interrupted files under strict conditions.
- Excluded: Test.17 additional DirectSessionObserver/second Media3 controller, Test.18 aggressive cancellation, Test.19 DSP, Test.20 drift experiment, Test.22 range downloads. Accepted seek/ACK and source gain arbitration should remain on Test.15 base.
- **No direct Test.23-specific `replacement_lookahead_cache_reused` or `replacement_interrupted_file_retained` event was found in these diagnostic exports.** Thus presence of code is verified but these two new code paths have not been shown to improve field behavior. Ordinary `replacement_audio_reused` can happen through the prior cache path.
- This is the owner's chosen fallback / starting point, **not** evidence that Test.23 is free of dropouts. Do not silently transfer its baseline designation to another ref or APK.

## 3. Exact evidence from two supplied reports — DO NOT double-count shared history

The owner attached:

1. `CELIKOM-combined-20261104-142226.txt` (Library `libfile_4760cc7e2ec88191b57cd340a521bf63`): contains Test.15 runs 13:57:09/13:57:36 and beginning of Test.23 run 14:21:38.
2. `CELIKOM-combined-20261104-142543.txt` (Library `libfile_c7b87374fdfc8191bd4a618f48388c66`): repeats the Test.15 13:57:36 and Test.23 14:21:38 runs, then new Test.23 run **14:22:31**. The repeated segments are the same historical journal, not new trials.

Environment observed: **HONOR NTH-NX9, Android 13/API33, Yandex Music 2026.09.5 #167.1gpr**, Wi-Fi and validated internet, no VPN at report start. Reports are journal/event data, no raw audio/PCM; claims about actual audible seamlessness require the owner's ear and ideally correlated video, not just event counters.

### 3.1 Run-by-run comparison (boundary-to-`replacement_transition_complete`)

| Run start (UTC+3) | Version | Completed replacement joins | Joins after observed boundary | >2 s | >5 s | >10 s | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 13:57:09 | Test.15 | 3 | 2 | 0 | 0 | 0 | 378ms |
| 13:57:36 | Test.15 | 11 | 10 | 4 | 2 | 1 | 10,018ms |
| 14:21:38 | Test.23 | 5 | 4 | 0 | 0 | 0 | 704ms |
| **14:22:31** | **Test.23** | **25** | **24** | **8** | **5** | **4** | **26,315ms** |

Metric is elapsed from logged source boundary to logged `replacement_transition_complete`. It includes intentional original-audio continuity while waiting and is **NOT proof that the listener heard silence for the whole period**. The user heard unacceptable delayed substitutions and occasional mid-track fallbacks. These trials differed in track/skip sequence; treat them as evidence of real failures, **not a controlled A/B benchmark**.

### 3.2 Longest Test.23 incident — 26.3-second late join

Latest run, relative `elapsed_ms`:

- `126080`: source boundary on another track, original restored.
- `131964`: after live resolve, cached lookahead is still **downloading**; current handoff waits.
- `141964`: **10-second current handoff timeout**, fallback to fresh full-file download.
- `141968`: lookahead canceled; `142046` reports `download_cancelled` after **17,417ms** and **7,584,788 bytes** already transferred.
- `151898`: fresh **current** download finishes in **9,848ms** (11,118,847 bytes, queue wait 78ms).
- `151956` decoder prepared; `152395` replacement transition completed. Difference from source boundary **26,315ms**. Track ID `48591846`.

This is the biggest confirmed defect. A valid in-flight full-file lookahead occupied ~17.4s then was thrown away on timeout, and the current fetch started again. Root-cause **hypothesis**: owner-lease / handoff timeout and cancellation policy not transferring completed/in-flight bytes safely. Need verify from code; do not assume that just lowering timeout is a fix. Never adopt a decoder from the wrong source identity or partially downloaded file.

### 3.3 Other important late joins in Test.23 latest run

- `152844 -> 164498` track `50163063`: **11,654ms**. Lookahead finished in 12,062ms after **3,875ms queue wait**; cached file then reused. Even a cache reuse only occurred after a long network wait.
- `166361 -> 177904` track `39949113`: **11,543ms**, lookahead fetched in 11,664ms; cached file then reused.
- ~`43974 -> 54968` track `42884423`: **10,994ms**; inspect associated resolve/download for exact bottleneck.
- `84864 -> 92593` track `1944605`: **7,729ms**, current full file download **5,088ms** after a changed item invalidated a still downloading lookahead `50163052` (3,905ms transfer already spent).
- Two `replacement_download_failure` records in latest Test.23, both `reasonCode=download_cancelled`, **not proof of server HTTP failure**. Earlier Test.15 comparison run logged four similar cancels; the behavior is still unresolved.

### 3.4 Mid-track audio reports and instrumentation

- Latest Test.23 run logged **24 source boundaries**, **25 seek request / 25 seek ack / 25 seek complete**, **25 exclusive handovers**, **23 original restorations**, and **21 ordinary cache reuses**. Counters alone do not prove good timing.
- Two short `replacement_source_buffer` reports at `38589` and `73313` (at source position zero), followed by `replacement_source_buffer_resumed` after approx **4ms** and **21ms**. User reports audible dropouts or loss of replacement mid-song, but these events alone do NOT establish a multi-second unexplained dropout; correlate `audio_owner_state`, original/decoder positions and user video.
- **368** `replacement_lookahead_prefetch_promoted_inflight` journal messages in the latest 2053-event run, often repeating the same alias/phase every ~250ms. **181** repeats in prior Test.15 13:57:36. This is noisy, likely repeated passive polling; it is not 368 distinct downloads. Event de-duplication would improve diagnostics but is not sound priority.
- `platform_audio_activity_observed`: 152 in latest Test.23, 28 in previous Test.23; no new sensitive permissions. These indicate system audio activity changes, **not Yandex playback transport/position**; do not infer a track's exact state from them.
- 16 cache evictions in latest run, each `reason=entry_limit`, with **8 remaining entries** and ~52–68MiB. Cache turnover on rapid Next may increase cold joins. Possible tuning only after checking identity / memory / storage bounds.
- `replacement_original_restored` on every source boundary is expected fail-open; **never remove restoration to cosmetically hide fallback**.

## 4. Next iteration: scope and non-negotiable safety

1. **Start a NEW feature branch from frozen Test.23 commit** `251b6f...`, never work on backup ref. Work from actual `git` SHA; compare full source tree against the frozen commit before building. Owner requires concrete useful changes, not a mere rollback APK. Never call an installer "the same Test.23" based solely on filename, UI, or `versionName`.
2. Diagnose the **current_handoff_timeout -> canceled 7.6MB -> fresh 9.8s re-download** path (`ReplacementEngine`/prefetch lease/cancel and HTTP transport). Investigate how to preserve safe in-flight work or fall back to original while avoiding repeated cold transfer. Verify strict album/identity matching and exact descriptor key. Do not blindly parallelize downloads.
3. Investigate long 11–12s current joins where original continues, including queue wait and network throughput; distinguish actual file transfer from decoder preparation. Seek improvement without sensitive permissions, global VPN, private audio capture, or user-side complex setup.
4. Mid-track loss: correlate source boundary, media session id changes, `audio_owner_state`, `effectHasControl`, user pause/Next, and decoder state. Keep seek/ACK and pause/resume fixes; never change them casually.
5. Avoid repeated journal spam while preserving high-signal counters; log distinct episode IDs and start/finish times, reason for abort; no account secrets/audio bytes.
6. Integrate and run full host/Android/API36/D8/seek/pause/signing/isolation tests, then produce **one** downloadable direct APK via Library, separate `.test` package, new versionCode, original signer. Do not touch production CELIKOM `0.3.85/code86`, OTA, Hostinger, or its Android package/data. Preserve new version's exact signed APK in Library and create its own backup branch only if owner confirms it surpasses Test.23.
7. If new experiment fails, truly restore **this** frozen Test.23: direct APK if Android permits downgrade, otherwise exact-audio-source rebuild with bumped versionCode (explicitly label as rebuild, preserve diagnostics/settings). Do not use old Test.15 or Test.18 as substitute unless user specifically asks.

## 5. Previous mistakes and owner expectations

User explicitly says several previous promises of saved rollbacks did not produce reinstallable byte-identical APKs, and using a merely old code branch caused new problems. Always **verify binary SHA, commit SHA, original signature, package, versionCode**, back up **actual signed APK**, and provide a direct link. No reassurance unsupported by those proofs. Existing working changes in historical commits are not lost, but not every experimental change was accepted; avoid mixing all changes blindly.

Document predecessor: `docs/android/ANDROID-0385-TEST23-SELECTIVE-16-17-ON-15-2026-11-04.md`. This file supersedes its "owner acceptance pending" designation only with respect to **owner-selected fallback baseline**; sound issues remain OPEN.
