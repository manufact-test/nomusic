# CELIKOM Windows — W163 track-transition and UI polish

Date: 16 November 2026  
Status: implementation, source verification and one internal W20 owner-review package passed. Owner manual confirmation pending.

## Scope and checkpoints

- Repository: `manufact-test/nomusic`
- Working branch: `main`
- W163 code checkpoint: `3b290931e2e1c9153f29a56e78cede45353fafbd`
- W20 package/docs commit: `57b826ed2431febb2fad31198897d94bd4cc1648`
- Pre-W163 rollback: `backup/windows-main-pre-w163-owner-ui-transition-20261116` @ `0db016cbdcb939911ae3fd6ff71c2aa9af07c876`
- App version: `0.24.45.0`
- Native module: `0.24.31`
- Previous owner version: `0.24.44.0`

## Owner findings

The owner reported that 0.24.44 still had:
- Insufficient bottom spacing below the disabled-state text and playback-waiting text before the Account card.
- An awkward line break in the large green Start message, leaving `к` at the end of the first line.
- A short misleading Yandex-connection-waiting message appearing during some track transitions before the next track title appeared.
- The expected active full-version wording and green color not appearing on mapping-only states.

## W163 implementation

1. Added `TrackStatusBottomSpacingPx = 18` and applied it to the final visible row of the track/status group before the Account card. The layout does not add unwanted gaps between title and artist.
2. Start message now contains an explicit newline: `Подождите, идёт подключение\nк приложению Яндекса.`
3. BridgeServer treats an ID-less PLAYING/PAUSED heartbeat from normal native connected/resolving/recovering states as a short track-transition gap. It keeps the previous metadata for up to 9 seconds. A real new track ID replaces all fields atomically; STOPPED, UNAVAILABLE and other non-transient states clear the retained identity.
4. `GetPlaybackSnapshot` exposes retained metadata only while it is within the bounded grace and the bridge is enabled/player is not unavailable. This preserves the UI label through short queue transitions without extending active-source proof.
5. Stale-heartbeat UI now uses last-known playback state (`Музыка продолжает играть.`, `Пауза`, `Воспроизведение остановлено.`) or neutral `Проверяем состояние воспроизведения…`, instead of claiming that Yandex is waiting to connect. The service indicator remains gray without a fresh heartbeat.
6. The active label is wired as `Играет полная версия CELIKOM` in green only for exact `NATIVE_SOURCE_VERIFIED` + `ACTIVE_REPLACEMENT` proof. W163 does not promote mapping-only to green.

## Active-source evidence limitation

The available W54 diagnostic from app 0.24.43.0 reported:
- `HEARTBEAT_NATIVE_MAPPING_ACCEPTED`
- `NativeDecoderUrlPropertyObserved=false`
- `PlayerAudibleEventObserved=false`
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`

The diagnostic confirms mapping acceptance but does not establish that the CELIKOM decoder URL is the current audible source. Therefore the UI must remain gray for mapping-only. The active label and green color are present in code for exact decoder proof; if that proof is still absent on 0.24.45.0, investigate the native decoder observer separately with a fresh diagnostic. Do not fake the green status.

## Changed files

- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion/BridgeServer.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Celikom.UpdateSupervisor.csproj`
- `windows-companion/w20/installer/CELIKOM.iss`

No W23 native host/renderer, audio pipeline, VPN recovery, entitlement authority, Yandex files, updater/P-256, backend, Android or browser extension files were changed.

## Verification

- Main CI run `43871031471` — SUCCESS.
- Windows integration CI run `43871031480` — SUCCESS.
- Main CI after W20 request/docs commit run `43871613360` — SUCCESS.
- Windows integration CI after W20 request/docs commit run `43871613282` — SUCCESS.
- W15 entitlement/login/native-state tests — SUCCESS:
  - same-track metadata preservation;
  - short ID-less PLAYING transition preserves current track;
  - real Next atomically replaces retained metadata;
  - STOPPED clears retained metadata;
  - bounded metadata grace and player-unavailable guards.
- GUI compile with warnings as errors — SUCCESS.
- W22/W23/W60 audio/VPN regression suite — SUCCESS.
- W21 rollback, W24 catalog/ASAR, W110 supervisor and W114/W117/W128/W136 installer/security checks — SUCCESS.
- W20 safe installer staging run `43871613198` — SUCCESS.

## Owner-review package

- Version: `0.24.45.0`
- Native module: `0.24.31`
- Installer: `CELIKOM-W163-TRACK-TRANSITION-AND-UI-SPACING-02445-UNSIGNED.exe`
- Artifact ID: `14227453095`
- Artifact name: `CELIKOM-Windows-internal-stage-57b826ed2431febb2fad31198897d94bd4cc1648`
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43871613198
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43871613198/artifacts/14227453095
- EXE SHA256: `e393cfa33d0399856a263e00f260a9ba227dc1d4407e02a4f6582f6733913a54`
- Artifact expires 2026-11-26 13:02:35 UTC.
- Artifact includes the standalone EXE, a ZIP containing the exact same installer, and SHA256SUMS.txt. The EXE hash matches the checksum; the inner ZIP contains exactly one root EXE and is byte-identical to the standalone file.
- Internal unsigned owner-review package only; not a production release, signed package or public feed.

## Owner manual verification

Install 0.24.45.0 over 0.24.44.0 and check:
- 18 px lower spacing below disabled/waiting text before Account.
- `к приложению Яндекса.` begins line 2 of the large green Start message.
- No false Yandex-connection-waiting flash during track transitions; title/artist remain stable and update when the new track ID arrives.
- Active full-version label is green only when exact decoder proof exists. Mapping-only remains gray.
- VPN continuity should remain unchanged; no broad VPN/audio re-test unless a regression appears.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No W23 host/renderer, audio or VPN changes in W163. No broad audits, speculative audio changes or intermediate installers. Preserve the pre-W163 rollback branch.
