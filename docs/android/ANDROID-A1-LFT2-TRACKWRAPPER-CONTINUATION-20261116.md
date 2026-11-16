# CELIKOM Android A1 — LfT2 TrackWrapper continuation handoff

**Updated:** 16 November 2026  
**Repository:** `manufact-test/nomusic`  
**Working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `27ccbe8348d598fead0386e70ef68573b04270c4`  
**CI #229:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139) — exact pinned issuer-signed Yandex Music 2025 XAPK, 16 signed splits / 6 DEX, read-only.  
**Exact backup:** `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116` @ `27ccbe8348d598fead0386e70ef68573b04270c4`.  
**Last runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`. No runtime-hook changes after it.

## 1. Current status

Stage A / NAV17: PASS by owner confirmation.  
Stage B: NOT CONNECTED / NO-GO.

The audit verdict is `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.  
`active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`.

No APK was built, patched, installed, or released. The original signed Yandex binary was inspected read-only. No login, user media, account data, private field values, or audio bytes were accessed.

## 2. Proven identity chain

The latest bounded scan of all six signed DEX proves these exact same-object edges:

1. `LIEa.new(...)` passes its TrackWrapper parameter to `Lqj8.if(...)`.
2. `Lqj8;` is an abstract interface. The exact method has one direct implementer: `Lxj8;`.
3. `Lxj8.if(LtCa;ZLqj8$a;LLEa;)Ljava/lang/Object;` passes the same service object and same TrackWrapper into the `Lvj8` continuation constructor.
4. `Lvj8.<init>` stores both objects on the continuation. Its `invokeSuspend` reads both same references and passes them to `Lxj8.for(...)`.
5. The exact `Lxj8.for(Lxj8;LtCa;ZLqj8$a;LOe2;)Ljava/lang/Object;` body is present and its bounded CFG trace is complete. It creates several continuation objects and passes the same TrackWrapper into `LfT2.<init>(LdA9;LtCa;LgA9;)V` at two callsites (PC 210 and 432).
6. `LfT2.<init>` stores that exact TrackWrapper parameter into a field on its own `this`.

The exact route and its caller traces are complete for the claims above. Evidence is CI #229, job 133374051903.

## 3. Exact stopping point — LfT2

The `LfT2` constructor is present and stores the same TrackWrapper. However:

- The exact `LfT2.invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;` method body was not found in the pinned six DEX.
- The bounded trace therefore cannot establish that `LfT2` reads its stored TrackWrapper or forwards it.
- No TrackWrapper-to-MediaSource, MediaPeriod, DataSource, MediaItem, Player mutator, or native audio-sink edge is proven from this route.
- The broader report's `active_selected_item_proven` remains false.
- The exact constructor has 9 direct callsites across 8 caller methods. Same-TrackWrapper identity is proven at the two `Lxj8.for(...)` callsites (the current chain), plus separate `LTJ7.invokeSuspend` and `LWBa.if` callsites. The other callers merely pass a compatible TrackWrapper-typed argument; identity was not established there.
- The caller census includes owners under `com/yandex/music/shared/player/download2` and `RetryingBalancingDataSource`. Those names suggest areas worth distinguishing, but do not prove that this object belongs to active playback rather than download, retry, or prefetch work.

Do not describe `LfT2` as a confirmed coroutine implementation or infer its purpose from the obfuscated name or constructor signature.

## 4. Next task — one bounded LfT2 class inspection

**Precondition:** first resolve the exact Yandex build CELIKOM A1 is targeting. CI #229 is pinned to 2025.10.4 #120.1gpr, while the owner's phone was previously reported as 2026.09.5 #167gpr. Do not trace the 2025 DEX and apply its obfuscated route to a 2026 runtime. If the target is 2026, pin and verify that exact original signed split set before continuing.

Continue from the exact class `LfT2;` only:

1. Resolve its class definition in the six signed DEX: superclass, interfaces, access flags, and exact declared method descriptors.
2. Determine whether it declares an executable continuation entry under another exact method/signature, inherits the continuation behavior, or is not the expected coroutine object. Do not assume `invokeSuspend` exists.
3. Trace only the stored TrackWrapper field's exact read sites and the immediate calls receiving that same object. Keep field names and values out of output.
4. Follow only an identity-proven call into a relevant source/playback boundary: `MediaSource`, `MediaPeriod`, `DataSource`, `Extractor`, or Player. A method name or compatible parameter type is not proof.
5. If no executable same-object continuation or source/player handoff exists, close this candidate and stop. Do not replace it with a global scan.

The two `LfT2` constructor callsites in `Lxj8.for(...)` are the only starting callsites for this pass. Do not repeat the already complete `LIEa → Lqj8 → Lxj8.if → Lvj8 → Lxj8.for` analysis.

## 5. Relevant previous closures — do not reopen

- `LiLb`: exact constructor/getter direct-caller route closed by CI #216. Its holder-internal MediaItem identity is not connected to Player. See [ANDROID-A1-LILB-PLAYER-HANDOFF-CLOSURE-20261116.md](ANDROID-A1-LILB-PLAYER-HANDOFF-CLOSURE-20261116.md).
- `LXk6`: inner List.get → MediaItem → Player mutator identity exists, but outer caller/runtime dispatch and List element provenance are unresolved; route closed. See [ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md).
- Media3 current-item getter and Player mutator forwarding are documented in [ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md).
- The ByteBuffer-to-native sink path is separate; no current-item identity reaches it. See [ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md](ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md).

These are reference documents only. Do not load all of them at startup; read one only when the exact next task needs it.

## 6. Hard constraints

- Android CELIKOM A1 only. No Windows or browser extension work.
- Do not change architecture, vendor behavior, runtime hooks, APK, or original Yandex application.
- Do not add a second Player, decoder, or AudioTrack.
- Do not read/export Track or Album IDs/titles, URLs, DataSpec, tokens, account data, private field names/values, or audio bytes.
- Do not touch NAV17, Test.50, frozen A1/LSPatch baseline, Windows, extension, backend/API/DB, or production.
- Static inspection must remain bounded, read-only, and fail-closed.
- Work in one substantial block. No progress narration; report only a real blocker, manual measurement requirement, or completed checkpoint.
