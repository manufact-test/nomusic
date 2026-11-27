CELIKOM Android A1 — BETA30 (HONOR 50 / Android 13)
27.11.2026. Приватная диагностическая сборка для владельца. Не stable/OTA.

BETA29 подтвердила чтение альтернативных аудиобайтов, но слышимой подмены
не было. BETA30 добавляет NAV51: сохраняет точное подтверждение связи
Track → Descriptor → Factory → DataSource после открытия источника, даже
если временные слабые ссылки на Descriptor и Factory больше недоступны.
При смене Descriptor/Factory подтверждение сбрасывается и строится заново.

Аудиомаршрут, декодер, сервер, авторизация и оригинальный плеер не менялись.
Добавлены счётчики причин, чтобы различать отсутствие creator-связи,
wrapper-связи, factory/source-привязки и потерю самого DataSource.

Короткое нажатие CELIKOM сохраняет TXT; удержание открывает меню проверки/
входа CELIKOM. Ошибки конфигурации, сессии и активации различаются.
HTTP 401 при обновлении или активации требует повторного входа. Не повторяем
автоматически потенциально уже использованный refresh token после сбоя.
Вход только по собственной учётной записи CELIKOM. Не меняем авторизацию
Яндекса, сервер, каталог, подписанные разрешения, Windows, stable или OTA.

Установить поверх BETA29, не удалять приложение и не очищать данные.
Если статус не ВКЛ, удержать CELIKOM и действовать по показанному состоянию
сессии. Если статус уже ВКЛ, повторно входить не нужно.

Затем проверить:
- Ramil / 10AGE — «Ау», альбом 38902809, track 144530503, 00:43–00:54.
- Вторую песню, у которой раньше были пробелы в начале.

Обычным коротким нажатием экспортировать TXT после проверки обеих песен.

В TXT важны NAV50 и новые NAV51-счётчики:
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS — тот же
  DataSource с альтернативными байтами найден в текущем non-EOS периоде.
- LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD — текущий период использует
  другой DataSource.
- LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD — у источника текущего
  периода нет активного альтернативного маршрута.
- LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD — связь
  текущего Track wrapper с DataSource не удалось подтвердить.
- LIVE_PERIOD_SOURCE_CREATOR_MATCH / CREATOR_MISSING — удалось ли подтвердить
  точный creator Track для wrapper текущего периода.
- LIVE_PERIOD_SOURCE_WRAPPER_LINK_MISSING — отсутствует точная связь wrapper.
- LIVE_PERIOD_SOURCE_FACTORY_LINK_UNBOUND — источник ещё не подтверждён точной
  цепочкой Factory → DataSource.
- LIVE_PERIOD_SOURCE_INSTANCE_NOT_LINKED / INSTANCE_WEAK_LOST — DataSource
  отсутствует в связи либо его weak reference уже потеряна.
- LIVE_PERIOD_SOURCE_REVERSE_LINK_MISMATCH — обратная привязка DataSource
  указывает не на ту же связь.
- LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED — точный DataSource успешно найден.

BETA30 — диагностическая сборка, не подтверждённое исправление слышимой
аудиоподмены. Даже совпадение DataSource ещё не доказывает слышимый звук;
итог устанавливается по TXT и отдельной проверке звука на телефоне.
