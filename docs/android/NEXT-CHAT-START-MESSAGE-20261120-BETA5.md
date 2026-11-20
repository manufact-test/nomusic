# CELIKOM Android A1 — первое сообщение следующему чату
Дата: 20.11.2026

Привет. Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай существующую работу строго с сохранённой точки. Не начинай проект заново и не меняй архитектуру.

**GitHub:** `manufact-test/nomusic`
**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
**HEAD на момент передачи:** `b5c25f8a42f9794615eedba430479f8cc172f315` — документационный коммит.
**Код BETA5:** `54452d21ae91a5c4c81b4b8ccf0f8d55e3fb17a8`.

Сначала прочитай:
1. `docs/android/NEXT-CHAT.md` — актуальная точка в самом верху.
2. `docs/android/CELIKOM-A1-RAMIL-AU-BETA3-FAILED-NEXT-CHAT-2026-11-20.md` — раздел **BETA5 owner-phone diagnostic result**.

## Что произошло

BETA5 проверен владельцем на HONOR 50 / Android 13 на Ramil' «Ау», publisher ID `144530503`. Звуковая подмена не сработала: альтернативная версия не слышна.

Диагностика: `CELIKOM-A1-Diagnostics-1795193426305.txt`.

Что работает:
- CELIKOM автоматически активируется из сохранённой сессии: `BETA_OWNER_AUTO_START=ENABLED`.
- `OWNER_ENABLED=ONE`.
- Кнопка статуса/TXT присутствует: `DIAGNOSTIC_UI=ATTACHED`.
- Proxy hook зарегистрирован и увидел создание одного proxy: `ISSUER_PROXY_HOOK_REGISTERED=ONE`, `ISSUER_PROXY_CREATED=ONE`.

Где обрывается:
- `ISSUER_METHOD_SELECTED=NONE`
- `ISSUER_HANDLER_INVOKE=NONE`
- `ISSUER_TRACKID=NONE)
- `EXACT_BETA_CREATOR=NONE`
- `ORIGINAL_SETTER=NONE)

Из-за этого не запускаются prefetch, owner resolve, signed MPEG, grant admission и alternate DataSource: `PREFETCH_STARTED=NONE`, `SIGNED_MPEG_READY=NONE`, `GRANT_ADMITTED=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN=NONE`, `AUDIO_READ=NONE`. `EXACT_PREPARE=FEW` само по себе не означает, что замена была допущена.

Оригинальный ExoPlayer продолжает нормально читать оригинальный звук: `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`, ошибок чтения нет. Итоговый статус: `CELIKOM_REPLACEMENT=NOT_CONNECTED`.

## Твоя первая задача

Не трогай нижние звенья, пока не исправлен первый разрыв.

В `ExitCallsiteWitness.java`, метод `hookConcretePublisherTrackIdProxy()`, текущий код ищет в загруженных `FileInfoApi` / `DownloadInfoApi` declared methods параметр String/number с Retrofit `@Query` или `@Path`, значение которого строго равно `trackId`. Proxy creation наблюдается, но метод не выбирается.

**Разберись именно с реальным runtime proxy:** какие интерфейсы он реализует, какие методы реально объявлены/унаследованы, какие аннотации присутствуют и какой classloader используется. Найди точную причину, почему метод selection не срабатывает. Не угадывай и не расширяй захват на любые String/number аргументы.

Сделай минимальное исправление, чтобы поймать только оригинальный издательский `trackId` в исходном request/Track scope и передать его дальше, не меняя оригинальный запрос и вызывая оригинальный handler ровно один раз. Добавь точечные regression tests и прогони JVM + Android ARM13 CI.

После получения реального `ISSUER_TRACKID` продолжай существующую цепочку по порядку: `EXACT_BETA_CREATOR` → `ORIGINAL_SETTER` → signed audio/grant → exact prepare → DataSource armed/open/read. Не перепрыгивай через проверки.

## Рабочие ограничения

- Не уходи в новые широкие исследования. Никаких AppMetrica/общих DEX-сканов/повторного анализа renderer, пока ранний issuer gate равен NONE.
- Не создавай новые диагностические APK без конкретного исправления и зелёного CI. Не проси владельца повторять тест до появления такого исправления.
- Не делай мелких промежуточных отчётов. Работай крупными законченными блоками; останавливайся только когда нужна помощь владельца или есть существенный проверенный результат.
- Не заявляй, что подмена работает, пока владелец реально не услышит альтернативные байты в оригинальном Яндекс-плеере.
- Сохрани один оригинальный проигрыватель и fail-closed: неизвестный трек всегда играет оригинал.

**Не изменять:** NAV40, NAV45, Test.50, Windows, backend/production, подпись и оригинальное приложение Яндекса. Не меняй единственную рабочую ветку.

Цель — не ещё одна диагностика, а работающая подмена в оригинальном Яндекс-плеере с нормальными Pause/Seek/Next/MyWave. Иди прямо к этому результату.
