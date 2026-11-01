# CELIKOM — follow-up handoff after the 0.3.75 audio diagnostic

**Current status:** diagnostic correction and update-state implementation are staged and CI-verified. Audio quality is NOT declared fixed.

## Branches and commits

- Repository: https://github.com/manufact-test/nomusic
- Production working branch / PR base: `feature/android-unified-preparation-seek-gate`
- Staging code branch: `feature/android-076-output-clock-update-state-staging-20261101`
- Draft PR: https://github.com/manufact-test/nomusic/pull/24
- Documentation branch: `handoff/diagnostic-audio-output-evidence-20261101`
- Rollback branch: `backup/android-0375-before-output-clock-and-update-state-20261101`
- Original HEAD: `0867c83c692cdc2dbfd74662476cb181ea2e9d51`
- Final staging HEAD: `a7b28fa8ebd6ed856e1ed9bfa02f0e7da612c06f`

## Most important corrected conclusion

The 772 ms ALIGNMENT value in `CELIKOM-combined-20261101-125049.txt` is not a 772 ms decoder landing error. In all 11 ALIGNMENT ACK outliers above 100 ms, the decoder cursor equalled the requested seek target. The source kept playing while the asynchronous replacement seek callback was pending. The old `rawResidualMs` mixed that source advance into the source-minus-decoder skew.

The 772 ms example:
- requested target: 221136 ms;
- decoder at ACK: 221136 ms;
- source projected at ACK: 221908 ms;
- callback elapsed: 816 ms;
- raw residual: 772 ms.

This is a real temporary transport lag during async seek, not evidence of a clock offset or speaker output error. The WARM stage subsequently corrects before output is granted; WARM had 20 ACKs at 40–91 ms, none above 100 ms.

## Other verified risks

- Eight `overlap_commands` were expected command-level overlaps in the eight `SAME_SONG_BLEND` entries, not eight random races. Their acoustic result remains unmeasured.
- Three replacements were shorter than Yandex: Биг сити лайф -1354 ms, Крылья -582 ms, Метамир -663 ms. All were accepted by the 1500 ms bounded-tail allowance.
- `automaticSourceIdVerified=false`: metadata matching does not prove same edit/master.
- Current linear blend is the owner-approved single production mode; don't change its gain law or duration without new evidence.

## What changed

1. Added `SeekTimingEvidence`: callback duration, source advance, decoder landing error, current skew, source snapshot age.
2. Added `OutputClockEvidence`: passive `MediaPlayer.getTimestamp()` samples at pre/mid/post transition, with separate System.nanoTime and elapsedRealtimeNanos fields.
3. Added expected-vs-unexpected command overlap classification.
4. Fixed Update Center persistence: background and foreground checks share saved candidate state; “Позже” preserves the update; failed checks do not erase it.
5. Kept all audio behavior and Android permissions unchanged.

## Validation

CI [41297330560](https://github.com/manufact-test/nomusic/actions/runs/41297330560) PASS on final staging HEAD. Existing engine tests, new 18 diagnostic checks, new 12 update-state checks, all 18 addon host gates, Android API 36 compile, D8 and release contract checks passed. The stable publish job was skipped. No signed APK or server deployment was made.

## Non-negotiable next steps

- Do not tune crossfade, seek duration, WARM lead or thresholds based on old ALIGNMENT rawResidual values.
- Do not say audio is fixed from MediaTimestamp alone.
- Install a build containing these diagnostics, repeat the owner's affected-track listening test, and inspect the new fields.
- Source PCM, phase correlation, Yandex presentation timestamp and actual speaker/Bluetooth output remain unmeasured.
- Do not add RECORD_AUDIO or MediaProjection to the shipping app until a separately approved diagnostic capture is demonstrably necessary.
- Keep PR #24 draft/unmerged until the owner wants the staging changes promoted to the main working branch.
