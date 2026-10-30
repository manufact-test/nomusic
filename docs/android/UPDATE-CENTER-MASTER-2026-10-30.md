# CELIKOM Update Center — ТЗ, архитектура и требования · 30.10.2026

> **СТАТУС: подготовлено к реализации в следующем чате.** Раздача APK на сайте, manifest, уведомления и встроенный обновлятор пока **не созданы и не развернуты**. Текущая подписанная 0.3.55/Gate G **не содержит** обновлятора. От этого документа нельзя считать, что скачивание по будущей ссылке уже работает.

## 1. Решение владельца (30.10.2026)

Сделать собственный механизм распространения Android CELIKOM без Google Play. **Главный и единственный пользовательский адрес:** одна постоянная HTTPS-ссылка на существующем сайте CELIKOM, переход по которой **сразу скачивает актуальный подписанный Android APK**. Когда выпускают новые версии, адрес остаётся тем же. Поставить его на кнопку «Скачать для Android» и использовать в сообщениях.

Система должна проверять доступность новых версий, показывать **обычное системное уведомление Android** («колокольчик»/шторка) и ненавязчивую плашку в приложении с номером версии и краткими изменениями. По нажатию «Скачать и установить» CELIKOM загружает APK, проверяет его и открывает штатный установщик; пользователь подтверждает установку поверх существующей версии. Текущие данные и авторизация сохраняются.

**ВАЖНО: не создавать публично видимых пользователю дополнительных ссылок на отдельные версии, “страницу выбора”, GitHub Releases и т. п.** Manifest и versioned APK URL — внутренние технические пути за одной кнопкой, а не ещё один пользовательский адрес.

Владелец отдельно уточнил: **не превращать статус приватности/закрытого сайта/CMS в отдельную задачу или блокер**. Сейчас сайтом управляют свои, вопросы видимости сайта они решат сами. В этой задаче главное — одна рабочая прямая ссылка и обновления. Не трогать дизайн сайта, админку, FAQ, CMS и сайт в целом кроме минимального подключения Android-download endpoint/кнопки, если нужно.

## 2. Релевантные адреса / источник фактов

- GitHub: https://github.com/manufact-test/nomusic
- Рабочая ветка Android: `feature/android-unified-preparation-seek-gate`.
- Код существующего сайта: `website/**` (PHP/Hostinger). Существующий технический домен из `website/README.md`: https://lemonchiffon-narwhal-791953.hostingersite.com/ . **Это факт о существующем сайте, не обещание, что будущий APK download endpoint там уже создан или доступен.**
- Текущая тестовая подписанная APK: `0.3.55`, `versionCode 56`, `pro.celikom.nativeprobe`. Нет updater и нет ручного подтверждения корректного звука.
- Signing certificate SHA256 (публичный отпечаток, **не ключ**) `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Прежняя установленная на HONOR APK — `0.3.54 AUDIOFIX`, versionCode 55.
- Сайт `website/README.md` и `docs/website/NEXT-CHAT.md` содержат историю staging; читать при работе с Hostinger, но **не расширять scope на публичный редизайн/снятие защиты/переписывание CMS**.

## 3. Один постоянный URL — контракт

Целевой путь **на текущем проверенном Hostinger-host** (это ШАБЛОН, окончательный URL обязан дать следующий чат **только после реального деплоя и HTTP проверки**):

`https://<действующий-хост-CELIKOM>/download/android`

- `GET /download/android` должен выдавать **тот же APK**, что актуально выбранный канал stable, с `Content-Disposition: attachment; filename="CELIKOM-Android.apk"`, MIME `application/vnd.android.package-archive`, корректными `Content-Length`, `Cache-Control: no-store` для resolver, `X-Content-Type-Options: nosniff`, HTTPS и без интерактивного HTML или ручного выбора файла. Допустим контролируемый redirect на immutable HTTPS APK с download headers, но проверять поведение в мобильном браузере.
- Одна ссылка остаётся неизменной при релизе 0.3.56, 0.3.57 и далее; сервер меняет **один атомарный указатель** на текущий опубликованный файл. Предыдущую подписанную версию сохранять для rollback. Не подменять файл под тем же SHA-именем.
- **Внутренние**, пользователю не показываемые endpoint’ы: `GET /updates/android/stable.json` для версии/changelog/checksum; физический immutable `/releases/android/<versionCode>-<sha256>.apk`. Точный layout выбрать по реальному Hostinger PHP/публичному каталогу. Тестовый канал может иметь другой manifest и административную конфигурацию, но **не вторую публичную “главную ссылку”**.
- Публикация новой версии — атомарная: сначала загрузить файл во временное имя, проверить SHA256, размер, package, versionCode, подпись, доступность GET/HEAD и целостность, затем переместить в immutable path, записать manifest и переключить stable pointer. Ошибка не должна ломать прежнюю ссылку. Никаких автоматических релизов при каждом push в GitHub.
- Простая серверная реализация **на имеющемся сайте / Hostinger**, без переписывания большой CMS, БД или сайта. Новую отдельную админку не делать без необходимости. При необходимости легковесный PHP endpoint и файловое хранилище. Изменения должны быть чётко ограничены download/update routes.
- **Не утверждать, что HTTPS-ссылка доступна**, пока не проведён реальный сетевой HTTP GET/HEAD и скачанный файл не проверен побайтно и установкой. Домен/путь, который реально опубликует следующий чат, предоставить владельцу одним адресом.

