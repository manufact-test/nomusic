# CELIKOM — этап 7: Загрузки и антидубли (план старта)

Дата: 2026-10-09. Источники требований: Master ТЗ MVP v1.5 §§11–13 и План работ MVP v1.6, этап 7. Это план реализации, а не изменение продуктового ТЗ.

## Перед стартом

Этап 6.1–6.6 завершён технически, сервер 6.7 обновлён и проверен. Владелец подтвердил работающую подмену после hotfix, но **весь этап 6 формально не закрыт**: нет подтверждённой ручной проверки в двух установках Chrome и осталась периодическая ошибка [#7](https://github.com/manufact-test/nomusic/issues/7). Работа над этапом 7 допустима в GitHub с тестовой БД; не объявлять публичную готовность.

Действующая библиотека Hostinger: 1 Track / 1 AudioAsset / 1 mapping; одобренный Yandex Track ID 144530503, Replacement ID 1, 180872 ms. Не менять её без отдельного разрешения. Branch feature/api-range, PR #6 открыт и не слит. Запрос управления библиотекой по умолчанию {"operation":"validate"}.

## Последовательность

1. **7.0 Инвентаризация.** Изучить существующие LibraryManagementService, StorageAdapter, схему MySQL, PHP Application и Chrome popup. Зафиксировать контракт API, изоляцию pending, точную идентичность Track и безопасность загрузки.
2. **7.1 Модель.** Миграции для track_requests и moderation/pending-upload records, fingerprint processing statuses. Сохранять уникальность SHA-256 и единственную active-approved привязку.
3. **7.2 UploadService.** Multipart POST /api/v1/uploads; проверять право доступа, MIME и контейнер, лимит конфигурации (текущая проверенная граница 30 MiB), длительность, SHA-256; безопасный приватный staging без путей пользователя и без прямой записи в web root.
4. **7.3 Антидубли.** Байтовый дубль под другим именем не создаёт второй физический AudioAsset. Один AudioAsset допускает несколько точных Track ID; повторы HTTP-запросов не создают лишних связей. Metadata не заменяет SHA-256.
5. **7.4 Fingerprint.** Абстракция FingerprintService и статусы not_processed / pending / ready / failed; допускается будущий worker без FFmpeg/transcoding на Hostinger на этом этапе.
6. **7.5 Приватный API.** POST /api/v1/track-requests и upload endpoint с owner-only gate, строгим rate limit и безопасными ответами. **FEATURE_UPLOADS=false для публичных пользователей до этапа 10.** Нельзя принимать неавторизованные загрузки.
7. **7.6 Chrome UI.** Add version: текущий Track ID только для чтения, выбор файла, чекбокс заявления, прогресс и pending status; ручная подмена Track ID запрещена.
8. **7.7 CI и регрессия.** Disposable celikom_test* MySQL и синтетические WAV/MP3: переименованный дубль, одинаковые байты, один asset с двумя Track IDs, fake .mp3, unsupported MIME, oversize, corrupted, interrupted, retry, race, authorization и отсутствие auto-approve.

## Неподлежащие изменению правила

Загрузка всегда остаётся pending; /resolve возвращает только approved-active. Этап 8 добавит ручную админ-модерацию. Не менять рабочую песню, PR #6 не сливать. Сохранить подписанный HTTP Range + MediaSource/blob, fail-open, playback controls. Реальные аудиофайлы и credentials не размещать в GitHub.

## Ручная проверка владельца (только в конце этапа 7, 10–15 минут)

После готового приватного ZIP: Add version → верный Track ID → загрузка разрешённого MP3 → pending → повтор с теми же байтами и новым именем → отсутствие публикации до approve. До этого всю основную реализацию и тесты вести самостоятельно.

## Важная незакрытая ошибка из этапа 6

[GitHub issue #7](https://github.com/manufact-test/nomusic/issues/7): Chrome Errors периодически показывает `Uncaught RangeError: Maximum call stack size exceeded` из `player/main-world-bundle.js`. До фикса — место около `celikomObservedHistory` и иногда зависания SPA Яндекса. Фикс 1d69906 (immutable native hooks и lifecycle guards) прошёл 80/80 JS CI; после него владелец полчаса работал без зависаний, **но новая ошибка вновь появилась**, скрин указывает на район `restorePrototypeHooks()` (около строки 1044 bundle). Причина не подтверждена, ошибка не устранена окончательно. Не выпускать дополнительные патчи вслепую; изучить полный stack / reproduce / lifecycle. Этап 7 может продолжаться с изолированными тестами.

## Фактическое исполнение 7.0–7.7 (09.10.2026, рабочая ветка)

**Код реализован в `feature/api-range`, CI прошёл; ручная приёмка владельца и deployment на Hostinger НЕ выполнены.** GitHub Actions: [37941932390](https://github.com/manufact-test/nomusic/actions/runs/37941932390) (настоящий HTTP multipart и PHP SAPI), [37942113245](https://github.com/manufact-test/nomusic/actions/runs/37942113245) (обновлённый клиентский контракт), оба success. Следующие прогоны после изменения документации и кода также должны быть зелёными.

- **7.0:** повторно использованы `tracks`, `audio_assets`, `track_replacements`, `LibraryManagementService`, `StorageAdapter`, `PdoCatalogRepository`. `ResolveService` продолжает возвращать только approved + active.
- **7.1:** аддитивная миграция `002_pending_uploads.sql`: `upload_submissions`, `track_requests`, `audio_fingerprint_jobs`, `upload_rate_buckets`. Старые 6 таблиц и существующие одобренные записи не переписываются. Отдельная таблица fingerprint обеспечивает перезапускаемость DDL.
- **7.2–7.3:** `UploadService`, `Mp3Inspector`, приватный `StorageAdapter`, проверка MIME/структуры MPEG-фреймов и до 30 MiB, SHA-256, стабильное хранилище по hash, idempotency UUID и Track-level InnoDB row lock. Повторный файл возвращает прежний pending candidate; для другого Track ID создаётся другая pending-связь с тем же AudioAsset. Файл с уже одобренной связью отклоняется, но не опубликованная новая кандидатура не активируется.
- **7.4:** `AudioFingerprintService` + `DeferredFingerprintService` ставят новые аудио в `pending` через `audio_fingerprint_jobs`. `not_processed/pending/ready/failed` описаны схемой; **реального вычислителя Chromaprint, similarity score и предупреждений о перекодированном дубликате пока нет**. Этот deferred worker не следует выдавать за готовый fingerprint detection.
- **7.5:** защищённые owner-only multipart `POST /api/v1/uploads` и `POST /api/v1/track-requests`. Сервер разрешает запись только при одновременно заданных `FEATURE_OWNER_UPLOADS=1` и независимом длинном `UPLOAD_OWNER_TOKEN`; read-only `API_TEST_TOKEN` не даёт upload-доступа. Токены не в Git; журнал ошибок отдаёт нейтральные коды. Лимиты загрузок и предложений хранятся в MySQL. `FEATURE_OWNER_UPLOADS=0` по умолчанию. Клиентский `/api/v1/config` всегда отдаёт `upload_enabled=false` до этапа 10.
- **7.6:** Chrome popup показывает read-only Track ID только при уверенном live-detection с duration, input файла, rights declaration, progress и pending/duplicate status. Исходный Track ID повторно проверяется перед отправкой. Owner-token вводится отдельно и не сохраняется в chrome.storage. Код работает из extension popup, не MAIN-world.
- **7.7:** `server/tests/uploads.php` (синтетические MPEG-фреймы и disposable MySQL), настоящий PHP HTTP multipart в `server/tests/http.mjs`; `extension/tests/upload-contract.test.mjs` (exact ID, ambiguous track, MP3 select, API origin). Проверены задвоенные запросы/переименование, тот же AudioAsset для разных Track, fake MP3, invalid metadata, partial upload, oversize, нет auto-approval/доступа к Range. Сценарий race требует дополнительной параллельной нагрузочной проверки; механизм Track row lock проверяется прежним Stage 6 тестом.

**Оставшиеся gate:** сформировать приватный owner-test ZIP, подготовить отдельную (не рабочую) API среду и только по явному разрешению владельца провести 10–15 минут живого Chrome тестирования. На Hostinger сейчас нет Stage 7, флаг не включён. Проверка технической валидности MP3 не заменяет декодирование/прослушивание, точное измерение длительности и ручную модерацию (этап 8). До владельческого gate не объявлять этап 7 принятым. Не закрывать issue #7 и Stage 6.7; PR #6 оставить несмёрженным.

## Дополнение: Stage 7 hardening / CI gate (09.10.2026)

Поверх пакетов 7.0–7.7 завершена отдельная техническая регрессия без доступа к Hostinger. В `Mp3Inspector.durationMs()` реализован полный последовательный проход MPEG Layer III кадров с проверкой согласованности sample rate/version, ID3, целостности кадра, конца файла и допустимой длительности. `UploadService` хранит независимо измеренную длительность AudioAsset, а не слепо доверяет duration текущего Track. Для уже известного SHA-256 недопустимое расхождение сохранённой длительности вызывает безопасный конфликт. Идемпотентный повтор после изменения модерационного статуса не выдаёт ложное `pending`.

`server/tests/uploads.php` расширен негативными MP3-вариантами (обрыв, испорченный средний кадр, посторонний хвост, неправильный ID3) и проверкой стандартного ID3. `server/tests/http.mjs` запускает четыре PHP-воркера с конкурентными одинаковыми Track/SHA запросами на disposable MySQL: создана ровно одна pending-связь. GitHub CI устанавливает FFmpeg **только в тестовый runner**, генерирует 2.5s synthetic MP3 в seekable file и с помощью изолированного `server/tests/http-router.php` проверяет Chromium decode/seek/play через HTTP Range. Ни одна тестовая медиа-страница не попадает в серверный deploy ZIP.

**Последний подтверждённый полный CI:** [37945005475](https://github.com/manufact-test/nomusic/actions/runs/37945005475) — success, включая HTTP concurrency и native Chromium synthetic MP3. Состояние: код/CI ready; отдельная временная HTTPS/MySQL среда и владелецкий 10–15-минутный manual gate ещё не выполнены. Порядок, безопасность и ограничения: [Stage 7 isolated owner acceptance](../deployment/stage7-owner-upload-acceptance.md). Не редактировать production Hostinger, PR #6 не мёржить и не закрывать Issue #7.
