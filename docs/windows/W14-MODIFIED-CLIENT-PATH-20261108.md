# W14 — CELIKOM Windows: modified-client delivery route, feasibility and safety plan

**W14 code checkpoint verified (2026-11-09):** real published PulseSync SDK addon **compiled** in [CI 42526627485](https://github.com/manufact-test/nomusic/actions/runs/42526627485), W14 source adapter **11/11**, previous W4–W12 regressions PASS. No official Yandex client installed, modified, launched or authorized. [First real-client isolated approval plan](W14-FIRST-REAL-CLIENT-TEST-PLAN-20261109.md).


**2026-11-08. Product-scope revision by owner following W13.** The owner now permits exploring an explicitly disclosed *modified* Yandex Music Windows client, as long as CELIKOM runs as a companion, Yandex retains its audio decoder/queue/controls and installation does not require users to disable Windows Defender, SmartScreen or any security setting. No official EXE/ASAR, accounts, server or production branch were changed by this document.

## Decision: W13 was a narrower NO-GO, not cancellation

W13 correctly stopped an **unaltered, officially integrity-protected Yandex 5.126.1.0 + independent external source bridge** approach with no exposed SDK. W14 **changes the input requirements**: optional mod installation is now allowed in product design *subject to reliable security, install/restore, rights and support*. Do not erase W13's W10 owner integrity facts: official app.asar is protected (V1 enabled / only ASAR enabled / PE hash match). Third-party mod installers may need to change signed client files or integrity resources; never do this silently or imply the original Yandex executable remains unmodified.

## Real immediately actionable technical lead

- [PulseSync-mod v2.1.5 release (2026-11-05)](https://github.com/PulseSync-LLC/PulseSync-mod/releases/tag/v2.1.5) has release text `Patch for Yandex Music 5.126.1` **but** also says `Версия спуфнута c 5.125.3 до 5.126.1`. This is *not proof of runtime support* for the user's installed official 5.126.1.0. Confirm on separately approved disposable test installation before choosing product architecture.
- [PulseSync-mod install instructions](https://github.com/PulseSync-LLC/PulseSync-mod) invoke the PulseSync Client to install its mod and reference `resources/app.asar`; it is a real modified-client route, not an undocumented extension in untouched official app.
- [FckCensor SDK bridge](https://github.com/Hazzz895/FckCensor/blob/main/src/sdk/bridge.ts) uses `@pulsesync/addon-sdk` and `api.client.setTrackReplacements(...)`: concrete source-substitution API in that third-party host. Still need to prove native pause/seek/next + CELIKOM authenticated signed Range source **in host running the target Windows version**.
- [PulseSync-mod LICENSE](https://github.com/PulseSync-LLC/PulseSync-mod/blob/main/LICENSE) is MIT. However [PulseSync-client LICENSE](https://github.com/PulseSync-LLC/PulseSync-client/blob/main/LICENSE) has noncommercial / redistribution/derivative restrictions (clauses 1.4, 3.1-3.3), automated updates and stated telemetry (6.2, 8.1). [PulseSync-client README](https://github.com/PulseSync-LLC/PulseSync-client) also warns about third-party mods using PulseSync without authorization. **MIT on the mod is not a blanket commercial license to the proprietary PulseSync Client, nor to Yandex binaries or music.** Commercial CELIKOM distribution needs written permission or a truly independent implementation and separate legal review.

## Target architecture

```
Official Yandex Music UI/queue/native audio decoder
                ↕
Versioned CELIKOM source adapter (installed as disclosed mod)
                ↕
CELIKOM Companion (tray, enable/disable, CELIKOM session, catalog)
                ↕
Existing CELIKOM backend: exact track ID / entitlement / signed audio Range
```

The customer launches Yandex + CELIKOM, not a second media player. Installer must clearly disclose that it modifies Yandex client, if it does, and provide verified repair/restore. When adapter incompatible, leave original playback alone and show Unsupported. No stealth process injection, account token extraction, disable Defender/SmartScreen, virus exclusions or evasion tricks.

## Engineering execution (large blocks, not W14–W99 synthetic fixtures)

**Block A — prove the third-party host on an isolated real official build.**
1. Read and audit PulseSync Client/mod install paths, SDK addon loading permissions, updater and data/telemetry behavior, exact package/version support and whether integrity/EXE/signature changes occur. Record expected AV/SmartScreen risk; no guarantee of zero warnings.
2. Prepare a byte-hash tracked, rollback-tested isolated Windows environment (VM or separate test user/machine), free of owner's existing authenticated Yandex process and user profile. An actual mod install requires a **separate precise approval** of installer/vendor/version/actions and risk, because W10 shows protected binaries. Never use owner account tokens in logs.
3. Once approved, test installer with the actual official 5.126.1.0, Yandex starts and normal playback works, then one CELIKOM-owned approved mapping with source substitution, Pause, Seek, Next, Stop, Original, update/restart and complete uninstall/repair. Use a dedicated test account/profile as practical; no CDP on an authenticated personal account. If setup fails or trips protection: stop; restore and record evidence.

**Block B — own product integration, not another loose demo.**
- If PulseSync commercial permission and host security are acceptable: implement a CELIKOM SDK addon with exact ID, per-device CELIKOM login, entitlement resolve, signed HTTPS Range streaming, cancellation/fallback, native single decoder and companion control/IPC.
- If license/telemetry/commercial dependency is unacceptable: investigate a CELIKOM-owned mod host built from compatible appropriately licensed components, with independent packaging, signing and rollback. This may be costlier and still requires transparent modification of the Yandex app. Do not treat PulseSync Client's restrictive license as MIT.
- Never use an independent playback clock. Reuse existing W4/W8 correctness contracts but gate success on actual installed-client audio behavior.

**Block C — consumer-grade release.**
- One guided, clearly branded CELIKOM installer/update/uninstall flow, signed CELIKOM components, provenance verified, native Yandex binary provenance explained, backups and byte-verified restoration, deny unknown Yandex updates rather than repatching.
- Validate on normal Defender + SmartScreen **enabled** Win10/Win11, with clean install/upgrade/restore testing and publisher reputation. Code signing improves authenticity/reputation but cannot guarantee no AV false positives or bypass signed-Yandex integrity issues.
- Independent licensing/privacy and distribution approval before paid launch. Users must not be instructed to switch off antivirus/Play Protect/SmartScreen.

## Current gate / owner action

**At writing: RESEARCH-READY, REAL HOST TEST NOT RUN.** W13 NO-GO remains valid only for the unmodified official-client method. No user installation recommended yet. Next is a concrete mod-host audit and test safety checklist, followed by *specific* owner consent to install only in an isolated environment. No new W0–W12 diagnostics and no fake synthetic success. If all variants require disabling security or unacceptable unsigned binary rewriting, stop that variant and escalate rather than conceal it.

Retain:
- `backup/windows-w11-verified-before-w12-20261108`
- `backup/windows-w12-verified-handoff-20261108`

Scope: `docs/windows/**` and later `windows-companion/**` on dedicated Windows branch. Browser, Android, backend and production untouched.
