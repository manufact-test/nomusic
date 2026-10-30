> **НОВАЯ АКТУАЛЬНАЯ ПЕРЕДАЧА (30.10.2026, Android 0.3.59/code60):** [HANDOFF-2026-10-30-AFTER-0359-AUTOPUBLISH.md](HANDOFF-2026-10-30-AFTER-0359-AUTOPUBLISH.md) — полная история реальных HONOR лагов/ Gate A–G, GitHub Actions signed Hostinger autopublish, versioned 404 и ремонт, что делать с новой диагностикой. [START-NEXT-CHAT-2026-10-30-AFTER-0359.md](START-NEXT-CHAT-2026-10-30-AFTER-0359.md) — готовое первое сообщение. **Новая 0.3.59 опубликована; качество звука ещё не принято.** Текущий чат по просьбе владельца больше не чинит аудио, только фиксирует новую диагностику до передачи. Исторические указания ниже про старые версии/отсутствие signing key/ручной Hostinger deploy НЕ актуальны. Desktop не трогать.\n\n---\n\n> **НОВЫЙ ГЛАВНЫЙ ПРИОРИТЕТ (30.10.2026): CELIKOM ANDROID UPDATE CENTER, ОДНА ПОСТОЯННАЯ ССЫЛКА НА APK.** Пользователь поручил подготовить и передать разработку следующему чату; **механизм обновлений пока НЕ реализован**, прямой сайт-URL ещё не проверен. Читать первым делом [UPDATE-CENTER-HANDOFF-2026-10-30.md](UPDATE-CENTER-HANDOFF-2026-10-30.md), [UPDATE-CENTER-MASTER-2026-10-30.md](UPDATE-CENTER-MASTER-2026-10-30.md), [UPDATE-CENTER-RELEASE-QA-2026-10-30.md](UPDATE-CENTER-RELEASE-QA-2026-10-30.md), готовое сообщение [START-NEXT-CHAT-UPDATE-CENTER-2026-10-30.md](START-NEXT-CHAT-UPDATE-CENTER-2026-10-30.md). Последняя подписанная 0.3.55/code56 НЕ содержит updater и ещё НЕ проверена на HONOR; следующий план — реально подписанные 0.3.56/code57 (первый updater) и 0.3.57/code58 (проверка обновления). После нового релиза должна быть **ОДНА** действующая прямоскачиваемая HTTPS-ссылка с сайта. Не начинать отдельную задачу приватности/редизайна сайта, не затрагивать компьютерную версию. Документационный checkpoint на Green CI audio code `d0317e3d697db202164804a27f18f3e688fe1d05` / https://github.com/manufact-test/nomusic/actions/runs/41043617578 .

> **LATEST 30.10.2026:** Android 0.3.55/Gate G signed APK ready for manual HONOR test. Code/CI green `d0317e3d697db202164804a27f18f3e688fe1d05`, Android Actions run `41043617578`, Library `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.55-GATEG-SIGNED-20261030.apk`, APK SHA256 `ff1c9d0757173796b1068acf52ebdecd8354cfb429dd35c2b7253f3e5596c54a`. Original signer retained and never committed. Device audio listening still outstanding. See `docs/android/UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md`. No desktop changes.\n\n> **АКТУАЛЬНАЯ ПЕРЕДАЧА (30.10.2026):** [HANDOFF-2026-10-30-UNIFIED-AUDIO.md](HANDOFF-2026-10-30-UNIFIED-AUDIO.md), [UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md](UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md), [START-NEXT-CHAT-2026-10-30-UNIFIED-AUDIO.md](START-NEXT-CHAT-2026-10-30-UNIFIED-AUDIO.md). Новая ветка `feature/android-unified-preparation-seek-gate` (docs-only checkpoint), базовый код `8128307d0daf95f3386b85791db5347e3ec56357`, Android CI 41019895272 SUCCESS; **signed 0.3.54 AUDIOFIX установлен**, signing key восстановлен и хранится приватно. Новый единый audio-owner дизайн ещё НЕ реализован, APK не выпускается. ВСЕ нижеследующие исторические статусы о потерянном ключе и неподписанной 0.3.52 устарели. Только Android; desktop/server/ad-protection не трогать.

