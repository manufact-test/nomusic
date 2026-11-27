CELIKOM Android A1 — BETA24 (HONOR 50 / Android 13)
27.11.2026. Только экспериментальная владелецкая сборка, не stable/OTA.

## Что показала BETA23

Серверная часть прошла: OWNER_RESOLVE_APPROVED=ONE, SIGNED_AUDIO_READY=ONE, OWNER_AUDIO_RANGE_VALID=ONE, GRANT_ADMITTED=ONE, DECISION_ALTERNATE=ONE.

Но аудиопоток не был подключён: DATASOURCE_ARMED=NONE, AUDIO_OPEN=NONE, AUDIO_READ=NONE. TRACK_DESCRIPTOR_FACTORY_LINK=NONE и TRACK_FACTORY_SOURCE_LINK=NONE.

При этом активный оригинальный MediaPeriod совпадал с Player source setter: LIVE_PERIOD_DIRECT_LO96=FEW и LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=FEW. Точная причина отказа — отсутствующая связь TrackWrapper с creator Track+Album. Диагностика показывает, что запись рождения tCa ещё существует, но связь отсутствует. Наиболее вероятно, короткая таблица из 16 ссылок вытеснила её; код не умел восстановить связь для трека, уже находившегося в Flow при создании wrapper.

Отдельно: ISSUER_CODEC_MP3_REQUESTED=NONE. Поэтому предыдущая настройка запроса MP3 в этой сессии фактически не сработала. Не считать, что BETA23 выбрала MP3.

## Что изменено в BETA24

- При рождении wrapper сохраняются слабые ссылки на точные исходные Track и Album также для случая, когда Track уже находится в Flow (scope 14).
- Если короткая таблица wrapper-связей вытеснила запись, связь восстанавливается только по уникальной записи исходного tCa creator и тем же живым объектам Track+Album.
- Другой wrapper для того же Track, неоднозначное рождение, изменившийся Album или потерянные ссылки по-прежнему отклоняются.
- Добавлена отдельная метка TRACK_WRAPPER_LINK_RESTORED и проверка связи с текущим original MediaPeriod.
- Не добавлялся второй плеер. Сервер, оригинальный подписанный Yandex, стабильная Android/Windows и OTA не менялись.

## Проверка на телефоне

1. Установить BETA24 поверх BETA23, не удалять данные и не очищать кеш.
2. Открыть Рамиль/10AGE «Ау» из альбома 38902809 — исходный ID 144530503. Не выбирать MyWave.
3. Послушать участок 00:43–00:54.
4. Если подмены нет, экспортировать TXT и отправить его сюда.

В TXT проверить цепочку:
TRACK_WRAPPER_LINK_RESTORED → TRACK_DESCRIPTOR_FACTORY_LINK → TRACK_FACTORY_SOURCE_LINK → AUDIO_EXO_FIRST_OPEN_ARM → DATASOURCE_ARMED → AUDIO_OPEN → AUDIO_READ.

Также проверить CODEC_CONFIG_MPEG/AAC и ISSUER_CODEC_MP3_REQUESTED. Наличие одной только метки восстановления или чтения байтов не доказывает слышимую подмену. Результат BETA24 на телефоне заранее не считать успешным.
