# CELIKOM Android A1 — единственный актуальный handoff

Дата состояния: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Последний source HEAD: `a513e1045bc5fdd76beb06e697399c9b48c6e351`  
HEAD ветки до этого обновления документации: `a513e1045bc5fdd76beb06e697399c9b48c6e351`

## Цель и границы

Добиться слышимой подмены аудио внутри **оригинального приложения Яндекс Музыки**. CI, запуск приложения, получение подписанных байтов и диагностические счётчики не являются доказательством успеха.

Работать только в указанной Android experiment-ветке. Не добавлять второй плеер. Не менять сервер, каталог, авторизацию, Windows, stable Android, OTA или `main` без отдельной доказанной необходимости и разрешения владельца.

## Последняя проверка — BETA33: НЕ РАБОТАЕТ

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

**Вывод:** grant/resolve и решение `ALTERNATE` доходят до pre-prepare, но точный DataSource не проходит first-open admission. До `DATASOURCE_ARMED` выполнение не доходит. Это текущая точка работы. Аудиоподмена не подтверждена.

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
- Owner build/export ARM13, run `46138985741`: **IN_PROGRESS** на момент обновления.
- Отдельный clone-alone ARM13, run `46138985739`: **IN_PROGRESS** на момент обновления.
- BETA34 APK ещё не доставлен. Не считать сборку готовой, пока оба ARM13 job не завершились успешно.

## Следующее действие

1. Дождаться owner build/export и отдельного clone-alone ARM13. При ошибке исправлять конкретную причину, не возвращаться к NAV51/NAV52/NAV53 и не начинать диагностику заново.
2. После успешных проверок получить один подписанный owner APK `CELIKOM-A1-RAMIL-AU-BETA34-HONOR50-20261128.apk`.
3. Владелец устанавливает BETA34 поверх BETA33 без очистки данных. Проверяет «Ау» и вторую проблемную песню в оригинальном Яндекс Музыке.
4. По новой диагностике проверить `FIRST_OPEN_CANDIDATE_ACCEPTED`, `FIRST_OPEN_BIRTH_NOT_FOUND`, `FIRST_OPEN_SOURCE_ALREADY_TOUCHED`, `DATASOURCE_ARMED`, `AUDIO_OPEN`, `AUDIO_READ` и renderer-period read. Не объявлять слышимую подмену без фактического прослушивания.

## Не повторять

- Не включать request-only MP3 override: BETA25/BETA32 уже проверяли этот путь; BETA32 ломала запуск «Ау». В BETA33 override отключён.
- Не начинать заново owner-session, авторизацию, resolve, signed grant или загрузку аудио: в свежей диагностике эти этапы проходят.
- Не повторять NAV51/NAV52/NAV53 вслепую и не делать APK только ради новых счётчиков.
- Не считать `DATASOURCE_ARMED`, `AUDIO_READ` или CI SUCCESS доказательством слышимой подмены.
- Не трогать второй плеер, сервер, каталог, Windows, stable Android, OTA и `main`.

**Текущий статус:** BETA34 NAV54 functional fix committed; JVM PASS; owner build/export и clone-alone ARM13 ещё выполняются. APK пока не доставлен. После успешных ARM13 проверок — одна установка BETA34 и проверка звука владельцем.
