# CELIKOM Android A1 NAV45 — read-only nonempty MediaItem logical ID

19 November 2026. Sole work branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Input: actual owner NAV44 phone diagnostic
`CELIKOM-A1-Diagnostics-1795100702186.txt` contains current `NAV_V44_CURRENT_MEDIAITEM_SOURCE_READONLY`; original `CURRENT_MEDIAITEM_SOURCE` registration SUCCESS, player PeriodID ↔ live SLOT_B UID+two ints MANY, NAV43 `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`. NAV44 same-Java-reference counter NONE; DIFFERENT FEW, UNAVAILABLE NONE, SLOT_CHANGED NONE. Original source/TrackWrapper/late Flow match MANY; `...NO_LINK=MANY` also occurs. `BUFFER_EOS_ACCESS=NO_HOOK` and identity remains STRUCTURAL_ONLY.

**Interpretation:** the two original MediaItems can be separate instances, so Java `==` is not a content identity. Do not infer different songs or editions and do not change the verified original player.

## Exactly one additional read-only witness
Signed-publication-gated private CI proves exactly one final, nonstatic `String` instance field on the signed `LOf6;` original MediaItem. Its name is compiled only in the ephemeral private Java target, never logged and never committed. The original receiver/link, Player PlaybackInfo/PeriodID UID+ints, actual SLOT_B, MediaPeriod underlying source, Window Timeline and late Flow all remain the existing NAV43/44 guards. Under a successful, unchanged callback:
- If either MediaItem ID is null/empty: `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_BLANK`.
- If both present and equal by Java `String.equals`: `...MATCH`.
- If both present and unequal: `...DIFFERENT`.
- Any inaccessible field: `...UNAVAILABLE`.

At most one final logical-ID result per bounded holder/source probe pair (3 callback attempts). The comparison never logs raw strings, song names, track IDs, URLs, album metadata, accounts, audio data or returned PCM. No new vendor hook, no source setter mutation, no player replacement.

## Gates and bounded claims
- Original private XAPK field+getter+exact Timeline proof: [signed CI #44551508431 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44551508431).
- Current Java fail-closed tests for same Java object, two objects with same logical ID, different nonempty IDs, blank ID, changing SLOT_B or changing source: [JVM #44552192680 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44552192680).
- Owner-signed ARM13 release CI **pending** before APK/ZIP acceptance.
- Even a nonempty ID MATCH is only a logical item candidate; the ID may not distinguish track editions/queue generations. Not a soundness proof of acoustic replacement. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `BUFFER_EOS_ACCESS=NO_HOOK`.
- Signed NAV40, earlier signed NAV43 and NAV44 APKs/ZIPs untouched.

## Next action
After ARM13 CI success, verify exact single APK+ZIP artifact, hashes, and embedded NAV45 marker/counters, upload both to `/CELIKOM/Android/Native/`, and request one owner phone TXT after 2–5 tracks including MyWave/Next/seek/pause/repeat.
