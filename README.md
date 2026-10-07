# CELIKOM

CELIKOM подменяет звук только для точно определённого трека в поддерживаемом веб-плеере. Сам музыкальный сервис остаётся источником интерфейса, очереди и состояния воспроизведения.

Обязательный технический gate `CELIKOM-POC-001` закрыт 7 октября 2026 года на версии v0.0.4. Безопасный playback-механизм доказан; следующая активная работа — Этап 1, фундамент production-репозитория. Backend, аккаунты, подписки и пользовательские загрузки добавляются последовательно после переноса подтверждённых PoC-механизмов.

## Текущий результат

- Chromium Manifest V3 unpacked extension.
- Диагностика exact Track ID и исходного media player, включая актуальную разметку Яндекс Музыки.
- Сопоставление нижнего player bar со структурированным состоянием страницы по title, artist, duration и artwork.
- Fail-closed выбор master player: пустые и рекламные media elements не участвуют в подмене.
- Самовосстановление content scripts в уже открытой вкладке без обязательного ручного refresh.
- Один настраиваемый Track ID сопоставляется с локальным синтетическим MP3.
- Replacement следует за play, pause, seek, playback rate и сменой трека.
- Drift correction с проекцией master time между snapshot-событиями.
- Аварийное восстановление original audio и ручной bypass текущего трека.
- Heartbeat watchdog восстанавливает звук, если extension-контекст исчез.
- Локальный fixture и автоматические тесты чистой логики.

## Быстрый запуск

1. Выполнить `npm test`.
2. Выполнить `npm run validate`.
3. Открыть `chrome://extensions`, включить режим разработчика и выбрать `Load unpacked`.
4. Указать каталог `spikes/player-poc`.
5. Открыть Яндекс Музыку и запустить любой трек.
6. Открыть popup CELIKOM, нажать `Использовать текущий ID`, затем `Сохранить`.
7. Перезапустить тот же трек и проверить play, pause, seek, next и previous.
8. В любой момент кнопка `Вернуть оригинал` останавливает replacement и оставляет текущий трек на оригинале до его смены.

Для безопасного локального прогона без Яндекс Музыки выполните `npm run fixture`, затем откройте `http://localhost:4173/album/1/track/424242`.

## Сборка

`npm run build` создаёт проверенные ZIP в `dist/CELIKOM-POC-001-v0.0.4.zip` и `dist/CELIKOM-POC-001-v0.0.4-source.zip`.

## Статус gate

Автоматические проверки, локальный fixture и финальный ручной прогон на реальном авторизованном веб-плеере пройдены. Exact Track ID, replacement, pause/resume, seek, track change, manual bypass, fail-open и отсутствие stuck mute/double audio подтверждены. Подробные результаты находятся в `docs/test-plans/CELIKOM-POC-001.md`.

Следующая ветка разработки: `feature/repository-foundation`.