## 4. Manifest v1 (внутренний)

Шаблон: [UPDATE-CENTER-MANIFEST-V1.example.json](UPDATE-CENTER-MANIFEST-V1.example.json). Пример **не готов к публикации**, URL намеренно не задан.

Поля:
- `schemaVersion` = 1; `channel` (stable или тестовый), `packageName` = `pro.celikom.nativeprobe`.
- `versionName` и **числовой** `versionCode`; только `versionCode > PackageInfo.getLongVersionCode(installed)` является новым обновлением. Та же или меньшая версия не предлагается.
- `apkUrl` — фактический HTTPS immutable URL, `apkSha256` (64 hex), `sizeBytes` (фактический размер), `signerSha256` (публичный fingerprint), `minSdk` (реально проверенный), `publishedAt` (ISO8601 UTC).
- `notesRu` (обычный текст/не HTML, разумный лимит), `enabled` и необязательные UX-поля `mandatory`, `minSupportedVersionCode`.
- Никаких паролей, API key, аккаунтных токенов, signing private key, персональной диагностики, URL приватного хранилища. Получить manifest можно **без входа** в CELIKOM, иначе проверка обновлений сломается у разлогиненного пользователя.
- Manifest **сам по себе не подтверждает подлинность APK**. Клиент хранит *локально* закреплённый certificate digest, отдельно проверяет downloaded bytes SHA256, размеры, имя пакета, Android signature и versionCode. Сеть только HTTPS на allowlisted host, безопасная обработка redirect, таймаут, ограничение максимального размера.
- Ошибочный, отсутствующий, устаревший manifest — безопасный результат “обновление проверить не удалось”, **не останавливать аудио**, не показывать фальшивую обновлённую версию.

## 5. Android updater: пользовательский сценарий и реализация

`RecorderActivity` добавляет самостоятельный небольшой блок «Обновления»/плашку: установленная версия, «Проверить сейчас», при новой версии — «Вышла CELIKOM 0.3.57», короткий changelog, кнопки «Скачать и установить» / «Позже». Не менять существующую аудио-панель и авторизацию.

- Отдельные классы для `UpdateManifest`, `UpdateRepository`, `UpdatePolicy`, `UpdateDownloader`, `UpdateInstaller`, `UpdateNotifications` / `UpdateCoordinator`; названия ориентировочные. Чистая логика отдельно тестируется на JVM. **Updater никогда не вызывает MediaPlayer, ReplacementEngine, AudioOwnership, Yandex/Media3 и audio fades**, не трогает DJ/seek, не блокирует UI.
- Автоматически проверить на старте Activity с разумным интервалом (например 6 часов), плюс периодическое фоновое задание с поддерживаемым Android `JobScheduler`/`WorkManager`, с сетевыми условиями, ограничением количества запросов и учетом OEM/Doze. Не гарантировать уведомление ровно в минуту публикации; это не обязательно push с сервера.
- Android 13+ требует разрешение `POST_NOTIFICATIONS` для обычных уведомлений. Оно уже есть в Android manifest и в UI `RecorderActivity` присутствует пункт «Включить уведомления CELIKOM». Не запрашивать многократно, учитывать отказ. При запрете уведомлений плашка внутри приложения продолжает работать. Для обновлений отдельный notification channel, **не подменять playback notification ProbeService**.
- **FCM push не обязателен для первого релиза:** сначала надежно работающая фоновая/при запуске проверка, без дополнительных Google-зависимостей. FCM/мгновенные пуши — отдельный будущий этап только если потребуется; могут зависеть от Play Services.
- При нажатии «Скачать» — защищенная загрузка в app-private cache на background thread с прогрессом/отменой/повтором, проверкой free space, timeout, сети, SHA256/size, поддержкой сетевого сбоя. Скачанное временное содержимое **не становится installable**, пока не проверены все параметры.
- Перед установкой проверять APK packageName, versionCode, подпись с доверенным локальным SHA256 сертификата. Затем открывать штатный Android `PackageInstaller` или системный установщик посредством scoped `FileProvider` и корректного URI grant. Обработать `REQUEST_INSTALL_PACKAGES`/`canRequestPackageInstalls()` и экран разрешения «Установка неизвестных приложений». Проверить фактическую совместимость с Android 13/HONOR и targetSdk 36.
- **Нормальный sideloaded Android может потребовать системного подтверждения установки**; кнопка запускает процесс, но нельзя обещать тихую бесшумную замену без участия пользователя. Установка поверх прежней APK возможна только при том же package/certificate, с большим versionCode и разрешением ОС. **Не удалять предыдущую APK и не предлагать uninstall для исправления несовместимого ключа.**
- После возвращения в обновлённое приложение реально сравнивать installed versionCode; запуск установщика ≠ успешная установка. При отмене остаётся прежняя версия, не отправлять ложное «успешно обновлено».
- Нотификации выводятся не больше одного раза на новую версию за период (snooze), обновление можно отложить. Без overlays/Accessibility/root/ADB/посторонних уведомлений и без пересылки пользовательских данных.
- Изолировать сетевые сбои обновлятора от аудио. Во время активного воспроизведения скачивание **по явному нажатию** допустимо, но оно не должно вызывать новую буферизацию/блокировать UI; проверить на реальном телефоне.

