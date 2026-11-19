# NAV45 owner-phone result — immutable MediaItem ID blank in current originals

Date 2026-11-19. This is a diagnostic assessment, **not a release**.
Phone TXT: `CELIKOM-A1-Diagnostics-1795102532842.txt`, complete 2066 lines / 147701 bytes. Contains two earlier `NAV_V44_CURRENT_MEDIAITEM_SOURCE_READONLY` sections followed by active `NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY` (main event and summary). Review specifically the NAV45 summary, not earlier NAV44 process sections.

## Owner NAV45 observed
- `CURRENT_MEDIAITEM_LOGICAL_ID=REGISTERED`, `CURRENT_MEDIAITEM_SOURCE=REGISTERED`: compiled original signed target was installed on owner HONOR 50.
- `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH=NONE`, `DIFFERENT=NONE`, `BLANK=FEW`, `UNAVAILABLE=NONE`: among the NAV44-qualified attempts, at least one of two original `LOf6` MediaItem final String values is empty/missing. Cannot tell **which** from this summary. **No nonempty logical ID evidence**, even though source and Timeline item objects are accessible.
- `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF=NONE`, `DIFFERENT=FEW`, `UNAVAILABLE=NONE`, `SLOT_CHANGED=NONE`. Two distinct Java references do NOT prove two different songs; do not collapse to reference-equality or compare empty Strings.
- `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`, `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`, `...NO_LINK=MANY`, `...SLOT_CHANGED=NONE`. Some reads are structurally linked, but linkage is not universal. `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`, `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`, `...MISSING=FEW`, `...DIFFERENT=NONE`.
- Source/reader evidence `EXO_READ_POSITIVE=MANY` is separately aggregated; `BUFFER_EOS_ACCESS=NO_HOOK`, `ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE=MANY`. No proven non-EOS audible PCM in exact joined callback.
- `METRICA_EXCEPTION_SUMMARY/MUSIC_APP=FEW` in this file. Category only, not crash attribution. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.
- Trim markers `LOG_TRIMMED KEEP_LAST_32KB`; avoid deriving track-specific exact order from summarized/truncated diagnostics.

## Direct next engineering target — NO new diagnostic APK yet
The NAV45 blank field is unusable for identity. Preserve owner-signed NAV40 (source `34cb32c88a11743a64c9f4814fa71957223a1391`) and signed NAV43/44/45 artifacts; **do not reinterpret NAV45 as a match**. Stop MediaItem ID and reference comparison as candidate admission gates.

The already hooked publisher-original `ru.yandex.music.data.audio.o` Track object is connected to `tCa` TrackWrapper through creator-owned binding, later Flow emission, original `LiLb` MediaSource and current live `SLOT_B`/PlaybackInfo PeriodID. `StageBAudioEvidence.classifyNativeTrackAlbumForWrapper` currently returns classification only, not selected track values. The signed original Track `o` copy method `new(o,long,Album,List,fCa,int)` contains a `long` parameter but **its meaning as track ID is NOT proven**. Previous `Ldjv.a():String` downstream API candidate is a separate object path; no justified join to this Track. Avoid guessing numeric ID or edition.

Next step is **a bounded publisher-signed original inspection** of typed Track identity/edition accessors and their exact provenance from the Track tied to the current source; separate current playback generation, fail closed for null/unknown/mismatch or MyWave/Next races. Only if signed-source provenance demonstrates exact Track ID *and* edition at current renderer callback should another read-only owner APK or eventual substitution be considered. Nothing in NAV45 phone TXT proves decoder ownership or authorizes substitution.

## Current checked repo
Sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112` HEAD before report `46f41c1fb833239f0cdfcd5ecf6c90db996113b9`. NAV45 owner-signed source `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`, full ARM CI #44552661805 SUCCESS 27/27. Signed NAV45 APK/ZIP already in original conversation as verified direct downloads; owner Library upload previously failed due storage quota. This phone test does not affect signed files.
