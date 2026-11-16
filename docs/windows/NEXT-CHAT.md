# CELIKOM Windows — active handoff W163 (16 November 2026)

**Status: W163 0.24.45.0 source CI and Windows integration CI passed. One internal W20 owner-review package has been requested; wait for the artifact and provide only the standalone EXE to the owner.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W163 code checkpoint: `3b290931e2e1c9153f29a56e78cede45353fafbd`.
- W20 request commit: this handoff/request commit (will be recorded after push).
- Pre-W163 rollback: `backup/windows-main-pre-w163-owner-ui-transition-20261116` @ `0db016cbdcb939911ae3fd6ff71c2aa9af07c876`.
- App: **0.24.45.0**, native module **0.24.31**.
- Full details: `docs/windows/W163-OWNER-TRACK-TRANSITION-UI-POLISH-20261116.md`.

## Owner findings addressed

1. Add 18 px below the last visible track/status line before the Account card. The gap is attached to the last visible row, so it works for disabled, waiting, track-only and track-plus-status layouts without widening the gap between title and artist.
2. Large green Start copy is explicitly split after `Подождите, идёт подключение`, so `к приложению Яндекса.` begins line 2.
3. A short ID-less PLAYING/PAUSED heartbeat during a Yandex queue transition no longer clears the last current track metadata. It is retained for at most 9 seconds; a new valid track ID replaces it atomically. STOPPED, UNAVAILABLE and other non-transient states clear the track.
4. A stale heartbeat no longer displays a false Yandex connection-waiting message. The UI uses the last known playback state (`Музыка продолжает играть`, `Пауза`, etc.) or neutral `Проверяем состояние воспроизведения…`. The service dot remains gray without a fresh native heartbeat.
5. Active-version copy remains `Играет полная версия CELIKOM` and green only when exact native decoder-source proof is present. Mapping-only stays gray.

## Evidence boundary for green active status

The W54 diagnostic from 0.24.43.0 showed `HEARTBEAT_NATIVE_MAPPING_ACCEPTED`, `NativeDecoderUrlPropertyObserved=false`, `PlayerAudibleEventObserved=false`, and `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`. This does not prove that the CELIKOM decoder URL is the current audible source. The UI path already renders the agreed active label in green when `NATIVE_SOURCE_VERIFIED` + `ACTIVE_REPLACEMENT` are present. Do not force green from mapping-only evidence. If it remains gray on 0.24.45.0, use a fresh diagnostic and investigate the native decoder observer separately.

## W163 implementation and verification

- Bridge metadata survives short ID-less PLAYING/PAUSED transitions for up to 9 seconds; real Next replaces all fields, STOPPED clears them.
- Compact layout spacing is 18 px below the final visible track/status row.
- Start message uses an explicit newline before `к приложению Яндекса.`.
- Main and compact stale-heartbeat messages no longer claim that Yandex is waiting to connect.
- Main CI run `43871031471` — SUCCESS.
- Windows integration CI run `43871031480` — SUCCESS.
- W15 entitlement/login/native-state tests — SUCCESS, including ID-less transition, real Next replacement and STOPPED clearing.
- GUI compile with warnings as errors — SUCCESS.
- W22/W23/W60 VPN/audio regression suite — SUCCESS.
- Supervisor, installer metadata and rollback checks — SUCCESS.

## Owner-review package

- Requested version: `0.24.45.0`.
- Native module: `0.24.31`.
- Installer: `CELIKOM-W163-TRACK-TRANSITION-AND-UI-SPACING-02445-UNSIGNED.exe`.
- ZIP and SHA256 are retained inside the private CI artifact for integrity; give the owner **only the EXE link**, not the ZIP or checksum file.
- Internal unsigned owner-review build only. Not a production release, not signed, not deployed to Hostinger or a public update feed.

## Owner's manual check

Install 0.24.45.0 over 0.24.44.0 and check:
- 18 px spacing under the disabled and waiting status text before the Account card.
- Large green Start message wraps with `к приложению Яндекса.` on line 2.
- Switching to the next song does not flash a false Yandex connection-waiting message; title/artist update to the next track without clearing the whole block.
- Active-version label is green only if exact decoder proof is present; mapping-only stays gray.
- Existing VPN continuity remains unchanged. Do not repeat broad VPN/audio testing unless a regression is reported.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No W23 native host/renderer, audio pipeline, VPN recovery or entitlement changes in W163. No broad audits or intermediate installers. Preserve the pre-W163 rollback branch.
