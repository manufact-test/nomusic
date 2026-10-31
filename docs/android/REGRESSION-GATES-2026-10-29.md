> **31.10.2026 — NEW MANDATORY HONOR 0.3.67 slow-stream RED/GREEN gates; NO APK.** In 0.3.67 cellular+VPN, successive Yandex finger positions preceded async decoder callbacks **2792 → 933 → 17 ms**, and five background HTTP Range prefetch failures left a sparse song without later fill. While the original was already at full volume and replacement decoder at zero/paused, `ReplacementEngine` unnecessarily released and later reattached its source DSP effect. `TestHonor067SlowStreamSeek` (11 checks) now requires the **same verified original effect** to remain attached during the whole slow wait, the latest seek position to win, and true Pause/Next/Stop to revoke stale callbacks. `TestBufferedAudio` now sends three HTTP503s on a prefetch block, then successfully reads another demanded block **before the old failure callback exits**, requiring **one recoverable background fill** (including a pending wakeup) with byte-exact ETag/Range validation, no eternal timer retry and no worker before the initial playback lifecycle requests prefetch. Host + isolated Java tests PASS locally; **GitHub SDK36/D8 [41211791265](https://github.com/manufact-test/nomusic/actions/runs/41211791265) SUCCESS, publish SKIPPED**. Physical HONOR listening still required. This does **NOT** resolve network stall duration or phase-unverified admin cold join. See [`ANDROID-0367-HONOR-SLOW-RANGE-OWNER-AUDIT-2026-10-31.md`](ANDROID-0367-HONOR-SLOW-RANGE-OWNER-AUDIT-2026-10-31.md).

---

> **31.10.2026 — new mandatory 0.3.66 red/green regression.** Two separate HONOR 0.3.66 runs establish 37 default versus 29 lab-mode seeks, with no commanded gaps in either; the linear-run trace has 14 BUFFERING and 15 resume-fast transactions. Critical ordering: native decoder seek complete → muted decoder clock gate pending → short Media3 BUFFERING → READY. On released 0.3.66 this **revoked and restarted** an existing muted handover. `TestHonor066SeekBufferReplay` must fail on 0.3.66 and pass only if short BUFFERING retains the current *silent* handover ticket, while long stalls, genuine user pause, Next and stale callbacks still revoke it. 24 new assertions pass locally; SDK36/D8 CI and physical HONOR/BT QA remain mandatory. See [`ANDROID-0366-DUAL-HONOR-DIAGNOSTICS-2026-10-31.md`](ANDROID-0366-DUAL-HONOR-DIAGNOSTICS-2026-10-31.md). The linear cold join still lacks verified acoustic phase and is **NOT accepted**.

---

> **31.10.2026 — experimental seek ownership checkpoint, still NO RELEASE.** The new `TestHonor065Media3Continuity` uses the production `Media3SourceRouter` from `ProbeService`: index-changing manual Next-as-SEEK → six cached seeks → automatic transition → six cached seeks → three partial HTTP seeks. It was RED on 0.3.65's both-muted cached seek and is GREEN after immediate fail-open source ownership and removal of per-scrub cold dips. Local host suite PASS and staging Android SDK36/D8 GitHub CI [41194035806](https://github.com/manufact-test/nomusic/actions/runs/41194035806) SUCCESS with publishing SKIPPED; physical HONOR audio remains unverified. **Cold entry's 500ms full-volume valley remains unresolved.** See [`AUDIT-2026-10-31-0365-CONTINUITY-STAGING.md`](AUDIT-2026-10-31-0365-CONTINUITY-STAGING.md). Do not push staging Android code to the original autopublishing branch or sign an interim APK.

---

> **2026-10-31 — additional RED gates from HONOR 0.3.65.** See [current diagnostic and handoff](HANDOFF-2026-10-31-AFTER-0365-HONOR-REVIEW.md) before any audio change. New required integration tests: actual Media3 manual Next via `ProbeService`/`SourceEventArbiter` followed by repeated cached seeks, then a natural next and more seeks; partial-stream seeks with repeated 500ms handovers; command silence observed in 0.3.65 for **43–194ms** even though seek callbacks took **20–77ms**. Host `TestHonor064ManualNext` alone is inadequate: it calls `sourceBoundary` directly and does not simulate external Next. Acoustic acceptance requires continuous smooth entry, not the currently deliberate down-to-zero/up-to-full valley. Older gates and all pause/BT/tail regressions remain mandatory. **0.3.65 is not approved; docs-only checkpoint, NO APK.**

---

> **АКТУАЛЬНОЕ ДОПОЛНЕНИЕ (30.10.2026):** [UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md](UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md) и [HANDOFF-2026-10-30-UNIFIED-AUDIO.md](HANDOFF-2026-10-30-UNIFIED-AUDIO.md). Контракт новых регрессий: PREPARE_READY+SEEK/PAUSE/BUFFERING/BOUNDARY, stale callback after Stop/logout, 10 rapid skips, route loss, no audible dual output. Базовый Android CI `41019895272` SUCCESS на `8128307d0daf95f3386b85791db5347e3ec56357`. Текущий 0.3.54 AUDIOFIX signed с оригинальным ключом уже протестирован на HONOR, но аппаратная бесшовность НЕ принята. Нижние версии/утверждения о потерянном ключе исторические.

---

> **СУПЕРСЕДЕД: ЗА ТЕКУЩИМ СТАТУСОМ СМОТРИ** [HANDOFF-2026-10-29-ANDROID-0352.md](HANDOFF-2026-10-29-ANDROID-0352.md). Новое: только Android, desktop 0.4.65 не менять, CI 40942060340 PASS, версия 0.3.52 готова только как НЕПОДПИСАННЫЙ structural smoke, оригинальный приватный ключ подписи отсутствует.

---

## Новый обязательный gate — APK integrity / CI provenance (29.10.2026)

| Область | Инвариант и фактическая проверка |
| --- | --- |
| Подмена или удаление ресурсов каталога | `release_archive.inspect_zip`: идентичные имена и байты original assets; в реальном APK — 3 исходных assets, без добавлений; 16 отрицательных тестов |
| Лишние DEX, обманная подпись, исходники/ключи | Только `classes.dex` и `classes2.dex`, 2-й DEX byte-identical от GitHub CI, ZIP paths/duplicate/name защита; signed gate всегда выполняет `apksigner verify` |
| Устаревший compiled DEX при новом Android-коде | `ci_provenance.py`: CI commit + digest ВСЕХ Java-файлов + DEX SHA, неправильный commit/source/Dex reject; 11 negative cases |
| Ошибочный выпуск unsigned | Только `--unsigned-inspection` + явное имя `*-INSPECTION-UNSIGNED.apk`; запрет --signing-dir; signed path не принимает CI-prebuilt DEX |
| Реальный переносимый kit | Скачать ZIP GitHub Actions; запустить все четыре contract/archive/mode/provenance теста без Git checkout; в ZIP отсутствует signing |
| Физический HONOR / BT | **Не проверено**; host и APK smoke не подтверждают реальный акустический результат |

Полный CI `7e49152d` — **PASS**, https://github.com/manufact-test/nomusic/actions/runs/40941509415. См. последнюю секцию [NEXT-CHAT.md](NEXT-CHAT.md) и практический [RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md](RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md). Старую матрицу ниже сохраняем.

---

## Android 0.3.52: дополнительные обязательные release gates · 29.10.2026

| Gate | Доказательство и запрет |
| --- | --- |
| Синхронность версии приложения, скриптов и APK | `release-spec.json`, `release_contract.py`, `AppVersion.java`, `check_release_contract.py`, `aapt dump badging`; только `0.3.52` / code 53 |
| Неподменённые инструменты и исходные байты | SHA Apktool2.11.1 `56d59c…`, JDK17 (сборщик запрещает иной для релиза), SDK API36, пять точных JAR, SHA базового 0.3.22 |
| Достоверный Apktool YML | Обработка реального `versionInfo:` с отступами, сохранение перевода строк, строго по одному имени и коду версии; красные тесты malformed/duplicate |
| Подпись | Базовый 0.3.22 и последний установленный 0.3.51 имеют одинаковую v3 подпись, но исходный секретный ключ недоступен; **unsigned не является кандидатом**. `verify_release.py` отказывается принимать unsigned |
| Ресурсы и DEX | Структурный smoke: `zipalign` PASS, оба `classes*.dex`, assets сохранены, `classes2.dex` строго равен JDK17 GitHub Actions DEX `8683a9f5…` |
| Реальное звучание | HONOR/BT ещё не тестировался на 0.3.52; CI и structural smoke не могут доказать отсутствие акустического наложения двух Android аудиосессий |

Последний CI PASS: https://github.com/manufact-test/nomusic/actions/runs/40937933292, код `04a583a5`. Полная запись: [RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md](RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md). Более ранние регрессионные матрицы ниже остаются действующими для аудио и историческими для версии.

---

## Дополнение: проверенные дефекты архитектуры после последнего прохода

| Новый риск | Блокирующий тест/поведение |
| --- | --- |
| Повторные `DynamicsProcessing.setInputGainAllChannelsTo(-100)` и повторные `MediaPlayer.setVolume(1)` на каждом tick | `TestAudioCommandGateway`: 80 одинаковых grant/gain должны дать только одну команду; нулевая громкость никогда не пропускается |
| Старое событие SEEK от соседней песни с совпадающим временем | `TestSourceEventArbiter`: сверить текущую, live и старую media alias, а не только skew секунд |
| Повторная загрузка той же песни после ошибки, старый callback | `TestAudioCommandGateway` и `TestAudioLifecycle`: retire epoch при освобождении декодера, callback старого decoder не затрагивает новый |
| Долгая пауза без освобождения декодера | `TestAudioLifecycle`: восстановление нативного audio effect не инвалидирует callback сохранённого плеера |
| Версия подписываемого APK | Старые скрипты настроены на 0.3.51/versionCode 52: перед релизом новой 0.3.52 синхронно обновить упаковку, верификатор и `AppVersion` |
| Физическое звучание HONOR/Bluetooth | CI **не** доказывает отсутствие наложения в независимых audio sessions |

Последний зеленый полный CI: https://github.com/manufact-test/nomusic/actions/runs/40931276362; код `ce52b178`, backup `backup/android-audio-callback-fencing-green-20261029`. Старые разделы ниже сохранены для истории.

---

## Новая обязательная матрица Android — системный аудиодвижок, 29 октября 2026

**Этот раздел заменяет старые указания ниже про «установленную 0.3.48».** Последняя установленная версия 0.3.51, она не принята. Подписанной следующей версии нет.

| Инвариант | Запрет на релиз без проверки |
|---|---|
| Только один владелец аудиокоманд | `check_audio_architecture.py` не допускает прямые `MediaPlayer.start/pause/seekTo` и изменение native gain в `ReplacementEngine` |
| Аудиоэффект принадлежит текущему треку | `AudioOwnership` привязывает `DynamicsProcessing` к одному источнику и эпохе; `TestAudioLifecycle`, `TestAudioCommandGateway` |
| Исторический Media3 SEEK с новым индексом песни | `SourceEventArbiter` и `TestSourceEventArbiter`: строки 104→105…108→109 из 0.3.51, stale seek 3648→61334 мс |
| Рассинхронизация ~1160 мс | `ClockSupervisor`, `TestRealFailures`, `TestClockSupervisor`, `TestHonor051Journal`; fail-open на оригинал только для плохого трека |
| Обычная Bluetooth-задержка 240–550 мс | `TestCarRecovery`, `TestHandoverClock`, `TestHonor051Journal`; не делать повторные слышимые seek |
| Несовпадение длительности 1469 мс и ранний конец замены | `TestRealFailures`, `TestAudioLifecycle`; не расширять порог безопасного совпадения 500 мс |
| Пауза, seek, Stop/Start, отключение наушников, завершение трека | `TestEngine`, `TestResumeClock`, `TestAudioOwnershipRegression`, `TestCarRecovery`, `TestLongRun` |
| Сборочная целостность | Полный `tests/run_engine.py`, 16 runnable `addon/Test*.java`, pinned JAR SHA256, API36 javac и D8. Конечный подписанный APK проверяется отдельно через `verify_release.py` |
| Реальный аппаратный звук | HONOR/BT тест после сборки. CI не измеряет акустический output, поэтому ни один PASS не означает, что пользователь принял исправления |

Последний проверенный код: `04588acf3495cff41603c2a9ea12ed3cabdddf83`, GitHub Actions https://github.com/manufact-test/nomusic/actions/runs/40926420266 — PASS. Полная спецификация и ограничения: `AUDIO-LIFECYCLE-DESIGN-2026-10-29.md`.

# Актуальная матрица для архитектурной переработки ПОСЛЕ Android 0.3.51

> **29.10.2026, supersedes historical 0.3.48 instructions below.** Полный источник статуса, бэкапов и архитектуры: [ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md](ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md). Пользователь не принял 0.3.51. **Не выпускать кандидат после маленькой правки таймера; пока только переработка архитектуры.**

## Обязательные новые gates

| Реальный случай / риск | Обязательное поведение | Проверка |
| --- | --- | --- |
| Источник alias106 «Есть вопросы», drift держался 1,156–1,166 сек более 80 сек | Нельзя показывать здоровую работающую подмену, если управляемые часы длительно расходятся; восстановить оригинал, не зациклить seek/fade; указать причину | `TestRealFailures`, новые replay/instrumentation проверки после рефакторинга, исходный комбинированный лог |
| Alias108 «Всё пиздато», native 221930 мс, replacement 223399 мс (1469 мс разницы) | **Не** проигрывать потенциально другую редакцию; native играет, причина понятна на экране; следующий трек автоматически может подменяться, без нового Start | `TestRealFailures`, UI/status test, E2E run |
| 0.3.51 alias105→106 и последующие переходы; пользователь слышал смесь песен и скачки | Старый decoder всегда глушится до восстановления нативного аудио; stale callbacks не оживляют старый трек; истечение/zero position не считать достаточным доказательством boundary | `TestAudioOwnershipRegression`, `TestHandoverClock`, детерминированный replay реального перехода, телефон |
| `outgoingItemReset` в 0.3.51, не зарегистрировал ни одного `replacement_outgoing_reset` | Не считать эту защиту проверенной: доказать срабатывание на реальном lifecycle и перепроверить на ложные срабатывания | Media3 transition/read fence + запись точных state snapshots |
| Возобновление и seek на 0.3.50 улучшились, drift 3–11 мс после prealign | Не потерять это поведение при новой state machine; разнести seek/pause/route и таймеры по поколениям | `TestResumeClock`, `TestCarRecovery`, `TestAudioOwnershipRegression`, hardware |
| Потеря audio effect / stream / callback / source / ручной Stop | Безопасный fail-open: secondary mute, исходный gain восстановлен; не запустить устаревший decoder | Existing full engine/stream/boundary/security tests, negative cases |
| Разный маршрут Android, Bluetooth, выключенный экран | Не обещать акустический результат по fake API или available-device list; с согласия владельца отдельно проверить физический output | Инструментация и единый объединённый owner test после полного рефакторинга |
| Release integrity | Из конкретного HEAD собирается signed APK, DEX в APK соответствует CI-компиляции, versionCode >52, старый сертификат, никаких secret assets | GitHub CI + `verify_release.py` + SHA256 APK и backup |

Обязательный host suite: `python3 android/native-companion/tests/run_engine.py`, `android/native-companion/addon/Test*.java`, isolation guard. **CI 40915407643 PASS подтверждает 16 дополнительных тестов и компиляцию промежуточного кода, но не закрывает ни один аппаратный дефект.** Работа по архитектуре должна дать новый красный/зелёный replay и проверку восстановления во всех переходах.

**Сохранено до переделки:** `backup/android-0351-last-signed-20261029` и `backup/android-pre-architecture-refactor-20261029`. Проверенный 0.3.51 установщик и ZIP лежат в Library пользователя; см. checkpoint. PR #22 остаётся черновиком.

---

## Историческая матрица 0.3.48 (НЕ текущая инструкция к выпуску)

# CELIKOM Android — регрессионная матрица и правила выпуска (29.10.2026)

**Актуально для кандидата 0.3.48; не является пользовательской приёмкой.**

## Зачем этот документ

В версиях 0.3.45–0.3.47 пользователь наблюдал повторяющиеся симптомы: одновременно слышны две версии или соседние песни, пауза/возобновление даёт рывок, перемотка/буферизация заставляет восстанавливать и заново приглушать оригинал, смена песни/конец трека создаёт сбой или повторное подключение. Зелёные прежние host-тесты не проверяли *инвариант исключительной слышимости*. Эти жалобы нельзя закрывать подбором одного таймера.

Первичный реальный журнал: `CELIKOM-combined-20261029-140931.txt` (0.3.47, 14:01:27 +03:00). Полный пользовательский журнал содержит личные сведения о прослушивании — **не коммитить его**. Контрольная задача: GitHub issue #20. Старые «RED» проверки: PR #21.

## Модель 0.3.48

- `AudioOwnership.java`: одна точка выдачи разрешения на ненулевую громкость подмены, состояния `SOURCE`, `PREPARING`, `ALIGNING`, `REPLACEMENT`, `PAUSED`, `RESTORING`; уникальный lease ожидающей паузы.
- `ReplacementEngine.java` использует **break-before-make**. При переходе к подмене оригинал получает `-100 dB` до роста громкости `MediaPlayer`. При возврате оригинала сначала сбрасывается громкость вторичного плеера.
- Обновление/выход из паузы инвалидирует старые delayed callbacks, сохраняя защиту синхронизации при in-flight seek.
- При повторном подключении эффекта к *уже запущенному* decoder запрещён прямой переход к полной громкости.
- При stream/buffer ожидании secondary сначала глушится/паузится, только потом восстанавливается original.
- **Не менять** готовые: 500 мс охрана длительностей (0.3.46), 180 мс повторный fade (0.3.46), 1000 мс удержание эффекта нормальной короткой паузы с аварийной дорожкой 350 мс (0.3.47), Bluetooth-порог 350 мс, работа оригинального каталога.

`AudioOwnership` — централизованный *аудио grant*, а НЕ обещание, что все независимые состояния транспорта полностью заменены универсальной state machine. Физическую эксклюзивность на Android/Bluetooth нельзя доказать Java-заглушкой без измерения выходного звука.

## Обязательные проверки перед любой следующей APK

| Симптом / инвариант | Тест / условие |
| --- | --- |
| Два слышимых потока одновременно | `TestAudioOwnershipRegression`: каждый шаг плавного переключения; `TestHandoverClock`, `TestStreamingEngine` проверяют, что при ненулевой громкости замены источник уже `-100dB` |
| Pause→seek→resume и запоздалый таймер | `TestAudioOwnershipRegression`: зафиксированная из 0.3.47 ситуация с in-flight seek и устаревшим source snapshot; ожидаем сохранение текущего эффекта |
| Промежуточная пауза и возврат после долгой | `TestResumeClock` (813 мс и >1000 мс), `TestEngine`, `TestAudioOwnershipRegression` |
| Стриминг/буфер/обрыв и коррекция позиции | `TestStreamingEngine`, `TestHandoverClock`, `TestPhoneReplay` |
| Конец песни, несовпадающая длительность, повтор | `TestResumeClock`, `TestEngine` (500 мс duration gate), `TestLongRun` |
| Новая песня, старый seek/response, маршрут Bluetooth | `TestAudioOwnershipRegression`, `TestCarRecovery`, `TestLongRun`, `TestEngine` |
| Отправка жалоб/авторизация и независимость от audio queue | `addon/TestMobileActions`, `TestDiagnosticRequest`, прочие `addon/Test*.java` |
| Передача/упаковка готового APK | `build_release.py` -> `verify_release.py` проверяет подписанный APK (не только исходники/промежуточный DEX), старый сертификат, manifest, API, отсутствие ключей и обязательный `AudioOwnership` в DEX |

Выпуск обязан запускать `python3 android/native-companion/tests/run_engine.py` **вместе** с остальными тестами, а не только специфический тест текущего исправления. `build_release.py` запускает все эти тесты автоматически и прекращает сборку при ошибке. GitHub Actions isolation guard проверяет границы изменений, **не является сборкой Android APK**.

## Установленные факты и ограничения

- 0.3.47 запуск от 14:01:27: есть `replacement_resume_fast` → `replacement_original_restored` во время перемотки; несогласованный жизненный цикл эффекта.
- В 0.3.47 тестовый midpoint имел `originalMix ≈ 0.5` и `MediaPlayer.volume ≈ 0.5`: заложенное кодом наложение. После 0.3.48 тест проверяет исключительность.
- 0.3.48: весь host suite, 300 автоматических переходов и 15 виртуальных часов, тесты полномасштабной сборки, независимая проверка подписанного APK — **PASS**.
- Это **не** физическая приёмка: могут остаться щелчки, небольшая тишина вместо crossfade, аппаратная задержка эффекта, независимые события маршрута/сетевых запросов. Если на HONOR не проходит — записать *новую* причину и сделать отдельную воспроизводимую красную проверку перед изменением.
- Не утверждать, что «все 4 ошибки доказанно исчезли», пока пользователь не проведёт реальный тест.

## Политика следующего чата

1. Сверить HEAD `feature/android-0348-audio-ownership-stabilization`, прочитать `docs/android/NEXT-CHAT.md` и `RELEASE-0.3.48.json`.
2. Убедиться, что реальная установка — `0.3.48/versionCode49` поверх старой (подпись SHA-256 сертификата в квитанции). Ничего не сбрасывать и не просить удалять приложение.
3. Один объединённый тест владельца: две-три естественные смены песни, пауза короткая и >1с, seek во время паузы, конец трека, Bluetooth/динамик если удобно. Получить один combined journal.
4. Анализировать только запуск версии 0.3.48 в журнале, а не два старых запуска. Не объявлять reconnect по одному HTTP 200 или смене трека; отличать `media3_connected`, `replacement_recovery`, `source_boundary` и эффект.
5. При провале не менять задержку вслепую — сначала воспроизвести точную последовательность и добавить тест, затем **весь** регрессионный набор; новый APK только одним комплектом.
6. Не трогать стабильную компьютерную 0.4.65, сервер, CMS и таблицу каталога. Android-ветка изолирована.
