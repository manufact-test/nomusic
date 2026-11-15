# CELIKOM Android A1 — Track/Album identity bridge

**Дата:** 15 ноября 2026  
**Репозиторий:** manufact-test/nomusic  
**Рабочая ветка:** experiment/android-a1-metrica-init-state-observer-arm13-20261112

## Checkpoint

- Runtime code commit: a655712d210189f3bc611847235de3ed4d985c1a.
- Branch HEAD before documentation update: 90f8ea394e1ac4168aa63f976e17fd18eb24befb.
- Current clone-green / publisher-first-green backup: backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb.
- Pre-large-push rollback: backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5.

## Static signed DEX findings

[Audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959) **SUCCESS**. The new Album summary objects are count-only. The broader legacy audit JSON still includes bounded signed-DEX method/field examples, so keep raw audit logs internal and do not paste the raw dump into public/user-facing text.

1. The native Track model declares one field typed as Album.
2. Two Track constructors accept exactly one Album-typed argument. Static inspection did **not** prove a direct write of that same argument to the Track instance's Album field (constructors_storing_same_album_argument_on_track = 0). Do not claim the constructor alone proves the model field value.
3. One exact Track copy-method shape accepts a Track and an Album and returns a Track. It reads the source Track's Album field; static register tracing finds a path that passes the Album argument to a Track constructor and returns a new Track. This is an **argument-to-returned-Track candidate**, not a proof that every branch uses that argument.
4. The copy method and constructor signatures give a safe read-only observation point: capture only the Album-typed argument and resulting Track object after the original method returns. Never read Track fields or Album values directly.

## Runtime observer added

Files:
- exit-callsite-witness-module/.../StageBAudioEvidence.java
- exit-callsite-witness-module/.../ExitCallsiteWitness.java
- ci/test_a1_stage_b_audio_evidence.py
- ci/a1_metrica_witness_private_parser.py
- ci/test_a1_metrica_witness_private_parser.py

Hooks:
- AUDIO_NATIVE_TRACK_ALBUM_HOOK: registers the two constructors that contain exactly one Album parameter; synthetic constructors with no Album parameter are ignored.
- AUDIO_NATIVE_TRACK_ALBUM_COPY_HOOK: registers the exact Track copy method and captures its returned Track plus Album argument after the unmodified original method returns.
- Both hooks are protective: observer errors do not replace or suppress the vendor method result/exception.

Identity handling:
- Only weak references to Track and Album objects are retained; comparisons use Java ==.
- No Track field reflection, Album ID/title/name, URLs, DataSpec, account values, credentials, headers, tokens or audio buffers are read or retained.
- Track→Album association conflicts revoke the Album link. The map is bounded to 32 Track identities; source links remain bounded to 16.
- Album identity is propagated through:
  Track constructor/copy result → Track Flow → wrapper → descriptor → factory → DataSource instance → successful open → positive read.
- TRACK_SOURCE_ALBUM_READ_LINK is only marked after the exact linked source had a successful open() and a positive read(). Reopen/close and identity conflicts invalidate the evidence.
- The read hot-path scan remains bounded to 256 inspections per source/reopen window; TRACK_SOURCE_READ_SCAN_EXHAUSTED means sampling ended, not that a source is absent.

New summary counters:
- TRACK_ALBUM_CONSTRUCTOR_LINK
- FLOW_TRACK_ALBUM_LINK
- TRACK_WRAPPER_ALBUM_LINK
- TRACK_DESCRIPTOR_ALBUM_LINK
- TRACK_FACTORY_ALBUM_LINK
- TRACK_SOURCE_ALBUM_LINK
- TRACK_SOURCE_ALBUM_OPEN_LINK
- TRACK_SOURCE_ALBUM_READ_LINK
- TRACK_ALBUM_IDENTITY_CONFLICT

The summary is now 53 rows; AUDIO_STAGE_B_STATUS is the final row at index 52.

## CI validation

