# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 15 November 2026  
**Repository:** manufact-test/nomusic  
**Current status:** **Stage A = PASS (NAV17 owner verification); Stage B = IN PROGRESS.** Research-only. CELIKOM replacement source is not connected; this is not a release build.

## Current CI-green code and exact next scope — 15 Nov 2026

**Active branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. **Latest CI-green code:** `3f6f9d7ed43e782dc9ab63a72531614e70c6cdb8`. [CI #43734257845](https://github.com/manufact-test/nomusic/actions/runs/43734257845) **SUCCESS 72/72**; original 16 signed splits / 6 DEX, 254,355 methods scanned. **Exact backup:** `backup/android-a1-coroutine-upstream-direct-census-ci-green-20261115`. Read `docs/android/ANDROID-A1-TRACK-COROUTINE-CALLER-IDENTITY-20261115.md` (latest upstream-entry section) before coding.

The exact inbound census found **3 direct upstream references**: `LDp0$a.invokeSuspend -> LDp0.if`, `LDp0.emit -> LDp0.if`, `Lwp0$a$a.invokeSuspend -> Lwp0$a.emit`. These are Flow/coroutine forwarding or resume paths; no direct player-selection identity was established. The **next specific task** is to identify the Flow producer and collector/virtual dispatch into these entry methods and connect it to the **active selected Track**, then join that identity to the previously audited decoder buffer -> audio sink. Do not continue exploring generic coroutine wrappers or claim a player-selection link from method names/types. `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`. **Stage A NAV17 PASS (owner verified); Stage B NO-GO for replacement. No APK, runtime hook or CELIKOM source switched.**

## Prior signed Track / coroutine checkpoint (supersedes renderer-only headline)

Read `docs/android/ANDROID-A1-TRACK-COROUTINE-CALLER-IDENTITY-20261115.md` first. **Last CI-green code** `0de0e4278977f5821ad1de6b0ca879bfa7d110e6`; [CI #43733450288](https://github.com/manufact-test/nomusic/actions/runs/43733450288) **SUCCESS 71/71**, 16 signed splits / 6 DEX, all 254,355 methods covered by caller census. Backup `backup/android-a1-continuation-hierarchy-ci-green-20261115`. Exact direct caller census of `LGp0.new`: `LDp0.if` passes the identical Track argument; `Lwp0$a.emit` passes its Object argument after Track cast; `LFp0.invokeSuspend` passes its `this` continuation with explicit Track=null. The two newly allocated entry continuations `LDp0$a` and `Lwp0$a$a` both inherit `LOe2 -> LZA0 -> Object`. **Do not equate a typed/captured Track with active playback**: `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`, resume binding and exact newly allocated constructor capture remain unproven. Continue upstream into selected-item/player identity, then join the previously audited ByteBuffer sink. No new runtime hooks, APK, download, replacement switch or production change. **Stage A NAV17 owner-verified PASS; Stage B research-only, not a release.**

## Latest renderer writer checkpoint (supersedes older research summaries)

Read `docs/android/ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md` before choosing a new hook or rerunning investigations. Signed audit [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS, **49/49 tests**, at `cfd02607829ef854065331571654c94bef5005ba`; exact backup `backup/android-a1-renderer-field-writer-census-ci-green-20261115`. Three typed ByteBuffer fields feed seven exact writer methods. `LcC0.n` / `Lkd6.n` contain `Lad6.final(I)ByteBuffer` → field-write candidates; the same declared fields are read toward virtual audio sink calls. Branches and other writes prevent claiming same runtime object/active selected track. **Stage A NAV17 is owner-confirmed PASS; Stage B has no CELIKOM audio yet.** All selected Track, Album, edition/generation and native decoder linkage gates remain false. No new runtime hook/APK. Ignore historical 'Stage A NO-GO' notes lower in this document: they belong to the pre-NAV17 research epoch.

## Active Git state

- **Only active working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- **Latest CI-green code checkpoint:** `cfd02607829ef854065331571654c94bef5005ba`
- **Latest docs handoff:** current working-branch HEAD; final handoff backup branch is `backup/android-a1-stage-b-audio-sink-audit-final-handoff-20261115`.
- **Static audit CI:** [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS; 49/49 tests; exact cross-method renderer ByteBuffer field writers verified as static candidates only.
- **Exact CI-green code backup:** `backup/android-a1-renderer-field-writer-census-ci-green-20261115` @ `cfd02607829ef854065331571654c94bef5005ba` (prior AudioTrack checkpoint `a9dfbbbc` and its backup retained).
- **Pre-fix rollback:** `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`
- **NAV17 owner-known-good baseline:** `backup/android-a1-nav17-owner-real-userinfo-main-music-audible-20261114` @ `d4c0887028b2bfbad7ed59f63ec88a4770f3595d`
- **Last runtime Java hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; unchanged by this static-audit pass.

**Status clarification:** Any older “Stage A = NO-GO” snapshot below refers to a pre-NAV17 checkpoint and is superseded by the owner-verified NAV17 result. Stage A here means the real owner Passport → userinfo → native Yandex Music UI/original playback path. Stage B means CELIKOM replacement source selection and is still incomplete.

## Current Stage B evidence

### Superseding technical checkpoint — 15 Nov 2026 (AudioTrack / ByteBuffer)

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 opened the owner's real Yandex Music account, showed albums and My Wave, and played original Yandex tracks on the handset. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

- Static audit code: `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Audit CI: [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) **SUCCESS**, 40/40 focused tests; verdict `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.
- Exact CI-green code backup: `backup/android-a1-audio-buffer-identity-ci-green-20261115` @ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Pre-fix rollback: `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`.
- Last runtime Java hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. This pass changed only the read-only static audit and its tests; no runtime hook, APK, account, phone or production component changed.

### Exact signed-DEX findings

- `LbJ2` implements `Lpk0` and declares typed `AudioTrack` and `ByteBuffer` fields. Its method named `native(ByteBuffer, long, int)` is the concrete ByteBuffer entry candidate; the same owner also exposes the AudioTrack construction/control path (`play`, `pause`, `flush`, AudioTrack factory methods).
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


## What is actually done

1. Added read-only Album identity capture at the two signed Track constructors that each have exactly one Album parameter. The hook calls the original constructor once, then associates the resulting Track object with that Album argument by Java reference identity.
2. Added a read-only hook on the exact Track copy method. It calls the original method once, then associates its returned Track object with the Album argument.
3. StageBAudioEvidence carries weak Track/Album references and compares with Java ==. The Track map is bounded to 32 entries; source lineage to 16. Conflicting Track→Album associations revoke the Album link.
4. Album identity can be followed through Track Flow → wrapper → descriptor → factory → DataSource instance → successful open() → positive read(). A read is linked only to the same source and lineage after successful open. Failed reopen and close revoke open proof. Read-path inspection is capped at 256 callbacks per source/reopen window.
5. Static signed-DEX audit and regression tests were extended to report Track/Album constructor and copy-method shapes without making an audio/current-track claim.

## Verified CI — exact scope

- [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**. One Album-typed field on Track; two constructors accept Album but direct same-argument write to Track's own field is **not proven**. One Track+Album→Track copy-method candidate; it reads source Track's Album field, passes the Album argument to a Track constructor and returns a Track. The audit does **not** prove the Album argument is stored on the returned Track. Current selected item is not proven.
- [Clone-only ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations; both Album hooks and all Track/Exo hooks registered. Publisher intentionally absent in this control.
- [Publisher-first ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original publisher 16/16 splits installed, clone co-installed, original remains installed, 25/25 stable observations, no Metrica fatal suppression. Both Album hooks and all Track/Exo hooks registered.
- All three are lab/CI results only. No owner phone was touched. No audio playback or account test was performed. No product APK was published.
- Final publisher-first verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO. stage_a=NO_GO; stage_b_current_player_album_edition_attested=false; audio_or_account_tested=false.



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

## Read these documents first

1. docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md — focused technical handoff.
2. docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md — exact static findings and Album identity observer.
3. docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md — fail-closed Exo source lifecycle.
4. Historical accumulated notes remain in Git history before this documentation cleanup; they are not the current task list.

## Next task — continue, do not restart

The next developer must continue in the existing branch and prove, using signed DEX analysis and read-only identity hooks:

1. Which Track object is the **current selected player item**, distinguishing it from queue, prefetch and download work.
2. Which exact edition/generation object belongs to that selected Track/Album.
3. Whether that same identity reaches the actual decoder input/audio renderer, not merely an Exo DataSource read.

Track Flow and positive DataSource reads are not proof of current audible playback. Do not infer edition semantics from obfuscated names or types. Do not mark Stage A ready until current Track + Album + edition + decoder identity and actual audio are demonstrated.

## Hard constraints

- Do not change the agreed A1 architecture, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend, or original Yandex app/account.
- Keep this work read-only and fail-closed. Every vendor method must execute exactly once and unchanged; no fatal suppression.
- Do not create or deliver a product/release APK from this lab work.
- Do not ask the owner to install anything or perform manual multi-step diagnostics unless a specific owner-side measurement becomes genuinely necessary.
- Work in large coherent blocks. Avoid unnecessary status reports and one-click-at-a-time instructions.
- If the owner sends a diagnostics file, inspect the nine Album counters together with Track/Exo open/read/close counters. Distinguish hook registration, no observations, identity conflict and scan exhaustion.