> **Актуальный checkpoint (30.10.2026):** [UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md](UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md). Ветка `feature/android-unified-preparation-seek-gate`; Android code `d1034816796d6fc1a421d559304f5c5218317c66`; [GitHub CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41027989995). Новые audio-ticket/epoch и наблюдение Media3 уже реализованы, но полноценный reducer и prefetch ещё НЕ готовы, нового APK нет. Старые данные ниже читать только в контексте этого checkpoint.

---

> **ГЛАВНЫЙ АКТУАЛЬНЫЙ ДОКУМЕНТ НА ПЕРЕДАЧУ В НОВЫЙ ЧАТ:** [HANDOFF-2026-10-29-ANDROID-0352.md](HANDOFF-2026-10-29-ANDROID-0352.md). **Готовое первое сообщение:** [START-NEXT-CHAT-2026-10-29.md](START-NEXT-CHAT-2026-10-29.md). Последний код `25767ce3`, CI https://github.com/manufact-test/nomusic/actions/runs/40942060340 PASS; последний signed 0.3.51 НЕ принят; 0.3.52 только unsigned inspection, оригинальный signing key отсутствует. Desktop 0.4.65/feature/api-range НЕ ТРОГАТЬ. Нижеследующие контрольные точки исторические.

---

# Последний Android checkpoint: архив, DEX-provenance и переносимая проверка 0.3.52 · 29.10.2026

**Последний проверенный код:** `7e49152d6a17cbf3d31e7b247b5e074f1fb215ac`. Полный CI **PASS**: https://github.com/manufact-test/nomusic/actions/runs/40941509415. Рабочая ветка `feature/android-0348-audio-ownership-stabilization`; PR #22 остаётся OPEN/DRAFT, Issue #20 OPEN. Перед работой сверяй HEAD: следующий docs commit изменит хеш.

- **Разовая проверка APK теперь воспроизводима без редактирования исходника:** `build_release.py --unsigned-inspection` работает с настоящим исходным APK 0.3.22, с тем же Apktool/resource assembly/zipalign и готовым CI DEX. Этот режим **не** принимает signing-dir, требует имя `*-INSPECTION-UNSIGNED.apk` и завершает только `verify_unsigned_inspection.py`, который **отказывает подписанным пакетам**. Режим полноценного подписанного релиза по-прежнему обязательно требует оригинальный `--signing-dir`, JDK17 и **не принимает prebuilt DEX**.
- **CI provenance:** `ci_provenance.py` + `ci-dex-provenance.json` (набор GitHub commit, fingerprint всех Android *.java, DEX SHA256, версия и отпечаток сертификата). Проверка обнаруживает чужой/устаревший DEX или изменённые Java-файлы. Это свидетельство из конкретного CI-запуска, НЕ криптографически подписанная attestation.
- **Строгий общий gate для APK:** `release_archive.py` применён к signed `verify_release.py` и unsigned inspector: точные два DEX, byte-identical CI DEX, полный список разрешённых original assets (не только их содержимое), отсутствие добавленных/удалённых файлов каталога, ZIP duplicates/traversal, отсутствуют исходники и ключи. `check_release_archive.py` — 16 тестов в том числе заведомо испорченных пакетов, `check_ci_provenance.py` — 11 negative cases, `check_release_modes.py` проверяет запрет подмены подписи inspection-режимом.
- **Реальный smoke:** Apktool 2.11.1 на приватном SHA-проверенном базовом 0.3.22 собрал структурный unsigned APK. Доказательство `0.3.52`/code 53, исходный каталог не изменён, 3 asset entries, 200 ZIP entries, JDK17 CI DEX SHA256 `8683a9f50fc2d1171206e0a803fe9f730c8e67f709909dcacecd67fa916ade98`, CI source fingerprint `60f0f7383a4ee382c5211f5856632770ec1a0f801eecce049053085b5ae64b97`, smoke SHA256 `dcc2cf36133f70d5bc60071a1802631997095d279541119358f2dff64ab6c1b4`. Подробности в [RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md](RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md).
- **Portable kit реально скачан и повторно протестирован:** `check_release_contract.py`, `check_release_archive.py`, `check_release_modes.py`, `check_ci_provenance.py` — PASS без git checkout. Состав kit фиксирует безопасные `source-gitignore.txt`, `ci-android-validation-workflow.yml` и source-to-DEX provenance. Ключи и подпись в kit не кладутся.
- **БЛОКЕР сохраняется:** оригинальных секретных `celikom-native-probe.p12` и `signing.json` нет в доступном здесь контейнере/Library-бэкапе. Signed APK **0.3.52 не существует**, 0.3.51 на HONOR не принята. Не создавать новый keystore, не выдавать unsigned для установки, не просить тестировать недоделанный кандидат. После доступности оригинального ключа нужен signed `build_release.py` + полноценный `verify_release.py`, затем физическое слушание HONOR/Bluetooth; CI не доказывает акустическую эксклюзивность.
- **Backup:** `backup/android-0352-provenance-and-archive-verified-20261029` → `7e49152d`; все предыдущие резервные ветки остаются неприкосновенны. Desktop, backend, сайт, CMS и каталог НЕ трогать.

