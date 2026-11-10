# CELIKOM Android Native — source.t transaction fence + exact ocv.i0→ero ownership (10 Nov 2026)

**Scope:** new Android native-Yandex one-player research branch only. NOT Test.50, Test.51, old DynamicsProcessing, WebView or two-player workaround. NO customer APK, no root, no publisher app modification, no Play Protect bypass.

## Why this block was needed

The previous in-process observer incorrectly counted `Lemb.t(dmb)` as started **before** forwarding the original invocation to the Yandex host. The original `t()` can still throw, retry, switch tracks, or race with a worker. An async `Lmb4.a` read completion arriving before the original `t()` returns could thus manufacture a false-positive source→reader success. Repeated `t()` on a reused source could count another successful start even when that call failed. This is a correctness defect in a telemetry gate, not a proven audible playback bug.

A second limitation: an `ero` can be constructed from `ocv.i0` directly, without passing through `kvs.A`; a factory-only observer missed that path. Merely seeing an `ero` constructor also could not establish *which `ocv` lifecycle owner* scheduled it.

## Real code changes

- `NativeSourceDispatchWitness` now separates provisional `onLifecycleTBegin` from **confirmed original return** `onLifecycleTFinish(receiver,true/false)`. Pending early reader completion is held in a bounded slot, promoted on normal return only; exception/removal/clock rollback/ambiguous parallel `t()` drops source and deferred data. Reusing the same source counts as `reusedTCalls`, not another successful `matchedCall`.
- `NativeHookEntry` surrounds the **original unmodified** `chain.proceed()` with `try/catch`; successful and throwing returns report distinct outcomes to the same-boundary observer. Neither branch modifies argument/return/source/audio, and the original exception is rethrown without masking.
- `NativeOwnerConstructionWitness` is a new exact Java ThreadLocal frame for a **real executing** `ocv.i0():void`. Only a successful, nested `ero` constructor on the **same thread** yields an exact `(owner,child)` reference pair. Delegating constructor calls for the **same** object are idempotent. A second distinct child, exception, foreign thread, missing child, reentrant mismatch or out-of-frame ctor cannot produce a pair. No names, URI, track ID, audio or secrets are read.
- `HookSpec.findLocvSourceBuilder` pins actual `ocv.i0()V`; `NativeHookEntry` wires that exact reader scope and two exact `ero` constructors, then `NativeSourceDispatchWitness.onOwnerChild(owner,child)` only accepts the two existing **same-reference** lifecycle instances. Final combined counter `parentOwnerReaderCompletions` requires confirmed owner `t()`, source `t()`, source→typed `mb4` reader, and a real nested positive `ha4` read/close from that source.
- The observer **does not identify active Yandex playback or the selected decoder**. A background `ocv` or prefetch can produce an otherwise perfect owner→child→reader chain. No chain is allowed to trigger an alternate source, grant, Media3 command or user APK.

## Original publisher-signed DEX verification

- Publisher-signed Yandex Music `2026.10.3 #170gpr`, 5 verified split APK, 6 DEX, 230533 method bodies. Only class signatures, field types and bounded register identities; no APK/DEX/audio/URI/account data exported.
- There is exactly **one** signed `Locv.i0()V` body, two supported `Lero` constructor shapes, seven exact `kvs/Lero/Lmb4/Lha4` target method bodies, and one `Lero→Lmb4` typed field.
- Inside `Locv.i0`, signed DEX contains **one direct invoke** of an `Lero` constructor. The strict 55-instruction same-basic-block `new-instance` receiver provenance produced **zero** proven local matches; this is NOT proof the direct constructor is unreachably dead, but neither can it be claimed that exact `new-instance` and invoke stay in the same straight-line block. Runtime owner/child identity remains unverified.
- All static facts remain **NON-RUNTIME**. The earlier unresolved bridge from current Yandex `trackId + edition + generation` to the exact **selected** MediaSource/decoder-before-prepare remains the release blocker.

## Automated tests / release boundary

- `NativeSourceDispatchLifecycleRaceTest`: 5,000 synthetic Next/async t-success-vs-throw races; reader completes before t returns, t failure drops deferred reader, source removal, repeated t (seek), overlapping same-instance t, wrong reader, cross-thread queue.
- `NativeOwnerConstructionWitnessTest`: 10,000 synthetic owner/child construction frames with exceptions, reentrance, multiple-child rejects and cross-thread isolation. End-to-end source→reader link is also synthetic; it validates reference bookkeeping, never real Yandex audio.
- `tests/test_native_runtime_hook_shapes.py`: exact signatures and synthetic DEX receiver register/branch tests; signed method audit in a separate CI workflow.
- `android-native-yandex-hooklab.yml`: compile pure-JVM tests and Android Xposed module **only**, verifies no permissions, data-values, second player or user-distributed APK.
- **NO manual owner check** until real, authorized in-process source-before-decoder integration is established; Play-Protect-blocked Native Gate is archived under STOP-SHIP. Preserve frozen old Test.50 branch.

## Result and remaining next gate

This block strengthens the **accuracy** of native source/reader observation and proves that a thrown source start can no longer masquerade as successful source acceptance in the synthetic gate. It does **not** make audio substitution work in original Yandex. A real *publisher-authorized or otherwise legitimately exposed* Android same-player source API is still missing. The next milestone must provide a real decoder-selected track+edition+generation witness under normal Android security. Until then **NO-GO** for user-facing native one-player replacement.

CI links, exact SHA and backup are recorded in the top of `docs/android/NEXT-CHAT.md` after all checks finish.
