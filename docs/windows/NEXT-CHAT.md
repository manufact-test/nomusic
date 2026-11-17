**W169 VERIFIED BUILD (owner review pending):** W20 run `44071025539` SUCCESS, source `c717428a7d9f01fc8e33b482fcf66a9ed1a02947`, app `0.24.51.0` and native `0.24.32`. EXE/ZIP/SHA256 independently verified and present in Library `/CELIKOM/W169/`. Prior 0.24.50 and rollback kept. Next test is actual Yandex runtime; restarts not yet proven eliminated. Full details in W169 document.

# CURRENT WINDOWS W169 (17 November 2026)

Read **`docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md`** before any other Windows history. Active source: UI `1ac135ba5312473cc6c7feca8d1f5f57726f5342`, native exception guards `b2f9131132e26020fd861dcb71d3c33b8ff9a0c1`. App **0.24.51.0**, native **0.24.32**, backup `backup/windows-w169-pre-track-handoff-crash-investigation-20261117` @ `92e0d9e63f5fd7dc7f243d7c2a2202cf5ad8b2de`. Owner says green status in 0.24.50 works; preserve it. No VPN modifications. **Actual Yandex restart mechanism not proven by old diagnostics; guards eliminate unsafe unhandled Node rejection/callback failure but runtime owner must confirm.**

---

# CELIKOM Windows — active W168 handoff (17 November 2026)

**W168 delivered for owner review:** W20 run `44051448677` SUCCESS; 0.24.50.0 owner installer/ZIP/SHA256 independently checked and verified in personal Library `/CELIKOM/W168/`. The Yandex spontaneous restart is STILL UNRESOLVED; see dedicated W168 incident doc. No audio/VPN/native module changes.

**CURRENT OWNER BUGS, not W167 stale instructions:** Read `docs/windows/W168-OWNER-THREE-ISSUES-20261117.md` FIRST. Owner has 0.24.49.0 and supplied two W54 diagnostics. W168 UI fixes committed at `2c352479b267266cd62fab7d8221bab97051c539` for (1) idle prompt after Start, (2) green available/paused labels without false audible claim. Proposed 0.24.50.0, native still 0.24.31. W168 backup: `backup/windows-w168-before-owner-three-fixes-20261117` @ `31e364bfba8795f84502f050d6716b2b6639f5cf`. **Third issue (actual Yandex main-process restart 08:13:54Z) diagnosed but root cause NOT proven; do not call it repaired or touch VPN/audio/host speculatively.** W167 documentation below is historical.

---

# CELIKOM Windows — active handoff W167 (16 November 2026)

**Status:** W167 UI fixes are committed on the W165-based branch. The single internal W20 owner-review package is being prepared; CI and owner runtime acceptance are still pending. W166 / 0.24.48.0 remains rejected and was not used as the implementation base.

## Exact repository state

