# CELIKOM Android — Test.20 rejected, Test.18 sound restored as Test.21 (2026-11-04)

## VERIFIED — Test.21 signed rollback ready
- Functional restoration packaged at source SHA `a706d4855c2e6b9b88e308782ea171d3ff9fe625` and full CI SUCCESS https://github.com/manufact-test/nomusic/actions/runs/41804036697 .
- Signed ZIP: https://github.com/manufact-test/nomusic/actions/runs/41804036697/artifacts/13309252135; contains `CELIKOM-Android-0.3.85-TEST-21-TEST18-RESTORE-SIGNED.apk` and verification JSON; artifact retention seven days.
- Signed APK SHA-256 `463e9c5cbf30aaba9b67f7a8e803161d469ee78610a3e67196407f5b9c9909c7`, Android v3 signature verified, separate Test sandbox/icon/authority, OTA absent, stable untouched.
- SHA diff against immutable Test.18 confirms **zero modifications to audio, playback, seek/ACK, or transport code**; the only non-document changes are the test version spec, contract, and signing workflow package naming.
- This restores known-good Test.18 audio in-place without uninstall. It does NOT solve measured 5.7–12.1s cold downloads and should not be marketed as a latency fix.

## Decision and deployment
- **Test.20 is REJECTED by owner**: 5–7s perceived join latency, and some songs noticeably later. Do not distribute as best build. Old signed test20 CI 41798899375 remains a historical artifact only.
- Audio accepted baseline **Test.18** immutable backup `backup/android-0385-test18-best-owner-20261103`, SHA `1a19ccec674d41b7417f29715d853eb693595687`, signed ZIP https://github.com/manufact-test/nomusic/actions/runs/41704016656/artifacts/13265222571 . Do not overwrite.
- Latest development branch `feature/android-0385-test15-permissionless-recovery-20261103` first explicitly restored the EXACT Test.18 bytes in **all 8 code/test/workflow paths modified by Test.20**, rollback commit `522c3a686b4e550e42f8f34d4820c8450dcc114d`. Comparison should have **zero audio-code differences** from Test.18.
- For painless user rollback over installed Test.20 (versionCode 86105), build an **in-place, identically signed** Test.21 package `pro.celikom.nativeprobe.test`, version `0.3.85-test.21/code86106`, with only version/spec/contract/workflow changes atop restored Test.18 code. Do not suggest installing versionCode 86103 directly over higher 86105, which Android may refuse; keep user app data/cache.
- Production `pro.celikom.nativeprobe`, 0.3.85/code86, stable OTA and production SHA untouched.
- Full CI passed and signed Test.21 artifact recorded above. Accepted Test.18 baseline remains rollback anchor; Test.21 is functionally Test.18, but owner must confirm on phone.

## New recording forensic facts
Provided `CELIKOM-combined-20261104-115530.txt`, screen recording `SVID_20261104_115426_1.mp4`. Combined TXT has Test.18 earlier segment and Test.20 from line 1641 (run_start UTC 2026-11-04T11:54:11+03:00).
- **Zero** `replacement_bounded_drift_realign` and **zero** `replacement_drift_unstable` during this Test.20 clip. The Test.20 new 700ms medium-drift recovery branch **never executed in this observed run**. We cannot attribute the late starts in this recording to that branch.
- The observed bottleneck is concrete: pipeline uses `ReplacementEngine(ProbeService owner){this(owner,true);}` and `replacement_full_file_experiment_start` (`streamingSkipped=true`). It waits for the **entire replacement file** before prepare/handover:
  | Track | Resolve start | Entire file downloaded | Exclusive join | Wait after resolve |
  | --- | ---: | ---: | ---: | ---: |
  | Пушка — 10AGE (85025192) | 0.323s | 6.046s, 8.18 MB | 6.587s | ~6.26s |
  | Нету интереса — 10AGE (78608850) | 24.482s | 36.461s, 7.41 MB | 36.886s | ~12.40s |
  | Старые фото — KEER (107389859) | 40.496s | 52.561s, 6.03 MB | 52.970s | ~12.47s |
  | track 105929447 | 61.643s | 63.877s | 64.283s | ~2.64s |
  | track 125724528 | 69.345s | 71.554s | 72.038s | ~2.69s |
- Crucial: `replacement_download_failure` near each successful download was **priority=lookahead, reasonCode=download_cancelled**, NOT the **priority=current** download (which succeeded). The speculative next-track prefetch was preempted/cancelled and failed to spare the next full-file wait. This reflects known foreground-priority preservation, not a global network failure.
- Screen recording (~36.56s) visually shows Yandex already playing while CELIKOM Test says `Подготавливаем версию CELIKOM...`, then eventually `Играет версия CELIKOM`.
- The accepted Test.18 often sounded quicker when warmed/cached. Since Test.21 uses identical code, **it does not by itself guarantee fast first play on cold, uncached songs**. A follow-up experiment must specifically address cold startup without regressing RASKOL/Dym seeks or first-note acoustic quality.

## Where to look next (no implementation in restore build)
1. Separate **current download wait**, **cache hit/miss**, **speculative prefetch blocked/preempted**, and **decoder prime** timestamps. The dominant observed latency is HTTP file transfer 2–12 seconds, not the ~0.1–0.4 second local handover.
2. Explore a **single-owner** safe progressive/partial-file decode strategy with a retained local-file fallback, or feasible foreground download acceleration / bounded priority warm-cache, only in a new test branch. The existing alternate `api.stream` path is behind `fullFileExperiment=false`; prior streaming/seek issues must be preserved as regression checks and not blindly reenabled.
3. Ensure next-track speculative prefetch never steals bandwidth/control from current track. No second independent observer, no Android permissions, no unverified two-sessions blend.
4. Quality goals: first syllable at time zero, transition smooth, finger-scrub RASKOL and Dym, pause/resume Dym, continuous background, live admin approval while playing.

## Owner check
Install Test.21 *over Test.20* without uninstalling; listen to same songs to revalidate accepted Test.18 behavior and preserve cache. Send one combined log/video when ready. If old Test.18 behavior is still poor on uncached songs, diagnose startup separately; do not keep increasing ClockSupervisor resync thresholds.
