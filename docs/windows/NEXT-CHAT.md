# CELIKOM Windows — active handoff W161 (16 November 2026)

**Status: W161 UI correction, source CI and internal owner-review package 0.24.43.0 are complete. Waiting only for the owner's manual UI check.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W161 source commit: `4d018021880bf2167d60f262a0ba23c29e0aba10`.
- W20 request/package commit: `4d1fd37203e2da03b91d226c9f5875f412bedcd3`.
- Pre-W161 rollback: `backup/windows-main-pre-w161-owner-ui-vpn-yandex-20261116` @ `851b24b02ed9398b30be4e4673485be6e772e2d5`.
- Version: **0.24.43.0**, native module **0.24.31**.
- W160 build 0.24.42.0 was the owner's installed version at the time of the report. Its VPN recovery messages are accepted; the remaining compact UI copy/colors were corrected in W161.

## What W161 changes

- Start: `Подождите, идёт подключение к приложению Яндекса.`
- Disabled: `Подмена выключена. Нажмите «Старт», чтобы подключиться к Яндекс Музыке`.
- Missing application: `Яндекс Музыка не найдена. Установите официальное приложение.`
- Fresh native Yandex connection: green dot + green `Сервис включён`, independently of track decoder proof.
- Exact active CELIKOM source: `Версия CELIKOM доступна` in green. Mapping-only availability stays neutral/gray.
- Pause: `Пауза` remains green while the service connection is live.
- Next/track transitions do not gray the service indicator while the native connection remains live.
- Compact window gets the requested 20 px lower breathing room.
- W160 VPN-recovery messages and audio path are untouched.

Read `docs/windows/W161-UI-STATE-START-COPY-20261116.md` before changing anything.

## CI and owner-review package

- Main CI: `43857753031` and `43858280540` — SUCCESS.
- Windows integration CI: `43857752831` and `43858280413` — SUCCESS.
- W20 safe installer staging: `43858280505` — SUCCESS.
- Artifact ID: `14222536548`.
- Installer: `CELIKOM-W161-UI-STATE-AND-START-COPY-02443-UNSIGNED.exe`.
- ZIP: `CELIKOM-Windows-0.24.43.zip`; it contains the exact same EXE.
- EXE SHA256: `1a3883b7c5eba1e98d467bf5f35146e3f11ca2910bf49becd1c81ba936064204`.
- ZIP SHA256: `ad1f4b7b305fc9733326a0c661e2071be69da551ebd2b00569419b0c483bbf77`.
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43858280505

## Next actions

1. Owner installs 0.24.43.0 and manually checks the UI states above.
2. Confirm the already accepted VPN recovery still preserves music.
3. Do not create another package unless the owner reports a reproducible defect.

Do not request the user to resend previous requirements; the exact agreed copy and state rules are in the W161 document.

## Yandex disconnect incident

The owner reported one unexpected Yandex Music disconnect/track switch during the conversation. The VPN handler does not kill or relaunch Yandex. A transient entitlement failure can temporarily disable/re-enable the CELIKOM bridge, and a rejected continuity hold can lead to source revalidation/reload. The process watcher records `YANDEX_PROCESS_UNAVAILABLE` for an observed process exit but polls every second, so a very brief restart may be missed. Source reload has separate events.

Earlier W54 diagnostics showed one same-track revalidation/reload and no `YANDEX_PROCESS_UNAVAILABLE`, but those logs do not identify this new incident. No fresh diagnostic was supplied for the exact event. Do not make speculative audio/VPN changes; if it repeats, use a fresh diagnostic to distinguish process exit from source reload.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No broad audits, speculative audio changes, unnecessary tests or intermediate packages. Preserve the pre-W161 rollback branch.
