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
