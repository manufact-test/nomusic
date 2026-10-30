Привет! Продолжаем разработку **CELIKOM Android (только телефон)** после завершения предыдущего чата. Ты — новый главный разработчик Android-части и самостоятельный интегратор именно этого модуля. Передаю полную проверенную точку и правила.

**ПОДКЛЮЧИСЬ К GITHUB И СНАЧАЛА ПРОЧИТАЙ ДОКУМЕНТЫ, НЕ ПИШИ НОВЫЙ КОД ДО ИЗУЧЕНИЯ ПЕРЕДАЧИ.**

**Репозиторий:** https://github.com/manufact-test/nomusic

**Единственная рабочая Android-ветка:** `feature/android-0348-audio-ownership-stabilization`

**PR #22:** https://github.com/manufact-test/nomusic/pull/22 — OPEN/DRAFT, НЕ MERGE.

**Issue #20:** https://github.com/manufact-test/nomusic/issues/20 — OPEN до принятия пользователем.

**Последний проверенный HEAD перед передающими документами:** `25767ce33ed89af1937e406b38786f60c24cde9a`. Последняя зелёная CI: https://github.com/manufact-test/nomusic/actions/runs/40942060340. После публикации документов HEAD должен измениться: сверь фактический SHA в GitHub, не откатывай docs, проверь новую CI.

**Главный документ с подробным состоянием и запретами:** `docs/android/HANDOFF-2026-10-29-ANDROID-0352.md`. Прочитай его полностью. Также `docs/android/NEXT-CHAT.md`, `docs/android/AUDIO-LIFECYCLE-DESIGN-2026-10-29.md`, `docs/android/RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md`, `docs/android/REGRESSION-GATES-2026-10-29.md`, `docs/android/ISOLATION.md`.

### АБСОЛЮТНАЯ ГРАНИЦА: ТОЛЬКО ANDROID

**Компьютерное расширение CELIKOM desktop 0.4.65, ветка `feature/api-range`, полностью неприкосновенно.** НЕ меняй его файлы, не мержи Android туда, не исправляй «заодно» десктоп или его VPN/reconnect. Также НЕ трогай backend, сервер, авторизацию, каталог, API, сайт, CMS, Ad Protection, production deployment, shared workflows, secrets. Изменения только `android/native-companion/**`, `docs/android/**` и, при реальной необходимости, отдельный `.github/workflows/android-0348-validation.yml`. Ранее сравнение с `b9c3e383` показало 38 изменений, **все** только в этой области.

### ПОЧЕМУ МЫ ЗДЕСЬ

Последняя установленная подписанная Android **0.3.51/code52 НЕ ПРИНЯТА**: на HONOR в Яндекс Музыке слышались наложения оригинала и замены, скачки/обрывы на границах, иногда длинный разъезд в ~1160 мс, несовпадение длительности версии 1469 мс, поздние Media3 события от старой песни вмешивались в новую. Частые маленькие APK-патчи оказались плохой стратегией. Пользователь потребовал **цельную архитектурную переделку**, не выпускать очередную промежуточную APK и сначала покрыть серьёзными регрессиями.

Приватный последний журнал есть в Library: `/CELIKOM/Android/Diagnostics/CELIKOM-combined-20261029-192517.txt`; в репозиторий попала ТОЛЬКО обезличенная replay-фактура `android/native-companion/tests/honor-0.3.51-clock-replay.tsv`.

### ЧТО УЖЕ ПЕРЕДЕЛАНО

`AudioOwnership.java` — единый authority команды оригинального и заменяющего звука, native `DynamicsProcessing`, `MediaPlayer`, без повторных gain-команд, с lease/epoch и безопасным восстановлением оригинала. `ClockSupervisor.java` — единственный действующий алгоритм drift/fail-open (старые `SyncPolicy`/`DriftGuard` не должны управлять live). `SourceEventArbiter.java` — Media3 track/seek/alias/obsolete-event gate. `ReplacementEngine.java` и `ProbeService.java` интегрированы с ними; исправлены ранний конец, несовпадение длительности, повторная загрузка той же песни после сбоя, long pause, stop/start. `PlaybackUi` выводит честные статусы.

Большой host/regression suite: `TestAudioLifecycle`, `TestAudioCommandGateway`, `TestClockSupervisor`, `TestSourceEventArbiter`, `TestHonor051Journal`, `check_audio_architecture.py`, старые long-run, Bluetooth, skip/seek/pause, 16 addon tests. Всё зелёное. Но host-tests **не доказывают физическое неналожение** независимых audio sessions на HONOR/BT.

