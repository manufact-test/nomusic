# SUPERSEDING CURRENT STATE — 15 Nov 2026, LDT0 Track/Flow split

**Current code checkpoint:** `b250aba2ca5e7555995099683736be572f0ef578`  
**CI:** [#43738914218](https://github.com/manufact-test/nomusic/actions/runs/43738914218) **SUCCESS, 80/80 tests**; exact pinned original verified (16 signed splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-ldt0-track-flow-origin-ci-green-20261115` @ the checkpoint above.  
**Detailed audit:** `docs/android/ANDROID-A1-FLOW-MODE-AND-INTERFACE-CENSUS-20261115.md`.

### Result of the one-callsite follow-up

The only `Ljm4.for(Flow, Scope, Collector)` callsite inside `LDT0.<init>(Album, Track, ...)` is now classified:

- Its Flow argument is the result of `LvF6.case(Album): Flow`. It is Album-derived, not derived from the Track parameter. Close this as a Track-to-Flow candidate.
- The same constructor separately passes its exact Track parameter to `LSW6.if(Track, boolean)`.
- It also passes that Track parameter to `LOW6.<init>(..., Track, ...)`.
- These are exact local Java-reference/register-flow candidates. They do not yet establish player selection, runtime dispatch, decoder input or audio output.

The focused signed-DEX audit remained read-only. CI passed 80/80; no APK, account/media access, runtime hook or vendor behavior change.

### Next exact task — one bounded hop only

Inspect only:
1. `LSW6.if(Track, boolean)`
2. `LOW6.<init>(..., Track, ...)`

Follow the same Track parameter through exact field stores and method calls. Determine whether either path reaches a concrete player-selection/transport owner, source descriptor, or the already identified decoder/audio sink. If neither does, close this branch; do not broaden to generic Flow, MediaSession or decoder APIs.

Do not return to the Album-derived `LDT0 → LvF6.case → Ljm4.for` branch.

**Gates remain:** `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`; CELIKOM replacement remains NOT CONNECTED. NAV17 Stage A remains owner-confirmed PASS; Stage B remains research-only / NO-GO for replacement. No release APK.

---

# SUPERSEDING CURRENT STATE — 15 Nov 2026, Flow mode audit

**Current branch HEAD:** `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`  
**CI:** [#43737913160](https://github.com/manufact-test/nomusic/actions/runs/43737913160) **SUCCESS, 80/80 tests**; exact signed original verified (16 splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-flow-mode-branch-audit-ci-green-20261115` @ `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`.  
**Detailed result:** `docs/android/ANDROID-A1-FLOW-MODE-AND-INTERFACE-CENSUS-20261115.md`.

The previous handoff's 72/72 / `3f6f9d7` headline is superseded. Current commit changes only the read-only signed-DEX audit and its tests; no runtime hooks or APKs changed.

### What this pass established

- Exact Flow mode switch keys and target blocks are now mapped for the bounded source classes. The selector comes from an integer constructor argument stored in a field; runtime branch choice is **not** proven.
- Direct implementer counts for generic Flow/FlowCollector interfaces are too broad to identify the active player path.
- Of 160 `Ljm4.for(Flow, Scope, Collector)` callsites, exactly one originates in a method accepting both Album and Track: `LDT0.<init>(Album, Track, ...)`. Its Flow argument is not yet proven to derive from that Track.
- `LzE7.collect` has a separate opaque-object-to-Track branch candidate; branch choice and active playback are unproven.
- Existing `LDp0.if` / `Lwp0$a.emit` Track-parameter identity results remain valid, but neither proves active selected playback.

### Exact next task

Inspect only `LDT0.<init>` and its `Ljm4.for` callsite. Prove or reject whether the Flow argument derives from the exact Track parameter. If it does not, close this candidate; do not fan out across the other generic Flow callsites. If it does, follow one bounded hop and distinguish active playback from queue/prefetch/download.

**Gates remain:** `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`; CELIKOM replacement is not connected. NAV17 Stage A remains owner-confirmed PASS; Stage B remains research-only / NO-GO for replacement. No release APK.

---

# SUPERCEDING ADDENDUM — 15 Nov 2026, renderer field writer xrefs

Current read-only checkpoint: `cfd02607829ef854065331571654c94bef5005ba`, CI [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS, 49/49 tests; exact backup `backup/android-a1-renderer-field-writer-census-ci-green-20261115`. Details: `docs/android/ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md`. Three exact ByteBuffer fields and seven writer methods; exact `Lad6.final(I)ByteBuffer` store references in `LcC0.n` and `Lkd6.n`. That is a **static field reference**, not a verified active Track or decoded object at audio sink. All selected identity gates remain false. NAV17 Stage A stays owner-confirmed PASS and Stage B replacement is unconnected. Historical Stage A NO-GO material below is superseded.

---

# CURRENT SUPPLEMENT — 15 Nov 2026, AudioTrack / ByteBuffer checkpoint

## Superseding technical checkpoint — 15 Nov 2026 (AudioTrack / ByteBuffer)

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 established the real owner flow; the owner reported audible original Yandex playback after login, with albums and My Wave visible. The diagnostic TXT does not independently verify the audio output. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

- Static audit code: `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Audit CI: [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) **SUCCESS**, 40/40 focused tests; verdict `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.
- Exact CI-green code backup: `backup/android-a1-audio-buffer-identity-ci-green-20261115` @ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Pre-fix rollback: `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`.
- Last runtime Java hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. This pass changed only the read-only static audit and its tests; no runtime hook, APK, account, phone or production component changed.

### Exact signed-DEX findings

- `LbJ2` implements `Lpk0` and declares typed `AudioTrack` and `ByteBuffer` fields. Its `native(ByteBuffer, long, int)` method is the concrete native audio-buffer entry candidate; the same owner also exposes the AudioTrack construction/control path (`play`, `pause`, `flush`, AudioTrack factory methods).
- Two direct class callsites pass the caller's exact ByteBuffer parameter to `LbJ2.native`: `LcLb.O(..., ByteBuffer, ...)` at ordinal 43 and `Lbd6.O(..., ByteBuffer, ...)` at ordinal 38. Both use the same caller parameter register (v6); the bounded register-write census found no write to it, and the invoke word map correctly accounts for the wide `long` argument occupying two register words. This is a static same-register provenance result, not runtime playback proof.
- `LEF2.j()` calls the exact `Lpk0.native(ByteBuffer, long, int)` interface reference and passes a ByteBuffer read from a typed field. `LbJ2` implements `Lpk0`, but the audit does not infer the runtime interface receiver/dispatch or prove that this is the same object as either direct class callsite.
- Branch handling now preserves a caller ByteBuffer parameter only when its original register is not written anywhere in the method (including the second word of wide writes). Other aliases are discarded at branch joins; the audit deliberately prefers false negatives over path-insensitive identity claims.
- Invoke mapping now expands `J`/`D` into two register words and reports both logical argument positions and register-word positions. Static and instance/interface invocation fixtures are separately tested.

### What remains unproven

`active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. We have not connected this ByteBuffer to the current selected Track, its Album, edition/generation, or the exact same item observed at the native decoder/audio renderer. No CELIKOM source resolver is wired into this path; no replacement source is selected. The audit does not read ByteBuffer contents, Track/Album field values, names/IDs, URLs, DataSpec, account data, tokens or audio bytes.

### Next work

1. Trace the actual caller/owner path into `LcLb.O` and `Lbd6.O`; distinguish active playback from queue, prefetch and download. Keep virtual/interface dispatch and coroutine resume uncertainty explicit.
2. Join the proven audio-buffer sink path to the exact Track/Album identity only by bounded Java object identity. Do not infer it from method names, timing or matching types.
3. Establish a distinct edition/generation identity for that same selected item. Numeric fields and collection fields alone are not semantics.
4. Require the same selected identity at the decoder/audio renderer. Only then connect the existing authorized CELIKOM resolve/entitlement contract before decoder input, preserving the single native player and original fallback.
5. Do not ask the owner for another login, APK install or manual diagnostic until a concrete read-only measurement is identified.



The historical sections below describe earlier checkpoints and remain useful background; this supplement supersedes their old branch SHA, old “Stage A = NO-GO” status and old next-task ordering.

---

# CELIKOM Android A1 — Track/Album + Exo continuity handoff

**Date:** 15 November 2026  
**Repository:** manufact-test/nomusic  
**Active branch:** experiment/android-a1-metrica-init-state-observer-arm13-20261112  
**Latest code/static audit:** 90f8ea394e1ac4168aa63f976e17fd18eb24befb  
**Last runtime hook change:** a655712d210189f3bc611847235de3ed4d985c1a

## Exact backups

- CI-green code: backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb
- Pre-large-push: backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5
- Final docs/code handoff: backup/android-a1-track-album-final-handoff-20261115-v2.

## Static signed-DEX result

[Audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959) succeeded with verdict SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY.

- Track declares one Album-typed field.
- Two Track constructors each accept exactly one Album argument.
- Neither constructor was proven to write that same argument to Track's own Album field: constructors_storing_same_album_argument_on_track = 0.
- One exact Track copy method accepts Track + Album and returns Track.
- That method reads the source Track's Album field, passes the Album argument to a Track constructor and returns a Track.
- The audit did **not** prove the Album argument is stored on the returned Track: copy_methods_storing_album_argument_on_new_track = 0. Passing an argument into a constructor plus returning a Track is only a candidate flow, not proof of resulting field identity.
- It did not prove the source Track's Album field is what is passed to that constructor: copy_methods_passing_source_track_album_to_track_constructor = 0.
- active_selected_item_proven = false; current song/audio was not accessed.

The new count-only Album summary objects do not expose names. The broader legacy audit JSON still contains bounded signed-DEX method/field examples; keep raw audit logs internal and do not paste the raw dump into public/user-facing text.

## Runtime identity hooks

In ExitCallsiteWitness.java:

- AUDIO_NATIVE_TRACK_ALBUM_HOOK: hooks the two constructors containing one Album parameter. The original constructor runs once; only after normal return, the hook associates this Track with the exact Album argument.
- AUDIO_NATIVE_TRACK_ALBUM_COPY_HOOK: hooks the exact Track copy method. The original method runs once; after normal return, the hook associates the returned Track with the exact Album argument.
- Both hooks use protective interception. Observer failures are ignored and do not replace the vendor method's result or exception.

In StageBAudioEvidence.java:

- Only weak references to Track and Album objects are retained; identity is compared with Java ==, never vendor equals/hashCode/toString.
- Track→Album links are bounded to 32; Track→source lineage links to 16. Conflicting Album associations revoke the link and invalidate downstream Album evidence.
- The Album association is propagated only through exact object links: Track Flow → wrapper → descriptor → factory result → DataSource instance.
- TRACK_SOURCE_ALBUM_OPEN_LINK requires the linked source's original open() to return normally.
- TRACK_SOURCE_ALBUM_READ_LINK requires a positive read from that same source after successful open. A failed reopen or close revokes open proof. A read before a witnessed successful open is classified as unverified.
- Read-path identity inspection is capped at 256 callbacks per source/reopen window. TRACK_SOURCE_READ_SCAN_EXHAUSTED means sampling stopped, not that a source does not exist.
- No Track/Album field values, album IDs/titles, URLs, DataSpec values, credentials, tokens, headers or audio bytes are read by this Album identity bridge.

Nine Album summary rows:
TRACK_ALBUM_CONSTRUCTOR_LINK, FLOW_TRACK_ALBUM_LINK, TRACK_WRAPPER_ALBUM_LINK, TRACK_DESCRIPTOR_ALBUM_LINK, TRACK_FACTORY_ALBUM_LINK, TRACK_SOURCE_ALBUM_LINK, TRACK_SOURCE_ALBUM_OPEN_LINK, TRACK_SOURCE_ALBUM_READ_LINK, TRACK_ALBUM_IDENTITY_CONFLICT.

The Stage B summary has 53 rows; AUDIO_STAGE_B_STATUS is the final row (index 52), and remains CELIKOM_REPLACEMENT / NOT_CONNECTED.

## CI results

- [Clone-only ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations; Album constructor/copy hooks, Track Flow/request/continuation/wrapper hooks, native main source hooks and Exo source hooks all registered. Publisher intentionally absent in this control.
- [Publisher-first ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original 16/16 splits and clone concurrently installed, publisher remained installed, 25/25 stable observations, no Metrica fatal suppression; the same Track/Album/Exo hooks registered.
- [Static Track/Album audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**, result described above.

These CI runs validate hook registration, lab lifecycle and static candidate analysis only. They do not validate audio playback, account login, the selected current item, edition/generation or decoder input. No owner phone was touched; no APK was published. Stage A remains **NO-GO**.

## Next work

Continue with bounded, read-only investigation:

1. Find the exact current selected Track state and distinguish it from queue, prefetch, download and stale Track Flow emissions.
2. Identify the edition/generation object structurally and prove its identity relationship to the selected Track/Album. Do not guess from obfuscated symbols.
3. Trace the same object identity to the real decoder input and renderer. Class-level hook registration or Exo DataSource read alone is insufficient.
4. If owner diagnostics arrive, parse the nine Album counters with the Track/Exo lifecycle counters. Distinguish NO_HOOK, no observations (NONE), conflict and scan exhaustion.
5. Keep AUDIO_STAGE_B_STATUS truthful and Stage A **NO-GO** until current Track + Album + edition + decoder identity and actual audio are demonstrated.

## Do not do

No architecture rewrite; no changes to Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend, original Yandex app or account. Do not ship this diagnostic clone as a product build. Do not ask the owner to install/test a new APK or perform repetitive manual steps unless a concrete owner-side measurement is essential. Continue autonomously in large blocks.


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
