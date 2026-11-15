# CELIKOM Android A1 — signed renderer ByteBuffer field-writer census, 15 Nov 2026

**Scope:** read-only, fail-closed examination of the pinned issuer-signed Yandex Music 2025.10.4 #120.1gpr six-DEX original (16 verified XAPK splits). No runtime instrumentation, build or media access.

**Latest code checkpoint:** 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
**CI #151:** [SUCCESS, 104/104](https://github.com/manufact-test/nomusic/actions/runs/43756845719).
**Exact green backup:** backup/android-a1-renderer-field-cfg-trace-ci-green-20261115 @ 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
**Last runtime-hook change:** a655712d210189f3bc611847235de3ed4d985c1a. Runtime hooks unchanged.

## Established native sink boundary

- LbJ2.native(ByteBuffer, long, int) is the native AudioTrack/ByteBuffer sink candidate, not a proven active playback sink.
- LcLb.O and Lbd6.O pass the same ByteBuffer parameter into LbJ2.native. The parameter-to-native-call identity is proven inside those methods.
- The earlier census identified 3 ByteBuffer field slots and 7 writer methods: LRF2.final(I)V, LcC0.S()V, LcC0.n(JJ)Z, LcC0.o()Z, Lkd6.S()V, Lkd6.n(JJ)Z, Lkd6.o()Z.
- Field names and values are not emitted. Slot numbers are local audit labels, not semantic generations or track IDs.

## New branch-sensitive CFG identity trace

The existing analyzer now follows the exact Lad6.final(I)ByteBuffer result through same-instance field store/read and into the virtual O dispatch callsite. CFG states and alternative writes are kept separate.

| Method | Proven path | Other incoming state |
|---|---|---|
| LcC0.n(JJ)Z | Lad6.final pc 193 → slot 2 store pc 197 → read pc 266 → virtual O pc 293 | One of two states has no proven in-method writer origin at read pc 266 |
| LcC0.n(JJ)Z | Same source/store → read pc 331 → virtual O pc 353 | One of two states has no proven in-method writer origin at read pc 331 |
| Lkd6.n(JJ)Z | Lad6.final pc 170 → slot 3 store pc 174 → read pc 232 → virtual O pc 259 | One of two states has no proven in-method writer origin at read pc 232 |
| Lkd6.n(JJ)Z | Same source/store → read pc 282 → virtual O pc 304 | One of two states has no proven in-method writer origin at read pc 282 |

For each of the four callsites, there are two distinct incoming CFG identity states: one proves the same Lad6.final Java reference from method return through the exact field slot/read to the virtual O call; the other remains unknown. Therefore:

- Method-local same-reference path: **proven for one state per callsite**.
- Same reference on every incoming state: **not proven**.
- No merging of unknown states with the Lad6.final path.
- Later unknown writes to slot 2 / slot 3 occur after the listed callsites and remain separate.
- The ByteBuffer argument is logical argument position 4 (register-word position 6) in the O call signature.

The virtual call references are LcC0.O and Lkd6.O, with possible sink implementations LcLb.O and Lbd6.O. The implementation parameter-to-LbJ2.native link is proven, but runtime virtual dispatch to those implementations is not. The CFG trace does not include exception edges and does not model external field mutation or reentrant calls.

## Current selected Track/Album bridge — not found

The same signed-DEX report still has:

- Zero direct Track-parameter callsites into Player selection, MediaSession state/metadata, native descriptor, or decoder boundaries.
- 267 Track-field owners; zero with Player API, MediaSession, decoder, MediaSource/source-like, or Kotlin Flow fields.
- 16 shared Track/Album or Track/wrapper owner candidates; 44 method summaries and 16 inbound-caller summaries. No candidate method calls Player API, MediaSession, decoder boundary, or source descriptor.
- The only two typed identity handoffs lead to auxiliary constructors, not to a proven current selected item.
- No Edition/Generation type descriptor or named/typed Edition/Generation field on Track or Album.

The exact missing link is the owner of the currently selected Track/Album and an identity edge from that owner to this decoder/render path. Queue, prefetch, download and helper constructors are not evidence of active playback.

## Strict interpretation

These observations establish one method-local ByteBuffer reference path for one of two incoming CFG states at each of four virtual dispatch callsites. They do not establish that the actual selected song or a particular decoded buffer is the one played. Runtime receiver dispatch, external field mutation, exception edges, active selection, Track/Album/edition/generation identity and concurrency are not proven.

Keep all gates false:
active_selected_item_proven=false;
same_native_item_to_decoder_proven=false;
same_track_album_edition_generation_owner_proven=false;
codec_output_object_to_audio_sink_proven=false.

**Stage A:** NAV17 owner-confirmed access to the real Yandex account, albums, My Wave and audible originals. Do not regress.
**Stage B:** replacement songs are not connected or audible; NO release APK.

## Next bounded action

Do not repeat this census or add generic runtime hooks. Do not change APK/vendor code. Continue only when a concrete identity-bearing witness of the current selected Track is available at an exact Player selection callsite; then connect the same Track + Album + edition/generation to this decoder/render path. Without that witness, keep the blocker explicit and stop.

No runtime hooks changed, no APK was built/patched/installed/released, and no field values, media identifiers, URLs, DataSpec, tokens, account data or audio bytes were read or exported.