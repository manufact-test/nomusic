# SUPERSEDING RESULT — 15 Nov 2026, LCK1 predicate/secondary Track source audit (CI GREEN)

**Code checkpoint:** `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**CI:** [#43745289143](https://github.com/manufact-test/nomusic/actions/runs/43745289143) **SUCCESS, 88/88 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green backup:** `backup/android-a1-lck1-predicate-audit-ci-green-20261115` @ `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.

## Predicate results

- `Lv3.throws(Track, Track): boolean` delegates directly to `java.util.Objects.equals(Object, Object)`. This is a pure equality check; close it as a player/source/decoder path.
- `LwEa.for(Track): boolean` has only the Kotlin non-null parameter check in its body; no outgoing Track call edge.
- `LHv4.if(Track): boolean` likewise had only parameter validation in the prior bounded trace.
- `LaC7.if(): Track` is referenced by `LCK1$c$a.emit` as the source of a second Track compared against the exact retained Track, but the exact method reference is unresolved in the pinned signed DEX. Do not infer its behavior.

The branch-sensitive trace still proves that neither inner coroutine passes the original field-backed Track to `LHl4.emit(Object, Continuation)`.

## Next bounded task

Inspect only the exact owner `LaC7;`:
1. Establish whether the owner is defined in the signed DEX and whether it is an interface/abstract class.
2. If the exact `if(): Track` method is abstract/unresolved, enumerate only direct implementers/subclasses and trace concrete implementations of that exact signature.
3. Determine whether the returned Track is sourced from a player/source/decoder state. If no implementation exists in the signed DEX, close this handoff as external/unresolved.
4. Do not reopen the equality predicate or generic Flow collector branches.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, branch-sensitive inner Flow identity trace (CI GREEN)

