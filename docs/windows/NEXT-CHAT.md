# CELIKOM Windows — current handoff W159 (16 November 2026)

<badge>Owner test pending</badge>

**The owner has downloaded version 0.24.41.0. Installation and manual verification are NOT yet confirmed.** Do not mark the build accepted, make speculative changes, or create another package before the owner reports the result.

## Product and source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W159 application code: `09fca7a0f7fb9b0f7fe4a436978c48968054a0fa`.
- W159 owner-package source: `f9e82d9cce43fe0fb7949c51fe442bf37827f09b`.
- Current docs/handoff commit before this cleanup: `8a0d8b75f6d60841fc4bb47d2803175e1c287146`.
- Exact pre-W159 rollback: `backup/windows-main-pre-w159-mapped-source-status-20261116` @ `0e1de874bc15c401fcceb206511d8cb8f4005d80`.

## Delivered build

- Version: **0.24.41.0**, native module **0.24.31**.
- Internal unsigned owner-review package; not a production release.
- W20 staging [run 43828713363](https://github.com/manufact-test/nomusic/actions/runs/43828713363) — SUCCESS; artifact ID `14208040930`.
- Main CI [43828713432](https://github.com/manufact-test/nomusic/actions/runs/43828713432) — SUCCESS.
- Windows integration CI [43828713415](https://github.com/manufact-test/nomusic/actions/runs/43828713415) — SUCCESS.
- EXE: `CELIKOM-W159-MAPPED-TRACK-STATUS-02441-UNSIGNED.exe`, SHA-256 `d378273712e1cb8876c4555d67dcabe1657d3359c87bd8969418c192b6f067e9`.
- ZIP: `CELIKOM-Windows-0.24.41.zip`, SHA-256 `0322d19133d4c950940b6c06d856f5333677e6547b717a50c64dfb06783e166e`.
- ZIP contains the exact same EXE plus `SHA256SUMS.txt`.

## W158 / W159 state

W158 VPN audio continuity was manually accepted by the owner: the already-playing replacement continues through VPN route recovery without an audible pop or unnecessary restart. Do not reopen this work unless a new audible failure is reported.

W159 corrects only presentation consistency for an accepted current-track mapping:
- Header/service: `Сервис включён`.
- Current mapped-track availability: `Версия CELIKOM доступна`.
- The old false `Источник текущего трека не подтверждён` / `Ожидаем подтверждения` messages should not reappear for that accepted mapping.
- `Подмена активна` and accent color still require exact current native decoder proof. Availability/mapping is not decoder proof.

## Immediate next action

Wait for the owner's installation and UI test result. The narrow check is:
1. One track with an available CELIKOM version before VPN.
2. The same track after VPN connection/recovery.
3. Next to another track with an available CELIKOM version.

The main window and compact popup should keep consistent neutral availability/service copy across all three states. Do not ask for the already-reviewed W54 diagnostics again.

- If the check passes: record owner acceptance and stop. No new build.
- If it fails: analyze only the exact reported mismatch, preserve a rollback point, make the smallest relevant fix, add a focused regression test, run only relevant tests and both CI workflows. Create at most one new owner package after a confirmed fix and only if a new package is needed for owner verification.

## Required reading

1. `docs/windows/W159-OWNER-TEST-HANDOFF-20261116.md` — detailed acceptance plan and ready-to-send first message for the next chat.
2. `docs/windows/W159-MAPPED-TRACK-STATUS-20261116.md` — W159 code changes, diagnostics and proof boundaries.
3. `docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md` — accepted VPN/audio work and historical owner findings.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256, W150 or architecture changes. No broad audits, unrelated tests, repeated diagnostics analysis, speculative fixes or intermediate EXE/ZIP packages.

The previous long handoff is preserved at `docs/windows/NEXT-CHAT-HISTORY-20261116.md`; it is an archive only, not an active task list.
