# CELIKOM Android A1 NAV41 — current Player PeriodID vs active SLOT_B at non-EOS audio read (READ ONLY)

19 November 2026. Android 13 original Yandex 2025.10.4 #120.1gpr, cloned owner laboratory; **not stock app alteration**.

## Precisely what changed

Retained the single original Yandex ExoPlayer, renderer, decoder and sound route. No new player or arbitrary audio interception. NAV40 signed code `34cb32c88a11743a64c9f4814fa71957223a1391` and backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` remain untouched.

A minimal NAV41 read-only observation was added to `NativeRendererStreamEvidence.onRendererTypeStateRead()` only after the existing independently tested renderer stream/holder/engine links and **fresh exact SLOT_B match**, with original renderer type 1, state 2, result -4 and `isEndOfStream() == false`. No new hook is installed. It reads only original e PlaybackInfo current MediaPeriodId and exact active SLOT_B holder period info ID (the two paths previously signed-DEX pinned at `e.break` PCs 1260/1262 and 1266/1268). Seven exact field *names* are compiled ephemerally in private issuer-signed CI and never stored in git, logs or owner exports. ID UID field is anchored at PC1264 and two distinct integer fields at PC1282/1295, with original paired reads at PC1291/1297.

The in-process observation compares exact references and integer equality only, without calling `equals`, hashing, printing values, or changing vendor behavior. It double-checks PlaybackInfo, PeriodID, UID and index values for concurrent changes and rechecks the **live SLOT_B pointer after sampling**. If any field/slot changes or becomes unavailable, the sample is rejected.

## Diagnostics (only finite enum counts)

- `PLAYER_PERIOD_AT_AUDIO_READ`: registration status.
- `PLAYER_PERIOD_AT_READ_SAME_REFERENCE`: exact Java MediaPeriodId reference identity at one non-EOS read.
- `PLAYER_PERIOD_AT_READ_UID_AND_INDEX_MATCH`: distinct ID instances with the same UID object ref and both integer fields equal; **not a queue generation**.
- `PLAYER_PERIOD_AT_READ_UID_ONLY`: UID same reference but integer mismatch; may be stale/replay.
- `PLAYER_PERIOD_AT_READ_DIFFERENT`: different UID references.
- `PLAYER_PERIOD_AT_READ_UNAVAILABLE`: snapshot invalid, missing, changed or reflection failed.

No raw values, titles, account/token data, URLs, Track IDs, audio bytes, periods or full Java identity strings are exported.

## CI and gating

- [Signed original static private-field generator CI #44527901915 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44527901915). Original 16 publisher-signed XAPK splits and pinned base unchanged; same exact field anchors proven.
- [JVM observer and fail-closed model CI #44529331046 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44529331046). Negative cases include EOS, wrong type/state, stale live slot, UID-only, different period, null and disabled hook.
- Android 13 ARM, original-first/persistent owner signing and export run [#44529576455](https://github.com/manufact-test/nomusic/actions/runs/44529576455) **initiated; not claimed successful until completed**. APK export requires explicit post-native acceptance and persistent owner signer; original stock app must stay installed. Build is marked `NAV_V41_PLAYER_PERIOD_SLOTB_NON_EOS_READONLY`.
- Read-only model/code commit `74df48624f79051276924326a8bd77dc1afe4174`; owner-export intent `c8e73015493c50c05fa97aaf9febdf802c48c864`.
- Do NOT treat prior failed CI runs caused by old NAV40 test marker assertions as vendor playback failures; the current typed tests were updated to NAV41 without removing NAV40 guards.

## Hard NO-GO

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. A same-reference ID, same UID/index, Player current Period and active queue comparison alone are **not** selected Track/album/edition/generation, permission to replace sound or audible PCM. This is a discriminating phone test, not a claim of working uncensored songs.

## Next action: one phone test if signed APK is released

Install NAV41 over NAV40 without removing data. Test 2–5 tracks including MyWave, pause/seek/Next and repeat the same song. Export CELIKOM TXT. Check the NAV41 registration and only these five categories, alongside already proven NAV40 live source/Flow counters. If no trustworthy current identity or scope mismatch, fail closed. Do not restart broad Timeline/MediaItem/Exo scans, redesign, or touch signed NAV40. Continue toward one original-player replacement only after runtime identity is verified.
