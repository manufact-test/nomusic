> **CURRENT STATUS — 31.10.2026:** the Update Center is implemented and CELIKOM Android **0.3.72 / versionCode 73 is published** to the stable channel. The previous plan to build the first updater-bearing 0.3.56/57 is historical and superseded. See [ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md](ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md) for APK SHA, DEX SHA, original signer, live manifest verification and the exact HONOR OTA acceptance steps. The owner must now test update discovery and successful-install removal from Recents on device; do not claim physical acceptance until then.

---

# Передача CELIKOM Android / Update Center — следующий чат · 30.10.2026

> **ТЕКУЩИЙ ПРИОРИТЕТ — РАЗРАБОТКА**, не очередной обзор. Полное ТЗ: [UPDATE-CENTER-MASTER-2026-10-30.md](UPDATE-CENTER-MASTER-2026-10-30.md). Детальный тестовый план: [UPDATE-CENTER-RELEASE-QA-2026-10-30.md](UPDATE-CENTER-RELEASE-QA-2026-10-30.md). Первая реплика: [START-NEXT-CHAT-UPDATE-CENTER-2026-10-30.md](START-NEXT-CHAT-UPDATE-CENTER-2026-10-30.md). Предыдущее обновление Gate G: [UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md](UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md).

## Задача и обещанный результат

Владелец хочет **одну и только одну стабильную пользовательскую ссылку** на имеющемся сайте CELIKOM: клик — сразу скачать последнюю подписанную APK (без выбора версий). Эта же ссылка остаётся той же во всех релизах и будет стоять на кнопке сайта.

После первой установки Android CELIKOM должен самостоятельно проверять новые версии, показывать верхнюю плашку внутри приложения и системное уведомление в шторке (если дано permission), а по кнопке — скачивать проверенный APK и запускать системную установку поверх существующего приложения. Раздельные, внутренние update-manifest/immutable APK пути нужны технически и не являются «ещё одной ссылкой для человека».

**Уточнение владельца:** не уходить в отдельную задачу «сделать сайт закрытым/открытым», публичный релиз CMS и ревизию защиты сайта. Сейчас он использует свой сайт сам и намерен разбираться с приватностью отдельно. Не превращать это в препятствие перед созданием единого URL. Не переписывать принятый сайт, CMS, дизайн, FAQ и admin. Строго нужные download endpoint/путь и при необходимости CTA — да.

**Готовый результат следующего чата** — реально работающий HTTPS download URL, подписанная **первая APK с updater**, затем настоящая **вторая APK для теста OTA-подобного сценария**, с проверкой подписи и последовательным обновлением на HONOR. До фактического деплоя и физической проверки не называть ничего готовым.

## Репозиторий, ветки, документация

- GitHub: https://github.com/manufact-test/nomusic
- Android рабочая ветка `feature/android-unified-preparation-seek-gate`.
- Проверенная Android точка **исходного кода** `d0317e3d697db202164804a27f18f3e688fe1d05`, полный CI SUCCESS https://github.com/manufact-test/nomusic/actions/runs/41043617578 . После неё только docs [skip ci], поэтому check current HEAD.
- Откаты: `backup/android-0355-gateg-signed-ci-green-20261030` (последний подписанный код), `backup/android-0355-before-update-center-handoff-20261030` (перед началом документирования нового направления), более ранние D/E/F/0.3.54 backups.
- Читай: `docs/android/UPDATE-CENTER-MASTER-2026-10-30.md`, `UPDATE-CENTER-RELEASE-QA-2026-10-30.md`, `docs/android/UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md`, `android/native-companion/README.md`, `website/README.md`, `android/native-companion/build_release.py`, `verify_release.py`, `decoded/AndroidManifest.xml`.
- Source Android: `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/`. UI `RecorderActivity.java`; Yandex foreground service `ProbeService.java`; old music notification `NotificationState.java`; last audio source `ReplacementEngine.java`, `AudioOwnership.java`. Не помещай update work внутрь audio engine.
- Website: `website/public/**`, PHP runtime `website/app/**`. Действующий Hostinger/staging-адрес из документации: https://lemonchiffon-narwhal-791953.hostingersite.com/ — факт об уже существующем сайте; **не подтверждённый URL прямой загрузки**. Конкретный download URL выбирай после проверки инфраструктуры и настоящего GET/HEAD. У владельца должно быть **ровно одно готовое название ссылки**.

## Что сделано в Android и что остаётся на реальный тест

**Последняя отдельная подписанная APK создана:** CELIKOM `0.3.55` / versionCode `56`, package `pro.celikom.nativeprobe`. **Updater там нет**. APK SHA256: `ff1c9d0757173796b1068acf52ebdecd8354cfb429dd35c2b7253f3e5596c54a`. Native DEX SHA256 `64ee7d70e48dba382effea638c17766052e58bd67ed56e663ff05d18d08b575c`. Публичный signer certificate SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Original private signer recovered but only in private user's Library; never expose in docs/GitHub/CI/site.

**Private Library:**
- `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.55-GATEG-SIGNED-20261030.apk` (подписанная, выпущена и проверена вне CI; не установлена/не проверена владельцем).
- `/CELIKOM/Android/Backups/CELIKOM-Android-0354-AUDIOFIX-DIRECT-20261030-B29AF425.apk` (предыдущая установленная подписанная версия, code 55, сохрани её).
- `/CELIKOM/Android/Private/CELIKOM-Original-Android-Signing-RECOVERED-20261029.zip` (PRIVATE, не копировать в репозиторий/сайт/лог/ответ; использовать только в защищённом локальном build).

