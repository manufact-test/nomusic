CELIKOM Android A1 — BETA36 NAV56 (HONOR 50 / Android 13)
28.11.2026. Приватная тестовая сборка для владельца. Не stable/OTA.

Что изменено после BETA35:
- BETA35 NAV55 подтвердил прямой активный MediaPeriod o96 и ту же identity при select, attach и renderer read.
- NAV56 сохраняет уже проверенную creator/source lineage после успешного first-open arm: live lookup больше не зависит от повторного чтения ограниченных creator/Flow registries, которые могут исчезнуть после admission.
- Для незафиксированного или отклонённого first-open прежняя строгая проверка creator остаётся обязательной. Никаких новых разрешений на подмену не добавлено.
- Оригинальные codec-запросы Яндекса не меняются. MP3 override выключен.
- NAV53 pending/committed pin сохраняется: поздние sibling/prefetch DataSource не могут затереть уже выбранный источник.
- NAV56 меняет только read-only связь renderer → committed DataSource; сам audio route, admission и codec requests не менялись.
- Оригинальный Яндекс Музыки остаётся единственным плеером. Сервер, каталог, авторизация и grant не менялись.

Установка:
- Установить BETA36 поверх BETA35 на существующем Honor 50.
- Не удалять CELIKOM и не очищать данные или кеш.
- Убедиться, что статус CELIKOM — ВКЛ.

Проверка:
1. В оригинальном Яндекс Музыке проверить Ramil / 10AGE — «Ау», альбом 38902809, track 144530503, сегмент 00:43–00:54.
2. Убедиться, что трек запускается без ошибки Яндекса.
3. Проверить вторую песню, у которой раньше были пропуски в начале.
4. Отдельно проверить, слышна ли именно альтернативная музыка внутри оригинального приложения Яндекс Музыки.
5. Обычным коротким нажатием CELIKOM сохранить TXT после проверки обеих песен.

Маркер сборки:
A1_TRACKID_BETA36_NAV56_COMMITTED_SOURCE_LINK_20261128

В TXT проверить:
- FIRST_OPEN_CANDIDATE_ACCEPTED
- FIRST_OPEN_SOURCE_ALREADY_TOUCHED
- FIRST_OPEN_BIRTH_NOT_FOUND
- DATASOURCE_ARMED / AUDIO_OPEN / AUDIO_READ
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS

Не считать CI PASS, DATASOURCE_ARMED или AUDIO_READ доказательством слышимого звука.
