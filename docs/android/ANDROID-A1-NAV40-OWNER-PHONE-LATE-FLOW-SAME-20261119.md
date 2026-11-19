# NAV40 real owner phone: exact late-Flow Track/Album SAME under strict original Player source

19 November 2026. **Real user phone** diagnostic: `CELIKOM-A1-Diagnostics-1795077619261.txt`, 122,665 bytes, 1,715 lines, SHA-256 `c0a5c30994d3e533db41618b7b1b4c880f6a42cf6bd513449adf28d5f114ad51`. Private raw TXT is not committed.

**Single working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
Last unchanged signed NAV40 runtime/source: `34cb32c88a11743a64c9f4814fa71957223a1391`; protected signed rollback:
`backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`.
All NAV40 JVM, clone-alone Android 13, original+clone owner-signed ARM13 release CI SUCCESS; verified artifact hashes/cert/original are in [NAV39 → NAV40](ANDROID-A1-NAV39-OWNER-PHONE-NAV40-LATE-FLOW-LIVE-WRAPPER-20261119.md). Library NAV40 APK/ZIP upload subsequently succeeded after user freed storage; readback materialization had correct sizes. No new code/APK or CI performed during this report.

## Active capture and interpretation

The raw export contains an **older historical NAV39** `DIAGNOSTIC_BUILD` event, followed by **NAV40 active marker** `NAV_V40_TCA_CREATOR_LATE_FLOW_LIVE_WRAPPER_READONLY` in its newest main process and current summary. Never mistake trimmed history for active build.

- `LIVE_QUEUE_SLOT_B=REGISTERED`; `LIVE_PERIOD_ORIGINAL_SOURCE=REGISTERED`; `TRACK_PLAYER_SOURCE_SCOPE=REGISTERED`; `NATIVE_PLAYER_SOURCE_SETTER=REGISTERED`.
- Same original live holder/rendered audio read cohort: `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`; OTHER/UNAVAILABLE NONE. `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=MANY`; OTHER/UNAVAILABLE NONE.
- `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=MANY`, UNAVAILABLE NONE. Direct holder `Lo96` and source present MANY. `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`, OTHER/NO_LINK NONE, `TRACK_PLAYER_SOURCE_CONFLICT=NONE`.
- Historical exact creator `Track`: `TCA_CREATOR_OWNER_ENTER=MANY`, `TRACK_FIELD_READ=MANY`, `WRAPPER_CONSTRUCTED=MANY`, `WRAPPER_NOT_FLOW=MANY` at birth; `TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED=MANY`; `TCA_CREATOR_FLOW_LATER_SAME_TRACK=MANY` and `_ALBUM_OBSERVED=MANY`. Owner/Track null/failure NONE.
- **NAV40 new mutually exclusive categories:** `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`; `_MISSING=NONE`; `_DIFFERENT=NONE`; `_REFERENCE_LOST=NONE`.
- Previous NAV39 `LIVE_PERIOD_SCOPED_TCA_BIRTH_TRACK_NOT_IN_FLOW=MANY` is **NONE** now, because later exact-match evidence is classified by the new specific NAV40 outcome; this does **not** mean Track suddenly appeared in Flow *at birth*. Its at-birth absence remains `TCA_CREATOR_WRAPPER_NOT_FLOW=MANY`.
- Legacy `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH=NONE` / `_NO_LINK=MANY` are intentionally still so: NAV40's exact later Flow classification lives within historical NO_LINK classification; it does **not** retroactively create the missing birth-time `NativeTrackSourceLink` or current Track→decoder claim. `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_CONFLICT=NONE`; `TRACK_ALBUM_IDENTITY_CONFLICT=NONE`.
- `EXO_IO_FAILURE=NONE`, `EXO_READ_POSITIVE=MANY`, `EXO_SOURCE_END=MANY`. Audio issue, seek/pause/Bluetooth/EOS bugs were **not** reported; do not invent them. `BUFFER_EOS_ACCESS=NO_HOOK` is unrelated and not the target.
- Active summary `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE`. Local historic events include `MUSIC_APP/EXC_OTHER` and separate SDK Push `EXC_OTHER` events; **no CELIKOM attribution** justified by this data. Earlier NAV39 history must not override the active summary.
- `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.

## Source-level meaning, limits

Review of unchanged NAV40 source:
`StageBAudioEvidence.classifyMissingWrapperBirth` returns category **16** only when the exact original `tCa` wrapper is in the bounded birth window, its **creator-owned same Java Track** (reference `==`) is seen in Flow **after its wrapper birth**, and the **Album observed at birth** is the exact Album still associated with that Track at the time of classification. No value IDs, names, URLs, content or PCM used.

`NativeRendererStreamEvidence.observeActivePeriodSource` invokes this category ONLY after exact current live SLOT_B type1/state2 attached-stream read, exact original Lo96/Sl6 source resolution and uniquely matched original scoped native Player setter source/wrapper. These are bounded repeated **observations** (counters may saturate at MANY); NOT a number of distinct tracks or independently proven queue generations.

**Proven:** strict live original source cohort shares exact wrapper whose creator Track was later emitted by Flow and whose original Album reference remains equal. **NOT proven:** current user-selected edition, Track assignment to a unique live queue generation, chosen playlist item identity or actual audible CELIKOM replacement. No Stage B permission. Never interpret structural SAME as current edition selection.

## Next narrow step — NO blind NAV41

Before new runtime probe, inspect only the **pinned signed original 2025.10.4 #120.1gpr** at the confirmed `ExoPlayer/h.SLOT_B` mutation / current item selection boundary. Establish an actual source-backed queue transition / epoch for the **same original native Player** and whether its exact holder/source can be paired with the selected playlist item **at the time of started audio read**. Distinguish static preparation/prefetch, selection, and stale previous holder. A monotonic observer epoch created without covering all relevant mutations is **not** proof of real original queue generation.

If exact signed DEX reference/CFG and fail-closed uniqueness can be proven, the possible minimal follow-up is **read-only** current selection/generation correlation of already verified source/wrapper with Track/Album, bounded weak refs and categorical non-private export. Tests must include unchanged slot, same Track in successive queue epochs, prefetch/previous period, wrong source, missing history, GC, and conflicting albums. No changes to original app, decoder, audio, Player, existing replacement gate; no NAV41 build before there is a clear signed original target.

If that boundary cannot be independently proven, **STOP at NAV40 structural-only**; don't fabricate a selector or change audio.

## Delivery / safety

NAV40 existing signed backup and CI-green code remain untouched. Owner's latest diagnostic is not committed. Future APK requires protected pre-change backup, JVM + Android13 clone-alone + publisher-first signed original+clone CI green, owner signature certificate and SHA-256 verification, preservation of untouched signed original, and Library readback confirmation.
