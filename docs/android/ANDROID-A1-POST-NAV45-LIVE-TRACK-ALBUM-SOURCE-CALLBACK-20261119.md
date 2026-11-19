# CELIKOM Android A1 — exact original Track/Album in live source callback (post NAV45)

**19 Nov 2026.** Sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; work started after doc-only checkpoint `8efad11e82d278a537cd91cf975df1748f71c442`. **Do not call this NAV46 or a signed release:** no new APK was exported. Signed NAV45 `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`, owner NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, Test.50, Windows, publisher original and existing signatures remain untouched.

## Real code change (not just another diagnostic counter)

The existing original Track object from the exact original `tCa` creator and later exact Flow now has a fail-closed **Track+Album object handle** available on the same original audio renderer callback where the original **PlaybackInfo.PeriodID UID + both integers**, live `SLOT_B`, same original `LiLb` source/period and original native Player setter source were already verified.

- `StageBAudioEvidence.exactOriginalTrackAlbumForWrapper(wrapper)` returns exactly the original **two Java references** (not their IDs/strings) only for a unique, unconflicted Track/Album/Flow/birth or current original wrapper association (`classify == 1 || 16`). All weak reference loss, conflicting albums, duplicated wrapper births, different Flow track and absent identities return null. The returned pair is **not cached** across callbacks.
- `NativeRendererStreamEvidence` has a **same-callback** `ActiveOriginalTrackObserver` seam, gated by original active source, the same `PeriodID` fields, two ints, `SLOT_B`, exact underlying native period's source reference and original renderer type/state/-4 unknown-EOS cohort. No adapter or stale source shortcuts. It carries the original Track/Album/source references only in the Java stack frame and never logs IDs/values.
- `ExitCallsiteWitness` wires `StageBAudioEvidence` as the original object-identity provider. **No replacement consumer is installed**, so this change does not select a new audio source, alter the original Player, create a second decoder, read private Track fields or change playback.
- JVM regression tests cover successful original Track+Album/source reference delivery, conflicting Album, unknown Flow, duplicate wrapper, replay with different original period second int, source change without `SLOT_B` pointer change, EOS and wrong/changed Player/source. No user/account/audio test claimed.

## Gates

- [Exact Java renderer JVM #44574303898 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574303898) (final tests `6474a94d`).
- [Publisher-first ARM13 #44572917325 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917325) (original 2025 + clone lifecycle, runtime code `2d73af05`; no owner APK exported). Clone-alone [#44572917099 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917099).
- [Exact signed 2025 `trackId` API/provenance gate #44574897138 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574897138): the original `FileInfoApi` and `DownloadInfoApi` indeed carry annotated `trackId` parameters; among **21** exact inbound writer calls is the original `LGp0` source-track creator with a Track-typed parameter and a Track String field read, but the precise receiver reaches a branch and is **NOT identity-proven as that same original Track** (`TRACK_RECEIVER_BRANCH_UNPROVEN`). No exact albumId, editionId, active original source, or replay generation is established through this API.

## Scope and next real blocker

This improvement makes the **original Track+Album Java objects available in an exact native live-source callback**, rather than merely a historical classification counter. It **does not establish those objects' semantic IDs, selected edition, audible PCM or pre-prepare audio replacement**. There is no product admission: `CELIKOM_REPLACEMENT=NOT_CONNECTED`; any unknown / conflicting source must keep the original Yandex audio.

The next required functional step is semantic `trackId + albumId + editionId` provenance from the SAME original Track/source before native source prepare, plus exact current selection generation; then adapt the already existing `NativeReplacementLifecycle`/signed source grant at the original pre-prepare DataSource path. Do **not** repeat blank MediaItem experiments, unbounded DEX scans or ship owner-side diagnostic variants just for classification counts.

No owner APK/ZIP or Library upload was made, and the last valid signed NAV45 remains unchanged.