## 6. Интеграция с существующей сборкой: важный подводный камень

Ветка Android содержит ``android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/RecorderActivity.java``, `ProbeService.java`, `NotificationState.java`, `AppVersion.java` и `release-spec.json`.

**Система сборки не является стандартной Gradle APK.** `android/native-companion/build_release.py` каждый раз декодирует pinned original `CELIKOM-0.3.22-install.apk` (проверяется SHA256), изменяет manifest ресурсы и main launcher, компилирует Java с Android API36/JDK17, прогоняет D8, собирает Apktool 2.11.1, подписывает оригинальным private keystore из закрытого рабочего окружения. `verify_release.py` **намеренно запрещает любые непредусмотренные изменения manifest**. Установка update APK потребует нового receiver/permission/provider path и/или scoped file path; менять **оба** build и verifier, добавить новые *negative* tests, а не «отключать строгую проверку». Изменение `decoded/AndroidManifest.xml` само по себе недостаточно: build заново декодирует baseline.

Сейчас manifest содержит `INTERNET`, `POST_NOTIFICATIONS` и existing `androidx.core.content.FileProvider` с authority `pro.celikom.nativeprobe.package-export`. Исследовать `res/xml/package_export_paths.xml` для безопасной передачи install APK, избегать доступа ко всему cache. `REQUEST_INSTALL_PACKAGES` пока **не зафиксирован** в manifest; добавлять только при нужной установочной стратегии.

Обязательно сохранить release invariants: `android/native-companion/release-spec.json` + `AppVersion.java`, cert fingerprint, package identity, higher versionCode, вся `tests/run_engine.py`, `tests/check_release_contract.py`, `tests/check_audio_architecture.py`, `verify_release.py`, native CI `.github/workflows/android-0348-validation.yml`. Никаких build artifacts/keystores/passwords в GitHub. Закрытую личную библиотеку signing source использовать только локально на этапе официально разрешенного подписания.

## 7. Версии и доказательство, что механизм действительно работает

**Нельзя проверять обновление фальшивым JSON**, указывая 0.3.57, а на деле раздавая APK 0.3.55. Требуются две действительно подписанные версии, у второй versionCode больше.

Текущая подписанная **0.3.55 / code 56** сделана до updater. Рекомендуемый следующий выпуск:
1. `0.3.56 / code 57` — **первая APK с полноценным Update Center** и всем ранее реализованным аудиокодом Gate G. Опубликовать по **одной новой рабочей прямой ссылке** только после реального сервера и тестов. Владелец установит поверх `0.3.54/55`.
2. `0.3.57 / code 58` — **вторая реально собранная и подписанная APK** с минимальным безопасным изменением, чтобы проверить живой путь: manifest → уведомление в шторке/плашка → скачать → проверка подписи → Android install confirmation → новый versionCode 58.
3. Сначала **приёмка владельцем**. Не сдвигать stable для обычных пользователей автоматически. Если канал пока нужен только ему, вариант отдельного тестового манифеста допускается, но не превращать в несколько публичных ссылок. **Одна ссылка на сайте должна вести на актуальную принятую stable APK.**

Когда первый релиз готов, следующий чат вручает **одну действительную HTTPS-ссылку** и объясняет первый install. До деплоя **никакую якобы готовую ссылку не выдавать**.

## 8. Официальные документы и точность обещаний

- Android PackageInstaller / `STATUS_PENDING_USER_ACTION`: https://developer.android.com/reference/android/content/pm/PackageInstaller
- Android 13+ notifications: https://developer.android.com/develop/ui/compose/notifications/notification-permission
- Android PackageInstaller.SessionParams and user-action rules: https://developer.android.com/reference/android/content/pm/PackageInstaller.SessionParams
- Doze/App Standby: https://developer.android.com/training/monitoring-device-state/doze-standby

**Правильная формулировка:** «Приложение само проверяет наличие обновления, показывает уведомление (если разрешено), по кнопке скачивает APK и предлагает штатную установку». Неправильно: «Все Android моментально получают push» или «Обновление устанавливается полностью бесшумно».
