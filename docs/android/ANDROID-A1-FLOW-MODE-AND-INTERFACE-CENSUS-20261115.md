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
