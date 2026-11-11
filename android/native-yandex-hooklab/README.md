> **Latest actual native ARM13 SUCCESS 11.11.2026:** [CI 42987483624](https://github.com/manufact-test/nomusic/actions/runs/42987483624), 2/2 GREEN: ARM Linux -> Android13 Redroid, ARMv7 ABI, own JNI app with pinned LSPatch level0 and exactly 1 own LibXposed module **executes real in-process onCreate interception**, own MAIN alive and resumed. No vendor Yandex code installed, no owner phone. [Report](../../docs/android/ANDROID-A1-TRUE-ARM13-REDROID-LSPATCH-OWN-HOOK-VERIFIED-20261111.md). Exact backup `backup/android-a1-real-arm13-armv7-own-lspatch-hook-green-20261111` @ `1390990fe3086c5690a8f0b2c33e5cc5dc2b00b9`. Do not claim working native Yandex UI/audio or Play Protect.

> **Latest 11.11.2026: vendor-free real emulator A/B:** [native ARMv7 via x86 NativeBridge crashes with SIGSEGV; x86-native LSPatch runs cleanly on SAME API30 emulator](../../docs/android/ANDROID-A1-OWNED-ARMV7-NATIVEBRIDGE-VS-NATIVE-X86-AB-20261111.md). CI [OWN ARMv7 #42982872899](https://github.com/manufact-test/nomusic/actions/runs/42982872899) / [OWN x86 #42983717005](https://github.com/manufact-test/nomusic/actions/runs/42983717005). No Yandex or owner device touched. Next: true ARM Android runtime, never fake x86 translation pass as Android Yandex sound. Backup `backup/android-a1-owned-armbridge-fails-native-x86-pass-20261111` @ d305f32dabb4e4209d2fa3fbf51bd55edec09db4.

> **Confirmed 11.11.2026 native SIGSEGV after ABI-correct emulator mirror:** CI [42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329), main-only debuggerd backtrace first frame LIBART, later NATIVE_BRIDGE, no Java dlopen. Independent clone MAIN/UI remains NO-GO. See [native crash handoff](../../docs/android/ANDROID-A1-ARMV7-MIRROR-NATIVE-CRASH-GATE-20261111.md). Mirror is temporary CI-only and not safe HONOR APK.

> **Latest isolated Android A1 11.11:** [ABI-mirrored upstream ARMv7 loader on x86 ARMv7 native bridge: no Java dlopen, but CRASH_NATIVE status=11, native UI NO-GO](../../docs/android/ANDROID-A1-ARMV7-MIRROR-NATIVE-CRASH-GATE-20261111.md). Strict CI [42980968489](https://github.com/manufact-test/nomusic/actions/runs/42980968489). Tombstone evidence run [42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329). Mirror is disposable CI-only; not for HONOR. Backup `backup/android-a1-emulator-armv7-mirror-native-crash-gate-20261111` @ 89de4fd6d0d58a2fcde51f44e034a91001a5b481.

> **Root-cause verified, 11.11.2026:** [Android x86+ARMv7 LSPatch loader EM_386 vs expected EM_ARM](../../docs/android/ANDROID-A1-LSPATCH-NATIVE-BRIDGE-ELF-ROOT-CAUSE-20261111.md), real [CI 42980016274](https://github.com/manufact-test/nomusic/actions/runs/42980016274). ZIP/4 ELF align correct, but Android primaryCpuAbi ARMv7 conflicts with x86 VM ISA loader choice; MAIN/UI still FAIL. Frozen `backup/android-a1-elf-machine-mismatch-proven-20261111` @ 8da1b888308bf7531485cd40e4d98b1907982b72. No owner APK. This supersedes older generic dlopen-unknown notes.

> **Актуальный handoff 11.11.2026:** [docs/android/NEXT-CHAT-NATIVE-CLONE-20261111.md](../../docs/android/NEXT-CHAT-NATIVE-CLONE-20261111.md); [фактическая диагностика native loader](../../docs/android/ANDROID-A1-LOADER0-RUNTIME-AND-CRASH-GATE-20261111.md). Independent 1 APK coexists with original 5 splits on disposable x86 ARMv7 emulator. LSPatch signature bypass remains 0; scoped CRASH buffer confirms `UnsatisfiedLinkError`/`dlopen failed` referencing `liblspatch.so` in native MAIN, no UI/login/audio. [CI 42977185868](https://github.com/manufact-test/nomusic/actions/runs/42977185868): ALL FOUR signed LSPatch loader ELF ABI are STORED, ELF-correct and 4096-page aligned; clone MAIN still REASON_CRASH/UnsatisfiedLinkError dlopen liblspatch.so. Not a successful runtime. See current NEXT-CHAT. Owner HONOR untouched, Play Protect unchanged, Test.50 frozen.

> **Native A1 latest A/B, 11.11.2026:** [actual clone-before-original CI](../../docs/android/ANDROID-A1-SINGLE-APK-CLONE-FIRST-AB-20261111.md). One APK clone installs but native MAIN fails even ALONE, original signature/publisher app not involved in collision. Repackaging cannot be declared solved; no owner APK. Exact backup `backup/android-native-singleapk-clone-alone-and-coexistence-a-b-no-ui-20261111`.

> **Latest 11.11.2026: native single-APK parallel-clone A1** — [full 5+1 evidence](../../docs/android/ANDROID-A1-PARALLEL-SINGLE-APK-MERGE-20261111.md), [competitor feasibility matrix](../../docs/android/ANDROID-A1-SEVEN-COMPETITORS-AND-5PLUS1-VERDICT-20261111.md). Exact 5 publisher-signed split + 1 separately signed merged clone APK **installed together** on disposable Android 11; **clone MAIN still EXIT_SELF(0), no playable native UI**. CI workflow intentionally FAIL; no user APK, no Play Protect or HONOR mutation. Do not revert to WebView or double audio engine. Research backup: `backup/android-parallel-one-apk-5plus1-install-pass-ui-blocked-20261111`.

# CELIKOM Android native-Yandex hook lab (ISOLATED, READ-ONLY)

> **CURRENT A1 checkpoint (11.11.2026):** [реальный ARM read-only witness + приватный lab split export](../../docs/android/ANDROID-NATIVE-A1-REAL-ARM-LSPATCH-WITNESS-20261111.md). Отдельная ветка `feature/android-native-clone-lspatch-a1-20261111`, CI [42902701224](https://github.com/manufact-test/nomusic/actions/runs/42902701224) SUCCESS. Ни одного ARM native Yandex runtime/аудиотеста нет; **не выдавать это за работающий APK**. Возвращаться к прежним synthetic-only задачам без аппаратного gate не нужно.


**Status:** Source code only; builds a *CELIKOM Xposed module APK* (not an independent music player). Owner authorized research and preparation for **a separate disposable test device only**. No package was installed, and **nothing** on the owner's HONOR, stable Test.50, catalog or server is touched.

## NEWEST verified actual Android 13 async player race / rapid Start-Stop-Next (2026-11-10)

- **CI-green code:** `50735e6d56481ea0ce3da8fdcb03589cad90608c`; frozen backup: `backup/android-own-api33-rapid-reload-race-pass-20261110`; full evidence: `docs/android/ANDROID-OWN-API33-RAPID-RELOAD-RACE-PASS-2026-11-10.md`.
- [Real API33 MediaPlayer CI #42837053639 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837053639): **BOTH** `OWN_DECODER_LIFECYCLE` (same-track paused/playing source reload and Next) **AND** `OWN_ASYNC_RACE_PASS` (12 rounds of rapid start/stop on same A during prepare, Next B, 48 platform player creations with never two simultaneously, six B pause+seek). Only OWN generated WAV on `x86_64` emulator, `-noaudio`; no Yandex or owner test.
- Fixed pending position bug in OWN `AudioSmokeScreen`: `restoreSeekMs` is authoritative **before** `onPrepared`, not just after seek starts. Late simulated tickets rejected; do NOT claim 36 real Android late callbacks.
- Earlier exact same Java sources on SHA `31c34b23`: [ARMv7 host #42837003150 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003150), [scope #42837003307 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003307), [research module #42837003096 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42837003096); only subsequent diff before current green SHA is a workflow edit.
- Android Yandex source/decoder preprepare **NOT** identified; no working audio swap. Public MediaSession and AudioPlaybackCallback do not expose another app's private `Lemb`/DataSource. Keep Test.50/HONOR/Windows/production unchanged.

## PREVIOUS OWN Android 13 actual MediaPlayer runtime PASS (2026-11-10)

- **CI-green source:** `bb26aca9652850c69fbd0896a26bec22601826b0`; **frozen backup:** `backup/android-own-api33-real-mediaplayer-source-reload-pass-20261110`; detailed evidence: `docs/android/ANDROID-OWN-API33-MEDIAPLAYER-RUNTIME-PASS-2026-11-10.md`.
- On a disposable **Android 13 x86_64 emulator**, only the CELIKOM-owned no-permission `armv7-loader-host` APK runs a synthetic 8s WAV through real Android `MediaPlayer`. Real callbacks show original A→Seek→Pause→Start alternative A (pause and 2.2s position retained)→Resume→Stop original A (position/playing retained)→Next original B. Android code calls `OwnSameTrackReloadPlan.decide` for the actual source change; releases old MediaPlayer before new prepare; does NOT call Windows Electron reloadEntity. CI logged `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE`.
- [Real Android runtime #42835181030 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181030), [ARMv7 owned host #42835181029 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181029), [scope #42835181289 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181289), [research module #42835181034 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181034).
- Crucially **NO Yandex package, user account, phone, audible playback, native Android selected Lemb source identity or live original decoder** was tested. Android CELIKOM audio swap NO-GO. This is a clean OWN-only actual Android platform proof, not a release.
  
## PREVIOUS Windows W60 concept transferred to OWN ARMv7 Android source-reload (2026-11-10)

- **CI GREEN code:** `a7f83f0ab836bbeeb12538c6a389c9569d326610`; **backup:** `backup/android-windows-w60-owned-reload-armv7-arm64-ci-green-20261110`; evidence: `docs/android/ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md`.
- Compared actual owner-accepted Windows 0.24.9 native source adapter and Electron source reload; W56 signed query guard is **Windows-only**, not blindly copied into Android. Android signed Yandex has eight candidate `Lemb` implementations and no verified native equivalent of Electron `reloadEntity("QUALITY_CHANGE")`.
- Implemented **only inside own generated WAV ARMv7 lab app**: `OwnSameTrackReloadPlan.java` and `AudioSmokeScreen.java` Start/Stop on current A preserve paused/position; release old `MediaPlayer` BEFORE constructing next; skip unchanged source; Next B remains original, async callbacks revision-fenced, fast toggles during restoration preserve pending seek.
- [OWN ARMv7 Android build/scope/safety/50,020 checks #42830966825](https://github.com/manufact-test/nomusic/actions/runs/42830966825) **SUCCESS**. [Real ARM64 Linux JVM source-selection plan #42831135970](https://github.com/manufact-test/nomusic/actions/runs/42831135970) **SUCCESS**. No device install, no real Yandex, no user account, no actual audio heard by owner.
- **Android playback substitution remains NO-GO** pending proof selected `Lemb` instance + current track/edition/generation + actual decoder prepare; lab model not wired to vendor app.

## PREVIOUS verified source-instance fail-closed ARM64 checkpoint (2026-11-10)

- **CI GREEN code:** `59aa2d14bf32fd0f5eb553c09ec88738d84353a0`; **frozen rollback:** `backup/android-signed-source-instance-failclosed-arm64-ci-green-20261110`; evidence: `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- Strict `NativeSourceInstanceFence.snapshot`: any rejected event in same generation permanently invalidates synthetic `complete`, even after clean `open/read/close`; old-generation stale events do not poison new epochs. New regression tests cover both. All code remains OWN-ONLY pure Java, no `NativeHookEntry` wiring.
- [Native ARM64 Linux JVM #42828086262](https://github.com/manufact-test/nomusic/actions/runs/42828086262) SUCCESS; [Android lab and module #42828086264](https://github.com/manufact-test/nomusic/actions/runs/42828086264) SUCCESS 2/2. This is **NOT a Yandex decoder runtime test or working alternate audio**. Signed 8 `Lemb` implementations still require a trusted active-source witness.

## PREVIOUS own-source instance fence and signed Lemb source alternatives (2026-11-10)

- **Signed-original + OWN-ONLY code:** `3aaab880fff4326b596f63a52a89a0f4d0085fef`, immutable backup `backup/android-signed-source-instance-arm64-lemb-ci-green-20261110`; full evidence: `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- Exactly 8 concrete `Lemb` implementors and only 4 direct `Lemb.t/remove` callsites in signed 6 DEX. `Lero` is just one of possible source classes (e.g. factories `Lkvs.A`, `Locv.i0`, `Larv.g` instantiate multiple alternative `Lemb` types). **Do not equate a static Lero reader chain with the selected active player.**
- New isolated pure-Java `NativeSourceInstanceFence`: exact JVM `Object ==` source/reader/loader/task identities, generation fencing, duplicate preprepare rejection, seek-reopen, Stop, monotonic-clock rollback, zero media or network. **Not referenced by `NativeHookEntry` and cannot authorize audio.**
- 44,478 synthetic assertions + 27 concurrency assertions and 4,800 deliberately stale cross-thread callbacks pass on [real ARM64 Linux JVM #42826864698](https://github.com/manufact-test/nomusic/actions/runs/42826864698) (**NOT Android runtime**). [Signed factory candidates #42827236492](https://github.com/manufact-test/nomusic/actions/runs/42827236492) SUCCESS. [Android module #42827236060](https://github.com/manufact-test/nomusic/actions/runs/42827236060) SUCCESS 2/2.
- Still **no chosen current track/edition/generation nor live decoder preprepare proof**. No Android audio replacement, no Yandex/owner account/phone mutation.

## PREVIOUS publisher-original exact Lero → async callback → byte reader (2026-11-10)

- **Code** `f04745f7dcd4455996eadf56dc0be6c52a44c63f`; **frozen rollback** `backup/android-signed-lero-lmb4-reader-case-ci-green-20261110`; details `docs/android/ANDROID-NATIVE-SIGNED-LERO-LMB4-EXECUTION-CHAIN-2026-11-10.md`.
- Signed concrete local `Lga4.c():Lha4` return goes into `Lero.Lha4` field and `Lmb4.<init>` source argument1 in same basic block. The constructor writes exact `Lmb4:Lm48` field, consumed by `Lmb4.a` and cast `Lha4`. The method calls `Lha4.b(La58)` twice, `read([BII)`, `close()`.
- Actual DEX packed-switch decoding validates `Lero.t`'s `Lwq7` synthetic callback mode: it selects the **default fallthrough** not one of 2 keyed cases. Exact constructor field capture of `Lero.this` and matching field load in selected callback yield the static `Lero.Lmb4.a` case.
- [Reader CI #42821377729](https://github.com/manufact-test/nomusic/actions/runs/42821377729), [async selector #42822722957](https://github.com/manufact-test/nomusic/actions/runs/42822722957), [exact field #42823360505](https://github.com/manufact-test/nomusic/actions/runs/42823360505), [read-only module #42823360398](https://github.com/manufact-test/nomusic/actions/runs/42823360398) SUCCESS 2/2.
- **Still no current trackId+edition+generation runtime binding, actual decoder PREPARE or Android audio replacement proof.** Source-only lab, no owner installations, no vendor APK changes.

## PREVIOUS signed original URI model → native DataSource source lifecycle (2026-11-10)

- **Verified CI green code:** `f327f5b9bcfee028e754f9a803f29ade347cb240`, **frozen rollback:** `backup/android-signed-uri-locv-source-cfg-green-20261110`, **details:** `docs/android/ANDROID-NATIVE-SIGNED-URI-TO-DATASOURCE-LIFECYCLE-EVIDENCE-2026-11-10.md`.
- `Locv.i0` reads URI-like input, `Lw4y.z` inspects scheme/host/path/query (never exporting values), coroutine `Llky` and `Lfwm.M` produce local `Ljgv`; bounded CFG shows it may pass as argument 1 to `Lcq7.i0` and `Lcq7.D`.
- `Lcq7.i0` has two concrete callers, `Lo4y.c` and `Locv.i0`: they **project a field** from a wrapper using `iget-object`, then conditionally pass cast `Lga4` into `Lnro/Lero`. Corrected old DEX 22c register kill that had incorrectly equated wrapper identity with field value. `Locv.t/remove` conditionally invoke `i0`.
- `Lcq7.A` result reaches the exact primary Le48 `Lga4` field in the same basic block; `Lga4.d` primary `Lm48` reaches constructor argument 3 of `Lha4`. The signed `Lha4.f` and `Lha4.read` methods call `Lm48.b(La58)` and `Lv38.read([BII)`.
- Verified [signed source #42819113120](https://github.com/manufact-test/nomusic/actions/runs/42819113120), [actual CFG #42819106641](https://github.com/manufact-test/nomusic/actions/runs/42819106641), [taint fix #42817633107](https://github.com/manufact-test/nomusic/actions/runs/42817633107), [Android module #42819113420](https://github.com/manufact-test/nomusic/actions/runs/42819113420) SUCCESS 2/2.
- **No runtime current trackId+edition+generation / decoder PREPARE / Android replacement audio proof.** No vendor APK patches, no user or installed Yandex changes.

## PREVIOUS publisher-signed obfuscated DataSource source/read evidence (2026-11-10)

- **Verified code:** `6b5bfde53d81a29920f32a3c6b13b730b216e669`; **backup:** `backup/android-signed-dual-source-dataspec-open-ci-green-20261110`; full note `docs/android/ANDROID-NATIVE-SIGNED-DATASPEC-OPEN-SOURCE-EVIDENCE-2026-11-10.md`.
- Exact signed six-DEX class and method inheritance: `Lm48` defines `b(La58):J`, `getUri`, `close`; its parent `Lv38` defines `read([BII):I`. Combined contract matches a DataSource-like shape, with 33 concrete implementations including `Lha4` and `Lza4`. No claim that a specific current Yandex track is routed through it.
- `Lga4.b/c` use secondary Le48, while `Lga4.d` reads primary Le48. `Lcq7.i0` places `Lya4 → Lza4` (throwing open/read) in secondary, `Lcq7.A → Luiq` in primary. `Luiq.a` lazily caches `Lm48` via `Lz3f`; real static invoke `Lz3f.a → Lm48.b(La58)`, and `Lha4.f` delegates to `Lm48.b`.
- [Signed source/open CI #42815048696](https://github.com/manufact-test/nomusic/actions/runs/42815048696) SUCCESS, [Android module CI #42815048701](https://github.com/manufact-test/nomusic/actions/runs/42815048701) SUCCESS 2/2. **No current-track + edition + generation binding / decoder prepare / Android audio replacement proof.** Source-only read-only research remains isolated.

## PREVIOUS signed native typed-model / field2 receiver proof (2026-11-10)

- Verified code `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`, rollback `backup/android-signed-typed-dispatch-field-audit-ci-green-20261110`.
- Full actual signed source-to-model investigation: `docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md`.
- Native DTO wrapper Lxa7 → Leed → typed Ldiv → Lygv.r(Ldiv):Ljgv → real consumers Lcq7/Lo4y/Larv. NO verified same-current-track decoder.
- Possible 7-hop obfuscated route to Lro7.y0 uses an **ambiguous 16-way Le48.a dispatch**. Exact original DEX read/write census across 230,533 method bodies shows Lga4.c loads Le48 field-2; ctor's Lzcd is in field-1, and field-2 has Lya4/Lkc6/unknown writers. Lsu5.invoke has unrelated switch branches. Treat the graph as candidate only, never as proof for sound substitution.
- Signed CI verified: typed [#42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855), field [#42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588), and read-only Android module [#42810750850](https://github.com/manufact-test/nomusic/actions/runs/42810750850) SUCCESS 2/2. No installable Yandex audio replacement.

## Previous publisher-signed DEX register/CFG audit (2026-11-10)

- Source-only `audit_native_register_bridge.py`, tests and independent workflow `android-native-register-bridge-audit.yml`.
- Pinned signed APK CI [#42806655214](https://github.com/manufact-test/nomusic/actions/runs/42806655214) SUCCESS; module build [#42806655152](https://github.com/manufact-test/nomusic/actions/runs/42806655152) SUCCESS 2/2; rollback `backup/android-signed-register-cfg-ci-green-20261110` at `8b7bc64f89249e5434da739851bececce2adb121`.
- Confirmed bounded register may-flow: FileInfo sw7.y0/z0 result → Lxa7 constructor; Lged.a invokes Lhee.a and can pass the result to Leed.a/Lta7.c/Lwa7.a. Coroutine immediate callers Lfed/Lgee/Lfqr exist. NO direct source/decoder or active-audio proof; module remains read-only.
- Detailed report: `docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md`.

## Exact target

- Native Yandex Music `ru.yandex.music`, **2026.10.3 #170gpr**, code **24026531**, exact original signer SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba` pinned in the offline host audit.
- Exact first-party API: `FileInfoApi` / `OldFileInfoApi` → `FileInfoDto.urls,codec,key,bitrate,quality` → `sw7.y0/z0` → `eed`. Static evidence and original source trace: `docs/android/ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md`.
- This module hooks **only the exact `sw7.y0(FileInfoDto,boolean):eed` and `sw7.z0(OldGetFileInfoDto,boolean):eed` after original conversion** and logs throttled **COUNTS ONLY**. A different name/signature/version fails shut. It passes all original arguments and original return value unchanged. Does not read `urls`, `key`, OAuth headers or account data; has **no network / accessibility / storage permissions**. No MediaPlayer, WebView, second clock or stream replacement.

## Build and verify source

Use Java 17, Android SDK 35, Gradle 8.11.1:

```bash
gradle -p android/native-yandex-hooklab :app:assembleDebug --no-daemon
```

Also run deterministic plain-JVM `HookSpecTest` with synthetic replacement DTO classes. CI intentionally does **not** retain a binary as a release artifact; the module APK alone cannot alter the unmodified Yandex app, and Play Protect/device startup cannot be verified by CI.

## Authorized isolated test path (NOT done automatically)

Use source-available **JingMatrix/LSPatch v1.2 build 487**, pinned upstream release, as a **tool** (GPL-3.0; evaluate licence obligations before any distribution). For a spare/emulator with Android 13 ARM64, patch the separately-verified original #170gpr **base plus splits** using embedded mode, with local lab signing. Never upload original/patched Yandex packages to GitHub, store logs containing account data, or share patch distribution. Verify after patch that all splits have matching lab signer, correct package/version, and modern module metadata. Original Yandex package cannot remain installed with same ID and a different signing certificate; do **not** try to upgrade/overwrite it, and **never delete the owner's official Yandex**. No special permission to switch off Play Protect has been given.

### Manual Gate 1 witness (spare device only)

- On a clean disposable test device with Play Protect ON, check unmodified Yandex baseline, then controlled patched test copy if safe and legally permitted.
- Confirm module logs `observer: native file-info converter hooks armed; read-only` and counters during native playback/seek/Next; verify original stream still plays. Record **only event categories, package version and aggregated counts**, never source URLs, user credentials, tokens or private files.
- **Counters are not enough** to release CELIKOM. Need identify exact track+edition and prove mapping from response model to *native* source/decoder before the next step. If original client fails login, package integrity, or Play Protect, stop—never bypass warnings or protections.

**No claim of working CELIKOM replacement:** actual audio source selector, account-safe broker, Google Play Protect verdict and native pause/seek continuity are still unverified. This is preparation for a genuine in-process test, not another user-facing fake player.

## Read-only spare ARM hardware preflight (09.11.2026)

Before considering any installation on a **separate disposable device**, run `python3 android/native-yandex-hooklab/probe_arm_device.py` from a PC with adb and exactly one authorized **spare** phone connected. It uses only `adb devices`, `getprop` and `pm path`; it never installs, removes, launches, roots or changes anything. It refuses the known owner HONOR 50, an existing Yandex package, Android below API 33, emulators, no Play Store and devices lacking `armeabi-v7a` (the exact native #170gpr host contains ARMv7 32-bit libraries). On a 64-bit-only Android device the official host is ABI-incompatible even if its CPU is arm64.

**A green preflight is NOT permission to install anything.** It is not proof that Play Protect is enabled, that the phone is an authorized spare, or that libxposed works. Those require explicit on-device checks and a separate lab installation decision. It never reports device serials, paths, account data or Play Protect status guesses. Unit tests run in the existing hooklab CI without adb.

## 10 Nov 2026: final source admission MODEL (not a live Yandex hook)

`NativePrePrepareAdmission.java` coordinates exact native track+edition+generation observation, FileInfo and the actual decoder-descriptor identity (only an approved future host may supply those values), plus a single pre-prepare source decision. Unknown identity, unsafe/stale candidate, edition mismatch, or missing real FileInfo → original source. Duplicate/stale prepare → no apply. No MediaPlayer or source mutation in the model.

[CI 42780177178](https://github.com/manufact-test/nomusic/actions/runs/42780177178) SUCCESS 2/2: 35,032 model admission assertions incl. 5,000 Next; 10,037 NativeSourceGate; 10,015 NativeTrackIdentityGate; read-only module APK built in CI but NOT released. **No live Yandex decoder/source replacement has been verified.** See `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md` and `docs/android/NEXT-CHAT.md`.



## 10.11.2026 — verified signed media engine class hierarchy

Read-only signed-original CI now found 4 concrete obfuscated classes implementing AndroidX Media3 ExoPlayer, but no named `ExoPlayerImpl`, `DefaultMediaSourceFactory` nor `prepare()V` code body in those four class inheritance chains. See `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md`. These are static implementation candidates, NOT a verified native audio source. An ubuntu-24.04-arm runner is native Linux ARM64 but cannot boot an accelerated native Android guest without /dev/kvm; do not treat CI's ARM runner as a working Android device. No owner action now.

## Current handoff / verified signed source evidence (2026-11-10)

For all new engineering sessions, start at `docs/android/00-NATIVE-HANDOFF-NAVIGATION-2026-11-10.md`. Latest signed actual Yandex six-DEX static audit: [CI #42804081064](https://github.com/manufact-test/nomusic/actions/runs/42804081064) SUCCESS; exact FileInfo converter caller `Lhee;->a`, model consumer `Lged;->a`; no proven dataflow into four obfuscated concrete Media3 ExoPlayer implementors. Platform `MediaSession.setMetadata` and `setPlaybackState` each have two signed-APK static callers, **not** actual runtime proof. Read-only module build/synthetic tests [CI #42804081053](https://github.com/manufact-test/nomusic/actions/runs/42804081053) SUCCESS 2/2. Windows real audio success DOES NOT imply Android source swap. No user APK or phone modifications.