---

# АКТУАЛЬНО: Android 0.3.52 — проверены API36/D8, упаковка и структурный APK · 29.10.2026

**Последняя зелёная кодовая точка: `04a583a5d32a29aa96f5a61aebd8bbbe892b92c9`**. Полный GitHub CI **PASS**: https://github.com/manufact-test/nomusic/actions/runs/40937933292. Рабочая ветка `feature/android-0348-audio-ownership-stabilization`, PR #22 **OPEN/DRAFT**; ничего не сливать. Сверить HEAD перед следующей работой: документационный коммит может изменить SHA.

- **Код Android 0.3.52 / versionCode 53 подготовлен.** `release-spec.json` — единый контракт, `release_contract.py` — защита от возврата к проблемной 0.3.51 и подмены сертификата. `build_release.py` и `verify_release.py` синхронизированы; JDK17, SDK API36, SHA Apktool2.11.1, все 5 JAR, исходный APK и подписывающий сертификат закреплены. `check_release_contract.py` запускает отрицательные тесты в CI.
- **Практическая упаковка проверена:** локально Apktool 2.11.1 пересобрал реальный SHA-проверенный оригинал 0.3.22 в структурный **НЕПОДПИСАННЫЙ** пакет 0.3.52. `aapt` видит versionCode 53/0.3.52, `zipalign` PASS, каталог/assets неизменны, классы2.dex побайтово равен результату **JDK17 CI** (не локальной JDK21 компиляции), лишних исходников и ключей нет. `verify_release.py` отказался принимать неподписанный пакет, как и должен.
- **БЛОКЕР:** нет доступного здесь старого приватного файла `celikom-native-probe.p12` + `signing.json`; архив сохранённого build-окружения ПРЯМО заявляет, что не содержит signing. Никакого нового ключа не создавать и не пытаться выдавать структурный файл за installable. **НОВОГО ПОДПИСАННОГО APK 0.3.52 НЕТ.**
- Базовый APK 0.3.22 и отвергнутый установленный 0.3.51 проверены через `apksigner`: одинаковая v3 сертификатная идентичность SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Лишь после получения исходного приватного ключа в безопасном offline runtime разрешена одна подписанная сборка и `verify_release.py`; затем физический тест HONOR и Bluetooth.
- **Новый подробный отчёт:** [RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md](RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md). Предыдущая архитектура, реальные 0.3.51 сбои, тесты, история и старые бэкапы остаются ниже.
- Новый backup `backup/android-before-0352-release-pipeline-20261029` указывает на `351d9cac`; зелёный backup версии `backup/android-0352-release-contract-green-20261029` указывает на `04a583a5`. Не трогать прошлые backup-ветки. Никакой Desktop, Backend, CMS или каталог не изменён.

