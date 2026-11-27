CELIKOM Android A1 — BETA27 (HONOR 50 / Android 13)
27.11.2026. Экспериментальная сборка для владельца. Не stable/OTA.

BETA26: «Ау» снова воспроизводится, ISSUER_CODEC_MP3_REQUESTED=NONE.
Подмена не работает: DATASOURCE_ARMED/AUDIO_OPEN/AUDIO_READ=NONE.
Наблюдалась точная связь descriptor→factory→source, но первый OPEN
отклонил кандидат с FIRST_OPEN_DESCRIPTOR_LOST=ONE.

BETA27: удерживается только уже подтверждённый объект дескриптора в
существующей ограниченной цепочке до первого касания источника.
При касании/смене дескриптора ссылка освобождается. Проверки identity,
Track/Album, поколения, setter, разрешения и запрет позднего переключения
не ослаблены. Исходные codecs Яндекса по-прежнему не меняются.
Не изменены сервер, каталог, Windows, stable, OTA, подписанные разрешения.

Проверка:
1. Установить BETA27 поверх BETA26, не удалять приложение и не очищать данные.
2. Запустить «Ау» Ramil / 10AGE из альбома 38902809, track 144530503.
3. Послушать 00:43–00:54 и проверить, слышна ли подмена.
4. Проверить другую песню с прежними пробелами в начале, затем экспортировать TXT.

Ожидаем: ISSUER_CODEC_MP3_REQUESTED=NONE; исчезновение конкретного отказа
FIRST_OPEN_DESCRIPTOR_LOST; FIRST_OPEN_CANDIDATE_ACCEPTED → FIRST_OPEN_SETTER_MATCH
→ FIRST_OPEN_DEFERRED_ARM_CALLED → DEFERRED_ARM_ENTER → DEFERRED_ARM_ACCEPTED
→ DATASOURCE_ARMED → AUDIO_OPEN → AUDIO_READ. Только звук на телефоне
подтверждает реальную подмену. CI не является акустическим доказательством.