### ГОТОВНОСТЬ 0.3.52 И ОСНОВНОЙ БЛОКЕР

Текущий Android исходный код помечен **0.3.52 / versionCode53**. Уже есть проверенный на настоящем базовом 0.3.22 APK **НЕПОДПИСАННЫЙ структурный smoke**, в котором `aapt`, `zipalign`, исходные assets и точный JDK17 CI DEX успешно проверены. Это **не установщик для пользователя**, его не выдавать.

Есть воспроизводимый `build_release.py` и два НЕПЕРЕСЕКАЮЩИХСЯ режима:
- обычная подписанная сборка = **только оригинальный приватный signing-dir + JDK17 + текущие Java исходники**, затем `verify_release.py`;
- `--unsigned-inspection` = полноценная проверка APK-структуры с CI DEX/source-provenance, без ключей и с явным суффиксом `-INSPECTION-UNSIGNED.apk`. Не пытаться установить или выдать как release.

Скрипты `release_contract.py`, `release_archive.py`, `ci_provenance.py` + тесты `check_release_contract.py`, `check_release_archive.py`, `check_ci_provenance.py`, `check_release_modes.py` защищают от подмены версии, каталога, APK/DEX, использования старого кода и нового сертификата. Полный GitHub CI 40942060340 PASS, переносимый offline-kit реально проверяли отдельно без git checkout.

**ПРОБЛЕМА:** оригинальные приватные `celikom-native-probe.p12` и `signing.json` из прежнего окружения пока не найдены. Архив `/CELIKOM/CELIKOM-Android-Build-Environment-20261029.tar.gz` из ChatGPT Library содержит базовый APK0.3.22, Android SDK API36, Build Tools, Apktool2.11.1 и пять точных JAR, но **НЕ содержит ключей подписи**. `/CELIKOM/Android/Backups/CELIKOM_Android_0351_LAST_SIGNED_2026-10-29.apk` — старый подписанный/неудачный APK для сверки подписи. 0.3.22 и 0.3.51 имеют одинаковый сертификат SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. НЕ ГЕНЕРИРУЙ НОВЫЙ КЛЮЧ — тогда обновление установленного приложения сломается. Секреты не публикуй и не коммить.

**СЕЙЧАС ПОДПИСАННОГО APK 0.3.52 НЕТ.** Полностью пройденная структурная проверка и CI не означают, что физическое воспроизведение уже исправлено.

### БЭКАПЫ И СЛЕДУЮЩАЯ РАБОТА

Сохранять все backup ветки, особенно `backup/android-0351-last-signed-20261029`, `backup/android-pre-architecture-refactor-20261029`, `backup/android-0352-provenance-and-archive-verified-20261029`, `backup/android-0352-audited-provenance-docs-20261029`, `backup/android-before-handoff-20261029-final` и новейший backup, указанный в HANDOFF. Прежде следующих больших изменений создать свежую backup-ветку от фактического HEAD. Никогда не удалять историю/force-push.

**Твоя последовательность:** (1) GitHub → прочитать HANDOFF и docs, сверить Android HEAD, PR, CI и ограничения; (2) найти возможность **безопасно восстановить именно исходный signing key**, не выдумывать и не подменять; (3) когда доступен старый ключ — сделать **одну** настоящую подписанную 0.3.52 на JDK17, прогнать полный `verify_release.py`, сертификат/version/assets/DEX, только затем дать установщик; (4) пользователь проведёт **один комплексный тест** HONOR/Яндекс Музыка/Bluetooth: Next, границы, короткая/долгая пауза, seek, route/reconnect, длинное воспроизведение и диагностика. Если ключ всё ещё недоступен — прозрачно сообщить блокер и не заниматься бесконечной сменой мелочей в Android ради коммитов.

Работай **большими законченными этапами**, сам проверяй, не останавливайся после каждого теста с «продолжать?», не проси переустанавливать недоделанное, не обещай реальную акустическую корректность до теста на HONOR. Важнее всего: **НЕ ТРОГАЙ КОМПЬЮТЕРНУЮ ВЕРСИЮ.**

Начинай с подключения GitHub и чтения `docs/android/HANDOFF-2026-10-29-ANDROID-0352.md`; доложи только фактическую найденную точку и двигайся по плану.