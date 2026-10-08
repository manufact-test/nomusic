# Changelog

## 0.3.1 — 2026-10-08 (startup regression fix; live acceptance pending)

- Воспроизведён присланный сбой `normalizeTrackId`: ранняя регистрация ReplacementController захватывала ещё отсутствующий core, затем immutable registry сохранял сломанный класс.
- Зависимости разрешаются при создании контроллера и проверяются явно; ранняя регистрация больше не сохраняет undefined.
- MAIN и ISOLATED получают по одному deterministic bundle с фиксированным порядком модулей и общей проверкой build/manifest.
- Popup polling больше не внедряет повторно controller с startupError; wake/storage/retry не повторяют неуспешную инициализацию. Диагностика сохраняется, а обновление вкладки позволяет начать с чистого контекста.
- Regression воспроизводит ошибку 0.3.0 до исправления, затем проверяет раннюю регистрацию, packaged startup, повторное внедрение и отсутствие log flood.

## 0.3.0 — 2026-10-08 (live playback acceptance pending)

- Stage 2 принят по ручному прогону владельца на 0.2.1 и зелёному CI; PR #4 интегрирован в develop.
- Перенесена локальная подмена в отдельные ReplacementController, ReplacementPlayer, SyncEngine, OriginalAudioGuard и FailOpenController.
- Exact-ID opt-in тестовая карта использует только встроенный синтетический MP3. Реальная библиотека и backend ещё не подключены.
- Добавлены generation/session leases, отмена старых загрузок, коррекция seek/drift, зеркалирование pause/resume/volume/mute/rate и fail-open без повторных попыток на ошибочном треке.
- MAIN-world watchdog самостоятельно останавливает подмену и возвращает пользовательский original volume/mute при потере heartbeat; устаревшие release не влияют на новую generation.
- Основной UI ограничен четырьмя действиями; тестовый Track ID и диагностика скрыты в developer details. Добавление треков пока явно coming-soon.
- Добавлены unit/race/compiled two-world playback тесты; живой gate новой версии остаётся обязательным.

## 0.2.1 — 2026-10-08

- Исправлена регрессия `CONNECTING`: production background автоматически запускает manifest-declared MAIN/ISOLATED scripts в уже открытой вкладке, как это делал принятый PoC.
- Добавлено разрешение `scripting` только для packaged-script recovery на существующем host `music.yandex.ru`; новых host permissions нет.
- Отказы доступа и ошибки запуска больше не превращаются в пустую диагностику: возвращаются `connection.error`, `connection.detail`, наличие controller и bridge health.
- Повторное внедрение core idempotent; потерянный первоначальный INIT повторяется через heartbeat.
- Content controller отвечает диагностикой даже при async startup error. При ошибке popup предлагает `Повторить`; permission failure не вызывает бесконечные фоновые попытки.
- Добавлены bootstrap regressions и сквозная проверка собранных MAIN/ISOLATED scripts в двух изолированных test environments. Живой браузерный gate остаётся обязательным.

## Unreleased — player integration

- Добавлен production `ServiceAdapter` и изолированный `YandexMusicAdapter` для exact Track ID, metadata и master media state.
- Добавлен версионированный MAIN-world ↔ ISOLATED `PlayerBridge` с session ID, monotonic sequence, heartbeat и отсечением stale events.
- Нормализованы `TRACK_CHANGED`, `PLAY`, `PAUSE`, `SEEK`, `TIME_UPDATE`, `VOLUME_CHANGED`, `RATE_CHANGED`, `METADATA_CHANGED`, `ENDED` и `ERROR`.
- Service-specific selectors, state patches и ограниченный пассивный JSON capture локализованы в одном адаптере.
- Popup версии `0.2.0` показывает найденный трек и копирует диагностику; на Stage 2 звук не изменяется.
- Добавлены fixture/contract/lifecycle тесты и ADR источников player state.

## Stage 1 — repository foundation

- Создан production-каркас Chromium MV3 расширения с TypeScript build без runtime-зависимостей.
- Добавлен PHP 8.3/Composer-каркас API с локальным health endpoint и smoke test.
- Добавлены CI, воспроизводимый extension archive, SHA-256 и manifest validation.
- Зафиксированы ADR структуры репозитория и обязательной приватизации перед клиентским релизом.
- Добавлены продуктовые принципы будущего минималистичного UI и versioned-определения аналитических метрик.
- Зарезервирована отдельная граница Android без преждевременного обещания playback.

## PoC gate accepted — 2026-10-07

- Закрыт технический Этап 0 на версии v0.0.4.
- Финальный live regression подтвердил exact Track ID, replacement, pause/resume, seek, track change, manual bypass, SPA/bridge recovery и fail-open.
- Подтверждены Track ID `38077230` и `37889209` с confidence 240–260; известный рекламный video отклонён.
- После намеренных seek corrections итоговый drift стабилизировался на `13 ms`.
- Следующая активная работа — Этап 1, фундамент production-репозитория.

## 0.0.4 - 2026-09-27

- `Вернуть оригинал` устанавливает ручной bypass для текущего Track ID и больше не активирует замену повторно через следующий snapshot.
- Bypass автоматически снимается после смены трека; повторное включение CELIKOM также разрешает новую попытку.
- Master time проецируется между snapshot-событиями, поэтому drift больше не рассчитывается относительно устаревшей позиции.
- Drift корректно учитывает циклический synthetic asset, если оригинальный трек длиннее тестового MP3.
- Короткий Yandex `video` со stream-хоста рекламы отклоняется, а playing audio имеет безопасный приоритет.
- Убраны дублирующие INIT при запуске heartbeat; добавлены regression-тесты live-находок.

## 0.0.3 - 2026-09-27

- Пустой рекламный `video` больше не может стать master player.
- В диагностику добавлены все обнаруженные media-кандидаты, их score и причина отклонения.
- Detached audio сохраняется как кандидат во время паузы; дополнительно наблюдаются вызовы `load()`.
- Heartbeat различает активную и фоновую вкладку, подтверждает каждый ping и автоматически переподключает bridge.
- Обновление из предыдущей PoC-версии останавливает старый controller перед внедрением нового.
- Добавлены regression-тесты выбора master media element.

## 0.0.2 - 2026-09-27

- Добавлено определение Track ID для новой разметки Яндекс Музыки без `/track/{id}` в player bar.
- Player metadata сопоставляется с track objects из `__STATE_PATCHES__` по названию, исполнителю, длительности и обложке.
- Добавлен ограниченный пассивный сбор track objects из JSON-ответов Яндекса для SPA-переходов и очереди.
- Popup автоматически восстанавливает content scripts в уже открытой вкладке через `chrome.scripting`.
- Добавлена защита от повторной инициализации и удаление устаревшего diagnostic overlay.
- Реальный сохранённый снимок страницы однозначно определяет Track ID `1944599` с confidence `245`.
- Добавлены regression-тесты нормализации artwork, state matching и fail-closed для дублей.

## 0.0.1 - 2026-09-20

- Создан первый воспроизводимый пакет `CELIKOM-POC-001`.
- Добавлены MAIN-world player probe и безопасный bridge в isolated content script.
- Реализованы локальная подмена, drift correction, generation guard и fail-open.
- Добавлены heartbeat watchdog, emergency restore и диагностический overlay.
- Добавлены RU/EN popup, локальный fixture, тесты и сборка ZIP.
