# CELIKOM Windows W79 — recovery of broken 0.24.24 on signed Yandex 5.127.0 (12.11.2026)

**Owner status: NOT YET PHYSICALLY CONFIRMED.** Do not claim working audio until owner runs Start and hears a replacement on the physical machine. This is an emergency repair of a previously working product, not a new roadmap or rewrite.

## Original incident, no more owner diagnostics needed

- Incident issue: https://github.com/manufact-test/nomusic/issues/44
- Authoritative owner handoff: `docs/windows/W78-OWNER-YANDEX-51270-UPGRADE-BLOCKER-HANDOFF-20261112.md`.
- Owner CELIKOM 0.24.24, Yandex `5.127.0.r22015925`, manifest `RESTORED`, both original 5.126.1 backups valid; currently installed EXE and ASAR disagree with legacy snapshot. Logs: `NATIVE_RESTORE_OK -> NATIVE_UPGRADE_FAILED -> START_HOST_PREFLIGHT_BLOCKED`.
- **Never** run legacy `Restore()->Install()` on active native host; this caused the regression. Do not reinstall Yandex, erase saved DPAPI, or overwrite unknown host files.
- 0.24.23 still exists as fallback installer but does **not** enable Yandex 5.127.0 compatibility by itself.

## Provenance of new official Yandex version

Downloaded **only to an ephemeral Windows GitHub runner**, via Yandex's official distribution origin:
`https://music-desktop-application.s3.yandex.net/stable/Yandex_Music_x64_5.127.0.exe`.

- Installer Authenticode valid, signer `YANDEX LLC`, SHA256 `24E15BCB83984633ED362D329B3E103FDB270515BE2E48EBCA316091C5A0DBAE`.
- Vendor EXE extracted from inner `$PLUGINSDIR/app-64.7z`: Authenticode valid, signer `YANDEX LLC`, FileVersion `5.127.0.r22015925`, SHA256 `DE2849A1378DAFF16500FD5C8499634AAB8D994C1FFB1B1D8A6BC264EDD9AADA`.
- Vendor `resources/app.asar` SHA256 `C176FF3CECDDDFAB76B2D0D90BF527BBED226919FAB37F5723B46913084620CB`.
- Lab CI: https://github.com/manufact-test/nomusic/actions/runs/43287570569 (signed official files), https://github.com/manufact-test/nomusic/actions/runs/43287830492 (build integration using **actual** signed 5.127.0 EXE + ASAR, integrity replacement count 1), https://github.com/manufact-test/nomusic/actions/runs/43288778724 (**PASS**: owner RESTORED/changed state -> signed 5.127 official -> native Active -> native Upgrade -> exact 5.127 Restore). No actual Yandex installer executed and no vendor binaries published.

## Surgical fix

Working branch `experiment/windows-w79-upgrade-transaction-recovery-20261112`.
- Pre-work exact backup `backup/windows-w79-pre-transaction-exact-20261112` at `87c470c0d73e2694365c40db822286073839fde3`.
- Tested before-version-bump backup `backup/windows-w79-51270-real-owner-state-ci-green-20261112` at `64dc3b5906f241a0ab47be163cdd328eed2fe1ce`.
- Candidate emergency GUI/native version `0.24.25`, Inno package `CELIKOM-W79-51270-EMERGENCY-RECOVERY-UNSIGNED.exe`; only distribute after CI checks.

1. `NativeIntegrationManager.Inspect` recognizes `VerifiedVendorUpdate` only for **RESTORED legacy snapshot + full exact official signed 5.127 EXE/ASAR pair**. Any unknown or partial vendor update remains `Changed` and cannot modify host.
2. `YandexHostProbe` validates actual 5.127 version, Authenticode signature, pinned EXE hash and ASAR hash. Does **not** add 5.127 to unverified version allowlist.
3. Explicit owner-approved Start can `Install` against the official 5.127 pair: stage two verified patched images first, archive old 5.126 snapshot as `NativeHost/previous-<guid>`, create new exact 5.127 snapshot, apply both with W21 recovery. Failed pre-capture rolls the old snapshot directory back to its original path. Never overwrite previous original backups or session.dpapi.
4. For an already ACTIVE native pair, `MainWindow.ConnectYandexAsync` and `CompleteApplicationUpdateAsync` now call `NativeIntegrationManager.Upgrade`, **not** `Restore() -> Install()`. `PairRecovery.UpgradeStaged` archives the previous patched pair under `snapshot/upgrades/<guid>`, records `UPGRADING` intent before any host writes, swaps only hash-verified known bytes, and can roll back a partially upgraded known pair. If third-party updater changes any byte, rollback refuses to overwrite it.
5. Existing audio behavior, extension, server, Android, sessions, payment and login flows untouched.

## Verification and owner procedure

- Windows backup/interruption/refusal + native builder + GUI/DPAPI compile/test: https://github.com/manufact-test/nomusic/actions/runs/43288711475 **PASS**.
- Real signed 5.127 and exact owner-state rehearsal: https://github.com/manufact-test/nomusic/actions/runs/43288778724 **PASS**, including installer-produced real ASAR patch, refreshed native module and restoration of exact Yandex 5.127 original bytes.
- Post-bump official 5.127 rehearsal and 0.24.24→0.24.25 actual Inno installer/DPAPI same-AppId test: check `.github/workflows/windows-w79-official-51270-readonly.yml` and `.github/workflows/windows-w79-51270-emergency-installer.yml` latest runs before owner handoff.
- Physical owner: **do not uninstall/reinstall Yandex or delete backups**. Once the signed-provenance recovery installer is fully CI-green, run it over existing CELIKOM 0.24.24, open CELIKOM, press Start and confirm native 0.24.25 Active and music playback. If still Changed, stop, retain all files, do not force fallback or resubmit generic diagnostics; compare exact official 5.127 hashes.
- Real song-specific work (Kishlak 102494056, 13 КАРАТ 106040459, Big City Life 40371622) is paused until owner confirms **real audible** native playback.
