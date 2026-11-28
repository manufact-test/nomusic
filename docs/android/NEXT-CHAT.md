# CELIKOM Android A1 — единственный актуальный handoff

Дата состояния: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Последний функциональный source commit: `6972ee7fbee06be8eec90be51f886deb48ef265b`  
HEAD ветки до этого обновления документации: `4cce953ea88d003e754e38b981555236dda16f1e`

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

## Точный участок следующей работы

В текущем коде:

- `ExitCallsiteWitness.java`, около строк 4771–4800: open-hook вызывает `exactFreshCreatorOrBetaAtFirstOpen(source)`, затем `onExoSourceInstanceOpenAttempt(source)`.
- `StageBAudioEvidence.java`, `exactFreshCreatorOrBetaAtFirstOpen()`: кандидат отклоняется, если `wasSourceTouched(source)` или не найден точный `ExactFactorySourceBirth`.
- `onExoSourceInstanceCreated(source, factory)` записывает exact birth только при найденной связи с нужным factory.
- `markSourceTouched()` навсегда помечает этот Java-объект как уже использованный для fresh-candidate admission после open/read/close.

Диагностика показывает много `SOURCE_ALREADY_TOUCHED` и несколько `BIRTH_NOT_FOUND`, но пока не доказывает, почему именно объект уже touched к моменту admission.

**Рабочая гипотеза, не установленная причина:** первый original open может происходить раньше, чем точная factory/source birth привязка становится доступна. Тогда первый вызов отклоняется как `BIRTH_NOT_FOUND`, помечает объект touched, а следующий вызов уже отклоняется как `SOURCE_ALREADY_TOUCHED`. Также проверить вариант повторного использования ранее открытого DataSource. Не объявлять гипотезу фактом — сначала проследить порядок вызовов.

## Следующее действие

1. Продолжить с этого состояния, не начинать расследование заново и не просить владельца повторно присылать уже разобранную BETA33 диагностику.
2. Проследить точный порядок для одного source object: создание DataSource → регистрация exact factory birth → первый `open()` → `markSourceTouched()` → последующие open. Проверить, кто и когда вызывает ранний touch либо почему birth отсутствует.
3. Сверить путь с `NativeRamilTrackOnlyLineageTest` и добавить один focused regression, воспроизводящий фактический порядок из телефона.
4. Исправлять точку привязки/порядок до первого I/O. **Не ослаблять** проверку touched, exact factory/descriptor/creator/track identity; не разрешать подмену после начала original I/O и не смешивать original и alternate bytes.
5. После функциональной правки выполнить нужный JVM regression, owner build/export и clone-alone ARM13. Только после прохождения проверок собирать одну следующую тестовую версию.

## Не повторять

- Не включать request-only MP3 override: BETA25/BETA32 уже проверяли этот путь; BETA32 ломала запуск «Ау». В BETA33 override отключён.
- Не начинать заново owner-session, авторизацию, resolve, signed grant или загрузку аудио: в свежей диагностике эти этапы проходят.
- Не повторять NAV51/NAV52/NAV53 вслепую и не делать APK только ради новых счётчиков.
- Не считать `DATASOURCE_ARMED`, `AUDIO_READ` или CI SUCCESS доказательством слышимой подмены.
- Не трогать второй плеер, сервер, каталог, Windows, stable Android, OTA и `main`.

**Текущий статус:** BETA33 не работает; функциональный код после неё не менялся; BETA34 не создана. Следующая задача — найти и исправить причину отказа точного DataSource на first-open admission.
