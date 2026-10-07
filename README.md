# CELIKOM

[![CI](https://github.com/manufact-test/nomusic/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/manufact-test/nomusic/actions/workflows/ci.yml)

CELIKOM — клиентская система безопасной замены звука для точно определённого трека в поддерживаемом веб-плеере. Музыкальный сервис остаётся источником интерфейса, очереди и состояния воспроизведения.

Технический gate `CELIKOM-POC-001` закрыт 7 октября 2026 года на версии `0.0.4`, Stage 1 production-фундамента также завершён. Активный Stage 2 переносит доказанное определение Track ID и состояния player в production-расширение `0.2.0`.

> Репозиторий временно публичный для закрытой разработки. Публичная видимость не означает открытую лицензию. До любого клиентского релиза Stage 18 требует перевести код и production-инфраструктуру в закрытый управляемый контур.

## Структура

- `extension/` — production Chromium Manifest V3 на TypeScript: ServiceAdapter, YandexMusicAdapter, PlayerBridge и диагностический UI.
- `server/` — минимальный PHP 8.3/Composer-каркас будущего API.
- `spikes/player-poc/` — принятый playback PoC, сохранённый как технический эталон.
- `docs/` — архитектура, ADR, продуктовые принципы, аналитика и тест-планы.
- `android/` — зарезервированная граница будущего Android-модуля; playback не обещан до отдельного технического gate.

## Требования

- Node.js 24 или новее.
- npm 11 или новее.
- PHP 8.3 и Composer 2 — для полного локального прогона server-проверок. При их отсутствии Node-проверка валидирует структуру, а PHP runtime-тест выполняется в CI.
- `zip` — для сборки дистрибутива расширения.

## Первый запуск

```bash
npm ci
npm run ci
```

Собранное расширение появится в `extension/dist/unpacked`, а воспроизводимый архив и SHA-256 — в `extension/dist/`. Инструкция живого Stage 2 прогона находится в `docs/test-plans/CELIKOM-STAGE2-PLAYER-INTEGRATION.md`.

Для server-каркаса:

```bash
composer --working-dir=server install
composer --working-dir=server test
php -S 127.0.0.1:8080 -t server/public
```

После запуска `GET http://127.0.0.1:8080/health` возвращает локальный health response. Бизнес-логика, аккаунты, загрузки и billing в Stage 1 намеренно отсутствуют.

## Принятый playback PoC

PoC умеет определять exact Track ID и master media element в актуальной SPA-разметке Яндекс Музыки, безопасно выполнять локальную замену, следовать за play/pause/seek и гарантированно восстанавливать оригинал. Его observation-контракты перенесены в production-код Stage 2; replacement и SyncEngine остаются замороженным эталоном до Stage 3.

```bash
npm run test:poc
npm run validate
npm run fixture:smoke
```

Подробности: `docs/spikes/0001-player-integration.md` и `docs/test-plans/CELIKOM-POC-001.md`.

## Ветки и выпуск

- `main` — стабильная подтверждённая база.
- `develop` — интеграционная ветка.
- `feature/*` — изолированные этапы разработки.
- Production-секреты, пользовательские аудиофайлы и реальные персональные данные в Git не попадают.
- Клиентский релиз из публичного репозитория запрещён правилами Stage 18.

## Правовой статус

Copyright © 2026 CELIKOM. All rights reserved. Исходный код опубликован для разработки проекта; лицензия на использование, распространение или создание производных работ не предоставляется.