**Verified code checkpoint:** `79e3399dd65806c4017f0077f406fdf0ef0b1265`.  
**CI:** [#43744778789](https://github.com/manufact-test/nomusic/actions/runs/43744778789) **SUCCESS, 88/88 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green backup:** `backup/android-a1-inner-flow-cfg-track-identity-ci-green-20261115` @ `79e3399dd65806c4017f0077f406fdf0ef0b1265`.  
**Previous green:** [#43744526981](https://github.com/manufact-test/nomusic/actions/runs/43744526981) SUCCESS, 87/87 tests; primitive argument false-positive guard verified.

## Branch-sensitive result

A bounded control-flow must-alias trace followed the exact Track field through all incoming branch states in the two inner Flow lambdas.

- `LCK1$c$a.emit`: reads the exact retained Track field; calls `Lv3.throws(Track, Track): boolean` with the field-backed Track as one argument. A separate `LaC7.if(): Track` call returns another Track. The subsequent `LHl4.emit(Object, Continuation)` call does **not** receive a proven alias of the original field-backed Track.
- `LCK1$l$a.emit`: reads the exact retained Track field; passes it to `LHv4.if(Track): boolean` and `LwEa.for(Track): boolean`. The subsequent `LHl4.emit(Object, Continuation)` call does **not** receive a proven alias of the original field-backed Track.

Thus neither inner coroutine proves emission of the original Track into the Flow collector. This branch is a predicate/filter path, not a proven player/source/decoder handoff. Do not describe it as playback or infer the collector's emitted value.

The audit now preserves aliases across branches only when the same exact origin is present on every incoming path. It rejects the proof if even one branch overwrites the register. Primitive DEX parameters are also excluded from object-identity evidence.

## Next bounded task

Inspect only:
- `LaC7.if(): Track` — exact source of the second Track returned in the LCK1$c$a predicate path;
- `Lv3.throws(Track, Track): boolean`;
- `LwEa.for(Track): boolean`.

`LHv4.if(Track)` was already traced and had no further same-Track call edge beyond parameter validation. If the three remaining methods only compare/filter Track metadata and do not reach a player/source/decoder boundary, close this entire LCK1 Flow branch and return to the previously identified native audio-output buffer path. Do not expand into generic Flow collectors or unrelated classes.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LCK1 Flow/coroutine field audit (CI GREEN)

**Code checkpoint:** `066778008331584301731f9d430a6713a0e7a02d`.  
**CI:** [#43743305204](https://github.com/manufact-test/nomusic/actions/runs/43743305204) **SUCCESS, 86/86 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-lck1-coroutine-field-audit-ci-green-20261115` @ `066778008331584301731f9d430a6713a0e7a02d`.  
**Previous audit-only run:** [#43743253472](https://github.com/manufact-test/nomusic/actions/runs/43743253472) SUCCESS, 85/85 tests.

## Exact Track field results

Each of these constructors stores the exact incoming Track into exactly one Track-typed field on `this`:
- `LJK1.<init>`: 1 field store; 4 methods read the exact field.
- `LCK1$a.<init>(Track, Continuation)`: 1 field store; 2 methods read the exact field.
- `LCK1$c.<init>(LC3a, Track)`: 1 field store; 1 method reads the exact field.
- `LCK1$l.<init>(LD3a, Track)`: 1 field store; 1 method reads the exact field.

Key exact same-Track outgoing edges:
- `LCK1$c.collect()` reads its exact Track field and passes that Track into `LCK1$c$a.<init>(LHl4, Track)`.
- `LCK1$l.collect()` reads its exact Track field and passes that Track into `LCK1$l$a.<init>(LHl4, Track)`.
- `LCK1$a.invokeSuspend()` passes the Track into `AbstractMap.containsKey(Object)`; this is a map-membership/filter candidate, not a player/source/decoder edge.
- `LUJ5.return(Track)` and `LHv4.if(Track)` expose no further Track-identity method handoff in the bounded trace (only parameter validation); do not chase them without new evidence.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Next bounded task

Trace only the two inner coroutine constructors:
- `LCK1$c$a.<init>(LHl4, Track)`
- `LCK1$l$a.<init>(LHl4, Track)`

Derive their exact Track field stores from the original Track parameter and scan only methods owned by those exact inner classes for reads of those exact field identities. Follow same-Track calls only toward Flow emission, source descriptor, player or decoder boundaries. Do not expand into generic Flow collectors or unrelated coroutine classes.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LCK1 Flow/coroutine Track path

**Code under CI:** `066778008331584301731f9d430a6713a0e7a02d`.  
**Prior green interface audit:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) SUCCESS, 85/85 tests, 16 signed splits / 6 DEX.  
**Current CI:** [#43743305204](https://github.com/manufact-test/nomusic/actions/runs/43743305204) — static tests/install phase; signed-DEX scan pending.  
**Previous code-only CI:** [#43743253472](https://github.com/manufact-test/nomusic/actions/runs/43743253472) — same implementation before the extra scope regression test; signed-DEX scan in progress.  
**Pre-CI backup:** `backup/android-a1-lck1-flow-coroutine-field-audit-pre-ci-20261115` @ `066778008331584301731f9d430a6713a0e7a02d`.  
**Previous green backup:** `backup/android-a1-lbk1-lgk1-interface-ci-green-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.

## Confirmed interface handoff

Both `LBK1` and `LGK1$a` are abstract interfaces in the signed original. `LBK1` has direct implementers `LCK1`, `LSV6`, `LXV6`; `LGK1$a` has 10 direct implementers. 42 exact method traces were captured.

The primary `LCK1` methods pass the same Track into:
- `LUJ5.return(Track): Flow`
- `LCK1$a.<init>(Track, Continuation)`
- `LCK1$c.<init>(LC3a, Track)`
- `LCK1$l.<init>(LD3a, Track)`
- `LHv4.if(Track): boolean`

`LXV6` delegates its five methods back to the `LBK1` interface refs. `LSV6` is a direct implementer but its exact concrete method bodies were not found in the prior bounded trace; the current owner profile output now includes its abstract/interface/superclass shape.

## Current bounded scope

The current code traces only the five exact LCK1 outgoing method refs and derives Track-typed fields written from the exact original Track parameter in constructors of `LJK1`, `LCK1$a`, `LCK1$c`, `LCK1$l`. It then scans only methods owned by those four classes for reads of those exact field identities. No field names/values are disclosed.

Next, read the report for:
- `LUJ5.return` and `LHv4.if` traces;
- constructor field-store counts and exact field-read method traces for each of the three LCK1 coroutine classes;
- `LSV6` implementer class shape.

If a coroutine reads the exact Track field and passes it to a concrete source/player/decoder boundary, follow only that edge. If it reaches only generic Flow construction, trace only the exact continuation/coroutine method that carries the same Track. Do not expand into unrelated implementers or generic player APIs.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

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
