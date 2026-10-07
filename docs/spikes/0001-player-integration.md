# CELIKOM POC 001 Player Integration

## Статус

Этап 0 закрыт 7 октября 2026 года. На реальном авторизованном Яндекс-плеере подтверждены exact Track ID, detached audio master, guard, replacement, pause/resume, seek, queue/track change, manual bypass, restore, SPA recovery и серия быстрых переключений. Блокирующих дефектов в финальном прогоне v0.0.4 не обнаружено.

Финальные diagnostics подтвердили Track ID `38077230` и `37889209` с confidence 240–260. Известный рекламный `video` был отклонён как `known-ad-media`, рабочий `audio` выбран master element, bridge оставался ready/healthy. После намеренных перемоток SyncEngine сходился к итоговому drift `13 ms`; при смене трека выполнялась последовательность `RESTORING · track-changed` → `IDLE · original restored`.

## Принятое решение

Исходный player всегда остаётся master-state. CELIKOM не управляет очередью и не пытается подменять интерфейс сервиса. MAIN-world bridge только наблюдает исходные media elements, определяет Track ID, применяет временный audio guard и передаёт нормализованное состояние isolated controller. ReplacementPlayer работает отдельно и повторяет currentTime, play, pause, playbackRate, volume и mute.

## Как определяется точный Track ID

Кандидаты собираются из нескольких независимых сигналов и получают вес:

1. Track objects из `window.__STATE_PATCHES__` и встроенных state scripts Яндекс Музыки.
2. Ограниченно отслеживаемые JSON-ответы только с доменов Яндекса для данных, загруженных после SPA-перехода.
3. Название, исполнитель, artwork и длительность из Media Session, нижнего player bar и active track card.
4. Ссылка `/track/{id}`, `data-track-id`, `aria-current` и active/playing class для старой или альтернативной разметки.
5. URL текущей страницы только как слабый fallback; он не считается достаточным без дополнительного подтверждения.

Для актуального снимка search page нижний player bar не содержит Track ID. Сопоставление `Папиросы` / `Зануда` / `201 s` / artwork с 31 track object выбирает exact ID `1944599` с четырьмя совпавшими сигналами и большим отрывом от второго кандидата.

Подмена запрещена, если лучший кандидат не достиг порога уверенности или два разных ID имеют близкий вес. В диагностике остаётся ранжированный список кандидатов, чтобы на живом плеере быстро подтвердить фактический hook.

## Как определяется master player

Bridge наблюдает `audio` и `video` в DOM, а также detached media elements, прошедшие через `play()`, `pause()` или `load()`. Кандидаты ранжируются по текущему воспроизведению, readyState, duration, currentTime, source и последнему media event; аудио имеет приоритет над коротким video stream. Пустой media element и известный рекламный `video` отклоняются fail-closed. Элемент CELIKOM отмечен `data-celikom-replacement=true` и никогда не может стать master.

## Safe mute и restore

Перед стартом replacement сохраняются исходные `muted` и `volume`. Bridge принудительно ставит original element в muted, продолжая отслеживать пользовательские изменения громкости. При restore возвращается последнее сохранённое пользовательское состояние. Любая ошибка запуска replacement немедленно вызывает emergency restore.

Ручная команда `Вернуть оригинал` дополнительно фиксирует bypass текущего Track ID. Поэтому очередной player snapshot не запускает replacement снова. Bypass снимается при переходе на другой трек либо после явного повторного включения автоматической замены.

Между snapshot-событиями controller проецирует позицию master по `observedAt` и `playbackRate`. Drift сравнивается с этой текущей оценкой, а не с устаревшим `currentTime`; короткий synthetic asset учитывается циклически.

На PoC штатный UI сервиса может визуально показать original player как muted. Это допустимая диагностическая оговорка Этапа 0. После подтверждения hook нужно отдельно выбрать production-механику, которая минимально влияет на индикатор громкости.

## Fail open

Восстановление запускается при смене Track ID, смене master element, media error, окончании трека, отключении CELIKOM, изменении настроек, ошибке bridge, ошибке `play()`, stale async activation и уходе со страницы.

MAIN-world bridge получает heartbeat раз в секунду и отвечает подтверждением. В видимой вкладке потеря heartbeat считается аварией через 12 секунд: bridge самостоятельно останавливает replacement element, снимает guard и восстанавливает original audio. Для фоновой вкладки предусмотрено окно 120 секунд из-за browser timer throttling; при возврате вкладки heartbeat немедленно перепроверяется и bridge переподключается.

## Сознательно не используемые подходы

- Извлечение или перехват защищённого audio stream.
- Cookies, токены или данные аккаунта музыкального сервиса.
- Глобальный monkey-patch `JSON.parse` или чтение ответов не с доменов Яндекса.
- Artist плюс title как автоматическая замена exact Track ID.
- Управление очередью CELIKOM вместо штатного player.
- Backend, авторизация и billing до закрытия playback gate.

## Что подтвердил живой тест

- Связка player metadata → state track object остаётся стабильной на разных типах страниц.
- Выбранный master media element остаётся корректным на album, playlist, search и queue страницах.
- SPA не заменяет необходимые узлы способом, который теряет события.
- Autoplay policy разрешает replacement после обычного пользовательского запуска трека.
- Mute/restore не конфликтует с внутренним состоянием веб-плеера.
- Не возникает persistent double audio или stuck mute после 20 и более быстрых переходов.

## Решение

Playback-механизм принимается как доказанный для продолжения MVP. В production-код переносятся только подтверждённые механизмы: exact Track ID ranking, master media selection, MAIN-world bridge, state projection, drift correction, manual bypass и fail-open restore. Диагностический overlay остаётся только инструментом developer mode и не определяет будущий пользовательский интерфейс.
