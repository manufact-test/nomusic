# CELIKOM Android — окончательная передача в новый чат (29.10.2026)

> **Единственный актуальный сводный документ для Android на 29 октября 2026.** Остальные файлы ниже сохраняют исторические этапы; их старые заголовки «актуально 0.3.48/0.3.51» НЕ перекрывают эту передачу. Перед любыми изменениями сверяйте GitHub HEAD и CI. Здесь подготовлен HANDOFF, а не новая Android сборка.

## 0. Неприкосновенные границы

**Разрабатывается ТОЛЬКО мобильный CELIKOM Android для HONOR/Яндекс Музыки.** Не трогать работающую компьютерную версию расширения **desktop 0.4.65**, особенно ветку `feature/api-range`. Не редактировать desktop-код, browser extension, server/backend, API, учетные записи и авторизацию, каталог песен/версий, базу, сайты, CMS, Ad Protection, продуктивное развертывание, платежи, инфраструктуру, общие секреты, общие GitHub Actions и корень репозитория.

Изменения разрешены только внутри:
- `android/native-companion/**` — Android native companion, только когда требуется;
- `docs/android/**` — документация Android;
- `.github/workflows/android-0348-validation.yml` — **исключительно** текущий изолированный Android CI; нельзя менять иные workflows.

Сравнение `b9c3e383f10630d5d55f8525e7cd300addc1e498..25767ce33ed89af1937e406b38786f60c24cde9a` показало **38 файлов и НУЛЬ изменений вне этой области**. PR по умолчанию НЕ объединять с desktop/main/master/другими ветками. Если задача требует изменения сервера, desktop или каталога — остановиться и отдельно обсудить с владельцем, а не делать тихо.

## 1. Проверенные ссылки и точка входа

- GitHub: https://github.com/manufact-test/nomusic
- **Единственная Android-рабочая ветка:** `feature/android-0348-audio-ownership-stabilization`
- HEAD **ДО документационного коммита этой передачи**: `25767ce33ed89af1937e406b38786f60c24cde9a`. Последний полный CI на этом HEAD: **SUCCESS**, https://github.com/manufact-test/nomusic/actions/runs/40942060340. Новый HEAD см. в `docs/android/NEXT-CHAT.md` / коммите handoff или запросить через GitHub; не принимать старый SHA за актуальный после обновления документации.
- Draft PR #22: https://github.com/manufact-test/nomusic/pull/22, **OPEN/DRAFT**, база `feature/android-red-regression-gates-20261029`. Не merge, не ready-for-review без явного решения.
- Issue #20: https://github.com/manufact-test/nomusic/issues/20, **OPEN**, не закрывать до реального принятия работы на телефоне.
- Последний стабильно прошедший Android-код до handoff: `7e49152d6a17cbf3d31e7b247b5e074f1fb215ac`; последующая фиксация `25767ce3` меняла только документацию, CI 40942060340 также зелёный.
- После перехода открыть в этом порядке: **этот документ** → `docs/android/NEXT-CHAT.md` → `docs/android/AUDIO-LIFECYCLE-DESIGN-2026-10-29.md` → `docs/android/RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md` → `docs/android/REGRESSION-GATES-2026-10-29.md` → `docs/android/ISOLATION.md` и `android/native-companion/README.md`. Открывать ВСЕ с Android-ветки, не с default.
- Готовый текст для вставки в новый чат: `docs/android/START-NEXT-CHAT-2026-10-29.md`.

## 2. Проблема, которую решали: история и мотивы архитектуры

Установленная Android **0.3.51 / versionCode 52** — **НЕ ПРИНЯТА** пользователем. На реальном HONOR с Яндекс Музыкой наблюдались: наложение оригинала и замещающей версии, рывки/обрывы в начале и на концах, долгий рассинхрон и ошибочное переподключение/замена при переключении песен. Последний приватный диагностический журнал: `/CELIKOM/Android/Diagnostics/CELIKOM-combined-20261029-192517.txt`; анализировать именно фрагмент 0.3.51, НЕ смешивать с .49/.50. Факты из журнала: устойчивый разъезд ~1156–1166 мс на протяжении >80 с; в другом случае несоответствие длительностей 221930 и 223399 мс (разница 1469 мс); Media3 присылал причина SEEK при смене item индексов 104→105 и далее; запоздалые события старого трека вмешивались в новый.

