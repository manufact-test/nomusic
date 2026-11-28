CELIKOM Android A1 — BETA37 NAV57 (HONOR 50 / Android 13)
28.11.2026. Приватная тестовая сборка для владельца. Не stable/OTA.

Что изменено после BETA36:
- NAV57 проверяет связь текущего SLOT_B MediaPeriod → DataSource и при renderer state != STATE_STARTED.
- Сверяются тот же holder, точный PeriodID (UID + оба индекса), источник периода и факт чтения альтернативных байтов.
- Проверка read-only: не меняет audio route, admission, grant или codec request и не доказывает слышимую подмену.
- NAV56 committed first-open source lineage сохранён.
- MP3 override выключен. BETA32 уже ломал воспроизведение; не повторять.
- Оригинальный Яндекс Музыки остаётся единственным плеером. Сервер, каталог, авторизация и grant не менялись.

Важно: CI/ARM13 PASS подтверждает только технический запуск и совместную установку, НЕ слышимую подмену.
Положительный LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS подтверждает, что альтернативные байты читает DataSource текущего MediaPeriod. Это ещё не доказательство decoder/PCM — результат нужно проверить прослушиванием.

Установка:
- Установить BETA37 поверх BETA36 на существующем Honor 50.
- Не удалять CELIKOM и не очищать данные или кеш.
- Убедиться, что статус CELIKOM — ВКЛ.

Проверка:
1. В оригинальном Яндекс Музыке открыть Ramil / 10AGE — «Ау», альбом 38902809, track 144530503, сегмент 00:43–00:54.
2. Убедиться, что трек запускается без ошибки Яндекса.
3. Проверить, слышна ли подменённая музыка.
4. Обычным коротким нажатием CELIKOM сохранить TXT после проверки.

Маркер сборки:
A1_TRACKID_BETA37_NAV57_PRESTART_PERIOD_SOURCE_LINK_20261128

В TXT проверить:
- LIVE_QUEUE_SLOT_B_TYPE1_NOT2_READ_MATCH
- LIVE_QUEUE_SLOT_B_TYPE1_NOT2_PERIOD_ID_SAME
- LIVE_PERIOD_SOURCE_LOOKUP_CALL / LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS (или EOS_UNKNOWN, если EOS accessor недоступен)
- ENGINE_HOLDER_TYPE1_STATE_NOT2 и ENGINE_HOLDER_TYPE1_STATE2

Не повторять NAV55 holder-аудит и MP3/AAC override без нового доказательства.
