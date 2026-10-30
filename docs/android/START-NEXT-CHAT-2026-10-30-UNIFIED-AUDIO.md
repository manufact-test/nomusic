# Сообщение для первого обращения к новому чату — CELIKOM Android

[$github](app://connector_76869538009648d5b282a4bb21c3d157)

Привет! Продолжаем самостоятельную разработку **CELIKOM только для Android-телефона**. Ты новый главный разработчик Android-модуля в этом чате. **НЕЛЬЗЯ** трогать компьютерное расширение, desktop-ветку `feature/api-range`, Ad Protection, сайт, сервер, базу, каталог, API, подписки, общие конфигурации и секреты.

**Репозиторий:** https://github.com/manufact-test/nomusic

**Новая рабочая ветка:** `feature/android-unified-preparation-seek-gate` (сначала проверь текущий HEAD, потому что документальный checkpoint увеличивает SHA).

**Техническая исходная точка, прошедшая полный CI:** `8128307d0daf95f3386b85791db5347e3ec56357`; GitHub Actions SUCCESS https://github.com/manufact-test/nomusic/actions/runs/41019895272. Эта SHA — код подписанного 0.3.54 AUDIOFIX. Новая ветка создана от неё; на момент передачи в новой ветке сохранялись только документы, **новой аудиореализации и нового APK ещё нет**.

**Старый Android workstream:** `feature/android-0348-audio-ownership-stabilization`, PR #22 OPEN/DRAFT, issue #20 OPEN. Резервная ветка `backup/android-0354-buffering-repair-green-20261030`. Не мержить напрямую в desktop.

### ОБЯЗАТЕЛЬНО ЧИТАЙ ПЕРВЫМИ

1. `docs/android/HANDOFF-2026-10-30-UNIFIED-AUDIO.md` — подробный текущий статус, все пути, диагностика, подписанные APK и границы проекта.
2. `docs/android/UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md` — **главный новый архитектурный контракт** и последовательность работы.
3. `docs/android/NEXT-CHAT.md` — смотри верхний актуальный указатель, нижние разделы исторические.
4. `docs/android/AUDIO-LIFECYCLE-DESIGN-2026-10-29.md`, `docs/android/REGRESSION-GATES-2026-10-29.md`, `docs/android/DEVICE-0353-ROOT-CAUSE-2026-10-30.md`.
5. `android/native-companion/README.md`, `android/native-companion/build-inputs.json`, `release-spec.json`; затем код Android и тесты.

### ПОЧЕМУ МЫ МЕНЯЕМ ПОДХОД

Мы долго исправляли Android-воспроизведение Яндекс Музыки маленькими заплатками. У нас появлялись конфликты: подготовка к следующей песне вмешивалась в seek, pause/буферизация запускали параллельные состояния, отложенные callback'и управляли уже неактуальным декодером. Большая переработка 0.3.52 ввела `AudioOwnership`, `ClockSupervisor`, `SourceEventArbiter`, однако в `ReplacementEngine` всё ещё остались конкурирующие флаги и асинхронные переходы.

**Я, пользователь, специально предупредил предыдущий чат: мы уже пробовали отдельно чинить подготовку и перемотку, и эти функции снова начали конфликтовать. НЕ ПОВТОРЯЙ.** Наша новая технология должна быть **единым управляющим процессом воспроизведения**, с одним владельцем аудио и одним согласованным порядком событий, а не двумя параллельными подсистемами.

Подготовка следующей песни может только заранее читать/скачивать безопасные данные; она НЕ должна сама запускать второй плеер, делать seek, менять громкость оригинала или захватывать аудио. Подмена и seek подчиняются одному audio owner с защитой по ключу трека и epoch. Подтверждённая смена трека отменяет все старые операции; seek имеет приоритет перед устаревшей подготовкой; реальные паузы и буферизация различаются. Никаких слышимых одновременно оригинала и замены.

Если Media3 Яндекс Музыки не позволяет **надёжно** узнать точную следующую песню заранее, не выдумывай предзагрузку по порядковому номеру; сначала докажи доступность read-only данных, иначе оптимизируй начало текущей песни.

### ЧТО ПОЛУЧИЛОСЬ К СЕЙЧАС

- 0.3.52 — существенный Android audio refactor, но проблемы слухового переключения остались.
- 0.3.53 — двухэтапное приглушение оригинала 100 мс и нарастание замены 200 мс. Старая проблема задержки запуска не устранена.
- 0.3.54 — исправление ложных отказов из-за разницы длительности до 1.5 с у точно подтверждённых треков. «Крылья», «Биг сити лайф», «Метамир» начали приниматься.
- **0.3.54 AUDIOFIX — последний проверенный на телефоне кандидат:** `playWhenReady=true` + `STATE_BUFFERING` отделено от ручной паузы; краткий буфер сохраняет декодер; убрана автоматическая перемотка во время паузы; неподтверждённый сброс старой песни не выбрасывает декодер; кеш публичной config 15 секунд без кеширования разрешения на музыку. Код прошёл CI и реально установлен на HONOR, но НЕ принят как стабильное звучание.

Последний пользовательский журнал `CELIKOM-combined-20261030-105118.txt`. В нём три run: 0.3.53 в 00:28:35, старая 0.3.54 в 01:14:46 и **AUDIOFIX 0.3.54 10:49:05 30 октября 2026 (+03)**. Последний run HONOR NTH-NX9 / Android13 / Yandex 2026.09.5: 132.389 секунды, 26 событий `replacement_source_buffer`, 19 `replacement_source_buffer_resumed`, 7 `replacement_outgoing_candidate`, 0 старых `replacement_outgoing_reset`, 26 `audio_command_anomaly`, 0 `replacement_duration_mismatch`. Задержка от обнаружения трека до завершения подмены ~1.05–1.72 с (средняя по восьми примерам ~1.31 с). **Это измерения программных событий, не запись физического звучания**. Пользователь всё ещё слышит начало оригинала, резкие переключения, заикания/провалы на перемотках. Не объявляй проблему решённой.

### ГДЕ КОД И ТЕСТЫ

`android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/`:
- `ReplacementEngine.java` — основная логика и конфликтующие переходы;
- `AudioOwnership.java` — эксклюзивный разрешающий шлюз для Android MediaPlayer/DSP;
- `ClockSupervisor.java` — единственный контроллер дрейфа;
- `SourceEventArbiter.java`, `SourceTransitionGate.java`, `ProbeService.java` — Media3 события и границы треков;
- `PlaybackSource.java` — состояние playing/intent/buffering;
- `NativeApi.java`, `BufferedAudio.java`, `StreamingAudio.java`, `PlaybackDuration.java` — API, подготовка и длительность.

`android/native-companion/tests/`: `run_engine.py`, `check_audio_architecture.py`, `TestAudioOwnershipRegression.java`, `TestAudioCommandGateway.java`, `TestEngine.java`, `TestStreamingEngine.java`, `TestHandoverClock.java`, `TestRealFailures.java`, `TestCarRecovery.java`, `TestAudioLifecycle.java`, `TestSourceEventArbiter.java`, `TestPhoneReplay.java`. Не отключай старые регрессии ради зелёного результата. Android CI — `.github/workflows/android-0348-validation.yml`.

### ПОДПИСЬ, APK И БЭКАПЫ

Последний установленный пользователем подписанный APK **0.3.54 AUDIOFIX**: package `pro.celikom.nativeprobe`, versionCode 55. SHA256 APK `b29af425b630816b6b7161700c130b9a3824a4a82f229d206939bfcb00a153b7`; приватная ChatGPT Library `/CELIKOM/Android/Backups/CELIKOM-Android-0354-AUDIOFIX-DIRECT-20261030-B29AF425.apk`. Там же бэкапы предыдущих подписанных 0.3.51–0.3.54. Оригинальный сертификат SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. В предыдущем приватном окружении есть recovery ZIP `/mnt/data/CELIKOM-Original-Android-Signing-RECOVERED-20261029(1).zip` с keystore и `signing.json`; новый чат может не увидеть этот путь — искать приватные файлы, НЕ придумывать и НЕ загружать ключи в GitHub. Никогда не публиковать пароли/keystore.

Для сборки нужны JDK17, SDK API36/build-tools36, Apktool 2.11.1, точный base 0.3.22 APK и зависимости из `build-inputs.json`. APK должен совпадать с CI по DEX, пройти `verify_release.py` и иметь оригинальную подпись. Новый candidate увеличивает versionCode выше 55. Не выпускать новый APK после мелких косметических изменений.

### ТВОЯ ЗАДАЧА

Начни с чтения документов и аудита текущего Android. Сделай большой логически цельный этап: контракт общего owner/reducer, запрет фоновой подготовке вмешиваться в PLAYING/PAUSED/SEEKING, ticket/epoch для callback'ов, жёсткие тесты interleaving (prepare+seek, prepare+pause, буферизация, boundary, logout, route loss, быстрые 10 переключений). Затем выясни реальную возможность read-only lookahead следующего трека. Только при надёжных данных добавляй **data-only prefetch**, интегрированный в тот же owner. При невозможности lookahead честно оптимизируй текущую подготовку.

Сначала сохранить контрольную точку, потом изменения и реальные CI-тесты. Не затрагивать компьютерную версию/сервер. Не заставлять меня ставить APK после каждой мелкой правки. Не выдавать красивую статистику как доказательство аппаратной бесшовности. Когда закончен один полноценный проверенный этап — доложи, что сделано, что осталось и какие точно тесты зелёные. Я хочу избавиться от заиканий и слышимой смены оригинала на замену, **без нового конфликта между подготовкой и перемоткой**.
