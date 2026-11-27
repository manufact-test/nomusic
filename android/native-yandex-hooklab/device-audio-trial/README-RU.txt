CELIKOM Android A1 — BETA26 (HONOR 50 / Android 13)
27.11.2026. Экспериментальная диагностическая сборка для владельца. Не stable/OTA.

ВАЖНО: BETA26 временно возвращает оригинальную передачу codecs в Яндекс Музыке. Подмена CELIKOM всё ещё не доказана.

## Что показала диагностика BETA25

Серверная часть получила подтверждения:
OWNER_RESOLVE_APPROVED=ONE
SIGNED_AUDIO_READY=ONE
OWNER_AUDIO_RANGE_VALID=ONE
GRANT_ADMITTED=FEW
EXACT_PREPARE=FEW
DECISION_ALTERNATE=ONE

Но CELIKOM DataSource не был подключён:
DATASOURCE_ARMED=NONE
AUDIO_OPEN=NONE
AUDIO_READ=NONE
FIRST_OPEN_CANDIDATE_ACCEPTED=NONE
DEFERRED_ARM_ENTER=NONE

Одновременно с этим BETA25 реально переписывала исходный запрос FileInfoApi Яндекса:
ISSUER_CODEC_MP3_REQUESTED=ONE

То есть Яндекс получал запрос только на MP3, хотя CELIKOM-источник так и не был подключён. Это могло нарушать обычное воспроизведение «Ау», не давая никакой пользы для подмены.

## Что изменено в BETA26

- Отключено принудительное изменение codecs на "mp3".
- Исходный аргумент codecs оригинального FileInfoApi теперь передаётся Яндексу без изменений.
- Сохранены BETA25 счётчики отказов первого OPEN и отложенного подключения DataSource.
- Проверки допуска остались fail-closed.
- Сервер, каталог, подписанные разрешения, Range/HMAC, оригинальный APK Яндекса, Windows, stable Android и OTA не менялись.

Это точечное восстановление исходного codec negotiation, а не заявление об исправленной подмене.

## Проверка на телефоне

1. Установить BETA26 поверх BETA25. Не удалять CELIKOM, не очищать данные и кеш.
2. Открыть оригинальный Яндекс Музыку и запустить Ramil / 10AGE — «Ау» из исходного альбома 38902809, оригинальный track ID 144530503.
3. Проверить участок 00:43–00:54 и отметить, появляется ли «Невозможно воспроизвести».
4. Затем запустить другую песню, на которой раньше были пробелы в начале.
5. Не перезапускать приложение между двумя проверками. После обеих выгрузить один CELIKOM diagnostic TXT и отправить его.

## Что проверить в новой диагностике

- ISSUER_CODEC_MP3_REQUESTED должен остаться NONE: CELIKOM больше не меняет codecs запроса Яндекса.
- FIRST_OPEN_HOOK_ENTERED и причины FIRST_OPEN_* покажут, дошёл ли источник до первого OPEN и почему кандидат отклонён.
- FIRST_OPEN_CANDIDATE_ACCEPTED → FIRST_OPEN_SETTER_MATCH → FIRST_OPEN_DEFERRED_ARM_CALLED → DEFERRED_ARM_ENTER → DEFERRED_ARM_ACCEPTED → DATASOURCE_ARMED → AUDIO_OPEN → AUDIO_READ.

Если «Ау» снова воспроизводится, это подтвердит, что request-only MP3 override ломал обычный путь. Это ещё не будет доказательством подмены CELIKOM. Если ошибка останется, будем отдельно разбирать оригинальный Yandex PlaybackException по следующей диагностике.

AUDIO_STAGE_B_STATUS / CELIKOM_REPLACEMENT=NOT_CONNECTED — статический legacy-маркер. Не использовать его отдельно как runtime-вердикт.
