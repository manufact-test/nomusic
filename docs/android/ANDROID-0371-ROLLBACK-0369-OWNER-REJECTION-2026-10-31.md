# CELIKOM Android 0.3.70 rejected on HONOR — return to verified 0.3.69 source

**31 October 2026. Android only. Owner verdict: 0.3.70 FAILED. Do not call a green host/CI run an audio acceptance.**

## The owner's actual listening report

- Frequent finger seeks stuttered in 0.3.70 and seemed to worsen during longer listening; on 0.3.69 the same class of seeks was nearly ideal.
- New-song joining was **not** audibly improved. Short dips and micro-repeats remain.
- System installer «Обновить» still left CELIKOM as a Recents card; the success-only task cleanup added in 0.3.70 did not deliver the desired experience on the HONOR.
- The owner unequivocally rejected 0.3.70, requesting restoration of **0.3.69 functionality**, no renewed tuning and an honest limitation statement for the updater.

## Private diagnostic, scoped to the correct run

File was inspected privately, **not committed or republished**. Partition at `run_start(version=0.3.69)` then `run_start(version=0.3.70)`; do not merge older 0.3.68 events into the comparison. The runs differ in length and activity.

| Metric | 0.3.69 run | 0.3.70 run |
| --- | ---: | ---: |
| Decoder seek completions | 33 | 38 |
| Observed completion time | 21–95 ms | 20–990 ms |
| Decoder seeks over 200 ms | 0 | 14 |
| Decoder seeks over 500 ms | 0 | 2 |
| Source buffering events | 25 | 29 |
| Background prefetch yield/resume pairs | 10 / 10 | 26 / 26 |
| Cold joins | 10 | 7 |

The 0.3.70 passive `replacement_join_clock_summary` samples included transport-clock offsets around 90–283 ms. **Transport timestamps are not measured PCM phase** and cannot explain or certify audible cancellations. The new `replacement_detached_resume_resync` event had **zero observations** in the 0.3.70 run; its absence means this report does **not** prove the newly added long-pause branch was reached, nor that it directly caused the seeks. It is important not to invent single-line causality: the release is rejected by real listening, and long seek latencies objectively reappear, but full causal attribution remains open.

## Reversion boundaries / non-negotiable gates

- Use `a30f949b10a72f62977e70cba30767b7c382a249` as the **exact** old application-code/test source for all files changed in 0.3.70 (except release identifiers). Do **not** tweak transition milliseconds, gain curves, Next, buffering, pause ownership, streaming, audio session or Bluetooth paths.
- Specifically restore `ReplacementEngine.java`, `UpdateInstallReceiver.java`, `TestResumeClock.java`, `TestHonor066JoinLab.java` and `tests/run_engine.py` byte-for-byte from 0.3.69. Delete the 0.3.70-only `UpdateInstallPolicy.java` and `TestUpdateInstallPolicy.java`.
- Change only release identity from `0.3.69/code70` to `0.3.71/code72`, with corresponding manifest contract tests. Reason: installed rejected `0.3.70/code71` cannot accept a standard lower-version `0.3.69/code70` update in place.
- Run the full host regression/negative release suite, Android SDK 36 javac and D8 in **nonpublishing** `feature/android-0371-rollback-0369-staging`. Require staging `publish-stable` SKIPPED before advancing the tested commit to production. Do not touch the immutable `backup/android-0369-honor-listening-control-20261031`.
- The 0.3.70 join-clock instrumentation and the strict detached resume path are **withdrawn** alongside the failed release. Do not re-introduce either without a new reproducible red device-side case; in particular, do not infer gain/PCM phase from transport clocks.
- Keep `0.3.69` in the historical documentation. If the publisher succeeds, `0.3.71` is a **rollback release**, not a new audio fix.

## Updater UX: candid limit

Android provides `Activity.finishAndRemoveTask()` / `ActivityManager.AppTask.finishAndRemoveTask()` to remove tasks from Recents, but the 0.3.70 post-install `PackageInstaller.STATUS_SUCCESS` receiver attempt has **already failed the actual HONOR acceptance test**. There is no evidence here that this receiver executed reliably while the updated app process was being replaced. Relaunching an Activity from the background is also subject to Android background-start restrictions. We **cannot guarantee** either "automatically reopen after replacing the package" or "remove the app task immediately after package replacement" in this app/device pathway. Per owner instruction, this rollback removes the unsuccessful experiment and makes no new updater change. Do not declare this UX fixed or try another speculative workaround.

## Acceptance

A green SDK36/D8/signing/stable publication confirms the code and APK, **not** good sound. The owner alone checks the rollback acoustically on HONOR, with special attention to repeated finger scrubs over time, plus ordinary Next, pause and first joins. Any new diagnostic stays private. Desktop/backend/site/auth/catalog/stable distribution and signing infrastructure are out of scope.
