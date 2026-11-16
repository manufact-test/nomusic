# CELIKOM Windows W161 — UI state and startup copy (16 November 2026)

## Status

**W161 source correction and internal owner-review package are complete. Main CI, Windows integration CI and W20 staging all passed. Owner manual acceptance remains pending.**

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W161 source commit: `4d018021880bf2167d60f262a0ba23c29e0aba10`.
- W20 request/package commit: `4d1fd37203e2da03b91d226c9f5875f412bedcd3`.
- Exact pre-W161 rollback: `backup/windows-main-pre-w161-owner-ui-vpn-yandex-20261116` @ `851b24b02ed9398b30be4e4673485be6e772e2d5`.
- Owner-review version: **0.24.43.0**.
- Native module remains **0.24.31**.

## Final CI and package

- Main CI: `43857753031` SUCCESS; after the request commit, `43858280540` SUCCESS.
- Windows integration CI: `43857752831` SUCCESS; after the request commit, `43858280413` SUCCESS.
- W20 safe installer staging: `43858280505` SUCCESS.
- Internal artifact ID: `14222536548`, name `CELIKOM-Windows-internal-stage-4d1fd37203e2da03b91d226c9f5875f412bedcd3`.
- Installer: `CELIKOM-W161-UI-STATE-AND-START-COPY-02443-UNSIGNED.exe`.
- Distribution ZIP: `CELIKOM-Windows-0.24.43.zip`, containing exactly the same installer EXE.
- EXE SHA256: `1a3883b7c5eba1e98d467bf5f35146e3f11ca2910bf49becd1c81ba936064204`.
- ZIP SHA256: `ad1f4b7b305fc9733326a0c661e2071be69da551ebd2b00569419b0c483bbf77`.
- The downloaded artifact was checked locally: both SHA256 manifest entries passed, and the EXE inside the ZIP has the same SHA256 as the standalone EXE.
- Installer compile, PE version/anti-downgrade checks, disposable per-user install/uninstall smoke and final ZIP/checksum packaging all passed.
- This is an internal unsigned owner-review artifact, not a production release.

## Owner's 0.24.42 observation

The owner confirmed that the W160 VPN-recovery presentation is now correct: during VPN recovery the compact window shows:

- `Связь с сервером восстанавливается.`
- `Музыка продолжает играть.`

The music continued. Keep this behavior unchanged.

The remaining owner complaint was that the other previously agreed UI changes were not present in 0.24.42: the old Start/wait copy remained, the service indicator/dot were gray, and the paused/track-availability colors were wrong.

## W161 UI correction

Only Windows companion presentation and version/package metadata change.

- Immediately after Start, show: `Подождите, идёт подключение к приложению Яндекса.`
- Do not show a duplicate `Ожидаем текущий трек` row while the startup banner is active.
- When stopped, show: `Подмена выключена. Нажмите «Старт», чтобы подключиться к Яндекс Музыке`.
- If Yandex Music is not installed, say explicitly: `Яндекс Музыка не найдена. Установите официальное приложение.`
- The header `Сервис включён` and the dot are green when a fresh native Yandex heartbeat confirms the service connection. This is independent of whether the current track's decoder source has been proven.
- Keep the service header green through pause and ordinary Next/track transitions while the native connection remains live.
- The track line is `Версия CELIKOM доступна`: green only with exact active native decoder proof; neutral/gray when a mapped version is available but active playback is not yet confirmed.
- Show `Пауза` in green while the service connection remains confirmed.
- Add the requested 20 px of lower breathing room to the compact window.

Source-proof boundaries remain strict: a mapping/approved version is not proof that the decoder is playing it. The service-connected label must not be confused with active replacement.

## VPN / unexpected Yandex disconnect investigation

The owner also reported one unexpected Yandex Music disconnect/switch during the conversation and suspects VPN interaction.

Code-path audit:
- The VPN/network-address handler does not call `Process.Kill`, `CloseMainWindow`, or `Process.Start` for Yandex.
- Yandex is launched only by the explicit Start/integration path when it is not already running; that path is not invoked by a VPN route notification.
- A transient entitlement failure can disable/re-enable the CELIKOM native bridge. If the native continuity hold is rejected, the renderer can revalidate/reload the current source. That can affect the song/source, but it is not a direct Yandex process termination.
- The process watcher records `YANDEX_PROCESS_UNAVAILABLE` when it observes an actual process exit. It polls every second, so an extremely brief exit/restart could be missed.
- Native source revalidation/reload has separate diagnostic events.
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

Windows integration CI checks the new Start-state presentation. The full W20 package path also compiled with warnings as errors and passed native bridge, host preflight, crash recovery, updater, install/uninstall and package identity checks.

## Next action — owner manual check

Install **0.24.43.0** and verify:
- Start shows the exact Yandex connection message.
- Disabled state shows the exact Start instruction.
- After native connection, dot and `Сервис включён` are green.
- `Версия CELIKOM доступна` is green only for exact active source proof; mapping-only availability is neutral.
- Pause stays green; Next does not gray the service indicator.
- VPN recovery still shows the two accepted messages and the same music continues.

Do not create another package unless the owner reports a reproducible defect.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. Do not reopen native audio/VPN code without a fresh diagnostic proving a new audible regression. No intermediate packages or unnecessary tests.
