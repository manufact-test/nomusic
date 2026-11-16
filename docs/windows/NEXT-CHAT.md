# CELIKOM Windows — current handoff W160 (16 November 2026)

**Status: W160 code, CI and one internal owner-review build are complete. Waiting only for the owner's manual VPN check.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W160 code/package source: `16db00425483ef32a5eaf6e9bdf350d82dce3c56`.
- Exact pre-W160 rollback: `backup/windows-main-pre-w160-vpn-recovery-status-20261116` @ `dda6e94f86ef9e4a2dd31ca6ab903873b21385a2`.
- Version: **0.24.42.0**, native module **0.24.31**.

## Build and CI

- Main CI [43848412090](https://github.com/manufact-test/nomusic/actions/runs/43848412090) — SUCCESS.
- Windows integration CI [43848412051](https://github.com/manufact-test/nomusic/actions/runs/43848412051) — SUCCESS.
- W20 owner staging [43848412064](https://github.com/manufact-test/nomusic/actions/runs/43848412064) — SUCCESS.
- Artifact ID: `14216831806`.
- [Download W160 owner-review artifact](https://github.com/manufact-test/nomusic/actions/runs/43848412064/artifacts/14216831806).
- Installer: `CELIKOM-W160-VPN-RECOVERY-PLAYBACK-STATUS-02442-UNSIGNED.exe`.
- ZIP: `CELIKOM-Windows-0.24.42.zip`; includes the same installer and `SHA256SUMS.txt`.
- Internal unsigned owner-review build, not a production release.

## Current task

The owner tested 0.24.41.0 with a heavier WireGuard VPN. The already-playing CELIKOM song continued without an audible interruption or source jump, but the UI incorrectly showed server recovery and unavailable track data for 20–30 seconds.

W160 corrects only the UI:
- server state: `Связь с сервером восстанавливается.`
- last fresh PLAYING state: `Музыка продолжает играть.`
- PAUSED / STOPPED states are shown accurately;
- unknown state remains unknown.

The last fresh player state is retained for presentation only. It does not grant entitlement or prove the decoder source. No native audio, VPN route, entitlement or playback logic was changed.

## Required reading

1. `docs/windows/W160-VPN-RECOVERY-PLAYBACK-STATUS-20261116.md` — root cause, code scope, CI and build evidence.
2. `docs/windows/W160-OWNER-TEST-HANDOFF-20261116.md` — manual acceptance and ready-to-send first message.
3. `docs/windows/W159-MAPPED-TRACK-STATUS-20261116.md` — previous W159 state and source-proof boundaries.
4. `docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md` — previously accepted VPN/audio continuity.

## Next action

Wait for the owner to install 0.24.42.0 and test the heavy VPN case. If the status now reads correctly while the same music continues, record acceptance and stop. Do not create another build or request diagnostics unnecessarily.

If a defect remains, inspect only the exact screenshot/observation and change only the relevant UI state. Do not reopen native audio or VPN architecture without a new audible failure.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256, W150 or architecture changes. No broad audits, repeated diagnostics analysis, speculative fixes, unnecessary tests or intermediate packages.

The previous W159 handoff remains in `docs/windows/NEXT-CHAT-HISTORY-20261116.md` as historical context only.