Прежняя попытка лечить это одиночными таймерами, отдельными audio fades и маленькими APK-патчами недостаточна и запрещена как стратегия. Пользователь потребовал системную архитектуру и целостный регрессионный проход, без установки очередной мелкой версии после каждого коммита.

## 3. Что реально реализовано в Android-коде

- `AudioOwnership.java` — state machine управления оригинальным источником, attached `DynamicsProcessing`, вторичным `MediaPlayer`, правом decoder start/pause/seek, track identity, generation/lease, разрешением positive gain, аварийным zero gain и **безопасным порядком**: сначала заглушить/остановить/освободить замену, затем вернуть нативное звучание. Невалидный/устаревший decoder не должен пробиться. `retireDecoder()` отзываeт старую epoch при пересоздании декодера даже той же песни; долгая пауза с сохранённым декодером epoch сохраняет. Стабильное воспроизведение не перезаписывает одни и те же параметры gain на каждом tick, emergency zero всегда отправляется.
- `ClockSupervisor.java` — один актуальный live-супервизор рассинхронизации. При длительном неподходящем drift (>700 мс ~1500 мс) возвращает оригинал для конкретного трека; старые `SyncPolicy` и `DriftGuard` оставлены для совместимости тестов, но **не должны** одновременно влиять на live решения.
- `SourceEventArbiter.java` — классифицирует асинхронные Media3 переходы, SEEK, stale aliases и смену item index. SEEK старой песни запрещен даже при совпавших миллисекундах.
- `ReplacementEngine.java` и `ProbeService.java` подстроены под единую ownership/event модель. `PlaybackUi.java` не объявляет замену успешно играющей только из-за подготовки файла; сообщает понятно об отказе (duration mismatch, drift, ранний конец).
- Длительности несовместимых редакций контролируются: ~1469 мс mismatch блокирует **конкретную** замену; при раннем конце декодера возвращается оригинал. Стоп → Старт на той же песне переармирует state.
- `check_audio_architecture.py` — **блокирующая защита** против возврата прямых `MediaPlayer.start/pause/seekTo`, установки effect/gain вне владельца и раздвоенных clock policies.

**Ограничение доказательства:** Yandex original output и replacement MediaPlayer — независимые Android audio sessions. Тесты доказывают последовательность программных команд в хостовых имитациях, а НЕ измеренное акустическое отсутствие наложения на железе HONOR/Bluetooth. Реальное воспроизведение 0.3.52 пока НЕ тестировалось; нельзя объявлять баг исправленным окончательно.

## 4. Автоматические тесты, которые нельзя удалить/ослабить

`android/native-companion/tests/run_engine.py` выполняет существующие многосценарные/долговременные регрессии, including original/replace race, next/seek/pause, Bluetooth/route changes, streaming, long-play, replay фактических случаев, и 16 запускаемых addon host тестов. Основные новые:
- `TestAudioLifecycle.java`: реальный host ReplacementEngine, retired same-song callback, длинная пауза, раннее завершение, стоп/rearm;
- `TestAudioCommandGateway.java`: command-only ownership, эффект, 80 одинаковых повторных grant, аварийное обнуление;
- `TestSourceEventArbiter.java`: SEEK/item index/старые aliases;
- `TestClockSupervisor.java`: BT tolerance, sustained 1160 мс drift;
- `TestHonor051Journal.java` + **обезличенный** `honor-0.3.51-clock-replay.tsv`: физически наблюдавшиеся timestamp/drift из последней 0.3.51 трассы;
- `check_audio_architecture.py`: статический blocking gate.

В CI `.github/workflows/android-0348-validation.yml`: Java17, Android SDK API36, Build Tools36.0.0, пять SHA-закреплённых JAR, host tests, 16 addon tests, D8, offline kit. Последний CI: https://github.com/manufact-test/nomusic/actions/runs/40942060340 — **PASS**.

## 5. APK: что сделано, чего ЕЩЁ нет

