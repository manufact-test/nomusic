# W80 — CELIKOM Windows survives reviewed Yandex vendor updates (12.11.2026)

> **Owner Windows 0.24.25 is reported "вроде бы работает"; long-audio QA tomorrow. DO NOT overwrite working owner installation before he confirms baseline.** W80 is an isolated experimental build, not a claim that unknown future vendor builds will necessarily work.

## Exact source and reserves

- Working: `experiment/windows-w80-vendor-update-auto-reconnect-20261112` from safe W79 `7fc0440945003fe825349ac61011bf4bf3aac179`.
- Exact before-work reserve: `backup/windows-w80-pre-vendor-auto-update-exact-20261112` (same commit).
- Prior owner-accepted experimental Windows 0.24.25 reserve: `backup/windows-w79-02425-emergency-recovery-ci-green-20261112`.
- New candidate GUI 0.24.26, **native host and renderer scripts are intentionally unchanged at 0.24.25**. Installer updates GUI and its local managed native integration manager, not currently active patched Yandex. Native pair is rewritten only when a real approved vendor change is detected on an explicit Start.
- Native Yandex source/patch belongs to `NativeIntegrationManager` and recovery `PairRecovery`. No changes to Android, extension, server, media bridge or audio handler.

## Why future updates broke CELIKOM

Old W79 `Inspect` classified a manifest `ACTIVE` + current Yandex official new EXE/ASAR as `Changed`, and hardcoded support for 5.126.1 / 5.127.0. Yandex updater can replace BOTH host files independently of CELIKOM. W77's old `Restore -> Install` was unsafe; W79 already replaced it with transaction-like `Upgrade`. W80 extends this without undoing W79.

## What is implemented

1. **Data-only, reviewed build catalog**, `OfficialYandexCatalog.cs`. Read-only HTTPS from:
   `https://raw.githubusercontent.com/manufact-test/nomusic/support/windows-yandex-compatibility/windows-companion/w24/compatibility/official-yandex-builds-v1.json`
   Branch `support/windows-yandex-compatibility` was created and contains **only proven official 5.127.0** as initial entry. Catalog is strictly bounded, schema/purpose and duplicate checks, immutable known hashes, no executable code, no scripts, 4-second timeout, 15-minute refresh. Offline still permits built-in 5.127.0; unknown builds remain blocked. New builds can be added centrally after signed original EXE and ASAR exact hashes + ASAR image build + runtime acceptance, **without requiring CELIKOM EXE distribution**.
2. **Full vendor trust gate**: matching exact FileVersion, SHA256 of both current EXE and app.asar, Windows Authenticode validity and signer `CN=YANDEX LLC, O=YANDEX LLC`. Any unsigned, unknown, half-updated, mismatching or altered file causes refusal. Feed does not allow arbitrary files.
3. **Already ACTIVE → official vendor replaces both**: `NativeIntegrationManager.Inspect` recognizes `VerifiedVendorUpdate` only for an *exactly pinned signed official pair*, even when old manifest remains `ACTIVE`. A new `Install` snapshots the new official pair separately, preserving all old backups as `NativeHost/previous-*`; no restore-first, and no overwrite of unrecognized bytes.
4. **Reconnection UX**: MainWindow periodically read-only scans when in tray and immediately disables stale bridge on verified vendor replacement. On the user's next actual **Start**, if prior manifest was `ACTIVE` and new vendor pair is approved, reuse prior native consent and reattach without a second confirmation modal or new CELIKOM installer. If it was `RESTORED` before update, explicit initial consent is retained. Live entitlement revalidation is still mandatory.
5. **Unknown future update**: fail-closed with calm message `Новая версия пока проходит проверку`; no attempts to force patch, downgrade Yandex, delete DPAPI or originals. Once that exact build is verified and added to central feed, connected users can reconnect without installing GUI updates.

### Honest limitation

This is not a guarantee of unconditional 100% uptime. A Yandex change that breaks the native injection contract still requires compatibility work and verification. Pinning an official signature and hash is a security identity check, **not** proof of audible functionality. Unknown versions are not patched automatically just to preserve optics. Continuous vendor compatibility monitoring and proof publication remain a developer responsibility; never auto-publish untested new vendor hashes.

## Test coverage and deployment gate

- W80 `windows-w80-vendor-compatibility-gate.yml`: real HTTPS feed matches GitHub-reviewed source, invalid/modified feed rejects, current DPAPI and entitlement tests, old stable native snapshots/crash rollback, GUI compiles warnings-as-errors, destructive Restore/Install guard.
- W80 `windows-w80-official-auto-reconnect-lab.yml`: download exact official signed 5.127.0 Yandex only to disposable Windows runner; prove actual native image builder works; recreate former `RESTORED` owner state, native install/upgrade/restore; simulate **ACTIVE** previously patched Yandex then vendor overwrites only EXE → `Changed` safe refusal, then both official EXE+ASAR → `VerifiedVendorUpdate`, old-user Start auto-reattaches, exact backups archived. No executable Yandex installer launched, and no vendor binary artifact published.
- W80 `windows-w80-auto-vendor-installer.yml`: build candidate GUI 0.24.26 with byte-identical 0.24.25 native assets, prior W79 0.24.25→ W80 0.24.26 in-place Inno proof, DPAPI saved login encryption and hash unchanged, same AppId, official Yandex directory untouched. **No owner install until physical QA decision.**
- **Do not mark production fixed** until owner confirms future real updater event, native Active, Yandex opening, and audible playback. Owner will check 0.24.25 audio separately tomorrow.

## Verified final W80 0.24.26 candidate (2026-11-12)

- **Real signed Yandex 5.127.0 lab PASS:** https://github.com/manufact-test/nomusic/actions/runs/43293978441 (full prior-RESTORED and newly ACTIVE→vendor-update→safe-reconnect lab using genuine official signed EXE + ASAR).
- **Reviewed HTTPS feed + W21/W24/W15 GUI/DPAPI checks PASS:** https://github.com/manufact-test/nomusic/actions/runs/43293623731, including live retrieval from the pinned support GitHub branch and exact hash equality with reviewed catalog.
- **W80 0.24.26 candidate installer PASS:** https://github.com/manufact-test/nomusic/actions/runs/43294151762. Native host.cjs and renderer.js from 0.24.25 remain unchanged; Inno 0.24.25→0.24.26 installs in place with one AppId, encrypted DPAPI login unchanged/decryptable, and Yandex host directory not touched.
- Artifact [CELIKOM-W80-AUTO-VENDOR-COMPATIBILITY-UNSIGNED](https://github.com/manufact-test/nomusic/actions/runs/43294151762/artifacts/13977289582), Windows installer SHA256 `1AE9698109AAAA01A65D3409CD8CD95186274277AE5A76C925AA455E0C1FC849`. This is an **owner-test candidate only**, not a mandatory update. Do not install on owner machine until baseline 0.24.25 has had its next-day music test.
- **Important limitation**: no tests can guarantee that future as-yet-unknown Yandex releases preserve runtime compatibility. Only a signed Yandex-publisher, exact SHA pair published in the reviewed compatibility catalog is eligible for automated recovery on Start; otherwise preserve all data and block unsafe operations.

