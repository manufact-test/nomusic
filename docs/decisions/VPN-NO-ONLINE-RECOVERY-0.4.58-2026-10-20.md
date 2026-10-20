# CELIKOM 0.4.58 — VPN route recovery without browser `online` event

Дата: 20.10.2026. Компонент: единое Chromium MV3 расширение; ветка `feature/api-range`.
Статус: исправление реализовано, CI и сборка PASS; ручная приёмка владельцем в реальном Chrome/OpenVPN **в процессе, ещё не подтверждена**.

## Инцидент владельца на 0.4.57

После очередного переключения VPN расширение потеряло связь и не подключилось само; владелец восстановил работу вручную. Ранее аналогичные переключения обычно восстанавливались быстро. Диагностика 0.4.57 непосредственно после сбоя:

- `enabled=true`, `phase=READY`, `startupError=null`, `replacementError=access_reconnecting`, `suspended=true`, `recovering=false`, `active=null`, `player.connected=false`.
- `bridge.ready=true`, `bridge.healthy=true`: bridge/MAIN были живы; Яндекс.Музыка продолжала воспроизводить оригинальный audio, без активной подмены.
- `playback.lastRestore.reason=api_network_error`; `recentLog` заканчивается `RESTORING · api_network_error` → `IDLE · original restored/release requested` (09:57:38 UTC).
- Сетевой журнал: до обрыва успешные `config`, `resolve`, `entitlement` HTTP 200; затем три последовательные `auth/me` с `auth_timeout` около 20 секунд каждый, отменённые GET и далее `auth_network_error` без HTTP-статуса. Это транспортная недоступность, а не установленный отказ entitlement/401.
- `lastRecoveryHint` указывает на прежнее событие `visible`; нельзя на основании лога утверждать, что браузер отправил `online` именно при возврате VPN.

Важно: конкретную внешнюю причину обрыва VPN/API по этим данным определить невозможно. Выявлен отдельный недостаток стратегии восстановления после сетевого тайм-аута: путь периодической проверки доступа ранее не обновлял зависший транспорт GET без явного сигнала `online`/`visible`/`document` или ручного Start.

## Исправление 0.4.58

- В `extension/src/background/service-worker.ts` после временной ошибки проверки доступа устанавливается `resetTransportOnRetry`.
- После прежнего ограниченного cooldown (5 секунд) следующая разрешённая проверка доступа сначала вызывает `userAuth.resetTransport()` и `resolveApi.resetTransport()`: отменяет старые GET и удаляет устаревшие связанные сетевые кэши без требования браузерного `online` event.
- Только успешная **серверная** проверка разрешённого доступа после retry инициирует `CELIKOM_ACCESS_STATE: allowed, recovered: true` для снятия suspension в content-контроллере. Уведомление `online` само по себе прав доступа не выдаёт.
- Успешный обычный путь не должен постоянно сбрасывать сеть. Явный reset/retry также очищает флаг; stale поколения и текущий user intent учитываются существующей логикой.
- POST-запросы и старт trial автоматически не повторяются; Stop, ручной оригинал и отказ сервера не обходятся. Fail-open с оригинальным воспроизведением при отсутствии подтверждённого доступа сохраняется.
- Добавлен regression-тест `VPN route change without online event resets stale GET transport and auto-resumes after verified access` в `extension/tests/unified-worker.test.mjs`.

Исходные технические коммиты:
- [e1a5be2 — reconnect fix](https://github.com/manufact-test/nomusic/commit/e1a5be2bf1bd27182394df17cd27ac95eb74dc62)
- [fb03386 — regression](https://github.com/manufact-test/nomusic/commit/fb03386bf2b5967c83b47589df706c8adfb2e0bb)
- [32914c8 — version 0.4.58](https://github.com/manufact-test/nomusic/commit/32914c86589b5f8833053925273695c4eb2e29e0)

## Проверки и выдача

- [Полный CI — PASS](https://github.com/manufact-test/nomusic/actions/runs/39405622654).
- [Private Chrome package build — PASS](https://github.com/manufact-test/nomusic/actions/runs/39405617786); артефакт `celikom-stage9-private-chrome-32914c86589b5f8833053925273695c4eb2e29e0`, внутри `celikom-extension-0.4.58.zip` и файл SHA-256.
- [Website CI (no deploy) — PASS](https://github.com/manufact-test/nomusic/actions/runs/39405622519).
- Собранный ZIP 0.4.58 передан владельцу в этом чате; установка — **поверх существующей распакованной папки**, Reload на `chrome://extensions` и обновление вкладки Яндекс.Музыки.
- Это клиентское исправление: сервер, БД, аудиофайлы, модерация, аккаунты и Android не изменялись; backend deploy не выполнялся. PR #6 остаётся открытым и не объединяется.

## Ручной gate: ожидается отчёт владельца

На установленной 0.4.58 с активной Яндекс.Музыкой несколько раз менять VPN/маршрут, включая сценарий, когда Chrome не выдаёт `online`. Проверить: оригинал играет во время отсутствия доступа, после возвращения API без ручного Start исчезает `access_reconnecting`, `suspended` становится `false`, а одобренная замена может активироваться на подходящем треке. Время переподключения зависит от реальной сети, тайм-аутов и 5-секундного cooldown — не обещать мгновенности. Также проверить Stop, ручной возврат к оригиналу, отсутствие ложного зелёного статуса.

При повторном сбое сохранить новую безопасную диагностику сразу после ожидания (версия, `suspended`, `recovering`, `bridge`, `lastRecoveryHint`, `network`, `recentLog`), скрыв токены, пароли и подписанные аудиоссылки. Не помечать как «исправлено владельцем» до фактического теста.
