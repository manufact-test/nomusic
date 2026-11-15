# SUPERSEDING RESULT — LaC7 / LCK1 bounded caller audit, CI #144

- The broad LaC7 interface census produced many unrelated callers; it is now explicitly superseded and must not be repeated.
- The only relevant callsites in the selected LCK1 path are \`LCK1$c$a.emit\` and \`LCK1$h$a.emit\`, each calling \`LaC7.if(): Track\`.
- For both exact callsites, receiver identity remains unresolved across the branch boundary. No exact receiver-field read matched a constructor store from a LaC7 parameter.
- \`LzA9.if()LaC7;\` is a common return-origin at 26 unrelated callsites, but no code-bearing definition was found under that exact signature. It is not evidence that the returned implementation is \`LyEa\`.
- Next: inspect only the two exact LCK1 emit methods, their exact constructors/field refs, and \`LzA9.if\` only if those constructors directly reach it.

CI #144 SUCCESS, 97/97. Code checkpoint \`592ed5c2aa162bfb7e7ef659fbe6d0146703d461\`; backup \`backup/android-a1-lya-exact-field-lck1-receiver-ci-green-20261115\`. No runtime hooks or playback behavior changed.

# SUPERSEDING RESULT — LaC7 owner resolution, 15 Nov 2026

**Repository:** `manufact-test/nomusic`  
**Working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `f860ab79d98bda49469a5ce7f9a4d4005c7976b2`  
**CI:** [#43747724142](https://github.com/manufact-test/nomusic/actions/runs/43747724142) — SUCCESS, 91/91 tests; exact issuer-signed 2025 original, six DEX inspected read-only.  
**Exact green backup:** `backup/android-a1-lac7-owner-audit-ci-green-20261115` @ `f860ab79d98bda49469a5ce7f9a4d4005c7976b2`.  
**Runtime hooks:** unchanged; no APK built, patched, or released.

## LaC7 result

- `LaC7;` is defined in the signed DEX as an abstract interface.
- It has 8 direct implementers and no direct subclasses: `LIz4;`, `LOG8;`, `LWo4;`, `LaC7$a;`, `LbC9;`, `Lc6b;`, `LyEa;`, `Lyw9;`.
- Seven concrete `if(): Track` method bodies were found in the scoped implementers/ancestry.
- Only `LyEa.if(): Track` produced a typed identity trace: it reads a Track-typed field from `this` and returns that same object.
- `LyEa` has a Track-typed field, but its owner profile does not establish Player, MediaSource, decoder, or active-playback ownership.
- No runtime dispatch from the LCK1 callsite to `LyEa` is proven. The other six method bodies produced no typed Track identity event in this tracer; do not infer their return source from that absence.

**Gates remain:** `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`, `runtime_dispatch_proven=false`. This is a candidate only, not a Stage B success.

## Next bounded task — LyEa only

1. Inspect the exact `LyEa` constructor(s) accepting Track and prove whether the same Track parameter is stored into the field later returned by `LyEa.if()`. Keep field names and values out of the report.
2. Find only direct `new-instance LyEa` / constructor callsites. Trace the Track argument's object identity to its immediate origin and classify the owner by exact type/field/call contracts.
3. Inspect the exact LCK1 callsite to `LaC7.if(): Track`. Determine whether its receiver can be proven to be the same `LyEa` object. A class implementing the interface is not proof of runtime dispatch.
4. If the LyEa instance and Track cannot be tied to the active selected item, close this route as an unproven candidate and return to the already documented bounded audio-sink caller audit. Do not broaden to all eight implementations again.

## After closing LyEa

Continue from the existing native sink path: callers of `LcLb.O` and `Lbd6.O`; distinguish active playback from queue/prefetch/download; connect Track/Album to the sink only through bounded Java object identity; establish edition/generation for that same item; then prove the same identity at decoder/audio renderer. Only after that may the existing CELIKOM resolve/entitlement contract be connected before decoder input with the original native fallback.

## Unchanged hard constraints

Read-only and fail-closed. No generic runtime hooks, APK changes/builds/releases, login, account/media access, field values, Track/Album names or IDs, URLs, DataSpec, tokens, or audio bytes. No vendor method behavior changes or exception suppression. Do not touch NAV17, original Yandex, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB, or production. Do not request owner action unless a concrete necessary read-only measurement is first identified.

---

# CURRENT RESTORE POINT — 15 Nov 2026, CELIKOM Android A1

**Repository:** `manufact-test/nomusic`  
**Only working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Branch HEAD before this documentation update:** `e159fc02ad4b746647d417b065daa5791cdcf315` (three documentation-only commits ahead of the code checkpoint below; no code changes after the green audit).  
**Latest code checkpoint:** `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**Exact green code backup:** `backup/android-a1-lck1-predicate-audit-ci-green-20261115` @ `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**Latest CI:** [#43745289143](https://github.com/manufact-test/nomusic/actions/runs/43745289143) — SUCCESS, 88/88 tests; exact publisher-signed 2025 original, 16 splits / 6 DEX.  
**Last runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; subsequent work was read-only static audit and documentation.

## Product status — preserve these boundaries

- **Stage A = PASS on NAV17:** owner confirmed real Yandex account, albums, My Wave and original-track playback. This success must not be disturbed.
- **Stage B = NOT CONNECTED / NO-GO:** CELIKOM replacement audio is not connected or audible. No release APK from this research branch.
- Gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Latest LCK1 result

- `Lv3.throws(Track, Track)` delegates to `Objects.equals`; close it as a pure equality predicate.
- `LwEa.for(Track)` contains only the Kotlin non-null parameter check.
- `LHv4.if(Track)` was already bounded to parameter validation only.
- Neither inner coroutine proves passing the original field-backed Track to `LHl4.emit`.
- `LaC7.if(): Track` is the only remaining narrow reference: it supplies a second Track for comparison, but its exact owner/method resolution is not yet established.

## Next bounded task — do only this

1. Inspect the exact signed-DEX owner `LaC7;`: defined or absent, interface/class, abstract or concrete, superclass and interfaces.
2. If the exact `if(): Track` body is absent/abstract/inherited, enumerate only direct implementers or subclasses and trace only concrete implementations of that exact signature (including the nearest inherited method owner where needed).
3. Determine whether the returned Track is structurally sourced from player/current-source/decoder state. Do not infer this from names or type similarity.
4. If no concrete implementation exists in the pinned signed DEX, close this path as external/unresolved and return to the previously identified native audio sink caller path. Do not reopen closed LCK1 predicates or generic Flow collectors.

## After closing LaC7

Resume only the existing bounded audio-sink route: callers into `LcLb.O` and `Lbd6.O`; distinguish active playback from queue/prefetch/download; connect Track/Album to the sink only by bounded Java object identity; establish edition/generation for that same item; require the same identity at decoder/audio renderer. Only after that may the existing CELIKOM resolve/entitlement contract be connected before decoder input, with the original native fallback.

## Hard constraints

Read-only and fail-closed until the chain is proven. No generic runtime hooks, APK changes/builds/releases, login, account/media access, field-value/ID/name/URL/DataSpec/token/audio-byte reads, vendor behavior changes, or exception suppression. Do not touch NAV17, original Yandex, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB or production. Do not ask the owner for manual steps unless a concrete, necessary read-only measurement has first been identified. Work in large bounded blocks and preserve exact backups.

---

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
