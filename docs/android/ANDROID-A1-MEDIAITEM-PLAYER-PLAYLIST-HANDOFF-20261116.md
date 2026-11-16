# CELIKOM Android A1 — MediaItem / Player playlist handoff checkpoint

**Date:** 16 November 2026  
**Repository:** manufact-test/nomusic  
**Only working branch:** experiment/android-a1-metrica-init-state-observer-arm13-20261112  
**Latest code checkpoint:** c0cf9896916cca9b13299cdb3fde7a78ffbe4da1  
**CI #213:** [SUCCESS, 127/127 tests](https://github.com/manufact-test/nomusic/actions/runs/43871788563)  
**Exact green backup:** backup/android-a1-playlist-callback-route-closed-ci-green-20261116 @ c0cf9896916cca9b13299cdb3fde7a78ffbe4da1  
**Previous callback/method-handle checkpoint:** 60498b225f634f81f9eab58814e7f7d163839618 — CI #205 SUCCESS.  
**Runtime-hook last change:** a655712d210189f3bc611847235de3ed4d985c1a. No runtime hooks changed after it.

This is a read-only static audit of the exact issuer-signed Yandex Music 2025 XAPK (six DEX). The original binary was not modified or exported. No APK was built, patched, installed, or released. No login, account data, media values, or audio bytes were accessed.

## 1. Product gates — unchanged

- Stage A / NAV17: PASS by owner confirmation.
- Stage B: NOT CONNECTED / NO-GO.
- active_selected_item_proven = false.
- same_native_item_to_decoder_proven = false.
- same_track_album_edition_generation_owner_proven = false.
- codec_output_object_to_audio_sink_proven = false.

The work below improves static object-flow evidence. It does not prove the runtime-selected item or connect that item to decoder output.

## 2. Closed route — do not revisit

The proposed route `LfH7.else()LkD7;` is closed.

- `LkD7;` is a concrete exception class in the signed DEX, with superclass `java.lang.Exception`. It is not MediaItem and is not a proven MediaItem wrapper.
- `Lp24.else()LkD7;` is a short delegate call to `ExoPlayer.else()LX04;` and returns that call result. It is not a current-MediaItem getter.
- Do not restart this route or infer semantics from obfuscated method names.

Full evidence remains in [ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md](ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md).

## 3. TrackWrapper → MediaItem holder path

A source-side MediaItem construction path is proven, but it is not connected to active playback.

- In `LcA9.extends(...)`, a TrackWrapper-typed argument is passed into `Lbq0.this(...)`, which returns `LmLb;`. The code reads an `android.net.Uri` from that result and calls `LOf6.new(Uri)`.
- The exact MediaItem result is then passed into `LiLb.<init>(...)`.
- `LiLb` stores that constructor argument in its own MediaItem-typed field. Its MediaItem-returning getter reads that field and returns the same object reference.
- `LgLb.<init>(...)` is a separate TrackWrapper-accepting path that also creates a MediaItem from a URI and stores it in `LgLb`.

These are proven construction/holder paths only. Do not call either object the active Player item without a same-object handoff into the Player.

## 4. Player current-item getter candidate

The obfuscated Player interface is `LfH7;`. Its no-argument MediaItem-returning method is `E()LOf6;`. The shared ExoPlayer base implementation is `LrD0;.E()LOf6;`.

The signed DEX trace shows this sequence:

1. Call `LfH7.Y()LTva;` to obtain a Timeline.
2. Call `LTva.while()Z` for the timeline state check.
3. Call `LfH7.m0()I` for the current index.
4. Read the Player-held `LTva$d` Window field.
5. Call `LTva.final(ILTva$d;J)LTva$d;` with the index and Window.
6. Read the `LOf6;` MediaItem field from the resulting Window.
7. Return that same field reference.

CI #202/#204 evidence:
- same_window_field_reference_returned = true.
- window_field_produced_by_timeline_window_method = true.
- current_timeline_receiver_identity_proven = false. The bounded tracer clears receiver provenance at the branch; do not upgrade this to a full same-Timeline-object proof.

This is the strongest current-item getter candidate. It is not, by itself, proof that the TrackWrapper-created MediaItem is the object currently returned.

## 5. Player MediaItem mutator chain

The Player-shaped MediaItem mutator contracts are:

- `LfH7;.C(LOf6;J)V`
- `LfH7;.V(LOf6;)V`
- `LfH7;.Z(ILOf6;)V`

The exact forwarding traces show:

- `LsO7;.C/V/Z` forwards the same MediaItem argument to `LBs4;.C/V/Z`.
- `LBs4;.C/V/Z` forwards that same argument to its `LfH7;` delegate.
- `LrD0;.C/V/Z` pass the MediaItem parameter to `Lo45;.default(Ljava/lang/Object;)LwN8;`. `LwN8;` is a List subtype, but the content identity inside that returned list is not proven by this call alone.

Do not infer more API semantics from the obfuscated method letters than the signatures and bodies establish.

