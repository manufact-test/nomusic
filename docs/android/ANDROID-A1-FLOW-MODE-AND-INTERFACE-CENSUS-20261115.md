# SUPERSEDING RESULT — 15 Nov 2026, LBK1 / LGK1$a implementation audit (CI GREEN)

**Code checkpoint:** `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**CI:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) **SUCCESS, 85/85 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-lbk1-lgk1-interface-ci-green-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.

## Interface findings

Both owners are defined abstract interfaces in the signed DEX:
- `LBK1`: 3 direct implementers — `LCK1`, `LSV6`, `LXV6`.
- `LGK1$a`: 10 direct implementers — `LHK1`, `LOIa`, `LU44`, `LZQ7`, `Lhe9`, `Lle9`, `LoC6`, `LuV2`, `LvG9`, `LyA8`.

42 exact implementation method traces were captured. Key `LBK1` implementation is `LCK1`:
- `LCK1.break(Track)` passes the same Track to `LUJ5.return(Track): Flow`.
- `LCK1.for(Track)` constructs `LCK1$a(Track, Continuation)`.
- `LCK1.new(Track)` constructs `LCK1$c(LC3a, Track)`.
- `LCK1.try(Track)` constructs `LCK1$l(LD3a, Track)`.
- `LCK1.this(Track)` passes the same Track to `LHv4.if(Track): boolean`.
`LXV6` is a delegating implementation whose five methods forward to the corresponding `LBK1` method refs. The exact `LSV6` implementation body was not present in the current bounded method trace; inspect its class shape before deciding whether it is abstract/delegating.

For `LGK1$a`, some implementers only forward the Track to generic Kotlin Function1/Function2 callbacks. More concrete callback paths include:
- `Lhe9` / `Lle9`: forward Track to three methods on `LVf9`.
- `LoC6`: forwards Track to `LLB6` methods.
- `LvG9`: forwards Track to `LpG9` methods.
These callback paths are secondary to the `LCK1` Flow/coroutine path unless the latter closes.

No field names or values were emitted. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Next bounded investigation

Prioritize the exact `LCK1` path:
1. Trace `LUJ5.return(Track): Flow` and `LHv4.if(Track): boolean`.
2. Inspect exact constructors `LCK1$a(Track, Continuation)`, `LCK1$c(LC3a, Track)`, `LCK1$l(LD3a, Track)`. Derive the exact Track-typed fields written from each original Track parameter and trace only reads of those exact fields in methods owned by those classes.
3. Follow only same-Track calls from those exact coroutine bodies toward a source descriptor, player or decoder boundary.
4. Check `LSV6` flags/superclass and do not fan out into all callback implementers unless the LCK1 path is closed.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LBK1 / LGK1$a implementation audit

**Code under CI:** `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**Last green signed-DEX audit:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) SUCCESS, 84/84 tests, 16 signed splits / 6 DEX.  
**Current CI:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) — parser/static tests SUCCESS; exact signed-DEX inspection in progress.  
**Pre-result code backup:** `backup/android-a1-lbk1-lgk1-implementation-audit-test-correction-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**Last green code backup:** `backup/android-a1-ljk1-exact-field-ci-green-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.

## Confirmed chain

- `LOW6.<init>` stores the exact Track and passes it to `LTv9.if`.
- `LTv9.if` passes the same Track to `LJK1.<init>`.
- `LJK1.<init>` stores the same Track in exactly one Track-typed field on `this`.
- Four `LJK1` methods read that exact field and pass the same Track to four `LGK1$a` methods:
  - `try(Context, Track)`
  - `case(Track)`
  - `else(Track)`
  - `goto(Track)`
- `LJK1.<init>` also passes the Track to four `LBK1` method refs returning Flow: `try(Track)`, `this(Track)`, `for(Track)`, `new(Track)`. The additional `LBK1.break(Track)` reference comes from `LOW6`.
- These `LBK1` and `LGK1$a` concrete method refs are now the only next focus.

## Current audit scope

