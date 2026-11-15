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

## Follow-up — renderer CFG identity and selected-owner result (CI #151)

See ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md for the full trace.

- The exact Lad6.final result is linked through slot 2 / slot 3 field store and same-this field read to each corresponding virtual O callsite on one incoming CFG state.
- Each of the four virtual O callsites has a second incoming CFG state whose field-read value has no proven in-method writer origin. Full path identity is therefore not established.
- LcLb.O / Lbd6.O parameter-to-LbJ2.native remains proven; runtime virtual dispatch remains unproven.
- The existing selected-state and shared-owner census finds no current selected Track/Album owner connected to Player, MediaSession, descriptor or decoder boundaries. Edition/Generation remains unidentified.

**Decision:** the native buffer path is only partially proven; the current selected Track/Album bridge is the exact blocker. Stage B remains NOT CONNECTED / NO-GO. Do not widen the scan, add runtime hooks or modify APK/vendor code. Wait for a concrete identity-bearing witness at an exact Player selection callsite.
## Safety/scope

Read-only and fail-closed. No original Yandex/account changes, no NAV17/Test.50/frozen A1/LSPatch changes, no Windows/extension/backend/production changes, no field values, media identifiers, URLs, DataSpec, tokens, account data, or audio bytes. No vendor behavior changes, exception suppression, second player/decoder/AudioTrack, or owner manual work without a concrete necessary measurement.
