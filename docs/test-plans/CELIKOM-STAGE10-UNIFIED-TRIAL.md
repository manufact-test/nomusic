# CELIKOM — Этап 10: Trial + EntitlementService и ОДНА рабочая версия

**Статус:** STARTED / FIRST PACKAGE BRANCH-ONLY · 10.10.2026
**Источники истины:** Master ТЗ MVP v1.5 (§§14–15,18,23,26, приложения G–I), План работ MVP v1.6 («Этап 10» и новый раздел 15), Issue #9 и актуальный HEAD `feature/api-range`. В случае расхождений продуктовая модель ТЗ сохраняется, актуальный статус исполнения определяется новым разделом handoff.

**Progress 10.10.2026:** audit + atomic trial foundation added; [package audit](CELIKOM-STAGE10-AUDIT-ATOMIC-TRIAL.md). No deployment, no user-bearer playback yet; owner acceptance still required.

## 0. Главный нерушимый критерий

**Этап 10 считается выполненным ТОЛЬКО после установки и ручной приёмки владельцем ОДНОГО расширения CELIKOM**, где подмена одобренной песни (ранее рабочая в оригинальной 0.4.4) и весь набор фич аккаунтов/загрузок (0.4.6) работают одновременно, включая 5-дневный trial, реальную проверку entitlement, управление доступом, загрузку MP3 и отдельное предложение трека без MP3.

Не откладывать «потом объединим» на этап 11. Не считать CI-only unit-тесты подтверждением playback в живом Yandex Music. Не удалять рабочее оригинальное Chrome 0.4.4 до независимой приёмки единой версии.

## 1. Отправная архитектура и текущий разрыв

- Код подмены в `extension/src/player/*`, `extension/src/content/controller.ts`, MAIN/ISOLATED bundles присутствует и в тестовой 0.4.6.
- `extension/src/api/api-broker.ts` требует собственный `apiTestToken` из Chrome storage. `server/src/Application.php` для `/api/v1/resolve` проверяет только конфигурационный `API_TEST_TOKEN`. В новой установке профиля Chrome токен отсутствует, в отличие от ранее настроенной рабочей 0.4.4.
- `extension/src/auth/auth-broker.ts` хранит отдельную пользовательскую auth-сессию. Её access/refresh-токены **пока не участвуют** в авторизации Resolve. Это подтверждено анализом исходников, но конкретная ошибка пользователя не воспроизведена инструментально.
- На Hostinger approved active: Yandex Track ID **144530503**, Replacement #1, длительность 180872 ms. Две pending: #2/799133075 (synthetic) и #3/38436680 (реальный MP3). Только approved active можно открывать через защищённые signed Range URLs.
- Этап 9 принят владельцем 10.10.2026: email verification (6 цифр, реальное письмо), recovery, 90-day rolling refresh, несколько независимых устройств в серверных интеграционных тестах, Chrome UI 0.4.6. Live Android APK пока нет. Ручную playback-проверку временных установок владелец **отложил сюда**.

## 2. Очерёдность работы (не нарушать)

### 10.0 — Инвентаризация и контракт единого релиза
1. Сверить HEAD, GitHub Actions, активный Hostinger config/feature flags, API route и обе Chrome версии без дублирования устройств.
2. Зафиксировать контракт `authenticated user + entitlement → resolve approved only → signed Range streaming`, включая 401/403, истечение, network fallback, offline и невозможность обращения к pending.
3. Подготовить изолированный тестовый стенд, сохранить working Chrome 0.4.4. Не передавать `API_TEST_TOKEN` через публичный UI и не объединять владельческий upload token с пользовательской авторизацией.

### 10.1 — EntitlementService и trial на сервере
1. По Master ТЗ реализовать trial **5 суток от первой фактической активации**, а не от скачивания, установки, регистрации или появления email в базе. Время и условия задаёт сервер, не системные часы пользователя.
2. Account-level trial, единый для двух устройств. Повторная регистрация / переустановка не должны бесконечно продлевать trial; сберечь privacy (без жёсткого fingerprinting).
3. `EntitlementService`: решение `allowed/source/valid_until/reason`, объяснимый subscription/entitlement ledger; серверный denied после срока, admin grants и остальные источники ТЗ — по согласованной архитектуре. Отдельные payments/recurring billing относятся к **этапу 11**, не представлять их выполненными на 10.
4. Миграции только аддитивные, idempotent, есть контроль прав и race/concurrency. Не сбрасывать действующие учётные записи/подтверждённые email.

