# CELIKOM A1 — NAV38 real phone Flow-later proof, NAV39 restored private live probe packaging

19 November 2026. `manufact-test/nomusic`, branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Owner phone evidence: NAV38
- Private `CELIKOM-A1-Diagnostics-1795072687109.txt`: 126,763 bytes / 1,783 lines, SHA256 `5282b02a1fe32407043fd6b7c3d6c21d496236787342c85212e9047c794467d8`. Never commit raw.
- `NAV_V38_TCA_CREATOR_FLOW_TIME_ORDER_READONLY` active, `TCA_CREATOR_TRACK_FIELD_READ=MANY`, `TCA_CREATOR_WRAPPER_CONSTRUCTED=MANY`, `TCA_CREATOR_WRAPPER_NOT_FLOW=MANY`.
- Exact same Java ref later emitted in Flow: `TCA_CREATOR_FLOW_LATER_SAME_TRACK=FEW`, `TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED=FEW`. At birth `TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED=MANY`, `...UNOBSERVED=FEW`.
- The exact same weak-held Java Track later appears in Flow; chronology is at least one real reason prior birth-time `NOT_FLOW` can occur. Does not prove this for *all* creator Tracks, nor selected audible edition/current queue generation.
- Live source witness unavailable in *this* export: `LIVE_QUEUE_SLOT_B=NO_HOOK`, `LIVE_PERIOD_ORIGINAL_SOURCE=NO_HOOK`; `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=NONE`. Historical NAV36 proof is not current.
- `EXO_IO_FAILURE=NONE`, `TRACK_ALBUM_IDENTITY_CONFLICT=NONE`, `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE`.

## NAV39 hypothesis addressed
The NAV38 owner ARM13 build generated only `PrivateTcaTrackCreatorTarget`, not the existing private source/queue targets. The current original read-only Java observer explicitly loads `PrivateNativeQueueSlotTarget` in the live queue scope and `PrivateNativeActivePeriodTarget` in the live original source resolver, and catches class-not-found as `NO_HOOK`. No new vendor hook required: generate those two ephemeral classes from same publisher-signed 16-split XAPK in CI and rebuild module, guarding that compiled DEX actually includes them.

**Protected backup before changes:** `backup/android-a1-nav38-phone-late-flow-before-nav39-hooks-repair-20261119` @ `fb2463ff7dbe48441bcb96ee89fdf4d8df9d1169`.
**NAV39 source:** `694f0efa1616560d814de60de2906446aad7e3d0`.
**Runtime version marker:** `NAV_V39_TCA_CREATOR_FLOW_LIVE_RECHECK_READONLY`.
**Signed original/version:** Yandex 2025.10.4 #120.1gpr unchanged. Player/audio/decoder/replacement not touched; `CELIKOM_REPLACEMENT=NOT_CONNECTED`.
**CI:** JVM #44479658027; ARM13 clone alone #44479658036; publisher-first signed ARM13 export #44479658010. Check final conclusion before release.

## Acceptance
1. All CI successful and published owner-signed APK verified unchanged owner v2/v3 certificate + SHA256 + correct original publisher splits, user-in-place update, no fresh install; ZIP instruction NAV39.
2. Upload to personal Library, read back and compare bytes, then provide only verified download.
3. Owner on-phone TXT with active NAV39 marker and `LIVE_QUEUE_SLOT_B=REGISTERED` and `LIVE_PERIOD_ORIGINAL_SOURCE=REGISTERED`. Check strict *current* SLOT_B type1/state2→ original Lo96/Sl6→ same original scoped Player setter, plus independent Track/Flow later reference histories. These are necessary but not sufficient to select current edition and queue generation.
4. Only decide subsequent minimal bounded read-only test after phone evidence. Do not infer historical Album equality as current edition or enable replacement without full admission/identity proof.

Never commit private diagnostic values/track names/IDs/URLs/media/PCM/tokens; don't rerun old EOS or comparator probing.
