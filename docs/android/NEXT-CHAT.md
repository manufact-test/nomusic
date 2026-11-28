# CELIKOM Android A1 — единственный актуальный handoff

Дата состояния: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Последний source HEAD: `a513e1045bc5fdd76beb06e697399c9b48c6e351`  
Source commit used for BETA34 build: `a513e1045bc5fdd76beb06e697399c9b48c6e351`

## Цель и границы

Добиться слышимой подмены аудио внутри **оригинального приложения Яндекс Музыки**. CI, запуск приложения, получение подписанных байтов и диагностические счётчики не являются доказательством успеха.

Работать только в указанной Android experiment-ветке. Не добавлять второй плеер. Не менять сервер, каталог, авторизацию, Windows, stable Android, OTA или `main` без отдельной доказанной необходимости и разрешения владельца.

## Предыдущая проверка — BETA33: НЕ РАБОТАЕТ

Владелец проверил BETA33 и сообщил: «Не работает».

Свежая диагностика: `CELIKOM-A1-Diagnostics-1795862373809.txt`  
Маркер сборки в диагностике: `A1_TRACKID_BETA33_NAV53_FIRST_OPEN_SOURCE_PIN_20261128`.

Что подтверждено диагностикой:
- `OWNER_ENABLED=ONE`, целевой track allowlisted — `ONE`.
- `SIGNED_MPEG_READY=ONE`, `OWNER_RESOLVE_APPROVED=ONE`, `GRANT_ADMITTED=ONE`.
- `EXACT_PREPARE=ONE`, `DECISION_ALTERNATE=ONE`.
- MP3 override отключён: `ISSUER_CODEC_MP3_REQUESTED=NONE`.
- `AUDIO_STAGE_B_STATUS=NOT_CONNECTED`.
- `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN=NONE`, `AUDIO_READ=NONE`.
- `FIRST_OPEN_HOOK_ENTERED=MANY`, `FIRST_OPEN_CANDIDATE_REJECTED=MANY`.
- Причины отказа: `FIRST_OPEN_SOURCE_ALREADY_TOUCHED=MANY`, `FIRST_OPEN_BIRTH_NOT_FOUND=FEW`.
- `FIRST_OPEN_CANDIDATE_ACCEPTED=NONE`, `FIRST_OPEN_SETTER_MATCH=NONE`.
- `TRACK_SOURCE_OPEN_LINK=NONE`, `TRACK_SOURCE_READ_LINK=NONE`.
- Чтение альтернативного источника в текущем renderer period не подтверждено; `LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD=FEW`.

Счётчики диагностики агрегированы по процессу: не приписывать каждое событие конкретной песне без отдельной корреляции.

**Вывод:** grant/resolve и решение `ALTERNATE` доходят до pre-prepare, но точный DataSource не проходит first-open admission. До `DATASOURCE_ARMED` выполнение не доходит. Это была точка отказа BETA33. Аудиоподмена не подтверждена.

## Что уже сделано в BETA33

- Откатили request-only MP3 override: оригинальные codec-запросы Яндекса не меняются.
- Добавили NAV53 first-open pin: pending/committed привязка удерживает точный DataSource и не позволяет позднему sibling/prefetch объекту заменить уже выбранный источник.
- Source commit: `6972ee7fbee06be8eec90be51f886deb48ef265b`.
- Owner build/export, JVM и clone-alone ARM13 на run `46132374238`, `46132374233`, `46132374224` прошли. Это не доказывает работу на телефоне.
- BETA33 уже собрана, подписана, доставлена и проверена владельцем. Не пересобирать и не доставлять её повторно.

## BETA34 NAV54 — функциональная правка внесена

**Кодовый разрыв, который исправлен:**
- Внешний `c.for` hook вызывает `chain.proceed()`, а `onExoFactoryCreated()` регистрирует точную связь descriptor → outer factory только после возврата `chain.proceed()`.
- Вложенный `$b.for` hook мог вернуть DataSource внутри этого `chain.proceed()`. В этот момент `findByFactory(nestedFactory)` ещё не находил outer link; `exactOuterFactoryForNested()` проверял только уже зарегистрированные links. Source birth терялся, и последующего backfill не было.
- Open hook сначала вызывает `exactFreshCreatorOrBetaAtFirstOpen(source)`, а затем `onExoSourceInstanceOpenAttempt(source)`. Поэтому при `BIRTH_NOT_FOUND` первый open отклонялся, после чего объект помечался `touched`; последующие попытки правильно отклонялись как `SOURCE_ALREADY_TOUCHED`.

**Что изменено в BETA34:**
- Вокруг точного `c.for` вызова добавлен ограниченный ThreadLocal scope.
- Вложенный `$b.for` сохраняет только weak Java identity пары source + nested factory.
- После `onExoFactoryCreated()` выполняется backfill только по проверенному bounded path outer → nested factory.
- Для привязки требуются одновременно unique path и отсутствие другого outer, который может ссылаться на тот же nested factory. Неоднозначные/shared пути отклоняются.
- Переполнение scope/birth history остаётся fail-closed.
- Уже touched DataSource не становится кандидатом после backfill. `markSourceTouched()` и запрет после первого original I/O не ослаблялись.
- NAV53 pending/committed first-open pin сохранён: поздний sibling/prefetch не может заменить уже выбранный source.
- Не менялись авторизация, resolve, signed grant, сервер, каталог, codec-запросы Яндекса и единственный оригинальный плеер. MP3 override не возвращён.

