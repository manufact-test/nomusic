# CELIKOM Windows — W162 owner UI and track metadata stability

Date: 16 November 2026  
Status: source CI + Windows integration CI + one internal W20 owner-review package passed. Owner manual UI confirmation pending.

## Scope and checkpoints

- Repository: `manufact-test/nomusic`
- Working branch: `main`
- Source checkpoint: `b6aa1dee19cd2862f23c9b656210f54db12cdfe9`
- W20 request/package commit: `a3a3506a1acea21a0b96d7ec7ec3de9b804596f8`
- Pre-W162 rollback: `backup/windows-main-pre-w162-title-status-polish-20261116` @ `5c6e5d902941bb931039aa54a26cc307c09b296f`
- App version: `0.24.44.0`
- Native module: `0.24.31`
- Previous owner-installed version: `0.24.43.0`

## Owner report and W54 diagnostic

The owner manually tested VPN toggling after W161 and reported that music no longer drops, with no noticeable extra delays.

The W54 diagnostic (generated 2026-11-16 11:51:16 UTC, app 0.24.43.0) shows repeated entitlement-route changes and two transient network suspensions. During both suspensions the same current track `144530503` was held, kept and resumed. The final recovery sequence completed at 11:51:14.798 UTC with `NATIVE_ROUTE_RECOVERY_SOURCE_KEPT` and `NATIVE_ROUTE_RECOVERY_RESUMED`.

The diagnostic does not prove audible replacement:
- `NativeDecoderPropertiesObserved=true`
- `NativeDecoderUrlPropertyObserved=false`
- `PlayerAudibleEventObserved=false`
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`

Therefore W162 deliberately preserves the exact decoder-source proof gate. A mapped replacement is not promoted to green unless the current CELIKOM decoder source is confirmed. The log also contains two `RESOLVE_REQUEST` events for track `144530503` one millisecond apart; no resolver/audio change was made because there is no evidence that this caused the compact title flicker or a playback regression.

## Root cause addressed

The compact UI read `LastSong`, `LastTrackTitle` and `LastTrackArtist` through separate property reads/locks. A heartbeat could arrive between those reads, so the UI could combine fields from different states. In addition, a same-track heartbeat with temporarily empty MediaSession metadata overwrote the last non-empty title/artist and caused a blank/repaint cycle.

## W162 implementation

1. Added immutable `BridgeServer.PlaybackSnapshot`, returned under one lock, containing track ID, title, artist, duration, status, source, playback state, freshness and connection/recovery flags.
2. Same-track heartbeat with empty title/artist/duration now preserves the last non-empty metadata. Non-empty fields can still refresh independently. A genuine track-ID change replaces all previous metadata, including clearing fields that are not yet available; invalid/unavailable state continues to clear.
3. `RefreshPlaybackUi` captures one snapshot and passes it to both compact and main UI updates.
4. Compact title, artist and status labels are assigned only when their text actually changes. Compact layout uses the last rendered track/duration snapshot rather than separately reading live bridge fields.
5. Active-source copy is now explicit:
   - Exact confirmed active CELIKOM decoder: green `Играет полная версия CELIKOM`.
   - Mapping/availability only: neutral gray `Версия CELIKOM доступна`.
   - Pause: `Пауза` remains green while the service connection is confirmed.

No audio, native-host, renderer, VPN, entitlement, Yandex, updater, backend or architecture changes were made. No new runtime hooks were added.

## Changed files

- `windows-companion/w15/Celikom.Companion/BridgeServer.cs`
- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion/UserFacingPlaybackHealth.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Celikom.UpdateSupervisor.csproj`
- `windows-companion/w20/installer/CELIKOM.iss`
- W20 request file: `windows-companion/w20/owner-review-package-20261114.request`

## Verification

Source checkpoint:
- Main CI run `43863680868` — SUCCESS.
- Windows integration CI run `43863680894` — SUCCESS.
- W15 entitlement/login/native-state tests — SUCCESS, including W162 same-track metadata preservation, Next replacement and partial metadata refresh.
- GUI compile with warnings as errors — SUCCESS.
- Supervisor, installer policy, metadata and crash-recovery checks — SUCCESS.

W20 request commit:
- Main CI run `43864166741` — SUCCESS.
- Windows integration CI run `43864166849` — SUCCESS.
- W20 safe installer staging run `43864166748` — SUCCESS.

W20 additionally passed:
- Source compile with warnings as errors.
- Native local bridge and host preflight tests.
- Native image construction and crash-recovery tests.
- Installer name/version resolution and updater ZIP/PE version/anti-downgrade validation.
- Disposable Windows per-user install/uninstall smoke: `W20_INTERNAL_INSTALL_UNINSTALL_PASS_NO_YANDEX_FILES`.
- Packaging the exact same installer into one ZIP with SHA256 checksums: `W137_SINGLE_INSTALLER_EXE_ZIP_AND_SHA256_PASS`.
- Internal staging only; no release.

## Owner-review artifact

- Run: https://github.com/manufact-test/nomusic/actions/runs/43864166748
- Artifact ID: `14224093499`
- Artifact name: `CELIKOM-Windows-internal-stage-a3a3506a1acea21a0b96d7ec7ec3de9b804596f8`
- Direct artifact URL: https://github.com/manufact-test/nomusic/actions/runs/43864166748/artifacts/14224093499
- Installer: `CELIKOM-W162-TRACK-STATUS-AND-METADATA-STABILITY-02444-UNSIGNED.exe`
- ZIP: `CELIKOM-Windows-0.24.44.zip`
- `SHA256SUMS.txt` is inside the artifact.
- Uploaded artifact ZIP SHA256: `342e28febb81b5304cfb793a7da24405f85a683901237f56921f34f4878341c4`
- Artifact expires 2026-11-26 12:13:49 UTC.
- Package is internal and unsigned, not a production release.

## Next action

Owner installs 0.24.44.0 over 0.24.43.0 and checks:
- title/artist stability when hiding/restoring the compact window and opening the full window;
- green active-source wording only when exact decoder proof is present;
- gray mapping-only availability and green pause status.

VPN was already manually tested and reported smooth. Do not repeat broad VPN testing unless a regression appears. If the active status stays gray while the owner hears the replacement, capture a fresh diagnostic and investigate the missing decoder proof; do not weaken the proof gate.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No broad audits, speculative audio changes, unnecessary tests or intermediate packages. Preserve the pre-W162 rollback branch.