- [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**.
- [Clone-only native ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations, both Album hooks and all existing Track/Exo source hooks REGISTERED.
- [Publisher-first native ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original publisher app 16/16 splits and clone co-installed, 25/25 stable observations, no suppression, both Album hooks and all Track/Exo source hooks REGISTERED.
- Final CI verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.
- stage_a = NO_GO, stage_b_current_player_album_edition_attested = false, audio_or_account_tested = false.

## What this does NOT prove

- Track Flow may include queued, prefetched or download-only tracks; it is not proof of the current audible selection.
- The Album-typed constructor/copy argument association is not proof of edition/generation semantics. The Track model has other nested metadata types, but their meanings are not yet established.
- A positive Exo DataSource read proves source activity only. It does not prove that this is the current player item or that the bytes reached the active decoder.
- The separate signed 2025 audio inventory found two private MediaDataSource implementations and one MediaExtractor.setDataSource(MediaDataSource) sink candidate. It did not prove a same-object chain from that source through readSampleData to MediaCodec input/AudioTrack output. Do not assume MediaExtractor is the music decoder solely from registration.
- No audio/account playback was tested in CI.

## Next work

1. Identify the current selected Track state, distinguishing it from queue, prefetch and download work. Use identity-only observations; no field-value reads.
2. Identify the exact edition/generation object and its relation to the selected Track/Album. Use signed DEX structure and method flows; do not guess semantics from obfuscated names.
3. Trace the same source identity to the actual decoder input/renderer. Establish an object-level path, not merely class-level hook registration.
4. When the owner supplies a diagnostics file, read the nine Album counters alongside open/read/close counters. Distinguish NONE, conflict, scan exhausted and hooks not registered.
5. Keep Stage A **NO-GO** until current Track + Album + edition + decoder identity and actual audio are demonstrated.

Do not modify Test.50, frozen A1, Windows, browser extension, backend, original publisher app or account. Do not ask the owner to install/test a new APK unless a specific owner-side measurement is genuinely required.


## Follow-up: selected-state / MediaSession / decoder boundary census — 15.11.2026

Latest static-audit code checkpoint: `8eb2e6a3bc61643219ddc2e261853f8a3bd4865f`. Runtime Java hooks were not changed; last runtime-hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. The new CI-green code backup is `backup/android-a1-track-return-callsite-ci-green-20261115` @ `8eb2e6a3bc61643219ddc2e261853f8a3bd4865f`. Pre-change backups: `backup/android-a1-selected-item-deeper-audit-prechange-20261115` @ `28cf873d8cc14cf6f62cafea0fb38fe9df3897e0`, `backup/android-a1-track-state-callsite-census-pre-20261115` @ `0cefeaa01b5f17aa455544d86064a288348e0baa`, and `backup/android-a1-track-return-callsite-pre-20261115` @ `15824db97162db20115da35ea41d80b98e1be814`. The earlier runtime/Album CI-green backup remains `backup/android-a1-track-album-publisher-first-ci-green-20261115` @ `90f8ea394e1ac4168aa63f976e17fd18eb24befb`.

### Final static findings on the exact pinned signed 2025.10.4 #120.1gpr six-DEX original

- [MediaSession / decoder boundary scan #43705414957](https://github.com/manufact-test/nomusic/actions/runs/43705414957): SUCCESS.
- [Typed boundary callsite census #43705670723](https://github.com/manufact-test/nomusic/actions/runs/43705670723): SUCCESS.
- [Track-returning helper census #43705962875](https://github.com/manufact-test/nomusic/actions/runs/43705962875): SUCCESS; 16/16 focused Python tests passed.
- MediaSession metadata: 1 unique method reference, 6 callsites in 5 caller methods. No Track/Album parameter, Track/Album field read, Track/Album model method call, or Track/Album-returning helper was found before those callsites.
- MediaSession state: 4 unique method references, 8 callsites in 7 caller methods. The same Track/Album relationships were absent.
- Decoder/render boundaries: 19 unique method references, 48 callsites in 38 caller methods. No Track/Album parameter, field read, model method call or Track/Album-returning helper was found before those callsites. Seven callsites read an integer/wide field from their own receiver; this is not evidence of a generation counter.
- No explicit Edition/Generation type descriptor or named/typed Edition/Generation field was found on the native Track or Album models. This is a bounded static result, not proof that no obfuscated or indirect representation exists.
- Direct Track-parameter flow into public Player selection/transport, MediaSession, decoder boundaries and the native descriptor builder: zero. The single direct Track-to-source call remains the known download/source-descriptor coroutine candidate; it is not proof of the currently selected player item.
- Existing Album constructor/copy result remains unchanged: one Album-typed field on Track; two Track constructors accept Album, but direct same-object storage into Track's own field is not proven. One Track+Album→Track copy candidate reads the source Track's Album field, passes the Album argument to a Track constructor and returns Track; storage on the returned Track is not proven.

### Scope and interpretation

This is same-method static structure only. It does not infer virtual receiver selection, branches, coroutine resumption, reflection, cross-method alias flow, current playback state or audio output. It does not read runtime field values, album names/IDs, URLs, DataSpec values, account data, tokens or audio bytes; the final census does not scan arbitrary DEX strings. Do not treat zero direct links as proof that no indirect path exists.

No runtime hook was added or changed, no APK was built or published, no owner phone/account was touched, and no playback/audio test was run. Stage A remains **NO-GO**; `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

### Next bounded research block

1. Inventory all classes that declare a Track-typed field and their structural relationship to player/source owners; do not assume a field means current selection.
2. Trace Track-typed values returned by helper methods across one bounded caller edge, with register identity and branch/coroutine uncertainty explicitly marked.
3. Only add a read-only runtime hook after a concrete player-state owner and exact method/callsite are identified. Do not add generic MediaSession/MediaCodec hooks as substitutes.
4. Keep edition/generation unclaimed until a distinct object or stable generation boundary is structurally linked to the same Track and Album.
5. Continue to require the same identity at actual decoder input/audio renderer; a Track Flow or DataSource read remains insufficient.


## Superseding follow-up: class-level Track owner inventory — 15.11.2026

Latest static-audit code checkpoint: `22e468df44b45f7bcbebd6261f25df816ff6d0aa`. CI [#43706266458](https://github.com/manufact-test/nomusic/actions/runs/43706266458) is **SUCCESS**, with 18/18 focused Python tests passing. CI-green code backup: `backup/android-a1-track-owner-inventory-ci-green-20261115` @ `22e468df44b45f7bcbebd6261f25df816ff6d0aa`. The prior `8eb2e6a3` checkpoint and its backup remain valid historical checkpoints; no runtime hook was changed by either static-audit extension.

The exact pinned signed 2025.10.4 #120.1gpr six-DEX inventory found:

- 267 class owners with a Track-typed instance field; 127 with an Album-typed instance field.
- 14 owners have both Track- and Album-typed instance fields; 2 have both Track and the track-ID wrapper.
- Zero Track-field owners have a Player API field, implement the standard Player API, or have a MediaSession, decoder, source-like or Kotlin Flow field.
- 23 Track-field owners also have a collection field; 91 have an integer/wide numeric field. These are only structural categories: do not label them queue or generation without an actual dataflow proof.
- MediaSession and decoder boundary caller classes also have zero Track/Album field owners. Combined with the previous census, there is no same-method Track/Album parameter, field-read, model-method or Track/Album-returning-helper link before those boundaries.

This does **not** prove that no indirect player-state path exists: cross-method object aliasing, coroutine resumption, virtual receiver choice and reflection are not inferred. It does establish that no safe class-level Player/source owner has yet been identified from the pinned DEX. The single direct Track-to-source path remains the download/source-descriptor candidate, not current selection.

### Next bounded research block (supersedes the earlier inventory task)

1. Inspect the 14 shared Track/Album owner classes and the 2 Track/wrapper owner classes through one bounded caller edge; classify methods by typed parameters/returns and object identity, not names guessed from obfuscated symbols.
2. Trace whether a stable Track wrapper or returned Track object is handed to the actual player owner through a method boundary. Keep queue, prefetch and download candidates separate.
3. If no identity-bearing player owner emerges, do not add generic MediaSession/decoder hooks. A real playback witness will then be the only meaningful next measurement; do not ask the owner for manual steps or an APK install until the exact hook/callsite is known.
4. Edition/generation remains unproven. Numeric fields and collection fields are not semantic evidence.

Stage A remains **NO-GO**. No runtime hooks changed, no APK was built/published, no owner phone/account was touched, and no audio playback was tested.


## Superseding follow-up: shared-owner one-hop census and renderer CFG — 15.11.2026

**Latest code checkpoint:** 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
**CI #151:** SUCCESS, 104/104 tests — [run 43756845719](https://github.com/manufact-test/nomusic/actions/runs/43756845719).
**Code backup:** backup/android-a1-renderer-field-cfg-trace-ci-green-20261115 @ 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
**Runtime hooks:** unchanged; last change remains a655712d210189f3bc611847235de3ed4d985c1a.

### Shared owner result

The existing bounded signed-DEX census covered 16 shared Track/Album or Track/wrapper owner candidates, 44 method summaries and 16 inbound-caller summaries. No candidate method calls Player API, MediaSession, decoder boundary or native source descriptor. Two typed identity handoffs were found, but both lead only to auxiliary constructors:
- a Track parameter is passed to a Track/Album constructor;
- a Track plus wrapper fields are passed to a continuation constructor.

Neither handoff proves the currently selected Track or connects to the renderer. Do not repeat the 16-owner census. The separate direct Track-to-source coroutine candidate remains download-related, not current playback.

### Renderer CFG result

- LcC0.n: source pc 193 → slot 2 store pc 197 → reads pc 266 / 331 → virtual O calls pc 293 / 353. Each call has two incoming identity states; one preserves the Lad6.final reference, one has no proven writer origin.
- Lkd6.n: source pc 170 → slot 3 store pc 174 → reads pc 232 / 282 → virtual O calls pc 259 / 304. Same one-of-two state result.
- The field-reference path is method-local and partial. Runtime virtual dispatch, active selected item, and Track/Album identity to decoder are not proven.

### Exact blocker and decision

The current selected Track/Album owner is still missing. The static report has zero direct Track-parameter links to Player selection, MediaSession, native descriptor or decoder boundaries; zero Track-field owners with Player API, MediaSession, decoder or source-like fields; and no Edition/Generation type or field on Track/Album.

Stage B remains **NOT CONNECTED / NO-GO**. No new runtime hook, APK or vendor change. Do not expand the static scan or ask for manual owner steps without an exact necessary read-only witness.