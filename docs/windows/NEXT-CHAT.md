# CELIKOM Windows — active handoff W164 (16 November 2026)

**Status: W164 0.24.46.0 source CI, Windows integration CI on the code checkpoint, and one internal W20 owner-review package passed. Package bytes and SHA256 checksums verified. Owner manual VPN/track-transition acceptance is pending.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- Code checkpoint: `2b7fb2d3627c27c1ec9052e49b7abdb49b87429e`.
- W20 package request commit: `98bb24a3081e616e8a4767323bbc685cf1b2ecde` (request file only; no code change).
- Exact pre-W164 rollback: `backup/windows-main-pre-w164-vpn-route-debounce-track-ui-20261116` @ `b5538b6bdbb62eeeaef74c57e10d0fe5a075af7a`.
- App: **0.24.46.0**, native module **0.24.31**.
- Full handoff: `docs/windows/W164-OWNER-VPN-RECOVERY-TRACK-TRANSITION-20261116.md`.

## W164 changes

1. VPN recovery now coalesces delayed adapter events across an 8-second burst, waits 3 seconds after the last route signal, uses a 5-second quick authenticated GET within an 8-second fast-route window, and clears the route hint after success. Normal 15-second healthy polling is restored. No offline entitlement or bypass.
2. Header text is fixed to **«Связь»**, size and vertical alignment fixed. A pending route check alone does not gray a still-live native heartbeat. Real bridge/heartbeat loss may still be gray.
3. On Next, previous title/artist are retained for at most 2.5 seconds while new metadata arrives. Raw Track ID and the transient «Проверяем версию песни CELIKOM…» line are no longer displayed.
4. Exact decoder-source proof for green active replacement remains unchanged. A source-held event/mapping is not proof of audible output.

## Verification

- Main CI [43878114276](https://github.com/manufact-test/nomusic/actions/runs/43878114276) — SUCCESS.
- Windows integration CI [43878114256](https://github.com/manufact-test/nomusic/actions/runs/43878114256) — SUCCESS on code checkpoint.
- Main CI after package request [43878846340](https://github.com/manufact-test/nomusic/actions/runs/43878846340) — SUCCESS.
- W20 package staging [43878846320](https://github.com/manufact-test/nomusic/actions/runs/43878846320) — SUCCESS, including W15/native tests, GUI warnings-as-errors, PE/version checks, install/upgrade/uninstall smoke and exact EXE/ZIP packaging.
- EXE SHA256: `451e8614a73bf20a446eeae72625715756c458b077e4274d004f8c7aa62a4054`.
- ZIP SHA256: `5578b2854be1f874c07260fc85097c2a80b1de35ddeebb5c3729222737bdd1d0`.

## Owner-review package

- Installer: `CELIKOM-W164-VPN-RECOVERY-AND-TRACK-TRANSITION-02446-UNSIGNED.exe`.
- Artifact ID: `14231891556`.
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43878846320/artifacts/14231891556
- Expires: 26 November 2026, 13:48:22 UTC.
- One internal unsigned owner-review build only; no production release or deployment.

## Owner manual acceptance

Install 0.24.46.0 over 0.24.45.0. Test a VPN toggle during playback and several Next transitions. Confirm the header stays centered, the recovery message clears promptly after server access returns, and no Track ID / presence-check text flashes. Do not force the active replacement label green without exact decoder proof. If it stays gray while the owner hears a CELIKOM version, collect a fresh W54 diagnostic for the native decoder observer.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, W23 native host/renderer, audio engine, entitlement authority or updater architecture changes. No broad audits, intermediate installers, production signing or deployment.