---

# Дополнительный зелёный Android checkpoint · 29.10.2026, после ревизии гонок

**Последний ПРОВЕРЕННЫЙ код:** `ce52b178c9101835619ceb8ee4a66b8784477f45`. Все шаги `native-android` **PASS**: https://github.com/manufact-test/nomusic/actions/runs/40931276362. До него PASS: https://github.com/manufact-test/nomusic/actions/runs/40930524770 и https://github.com/manufact-test/nomusic/actions/runs/40930935879.

**Что нового после основного рефакторинга:** (1) `AudioOwnership.grantReplacement` не отправляет повторно отрицательное усиление эффекта на каждом 250-мс tick/20-мс ramp при уже активном разрешении; `volume` не повторяет неизменные положительные команды, но ВСЕГДА отправляет аварийное обнуление. Все разрешения положительной громкости по-прежнему проверяются. (2) `SourceEventArbiter` отвергает устаревшие SEEK от *другого media item* даже при совпадении позиций в миллисекундах. (3) При полном освобождении декодера `AudioOwnership.retireDecoder()` инвалидирует epoch даже для восстановления **той же песни**; при длительной паузе с сохранённым плеером epoch не сбрасывается. Новые fake-счётчики, тесты gateway, реальные сценарии `TestAudioLifecycle` и блокирующий архитектурный gate включены в полный CI.

**Сохранённая зелёная точка:** `backup/android-audio-callback-fencing-green-20261029` → `ce52b178`. Не перемещать старые backup-ветки; не сливать PR #22. Вся разница относительно `b9c3e383` строго в `android/native-companion/` и `docs/android/`.

**APK всё ещё НЕТ:** 0.3.51 установленная неудачная версия, следующая 0.3.52 НЕ собрана/подписана. У текущего `build_release.py` и `verify_release.py` зафиксированы старые `0.3.51`/versionCode 52, а `AppVersion.java` требует синхронного повышения до версии с versionCode **>52** перед новой сборкой. Нельзя запускать старую упаковку как новый релиз. Истинное акустическое неналожение Android/BT требует теста на HONOR после полноценной проверки подписанного файла. См. [AUDIO-PRE-RELEASE-REVIEW-2026-10-29.md](AUDIO-PRE-RELEASE-REVIEW-2026-10-29.md).

---

# Актуальный Android-checkpoint после системной переработки · 29 октября 2026

> **Этот раздел новее исходной передачи 0.3.51 и исторических инструкций про 0.3.48.** Полный технический контракт находится в [AUDIO-LIFECYCLE-DESIGN-2026-10-29.md](AUDIO-LIFECYCLE-DESIGN-2026-10-29.md). Вначале сверить фактический HEAD рабочей ветки, потому что документационный коммит меняет SHA.

