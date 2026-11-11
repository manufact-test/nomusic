> **Decisive vendor-free A/B 11.11.2026:** [OWN ARMv7 NativeBridge SIGSEGV vs native x86 LSPatch launch pass](ANDROID-A1-OWNED-ARMV7-NATIVEBRIDGE-VS-NATIVE-X86-AB-20261111.md), CI 42982872899 + 42983717005. The previous MAIN SIGSEGV is reproducible with **no Yandex code**; in the same Android 11 emulator LSPatch succeeds on native x86. Do not conflate with a verified physical ARM launch or Yandex native UI. Exact checkpoint `d305f32dabb4e4209d2fa3fbf51bd55edec09db4` backed up.

# Android A1 — ARMv7 loader mirror: dlopen снят, следующий блокер native crash (11.11.2026)

**Status:** NO-GO native MAIN/UI; isolated disposable Android 11 emulator only. No installable CELIKOM release, no login/audio/device owner tests.

## Checked source and CI
- Source in `experiment/android-native-a1-lspatch-clone-loader0-20261111` from `788ef2189559f5a15c81b956de5d9560b45bcd6c`; new signal/tombstone-only diagnostics `89de4fd6d0d58a2fcde51f44e034a91001a5b481`.
- Prior [CI 42980016274](https://github.com/manufact-test/nomusic/actions/runs/42980016274): Android linker **actual EM_386, expected EM_ARM** for LSPatch `System.load` in ARMv7 clone on x86 NativeBridge. Signed four upstream libraries were present, STORED and page-aligned. Independent installed original was not the root cause.
- New [CI 42980968489](https://github.com/manufact-test/nomusic/actions/runs/42980968489): controlled `CELIKOM_BRIDGE_X86_RESOURCE_ARMV7=1` mirror **only** upstream ARMv7 LSPatch `.so` bytes into the **x86-named resource entry**, used solely in disposable x86+ARMv7 translated CI, no general emulator/phone APK. Structural and signed-layout checks verify x86 entry EM_ARM (40), preserved inner six host DEX/three host libs, `sigBypassLevel=0`, no competitor module, original issuer-signed Yandex unchanged.
- In both standalone and side-by-side launch, old `UnsatisfiedLinkError / dlopen failed` marker is now **absent** in MAIN PID scoped crash buffer. Android instead reports `ApplicationExitInfo REASON_CRASH_NATIVE=true`, status 11, no AndroidRuntime fatal Java exception. Main process not alive, Activity not resumed, no focused UI. Native crash category/faulting frame is still **unproven** until new debuggerd classification runs.
- Synthetic tests of mirror + zero-bypass + ABI parity pass; full runtime workflow is intentionally FAILED by strict MAIN/UI gate. This is **not proof of a functioning LSPatch injector**; NativeBridge may be incompatible beyond ELF selection.

## Current next gate
- [CI 42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329): native tombstone detector added to parse exact main PID libc fatal signal and DEBUG debuggerd traceback, only reporting signal and whitelisted library groups (LSPATCH/NATIVE_BRIDGE/LIBART/LIBC/LINKER/OTHER), no raw paths, tokens, addresses or stack. Its status **must be verified** before stating fault ownership; this entry documents its initiation, not its outcome.
- If native crash occurs in NativeBridge after correcting EM_ARM, do not extrapolate to actual ARM64 HONOR. Native ARM emulator on GitHub lacks KVM / may not be viable. Owner HONOR cannot be used as first unvetted install. Avoid blind APK repack, permissions, spoofed signature, disabling Play Protect.
- Do not claim executable native UI until stable independent MAIN, resumed Activity and focused window coexist with 5 original split APK. Only then proceed read-only hook, single native player audio substitution, audible owner acceptance. Stage B independent mechanism must be reminded **after** real Stage A audio success and exact backup, not now.

## Safe rollback
- Before ARMv7 mirroring: `backup/android-a1-before-emulator-armv7-loader-mirror-20261111` @ `99c064cd3e2adddf58d92b39ec2afc52b6c0cdde`.
- Current safe diagnostic source: `backup/android-a1-emulator-armv7-mirror-native-crash-gate-20261111` @ `89de4fd6d0d58a2fcde51f44e034a91001a5b481`.
- Prior proved-linker error backup: `backup/android-a1-elf-machine-mismatch-proven-20261111` @ `8da1b888308bf7531485cd40e4d98b1907982b72`.
- Never modify accepted Android Test.50, Windows, browser extension, production, or user's HONOR while these experiments are NO-GO.


## Finalized crash buffer evidence: CI 42981555329 (11.11.2026)

[Actual run 42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329) finished **FAIL** because hard native MAIN/UI gate remains unsatisfied. All classifier/mirror static tests passed.

- **Standalone clone before original install:** exact MAIN PID from ApplicationExitInfo and matching debuggerd victim header; `native_main_signal=SIGSEGV`, `fatal_category=NATIVE_SIGNAL`, `native_backtrace_first_frame_group=LIBART`. Top 12 frame groups: `LIBART, LIBART, LIBART, LIBART, NATIVE_BRIDGE, OTHER, LIBART, LIBART, LIBART, LIBART, NATIVE_BRIDGE, OTHER`.
- **Clone alongside original signed 5 splits:** exact MAIN victim debuggerd match; `SIGSEGV`, first frame `LIBART`, `NATIVE_BRIDGE` appears further down. Original control process remains alive. No scoped `UnsatisfiedLinkError/dlopen failed`.
- Thus **native crash is confirmed**, and ART/native-bridge execution is involved. The precise instruction, ownership and root cause of the SIGSEGV remain unproven; frame groups do **not** prove faulty Android ART or faulty LSPatch. Not evidence for physical ARM64 behavior.
- Current emulator is not a valid stage-A UI/audio acceptance target for this pinned native-bridge LSPatch loader variant. Further random manifest/ZIP patches are not justified. Next meaningful gate is a **safe native ARM runtime** with no original-phone modification, if available, before owner preflight. No request for a second physical phone.
- Original one-APK clone is still separate, `sigBypassLevel=0`, signed with ephemeral lab signer, no module from competitors, no Play Protect setting changes, no code or audio released.
- Stage B reminder only after real audible A accepted with exact backup; **not due now**.

Current documented source+diagnostics after this note: `e7d160af2b63ee06aef027653fec54c45d9405d9` (previous HEAD; documentation advances it).
