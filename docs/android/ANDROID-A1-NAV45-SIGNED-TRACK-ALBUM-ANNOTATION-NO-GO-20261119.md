# CELIKOM Android A1 — bounded signed Track/Album semantic ID gate: NO-GO

**Date:** 19 November 2026. **Repository branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Input point before changes: `366a10e9be6653bb4140e4b2b6d93bf0dc1940d9`. Signed NAV45 release `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8` and NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391` remain untouched.

## Exactly what was checked

A **single bounded, read-only, CI-only** semantic annotation checker `android/native-yandex-hooklab/ci/a1_private_track_model_identity_annotation.py` was added along with `.github/workflows/android-a1-track-model-id-edition-annotation.yml`. The workflow reuses the already owner-authorized historical issuer-signed Yandex Music **2025.10.4 #120.1gpr** original, verifies pinned archive/base SHA256, verifies all **16 publisher-signed splits**, then inspects only the original Track `ru.yandex.music.data.audio.o` and Album `ru.yandex.music.data.audio.Album` class definitions in **six DEX**.

The checker permits only explicit semantic ID/edition labels in known serialization annotations (`SerializedName`, Moshi `Json`, Jackson `JsonProperty`, Kotlin `SerialName`), attached to actual instance fields **or** typed constructor parameters. Constructor parameters are **not** assumed to map to fields by position. No runtime hook, identifier value, private field name, account, URL, audio, publisher APK, signed build or playback behavior was exported/altered.

## Verified final CI result

[Exact signed original gate #44562209490 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44562209490). All job steps passed, including issuer verification, bounded scan, and cleanup.

- Original Track class: **51 instance fields**; zero recognized explicit serialized identity annotations on instance fields and constructor parameters.
- Original Album class: **37 instance fields**; zero recognized explicit serialized identity annotations on instance fields and constructor parameters.
- `track_id_annotation_present=false`, `album_id_annotation_present=false`, `distinct_edition_annotation_present=false`.
- `track_ctor_id_annotation_candidate=false`, `album_ctor_id_annotation_candidate=false`, `edition_ctor_annotation_candidate=false`.
- Final verdict: **`NO_GO_EXACT_ID_AND_EDITION_NOT_SEMANTICALLY_ATTESTED`**.
- `current_playback_generation_proven=false`; `active_source_album_edition_binding_proven=false`; `replacement_connected=false`.

**Scope of absence:** only known serialization annotations on these exact signed-model fields/constructor parameters. This does **not** prove there is no obfuscated identity property elsewhere or that the Track has no ID. The historical `Track.copy` wide argument is still not proven to mean `trackId`; the distinct `Ldjv.a():String` download/FileInfo getter still lacks same-source provenance. NAV45's blank MediaItem ID remains unusable.

## Engineering decision

Do **not** ship another read-only NAV46 just to get negative counters, and do **not** enable replacement by guessing the ID, Album or edition. The active original `PeriodID → SLOT_B → TrackWrapper → original source → late Flow` link remains the only owner-phone-supported partial structural link; `NO_LINK=MANY` prohibits unconditional admission. The exact original ID/edition and replay generation remain unproven, and current renderer PCM isn't attested. Thus no next signed APK/ZIP was produced. All existing signed releases and Android playback behavior remain intact.

The only useful new gate would have to tie an independently semantically proven original Track+Album+edition identifier to **that exact live source and generation**. If that cannot be shown, fail closed and retain the original Yandex sound. Do not reopen blank MediaItem comparisons or the same unbounded history searches.
