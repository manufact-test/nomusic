# CELIKOM Test — читаемость полей входа, проверенная отдельная APK (2026-11-02)

## Результат и границы

- **Только CELIKOM Test**: `pro.celikom.nativeprobe.test`, `0.3.85-test.1`, versionCode **86086**, label `CELIKOM Test`.
- Source commit исправления: `09b08fbaa9fb0e30e72bb0d1020c9ce857308772` на `feature/android-0385-intro-join-investigation-20261102`. Следующие документальные коммиты не изменяют исходники этого APK.
- [GitHub Actions validation + automatic signed test build #41470985426](https://github.com/manufact-test/nomusic/actions/runs/41470985426): `native-android` SUCCESS, `build-celikom-test / build-test-app` SUCCESS. Artifact `CELIKOM-Test-0.3.85-test.1-code-86086`, ID `13153724134` (архив GitHub Actions сохраняется по собственной политике retention 7 дней).
- Подписанная APK (8,747,161 байт) SHA-256: `c030111f0caac0b79fcd079690f26a353ce693ec43bbc6fe38ef6bc3a72395a7`. Подпись APK Signature Scheme v3 verified, сертификат SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` — **совпадает с оригиналом**.
- В ChatGPT Library: `/CELIKOM/Android/Test/CELIKOM-Test-0.3.85-test.1.apk`, `CELIKOM-Test-0.3.85-test.1-receipt.json`, `CELIKOM-Test-0.3.85-test.1-verification.json`. Все три — новые файлы, старые файлы не перезаписаны.
- Следующая проверка владельца на HONOR: только открыть форму входа и убедиться, что email, маска пароля, подсказки, курсор и выделение читаются на реальном экране. UI-приёмка на устройстве **пока не подтверждена**. Логика входа и сетевые запросы прежние.

## Разбор двух новых диагностик

Получены `CELIKOM-combined-20261102-172508.txt` и `SVID_20261102_172353_1.mp4`. Журнал структурированного аудио и 62-секундное видео показывают работу/переходы песен в Яндекс Музыке; **они не содержат записи формы логина или измерения цветов Android EditText**. Поэтому причину белого текста установили по исходникам и теме, не приписывая видео несуществующую демонстрацию входа.

По аудио: в текущем test-run фиксируются шесть переходов источника с `exclusive_after_existing_clock_gate`, шесть загрузок полных локальных файлов (около 1.18–3.99 с), 19 ALIGNMENT и один WARM seek ACK (около 15–91 мс), без `rangeWaitObserved` и `staleOperation` в рассмотренном фрагменте. В журнале нет speaker PCM и завершённого `run_end`. Владелец сообщает, что по звучанию «всё осталось как было». **Холодные начала песен акустически не приняты**. Это самостоятельная будущая задача, никакие параметры handover сейчас не менялись.

## Доказанная причина UI-дефекта

Форма входа — **нативные Android `EditText`**, а не WebView. Она создаётся методом `login()` в `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/RecorderActivity.java` внутри `AlertDialog`; шестизначный код подтверждения создаётся в `verify()` аналогичным образом.

У `RecorderActivity` в `android/native-companion/decoded/AndroidManifest.xml` явно задана **светлая** тема `@android:style/Theme.Material.Light.NoActionBar`. Общий helper `input()`, рассчитанный на тёмную основную панель, вручную задаёт всем полям `v.setTextColor(FG)`, где `FG=0xfff4f7f8` (почти белый), и `v.setHintTextColor(MUTED)`, где `MUTED=0xffaab8be`. Поле внутри светлого системного диалога имеет белый фон. Следствие — белый введённый текст и плохо различимые подсказки. `InputType.TYPE_TEXT_VARIATION_PASSWORD` сам по себе не является причиной.

## Минимальное изменение только при сборке отдельного Test

`android/native-companion/build_test_release.py` копирует исходники во временное test-only дерево и вставляет в копию `RecorderActivity` метод `styleLoginInput(EditText field)`. Он вызывается **только** для email, пароля и кода подтверждения в светлых диалогах:

- Ввод и маска пароля: `#1F2933` (контраст примерно 14.8:1 с белым).
- Hint/placeholder: `#52606D` (примерно 6.5:1).
- Цвет выделения: `#BFDCFF`.
- Курсор и три маркера выделения: `#1558B0` (примерно 6.9:1); Android API 29+ через `getTextCursorDrawable` и `getTextSelectHandle*`. Для более старых API остаётся системная обработка.
- Состояния focus/password transformation продолжают управляться Android: `InputType`, существующий `IMPORTANT_FOR_AUTOFILL_NO`, обработчики `api().login`/`api().verify` и networking не менялись.

**Оригинальный `addon/src/.../RecorderActivity.java` не изменён.** На стабильной сборке и на прочих тёмных полях Test ничего не перекрашено. `test-app-spec.json` отдельно увеличен до `0.3.85-test.1`/86086. Не менялись звук, seek, Pause, Resume, Next, cold-join эксперимент, OTA, backend, сайт, stable release contract.

## Автоматические защиты и результаты CI

`android/native-companion/tests/check_test_app_build_contract.py` создаёт временную копию исходников и применяет настоящий test patch, затем проверяет: явную светлую тему, точные места перекраски, прежнюю маску пароля, отсутствие изменений стабильного Java, сохранность вызовов login/verify, API курсора/выделения и нижние границы контраста (7:1 для текста, 4.5:1 подсказки, 3:1 курсора). Контракт test package, подписи и отключённого OTA сохранён.

В CI [#41470985426](https://github.com/manufact-test/nomusic/actions/runs/41470985426) успешно завершены полный native host regression suite, холодный эксперимент, **неизменённый** `check_0385_seek_baseline.py`, Android API 36, D8, создание/подпись/проверка APK, receipt и загрузка только тестового artifact. `publish-stable` и остальные publisher jobs **SKIPPED**; `stable.json` и Hostinger не публиковались.

## Сохранённые контрольные точки (не менять)

1. **Стабильный оригинал**: `pro.celikom.nativeprobe`, `0.3.85`, code86, source `053b7d59beb53db5f30b942feba35e51a1ab256a`. `backup/android-0385-honor-seek-accepted-20261102` и `backup/android-0385-honor-seek-accepted-recovery-20261102` не перемещать.
2. **Прежняя тестовая контрольная**: `pro.celikom.nativeprobe.test`, `0.3.85-test`, code86085, source `32a4afa7c381758502bf47d7b3facd200e74842a`; `backup/android-0385-test-first-owner-check-20261102`; SHA-256 APK `bf1fc8b39a08b3c1f5f5b2d1483f0fe0fb013bbd7041671867dea77e2b5e4bee`; прежняя Library APK и два JSON оставлены без изменений.
3. **Новая тестовая, исправление ввода**: source `09b08fbaa9fb0e30e72bb0d1020c9ce857308772`, code86086, SHA-256 `c030111f0caac0b79fcd079690f26a353ce693ec43bbc6fe38ef6bc3a72395a7`. Отдельная APK/receipt/verification в Library и Actions artifact.

PR #37 остаётся открытым, **не сливать**. Не запускать stable publisher, не включать «Плавный переход» Яндекс Музыки до отдельной акустической приёмки, не требовать повторного seek/Pause/Resume-тестирования.
