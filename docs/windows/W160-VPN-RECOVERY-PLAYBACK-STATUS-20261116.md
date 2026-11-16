# CELIKOM Windows W160 — VPN recovery playback status (16 November 2026)

## Status

**Code, CI and internal owner-review package are complete. Manual owner acceptance of 0.24.42.0 is pending.**

Product: CELIKOM Windows only.  
Repository: `manufact-test/nomusic`.  
Working branch: `main`.  
W160 application/package source commit: `16db00425483ef32a5eaf6e9bdf350d82dce3c56`.  
Exact pre-W160 rollback: `backup/windows-main-pre-w160-vpn-recovery-status-20261116` @ `dda6e94f86ef9e4a2dd31ca6ab903873b21385a2`.

## Owner observation on 0.24.41.0

The owner tested a heavier WireGuard VPN used to represent the likely customer network conditions. On VPN activation, the already-playing CELIKOM replacement continues without an audible interruption or a jump to the original. The UI nevertheless showed:

- `Восстанавливаем связь. Текущий звук не переключаем.`
- `Данные текущего трека временно недоступны…`

These messages remained for roughly 20–30 seconds, then returned to normal.

This confirms a UI-state mismatch, not a reported playback failure. The manual listening result is the evidence for continuous sound; the diagnostics do not independently prove the audible decoder source.

## Root cause

On a transient authenticated entitlement-request failure, `CompactPopupActions.RefreshCompactAccessAsync` sets `_resumeAfterNetworkFailure`, marks native network recovery pending, then disables the local Bridge until a fresh server entitlement response is received. Disabling the Bridge clears its current heartbeat and track metadata. The native recovery path holds the already-playing source, so audio can continue while the UI has lost the current-player lease.

The UI was incorrectly presenting loss of the server connection and local player metadata as though playback itself had failed.

## W160 correction

- Capture the last **fresh** player state (`PLAYING`, `PAUSED`, `STOPPED`) before a route change or transient entitlement suspension clears the Bridge lease.
- Refresh that snapshot whenever a fresh heartbeat is accepted.
- Keep server connectivity and playback presentation separate:
  - connection: `Связь с сервером восстанавливается.`
  - last fresh state PLAYING: `Музыка продолжает играть.`
  - PAUSED: `Музыка на паузе.`
  - STOPPED: `Воспроизведение остановлено.`
  - unknown/stale state: `Проверяем состояние воспроизведения…`
- The snapshot is **presentation only**. It does not grant entitlement, restart playback, or prove the exact decoder source.
- Existing `Подмена активна` / green state remains gated by exact current native decoder proof.

No changes to native audio, VPN route recovery, entitlement authority, playback Start/Stop, Yandex files, backend, Android, browser extension, updater or P-256.

## Code and checks

Changed:
- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopupActions.cs`
- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`
- Companion and UpdateSupervisor project versions
- W20 installer identity and the single owner-package request

Version: **0.24.42.0**. Native module remains **0.24.31**.

- Main CI [43848412090](https://github.com/manufact-test/nomusic/actions/runs/43848412090) — **SUCCESS**.
- Windows integration CI [43848412051](https://github.com/manufact-test/nomusic/actions/runs/43848412051) — **SUCCESS**.
- W20 safe installer staging [43848412064](https://github.com/manufact-test/nomusic/actions/runs/43848412064) — **SUCCESS**.
- W20 verified GUI compile, W15 tests, native/ASAR checks, installer metadata, same-AppId update from 0.24.41.0, no Yandex files touched, one-installer ZIP and SHA256 manifest.

## Owner package

[Download the W160 owner-review artifact](https://github.com/manufact-test/nomusic/actions/runs/43848412064/artifacts/14216831806)

Artifact ID: `14216831806`  
Artifact name: `CELIKOM-Windows-internal-stage-16db00425483ef32a5eaf6e9bdf350d82dce3c56`  
Artifact ZIP digest: `da5b9dc539adbb8cb7a49367cb6c91d8cb2418a97dd4a84a9c4cad739fcb0167`

Contains:
- `CELIKOM-W160-VPN-RECOVERY-PLAYBACK-STATUS-02442-UNSIGNED.exe`
- `CELIKOM-Windows-0.24.42.zip` (same installer inside)
- `SHA256SUMS.txt`

Internal unsigned owner-review build only. Not a production release.

## Manual acceptance — pending

1. Download the artifact and run `CELIKOM-W160-VPN-RECOVERY-PLAYBACK-STATUS-02442-UNSIGNED.exe` over the installed 0.24.41.0.
2. Play a track with an available CELIKOM replacement.
3. Enable the heavier WireGuard VPN.
4. During recovery, confirm the UI says `Связь с сервером восстанавливается.` and `Музыка продолжает играть.`, while the same song continues without a jump, click or restart.
5. After server connectivity returns, confirm the normal status returns.

No new diagnostics are needed if this passes. If the actual sound fails or the UI still reports the wrong state, send only the observed mismatch and a fresh diagnostic if needed.

If the check passes: record owner acceptance and stop. No second build. If it fails: fix only the reported issue; do not reopen the accepted native audio path without a new audible regression.
