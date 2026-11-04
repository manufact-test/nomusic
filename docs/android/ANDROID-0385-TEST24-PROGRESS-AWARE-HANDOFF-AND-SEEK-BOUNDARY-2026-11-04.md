# CELIKOM Android — Test.24: preserve progressing handoff, bounded cache and seek evidence

Date: 2026-11-04. Status: NEW, UNVERIFIED FIELD EXPERIMENT. Owner's only accepted rollback reference remains **Test.23**.

## Exact starting point and isolation

- Frozen Test.23 source: `251b6facc8739557ff962365da012d502ed3bac8` on `backup/android-0385-test23-owner-accepted-20261104` — **must stay unchanged**.
- New experiment: `feature/android-0385-test24-inflight-handoff-20261104`, branched from the exact frozen source.
- Separate app only: `pro.celikom.nativeprobe.test`, `CELIKOM Test`, `0.3.85-test.24` / `86109`.
- Stable `pro.celikom.nativeprobe` 0.3.85/code86, stable.json, OTA and Hostinger content are out of scope.
- Frozen Test.23 original signed APK is retained at [Library](https://chatgpt.com/library?file_id=libfile_301d98360e9c8191b8e05594f402d265&account_id=personal), SHA-256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.

## Evidence and implemented hypothesis

Test.23 14:22:31 run: 24 boundary transitions; eight >2s, five >5s, four >10s; max 26,315ms. In the largest case, `current_handoff_timeout` at a fixed ten-second current wait invalidated the live lookahead lease after 7,584,788 received bytes / 17,417ms, deleted the partial file, and paid 9,848ms for an entirely new current download. See `ANDROID-0385-TEST23-OWNER-FREEZE-LOG-REVIEW-HANDOFF-2026-11-04.md` for non-duplicated logs.

1. `AudioTransfer.copy` now has an optional byte-progress observer; no audio bytes or URL are logged. It still validates full content size, bounded retries and strong-ETag Range resume; **partial files are never exposed to a decoder**.
2. The current track can hold the *same* promoted prefetch beyond the old ten-second timeout **only** if the download has received bytes within the last 8 seconds. Check every 2 seconds. A temporarily stale Media3 snapshot reschedules the timeout watcher rather than silently orphaning PREPARING. Stalled/no-progress waits fall back; a 45-second maximum prevents indefinite PREPARING. The owner remains the original audible source until the local full file passes the existing measured duration, separate session and owner lease checks.
3. Progress is associated with the exact speculative generation/account; fresh current resolve must match descriptor key (`trackId|replacement_id|version|duration|mime_type`). Stale/wrong-account callbacks cannot retain a lease or start playback. A mismatched live edition still uses a fresh current download.
4. Repeated `replacement_lookahead_prefetch_promoted_inflight` diagnostic spam is deduplicated per phase for one lease. Diagnostic `replacement_lookahead_current_inflight_retained` and `replacement_lookahead_current_stalled` now show received byte counts and progress ages to distinguish slow-but-live from failed handoff.
5. Bounded private audio cache increased **8 files / 96MiB → 12 files / 128MiB** to reduce repeat cold joins after 16 entry-limit evictions in the owner trace. Same fresh resolve, exact edition key, account/Stop cleanup and file bound remain mandatory.

The fixes target duplicate downloads and cache churn. They **cannot accelerate an intrinsically slow first uncached full-file network transfer** (previously 5–12s), nor can a host test prove seamless speaker audio.

## Important limitation: Yandex UI finger scrubbing on «Дым» and RASKOL

User again reports that a finger seek in Yandex may leave CELIKOM's replacement running at the old position. Previous controlled reports show why:

- «Дым» / track 39949113: Yandex UI seek moved, but CELIKOM's sole Media3 controller kept reporting seconds near the start and did not emit a `SAME_ITEM_SEEK` event.
- «Нас не понимают вообще» (RASKOL) / 42884423: the UI moved first, but the Media3 position jump arrived seconds later. When the new position reached the app, the existing native seek/ACK completed promptly.
- AudioPlaybackCallback has no Yandex track position. An earlier direct second Media3 controller and legacy browser gave no reliable fresh position; the former coincided with serious pause/seek regression and is intentionally excluded.

The accepted local-file `seek()/completeSeek()` and pause/ACK remain byte-identical to Test.23 and are protected by `check_0385_seek_baseline.py`. No new sensitive permissions or second controller were introduced. **Test.24 does not claim that the externally invisible finger seek is fixed.** A correct remote seek target is not inferable from anonymous audio activity, a playback clock or an older Media3 snapshot. A future solution requires observable trustworthy transport position; guessing and muting source blindly would worsen audio safety.

For the user's field test, record separately whether CELIKOM replacement was actually active (`replacementArmed=true`, `replacementReady=true`, `audio_owner_state=REPLACEMENT`) when testing each finger seek, and whether `source_discontinuity`/source position changed before `replacement_seek_request`. Also test Pause→Play, rapid Next, first uncached songs, mid-track replacement continuity, and repeated track cache reentry.

## Verification and release gates

- Deterministic handoff regressions: progress at 10s must keep one download; successful completion must be reused; lack of progress must fall back; hard deadline applies even to trickling requests; edition/account/boundary mismatches must never adopt stale bytes.
- Complete Android host suite, baseline seek hash, architecture regression, Android API36/D8, separate-package signing and signature checks before delivering one APK.
- Original signed APK from frozen Test.23 remains the rollback reference. If Test.24 is worse, use the exact saved Test.23 APK (only after uninstalling the separate Test app if Android blocks downgrade), or an explicitly marked exact-source repackaging with higher versionCode for in-place recovery.
- Keep Test.24 as experiment only until the owner confirms actual HONOR/Yandex listening. Never overwrite Test.23 backup on the strength of CI alone.

## Signed build completed — repeatable provenance

CI **SUCCESS**: https://github.com/manufact-test/nomusic/actions/runs/41827246558. Original functional source commit `136caff44c6db10ec52b57bb712ee41fe1b79921` (tree `1d7d8fec19053b7e9004caa0862518c52bd622eb`). All native host/Android API36/D8 gates, accepted seek hash and release isolation checks passed. Stable publish was skipped. Physical listening acceptance is **pending**.

| Property | Verified value |
| --- | --- |
| APK | `CELIKOM-Android-0.3.85-TEST-24-HANDOFF-RETAIN-SIGNED.apk` |
| **Permanent signed APK** | https://chatgpt.com/library?file_id=libfile_5d1ffa5a20348191a1f6959ecd1117cd&account_id=personal |
| **SHA-256 APK** | `47115dae7487b727d9fb3d7e74e92324fe208f7293073f7930f0c4c75866aed5` |
| APK byte count | `8796313` |
| Package / label | `pro.celikom.nativeprobe.test` / `CELIKOM Test` |
| Version / code | `0.3.85-test.24` / `86109` |
| Signing certificate SHA-256 | `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` |
| Verification | Original signer matched, APK signature v3 valid, isolated Test sandbox, unique authorities, no OTA updater |
| Secondary CI artifact (expires) | https://github.com/manufact-test/nomusic/actions/runs/41827246558/artifacts/13320615401 |

The downloaded CI artifact ZIP passed archive validation and digest `36115d4b724500524badbce54c2381a80dfbcb057055b6e9c2775e589799dc98`. Its extracted signed APK was independently hashed and matched the CI receipt and verifier. The original signed APK is stored in the owner Library, **not** merely a Git commit or expiring Action artifact. Do not promote Test.24 to rollback baseline before owner approval.
