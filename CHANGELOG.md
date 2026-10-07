# Changelog

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
