CELIKOM Android A1 — BETA25 (HONOR 50 / Android 13)
27.11.2026. Экспериментальная диагностическая сборка для владельца. Не stable/OTA.

ВАЖНО: BETA25 добавляет диагностику отказа на первом OPEN и отложенного подключения DataSource. Это НЕ заявление, что воспроизведение уже исправлено.

## Что показала BETA24

Серверная часть получила подтверждения:
OWNER_RESOLVE_APPROVED=ONE
SIGNED_AUDIO_READY=ONE
OWNER_AUDIO_RANGE_VALID=ONE
GRANT_ADMITTED=FEW
EXACT_PREPARE=FEW
DECISION_ALTERNATE=FEW

Но подтверждённого подключения альтернативного CELIKOM DataSource не было:
DATASOURCE_ARMED=NONE
AUDIO_OPEN=NONE
AUDIO_READ=NONE
Успешный AUDIO_EXO_FIRST_OPEN_ARM не зарегистрирован.

При этом оригинальные Exo-источники Яндекса открывались и читались:
EXO_OPEN_OK=MANY
EXO_READ_POSITIVE=MANY
EXO_IO_FAILURE=NONE

Это подтверждает работу наблюдения оригинального потока, но не доказывает воспроизведение альтернативного аудио. Счётчик TRACK_WRAPPER_LINK_RESTORED=NONE сам по себе не является ошибкой: это только число восстановлений; обычные TRACK_WRAPPER_LINK и другие связи в BETA24 присутствовали.

Точная причина, по которой цепочка не доходила до DATASOURCE_ARMED, в BETA24 не экспортировалась.

## Что добавлено в BETA25

Новые счётчики выгружаются вместе с диагностикой:

- AUDIO_STAGE_B_SUMMARY: FIRST_OPEN_HOOK_ENTERED, FIRST_OPEN_CANDIDATE_REJECTED, причины отказа кандидата, FIRST_OPEN_CANDIDATE_ACCEPTED, FIRST_OPEN_SETTER_MATCH/MISSING, FIRST_OPEN_DEFERRED_ARM_CALLED/ACCEPTED/REJECTED и FIRST_OPEN_ARM_EXCEPTION.
- AUDIO_NATIVE_RENDERER_SUMMARY: FIRST_OPEN_SETTER_CHECK и отдельные причины отказа точного setter.
- AUDIO_EARLY_ADMISSION_SUMMARY: DEFERRED_ARM_ENTER и причины отказа отложенного подключения — отсутствие подтверждённого разрешения, несовпадение поколения, неподтверждённый prepare, несовпадение исходного источника, выключенный owner или отказ native route.

Значения агрегированы в NONE / ONE / FEW / MANY. Сырые ID, URL, адреса объектов и аудиобайты не экспортируются.

Проверки допуска остались fail-closed. Сервер, подписанный оригинальный Яндекс, codec negotiation, Windows, stable/OTA и архитектура плеера не менялись. Поведение подмены намеренно не ослаблялось.

## Проверка на телефоне

1. Установить BETA25 поверх BETA24. Не удалять приложение, не очищать данные и кеш.
2. Открыть оригинальный Яндекс Музыку и запустить «Ау» Рамиля/10AGE из исходного альбома. Не выбирать MyWave.
3. Зафиксировать, появляется ли сообщение «Невозможно воспроизвести».
4. Затем запустить другую песню, на которой раньше были пробелы в начале.
5. Не перезапускать приложение между этими двумя проверками. После обеих выгрузить один CELIKOM diagnostic TXT и отправить его.

## Как читать новые счётчики

- FIRST_OPEN_HOOK_ENTERED=NONE: до нового first-open наблюдателя не дошёл вызов открытия источника.
- FIRST_OPEN_CANDIDATE_REJECTED: смотреть конкретную причину FIRST_OPEN_* — потерянное/неоднозначное рождение, touched source, sibling, wrapper/factory link или creator/album mismatch.
- FIRST_OPEN_CANDIDATE_ACCEPTED есть, но FIRST_OPEN_SETTER_MISSING: смотреть AUDIO_NATIVE_RENDERER_SUMMARY / FIRST_OPEN_SETTER_*.
- FIRST_OPEN_SETTER_MATCH и DEFERRED_ARM_ENTER есть: смотреть AUDIO_EARLY_ADMISSION_SUMMARY / DEFERRED_ARM_*.
- DEFERRED_ARM_ACCEPTED и DATASOURCE_ARMED подтверждают прохождение gate; затем проверить AUDIO_OPEN и AUDIO_READ.
- Если arm принят, источник открывается/читается, но Яндекс всё равно показывает ошибку, следующий отдельный этап — диагностика downstream decoder/player error. BETA25 не заявляет, что уже фиксирует сам PlaybackException.

AUDIO_STAGE_B_STATUS / CELIKOM_REPLACEMENT=NOT_CONNECTED — статический legacy-маркер. Не использовать его отдельно как runtime-вердикт.
