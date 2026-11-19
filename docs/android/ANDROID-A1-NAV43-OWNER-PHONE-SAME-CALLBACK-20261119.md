# NAV43 — owner HONOR 50 same-callback result (19 November 2026)

## Source / exact status
Owner local TXT `CELIKOM-A1-Diagnostics-1795097798424.txt`: 122,007 bytes, 1,685 lines. It contains historical NAV42 process sessions followed by active `NAV_V43_PERIOD_FLOW_UID_INTS_SAME_CALLBACK_READONLY` and the NAV43 renderer summary. Do not misclassify the earlier NAV42 markers as the tested build. Personal diagnostic stays outside GitHub; no accounts, raw logs, IDs or URLs committed.

**NAV43 owner phone structural gate: PASS.** Actual NAV43 counters:
- `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY` and `...MINUS4=MANY`.
- `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`; `...SAME_REF=NONE`, `...UID_ONLY=NONE`, `...DIFFERENT=NONE`, `...UNAVAILABLE=NONE`.
- **`PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`**.
- `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_NO_LINK=NONE`; `...SLOT_CHANGED=NONE`.
- `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY` and `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`; matching source conflict/different/missing categories NONE.
- `AUDIO_NATIVE_RENDERER_HOOK_STATUS/BUFFER_EOS_ACCESS=NO_HOOK`; buffer EOS is unavailable (`ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE=MANY`).
- `METRICA_EXCEPTION_SUMMARY/MUSIC_APP=NONE` in final summary; `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.

## Exact interpretation and comparison with NAV42
NAV42 showed original PlaybackInfo PeriodID UID plus both int fields matching live active `SLOT_B`, and separately the original source → creator-owned tCa TrackWrapper → later SAME Flow Album; independent counts were not a shared callback. NAV43 confirms both sets of evidence advanced within one started type-1 / state-2 original renderer read callback returning -4, and revalidated live `SLOT_B` after source classification. This follows the exact read-only code introduced at `24a6a2dfcce86e7514fccd8253bc4eae440de5d4`, released as source `3cc409d9e7879abf91783109fd28f66586881bdc`. User-signed NAV43 [JVM #44538897528 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44538897528), [Android13 ARM #44538897470 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44538897470).

**This remains a structural witness.** Unknown EOS means -4 must not be called a confirmed non-EOS sample, PCM or audible sound. Correlated Track reference and later album do not yet prove *which original Track ID and exact edition*, repeated same track/new queue generation, or rights-approved CELIKOM replacement. Existing `AUDIO_STAGE_B_SUMMARY/EXO_READ_POSITIVE=MANY` is a separate data-source cohort, not proof the selected original decoder consumed CELIKOM audio.

## Next narrow engineering gate (not a license to publish NAV44)
1. Start from the **existing NAV43 same-callback and live-SLOT_B read** path, not fresh generic architecture/DEX exploration.
2. Identify the exact *original selected* Track identity and edition for that same Player PeriodID / current started renderer read. An original publisher-signed typed getter/field route and a runtime read-only provenance proof are required; do not infer edition from matching UID/two ints, Flow album, display title or a separate aggregate event.
3. Fail closed for null/ambiguous edition, stale or prefetched period, a Next switch while sampling and a repeated identical composition with different period/generation. Re-read live SLOT_B and current Player period before accepting a witness.
4. Until this can be established, **do not create NAV44 or connect/modify audio**, and do not claim replacement. Check the existing precise targets first, not broad static scans. After a justified focused code change: JVM CI, owner-signed ARM13 CI, one Library APK/ZIP and owner phone evidence.

**Protected:** owner-signed NAV40 code `34cb32c88a11743a64c9f4814fa71957223a1391`, backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`, NAV41–NAV43 signed binaries and the canonical single branch remain unchanged. No new binary or runtime modification for this documentation checkpoint.
