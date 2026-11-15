# CELIKOM Android A1 — LyEa route closed; return to native audio sink

**Date:** 15 Nov 2026  
**Working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `815abcb4f9f43224506392b67efc07b3e34cf26b`  
**CI #148:** [SUCCESS, 102/102](https://github.com/manufact-test/nomusic/actions/runs/43753653243)  
**Green backup:** `backup/android-a1-lya-route-closed-ci-green-20261115` @ `815abcb4f9f43224506392b67efc07b3e34cf26b`  
**Runtime hooks:** unchanged since `a655712d210189f3bc611847235de3ed4d985c1a`.

## Final LyEa result

- The Track field returned by `LyEa.if(): Track` has one writer in the full `LyEa` constructor.
- The bounded field-store trace links the stored reference to the constructor's original Track parameter. This is a constructor-field identity fact only; it does not identify the active selected item.
- Two direct constructor callsites were found: overload delegation preserving its Track parameter, and `LyEa.try(...)` constructing a new instance with Track read from a field on another LyEa receiver.
- The exact LCK1 calls to `LaC7.if(): Track` are in `LCK1$c$a.emit` and `LCK1$h$a.emit`. Each has four incoming CFG states and no common must-alias receiver identity.
- `LzA9;` is an abstract interface in the signed DEX. No concrete body for exact `LzA9.if()LaC7;` was found. No runtime dispatch to `LyEa` is proven.

**Decision:** close LyEa / LaC7 / LCK1 as an unproven candidate. No more scans of these owners, implementers, or unrelated callers. CI #148 is sufficient; do not spend another CI run trying to force this route.

## Product gates

- NAV17 Stage A remains owner-confirmed PASS; preserve it.
- Stage B remains NOT CONNECTED / NO-GO.
- `active_selected_item_proven=false`
- `same_native_item_to_decoder_proven=false`
- `same_track_album_edition_generation_owner_proven=false`
- `codec_output_object_to_audio_sink_proven=false`

## Next work — existing renderer field-writer path only

See `ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md`. Do not repeat its completed census.

Known:
- `LcLb.O` and `Lbd6.O` pass the same ByteBuffer parameter into `LbJ2.native(ByteBuffer, long, int)`.
- Three ByteBuffer field slots, seven writer methods have already been identified.
- `LcC0.n(JJ)Z` and `Lkd6.n(JJ)Z` contain exact `Lad6.final(I)ByteBuffer` return-to-field-store references, but branches and alternative writes prevent claiming one continuous runtime buffer identity.

Next bounded action: trace only the exact buffer reference through `LcC0.n` / `Lkd6.n`, field write/read and sink call. Treat alternate stores and branch paths as unresolved unless identity is preserved on every path. Then locate the actual current selected Track/Album owner and connect that same item to the decoder/render path. Explicitly exclude queue/prefetch/download.

Do not create new analyzer infrastructure or run repeated broad tests. Use existing evidence, make one focused change only if necessary, and run focused tests only for changed logic. No runtime hooks or APK changes until the full selected-item-to-decoder chain is proven.

## Safety/scope

Read-only and fail-closed. No original Yandex/account changes, no NAV17/Test.50/frozen A1/LSPatch changes, no Windows/extension/backend/production changes, no field values, media identifiers, URLs, DataSpec, tokens, account data, or audio bytes. No vendor behavior changes, exception suppression, second player/decoder/AudioTrack, or owner manual work without a concrete necessary measurement.
