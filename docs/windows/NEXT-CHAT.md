# CELIKOM Windows — active handoff W163 (16 November 2026)

**Status: W163 0.24.45.0 source CI, Windows integration CI and one internal W20 owner-review package all passed. The standalone EXE is ready; owner manual check pending.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W163 code checkpoint: `3b290931e2e1c9153f29a56e78cede45353fafbd`.
- W20 package/docs commit: `57b826ed2431febb2fad31198897d94bd4cc1648`.
- Pre-W163 rollback: `backup/windows-main-pre-w163-owner-ui-transition-20261116` @ `0db016cbdcb939911ae3fd6ff71c2aa9af07c876`.
- App: **0.24.45.0**, native module **0.24.31**.
- Full details: `docs/windows/W163-OWNER-TRACK-TRANSITION-UI-POLISH-20261116.md`.

## Owner findings addressed

1. Added 18 px below the last visible track/status line before the Account card. The gap is attached to the last visible row, so it works for disabled, waiting, track-only and track-plus-status layouts without widening the gap between title and artist.
2. Large green Start copy is explicitly split after `Подождите, идёт подключение`, so `к приложению Яндекса.` begins line 2.
3. A short ID-less PLAYING/PAUSED heartbeat during a Yandex queue transition no longer clears the last current track metadata. It is retained for at most 9 seconds; a new valid track ID replaces it atomically. STOPPED, UNAVAILABLE and other non-transient states clear the track.
4. A stale heartbeat no longer displays a false Yandex connection-waiting message. The UI uses the last known playback state (`Музыка продолжает играть`, `Пауза`, etc.) or neutral `Проверяем состояние воспроизведения…`. The service dot remains gray without a fresh native heartbeat.
5. Active-version copy remains `Играет полная версия CELIKOM` and green only when exact native decoder-source proof is present. Mapping-only stays gray.

## Evidence boundary for green active status

The W54 diagnostic from 0.24.43.0 showed `HEARTBEAT_NATIVE_MAPPING_ACCEPTED`, `NativeDecoderUrlPropertyObserved=false`, `PlayerAudibleEventObserved=false`, and `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`. This does not prove that the CELIKOM decoder URL is the current audible source. The UI path already renders the agreed active label in green when `NATIVE_SOURCE_VERIFIED` + `ACTIVE_REPLACEMENT` are present. Do not force green from mapping-only evidence. If it remains gray on 0.24.45.0, use a fresh diagnostic and investigate the native decoder observer separately.

## W163 verification

- Main CI run `43871031471` — SUCCESS.
- Windows integration CI run `43871031480` — SUCCESS.
- Main CI after W20 request/docs commit run `43871613360` — SUCCESS.
- Windows integration CI after W20 request/docs commit run `43871613282` — SUCCESS on attempt 2 (first attempt had a transient supervisor named-pipe closure; rerun passed).
- W15 bridge/state tests, GUI compile with warnings as errors, W22/W23/W60 VPN/audio regression suite, supervisor and installer checks — SUCCESS.
- W20 safe installer staging run `43871613198` — SUCCESS.
- No production signing, stable feed or deployment.

## Owner-review installer

<badge>Internal unsigned owner-review build</badge>

- Version: `0.24.45.0`
- Native module: `0.24.31`
- Installer: `CELIKOM-W163-TRACK-TRANSITION-AND-UI-SPACING-02445-UNSIGNED.exe`
- Artifact ID: `14227453095`
- Artifact name: `CELIKOM-Windows-internal-stage-57b826ed2431febb2fad31198897d94bd4cc1648`
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43871613198
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43871613198/artifacts/14227453095
- EXE SHA256: `e393cfa33d0399856a263e00f260a9ba227dc1d4407e02a4f6582f6733913a54`
- Artifact expires: 26 November 2026, 13:02:35 UTC.

The artifact contains the standalone EXE, one ZIP containing that exact same EXE, and SHA256SUMS.txt. The EXE hash matches the checksum file; the ZIP contains exactly one root installer and byte-for-byte matches the EXE. **Give the owner only the standalone EXE link**, not the ZIP or checksum file.

## Owner's manual check

Install 0.24.45.0 over 0.24.44.0 and check:
- 18 px spacing below the disabled and waiting status text before the Account card.
- Large green Start message wraps with `к приложению Яндекса.` on line 2.
- Switching to the next song does not flash a false Yandex connection-waiting message; title/artist remain stable and update when the new track ID arrives.
- Active-version label is green only if exact decoder proof is present; mapping-only stays gray.
- VPN continuity should remain unchanged. Do not repeat broad VPN/audio testing unless a regression is reported.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No W23 native host/renderer, audio pipeline, VPN recovery or entitlement changes in W163. No broad audits or intermediate installers. Preserve the pre-W163 rollback branch.
