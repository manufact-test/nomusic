# Android A1 — signed native Track / coroutine caller-identity checkpoint (15 Nov 2026)

**Scope:** read-only, publisher-signed Yandex Music 2025.10.4 #120.1gpr (pinned original XAPK SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`). 16 signed splits / 6 DEX; 254,355 methods scanned. This is **not** a working CELIKOM replacement build.

**Code checkpoint:** `0de0e4278977f5821ad1de6b0ca879bfa7d110e6`; CI [#43733450288](https://github.com/manufact-test/nomusic/actions/runs/43733450288) **SUCCESS, 71/71 tests**. Exact backup: `backup/android-a1-continuation-hierarchy-ci-green-20261115` @ same SHA. Active branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Prior checkpoint: `backup/android-a1-continuation-new-instance-types-ci-green-20261115` @ `4a15adf7644c2ea1066620c4c0c615522af3a2d3`.

## Established from the exact signed DEX

- There are exactly **three direct invocation sites** of `LGp0.new(LGp0; Track; LOe2;)`. This is a direct-call census; virtual/interface dispatch and runtime invocation are not proven by it.
- **Initial entry `LDp0.if(Track, kotlin.coroutines.Continuation)`**, ordinal 34: the Track argument of `LGp0.new` is the exact original Track parameter Java reference on all observed bounded dataflow paths. The continuation argument is either its original Kotlin Continuation parameter or a fresh instance of `LDp0$a`.
- **Flow entry `Lwp0$a.emit(Object, kotlin.coroutines.Continuation)`**, ordinal 39: the Track argument is the exact method Object parameter reference after Track check-cast on observed bounded dataflow paths. The continuation argument is either its Kotlin Continuation parameter or a fresh instance of `Lwp0$a$a`. The fact that this is Flow does **not** prove it represents the actively playing track.
- **Resume `LFp0.invokeSuspend(Object)`**, ordinal 7: passes this exact continuation object to `LGp0.new` while the explicit Track argument is null. In `LGp0.new`, the Track typed continuation field may be reused for wrapper creation. Initial capture and resumed reuse are structurally evidenced but **inter-invocation Java object identity is not established** at runtime.
- Both new classes `LDp0$a` and `Lwp0$a$a` **exist in the signed DEX** and have exact superclass chain `LOe2; -> LZA0; -> java.lang.Object`. These are genuine descendants of the expected `LOe2` continuation type, not unrelated newly allocated types. This does **not** prove they capture the same original continuation parameter, because exact constructor argument capture has not been established.
- Earlier signed audit found 1 writer method for the observed Track continuation field, and the audio renderer census found three ByteBuffer fields / seven writer methods with decoder-return candidate `Lad6.final(...)` feeding `LcC0.n` and `Lkd6.n`. This is still a disconnected static audio chain, not evidence for the same selected Track.

## Explicit NO-GO boundaries

`active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`, `fp0_resume_track_binding_runtime_proven=false`. Branch predicates are not evaluated as runtime facts; exception-handler edges are not included in the bounded caller trace. There is no proof the Track reaching `LDp0.if` or `Lwp0$a.emit` is the live player item rather than queue, download, cache or prefetch. There is also no proof it is the exact identity that produces the decoded ByteBuffer fed into the audio sink.

**Do not enable CELIKOM replacement or report Stage B as ready.** NAV17 Stage A remains owner-confirmed PASS (native Yandex login, library and original playback); Stage B still has no CELIKOM replacement audio. No runtime hooks or native Yandex code changed, no APK built/installed/exported, no account/media values or private field contents accessed.

## Next exact research work

1. Enumerate exact incoming direct callsites / observed Flow dispatch contracts for `LDp0.if` and `Lwp0$a.emit`; trace Track reference provenance toward **active player selection**, explicitly distinguishing queue/prefetch/download. Keep virtual dispatch uncertainty visible.
2. Inspect constructor callsite captures for `LDp0$a` and `Lwp0$a$a` only if this is needed for the selected-item chain; do not let coroutine wrappers become an endless detour.
3. Link the exact selected Track / Album / edition / generation to the previously established decoder-buffer field -> sink chain with object-identity and lifecycle evidence. No name, timestamp or type-only shortcuts.
4. Only when this gate is proven, reuse existing CELIKOM resolve/entitlement and original-fallback contracts before decoder input in the **same native Yandex player**. Preserve NAV17 and Test.50 baselines; no new player.

**Files changed in this audit:** `android/native-yandex-hooklab/audit_native_selected_item_handoff.py` and its focused tests; no runtime component. This document supersedes the old 49/49 renderer-only headline, not the original NAV17 owner-confirmed result.