The current commit adds:
- exact interface/abstract-class profiles for `LBK1` and `LGK1$a`;
- direct implementers or direct subclasses, plus their in-repository superclass method owners;
- exact concrete method traces only for the known five `LBK1` Track-to-Flow contracts and four `LGK1$a` Track callback contracts.

The method scan does not expand to unrelated methods/classes. Field names/values, media, URLs and account state are not emitted. CI parser/static tests passed; exact signed-DEX result is still pending.

## Next action after CI #43742534368

Read the interface owner map and exact implementation traces:
- If concrete implementations pass the same Track to a player/source/decoder boundary, follow only that exact edge.
- If an interface/abstract class has no in-signed-Dex implementation, trace only the exact constructor callsite that supplies that interface object, if necessary; do not fan out to unrelated implementers.
- If no direct same-Track path reaches player/source/decoder, close that branch and report the exact boundary.
- Keep `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false` until direct proof exists.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LJK1 exact field + LBK1 handoffs (CI GREEN)

**Code checkpoint:** `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**CI:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) **SUCCESS, 84/84 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-ljk1-exact-field-ci-green-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Pre-CI retry backup:** `backup/android-a1-ljk1-exact-field-and-lbk1-handoffs-ci-retry-20261115` @ same code SHA.

## New signed-DEX findings

- `LJK1.<init>` stores the incoming Track parameter into exactly one Track-typed instance field on `this`.
- Four methods owned by `LJK1` read that exact same field on `this`: `break()`, `case()`, `if()`, `new()`.
- Those methods pass the exact field-read Track reference onward to `LGK1$a`:
  - `try(Context, Track)`
  - `case(Track)`
  - `else(Track)`
  - `goto(Track)`
- `LJK1.<init>` itself also passes the original Track parameter to four `LBK1` method references returning Flow: `try(Track)`, `this(Track)`, `for(Track)`, `new(Track)`.
- All five observed `LBK1` references in scope are unresolved as concrete method bodies in the pinned DEX (including `break(Track)` from `LOW6`). `LSV6.else` and `LSW6.if` are also unresolved. Do not infer their behavior.

No field names or values were emitted. These are static identity-preserving handoffs only; active selected playback and same-native-item-to-decoder are still not proven.

## Next bounded investigation

Inspect the exact contracts and direct implementers for `LBK1` and `LGK1$a`:
1. Establish whether each owner is an interface/abstract class and enumerate only its direct implementers.
2. For the four exact `LGK1$a` method signatures and four exact `LBK1` Track-to-Flow signatures, inspect only concrete implementations on those implementers (including superclass implementations where needed).
3. Trace the same Track parameter into an exact player/source/decoder boundary. If the interface has no concrete implementation in the signed DEX, record that as a closed boundary and do not fan out into unrelated classes.
4. Keep runtime and decoder gates false until the same native item is directly linked to the active player/source/decoder path.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT CHECKPOINT — 15 Nov 2026, LJK1 exact Track field + LBK1 recipients

**Code under CI:** `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Prior CI-green:** [#43740768063](https://github.com/manufact-test/nomusic/actions/runs/43740768063) SUCCESS, 81/81 tests; exact publisher-signed 2025 original 16 splits / 6 DEX.  
**Current CI:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) — parser/static tests SUCCESS; exact signed-DEX inspection in progress.  
**Pre-CI code backup:** `backup/android-a1-ljk1-exact-field-and-lbk1-handoffs-ci-retry-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Previous green code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Confirmed chain before current CI

`LOW6.<init>(..., Track, ...)` stores the exact incoming Track and passes it to `LTv9.if(..., Track, boolean)`. The defined `LTv9.if` passes that same Track reference to `LJK1.<init>(..., Track, boolean)`.

CI #120 confirmed `LJK1.<init>` stores the exact Track parameter into a Track-typed field on `this`, then passes the same parameter to four methods on `LBK1`:
- `try(Track): Flow`
- `this(Track): Flow`
- `for(Track): Flow`
- `new(Track): Flow`

The current audit adds only those four exact method references to the bounded focus set and adds an internal exact-field matcher. It derives Track-typed field references stored from the original constructor parameter, then traces only reads of those exact field IDs from methods owned by `LJK1`. Field names and values are not emitted.

CI #121 failed only because the new test file had an escaped line-continuation syntax error. That was corrected in `a4cd352`; CI #122 parser/static tests passed. Do not revert working audit logic because of the prior syntax-only failure.

## Next action after CI #122

1. Read the report from [CI #43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839).
2. If the exact Track field reads are found in LJK1 methods, follow only their same-Track outgoing calls. Separately inspect the four exact LBK1 recipient methods if they are defined in the signed DEX.
3. Follow only an exact same-Track identity edge into a concrete player/source/decoder boundary. If these paths end in Flow construction or unresolved interface methods, close them without expanding to generic APIs or unrelated owners.
4. Keep active selected item and same-native-item-to-decoder gates false unless directly proven.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LJK1 Track continuation

**Previous CI-green code:** `70075818bb9965a98376f4cca30157a10bf746e8`.  
**Previous CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) **SUCCESS, 81/81 tests**, exact original 16 signed splits / 6 DEX.  
**New code HEAD:** `c9f218810392ba19e7c6997ed20ae3e7eaa6d059` — adds only the exact `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)` identity trace and its bounded-scope test.  
**Exact pre-CI backup:** `backup/android-a1-ljk1-constructor-pre-ci-20261115` @ `c9f218810392ba19e7c6997ed20ae3e7eaa6d059`.  
**Last green code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Last confirmed identity chain

`LOW6.<init>(..., Track, ...)` stores the exact incoming Track and passes it to `LTv9.if(..., Track, boolean)`. The defined `LTv9.if` passes the same Track reference to `LJK1.<init>(..., Track, boolean)`.

The other two referenced methods `LSV6.else(Track)` and `LBK1.break(Track)`, as well as the optional `LSW6.if(Track, boolean)`, are not defined in the pinned signed DEX. Do not infer behavior or chase them.

## Current bounded task

The new audit traces only `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`. On CI success:
- inspect whether the exact Track parameter is stored on `this` and whether it is passed unchanged to a concrete player/source/decoder boundary;
- if stored, trace only reads of that exact field from methods on `LJK1`, without disclosing its field name or value;
- if no relevant identity edge exists, close this branch rather than expanding into generic player APIs/Flow.

The latest code commit is not yet CI-verified at this handoff. No runtime hooks, APK, login, account/media access or vendor behavior change. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LOW6 recipient trace (CI GREEN)

**Code checkpoint:** `70075818bb9965a98376f4cca30157a10bf746e8`  
**CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) **SUCCESS, 81/81 tests**; exact pinned publisher-signed original verified (16 splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Signed-DEX findings

From `LOW6.<init>(..., Track, ...)`, the same exact incoming Track reference is:
- stored in a Track-typed instance field on `this`;
- passed to `LTv9.if(..., Track, boolean)`;
- passed to method references `LSV6.else(Track)` and `LBK1.break(Track)`.

The pinned signed DEX defines `LTv9.if`, but does **not** define the referenced `LSV6.else`, `LBK1.break`, or `LSW6.if` methods. Those unresolved refs are closed as implementation candidates; do not infer their behavior.

Inside the defined `LTv9.if`, the same Track parameter is passed to:
`LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`.

This is an exact local object-identity edge, not proof that the object is the active selected player item. The return from `LTv9.if` is `LJK1`; no decoder/source/audio boundary was reached in this bounded trace.

## Exact next hop

Inspect only `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`:
1. Verify whether the exact Track parameter is stored on `this` and/or passed unchanged to a concrete player/source/decoder method.
2. If stored, identify its field internally without exposing field name/value and trace only reads of that exact field from `LJK1` methods.
3. If no relevant outgoing identity edge exists, close this path; do not expand to generic player APIs or Flow implementers.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. Stage A NAV17 remains owner-confirmed PASS. Stage B replacement remains NOT CONNECTED / NO-GO. No release APK, runtime hook, login or media access.

---

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
