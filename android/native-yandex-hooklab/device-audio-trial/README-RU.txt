CELIKOM Android A1 — RAMIL' «АУ», BETA3 (HONOR 50 / Android 13)
Дата: 20.11.2026. Подписанная испытательная сборка, не стабильный релиз.

1. Ставить поверх уже установленного CELIKOM A1: не удалять данные, оригинальную Яндекс.Музыку не трогать.
2. Открыть CELIKOM A1. В углу должна быть кнопка «CELIKOM BETA: ВЫКЛ». Нажать, войти в отдельный аккаунт CELIKOM и дождаться статуса «ВКЛ».
3. В Яндекс.Музыке внутри CELIKOM открыть именно 10AGE, Ramil' — «Ау» (2019): https://music.yandex.ru/album/38902809/track/144530503
4. Если песня уже играла при включении, переключить на другую и вернуться. Слушать примерно 00:43–00:54: по этому фрагменту ранее сравнивались цензурная и полная версии.
5. Если замена слышна, проверить Pause/Resume, Seek, Next и возврат. Если замена не слышна, НЕ переустанавливать приложение — один раз нажать «Диагностика NAV9» и прислать TXT из Загрузки / CELIKOM A1.
6. Новая диагностика содержит event=AUDIO_TRACKID_BETA с этапами ISSUER_TRACKID, EXACT_BETA_CREATOR, ORIGINAL_SETTER, OWNER_ENABLED, PREFETCH_STARTED, SIGNED_MPEG_READY, OWNER_RESOLVE_REQUEST, GRANT_ADMITTED, EXACT_PREPARE, DECISION_ALTERNATE, DATASOURCE_ARMED, AUDIO_OPEN, AUDIO_READ. Все счётчики только NONE/ONE/FEW/MANY — ни URL, ни токенов, ни ID пользователя.

Новый путь допускает оригинальный publisher trackId=144530503 + истинный объект Track + тождественный оригинальный tCa wrapper + успешный original source setter. Отсутствующий оригинальный Album не подделывается: wrapper — только временный scope token для явно разрешённой beta. Перед аудиоподменой требуются одобренная версия, активный CELIKOM entitlement, подписанный HTTPS URL, MPEG-совместимость и реальный HTTP206. Original ExoPlayer один. Если связи с Exo DataSource нет или таймаут — остаётся оригинал.

Есть ещё два ранее разрешённых тестовых ID (RASKOL 42884423, Лёша Свик 39949113), но основной следующий тест только «Ау». CI не доказывает слышимую подмену.

Техническая отметка испытания BETA3: оригинальные NAV45 read-only счётчики сохраняются для контроля совместимости. Проверять новую цепочку только по DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA_RAMIL_AU_20261120 и AUDIO_TRACKID_BETA этапам. NOT_CONNECTED старого NAV45 не является статусом beta-подмены.
