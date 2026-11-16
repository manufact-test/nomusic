# CELIKOM Windows — active handoff W161 (16 November 2026)

**Status: W161 UI correction is committed on main; source CI is the next gate. W20 owner package 0.24.43.0 has not been triggered yet.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- Source checkpoint: the commit containing this document; fetch current `main` HEAD before continuing.
- Pre-W161 rollback: `backup/windows-main-pre-w161-owner-ui-vpn-yandex-20261116` @ `851b24b02ed9398b30be4e4673485be6e772e2d5`.
- Target version: **0.24.43.0**, native module **0.24.31**.
- W160 build 0.24.42.0 is the owner's current installed version. Its VPN recovery messages are accepted; the remaining compact UI copy/colors are not.

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

## Next actions

1. Wait for Main CI and Windows integration CI on current main HEAD.
2. If both pass, update only the existing W20 request file for 0.24.43.0 and trigger exactly one owner-review package.
3. Verify installer, ZIP containing the identical installer, and SHA256 manifest.
4. Owner manually checks the UI states above and confirms the already accepted VPN recovery still works.

Do not request the user to resend previous requirements; the exact agreed copy and state rules are in the W161 document.

## Yandex disconnect incident

The owner reported one unexpected Yandex Music disconnect/track switch during the conversation. The VPN handler does not kill or relaunch Yandex. A transient entitlement failure can temporarily disable/re-enable the CELIKOM bridge, and a rejected continuity hold can lead to source revalidation/reload. The existing process watcher records `YANDEX_PROCESS_UNAVAILABLE` for an observed process exit; source reload has separate events.

Earlier W54 diagnostics showed one same-track revalidation/reload and no `YANDEX_PROCESS_UNAVAILABLE`, but those logs do not identify this new incident. No fresh diagnostic was supplied for the exact event. Do not make speculative audio/VPN changes; if it repeats, use a fresh diagnostic to distinguish process exit from source reload.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No broad audits, speculative audio changes, unnecessary tests or intermediate packages. Preserve the pre-W161 rollback branch.
