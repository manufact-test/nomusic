# CELIKOM Android — native Yandex Lemb instance dispatch witness (10.11.2026)

## Boundary and purpose

This is a continuation of **NEW NATIVE** Android work only. Not Test.50, not DynamicsProcessing, not second MediaPlayer. The Test.51 secondary-decoder APK from a different branch is **not part of the native project**.

Signed Yandex #170gpr six DEX audit previously established:
- Lemb has 8 implementors: `alt, chg, ero, ocv, ojz, t67, t6f, xq7`;
- factory `Lkvs;->A(Lzcb;Lgmb;)Lemb;` conditionally creates distinct implementations;
- `Lemb;->t(Ldmb;)V` and `remove()V` have 4 direct interface invoke sites;
- static existence alone never proves active currently-audible track or decoder prepare.

## What changed in the actual native branch

- `HookSpec.findSourceFactory`: version-pinned exact factory owner/arg/return shape `kvs.A(zcb,gmb):emb`, static **or instance** (access flags not separately verified). Fails closed if absent, overloaded wrong or unknown class loader.
- `HookSpec.findSourceLifecycle`: only eight explicitly known implementors, exact concrete non-static `t(dmb):void` / `remove():void`; wrong or inherited methods not speculatively hooked.
- `NativeHookEntry.armSourceDispatchWitness`: read-only post-`chain.proceed()` observation with `PROTECTIVE` exception mode after pinned package and version proof; independently arms factory and available lifecycle implementations, never mutates args/result/stream.
- `NativeSourceDispatchWitness`: bounded **16 reference identities**, 15s monotonic time window, factory→t same-instance match uses `==` not class-only or `equals`. Unknown classes, old references, clock rollback and removed sources fail closed. Logs only aggregate counts, no track, edition, title, URL, auth, audio or objects.
- A factory→t match **does not prove it is the decoder-selected source**. A source could be background/preload, a t-call is not necessarily a DataSource.open or decoder.prepare. This remains read-only evidence.

## Validation and remaining blocker

- `NativeSourceDispatchWitnessTest` uses only synthetic obfuscated descriptors and 10,000 same-instance / late-identity cycles. Pure JVM.
- **CI GREEN:** [#42857995073 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42857995073), exact code `9073ea35d3f5ef2a996b197d237f4265ab0ab564`, immutable rollback `backup/android-native-lemb-instance-observer-ci-green-20261110`. Both JVM regression / security and Android module build passed. The CI module is a read-only research artifact, NOT a functioning publisher playback-source replacement.
- No authorized and working host with the real publisher-original player source selector is connected; the host is not instrumentable from a separate no-root ordinary Android app.
- **No legitimate native Android audio replacement APK exists from this change.** Do not release an APK claiming it works in Yandex. Do not bypass original signature, DRM, Play Protect or install a modified app on owner HONOR.

## Next engineering admission

To advance beyond candidate class/ref counts requires a real, publisher-permitted, in-process Android host source boundary: at runtime show that factory-returned `emb` object is the instance selected by the active player, tied to same `trackId+edition+generation`, and that its decoder descriptor is passed before prepare. Only then call `NativePrePrepareAdmission`, resolve a rights-authorized alternative and test a true one-player change. Without host access, tests remain investigative; do not invent a source-first API or repeat the blocked x86/AppMetrica clone loops.

Scope untouched: exact owner Test.50, main HONOR/Yandex, Windows, extension, production/API/database and the unrelated Test.51 branch.
