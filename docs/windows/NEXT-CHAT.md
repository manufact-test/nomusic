# CELIKOM Windows — NEXT CHAT (W102, 2026-11-13)

Read first: [W102 — single production line, Yandex 15-minute monitoring and complete work order](W102-SINGLE-PRODUCTION-LINE-YANDEX-15MIN-AND-WORK-ORDER-20261113.md).

The owner wants ONE original CELIKOM Windows product, not parallel TEST apps or repeated interim installers. Before substantial edits, create an exact backup of the current production commit. Backups are rollback points only. Work on one canonical production line and produce one coherent next release.

## Critical source reconciliation

GitHub default `main` at `2741c403772f6e2837cd27bf748f90dc8d7722c9` did not contain `windows-companion/` or `docs/windows/`. Windows application source is on `experiment/windows-w98-integrated-gain-and-original-vpn-20261113` at `0158fcf71d06e4784751b8ddc1982e2b951b2753`. These histories are diverged (main→W98: ahead 2661 / behind 41). Do not blindly merge all history, reset main or continue experiment branches as permanent product lines. Inspect merge base and trees, then safely integrate only the Windows source into one canonical production line while preserving Android, extension and server code.

Exact backups already created:
- `backup/windows-main-pre-w102-handoff-20261113` @ `2741c403772f6e2837cd27bf748f90dc8d7722c9`
- `backup/windows-source-pre-w102-handoff-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`

## Current release state

- Windows code baseline GUI 0.24.36 / native 0.24.29 / W23 0.24.10 @ `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- Windows CI [43500415302](https://github.com/manufact-test/nomusic/actions/runs/43500415302): SUCCESS.
- Hostinger/final release [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358): FAILURE at isolated MySQL restore/audit. Gain stage, final installer and publication skipped. Inspect logs and actual server state before retry.
- Previous run [43495186951](https://github.com/manufact-test/nomusic/actions/runs/43495186951) did pass live gain sidecar staging for Big City Life, track 40371622, configured +11.5 dB, measured +6.70 dB RMS with peak limited to 0 dB, signed Range 206 / gain_applied=true.
- No final EXE/ZIP from the failed latest run; no owner PC install.

## Work order

1. Reconcile the Windows source into one canonical production line; no blind merge.
2. Diagnose the MySQL restore/audit failure in run 43500415358; no blind deploy.
3. Close sequentially: VPN reconnect; #52 «Ты» audible replacement; #53 Brave/Windows stalls; #54 Big City Life mid-track volume drop; #56 admin gain; #57 403→206 hiss; #58 original songs/My Wave on VPN switch. Keep #54/#56/#57 separate.
4. Finish earlier startup items: W74 first-start retry; W75 persistent diagnostics; W87 no-flash/quiet module repair; W88 default tray autostart and remembered opt-out.
5. Change Yandex vendor discovery from hourly to every 15 minutes (suggested cron `7,22,37,52 * * * *`), split quick discovery from long candidate validation, and add immediate app-side compatibility checks on startup, local Yandex version change and bridge failure. Keep official signature/hash/runtime gates. Current main workflow checks out stale W81 experiment branch; remove this dependency.
6. Implement signed automatic CELIKOM app updates, safe in-place installation, post-update health checks, and exact local/remote rollback. Current app updater is manual staff-only local ZIP/EXE selection, not automatic.
7. Deliver one coherent next version of the same app to the owner. Owner installs it once and checks it. Fix any findings on the same production line.
8. After owner acceptance, publish the signed stable update feed for mass rollout. Legacy clients without updater need one bootstrap update; future fixes should arrive in-app.

No new accounts/emails/secrets. No remote install. No intermediate installers. No TEST product. No claims of audio fixes based on CI alone. See W102 for complete status and closure conditions, and W101 for the detailed updater security/rollback design.
