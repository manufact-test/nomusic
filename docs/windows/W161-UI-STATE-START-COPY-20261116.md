# CELIKOM Windows W161 — UI state and startup copy (16 November 2026)

## Status

**W161 source correction is prepared in this commit. Main CI and Windows integration CI must pass before the one owner-review package is requested.** No W20 build has been triggered yet.

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- Source checkpoint: the commit containing this document; fetch current `main` HEAD before any follow-up.
- Exact pre-W161 rollback: `backup/windows-main-pre-w161-owner-ui-vpn-yandex-20261116` @ `851b24b02ed9398b30be4e4673485be6e772e2d5`.
- Target owner-review version: **0.24.43.0**.
- Native module remains **0.24.31**.
- W20 request file is intentionally unchanged until source CI passes.

## Owner's 0.24.42 observation

The owner confirmed that the W160 VPN-recovery presentation is now correct: during VPN recovery the compact window shows:

- `Связь с сервером восстанавливается.`
- `Музыка продолжает играть.`

The music continued. Keep this behavior unchanged.

The remaining owner complaint is that the other previously agreed UI changes were not present in 0.24.42: the old Start/wait copy remained, the service indicator/dot were gray, and the paused/track-availability colors were wrong.

## W161 UI correction

Only Windows companion presentation and version/package metadata change.

- Immediately after Start, show the single clear message: `Подождите, идёт подключение к приложению Яндекса.`
- Do not show a duplicate `Ожидаем текущий трек` row while the startup banner is active.
- When stopped, show: `Подмена выключена. Нажмите «Старт», чтобы подключиться к Яндекс Музыке`.
- If Yandex Music is not installed, say explicitly: `Яндекс Музыка не найдена. Установите официальное приложение.`
- The header `Сервис включён` and the dot are green when a fresh native Yandex heartbeat confirms the service connection. This is independent of whether the current track's decoder source has been proven.
- Keep the service header green through pause and ordinary Next/track transitions while the native connection remains live.
- The track line is `Версия CELIKOM доступна`: green only with exact active native decoder proof; neutral/gray when a mapped version is available but active playback is not yet confirmed.
- Show `Пауза` in green while the service connection remains confirmed.
- Add the previously requested 20 px of lower breathing room to the compact window.

Source-proof boundaries remain strict: a mapping/approved version is not proof that the decoder is playing it. The service-connected label must not be confused with active replacement.

## VPN / unexpected Yandex disconnect investigation

The owner also reported one unexpected Yandex Music disconnect/switch during the conversation and suspects VPN interaction.

Code-path audit:
- The VPN/network-address handler does not call `Process.Kill`, `CloseMainWindow`, or `Process.Start` for Yandex.
- Yandex is launched only by the explicit Start/integration path when it is not already running; that path is not invoked by a VPN route notification.
- A transient entitlement failure can disable/re-enable the CELIKOM native bridge. If the native continuity hold is rejected, the renderer can revalidate/reload the current source. That can affect the song/source, but it is not a direct Yandex process termination.
- The process watcher records `YANDEX_PROCESS_UNAVAILABLE` when it observes an actual process exit. Native source revalidation/reload has separate diagnostic events.
- Earlier W54 diagnostics recorded one `NATIVE_CURRENT_SOURCE_REVALIDATE` and one `NATIVE_REPLACEMENT_SOURCE_RELOAD`, but no `YANDEX_PROCESS_UNAVAILABLE`. Those are historical observations, not proof of what happened in the new incident.
- W158/W160 continuity work was accepted by the owner for the VPN-recovery case; do not make speculative audio/VPN changes based on this single unlogged event.

No fresh diagnostic from the exact new incident is available, so the cause is **not established**. If it repeats, inspect a diagnostic captured immediately after the event and distinguish process exit (`YANDEX_PROCESS_UNAVAILABLE`) from source revalidation/reload (`NATIVE_CURRENT_SOURCE_REVALIDATE`, `NATIVE_REPLACEMENT_SOURCE_RELOAD`, and route-recovery hold events).

No native audio, VPN route, entitlement, playback Start/Stop, Yandex files, backend, Android or browser-extension logic is changed in W161.

## Focused regression coverage

W161 adds targeted checks for:
- exact Start and disabled-state copy;
- startup text appearing before the bridge is enabled;
- service-connected status being independent from decoder-source proof;
- neutral mapping-only availability versus green exact source proof;
- short `Пауза` presentation;
- removal of ambiguous “current player” text from the compact state.

Windows integration CI also checks the new Start-state presentation. No broad test sweep is requested.

## Next actions

1. Confirm Main CI and Windows integration CI pass on this source commit.
2. Only after both pass, update `windows-companion/w20/owner-review-package-20261114.request` for **0.24.43.0** and trigger exactly one W20 internal owner-review build.
3. Verify the one EXE, ZIP containing that same EXE, and SHA256 manifest. No signing, stable feed, deployment or customer release.
4. Give the owner one 0.24.43.0 installer for manual UI acceptance.

Manual owner check after installing 0.24.43.0:
- Start shows the exact Yandex connection message.
- Disabled state shows the exact Start instruction.
- After native connection, dot and `Сервис включён` are green.
- `Версия CELIKOM доступна` is green only for exact active source proof; mapping-only availability is neutral.
- Pause stays green; Next does not gray the service indicator.
- VPN recovery still shows the two accepted messages and the same music continues.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. Do not reopen native audio/VPN code without a fresh diagnostic proving a new audible regression. No intermediate packages or unnecessary tests.
