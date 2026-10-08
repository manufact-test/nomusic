# CELIKOM

[![CI](https://github.com/manufact-test/nomusic/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/manufact-test/nomusic/actions/workflows/ci.yml)

CELIKOM — клиентская система безопасной замены звука для точно определённого трека в поддерживаемом веб-плеере. Музыкальный сервис остаётся источником интерфейса, очереди и состояния воспроизведения.

Технический gate `CELIKOM-POC-001` закрыт 7 октября 2026 года на версии `0.0.4`. Stage 2 принят владельцем на `0.2.1`, Stage 3 — по сообщению и диагностике `0.3.2`. Версия `0.4.0` реализует Stage 4: PHP/MySQL API, подписанные Range audio, серверный каталог, client cache и реальную подмену. Следующий gate — развёртывание и живые MP3/WAV на Hostinger. Подробные границы проверки: `docs/project-status.md`.

> Репозиторий временно публичный для закрытой разработки. Публичная видимость не означает открытую лицензию. До любого клиентского релиза Stage 18 требует перевести код и production-инфраструктуру в закрытый управляемый контур.

## Структура

- `extension/` — Chromium MV3 на TypeScript: адаптер/bridge, локальный playback engine и минимальный клиентский UI.
- `server/` — PHP 8.3/MySQL API, приватное хранилище, migrations и analytics foundation.
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

Собранное расширение появится в `extension/dist/unpacked`, архив и SHA-256 — в `extension/dist/`. Серверный пакет — в `dist/celikom-server-0.4.0.zip`. Для server integration tests задайте DB_NAME с префиксом `celikom_test`, DB_* и приватный STORAGE_PATH; этот тест очищает исключительно disposable test DB. CI использует MySQL 8 и требует native Chromium decode/seek. Без локальных PHP/DB соответствующая проверка отложена до CI. Тест-план: `docs/test-plans/CELIKOM-STAGE4-API.md`.

Для закрытого сервера:

```bash
composer --working-dir=server install
php server/bin/migrate.php
php -S 127.0.0.1:8080 -t server/public
```

Настройте приватный `.env` по `server/.env.example`. `/api/v1/health` и `/api/v1/config` доступны без авторизации; resolve/events используют временный API_TEST_TOKEN, audio — истекающую подпись. Для локального PHP сервера используйте router `server/public/index.php`, если нужны вложенные API routes. Публичная клиентская авторизация и загрузки будут реализованы в дальнейших этапах.

Развёртывание и первые файлы: `docs/deployment/hostinger-private-test.md`. Сборка расширения под конкретный HTTPS origin: `CELIKOM_API_BASE_URL=https://API_DOMAIN npm run build:extension`. Без API-конфигурации работает developer demo; для реального каталога очистите тестовый ID и сохраните код доступа в developer details.

## Принятый playback PoC

PoC доказал exact Track ID, выбор master media, локальную замену и возврат оригинала. Observation перенесён на Stage 2, replacement/SyncEngine — на Stage 3 и приняты владельцем. PoC остаётся замороженным техническим эталоном, production-код его не импортирует.

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
