# CELIKOM Android — ПЕРЕДАЧА НОВОМУ ЧАТУ · 30.10.2026

> **ОБНОВЛЕНИЕ 30.10.2026:** Этот документ описывает исходный handoff, до реализации. Код новой архитектуры уже начали внедрять. Сначала прочитайте [UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md](UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md). Последний проверенный код: `d1034816796d6fc1a421d559304f5c5218317c66`, CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/41027989995. Gate A частично реализован; Gate B — только наблюдение; **подписанный APK не создан**. Сведения ниже об отсутствии новых изменений — историческое состояние на момент передачи.

> **АКТУАЛЬНЫЙ ПРИОРИТЕТ: ЭТОТ ДОКУМЕНТ + [UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md](UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md).** Старые handoff 29 октября, README и NEXT-CHAT описывают более раннее состояние (0.3.52 unsigned / signing key missing) и являются историей. Ключ позже восстановлен, 0.3.52–0.3.54 подписаны.

## Главная задача и пределы

Продолжить самостоятельную разработку CELIKOM **только для Android телефона**. Избавиться от слышимого переключения оригинала Яндекс Музыки на замену в начале каждой песни, провалов при seek, конкурирующих pause/buffering/seek callbacks, сохранив все исправления 0.3.54. НЕ переключаться на desktop, не менять `feature/api-range`, extension, рекламу, API, сайт, БД, каталог, подписки/авторизацию, общие CI и secrets. Ветка desktop 0.4.65 — неприкосновенна. Изменять только `android/native-companion/**`, `docs/android/**`, при необходимости ровно Android CI.

### Почему нельзя делать две функции независимо

Пользователь помнит предыдущие регрессии, вызванные раздельными правками подготовки следующей песни и перемотки; оба пути конкурировали за один MediaPlayer и source effect. Его предупреждение **главное архитектурное требование**. В текущем `ReplacementEngine.java` много отдельных transition/seek/fading/pause flags и handler tasks, хотя `AudioOwnership`, `ClockSupervisor`, `SourceEventArbiter` уже введены. Следующий разработчик должен построить *одно событие / одно решение / один owner*, а не ещё два модуля-переходника. Ускорение старта только после защиты ownership и доказательства источника данных о следующем треке. См. план.

## GitHub/checkpoints

- Repository: https://github.com/manufact-test/nomusic
- **Новая ветка для продолжения (документы, код baseline):** `feature/android-unified-preparation-seek-gate`. Проверить её HEAD (docs commit меняет SHA). Исходный код создан от `8128307d0daf95f3386b85791db5347e3ec56357`.
- **Историческая активная ветка Android:** `feature/android-0348-audio-ownership-stabilization`, SHA `8128307d0daf95f3386b85791db5347e3ec56357` до нового чата, PR #22 OPEN/DRAFT, Issue #20 OPEN. НЕ переносить неготовое в desktop. 
- **CI на том коде:** https://github.com/manufact-test/nomusic/actions/runs/41019895272 SUCCESS. Это host/API36/DEX, НЕ реальный звук на HONOR. Документальная ветка сама по себе не проходила новый CI.
- **Rollback Git ref:** `backup/android-0354-buffering-repair-green-20261030` at `8128307...`. Более ранние `backup/android-0354-user-test-before-duration-fix-20261030`, `backup/android-0353-user-test-before-duration-fix-20261030`, `backup/android-0352-accepted-test-before-0353-20261029` могут существовать; проверять, не угадывать.
- **Первое действие:** проверить HEAD новой ветки, прочитать этот handoff и план, затем `docs/android/AUDIO-LIFECYCLE-DESIGN-2026-10-29.md`, `docs/android/DEVICE-0353-ROOT-CAUSE-2026-10-30.md`, `android/native-companion/README.md`, `build-inputs.json`, классы/тесты и user log. Не переписывать desktop или сервер.

## Что уже сделано/почему жалобы остались

- 0.3.52 большая перестройка ownership/clock/event arbiter, оригинал/замена эксклюзивны по командам; но реальный HONOR всё ещё слышит задержку.
- 0.3.53 ввёл двухступенчатый fade 100ms original then ~200ms replacement; небесшовность старта и seek не исправил, duration gate был противоречивым.
- 0.3.54 исправлена проверка измеренной длительности для строго подтверждённой версии (до 1500ms codec/outro tail); теперь "Крылья", "Биг сити лайф", "Метамир" проходят, не ослаблять идентификацию для неподтверждённых версий.
- 0.3.54 **AUDIOFIX TEST**, билд на текущем baseline `8128307...`: Media3 `STATE_BUFFERING` с `playWhenReady=true` не путается с ручной паузой, короткий buffer удерживает decoder, отложенная prealign перемотка в паузе убрана, unconfirmed outgoing reset не освобождает decoder, public config request 15s cache без пропуска per-track resolve. GitHub green, подписанный APK уже установлен пользователем.
- **Но** начало всё ещё через ~1.05–1.72s после появления песни (8 примеров среднее ~1.31s); 26 commanded_silence эпизодов в последнем 132.389s тесте, главные проблемы — seek and decoder hang/recovery; не выдавать очередные "поправленные 100ms" как решение.

## Evidence — последнее диагностика

Приватные, доступные новому чату резервные материалы в ChatGPT Library:
- журнал: `/CELIKOM/Android/Diagnostics/CELIKOM-combined-20261030-105118.txt` (verified private upload 30.10.2026);
- **восстановленный оригинальный signing backup**: `/CELIKOM/Android/Private/CELIKOM-Original-Android-Signing-RECOVERED-20261029.zip` (verified private upload 30.10.2026; contains sensitive private keystore and config, NEVER include in repo/CI/output; access only as needed to sign).


