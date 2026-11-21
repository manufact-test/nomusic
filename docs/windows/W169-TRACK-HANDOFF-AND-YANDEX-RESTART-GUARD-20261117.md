# CELIKOM Windows W169 — next track UI + Yandex main-process resilience
Date: 2026-11-17

## Exact state
- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`
- Owner installed W168 / app 0.24.50.0; owner confirms green positive statuses now work and must not regress.
- Pre-W169 backup: `backup/windows-w169-pre-track-handoff-crash-investigation-20261117` @ `92e0d9e63f5fd7dc7f243d7c2a2202cf5ad8b2de`
- W169 UI commit: `1ac135ba5312473cc6c7feca8d1f5f57726f5342`
- W169 Electron exception-safety commit: `b2f9131132e26020fd861dcb71d3c33b8ff9a0c1`
- App 0.24.51.0. Native module now **0.24.32** because real host.cjs code changed; previous native 0.24.31. Existing safe install/upgrade must be used. Never update Yandex original files outside the existing exact-image native upgrade.
- main untouched; W167/W168 backups preserved.

## User acceptance goal
1. Switching tracks should retain previous title, artist and status through a brief metadata/ID gap; no blank or spurious “Пауза”, recovery, search, or disconnected text while the music actually switches normally. Must still display genuine Stop, player loss and VPN/server recovery; do not alter existing W164 recovery.
2. Yandex desktop occasionally closes and reopens itself at track end. Owner provided W54 logs from 0.24.49, confirmed the host reinitialization at 2026-11-17 08:13:54 UTC. A direct initiating CELIKOM reload is **not** in the logs. This is not the VPN behavior; VPN changes are accepted and must not be touched.
3. Preserve approved-available green and connected-paused green from 0.24.50 and exact decoder proof for active replacement.

## Targeted changes
- W169 compact UI only: bounded 2.5-second previous-title/artist/status retention for valid new ID without metadata and brief invalid track ID. Preserve account, upload restrictions and real errors; do not show the first-play idle prompt again after a track has been observed. Regression tests for gap, stop, VPN, stale heartbeat, host error, and expiry.
- W169 native host 0.24.32: unhandled rejection from fire-and-forget `tick(view)` might terminate Electron's main process on exceptional responses. All three native relay entry points now use `scheduleTick(view)` with a rejection catch. CDP “message” callback also catches unexpected event payload exceptions, drops source proof and records `NATIVE_CDP_EVENT_EXCEPTION`, never invoking Yandex controls or restarting it. A synthetic malformed CDP event regression test is included.
- Native 300ms relay, URL/source decisions, media/reloadEntity behavior, CDP commands, VPN network recovery and all server/auth logic **unchanged**.

## Evidence boundary
Uncaught Electron async/callback errors were a real unsafe code path, now guarded. **Owner's particular restart is not proven to have been caused by that path** because prior diagnostics have no OS crash reason, process exit code or Yandex updater history. CI passing cannot establish that Yandex will never restart. If it recurs, correlate the exact wall-clock timestamp with Windows Application Error 1000 / Windows Error Reporting 1001 and Yandex's own update log; inspect `native-events.log` for new `NATIVE_RELAY_TICK_EXCEPTION` / `NATIVE_CDP_EVENT_EXCEPTION`. Never invent a resolved root cause.

## Review required
W20 internal unsigned owner build; no production deployment. Validate no build regressions, new native module upgrade is exact and safe, first Start works, user green statuses intact, Next does not flicker, no VPN/audio regression, then prolonged runtime check for Yandex unexpected restart.
