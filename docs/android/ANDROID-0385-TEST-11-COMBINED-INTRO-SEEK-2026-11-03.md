# CELIKOM Test.11 — one combined seek and intro candidate (2026-11-03)

## Owner instruction

Do **not** ask the owner to install one APK per narrow fix. Batch every bounded, evidenced change into **one** test app and ask for one combined listening/seek pass. Test.10 was already built but not the owner's final test candidate. This Test.11 supersedes Test.10 for the next device check.

## Input evidence

- Freshest private user files: `CELIKOM-combined-20261103-150348.txt` and `SVID_20261103_150238_1.mp4`. Only the segment beginning at line 3557 (Test.9 run at 15:02:22 +03:00) is new; previous Test.7/Test.8 logs are included historically.
- “Дым” alias77: owner visibly scrubbed the Yandex UI toward ~3:16/3:39, but Media3 source current position still around 9.7s and then 11.5s; **no same-item source seek** and no CELIKOM seek request during the track. Other songs do emit seeks and native seek ACKs, so the accepted `ReplacementEngine.seek()` / `completeSeek()` code is not responsible for this example.
- Test.9 source alias77 boundary 23783ms → fresh resolve23948 → primed decoder adopted23950 → initial alignment ACK23967 → alignment completed23969 → effect attached24237 → WARM seek24280 → exclusive command24417. **A 268ms gap from first alignment ACK to the next effect creation** coincides with the 250ms periodic source observation cadence. This can waste first-note time and force a second WARM adjustment. Most other joins have 24–69ms between alignment complete and effect creation; the outlier is timing-sensitive, so avoid declaring universal improvement without HONOR evidence.
- Test.9 initial track (not “Дым”) had source-vs-decoder drift rising from112ms at14.2s to755ms at17.8s to1087ms at19.3s. Existing fail-closed fallback restored original; root audio clock cause is not verified. Do not reset frozen seek, attempt uncontrolled transport operations or claim that acoustic phase can be measured from Media3 timestamps.
- There was **no invocation of Test.9's new 150ms promoted-prime wait** in this owner's run. Do not blame the subjective slight deterioration versus Test.8 on that unexecuted branch.

## Combined Test.11 changes

Work branch `feature/android-0385-intro-join-investigation-20261102`, separate APK `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, code **86096**.

1. **Includes Test.10 rare scrub fallback, not previously field tested**: a separate passive Android platform MediaBrowser + MediaController reads the same Yandex service session as a backup. The new source position is only trusted when exact title/artist and duration agree, both playing states agree, state is recent, and position divergence >=4s survives two observations over >=250ms. Then the existing accepted native seek code gets a corrected source position. If any required evidence disappears, the original plays; no transport command, notification access, or new permissions.
2. **Fixes a Test.10 pause-after-recovery edge case**: after the passive source has been verified, simultaneous paused states preserve that same position for a bounded hold (up to five minutes), without spuriously falling back merely because `isPlaying=false`. Stale paused platform state beyond that limit still fails closed. This is covered by host tests.
3. **Fast, bounded source observation only after a ready current decoder**: an additional read-only source sample at35ms, then every60ms for at most1200ms, and only while playing with the verified decoder ready, trusted session attached, source identity matching and output not yet handed over. It ends as soon as the effect is attached, the song changes, audio is paused, arm is revoked or the deadline expires. Normal sampling is still250ms. This targets the measured 268ms post-ACK blind interval without changing the accepted seek function, handover clock gate, audio ownership, gain law, Next routing or speculative permission. It may save first-note time and avoid one unnecessary WARM correction.
4. New pure host test `TestFastJoinPollPolicy` verifies bounded cadence and all negative gates; `TestLegacySourcePositionPolicy` extends coverage for paused recovery/expiry. Both are compiled and run by the signed test builder.
5. Existing Test.8/Test.9 primed-decoder lifecycle fixes remain; no speculative revert of a code path that did not execute in Test.9. The known drift fallback is retained rather than replaced with an unverified audible corrective seek.

## Safety, CI and field validation

- Stable original **0.3.85/code86** and its OTA/Hostinger, backup refs, accepted HONOR seek/Pause/Resume, and PR#37 remain untouched/unmerged.
- Native host regression and golden seek source hash, full API36 Android compile/D8, test package identity/signature/receipt must all pass before delivering the single new ZIP.
- **No acoustic acceptance until owner tests one combined Test.11 APK** (starts, manual/automatic Next, repeated seeking, pause/resume on same track, ordinary listening). Upload one combined log/video if anomalous. If the platform browser is unavailable, expected log event is `legacy_position_source_unavailable`; `source_seek_platform_recovered` means the fallback was exercised. The fast sampler logs `replacement_fast_join_poll_started` when it runs.
- Do not ask the owner to do separate Test.10 and Test.11 tests; Test.11 supersedes.

## Verified Test.11 build receipt and next owner handoff (2026-11-03)

Functional SHA `7cb3cc190d614dd23646fa9b64a233e5f91162d4` passed all CI checks: [run #41638455540](https://github.com/manufact-test/nomusic/actions/runs/41638455540), conclusion **success**. Signed test artifact [ZIP ID 13231786977](https://github.com/manufact-test/nomusic/actions/runs/41638455540/artifacts/13231786977); APK `CELIKOM-Android-0.3.85-TEST-COMBINED-SEEK-INTRO-SIGNED.apk` SHA256 `dc3d1026948d4b8e5978a5d116d09ceb2b57ff2d7ca2b1c347d1e60e25a52089`; package `pro.celikom.nativeprobe.test`, versionName `0.3.85-test.11`, code86096, v3 signature valid, original signing certificate, size 8,788,121 bytes. OTA absent, stable publish skipped. **Still unverified on HONOR.** Test.11 subsumes Test.10: owner will supply one combined report to next chat; see [ANDROID-0385-TEST-11-VERIFIED-HANDOFF-2026-11-03.md](ANDROID-0385-TEST-11-VERIFIED-HANDOFF-2026-11-03.md).
