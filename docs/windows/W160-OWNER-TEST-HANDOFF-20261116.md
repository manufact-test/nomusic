# CELIKOM Windows W160 — owner test handoff (16 November 2026)

## Current status

W160 code and CI are complete. The internal owner-review build **0.24.42.0 / native 0.24.31** is ready. Manual owner acceptance is pending.

- Repository: `manufact-test/nomusic`
- Branch: `main`
- Code checkpoint: `16db00425483ef32a5eaf6e9bdf350d82dce3c56`
- Rollback: `backup/windows-main-pre-w160-vpn-recovery-status-20261116` @ `dda6e94f86ef9e4a2dd31ca6ab903873b21385a2`
- Artifact: [W160 owner-review build](https://github.com/manufact-test/nomusic/actions/runs/43848412064/artifacts/14216831806)

The artifact contains the standalone installer `CELIKOM-W160-VPN-RECOVERY-PLAYBACK-STATUS-02442-UNSIGNED.exe`, `CELIKOM-Windows-0.24.42.zip` and `SHA256SUMS.txt`.

## Manual check

Install 0.24.42.0 over 0.24.41.0, play a track with a CELIKOM replacement, then enable the heavier WireGuard VPN.

During server recovery the compact UI should show:
- `Связь с сервером восстанавливается.`
- `Музыка продолжает играть.`

The same song must continue without a jump to the original, audible click or restart. After connectivity returns, normal UI status should return.

W160 also handles last-known PAUSED and STOPPED states. Those are covered by regression tests; the manual check only needs the playing case.

If this passes, record acceptance and stop. No new package or diagnostics are needed. If it fails, send the exact mismatch and only the diagnostics needed to isolate it.

## First message for the next chat

Привет! Принимай **CELIKOM Windows после W160**. Продолжай строго с текущего состояния, ничего не начинай с нуля и не меняй архитектуру.

Сначала прочитай:
- `docs/windows/W160-OWNER-TEST-HANDOFF-20261116.md`
- `docs/windows/W160-VPN-RECOVERY-PLAYBACK-STATUS-20261116.md`
- `docs/windows/W159-MAPPED-TRACK-STATUS-20261116.md`
- `docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md`

**Продукт:** только CELIKOM Windows.  
**GitHub:** `manufact-test/nomusic`  
**Рабочая ветка:** `main`  
**Кодовый checkpoint W160:** `16db00425483ef32a5eaf6e9bdf350d82dce3c56`  
**Резерв до W160:** `backup/windows-main-pre-w160-vpn-recovery-status-20261116` @ `dda6e94f86ef9e4a2dd31ca6ab903873b21385a2`  
**Версия для владельца:** 0.24.42.0, native 0.24.31.  
**Сборка:** W20 run `43848412064`, artifact `14216831806`, SUCCESS. Main CI `43848412090` и Windows integration CI `43848412051` — SUCCESS.

Владелец сообщил, что на 0.24.41.0 при включении тяжёлого WireGuard уже играющая CELIKOM-песня не прерывалась и не прыгала на оригинал. Ошибка была в интерфейсе: он 20–30 секунд показывал восстановление связи и недоступность текущего трека, хотя музыка продолжала играть.

W160 исправляет только отображение:
- сервер: `Связь с сервером восстанавливается.`
- последний свежий статус PLAYING: `Музыка продолжает играть.`
- PAUSED и STOPPED показываются отдельно;
- неизвестное состояние не выдаётся за воспроизведение.

Последнее состояние сохраняется только для UI. Оно не подтверждает точный decoder source и не выдаёт entitlement. Нативный аудиопуть, VPN-механика и серверная проверка доступа не менялись.

**Сейчас не делай новых изменений и не собирай ещё один установщик.** Дождись ручной проверки владельца 0.24.42.0 на тяжёлом VPN. Если интерфейс показывает оба правильных статуса, а песня продолжает играть, зафиксируй acceptance и остановись. Если есть проблема — разбирай только конкретный скриншот/наблюдение. Не открывай заново нативный аудиопуть без новой слышимой регрессии.

Не начинать Android, браузерное расширение, backend, Yandex original files, updater/P-256 или архитектурный рефакторинг. Не делать массовых аудитов, повторных диагностик и лишних тестов.
