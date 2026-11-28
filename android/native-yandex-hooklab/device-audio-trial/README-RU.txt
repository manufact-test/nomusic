CELIKOM Android A1 — BETA34 (HONOR 50 / Android 13)
28.11.2026. Приватная тестовая сборка для владельца. Не stable/OTA.

Что исправлено после BETA33:
- BETA33 теряла точную связь DataSource с Factory, если вложенный $b.for возвращал источник до того, как внешний c.for успевал зарегистрировать descriptor → factory.
- Первый open в таком случае отклонялся как FIRST_OPEN_BIRTH_NOT_FOUND, после чего сам original open помечал объект touched. Повторно разрешать такой источник нельзя.
- BETA34 временно удерживает только точные Java identity source + nested factory в пределах вызова внешнего c.for. После возврата c.for и регистрации точного factory link выполняется backfill по единственному проверенному пути outer → nested factory.
- Если путь отсутствует, неоднозначен, источник уже touched или фабрика конфликтует, кандидат остаётся отклонённым. Проверка touched не ослаблена.
- Оригинальные codec-запросы Яндекса не меняются. MP3 override выключен.
- NAV53 pending/committed pin сохраняется: поздние sibling/prefetch DataSource не могут затереть уже выбранный источник.
- Оригинальный Яндекс Музыки остаётся единственным плеером. Сервер, каталог, авторизация и grant не менялись.

Установка:
- Установить BETA34 поверх BETA33 на существующем Honor 50.
- Не удалять CELIKOM и не очищать данные или кеш.
- Убедиться, что статус CELIKOM — ВКЛ.

Проверка:
1. В оригинальном Яндекс Музыке проверить Ramil / 10AGE — «Ау», альбом 38902809, track 144530503, сегмент 00:43–00:54.
2. Убедиться, что трек запускается без ошибки Яндекса.
3. Проверить вторую песню, у которой раньше были пропуски в начале.
4. Отдельно проверить, слышна ли именно альтернативная музыка внутри оригинального приложения Яндекс Музыки.
5. Обычным коротким нажатием CELIKOM сохранить TXT после проверки обеих песен.

Маркер сборки:
A1_TRACKID_BETA34_NAV54_NESTED_FACTORY_BIRTH_ORDER_20261128

В TXT проверить:
- FIRST_OPEN_CANDIDATE_ACCEPTED
- FIRST_OPEN_SOURCE_ALREADY_TOUCHED
- FIRST_OPEN_BIRTH_NOT_FOUND
- DATASOURCE_ARMED / AUDIO_OPEN / AUDIO_READ
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS

Не считать CI PASS, DATASOURCE_ARMED или AUDIO_READ доказательством слышимого звука.
