# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 15 November 2026  
**Repository:** manufact-test/nomusic  
**Status:** research-only, read-only native identity work. **NOT a product build. Stage A = NO-GO.**

## Active Git state

- **Only active branch:** experiment/android-a1-metrica-init-state-observer-arm13-20261112
- **Latest code + static-audit checkpoint:** 8eb2e6a3bc61643219ddc2e261853f8a3bd4865f
- **Last runtime Java hook change:** a655712d210189f3bc611847235de3ed4d985c1a (unchanged by the new static audits)
- Current branch HEAD may advance with documentation commits; use the code checkpoint above for the audited code.
- **Latest static-audit CI-green backup:** backup/android-a1-track-return-callsite-ci-green-20261115 @ 8eb2e6a3bc61643219ddc2e261853f8a3bd4865f
- **Prior runtime/Album CI-green backup:** backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb
- **Pre-large-push rollback:** backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5
- Final docs/code backup branch: backup/android-a1-track-album-final-handoff-20261115-v2.

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
