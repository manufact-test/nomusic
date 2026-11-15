# CELIKOM Android A1 — signed renderer ByteBuffer field-writer census, 15 Nov 2026

**Scope:** read-only, fail-closed examination of the pinned issuer-signed Yandex Music 2025.10.4 #120.1gpr six-DEX original (16 verified XAPK splits). No runtime instrumentation, build or media access.

**Latest CI-green code:** \`cfd02607829ef854065331571654c94bef5005ba\`.
**CI:** [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS; 49/49 focused Python tests.
**Exact backup:** \`backup/android-a1-renderer-field-writer-census-ci-green-20261115\` @ \`cfd02607829ef854065331571654c94bef5005ba\`.
**Previous backups:** \`backup/android-a1-renderer-field-census-ci-green-20261115\` @ \`9a1d0f9f469ef14783b1d95f2544510de23acd99\`, \`backup/android-a1-renderer-buffer-provenance-ci-green-20261115\` @ \`fa5a84c0db46856f9b30f963c51cf967c3fd845c\`, \`backup/android-a1-audio-output-dispatch-census-ci-green-20261115\` @ \`60192d8e55d48f49f9a95d8e42779aa6ac772b53\`.

## Findings from exact signed DEX

- \`LbJ2\` is the static AudioTrack/ByteBuffer sink candidate, not a proven active playback sink. \`LcLb.O\`, \`Lbd6.O\`, and \`LEF2.j\` are the three established sink-related methods. The 7 exact callsites cover 5 renderer/caller methods; 6 pass a typed ByteBuffer read from a field. Typed buffer reference is NOT identical to proving the codec-returned runtime object.
- New exact field-reference xref finds **3 ByteBuffer field slots** that feed those callsites and **7 writer methods**: \`LRF2.final(I)V\`, \`LcC0.S()V\`, \`LcC0.n(JJ)Z\`, \`LcC0.o()Z\`, \`Lkd6.S()V\`, \`Lkd6.n(JJ)Z\`, \`Lkd6.o()Z\`. Field names and values are not emitted. The numbered slots are local audit labels, not semantic generations or track IDs.
- \`LcC0.n(JJ)Z\` and \`Lkd6.n(JJ)Z\` each contain an exact basic-block \`Lad6.final(I)Ljava/nio/ByteBuffer;\` return-to-field-store reference (slots 2 and 3 respectively). They also have reads of the same declared fields before virtual sink calls. Both contain branches and additional writes, so no continuous same-runtime-buffer path or selected-track dispatch is claimed.
- \`LcC0.o()Z\` / \`Lkd6.o()Z\` store a ByteBuffer returned by \`Lad6.class(I)Ljava/nio/ByteBuffer;\` into slot 1; \`LRF2.final(I)V\` stores the return from \`LRF2.const(I)Ljava/nio/ByteBuffer;\` into that same declared slot. These are static candidates only. \`S()V\` methods also write typed fields without a proven immediate return origin.
- Existing Track+Album identity candidates remain separate from the renderer/AudioTrack objects. No single exact object chain proves current Track, Album, edition/generation and decoder input on the same item. Do not label numeric fields or collections as edition or playback generation.

## Strict interpretation

These observations establish **declared ByteBuffer field write and read references** between codec-like methods and sink callsites. They do not establish that the actual selected song or a particular decoded buffer is the one played. Virtual receiver dispatch, branches, alternative writes, queue/prefetch/download and concurrency have not been proven equivalent to active playback.

Keep all gates false:
\`active_selected_item_proven=false\`; \`same_native_item_to_decoder_proven=false\`; \`same_track_album_edition_generation_owner_proven=false\`; \`codec_output_object_to_audio_sink_proven=false\`.

**Stage A:** NAV17 owner-confirmed access to the real Yandex account, albums, My Wave and audible originals (owner-reported sound, not TXT audio verification). Do not regress. **Stage B:** replacement songs not connected or audible; NO release APK.

## Next bounded block (do not widen to generic hooks)

1. On \`LcC0.n\` / \`Lkd6.n\`, trace receiver and field identity only through bounded basic blocks, with each alternate store/branch treated as uncertainty; do not claim uninterrupted ByteBuffer identity from field type alone.
2. Separately find an actual owner of the **currently selected** native Track (not queue, prefetch or download). Follow bounded Java object identity through a specific player-state/selection method into media source setup and the decoder; the renderer census alone cannot identify the Track.
3. Only after exact Track + Album + edition/generation + actual decoder/audio-renderer identity are proven, connect the existing CELIKOM resolve/entitlement contract before decoder input, with unchanged original fallback. Otherwise fail-closed, no generic hooks.
4. Preserve pinned signed XAPK, NAV17, Test.50, frozen A1/LSPatch, vendor call semantics, accounts, production, Windows, browser extension, backend/API/DB. No second player/decoder, no audio bytes, no IDs/titles/URLs/credentials, no manual owner work without a necessary exact read-only witness.

**Last runtime hook change:** \`a655712d210189f3bc611847235de3ed4d985c1a\`. The three new audit phases modified only \`audit_native_selected_item_handoff.py\` and its isolated unit tests, not runtime hooks.
