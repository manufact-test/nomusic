# CELIKOM Test.8 — intro decoder retention and cold-only alignment (2026-11-03)

## Owner field evidence (Test.7)

Owner installed `0.3.85-test.7` / code86092 on HONOR NTH-NX9 and submitted two combined diagnostics: `CELIKOM-combined-20261103-124420.txt` and `CELIKOM-combined-20261103-131425.txt`. The second contains the first run plus further Test.7 events; **do not double-count**. Raw journals remain private and are not committed.

The relevant Test.7 run began 2026-11-03 12:40:23 +03:00; it has 17 source boundaries and 18 cold join starts (first initial attachment excluded from boundary medians). All 17 upcoming files were ready before the source boundary. Boundary→cold join median **257 ms**, max **554 ms**. Boundary→exclusive output command median **530 ms**, max **838 ms**. The comparable prior Test.6 run had 11 boundaries, cold median 239 ms, max 2196 ms; exclusive output-command median 494 ms, max 2541 ms. Different runs/tracks; this is not a paired benchmark.

**Root-cause evidence:** two ready speculative decoders were discarded before use:
- At elapsed 1596 ms, preparing the unrelated current item called `takePrimedNext(...)` with another alias and destroyed the correctly primed upcoming decoder (`not_ready_or_live_key_mismatch`).
- At elapsed 1219328 ms, prefetch of the new successor invalidated the *already promoted current* speculative decoder during its still-pending fresh server resolve (`prefetch_invalidated_new_next_item`). That boundary needed new decoder warmup and took 838 ms to output command.

Thirteen of the 17 boundaries required an additional muted WARM alignment correction after the initial cold alignment. A distinct, bounded initial cold-position lead is the Test.8 experiment. **Neither transport clocks nor command completion proves actual PCM continuity.** Owner still hears some joins, often more noticeable at higher volume.

No rare unlock/seek failure was observed; seek submission/ACK and Pause/Resume must remain unchanged. The six session broadcasts in this Test.7 run all carried the trusted session ID 75561; there was no new-session mismatch, so the Test.7 stale-session fail-closed fix was **not field-exercised**. No unexpected mid-song replacement loss was established.

## One combined Test.8 candidate

Work branch: `feature/android-0385-intro-join-investigation-20261102`; separate package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, versionName `0.3.85-test.8`, code **86093**.

1. `takePrimedNext` no longer discards a primed *future* decoder while preparing a distinct current alias; same-alias key/account/file mismatch still fails closed.
2. A ready primed decoder promoted to current is retained for at most 800 ms while awaiting the fresh current-song resolve. New next-candidate prefetch is retried after 200 ms. On late authorization, the bounded lease expires and the existing fallback remains.
3. **Cold attachment only:** the first muted local-file alignment seeks up to 70 ms ahead of the current projected source position. It still uses the frozen accepted seek/ACK methods, the existing 100 ms transport-only drift guard, maximum two WARM corrections and original-audible fallback. No in-song user seek, Pause/Resume, gain handover, Yandex effect ownership or audio-session policy is changed.
4. Host regressions cover unrelated-current prime preservation, promoted current authorization race, delayed next candidate, and cold-only predictive alignment.

This is an experiment, not an acoustic acceptance. If it causes overshoot/new artifacts on HONOR, roll back Test.8 to the installed Test.7 without modifying stable.

## Release safety / verification pending

The candidate must pass the complete native host suite, `check_0385_seek_baseline.py` unchanged, Android API36/D8, dedicated Test package and original signer, stable publisher SKIPPED. Build precisely one signed, nonpublishing Test.8 APK. Do not alter stable 0.3.85/code86 (SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`), either accepted-seek backup, stable.json, Hostinger, or merge PR #37.

User does **not** need to rerun a special seek test. The next field check is ordinary song starts/transitions with Yandex `Плавный переход` OFF, then combined diagnostics and subjective listening verdict. If the rare unlock seek bug occurs naturally, preserve its telemetry without changing the accepted seek code.