- **Последний проверенный кодовый коммит:** `04588acf3495cff41603c2a9ea12ed3cabdddf83`. Полная проверка **PASS**: https://github.com/manufact-test/nomusic/actions/runs/40926420266 (host tests, API 36 compile, D8, Android offline toolkit).
- **Только Android.** Изменения с контрольной точки `b9c3e383` ограничены `android/native-companion/` и `docs/android/`. Desktop 0.4.65, сервер, CMS, сайт и каталог не изменялись. PR #22 — по-прежнему OPEN/DRAFT, Issue #20 — OPEN.
- **Новая архитектура:** `AudioOwnership` — единственный программный владелец громкости, разрешения на запуск/паузу/seek декодера, прикрепления `DynamicsProcessing` и безопасного возврата оригинала. `SourceEventArbiter` — единый классификатор событий Media3. `ClockSupervisor` — единственный действующий контроллер коррекции/отказа при рассинхронизации. Старые `SyncPolicy` и `DriftGuard` больше не принимают решения в `ReplacementEngine`.
- **Обязательные новые тесты:** `TestAudioLifecycle`, `TestAudioCommandGateway`, `TestSourceEventArbiter`, `TestClockSupervisor`, `TestHonor051Journal` с обезличенной фактической трассой 0.3.51, `check_audio_architecture.py` (запрещает прямые команды звука в обход контроллера). CI также выполняет все прежние сценарии паузы, перемоток, Bluetooth, повторов, обрывов, задержек и 16 исполняемых addon-тестов.
- **Реальные ошибки 0.3.51:** устойчивый drift 1156–1166 мс больше не допускается; несовпадение длительности 1469 мс блокирует только конкретную замену; старые Media3-переходы не должны глушить новую песню; преждевременное окончание декодера возвращает оригинал с понятным статусом. Сценарий `Стоп → Старт` на той же песне тоже закрыт регрессионным тестом.
- **Backup-ветки:** `backup/android-architecture-reset-head-20261029`, `backup/android-phase1-audio-lifecycle-20261029`, `backup/android-before-transport-command-gateway-20261029`, `backup/android-audio-command-gateway-green-20261029`. Старые три backup-ветки 0.3.51/до рефакторинга/handoff не трогать. Перед новой крупной переделкой создавать ещё одну ветку.
- **НЕ готовый релиз:** APK 0.3.52 НЕ собран и НЕ подписан; последняя установленная и не принятая на HONOR версия — 0.3.51. Автоматические тесты подтверждают команды, но не акустическое отсутствие наложения двух независимых Android audio sessions. До релиза требуются финальный архитектурный аудит, проверка Android-ограничений и физическое прослушивание на HONOR/Bluetooth после одной новой сборки. Не предлагать пользователю тестировать отдельные незавершённые APK.

# CELIKOM Android — НАЧНИ ОТСЮДА · 29 октября 2026

> **Актуальная передача ПОСЛЕ проблемной 0.3.51.** Этот файл заменяет старую передачу 0.3.48: старые советы выпускать/проверять 0.3.48 устарели. Главный подробный документ: [ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md](ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md). История прежнего NEXT-CHAT сохранена в backup-ветках Git.

## Задача нового чата — НЕ очередной APK

Пользователь месяц тестирует нестабильную Android-подмену звука CELIKOM поверх **установленной** Яндекс Музыки. В 0.3.51 сохраняются наложения соседних песен, скачки в начале, обрыв на границе, устойчивый drift >1 секунды и скрытый отказ замены на целую песню. Мелкие патчи fade/seek/pause приводили к возврату симптомов. **Пользователь требует СМЕНЫ ПОДХОДА: спроектировать и затем переписать именно механизм управления аудио Android, прежде чем делать новый подписанный APK.** Не путать эту просьбу с разрешением просто подкрутить DriftGuard или таймеры и сразу предложить 0.3.52.

## СНАЧАЛА ПРОЧТИ И ПРОВЕРЬ

1. `docs/android/ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md` — новый главный checkpoint: доказанные сбои, состояние незавершённого кода, план системной переработки, критерии готовности.
2. `docs/android/REGRESSION-GATES-2026-10-29.md` — актуальная матрица; старые разделы по 0.3.48 исторические.
3. `docs/android/ISOLATION.md`, `android/native-companion/README.md`, `android/native-companion/build-inputs.json`, `build_release.py`, `verify_release.py`.
4. Код `ProbeService.java`, `ReplacementEngine.java`, `AudioOwnership.java`, `SyncPolicy.java`, `DriftGuard.java`, `SourceTransitionGate.java`; все tests и Android GitHub Actions.
5. Проверь HEAD и PR перед изменениями, не ориентируйся на SHA прошлой сессии.

## GitHub и две независимые точки отката