### 10.2 — Привязать авторизованного пользователя к настоящей подмене
1. `auth bearer` + server-side entitlement проверяются в Resolve. Не делать открытый анонимный аудиокаталог и не утекать в Yandex page long-lived refresh/token.
2. Клиент использует уже сохранённую session/refresh, автоматически обновляет; при `denied` оригинальная песня играет как обычно, без зависания вкладки. Истекший trial не переходит в ложный `allowed` после перезапуска Chrome.
3. Убрать необходимость вводить `API_TEST_TOKEN` в конечном пользовательском сценарии. Старый технический токен использовать только в закрытом контролируемом переходном тесте с отдельным owner gate; не полагаться на его наличие для clean install.
4. Развести бизнес-разрешение и playback-fail-open: отсутствие сервера/аудио не должно прерывать оригинал.

### 10.3 — Публичные действия после гейтов
1. «Загрузить версию» — MP3, SHA-256 дедупликация, права на файл, статус pending, ручная модерация.
2. **«Предложить песню»** — отдельная равноправная кнопка, текущий точный Track ID + trusted URL и metadata, **без MP3 и галочки о правах на передаваемый MP3**, собственная очередь в Stage8 admin, throttle/antispam/dedupe.
3. Обе публичные операции и entitlement не включать в тестовый Hostinger без security/QA gate. Никакой автоматической публикации на основании предложения.

### 10.4 — Тесты и изолированный интеграционный gate
Проверить MySQL migrations/rollback, concurrency при двойном trial start; TTL ровно 5 суток; два устройства и logout/revoke; недоступный/истёкший trial; обычный bearer вместо API_TEST_TOKEN; approved / pending; short TTL, HTTP Range 206/HEAD/416, seek/pause/sync/next/return/fail-open; email verify/recovery не регрессируют; zero leaked secrets; XSS/CSRF/rate limiting как применимо.

### 10.5 — Защищённое включение на Hostinger
Pre-snapshot всего private env + SQL + всех MP3, **disposable restore**, deploy по `feature/api-range` только после CI, post-deploy read-only audit + post-snapshot/restore. Не изменять approved #1, pending #2/#3, права на медиа, admin owner flag/credentials или public upload flag до gate.

### 10.6 — ОБЯЗАТЕЛЬНАЯ ручная приёмка владельца
- Чистая установка единого релиза **без предварительного `apiTestToken`**.
- Обычный подтверждённый email login → активный 5-day trial/entitlement → approved #1 реально заменяет музыку в Яндекс.Музыке; Play/Pause/Seek/Next/Stop/Return.
- Недоступный MP3/сеть/entitlement → оригинал без ошибок. Pending #2/#3 не заменяются и не раскрывают защищённое аудио.
- 2 независимых профиля/устройства, вход/выход, refresh; нет требования «Мои устройства» в маленьком popup.
- Upload MP3 и separate Suggest Song проверены, admin queue получает только pending.
- Владелец подтверждает **один установленный клиент** с функциями 0–10. Только после подтверждения пометить Issue #9 / Stage 10 COMPLETED.

## 3. Неприкосновенные ограничения / known issues
- `PR #6` OPEN / UNMERGED, не сливать по умолчанию.
- `Issue #7` OPEN — редкий MAIN-world `RangeError: Maximum call stack size exceeded`; не объявлять исправленным без воспроизведения/валидации.
- Тестовый сервер: `https://darkred-camel-588676.hostingersite.com`, private env и DB вне public webroot. Секреты, коды из email и пароль приложения Google не попадут в GitHub/chat.
- Этап 11 billing, реферальные выплаты, Android APK не начинать вместо объединения на этапе 10.
- Отдельные рабочая 0.4.4 и тестовая 0.4.6 — исторические стадии разработки, не целевой продукт.

## 4. Ссылки для старта
- [Issue #9 — главный критерий Stage 10](https://github.com/manufact-test/nomusic/issues/9)
- [Stage9 UI closed #8](https://github.com/manufact-test/nomusic/issues/8)
- [Stage9 0.4.6 private build PASS](https://github.com/manufact-test/nomusic/actions/runs/38057989522)
- [Stage9 90-day server deployment PASS](https://github.com/manufact-test/nomusic/actions/runs/38058274439)
- [Stage9 post-deploy integrity audit PASS](https://github.com/manufact-test/nomusic/actions/runs/38058420995)