- Текущая подготовленная версия в исходниках: **CELIKOM Android 0.3.52 / versionCode 53** (не signed release). Единый metadata contract: `android/native-companion/release-spec.json`, `release_contract.py`, `AppVersion.java`, `build_release.py`, `verify_release.py`.
- Реальный оригинальный APK `CELIKOM-0.3.22-install.apk`, SHA256 `170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9`. Это **база для репакета**, НЕ новая версия и НЕ ответ пользователю.
- Сохранено Android-окружение в ChatGPT Library: `/CELIKOM/CELIKOM-Android-Build-Environment-20261029.tar.gz` + `.sha256` (APK0.3.22, API36, Build Tools, Apktool2.11.1, 5 JAR). Секретов signing в нём НЕТ. Если среда нового чата пустая, искать файлы в Library/материализовать; не предполагать старых `/mnt/data` и `/workspace/scratch`.
- Последний установленный подписанный пользователем `0.3.51` доступен как private `/CELIKOM/Android/Backups/CELIKOM_Android_0351_LAST_SIGNED_2026-10-29.apk`; только для сравнения подписи, не публиковать и не объявлять исправленным.
- Оригинал 0.3.22 и 0.3.51 прошли `apksigner verify` и имеют **один сертификат SHA256** `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Это открытый fingerprint сертификата, НЕ приватный ключ.
- SHA Apktool 2.11.1 `56d59c524fc764263ba8d345754d8daf55b1887818b15cd3b594f555d249e2db`. JDK17 обязателен для подписанного пакета (локальная JDK21 дала иной DEX); точные SHA пяти JAR в `build-inputs.json`.
- `build_release.py` имеет **два строго изолированных режима**:
  1. Signed production: компилирует Java сам с JDK17, требует ОРИГИНАЛЬНЫЙ `--signing-dir` (вне Git), запрещает предварительно собранный DEX, после подписи запускает полноценный `verify_release.py`.
  2. `--unsigned-inspection`: реальный Apktool decode/build/zipalign с DEX из успешного GitHub CI, обязательные `--inspection-ci-dex`, `--inspection-ci-dex-sha256`, `--inspection-ci-provenance` и имя `*-INSPECTION-UNSIGNED.apk`. Принципиально НЕ принимает signing-dir. `verify_unsigned_inspection.py` явно отказывает подписанному файлу и отмечает результат как `UNSIGNED_INSPECTION_ONLY_NOT_INSTALLABLE`. НЕ ДАВАТЬ пользователю на установку.
- `release_archive.py` в обеих проверках требует ровно `classes.dex` + `classes2.dex`, побайтовое совпадение addon DEX, неизменность множества и содержимого каталожных assets, запрет добавленных ресурсов, скрытых исходников, ключей, duplicate ZIP entries и traversal.
- `ci_provenance.py` связывает SHA Java-исходников и DEX с конкретным GitHub Actions commit. `ci-dex-provenance.json` — свидетельство сборки, НЕ криптографически удостоверенная подпись/attestation.
- В `tests/check_release_archive.py`, `check_release_contract.py`, `check_ci_provenance.py`, `check_release_modes.py` встроены отрицательные тесты на подмены, старый DEX, старый номер версии, неполный пакет и попытку выдать unsigned за release.
- **Практически** уже собирался настоящий структурный **UNSIGNED** APK0.3.52 из проверенной 0.3.22, с точно CI JDK17 DEX `8683a9f50fc2d1171206e0a803fe9f730c8e67f709909dcacecd67fa916ade98`; проверен `aapt`, `zipalign`, исходный каталог. Один свежий smoke имеет SHA `dcc2cf36133f70d5bc60071a1802631997095d279541119358f2dff64ab6c1b4`. Production `verify_release.py` **правильно отверг** его как unsigned.
- GitHub Actions run `40942060340` создаёт артефакты `celikom-android-offline-kit` и `celikom-android-0352-dex-unsigned` (НЕ подписанный APK); kit можно повторно проверить без git checkout, ключей нет. Артефакты workflow могут иметь срок хранения; скачивать актуальные из нового run.

**КРИТИЧЕСКИЙ БЛОКЕР: оригинальный приватный `celikom-native-probe.p12` и `signing.json` здесь НЕ ОБНАРУЖЕНЫ.** В ChatGPT Library / Build Environment их нет. Не создавать новый keystore: подпись несовместима с установленной. Не добавлять ключ, пароль или signing config в Git/CI/комментарии/документацию. Если они будут найдены в приватных прошлых backups — использовать только локально/офлайн, не печатать пароли и не прикреплять содержимое в PR. **Подписанного APK0.3.52 НЕТ.**

## 6. История резервных точек (не переписывать и не удалять)

- `backup/android-0351-last-signed-20261029` — 0.3.51 последняя подписанная **неудачная**;
- `backup/android-pre-architecture-refactor-20261029` — до redesign;
- `backup/android-architecture-reset-head-20261029`, `backup/android-phase1-audio-lifecycle-20261029`, `backup/android-before-transport-command-gateway-20261029`, `backup/android-audio-command-gateway-green-20261029`;
- `backup/android-audio-architecture-checkpoint-20261029` → `aaef1741`;
- `backup/android-audio-callback-fencing-green-20261029` → `ce52b178`; `backup/android-callback-audit-docs-20261029` → `351d9cac`;
- `backup/android-before-0352-release-pipeline-20261029` → `351d9cac`;
- `backup/android-0352-release-contract-green-20261029` → `04a583a5`;
- `backup/android-0352-structural-smoke-docs-20261029` → `0e5fb193`;
- `backup/android-0352-provenance-and-archive-verified-20261029` → `7e49152d`;
- `backup/android-0352-audited-provenance-docs-20261029` → `25767ce3`;
- **Новый pre-handoff:** `backup/android-before-handoff-20261029-final` → `25767ce3`.

После коммита передачи создать новую ПОСЛЕДНЮЮ backup-ветку от него. Новые большие изменения всегда сначала сохранять в собственный новый backup. Не force-push старые бэкапы.

## 7. Что использовать / чего избегать / порядок следующего захода

**Использовать:** текущую Android-ветку и новый handoff; `AudioOwnership/ClockSupervisor/SourceEventArbiter`; обезличенный HONOR 0.3.51 fixture и действующий CI; SHA-проверенный base APK0.3.22 + pinned toolchain; текущие version-contract/production release/unsigned inspect скрипты; прозрачную diagnostics для следующей возможной ошибки.

**НЕ использовать в качестве актуальной реализации:** прежние подписанные APK 0.3.48–0.3.51, их старые ветки/инструкции как latest, отдельные таймерные патчи и конкурирующие sync policies, unsigned inspection в качестве установщика, DEX от старого commit, локальный JDK21 для финального signed build, новый signing certificate вместо прежнего, старые контейнерные пути из другого чата.

**Следующий ход:**
1. Подключить GitHub и СНАЧАЛА прочитать этот документ. Сверить HEAD/PR/CI/область изменений, не писать в ветку desktop.
2. Оценить возможность достать именно **оригинальные** signing credentials из авторизованного защищённого источника. Старый build-архив их НЕ содержит. Ничего не угадывать, не выдавать иной сертификат за прежний. Если ключ доступен, выполнить **один** полный signed build на JDK17 и `verify_release.py`, перепроверить SHA и файл APK до предоставления пользователю. Если ключа нет — чётко сказать, что выпуск заблокирован, и не создавать замену.
3. При необходимости ещё проверить safety подписывающего пути, но **не тратить чат на бесконечные новые статические тесты ради галочек**: основной architecture/host/DEX/packaging уже достаточно тщательно прогнан. Желаемый следующий осязаемый этап — **одна подписанная 0.3.52**.
4. Только после verified signed APK попросить владельца выполнить единый комплексный тест HONOR / Яндекс Музыка / Bluetooth (границы песен, skip, короткая и длинная паузы, seek, связь/Bluetooth route, долгий play + drifting). Реальные наложения/перебои проверяются слухом и новой diagnostic, а не CI.
5. Ошибки разбирать без догадок по поддерживаемому журналу, устранять root cause в Android only; перед изменениями делать backup. Desktop и production не затрагивать. Не закрывать Issue20/PR22 до пользовательского принятия.

**Принцип общения с владельцем:** крупные целостные этапы, самостоятельная проверка до отчёта; не отправлять каждые 5 минут полусобранный APK и не требовать у пользователя повторить уже предоставленные сведения. Сохранять промежуточную версию прежде каждой серьёзной правки. Говорить честно: «programmatic CI PASS» не равняется «physically zero overlap». Пользователь просит только телефон; десктоп в этом чате остаётся без изменений.
