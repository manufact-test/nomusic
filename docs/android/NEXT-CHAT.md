## НОВАЯ ПРАКТИЧЕСКАЯ ВЕТКА ОТ TEST.50 — GREEN (10.11.2026)

- После успешного OWN Android13 MediaPlayer / 12-round race [#42837053639](https://github.com/manufact-test/nomusic/actions/runs/42837053639) подтверждено: на x86_64 Android **только собственные WAV**, не реальная native-Yandex подмена. Выбранный Yandex `Lemb` runtime не установлен.
- По проверенным старым CI настоящий signed Yandex #170gpr запускается в **Android 11 x86/ARM translation** (baseline [#42621833205](https://github.com/manufact-test/nomusic/actions/runs/42621833205)), но **анонимного живого playback witness нет**. ARM64 macOS эмулятор дважды не загрузился [#42672246229](https://github.com/manufact-test/nomusic/actions/runs/42672246229), hosted ARM64 Linux KVM **нет** [#42792130918](https://github.com/manufact-test/nomusic/actions/runs/42792130918); public MediaSession bind [#42785272172](https://github.com/manufact-test/nomusic/actions/runs/42785272172) **rejected**. Не повторять те же тупиковые CI.
- Вместо новых DEX циклов открыт отдельный **поведенческий Android Test.50 эксперимент**: `experiment/android-test50-repeated-seek-failopen-20261110`, green SHA `7440d70be0e0584fde12bff2c1fc43725717475e`, backup `backup/android-test50-repeated-seek-failopen-ci-green-20261110`; [CI #42843272827 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42843272827).
- Полный документ в другой ветке: [ANDROID-TEST50-REPEATED-SEEK-FAILOPEN-EXPERIMENT-2026-11-10.md](https://github.com/manufact-test/nomusic/blob/experiment/android-test50-repeated-seek-failopen-20261110/docs/android/ANDROID-TEST50-REPEATED-SEEK-FAILOPEN-EXPERIMENT-2026-11-10.md).
- После **двух неуспешных seek за 60 с на одной песне** Test.50-эксперимент откатывает в оригинал до следующего трека; одна неудача допускает прежний retry. Полный Android CI и защитный hash старого seek/ACK прошли. **Не выдан APK и не подтверждён звук на HONOR**, эталон Test.50 `backup/android-test50-exact-source-owner-accepted-20261106` @ `5d737d2` неизменен.
- Основные Windows, browser, production/API, сервер, DRM/подписи, пользовательский HONOR и установленный официальный Яндекс не трогались. Продолжение без отдельного ARM-хоста — на экспериментальной Test.50 ветке, не в signed-Dex mayflow.

---

## НОВЕЙШАЯ CI GREEN — Android 13 real MediaPlayer rapid Start/Stop/Next race PASS (10.11.2026)

- **Точный код:** `50735e6d56481ea0ce3da8fdcb03589cad90608c`; **неизменяемый rollback:** `backup/android-own-api33-rapid-reload-race-pass-20261110`. **Читать первым:** `docs/android/ANDROID-OWN-API33-RAPID-RELOAD-RACE-PASS-2026-11-10.md`.
- **Реальный Android 13 Google APIs x86_64 emulator / OWN-WAV only / noaudio**: обычный source reload с сохранением Pause/Seek/Next **PASS** и **новый быстрый стресс** 12 round / 48 media-player creates / max1 concurrent / 47 release, 12 B prepared, 6 Paused+Seek **PASS**. CI зафиксировал **`RESULT=PASS CODE=OWN_DECODER_LIFECYCLE` И `RESULT=PASS CODE=OWN_ASYNC_RACE_PASS`** в одном run [#42837053639 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837053639).
- Починен настоящий баг OWN UI: второй Start/Stop **до `onPrepared`** сбрасывал pending restore position в 0; теперь `restoreSeekMs>0` действует с начала prepareAsync. 36 искусственно вставленных stale-tickets отсекаются generation guard, но **реальное число framework late callbacks не измерено** — не путать.
- **Android ARMv7 host [#42837003150 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003150), own scoped module [#42837003307 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003307), native research [#42837003096 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42837003096)** на соседнем SHA `31c34b23`; после него менялась **только workflow safety-check** (проверено compare). Оригинальный Yandex/owner Test.50/Windows/API/production НЕ менялся.
- **Android Yandex runtime selected Lemb / trackId+edition+generation → real decoder preprepare НЕ ДОКАЗАН**. Обычные Android `AudioPlaybackCallback`/MediaSession уведомления не открывают объект DataSource чужого плеера. Android CELIKOM source swap по-прежнему **NO-GO**, не выдавать собственный тестовый APK за готовую подмену.

---

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ ANDROID RUNTIME PASS — API33 OWN MediaPlayer, source reload/Seek/Pause/Next (10.11.2026)

- **CI GREEN код:** `bb26aca9652850c69fbd0896a26bec22601826b0`, **точный immutable backup:** `backup/android-own-api33-real-mediaplayer-source-reload-pass-20261110`, **главный документ:** `docs/android/ANDROID-OWN-API33-MEDIAPLAYER-RUNTIME-PASS-2026-11-10.md`.
- **Впервые реальные Android 13 native MediaPlayer callbacks в эмуляторе, не JVM модель:** собственный WAV A 440 Hz → Seek 2.2 с → Pause → SAME-TRACK Start alternative A 660 Hz с сохранением Pause и позиции → Resume → Stop, original A 440 Hz с сохранением Playing/позиции → Next B original 330 Hz. Источник выбирается через тот же `OwnSameTrackReloadPlan.decide`; старый плеер сначала release, новый один. На реальном Android CI `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE`.
- **[Android 13 OWN runtime #42835181030 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181030)**; на том же SHA [OWN ARMv7 host+50 020 tests #42835181029 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181029), [scoped own module #42835181289 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181289), [native-Yandex research build #42835181034 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181034).
- **Жёсткая граница:** Android emulator x86_64 использует только OWN-пакет, WAV и `-noaudio`; не доказывает слышимый звук, Android-Яндекс, выбранный Lemb из 8 реализаций, trackId+edition+generation или декодер Яндекса. Реальная Android CELIKOM-подмена всё ещё **NO-GO**. Original/Test.50/HONOR/Windows/API/production не трогать.

---

## ПРЕДЫДУЩАЯ CI GREEN — Windows 0.24.9 audio lessons → OWN Android same-track reload (10.11.2026)

- **Проверенный code SHA:** `a7f83f0ab836bbeeb12538c6a389c9569d326610`; **замороженный rollback:** `backup/android-windows-w60-owned-reload-armv7-arm64-ci-green-20261110`; главный документ: `docs/android/ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md`.
- **Наконец сопоставили реальные исходники Windows:** `w22/native-resource-adapter.mjs` + `w60/current-source-refresh.mjs` и свежие W57/W60/W61/W62/W63. Owner audio/Pause/Seek/Next/MyWave/Start/Stop **PASS на Windows 0.24.9**, W63 (0.24.11) пока пользовательский UI-кандидат. Windows работает через проверенный `getFileInfo` и Electron `7123.VE.reloadEntity("QUALITY_CHANGE")`; Android **не имеет доказанного идентичного API**.
- Из принципов Windows портирован **реально собираемый ARMv7 OWN-only Android стенд:** `OwnSameTrackReloadPlan.java`, новые Start/Stop в `AudioSmokeScreen` для той же 8-секундной искусственной песни A. **Только при смене источника** релиз единственного `MediaPlayer` и создание нового; position/paused восстанавливаются после `prepareAsync→seekTo`, быстрые повторные нажатия защищены revision, Next B остаётся оригиналом. **Не Яндекс!**
- **CI SUCCESS:** [OWN ARMv7 Android build + safety + 50 020 assertions #42830966825](https://github.com/manufact-test/nomusic/actions/runs/42830966825); [ARM64 Linux JVM test #42831135970](https://github.com/manufact-test/nomusic/actions/runs/42831135970). Нет физического Android-аудио теста и live Yandex decoder evidence, оригинал не меняли.
- **Windows W56 query guard не переносить на Android:** вызван конкретным Windows `DownloadInfoSource` append `?vsid`; подтверждения такого Android транспорта нет; `NativeGrantContract` правильно отклоняет неподписанные дополнения. Не копировать JS Electron reload, ключи/IV, DRM и URL в неподтверждённый Android путь.
- **Единственный главнейший blocker:** выбранный live `Lemb` receiver (из восьми вариантов) + тот же current `trackId/edition/generation` → истинный decoder preprepare. Без отдельного ARM Android test host нельзя обещать owner APK. Test.50/HONOR/Windows/production не трогались.

---

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — строгий source-instance fail-closed на ARM64 (10.11.2026)

- **Исходники и тесты SHA:** `59aa2d14bf32fd0f5eb553c09ec88738d84353a0`; **точный бэкап:** `backup/android-signed-source-instance-failclosed-arm64-ci-green-20261110`. **Главный отчёт:** `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- После предыдущего green `3aaab880` поймали дополнительную ошибку исследовательского допуска: после событий `OUT_OF_ORDER` более поздний чистый `open/read/close` мог снова дать `syntheticSequenceComplete=true`. Исправлено: **любое rejected-событие текущего поколения навсегда лишает его статуса complete**; stale-вызовы старых поколений новое не портят. Добавлены регрессии.
- **[Нативный ARM64 Linux JVM #42828086262 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42828086262)**: 44 480 OWN-ONLY assertions + 27 concurrency checks, 4 800 stale callbacks. **[Read-only Android module #42828086264 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42828086264)**. Signed original Lemb factory source census [#42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492).
- `NativeSourceInstanceFence` — чистая локальная Java-модель без подключения к `NativeHookEntry`. Нет live Android ARM runtime decoder proof, selected trackId/edition/generation / Lemb source match, Android аудиоподмена **НЕ** работает; HONOR/Test.50/Windows/production не трогали.

---

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ CI — Lemb source alternatives + exact source-instance generation fence (10.11.2026)

- **CI GREEN SHA:** `3aaab880fff4326b596f63a52a89a0f4d0085fef`; **точный бэкап:** `backup/android-signed-source-instance-arm64-lemb-ci-green-20261110`. **Читать первым:** `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- Подписанный original #170gpr: **8 concrete Lemb implementations**, 4 direct `Lemb.t/remove` callsites в `Lchg.t/remove`, `Lciv.e`, `Larv.g`. Даже доказанный ранее `Lero→Lwq7→Lmb4` может быть **не выбранным** источником.
- В factory `Lkvs.A` есть 4 условных типа `Lero/Lojz/Lalt/Lt6f`; в `Locv.i0` — `Lero/Lxq7/Lchg/Lt67`; в `Larv.g` — `Lero/Lt6f`. Показаны типы/ветвления, **не** значения URL/строк и не то, какая ветка сработала на устройстве.
- Добавлена **исключительно OWN-ONLY** `NativeSourceInstanceFence`: отдельный pure Java контракт точной `Object ==` идентичности selected/owner/reader/loader/task/DataSpec, preprepare-once, поколений Next/Radio, Stop, Seek/reopen, монотонных часов и fail-closed. **К `NativeHookEntry` НЕ подключена, аудио не трогает.**
- **CI:** [ARM64 Linux JVM #42826864698 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826864698) (44 478 deterministic + 27 concurrency assertions; 4 800 запоздавших вызовов), [Lemb factories #42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492), [signed Lemb callers #42826778879 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826778879), [Android native module #42827236060 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42827236060).
- **Android Yandex live source selected/predecoder доказательства нет; аудиоподмены нет.** ARM64 Linux — не Android runtime. Перед подключением нужны независимые trusted selected trackId+edition+generation + точно выбранный Lemb и actual decoder prepare в изолированной ARM Android среде. Test.50/HONOR/Windows/production не трогать.

---

## ПРЕДЫДУЩИЙ CI GREEN — точный Lero → Lwq7 task → Lmb4 DataSource.open/read/close (10.11.2026)

- **Проверенный SHA:** `f04745f7dcd4455996eadf56dc0be6c52a44c63f`; **замороженный откат:** `backup/android-signed-lero-lmb4-reader-case-ci-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-LERO-LMB4-EXECUTION-CHAIN-2026-11-10.md`. Signed original 5 APK/6 DEX/230533 bodies: `Lga4.c():Lha4` move-result **в том же basic block** записывается в `Lero.Lha4` и передаётся в `Lmb4.<init>` word1; конструктор кладёт его в точное поле `Lmb4:Lm48`; `Lmb4.a` читает тот же field-ref, cast `Lha4`, вызовы `b(La58)`×2/`read([BII)`/`close()`.
- В `Lero.t` **проверен actual DEX selector** и захват точного `Lero.this` в `Lwq7.<init>(I,Object)`. Mode **не** входит в 2 explicit packed-switch кейса `Lwq7.e` и выполняет **default fallthrough**, где `Lwq7` считывает то же captured field → `Lero.Lmb4` → `Lmb4.a`. У `Lero.t` есть `execute/get`, но это не runtime-аудио подтверждение.
- **CI SUCCESS:** [source read #42821377729](https://github.com/manufact-test/nomusic/actions/runs/42821377729), [selector/capture #42822722957](https://github.com/manufact-test/nomusic/actions/runs/42822722957), [exact source field #42823360505](https://github.com/manufact-test/nomusic/actions/runs/42823360505), [Android module #42823360398](https://github.com/manufact-test/nomusic/actions/runs/42823360398) 2/2.
- **Критическая граница:** точный выбранный `trackId+edition+generation` в живом ExoPlayer и `decoder PREPARE` всё ещё НЕ доказаны. Android replacement audio НЕ работает, runtime hooks/прошивки не тронуты. Следующий этап: отдельный пассивный ARM Android player/source witness. Не повторять x86 LSPatch; не трогать Test.50/HONOR/Windows/production.

---

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — URI-модель → Lcq7.i0 → Lga4/Lero/Lha4 → DataSource (10.11.2026)

- **Проверенный исходник:** `f327f5b9bcfee028e754f9a803f29ade347cb240`, **rollback:** `backup/android-signed-uri-locv-source-cfg-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-URI-TO-DATASOURCE-LIFECYCLE-EVIDENCE-2026-11-10.md`. В оригинальном подписанном six-DEX `Locv.i0` читает URI-подобные данные, `Lw4y.z` парсит scheme/host/path/query (значения не экспортированы); результат попадает в coroutine `Llky`, `Lfwm.M` возвращает `Ljgv`, который bounded CFG передаёт `Lcq7.i0` и `Lcq7.D`.
- У `Lcq7.i0` только 2 прямых вызывающих: `Lo4y.c` и `Locv.i0`. Результат — **обёртка**; реальный `Lga4` извлекается через `iget-object` с условным путём к `Lnro/Lero`. Предыдущий анализатор ошибочно сохранял taint обёртки при `iget-object`; ошибка в DEX 22c nibble-kill исправлена и протестирована.
- В том же signed DEX: `Lcq7.A` результат → точный primary `Le48`-slot `Lga4`; `Le48.a` результат `Lm48` → argument word 3 `Lha4.<init>`; `Lha4.f` вызывает `Lm48.b(La58)`, `Lha4.read` — `Lv38.read`. `Locv.t/remove` условно вызывают `Locv.i0`, но это **НЕ доказательство live decoder prepare**.
- **CI:** [source register #42819113120 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819113120), [actual i0 CFG #42819106641 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819106641), [taint fix #42817633107 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42817633107), [Android module #42819113420 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42819113420).
- **ANDROID audio PASS — НЕТ.** Нельзя считать модель соответствующей активному `trackId/edition/generation` или выбранному pre-prepare DataSource. Контракты замены не подключались, HONOR/Test.50/Windows/API/production не трогались.

---

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ КОД — obfuscated DataSource + два Le48-источника (10.11.2026)

- **CI GREEN SHA:** `6b5bfde53d81a29920f32a3c6b13b730b216e669`; **независимый откат:** `backup/android-signed-dual-source-dataspec-open-ci-green-20261110`.
- **Читать ПЕРВЫМ:** `docs/android/ANDROID-NATIVE-SIGNED-DATASPEC-OPEN-SOURCE-EVIDENCE-2026-11-10.md`. Установлен подписанный DEX DataSource-совместимый контракт Lm48(b(La58):J, getUri, close) + родитель Lv38(read([BII):I), 33 реализации; проверены реальные Lha4.open/read и Lz3f.a→Lm48.b(La58).
- Lga4.b/c используют secondary Le48, Lga4.d primary Le48; secondary в Lcq7.i0 = Lya4 → Lza4 (открытие/чтение выбрасывает исключение), **primary = Lcq7.A→Luiq** (ленивая фабрика Lm48). Оба источника передаются в Lha4, нельзя их путать. Общее соседство с ExoPlayer **не доказывает** текущий trackId/edition/generation и live decoder PREPARE.
- **CI:** [field2 #42813687276 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42813687276), [two slots #42814211492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814211492), [inherited API #42814967628 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814967628), [source/open #42815048696 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42815048696), [Android module #42815048701 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42815048701).
- **Нет Android audio PASS** и точной идентичности FileInfo→текущий экземпляр Lm48 перед prepare. Ничего в player/replacement не подключено; Test.50/HONOR/Windows/API/production не тронуты.

---

## PREVIOUS 2026-11-10: REAL SIGNED TYPED FileInfo LINEAGE / CI ALL GREEN

**Verified code:** `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`; **rollback:** `backup/android-signed-typed-dispatch-field-audit-ci-green-20261110`. [Полный отчёт](docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md). Результат: оригинальный signed six-DEX содержит Lhee.a→Lxa7, Lged.a unwrap Leed, Lfqr coroutine→Ldiv, Lygv.r(Ldiv)→Ljgv, её реальные потребители Lcq7/Lo4y/Llvc/Larv. Далее обфусцированные Lga4/Lkq7/Lnro могут взаимодействовать через Le48/Le93.

**ВАЖНОЕ исправление ложноположительного пути:** возможная Larv.g→Lero→Lga4.c→Le48.a→Ldl8.a→Lsu5.invoke→Lro7.y0 цепочка не доказывает audio source. У Le48.a 16 потенциальных реализаций; Lga4.c читает **Le48 field-2**, конструктор кладёт Lzcd в **field-1**, прямые записи field-2 имеют источники Lya4/Lkc6 и неизвестные, Lsu5.invoke имеет 721 opcode и switch (независимые сценарии). Все точные field refs проверены на 230 533 DEX телах. Изолированный ARM decoder PREPARE с текущим trackId+edition+generation НЕ подтверждён. Контракты замены не включать.

**Green CI:** [typed #42808158803](https://github.com/manufact-test/nomusic/actions/runs/42808158803), [post DTO #42808680756](https://github.com/manufact-test/nomusic/actions/runs/42808680756), [typed candidate #42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855), [dynamic #42809849405](https://github.com/manufact-test/nomusic/actions/runs/42809849405), [field #42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588), [Android hooklab #42810750850](https://github.com/manufact-test/nomusic/actions/runs/42810750850) 2/2. No owner APK, Windows, HONOR, Test.50, API or production touched.

---

## НОВЕЙШАЯ ПРОВЕРЕННАЯ ТОЧКА — signed register/CFG + coroutine (10.11.2026)

**Код CI GREEN:** 8b7bc64f89249e5434da739851bececce2adb121. **Бэкап:** backup/android-signed-register-cfg-ci-green-20261110. Исследование оригинального подписанного 6-DEX APK [#42806655214 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42806655214); сборка модуля и тесты [#42806655152 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42806655152). **Отчёт:** docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md.

**Реально найдено:** sw7.y0/z0 → объектный результат → Lxa7.<init> (bounded CFG); Lged.a → Lhee.a → Leed.a / Lta7.c / Lwa7.a, наблюдается возврат объекта. Lfed / Lgee / Lfqr — прямые coroutine invokeSuspend callers; в Lfqr есть collect/emit, но результат не доказан как payload интерфейса. Это только статическая may-flow DEX, НЕ активный decoder source и НЕ Android audio PASS. Android grant/Stop контракты не подключались к настоящему декодеру. Не трогать Test.50/HONOR/официальный Яндекс/Windows/API/production/DRM/подписи.

---

# 10.11.2026 — АВТОРИТЕТНАЯ НАВИГАЦИЯ / ПЕРЕДАЧА

**Начинать с** `docs/android/00-NATIVE-HANDOFF-NAVIGATION-2026-11-10.md` и **`docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md`**. Нижеследующие разделы этого файла являются историей и могут содержать устаревшие слова LATEST и SHA.

**Предыдущий проверенный код:** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`. **Два CI SUCCESS:** [signed six-DEX bridge scan #42804081064](https://github.com/manufact-test/nomusic/actions/runs/42804081064), [Android module build/tests #42804081053](https://github.com/manufact-test/nomusic/actions/runs/42804081053). Прямой caller `FileInfo→sw7.y0/z0`: `Lhee;->a`. Есть consumer `Lged;->a`, но связка к декодеру НЕ доказана. В оригинальном Android APK статически найдены по два вызывающих метода `MediaSession.setMetadata` и `setPlaybackState`, НЕТ подтверждения их live исполнения на пользовательском треке. Полный отчёт `docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md`.

**Windows W58:** пользователь ПОДТВЕРДИЛ аудиоподмену, Pause, Seek, Next, Previous, MyWave на Windows 0.24.7; в Android такой замены ещё НЕ БЫЛО. Уже перенесены только чистые модельные контракты для grant/Stop/Next; основной блокер — реальная Android decoder pre-prepare точка. Все рабочие версии/production не тронуты.

---

## NEW VERIFIED ANDROID CHECKPOINT — Windows W58 logic carried into source-only Android (2026-11-10)

**GitHub code SHA `e2a3c7c9577ea0a44966d1859296d77e0bae40d7`, CI [#42802150192 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42802150192), backup `backup/android-w58-grant-stop-next-ci-green-20261110`.** Owner Windows 0.24.7 genuinely PASSED audio + Pause/Seek/Next/MyWave. Windows Stop leaves *already delivered* signed audio playing in existing Yandex buffer, but no proven newly mapped track after OFF. Do NOT confuse this UX semantics with an active background hook.

Imported strict native approved signed grant shape/Track ID/expiry/entitlement checks and exact Stop/Next/re-enable epoch fencing into **`NativeGrantContract.java`** and **`NativeReplacementLifecycle.java`** with thousands of simulated races. Important: These are **NOT YET CONNECTED** to a verified real Android decoder; no Android audio replacement tested. The desktop `&celikom_native_query_guard=0` trick was NOT copied because Android URL transformation is unknown. No Windows/production/HONOR/Test.50 changes. Full report: `docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md`.

---

## VERIFIED GREEN CHECKPOINT 2026-11-10 / cross-platform Windows W57

- **Current Android native hooklab code SHA**: 4166b3f5f75df45b717308356995af22e1babc3c. [GitHub Actions CI #42800426147 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42800426147): full synthetic native source, event order and playback-state tests; Android libxposed module debug APK compiles and signature/module metadata validates. **No actual Android Yandex audio hook or source replacement proven**.
- New passive Android framework MediaSession.setPlaybackState observer tracks published enum and aggregate rapid Play/Pause/Buffering/Error reports. It reads **ONLY public enum** and cannot know track or user intent; multiple MediaSessions and normal user pause can look like quick state flips. Never connect to source replacement or decoder admission.
- Windows **0.24.7** owner-verified first real audible approved replacement inside real Yandex desktop. Native audio GET 206 (2), 403 (0). W56 root cause is **desktop-specific** vendor-added second ?vsid query corrupting signed source URL sid, fixed without HMAC bypass. Android has no verified equivalent, so DO NOT port the desktop URL padding blindly. Full review at docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md.
- **Rollback exact tested code:** backup/android-native-w57-review-playback-state-ci-success-20261110 (same SHA as above); pre-review baseline backup/android-native-before-windows-breakthrough-review-20261110 at 22d5ef25. Do not touch stable Android Test.50, owner's HONOR or Yandex, Windows 0.24.7 or production server. No APK suitable for user installation.

---
## 10.11.2026 IMPORTANT: verified CELIKOM Windows W57 audio breakthrough reviewed

**Windows 0.24.7 real replacement audio heard by owner, real HTTP206, 0 HTTP403.** Desktop Yandex DownloadInfoSource appended its own second ?vsid query to already signed audio URL and Windows team fixed the resultant session-field corruption with a narrow media-only trailing guard. This is DESKTOP Electron-specific; not evidence the native Android player also does that. See docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md.

Experimental native Android observer has new public playback state *aggregate-only* witness and synthetic JVM tests; no audio source swap and no actual patched native Yandex ARM run yet. Windows accepted baseline, Android Test.50 and HONOR unchanged.

---
## VERIFIED CHECKPOINT: 10.11.2026 — CI SUCCESS / NO NATIVE AUDIO CLAIM

**Latest verified CODE SHA:** `c5f76316f8a00e8b30c2cdae402fe0ec64dfeea2` on `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**[CI #42798290760 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42798290760):** pure-Java `NativeEventOrderProbeTest`, Python categorical/redaction tests and existing source/identity tests passed; Android observer APK built, metadata and signing structure verified. A previous CI #42798154589 failed only because its guard still expected an old log phrase; the guard was corrected and entire CI reran green.

**What changed from pre-experiment SHA `1ad5870f`:** pure-Java bounded FileInfo/metadata temporal classifier, native read-only hook observer integration, distinct FileInfo vs MediaSession counter categories, aggregate logs, updated safe emulator log parser and unit tests. There is no source mutation. Every real audio source comparison still requires a physically valid native-Yandex host; metadata temporal proximity is **not** trackId+edition proof. Do not use it in `NativePrePrepareAdmission`.

**Backups:** `backup/android-native-before-temporal-event-probe-20261110` at `1ad5870f`; `backup/android-native-temporal-event-probe-ci-passed-20261110` at `518dd07d`. Owner Test.50 baseline unchanged. No APK for manual Yandex testing, no production, no HONOR changes, no ChromaSync purchase.

---

## UPDATE 10.11.2026 — temporal diagnostic CI green + meaningful log summaries

**CI [#42797745570](https://github.com/manufact-test/nomusic/actions/runs/42797745570): SUCCESS 2/2**: >36k synthetic rapid Next/prefetch/privacy assertions, ARM source-only Xposed observer APK compiles and signature metadata passes. NO real Yandex host/runtime or source replacement.

Follow-up fixes: `NativeHookEntry.safeCount` now uses **metadata update** vs **FileInfo conversion** labels correctly, and every 20 metadata updates prints **only aggregate categories** (one nearby source, ambiguous multiple, none, clock discontinuity). `diagnose_emulator.py` recognizes distinct `CONVERSION_WITNESSED`, `METADATA_WITNESSED` and `TEMPORAL_ORDER_AGGREGATE` without exposing raw log lines. New categorical-parser unit tests; no song/account data processed. Snapshot backup `backup/android-native-temporal-event-probe-ci-passed-20261110` (code from green CI).

This does NOT prove the correct track / edition, is NOT plugged into `NativePrePrepareAdmission`, and cannot replace audio. Still requires a verified compatible native ARM Android host, not an x86 test or user HONOR installation.

---

## UPDATE 10.11.2026 — Native FileInfo / MediaSession temporal witness (NEWEST)

**Previous checkpoint and rollback:** `backup/android-native-before-temporal-event-probe-20261110` at `1ad5870f05105ffc5f9a105a052aca211ebaa6a7`.

Implemented `NativeEventOrderProbe.java`: a bounded, pure-Java diagnostic, now connected to the existing read-only FileInfo converter hooks (modern and legacy) and platform `MediaSession.setMetadata` observer in `NativeHookEntry`. Every method proceeds unmodified. Classifier records only monotonic event ordering, not absolute timestamps, IDs, editions, URLs, source responses, accounts or metadata values.

Diagnostic categories: one nearby FileInfo (temporal coincidence only), multiple nearby FileInfo (ambiguity/prefetch), metadata without recent FileInfo, clock discontinuity. Source event queue saturates at 2 and is consumed once for each metadata callback. The 12-second window is a provisional upper diagnostic bound, NOT a performance benchmark. `SINGLE_RECENT_FILEINFO_TEMPORAL_ONLY` is explicitly NOT a verified track-to-source match and may never authorize replacement. `NativePrePrepareAdmission` remains disconnected from real native decoder.

`NativeEventOrderProbeTest.java` exercises duplicate metadata, 12,000 Next/radio bursts, 20,000 prefetch events, expiry and clock reversal. Hooklab CI compiles/runs it as well as the Android libxposed module build. No user APK yet: actual runtime Yandex hook and native audio replacement still UNVERIFIED. Owner HONOR, stable Test.50, server and production untouched. ChromaSync paid/manual patcher rejected, no outreach.

---

## UPDATE: open-source native playback event evidence (10.11.2026)

Owner personally confirmed ChromaSync Android requires payment and manual patcher; **do not ask for it**, do not claim it free. No candidate outside CELIKOM was installed or paid for.

Checked actual public code, **not marketing alone**:
- [windyx0/YaMusicLsposed](https://github.com/windyx0/YaMusicLsposed/blob/main/app/src/main/java/io/github/windyx0/yamusiclsposed/MainHook.kt) (MIT): hooks Android framework `android.media.session.MediaSession.setMetadata` from within Yandex process; its sample reads/logs metadata, **we intentionally DO NOT**.
- [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) (source available): modern libxposed `onPackageReady` with the Yandex host classloader to hook native UI. No audio source swap.
- [errorman-awful/YMDownloaderXposed](https://github.com/errorman-awful/YMDownloaderXposed): public GitHub repository has README/demo, **no Android source**, not a reusable implementation.
- ChromaSync Android still has only README publicly; exact paywalled module source unavailable.

**Implemented in our native FileInfo module:** passive, version-locked `MediaSession.setMetadata` observer with only throttled integer counter and immutable original call path. Does not inspect MediaMetadata fields, track IDs, titles, URLs, queues, accounts or audio. It can later establish whether a native Android host process emits media metadata changes, *independently* of our already present FileInfo converter counters. A media session event DOES NOT confirm trackId+edition+generation identity or decoder source. Never use it to select alternate audio.

This is a concrete open-source-informed engineering improvement, not a full working native source replacement; must verify module build CI separately and real Yandex runtime only on suitable isolated ARM hardware. Primary HONOR, Test.50, other branches, Windows, extension, server/DB/production unchanged. Backup `backup/android-native-before-open-source-metadata-20261110` before these changes.

---

## UPDATE 10.11.2026 — signed native ExoPlayer implementor truth (LATEST)

**Verified code commit:** `fcd7550b86ee93082ff3a8b119e38b29d02482d8`. **Rollback backup:** `backup/android-native-real-media-implementation-evidence-20261110`.

- [Native original media engine CI #42791262439](https://github.com/manufact-test/nomusic/actions/runs/42791262439) **SUCCESS**: standard class `ExoPlayerImpl` absent, `ExoPlayer` interface defined.
- [Exact DEX type hierarchy #42791641169](https://github.com/manufact-test/nomusic/actions/runs/42791641169) **SUCCESS**: 4 obfuscated concrete implementors `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`, not necessarily player/decoder for current audio.
- [Inherited prepare body scan #42791829407](https://github.com/manufact-test/nomusic/actions/runs/42791829407) **SUCCESS**: no `prepare()V` bodies in those classes or their scanned parent chains. **Do not blindly hook named `ExoPlayerImpl.prepare`**.
- [Existing read-only hooklab #42791829435](https://github.com/manufact-test/nomusic/actions/runs/42791829435) **SUCCESS** module build/synthetic only.
- [Native AArch64 Linux GitHub runner #42792130918](https://github.com/manufact-test/nomusic/actions/runs/42792130918) **SUCCESS probe** but `/dev/kvm` unavailable; **not** usable native ARM Android guest.

Full bounded evidence `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md`. All code only on native hooklab branch. No real Yandex source/decoder/runtime hook proven; no Android CELIKOM APK to install. NO Yandex outreach. Primary device/Test.50 untouched. Next requirement remains a safe real native ARM Android test host, then trackId+edition+generation→decoder pre-prepare witness. Do not repeat stale x86/AМetrica experiments.

---

# CELIKOM Android — НАЧНИ ЗДЕСЬ (10.11.2026, проверенный текущий статус)

**GitHub:** `manufact-test/nomusic`.
**Рабочая ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**Кодовый HEAD, CI SUCCESS:** `18e0d1126187a2c2a26eeb7df7a25de935e19a54`.
**Точный бэкап исходников с рабочим кодом:** `backup/android-native-hook-classloader-verified-20261110`.
Любой более новый HEAD после этого — это документационные изменения; сначала проверить ref.

## 1. Что требует владелец. Не менять без его решения

**Один нативный проигрыватель Яндекс Музыки.** Пользователь входит только в самом Яндексе, пользуется родными плейлистами, радио, паузой, перемоткой и Next. CELIKOM выбирает подтверждённый альтернативный аудиоисточник только если он безопасно связывается с *текущими* trackId + edition + generation до decoder prepare. Иначе оригинал. Никакого второго MediaPlayer, WebView, отдельного fake player, чужих OAuth/Passport токенов или обхода DRM/Play Protect/подписей. Разрешённая модель установки в будущем может использовать **совместимую патченную нативную Яндекс Музыку, как ChromaSync**, но не поверх официальной подписи без осознанной смены установки.

**Яндексу ничего не отправлять**. Идею партнёрского письма владелец категорически отверг. Старый `ANDROID-NATIVE-YANDEX-PARTNER-INQUIRY-2026-11-10.md` — только архив, НЕ отправлять.

**Не трогать:** стабильную эталонную Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`; Яндекс Музыку и локальные загрузки владельца на HONOR 50; Windows, расширение, API, БД, production. Не предлагать владельцу тесты синтетического APK вместо проверки подмены в настоящем Яндексе.

## 2. Фактическая архитектура конкурента

[ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) заявляет native in-process модуль:
- **Без root:** совместимый оригинальный APK + патчер на устройстве + модуль; может требоваться удаление официального Яндекса из-за разных подписей.
- **С root:** LSPosed + модуль внутри Яндекса.
- В публичном Android-репозитории только README. Прямого исходного audio hook нет. Нельзя выдавать README за подтверждённую реализацию или обещать аналогичные результаты.
- Успех конкурента не делает безопасным наш параллельный клон с другим packageId. Именно этот путь уже потерпел неудачу.

Ещё один исходный пример [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) использует modern libxposed `onPackageReady` / classloader для **UI**, не для аудио. Это подтверждает полезность lifecycle-подхода, но не FileInfo->decoder.

## 3. Что реально подтверждено CELIKOM

- **Свой ARMv7 libxposed in-process witness на HONOR:** скрин владельца `Module hook armed=YES`, `onCreate intercepted=YES`, [CI 42643802887](https://github.com/manufact-test/nomusic/actions/runs/42643802887). Это ТОЛЬКО собственное приложение, не Яндекс.
- **Подписанный издателем Яндекс `2026.10.3 #170gpr`** (5 splits, 6 DEX) запускается в чистом изолированном Android 11 x86 с ARM translation. Из его DEX статически найдены `FileInfoApi/OldFileInfoApi @Query("trackId")` как param 0, `sw7.y0/z0(FileInfoDto,boolean):eed`. Реальная текущая edition+generation к конкретному decoder prepare ещё НЕ доказана.
- **Параллельный clone другого packageId**: MAIN `EXIT_SELF status 0`, вспомогательный `:AppMetrica` остаётся. Точная причина самозавершения не определена, **это не доказанный anti-tamper или несоответствие подписи**. См. `ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`.
- **Same-package LSPatch на x86/ARM-translation AVD**: и с модулем, и без модуля раньше падал в загрузчике `liblspatch.so` / `UnsatisfiedLinkError` ДО нашего hook; [42622523007](https://github.com/manufact-test/nomusic/actions/runs/42622523007), [42622723034](https://github.com/manufact-test/nomusic/actions/runs/42622723034). Это не проверка настоящего ARM. **Не повторять эти x86 тесты.** `.github/workflows/android-native-yandex-emulator.yml` переведён на manual-only.
- Уже реализованы *синтетические* `NativePrePrepareAdmission`, `NativeSourceGate`, `NativeTrackIdentityGate`: точные edition/generation/ready/expiry проверки. Ни один из них не включён в настоящий decoder.

## 4. Новый реальный код в этой сессии

`android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeHookEntry.java`:
- После exact-version проверки сохраняет только host Context, а при `onPackageReady` повторно пытается установить **read-only** хуки, если на `Application.attach` split-классы ещё не были готовы.
- Частично установленные хуки не дублируются: `modernHooked`, `legacyHooked`, `accessorHooked`.
- `HookSpec.findConversionPair(preferred, fallback)` требует **обе** точные сигнатуры `sw7.y0/z0` из **одного** classloader. Если preferred loader ещё не готов, пробует validated Context loader. Нет смешивания моделей из двух loader и нет fuzzy fallback.
- `HookSpecTest` проверяет точный version gate, пару, отказ при неподходящем loader и fallback.
- **[CI #42790028152](https://github.com/manufact-test/nomusic/actions/runs/42790028152) SUCCESS 2/2:** Java-policy и Android libxposed module APK build. Это НЕ тест реального Yandex hook. Исходники в `18e0d1126187a2c2a26eeb7df7a25de935e19a54`, отдельный бэкап `backup/android-native-hook-classloader-verified-20261110`.

**Изменений источника звука нет.** Модуль по-прежнему считает конвертации без чтения trackId, URL, ключей, токенов. НЕ продавать это владельцу как работающий Android CELIKOM.

## 5. Точный следующий рубеж

1. Нужна воспроизводимая **гостевая нативная ARM-среда** с совместимым same-package подготовленным Яндексом и без риска для основной установки; отдельный аппарат/разрешённая cloud ARM с допустимой установкой. Старые x86 AVД/clone нельзя выдавать за ARM proof.
2. Только после успешного native MAIN UI/login **в Яндексе**, Play Protect и hook witness: получить read-only runtime связь `current trackId + edition + generation -> FileInfoDto -> фактический source/decoder BEFORE prepare`. Не собирать пользовательские токены или чужие аудиопотоки.
3. Только после такого доказательства связывать `NativePrePrepareAdmission` с реальным нативным входом и затем тестировать «Раскол» `42884423`, «Дым» `39949113`, начало без «пшика», Next, radio, seek/pause. Никаких выдуманных CI green.

**Сейчас** без такого разрешённого native ARM runtime `NO-GO` для установки/теста владельцем; не требовать от него удалить официальный Яндекс и не запускать бесконечные emulator/DEX/AМetrica эксперименты. Если появится настоящий тестовый кандидат, обращаться к владельцу **один раз, только для реальной ручной проверки**, заранее называя риск удаления/подписей.

## 6. Исторические материалы

Старый разросшийся NEXT-CHAT с устаревшими и частично противоречивыми решениями сохранён **только для истории**: `docs/android/ARCHIVE-NEXT-CHAT-ACCUMULATED-20261110.md`.

Контекст: `docs/android/ANDROID-NATIVE-COMPETITOR-PATH-CORRECTION-2026-11-10.md`, `docs/android/ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md`, `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md`. Во всех спорных местах приоритет у настоящего документа и новых подтверждённых результатов CI, не у старых прогнозов.