Маркер BETA34: `A1_TRACKID_BETA34_NAV54_NESTED_FACTORY_BIRTH_ORDER_20261128`.

**Регрессии:**
- `NativeRamilTrackOnlyLineageTest`: nested source создаётся до outer factory link; после регистрации link выполняется backfill, first-open admission проходит, а после original open тот же объект снова отклоняется как touched.
- `NativeExoFactoryProductWitnessTest`: проверяются unique и ambiguous reference paths; неоднозначная ссылка учитывается как возможная связь и блокирует admission.
- Python static hook-order и owner artifact tests.

## Проверки и доставка

- Main JVM job `jvm-issuer-proxy-contract`, run `46138985741`: **PASS**. Включает Stage B Python tests, `NativeRamilTrackOnlyLineageTest`, Exo byte-route и `NativeExoFactoryProductWitnessTest` (24 assertions).
- Отдельный `exact native renderer observer JVM regressions`, run `46138985796`: **PASS**.
- Owner build/export ARM13, run `46138985741`: **PASS**. Publisher-first side-by-side 75s gate passed; original publisher and clone were concurrently installed; persistent owner signer verified.
- Отдельный clone-alone ARM13, run `46138985739`: **PASS** по техническому gate. Его verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS` — это диагностический clone-alone прогон, не product acceptance; owner handset не затрагивался.
- BETA34 APK exported as an unpublished owner-only draft release. APK size: `71,606,252` bytes. SHA-256: `516bbdb47dd7d5efdb010c0d57da2055f6f5e90972353aa62a77562b31b9e54a`. Release: https://github.com/manufact-test/nomusic/releases/tag/untagged-575ee4cab0a6f3ad6ff9. Direct APK: https://github.com/manufact-test/nomusic/releases/download/untagged-575ee4cab0a6f3ad6ff9/CELIKOM-A1-RAMIL-AU-BETA34-HONOR50-20261128.apk. Draft only; do not publish. CI provenance explicitly says acoustic replacement is not proven.

## Последняя проверка владельцем — BETA34: НЕ РАБОТАЕТ

Диагностика: CELIKOM-A1-Diagnostics-1795866321890.txt. Маркер BETA34 NAV54 подтверждён.
- FIRST_OPEN_CANDIDATE_ACCEPTED=ONE, FIRST_OPEN_SETTER_MATCH=ONE, FIRST_OPEN_DEFERRED_ARM_ACCEPTED=ONE.
- DATASOURCE_ARMED=ONE, AUDIO_OPEN=ONE, AUDIO_READ=MANY; TRACK_SOURCE_OPEN_LINK=ONE, TRACK_SOURCE_READ_LINK=MANY, TRACK_SOURCE_CLOSE_LINK=ONE; EXO_IO_FAILURE=NONE.
- FIRST_OPEN_BIRTH_NOT_FOUND=MANY и FIRST_OPEN_SOURCE_ALREADY_TOUCHED=MANY сохраняются в общей статистике. Не считать, что все источники связаны.
- SIGNED_MPEG_READY=ONE, OWNER_RESOLVE_MPEG=ONE, CODEC_CONFIG_MPEG=NONE, CODEC_CONFIG_AAC=FEW, CODEC_AUDIO_START=FEW, PLATFORM_AUDIOTRACK_PLAY=FEW.
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS=NONE, ENGINE_HOLDER_READ_RETURN_MINUS3=MANY, MINUS4/MINUS5=NONE, ENGINE_HOLDER_TYPE1_STATE2=NONE. CELIKOM_REPLACEMENT=NOT_CONNECTED.
- Счётчики агрегированы по процессу, поэтому AAC нельзя доказательно приписать именно альтернативному источнику; причина отсутствия слышимого результата пока не установлена.

NAV54 сохранять: впервые в этой проверке подтверждено чтение альтернативных байтов. Не считать его доказательством звучания.

## Следующее действие

Исследовать участок между подтверждённым чтением и выдачей аудиосэмплов: различить несовместимый формат/контейнер и чтение неактивного источника. Проверять на собственных тестовых аудиоданных с воспроизводимым тестом декодирования; не возвращать request-only MP3 override. Не выпускать BETA35 без установленной причины и проверенной функциональной правки. Технические проверки BETA34 уже завершены, повторно собирать её не требуется.

## Не повторять

- Не включать request-only MP3 override: BETA25/BETA32 уже проверяли этот путь; BETA32 ломала запуск «Ау». В BETA33 override отключён.
- Не начинать заново owner-session, авторизацию, resolve, signed grant или загрузку аудио: в свежей диагностике эти этапы проходят.
- Не повторять NAV51/NAV52/NAV53 вслепую и не делать APK только ради новых счётчиков.
- Не считать `DATASOURCE_ARMED`, `AUDIO_READ` или CI SUCCESS доказательством слышимой подмены.
- Не трогать второй плеер, сервер, каталог, Windows, stable Android, OTA и `main`.

**Текущий статус:** BETA34 проверена владельцем: слышимой подмены нет. NAV54 обеспечила first-open admission и чтение альтернативных байтов хотя бы для одного DataSource. Причина отсутствия звука не установлена. BETA35 не создана.