- Repository: `manufact-test/nomusic`
- Product: **CELIKOM Windows only**
- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`
- W167 source checkpoint: `e88280740457bf539ec8e661416a26d9de1e1102`
- CI validation checkpoint: `8964ec124025cf2f480c0f913f5b7b2d69a90f00` (Main CI and Windows integration CI both succeeded).
- App version: **0.24.49.0**
- Native module: **0.24.31**
- Rollback branch before W167 fixes: `backup/windows-w167-pre-ui-fixes-20261116` @ `ea788eaed198b71db787215b9ba85829766d6062`
- W165 code baseline: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`
- Original pre-W166 backup: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`
- Main/W166 was not reset, force-pushed or modified by W167.

## W167 implementation

1. **Start / module refresh:** `StartAction` no longer clears `_compactStarting` before `ConnectYandexAsync`. The green Yandex connection banner remains visible through the existing module validation and upgrade. Startup completion is blocked while native integration is busy or the installed module still mismatches. If the initial consent prompt is declined, the banner is cleared. The real version check, upgrade, entitlement checks and fail-closed behavior remain intact.
2. **Transient waiting copy:** the fresh-heartbeat + `UNKNOWN` fallback now returns an empty track row. The same old waiting copy was removed from the legacy `_switchHint`, `_song` and service-status fallbacks. W164's 2.5-second previous-title/artist handoff, raw Track-ID suppression and pending-presence suppression are unchanged.
3. **Pause:** `Пауза` is neutral in both compact and legacy UI. The header connection dot/label still follow the independent fresh native-service heartbeat and may remain green.
4. **Active replacement:** the green predicate is centralized and remains strict: enabled bridge, fresh heartbeat, `ACTIVE_REPLACEMENT`, current `PLAYING`, `NATIVE_SOURCE_VERIFIED`, and approved presence. Mapping, HTTP 206, prefetch, entitlement or generic PLAYING cannot turn the label green. No W166 DOM observer was copied; no current W55 diagnostic was supplied to justify it.
5. **Spacing:** idle/disabled placeholder remains 18 px. Active status uses a 28 px row and 2 px lower gap before Account. No global window, title, artist or idle spacing changes.
6. **Scope:** no W23 native host/renderer, audio, VPN, source routing, server, auth, Android or browser-extension code changed.

## Verification and package — all CI passed

- Main CI: [run 43903409504](https://github.com/manufact-test/nomusic/actions/runs/43903409504) — **SUCCESS**.
- Windows integration CI: [run 43903409454](https://github.com/manufact-test/nomusic/actions/runs/43903409454) — **SUCCESS**.
- W20 safe installer staging: [run 43903271312](https://github.com/manufact-test/nomusic/actions/runs/43903271312) — **SUCCESS**.
- W20 source commit: `025a51d7478b3c7591f893a5dc55fd8ecfee7bdc`; it contains the full W167 source checkpoint above. Latest branch HEAD differs only by branch-scoped CI trigger configuration and this documentation update.
- W15 contract tests: `W15_NATIVE_CONTRACT_PASS 436`; W23 native tests and W24 native image-builder tests passed.
- W20 passed warnings-as-errors compilation, stage-only policy, PE file-version/identity and anti-downgrade validation, disposable install, same-AppId in-place upgrade, uninstall without touching Yandex, and one-installer ZIP/SHA256 checks.
- One internal unsigned owner-review package only:
  - Installer: `CELIKOM-W167-OWNER-UI-REGRESSIONS-02449-UNSIGNED.exe`
  - ZIP: `CELIKOM-Windows-0.24.49.zip`
  - SHA256 manifest: `SHA256SUMS.txt`
  - EXE SHA256: `f363a23b90a58268d31f2c5a34313f35510645ab34bcf2c9acfcc3521b14a852`
  - ZIP SHA256: `abd7ab026a6dcfa7532f4aa833c7db2c4bf93c81e76c17afa001b941dfa15f0e`
  - GitHub Actions artifact ID: `14242836055`; expires **26 November 2026, 16:06:19 UTC**.
- ZIP contains exactly one root installer, byte-identical to the standalone EXE. Both hashes were independently recalculated after download and matched the manifest.
- Verified Library files: `/CELIKOM/W167/` (installer, ZIP and SHA256 manifest). Use the Library copies for download, not a sandbox or direct Actions artifact link.
- Package is internal and unsigned; no production signing, public feed, deployment or owner acceptance is claimed.

## Owner manual check

1. Press Start with the module requiring refresh: green Yandex connection text appears immediately; no disabled-state copy or idle module-update hint appears during the operation.
2. Let Yandex open and press Next: no `Ожидаем воспроизведения в Яндекс Музыке…` flash; previous title/artist handoff remains stable and no raw Track ID or pending-presence copy appears.
3. When the current replacement is genuinely active, `Играет версия CELIKOM` is green only if exact current-source proof is present. If the owner hears the replacement but the label remains neutral, collect a fresh W54/W55 diagnostic from 0.24.49.0; do not weaken the proof gate.
4. Pause is neutral while the header connection indicator may stay green.
5. Active status-to-Account spacing is compact; disabled/placeholder breathing room remains.
6. No broad VPN/audio retest is required; those paths were accepted in W164 and remain untouched.

## Hard boundaries

Do not start from W166. Do not reset or force-push main. Do not alter audio, VPN, source routing, server, entitlement authority, updater architecture, Yandex files, Android or browser extension. No broad audits, speculative hooks or intermediate packages.