Uploaded private file in previous conversation: `/mnt/data/CELIKOM-combined-20261030-105118.txt` (new chat runtime may not preserve exact path; search conversation / Library using Files). Contains **3 RUNS**:
- 0.3.53 @ 2026-10-30T00:28:35+03
- 0.3.54 pre-AUDIOFIX @ 2026-10-30T01:14:46+03
- **0.3.54 AUDIOFIX** @ 2026-10-30T10:49:05+03, duration 132389ms; HONOR NTH-NX9 / Android13, Yandex 2026.09.5 #167.1gpr.
Last only: `replacement_source_buffer`=26, `replacement_source_buffer_resumed`=19, `replacement_outgoing_candidate`=7, old `replacement_outgoing_reset`=0, `audio_command_anomaly`=26, `replacement_duration_mismatch`=0, `replacement_bounded_tail_accepted`=3, `replacement_transition_complete`=28. These are software traces, NOT acoustic proof. Do not commit raw TXT to Git.

## Source tree: exact location

`android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/`
- `ReplacementEngine.java`: asynchronous resolve/prepare, pending stream/seek/pause/fade/handover, largest conflict zone.
- `AudioOwnership.java`: authority for decoder commands, effect gain, epoch/lease, exclusive-volume guard.
- `ClockSupervisor.java`: only drift policy (don't reintroduce DriftGuard/SyncPolicy parallel decision).
- `SourceEventArbiter.java` + `SourceTransitionGate.java`: reject stale Media3 events, confirm boundary.
- `ProbeService.java`: single main handler/Media3 events, collects source metadata, gives snapshots to engine.
- `PlaybackSource.java`: source playing/connected/buffering/wantsToPlay, source identity.
- `NativeApi.java`: config/resolve/authorized stream, never cache auth. `BufferedAudio.java`/`StreamingAudio.java`: bounded streamed file.
- `PlaybackDuration.java`: verified codec/outro policy. Other key classes `AudioContinuityMonitor.java`, `BufferRecoveryGate.java`, `TransitionMix.java`.
- Tests: `android/native-companion/tests/run_engine.py`, `check_audio_architecture.py`, `TestAudioCommandGateway.java`, `TestAudioOwnershipRegression.java`, `TestEngine.java`, `TestRealFailures.java`, `TestStreamingEngine.java`, `TestHandoverClock.java`, `TestCarRecovery.java`, `TestSourceEventArbiter.java`, `TestPhoneReplay.java`, `TestAudioLifecycle.java`, `TestLongRun.java` and others.
- Build: `android/native-companion/build_release.py`, `verify_release.py`, `release-spec.json`, `build-inputs.json`; Android-only workflow `.github/workflows/android-0348-validation.yml`.

## Signed backups and signing

- User-installed latest: `CELIKOM Android 0.3.54 AUDIOFIX`, package `pro.celikom.nativeprobe`, versionCode **55** (same as first 0.3.54 test), APK SHA256 `b29af425b630816b6b7161700c130b9a3824a4a82f229d206939bfcb00a153b7`. Private ChatGPT Library: `/CELIKOM/Android/Backups/CELIKOM-Android-0354-AUDIOFIX-DIRECT-20261030-B29AF425.apk`. Alternative zip `CELIKOM_Android_0354_AUDIOFIX_TEST_2026-10-30.zip`; previous 0.3.51, 0.3.52, 0.3.53, old 0.3.54 are there. Do not overwrite/lose.
- Original signing recovery ZIP in the past shared runtime: `/mnt/data/CELIKOM-Original-Android-Signing-RECOVERED-20261029(1).zip`, containing *private* `celikom-native-probe.p12` and `signing.json`. May NOT be automatically mounted in a new chat; retrieve privately if necessary. NEVER commit, send to GitHub, echo passwords or package in release. Cert SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Build JDK17, SDK API36+build tools36, Apktool2.11.1, exact 0.3.22 base (sha in `build-inputs.json`), pinned jars, source-matched DEX from successful CI. Require signed APK verify_release.py and original cert for any installable build. **No new APK at handoff**; do not need new versionCode until genuinely preparing next candidate; then increment above 55.
- User has repeatedly experienced red download UI errors from ChatGPT sandbox links; a Library-hosted **direct APK** worked. Never claim download works until user confirms. Do not give ZIP as the only install method.

## Continuation specification

1. Before coding, check code/branch and read `UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md`.
2. Do NOT build a standalone preloader and a standalone seek patch. Design one reducer/transaction contract integrated into existing `AudioOwnership` and `SourceEventArbiter`.
3. **Gate A:** fail closed on audio-owner mutation by background prepare; tickets/epoch for callbacks; add RED tests to current engine for interleavings; unify state transitions. Move carefully without breaking 0.3.54.
4. **Gate B:** verify Media3 read-only lookahead capability; if not trustworthy, avoid speculative "next" and optimize existing per-track stream.
5. **Gate C/D:** only then data-only prefetch and seek/handover integrated through single owner, preserving fresh authorization and exclusive output. Include negative tests for logout, rapid skips, repeat, route change, waiting downloader, wrong edition.
6. Full CI + fail-on-diff signed DEX verification; do not merge PR or send user APK just because host tests green. Report metrics and honest physical limits.
7. Complete a substantial coherent code batch before asking owner to test again. User prefers no endless micro-builds/no extra app or staging setup. Keep regular backup branches/checkpoints and only Android scope.

### Handoff end state

**Historical state only (before 30.10 development):** No audio code had been added at the original handoff. **Current code and CI checkpoints are documented in [UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md](UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md).** Old working branch and installed signed AUDIOFIX remain intact. New chat can begin implementation without the user repeating history.
