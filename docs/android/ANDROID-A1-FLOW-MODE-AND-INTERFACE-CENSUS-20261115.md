# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LOW6 direct Track recipients

**Latest committed code:** `70075818bb9965a98376f4cca30157a10bf746e8`.  
**Previous CI-green signed-DEX result:** [#43739559516](https://github.com/manufact-test/nomusic/actions/runs/43739559516) SUCCESS, 80/80 tests; exact original verified (16 signed splits / 6 DEX).  
**Current audit CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) — in progress; this commit adds a single bounded hop from the exact Track handoffs observed in `LOW6.<init>`.  
**Intermediate audit run:** [#43740249574](https://github.com/manufact-test/nomusic/actions/runs/43740249574) was triggered by the parser-only commit immediately before the test-scope commit; prefer final result of #43740254479.  
**Exact code backup before this audit:** `backup/android-a1-low6-track-identity-pre-ci-20261115` @ `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Latest in-progress code backup:** `backup/android-a1-low6-direct-recipient-audit-pending-ci-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Confirmed result from CI #118

The signed-DEX report established that `LOW6.<init>(..., Track, ...)`:
- stores the exact incoming Track parameter into a Track-typed instance field on `this`;
- passes that same Track reference to `LTv9.if(..., Track, boolean)`;
- passes that same Track reference to `LSV6.else(Track)`;
- passes that same Track reference to `LBK1.break(Track)`, whose declared return type is a Flow interface.

No field names or values were disclosed. The optional `LSW6.if(Track, boolean)` reference was not defined in the pinned signed DEX; do not infer it exists or use it as evidence.

These are exact local object-identity edges only. They do **not** prove active selected playback, player dispatch, decoder input or same-item audio output. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Current bounded audit scope

The latest audit adds exact identity traces only for:
- `LTv9.if(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`
- `LSV6.else(Track)`
- `LBK1.break(Track)`

A regression test pins this exact five-entry focus set (including the optional unresolved LSW6 candidate and LOW6 constructor) so the audit cannot silently expand to generic callsites.

**Next action:** wait for CI #43740254479. On success, inspect only these three method traces. Follow only an exact same-Track call to a concrete player/source/decoder boundary. If no such call is present, close that recipient path and do not fan out into generic Flow or unrelated owners. On failure, retain the prior green checkpoint `70495580` and diagnose only the failing test/audit.

No runtime hooks, APKs, original Yandex/account/media access, or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS. Stage B replacement remains NOT CONNECTED / NO-GO.

---

# IN-PROGRESS CHECKPOINT — 15 Nov 2026, LSW6 / LOW6 identity trace

**Latest CI-green code:** `b250aba2ca5e7555995099683736be572f0ef578`, CI [#43738914218](https://github.com/manufact-test/nomusic/actions/runs/43738914218) SUCCESS, 80/80.  
**Current research HEAD:** `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Current CI:** [#43739559516](https://github.com/manufact-test/nomusic/actions/runs/43739559516) — still in progress at handoff.  
**Pre-CI code backup:** `backup/android-a1-low6-track-identity-pre-ci-20261115` @ `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Last fully documented CI-green handoff:** `backup/android-a1-ldt0-track-final-handoff-20261115`.

The only code change after the last green checkpoint adds read-only exact identity traces for:
- `LSW6.if(Track, boolean)`
- `LOW6.<init>(..., Track, ...)`

No runtime hook, APK, original app, account or media behavior was changed. The 80 local tests completed successfully before the signed-DEX scan began; the full signed-DEX scan has not yet reported its final result.

**Next action:** check CI #43739559516 to completion and inspect only `selected_track_path_identity_traces` plus `selected_track_path_missing_method_refs`. Do not start another broad audit. If the run fails, preserve the CI-green `b250aba2` checkpoint and diagnose only the failure. If it succeeds, decide from the exact Track identity events whether either method reaches a player/source/decoder boundary; then update this handoff with the result.

All gates remain false until proven: `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`. Stage A NAV17 remains owner-confirmed PASS; Stage B replacement is NOT CONNECTED / NO-GO. No release APK.

---

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

# Android A1 — Flow mode and interface census (15 Nov 2026)

**Repository:** `manufact-test/nomusic`  
**Active branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`  
**CI:** [#43737913160](https://github.com/manufact-test/nomusic/actions/runs/43737913160) — **SUCCESS, 80/80 focused tests**  
**Exact code backup:** `backup/android-a1-flow-mode-branch-audit-ci-green-20261115` @ `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`  
**Scope:** signed-DEX static audit only; no runtime hook, APK, original app, account or media changes.

## Result

The exact pinned publisher-signed Yandex Music 2025.10.4 #120.1gpr package was verified: **16 signed splits / 6 DEX**. The audit remained read-only and returned `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.

This commit changed only:
- `android/native-yandex-hooklab/audit_native_selected_item_handoff.py`
- `android/native-yandex-hooklab/tests/test_audit_native_selected_item_handoff.py`

It adds DEX class interface/abstract flags, exact packed/sparse-switch case-to-target mapping, bounded Flow mode branch census and direct interface-implementer census. It does not change runtime hooks.

## Findings

1. The Flow source classes `LBy4`, `Lvp0`, `Lyp0` and `LzC3` store an integer constructor parameter in their own `default` field. Their `collect()` methods read that field as a switch selector. The audit now records exact switch keys and target blocks. It does **not** evaluate runtime branch predicates, so the selector is not assigned a semantic label such as current playback, queue or prefetch.

2. The direct implementer census confirms the interface hierarchy, but the generic Flow contracts are too broad to identify the active player path: `LGl4` has 698 direct implementers and `LHl4` has 1,735. Interface membership alone is not runtime dispatch evidence.

3. A bounded census found 160 callsites to `Ljm4.for(Flow, CoroutineScope, FlowCollector)`. Exactly one callsite originates in a method whose signature accepts both native Album and Track: `LDT0.<init>(Album, Track, ...)`. The call itself passes a Flow object, not the Track parameter; the Flow argument's derivation from that exact Track is **not proven**. This is the narrowest next candidate and should be inspected before expanding the search.

4. `LzE7.collect()` contains a branch that reads an opaque object field, casts it to Track and constructs a collector wrapper. The branch condition and runtime dispatch are not established. Treat this only as a secondary static candidate, not as the selected song.

5. Previously established Track entry evidence remains unchanged:
   - `LDp0.if` receives the same Track reference as its original Track parameter.
   - `Lwp0$a.emit` receives the same Track reference as its Object parameter after cast.
   - The paths still do not prove that either Track is the active selected player item.
   - The continuation resume/capture relationship is not a runtime identity proof.

## Gates and status

- `active_selected_item_proven=false`
- `same_native_item_to_decoder_proven=false`
- CELIKOM replacement source remains **NOT CONNECTED**.
- NAV17 Stage A remains owner-confirmed **PASS**: native Yandex account/UI and original-track playback were owner-verified. This static audit does not independently verify audio.
- Stage B remains research-only / **NO-GO for replacement**. No release APK is to be produced from this branch.

## Next bounded block — do not broaden

Inspect only `LDT0.<init>` and the exact `Ljm4.for` callsite:

1. Determine whether the Flow argument is derived from the exact Track parameter by bounded register/object identity, or is independent of it.
2. If it is independent, close this candidate and do not chase the other 159 generic Flow factory callsites.
3. If it is derived from the exact Track, follow only one bounded hop to the collector/entry path and classify it as active playback versus queue/prefetch/download. Do not infer selection from the class name or Flow type.
4. Do not add runtime hooks unless this yields a concrete player-state owner and exact method/callsite.

The `LzE7` opaque-field branch is secondary and should be revisited only if the `LDT0` path is negative and the result specifically warrants it.

## Hard constraints

Preserve NAV17, native Yandex auth/original playback, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend and production. No second player, no decoder/audio sink changes, no reading private Track/Album values, IDs, URLs, DataSpec, tokens or audio bytes. Every vendor method must execute exactly once and unchanged. No owner login, OTP, APK install or manual diagnostic request without a concrete, necessary read-only measurement.