- Репозиторий: https://github.com/manufact-test/nomusic
- **Рабочая ветка:** `feature/android-0348-audio-ownership-stabilization`.
- **HEAD до документации:** `9a0561c8946150146141316bfe5b8d6788129859`; docs commit позже изменит HEAD.
- **Бэкап последнего реального подписанного APK 0.3.51:** ветка `backup/android-0351-last-signed-20261029`, SHA `72d899c51b7c6585b5df5920057f8cc7388c9f41`.
- **Бэкап текущих промежуточных правок перед переделкой:** `backup/android-pre-architecture-refactor-20261029`, SHA `9a0561c8946150146141316bfe5b8d6788129859`.
- **PR #22** https://github.com/manufact-test/nomusic/pull/22 — OPEN/DRAFT, не сливать.
- **Issue #20** https://github.com/manufact-test/nomusic/issues/20 — не закрывать.
- **Desktop 0.4.65 / feature/api-range, backend, сайт, CMS, auth/catalog** — НЕ ТРОГАТЬ.

Резервные ветки не сбрасывать/не перезаписывать/не удалять. Перед новой архитектурной серией создать отдельный архив от фактического HEAD; не работать в backup-ветках.

## Последний файл и стабильное хранение

- Последний подписанный APK **0.3.51** / versionCode **52**, проверенный SHA256 `41825715f65ac7fb058c4f652ec3cc7d9be2f7798062aeadef16a28154f8833a`. На HONOR НЕ принят.
- Личная библиотека пользователя: `/CELIKOM/Android/Backups/CELIKOM_Android_0351_LAST_SIGNED_2026-10-29.apk` и `.../CELIKOM_Android_0351_LAST_SIGNED_2026-10-29.zip`. Файлы действительно загружены в Library; использовать поиск файлов, НЕ придумывать sandbox paths.
- Последний общий журнал: `/CELIKOM/Android/Diagnostics/CELIKOM-combined-20261029-192517.txt` (в нём 0.3.49, 0.3.50, 0.3.51 — анализировать именно 0.3.51). Не коммитить пользовательский журнал.
- Android 0.3.51 CI `40899916022` PASS, но звук не принят.
- Промежуточные `DriftGuard`, статус duration mismatch и 16 регрессий уже есть в рабочей ветке; CI `40915407643` PASS: https://github.com/manufact-test/nomusic/actions/runs/40915407643. **Из этого HEAD APK ещё не собирался и не подписывался. Это НЕ новая архитектура.**
- Приватный signing-бэкап хранить вне Git; сертификат SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.

## Первое действие нового разработчика

Продолжить без уточняющих повторных вопросов, не просить пользователя вновь тестировать неисправную 0.3.51. После прочтения документов/кода сначала создать системную архитектуру state/ownership событий, красные проверки на реальные случаи `CELIKOM-combined-20261029-192517.txt`, затем **одним крупным целостным заходом** заменить конфликтующие audio переходы, провести полную проверку границ и regressions. Только после этого решать о сборке **одного** нового подписанного APK, с проверкой DEX/подписи и честной границей acoustic evidence.

**Критерии:** непротиворечивая эксклюзивность оригинал/замена; отсутствие звучащего предыдущего decoder после track change; fail-open при нестабильном drift; понятный отказ для несовпадающей редакции без обрыва всего режима; восстановление после ошибок; не ломать улучшенные паузы/seek; никаких не подтверждённых заявлений об акустике. Если платформа не позволяет гарантировать бесшовность, прямо обосновать пределы, не притворяться, что CI проверил звук.

## Следующий Android APK — только после переписывания

Номер нового выпуска должен быть > versionCode 52, но **не повышать AppVersion и не собирать сейчас**. `build_release.py` требует SDK API36/Build Tools36/D8, Apktool2.11.1, ровно pinned JAR из `build-inputs.json`, исходный 0.3.22 base APK и приватный сертификат. Проверить `verify_release.py` на готовом подписанном пакете. GitHub Actions не располагает подписью. APK не должен уходить пользователю по недействительной ссылке.