## 6. Playlist List → Player setter — inner method proven, outer route closed

Inside the exact method `LXk6;.if(LsO7;LXi6$e;Ljava/util/List;)V`:

- `List.size()` is called on the List parameter.
- `List.get(I)Ljava/lang/Object;` is called on that same parameter.
- The returned Object is cast to `LOf6;` (MediaItem).
- At the next setter call, that same object is passed to `LsO7;.Z(ILOf6;)V`.

The inner `List.get → MediaItem → Player mutator` identity edge is proven. The outer caller route is not:

- A scan of all six signed DEX found **zero direct `invoke-*` callsites** to the exact `LXk6.if(...)` method.
- Exact MethodHandle and referencing call-site scan found zero matching handles, zero matching call-site items and zero `invoke-custom` reference sites.
- `LXk6;` implements `LLl6$c;.if(LsO7;LXi6$e;Ljava/util/List;)V`. This interface has six concrete implementers: `LPk6;`, `LVk6;`, `LXk6;`, `Ldl6;`, `Leg3;`, `Lwg3;`. `LXk6;` is not the unique implementer.
- The only direct interface callsite found is `LKl6;.run()V`. It passes `LsO7;` from a `Lek6;` field, `LXi6$e;` from a `LKl6;` field, and `List` from a `LKl6;` field. The callback receiver `LLl6$c;` is also read from a `LKl6;` field.
- The List argument is therefore traced back to a field on `LKl6;`, but its writer/builder and element provenance were not established.
- Runtime interface dispatch from `LKl6.run()` to `LXk6;` is not proven.

The bounded Player caller census found 52 native-track-related caller rows without truncation. Its `track_bearing_player_mutator_callers` list contains only `LXk6.if(...)` → `LsO7.Z(ILOf6;)V`; this caller has a Player-holder/List contract, no Track/TrackWrapper parameter and no Track/Wrapper-typed owner field. **No exact Track-bearing Player mutator caller was found in this census.**

Close `LXk6.if(...)` as a route for proving TrackWrapper → active Player item. This does **not** prove the List is unrelated to Track; it means the List's elements are unresolved and runtime dispatch to this implementation is unresolved. Do not repeat the exact direct-call, MethodHandle, interface or broad List/Object scans.

Full result: [ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md).

## 7. Decoder / audio sink boundary

The existing sink-side evidence remains separate:

- `LcLb;.O(...)` and `Lbd6;.O(...)` pass their ByteBuffer parameter unchanged to `LbJ2;.native(...)`.
- This proves a ByteBuffer-to-native-sink path, not that the buffer belongs to the MediaItem returned by `LfH7;.E()`.
- No current-item-to-decoder identity edge is proven. Do not repeat the broad sink census.

See [ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md](ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md) for the earlier bounded sink evidence.

## 8. Exact next task

Do not revisit `LXk6.if(...)`. No direct Track-bearing Player mutator caller was found in the bounded census.

Continue only from the already proven source-side chain `TrackWrapper → URI → MediaItem → LiLb holder`:

1. Find only direct callers of the exact MediaItem-returning getter/constructor handoff for `LiLb;`.
2. Check whether the same MediaItem reference is passed into one of the known Player mutators `LsO7/LBs4/LfH7`.
3. If the same object reaches a Player mutator, trace only that object to `LfH7.E()LOf6;`.
4. If no direct caller or same-object edge exists, close this holder route promptly. Do not expand into global Media3, List/Object, competitor, or renderer scans.

Do not repeat the competitor sweep, full Player ancestry, generic getter search, broad LiLb/LgLb holder audit, or ByteBuffer sink census.

## 9. Hard constraints

- Android CELIKOM A1 only. Do not switch to Windows or the browser extension.
- Do not change architecture, vendor behavior, runtime hooks, APK, or original Yandex application.
- Do not add a second Player/decoder/AudioTrack.
- Do not read/export Track/Album IDs, titles, URLs, DataSpec, tokens, account data, private field values, or audio bytes.
- Do not touch NAV17, Test.50, frozen A1/LSPatch baseline, Windows, extension, backend/API/DB, or production.
- No manual owner action is required at this point.
- Work in one bounded block. Stop only at a real blocker or when a manual measurement is genuinely required.

## 10. CI history for this pass

- CI #202: SUCCESS, 122/122 — established the current-item getter and Player mutator forwarding summary.
- CI #203: rejected broad List/Object expansion hit `MEDIA3_ITEM_HANDOFF_METHOD_LIMIT`. It is not the current baseline.
- CI #204: SUCCESS, 122/122 — narrowed List/Object tracing to `LXk6.if(...)` and established the inner `List.get → MediaItem → LsO7.Z` bridge.
- CI #205: SUCCESS — exact direct-call and MethodHandle/`invoke-custom` census; no direct references to the exact method.
- CI #213: SUCCESS, 127/127 — interface callback implementers/caller provenance and Player mutator caller census. Exact signed original, six DEX, read-only.
