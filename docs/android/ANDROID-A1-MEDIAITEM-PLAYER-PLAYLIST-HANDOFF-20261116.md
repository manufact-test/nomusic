# CELIKOM Android A1 — MediaItem / Player playlist handoff checkpoint

**Date:** 16 November 2026  
**Repository:** manufact-test/nomusic  
**Only working branch:** experiment/android-a1-metrica-init-state-observer-arm13-20261112  
**Code checkpoint:** 31fc7e48dfe7f77eca038277ff61783ed784e6a6  
**CI #204:** [SUCCESS, 122/122 tests](https://github.com/manufact-test/nomusic/actions/runs/43864810093)  
**Exact green backup:** backup/android-a1-player-playlist-mediaitem-ci-green-20261116 @ 31fc7e48dfe7f77eca038277ff61783ed784e6a6  
**Previous green checkpoint:** eee44500e973a92ffc0772e7101616db2cc2449c — [CI #202 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43863099235)  
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

The proposed route LfH7.else()LkD7; is closed.

- LkD7; is a concrete exception class in the signed DEX, with superclass java.lang.Exception. It is not MediaItem and is not a proven MediaItem wrapper.
- Lp24.else()LkD7; is a short delegate call to ExoPlayer.else()LX04; and returns that call result. It is not a current-MediaItem getter.
- Do not restart this route or infer semantics from obfuscated method names.

Full evidence remains in ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md.

## 3. TrackWrapper → MediaItem holder path

A source-side MediaItem construction path is proven, but it is not connected to active playback.

- In LcA9.extends(...), a TrackWrapper-typed argument is passed into Lbq0.this(...), which returns LmLb;. The code reads an android.net.Uri from that result and calls LOf6.new(Uri).
- The exact MediaItem result is then passed into LiLb.<init>(...).
- LiLb stores that constructor argument in its own MediaItem-typed field. LiLb.for() reads that field and returns the same object reference.
- LgLb.<init>(...) is a separate TrackWrapper-accepting path that also creates a MediaItem from a URI and stores it in LgLb.

These are proven construction/holder paths only. Do not call either object the active Player item without a same-object handoff into the Player.

## 4. Player current-item getter candidate

The obfuscated Player interface is LfH7;. Its no-argument MediaItem-returning method is E()LOf6;. The shared ExoPlayer base implementation is LrD0;.E()LOf6;.

The signed DEX trace shows this sequence:

1. Call LfH7.Y()LTva; to obtain a Timeline.
2. Call LTva.while()Z for the timeline state check.
3. Call LfH7.m0()I for the current index.
4. Read the Player-held LTva$d window field.
5. Call LTva.final(ILTva$d;J)LTva$d; with the index and Window.
6. Read the LOf6; MediaItem field from the resulting Window.
7. Return that same field reference.

CI #202/#204 evidence:
- same_window_field_reference_returned = true.
- window_field_produced_by_timeline_window_method = true.
- current_timeline_receiver_identity_proven = false. The bounded tracer clears receiver provenance at the branch; do not upgrade this to a full same-Timeline-object proof.

This is the strongest current-item getter candidate. It is not, by itself, proof that the TrackWrapper-created MediaItem is the object currently returned.

## 5. Player MediaItem mutator chain

The Player-shaped MediaItem mutator contracts are:

- LfH7;.C(LOf6;J)V
- LfH7;.V(LOf6;)V
- LfH7;.Z(ILOf6;)V

The exact forwarding traces show:

- LsO7;.C/V/Z forwards the same MediaItem argument to LBs4;.C/V/Z.
- LBs4;.C/V/Z forwards that same argument to its LfH7; delegate.
- LrD0;.C/V/Z pass the MediaItem parameter to Lo45;.default(Ljava/lang/Object;)LwN8;. LwN8; is a List subtype, but the content identity inside that returned list is not proven by this call alone.

Do not infer more API semantics from the obfuscated method letters than the signatures and bodies establish.

## 6. Playlist list → Player setter — new concrete bridge

The exact method LXk6;.if(LsO7;LXi6$e;Ljava/util/List;)V is now traced with List/Object flow limited to this one method.

The trace shows:

- List.size() on the List parameter.
- List.get(I)Ljava/lang/Object; at instruction ordinal 19.
- The returned Object is moved at ordinal 22 and cast to LOf6;.
- At ordinal 25, that same returned object is passed to LsO7;.Z(ILOf6;)V. The call event carries both Object and MediaItem identity aliases with RETURNED_FROM_METHOD origin.

Therefore, the List.get result → MediaItem cast → Player mutator argument identity is proven on this path.

Important limitations:

- The List.get receiver identity is not proven across the preceding branch; the trace deliberately clears aliases there.
- The direct caller census for LXk6;.if(...) found no caller in the bounded Track/holder-relevant set. This is not an unconditional all-caller census.
- The LXi6$e; profile contains only primitive/other-object/Bundle field types; no Track, TrackWrapper, or MediaItem field was found.
- The only Track/holder-relevant Player-mutator caller currently reported is LXk6;.if(...) itself because it accepts the LsO7; Player holder. It does not accept Track/TrackWrapper and its owner has no Track/Wrapper field.

The bridge proves that a MediaItem taken from a List reaches a Player mutator. It does not prove where that List or its item originated.

## 7. Decoder / audio sink boundary

The existing sink-side evidence remains separate:

- LcLb;.O(...) and Lbd6;.O(...) pass their ByteBuffer parameter unchanged to LbJ2;.native(...).
- This proves a ByteBuffer-to-native-sink path, not that the buffer belongs to the MediaItem returned by LfH7;.E().
- No current-item-to-decoder identity edge is proven. Do not repeat the broad sink census.

See ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md for the earlier bounded sink evidence.

## 8. Exact next task

Continue only from the unresolved List source for LXk6;.if(LsO7;LXi6$e;Ljava/util/List;)V:

1. Find direct callers of this exact method, not a generic Player/Media3 caller census.
2. Identify where its List argument is built and whether its elements originate from TrackWrapper/Track.
3. If a TrackWrapper-derived MediaItem reaches List.get, prove the same object through the cast and LsO7;.Z(...).
4. Then connect that exact object to the LfH7;.E()LOf6; current getter / Timeline.Window field. Only after that investigate the already-known decoder sink.
5. If the List source is not Track/TrackWrapper-derived, close this route and find the exact Track-bearing caller of the Player mutator.

Do not repeat the competitor sweep, full Player ancestry, generic getter search, LiLb/LgLb holder analysis, or ByteBuffer sink census.

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
- CI #203: rejected broad List/Object expansion hit MEDIA3_ITEM_HANDOFF_METHOD_LIMIT. It is not the current baseline.
- CI #204: SUCCESS, 122/122 — narrowed List/Object tracing to LXk6;.if(...) and established the List.get → MediaItem → Player mutator bridge.