**Gate A–G** завершили частичную конвергенцию Android exclusive audio owner: owner tickets/source/account epochs; read-only Media3 lookahead; native seek single-flight; отличить пользовательскую паузу от Media3 BUFFERING; stale callback/account protection; удалить дублирующие `warmSeekTransition` и `handoverPending`, manual return through owner ticket. **Полный pure reducer не завершён**, обещания абсолютно бесшовного звука нет. Нет следующей песни prefetch. Host tests/DEX не измеряют акустическое звучание. На HONOR NTH-NX9 Android13 Yandex Music 2026.09.5 #167.1gpr в прошлом run 0.3.54 ещё были паузы/переходы ~1.31с по telemetry. Новую APK владелец ждёт, чтобы **одновременно проверить updater и audio**. Не перекрывай audio code новой рефакторизацией обновлятора.

## Подводные камни реальной сборки

В отличие от обычного Gradle-приложения, `android/native-companion/build_release.py` распаковывает pin-original 0.3.22 APK с SHA, патчит manifest/launcher, собирает новый Java DEX с JDK17+SDK36+D8 и возвращает его в APK. Защитный `verify_release.py` проверяет целостность архива, signer, package, versionCode и **точное соответствие baseline Manifest**, допускает лишь известные патчи. Для installer permissions/receiver/FileProvider paths updater нужно **точечно** расширить build+verify и negative tests, НЕ снимать проверки. `decoded/AndroidManifest.xml` сам не является authoritative final build input.

В исходном Manifest уже есть `INTERNET`/`POST_NOTIFICATIONS` и `androidx.core.content.FileProvider`; `REQUEST_INSTALL_PACKAGES` сейчас нет. Проверить нужность permission, необходимость и scope FileProvider xml. Для Android13+ настройка «Установка неизвестных приложений» от этого источника и системное подтверждение установки могут потребоваться. Согласие системы нельзя обойти и нельзя выдавать скачивание за выполненную установку.

Все apk релизы: один package ID, тот же оригинальный signing cert, строго возрастающий versionCode. `release-spec.json` и `AppVersion.java` должны совпадать; release contract tests и CI обновить. Секреты подписи локально, ни в GitHub/CI, ни в manifest. Сохранять старые signed APK и branch перед каждым кодовым этапом.

## Рекомендуемый порядок самостоятельной работы без микротапов

1. В GitHub сверить latest HEAD и docs; создать резервную ветку *до* правок, держать Android/audio baseline неизменным. Проверить текущие Hostinger/deploy возможности, не придумывать адрес.
2. Реализовать **на существующем сайте** минимальную atomic server-side раздачу: главный `/download/android`, внутренний manifest endpoint и immutable APK, publisher/rollback, HTTP GET/HEAD/MIME/Content-Disposition/HTTPS. Отдельные важные test fixtures для old/new file. Не модифицировать ненужный CMS функционал.
3. Реализовать Android Update Center полностью, а не экран-заглушку: строгий policy/parser + скачивание SHA/size/cert + native installer + in-app banner + системное уведомление + разумные проверки на запуск/фоне. Независимость от audio service; Android notification permission отказ не должен блокировать in-app banner.
4. Обновить build/verify manifest checks, test suite; подтвердить локальный test Android 13 и API36/JDK17/DEX. Провести нормальный CI. Подписать **0.3.56/versionCode57** оригинальным сертификатом (первая updater-bearing версия), сравнить signer SHA, version, compiled DEX, archive, hashes, сохранить backup.
5. Опубликовать на сайте актуальную APK по **единой прямой ссылке**, проверить реально скачанное APK (HTTPS, HTTP headers, SHA, размер, подпись). **Дать владельцу одну готовую рабочую ссылку**.
6. Для полной проверки сделать **реальную подписанную 0.3.57/versionCode58**, только минимальное безопасное изменение, опубликовать manifest, чтобы 0.3.56 получила новое обновление. Уведомление от фонового задания Android может появиться не сразу; наличие обновления проверяем сначала ручной кнопкой, потом системной шторкой.
7. Владелец устанавливает/сравнивает и даёт диагностику. Тесты: download→OS install→installed 58 + pause/seek/next song/no overlap/route loss. Отдельно тестирование permission decline, offline, invalid SHA, downgrade, no storage. Только после его приёмки расширять deployment.

**Примечание по двухэтапному тесту:** Если 0.3.56 с updater ещё не существует, нельзя обещать, что 0.3.55 сейчас получит пуш: его в ней нет. Не считать обновление «заработало» после одного download; вторую установленную версию 58 надо увидеть реально.

## Границы и стиль сотрудничества

- Владелец просил **не останавливать работу ради мелких отчётов**, брать существенные блоки, самостоятельно проверять и чинить тесты. Отчитаться по факту законченного результата/действительно необходимой ручной проверки. Не выдавать неполный архив или гипотетическую ссылку как готовую APK.
- Desktop `feature/api-range`, `extension/**`, `ad-protection/**`, сервер треков `server/**`, каталог, оплату, музыкальную API авторизацию не трогать. Сайт менять **только ровно настолько, насколько нужно для одной download-ссылки**.
- Если live Hostinger не доступен в подключённых инструментах, не симулировать деплой: сделать весь код, тесты и готовый развертываемый пакет, затем сообщить владельцу ровно, какого доступа/действия не хватает. Не просить его повторять известные GitHub, сайт, модель телефона и цели.
