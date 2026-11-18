# CELIKOM Android A1 — NAV37 real owner-phone evidence to NAV38 minimal diagnostic

19 November 2026. Sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## NAV37 exact phone evidence

Private file `CELIKOM-A1-Diagnostics-1795038626276.txt`, 94,207 bytes / 1,300 lines, SHA256 `83a0a18170bfdebdc6f981068e8642eee0e6fc1c513979b830ecbe95899c6352` (not in repo).

`NAV_V37_TCA_CREATOR_TRACK_FIELD_SCOPE_READONLY` active. Exact creator owner entered MANY, Track field read MANY, original wrapper created MANY. Owner/Track-field/null/failed cases NONE. **TCA_CREATOR_WRAPPER_NOT_FLOW=MANY; FLOW_MATCH=NONE; ALBUM_LINK=NONE.** The bounded Flow history had FEW emissions, and independent Track/Album/wrapper histories were positive, but that does not prove the creator Track is the same Flow Java reference.

No strict current Player-scoped live source or SLOT_B match reproduced in this snapshot; all LIVE_PERIOD_SCOPED counters NONE, LIVE_QUEUE_SLOT_B=NO_HOOK. This does not erase earlier NAV36 phone proof; it only prevents treating it as current evidence.

`METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE`, `EXO_IO_FAILURE=NONE`; do not assign SDK Push exceptions or playback defects to CELIKOM.

## NAV38 hypothesis and bounded instrumentation

NAV37's `NOT_FLOW` check means **not retained in this observer's last 32 weak Flow track objects at wrapper birth**, not that the Java Track cannot appear later. To distinguish chronology from distinct Java identity:
- Keep at most 32 new weak references for exact creator-owned Track objects not found in Flow history at birth (no raw fields, no IDs/titles).
- At original Flow emission, test strict `==` for pending Track and consume the match once; never infer match from time proximity or shared type.
- At birth and later Flow event, classify whether direct previously observed Track/Album constructor link is available. `UNOBSERVED` means not attested, not proof of absence.
- Do **not** create retroactive NativeTrackSourceLink or link to currently audible renderer; keep audio replacement disabled.

NAV38 build marker `NAV_V38_TCA_CREATOR_FLOW_TIME_ORDER_READONLY`. Four new Stage B categories:
`TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED`,
`TCA_CREATOR_NOT_FLOW_ALBUM_UNOBSERVED`,
`TCA_CREATOR_FLOW_LATER_SAME_TRACK`,
`TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED`.

## Provenance and verification
- Source: `72d5c42f1678d7b6839202a52712e5e80bf8a019`.
- Pre-NAV38 protected backup: `backup/android-a1-nav37-owner-phone-not-flow-pre-nav38-20261119` @ `211460b4143bd3f775ccc0001a65afb5ce75b640`.
- JVM regression: [#44407443841 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44407443841).
- Owner-signed ARM13 and APK export: [#44407443952](https://github.com/manufact-test/nomusic/actions/runs/44407443952), pending.
- Clone-alone: [#44407443848](https://github.com/manufact-test/nomusic/actions/runs/44407443848), pending.
- APK package expected `CELIKOM-A1-NAV38-Creator-Flow-Time-Order-ReadOnly-20261119.apk`.
- Follow owner acceptance + signer/SHA256 checks, upload signed ZIP to personal Library, materialize for byte comparison; only then owner installs over NAV37 and returns another private TXT.

## Boundaries

Original Yandex `2025.10.4 #120.1gpr` unchanged. No original Player/decoder/audio changes, no new media collection, no invented playback problems. `CELIKOM_REPLACEMENT=NOT_CONNECTED` and `IDENTITY_STATUS=STRUCTURAL_ONLY`. Historical Flow/Album links alone do not establish selected edition or queue generation.
