# CELIKOM Android — актуальная навигация к передаче (10.11.2026)

**Начальная точка:** `docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md` — готовый текст первого сообщения новому разработчику.

## НОВЕЙШИЙ ПРОВЕРЕННЫЙ CI — Lemb source alternatives + exact source-instance generation fence (10.11.2026)

- **CI GREEN SHA:** `3aaab880fff4326b596f63a52a89a0f4d0085fef`; **точный бэкап:** `backup/android-signed-source-instance-arm64-lemb-ci-green-20261110`. **Читать первым:** `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- Подписанный original #170gpr: **8 concrete Lemb implementations**, 4 direct `Lemb.t/remove` callsites в `Lchg.t/remove`, `Lciv.e`, `Larv.g`. Даже доказанный ранее `Lero→Lwq7→Lmb4` может быть **не выбранным** источником.
- В factory `Lkvs.A` есть 4 условных типа `Lero/Lojz/Lalt/Lt6f`; в `Locv.i0` — `Lero/Lxq7/Lchg/Lt67`; в `Larv.g` — `Lero/Lt6f`. Показаны типы/ветвления, **не** значения URL/строк и не то, какая ветка сработала на устройстве.
- Добавлена **исключительно OWN-ONLY** `NativeSourceInstanceFence`: отдельный pure Java контракт точной `Object ==` идентичности selected/owner/reader/loader/task/DataSpec, preprepare-once, поколений Next/Radio, Stop, Seek/reopen, монотонных часов и fail-closed. **К `NativeHookEntry` НЕ подключена, аудио не трогает.**
- **CI:** [ARM64 Linux JVM #42826864698 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826864698) (44 478 deterministic + 27 concurrency assertions; 4 800 запоздавших вызовов), [Lemb factories #42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492), [signed Lemb callers #42826778879 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826778879), [Android native module #42827236060 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42827236060).
- **Android Yandex live source selected/predecoder доказательства нет; аудиоподмены нет.** ARM64 Linux — не Android runtime. Перед подключением нужны независимые trusted selected trackId+edition+generation + точно выбранный Lemb и actual decoder prepare в изолированной ARM Android среде. Test.50/HONOR/Windows/production не трогать.

## ПРЕДЫДУЩИЙ CI GREEN — точный Lero → Lwq7 task → Lmb4 DataSource.open/read/close (10.11.2026)

- **Проверенный SHA:** `f04745f7dcd4455996eadf56dc0be6c52a44c63f`; **замороженный откат:** `backup/android-signed-lero-lmb4-reader-case-ci-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-LERO-LMB4-EXECUTION-CHAIN-2026-11-10.md`. Signed original 5 APK/6 DEX/230533 bodies: `Lga4.c():Lha4` move-result **в том же basic block** записывается в `Lero.Lha4` и передаётся в `Lmb4.<init>` word1; конструктор кладёт его в точное поле `Lmb4:Lm48`; `Lmb4.a` читает тот же field-ref, cast `Lha4`, вызовы `b(La58)`×2/`read([BII)`/`close()`.
- В `Lero.t` **проверен actual DEX selector** и захват точного `Lero.this` в `Lwq7.<init>(I,Object)`. Mode **не** входит в 2 explicit packed-switch кейса `Lwq7.e` и выполняет **default fallthrough**, где `Lwq7` считывает то же captured field → `Lero.Lmb4` → `Lmb4.a`. У `Lero.t` есть `execute/get`, но это не runtime-аудио подтверждение.
- **CI SUCCESS:** [source read #42821377729](https://github.com/manufact-test/nomusic/actions/runs/42821377729), [selector/capture #42822722957](https://github.com/manufact-test/nomusic/actions/runs/42822722957), [exact source field #42823360505](https://github.com/manufact-test/nomusic/actions/runs/42823360505), [Android module #42823360398](https://github.com/manufact-test/nomusic/actions/runs/42823360398) 2/2.
- **Критическая граница:** точный выбранный `trackId+edition+generation` в живом ExoPlayer и `decoder PREPARE` всё ещё НЕ доказаны. Android replacement audio НЕ работает, runtime hooks/прошивки не тронуты. Следующий этап: отдельный пассивный ARM Android player/source witness. Не повторять x86 LSPatch; не трогать Test.50/HONOR/Windows/production.

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — URI-модель → Lcq7.i0 → Lga4/Lero/Lha4 → DataSource (10.11.2026)

- **Проверенный исходник:** `f327f5b9bcfee028e754f9a803f29ade347cb240`, **rollback:** `backup/android-signed-uri-locv-source-cfg-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-URI-TO-DATASOURCE-LIFECYCLE-EVIDENCE-2026-11-10.md`. В оригинальном подписанном six-DEX `Locv.i0` читает URI-подобные данные, `Lw4y.z` парсит scheme/host/path/query (значения не экспортированы); результат попадает в coroutine `Llky`, `Lfwm.M` возвращает `Ljgv`, который bounded CFG передаёт `Lcq7.i0` и `Lcq7.D`.
- У `Lcq7.i0` только 2 прямых вызывающих: `Lo4y.c` и `Locv.i0`. Результат — **обёртка**; реальный `Lga4` извлекается через `iget-object` с условным путём к `Lnro/Lero`. Предыдущий анализатор ошибочно сохранял taint обёртки при `iget-object`; ошибка в DEX 22c nibble-kill исправлена и протестирована.
- В том же signed DEX: `Lcq7.A` результат → точный primary `Le48`-slot `Lga4`; `Le48.a` результат `Lm48` → argument word 3 `Lha4.<init>`; `Lha4.f` вызывает `Lm48.b(La58)`, `Lha4.read` — `Lv38.read`. `Locv.t/remove` условно вызывают `Locv.i0`, но это **НЕ доказательство live decoder prepare**.
- **CI:** [source register #42819113120 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819113120), [actual i0 CFG #42819106641 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819106641), [taint fix #42817633107 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42817633107), [Android module #42819113420 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42819113420).
- **ANDROID audio PASS — НЕТ.** Нельзя считать модель соответствующей активному `trackId/edition/generation` или выбранному pre-prepare DataSource. Контракты замены не подключались, HONOR/Test.50/Windows/API/production не трогались.

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ КОД — obfuscated DataSource + два Le48-источника (10.11.2026)

- **CI GREEN SHA:** `6b5bfde53d81a29920f32a3c6b13b730b216e669`; **независимый откат:** `backup/android-signed-dual-source-dataspec-open-ci-green-20261110`.
- **Читать ПЕРВЫМ:** `docs/android/ANDROID-NATIVE-SIGNED-DATASPEC-OPEN-SOURCE-EVIDENCE-2026-11-10.md`. Установлен подписанный DEX DataSource-совместимый контракт Lm48(b(La58):J, getUri, close) + родитель Lv38(read([BII):I), 33 реализации; проверены реальные Lha4.open/read и Lz3f.a→Lm48.b(La58).
- Lga4.b/c используют secondary Le48, Lga4.d primary Le48; secondary в Lcq7.i0 = Lya4 → Lza4 (открытие/чтение выбрасывает исключение), **primary = Lcq7.A→Luiq** (ленивая фабрика Lm48). Оба источника передаются в Lha4, нельзя их путать. Общее соседство с ExoPlayer **не доказывает** текущий trackId/edition/generation и live decoder PREPARE.
- **CI:** [field2 #42813687276 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42813687276), [two slots #42814211492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814211492), [inherited API #42814967628 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814967628), [source/open #42815048696 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42815048696), [Android module #42815048701 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42815048701).
- **Нет Android audio PASS** и точной идентичности FileInfo→текущий экземпляр Lm48 перед prepare. Ничего в player/replacement не подключено; Test.50/HONOR/Windows/API/production не тронуты.

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — оригинальный FileInfo → typed model → реальный Le48 field (10.11.2026)

- **Проверенный код:** `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`. **Бэкап:** `backup/android-signed-typed-dispatch-field-audit-ci-green-20261110` → ровно `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md` — реальные DEX данные от Lhee/Lged через Leed/Ldiv → Lygv.r → Ljgv → Lcq7/Lo4y/Larv; неоднозначный 16-way Le48 dispatch и точный writer/reader аудит двух разных Le48-полей класса Lga4.
- **CI SUCCESS:** [typed coroutines #42808158803](https://github.com/manufact-test/nomusic/actions/runs/42808158803), [Ldiv/Ljgv consumers #42808680756](https://github.com/manufact-test/nomusic/actions/runs/42808680756), [media candidates #42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855), [virtual dispatch #42809849405](https://github.com/manufact-test/nomusic/actions/runs/42809849405), [exact field writer #42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588), [Android module #42810750850](https://github.com/manufact-test/nomusic/actions/runs/42810750850) SUCCESS 2/2.
- **НЕ decoder proof:** найденная семишаговая близость к Lro7.y0 зависит от выбора одного из 16 виртуальных receiver и разных switch-веток. Фактически Lga4.c использует Le48 field-2, а конструктор инициализирует Lzcd в ДРУГОЙ field-1. Field-2 наблюдался с Lya4/Lkc6 и неизвестными writes, без подтверждённого current-track source. Android audio replacement по-прежнему НЕТ.

## Предыдущая подтверждённая точка

- **Точный проверенный код:** `8b7bc64f89249e5434da739851bececce2adb121` — [signed DEX CI #42806655214](https://github.com/manufact-test/nomusic/actions/runs/42806655214) SUCCESS, [Android module CI #42806655152](https://github.com/manufact-test/nomusic/actions/runs/42806655152) SUCCESS 2/2.
- **Rollback:** `backup/android-signed-register-cfg-ci-green-20261110` → `8b7bc64f89249e5434da739851bececce2adb121`.
- **Сначала изучать:** `docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md`. Выявлены Lxa7.<init>, Lged.a → Lhee.a и прямые coroutine callers; это may-flow, не Android decoder proof.

## Главное, читать по порядку

1. **Новый результат подписанного Android APK:** `docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md` — 6 DEX / 837 500 вызовов, прямой FileInfo caller `Lhee;->a`, model consumer `Lged;->a`, без ложного decoder proof, 2+2 прямых вызова MediaSession.
2. **Актуальный краткий статус + исторические ссылки:** `docs/android/NEXT-CHAT.md`. В этом накопительном документе старые «LATEST» и старые SHA — архив; верный кодовый SHA см. выше.
3. **Windows, реально работающий продукт:** `docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md` и `docs/windows/W57-OWNER-0247-REAL-AUDIO-SUCCESS-20261110.md`; код `windows-companion/w22/native-resource-adapter.mjs`. Windows `0.24.7` пользователь принял.
4. **Что из Windows уже аккуратно перенесено в Android:** `docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md` — строгий grant, Track ID, Next, Stop, поколения.
5. **Где находятся реально существующие кандидаты ExoPlayer:** `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md` — четыре обфусцированных класса и отрицательные результаты поиска.
6. **Старые исследования/отказы:** `docs/android/ANDROID-NATIVE-SIGNED-SOURCE-HOP-EVIDENCE-2026-11-10.md`, `docs/android/ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`; они нужны, чтобы не повторять x86/clone тупики, а НЕ как главная задача.

## GitHub, проверка, откат

- Репозиторий: https://github.com/manufact-test/nomusic
- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`; перед работой считать текущий HEAD, docs-коммит может быть новее кода.
- **Предыдущий проверенный код (shared-caller этап):** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- **[Подписанный APK статический CI #42804081064 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42804081064)**.
- **[Android Xposed read-only модуль CI #42804081053 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42804081053)**.
- Резервная ветка точно проверенного кода: `backup/android-signed-source-bridge-media-session-ci-green-20261110` → `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- До нового аудита: `backup/android-pre-real-signed-bridge-proximity-audit-20261110` → `0a1f035113fb826f88ebf827a46e5edc66635c7f`.
- Эталон владельца **Test.50** (реально проверен ref `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`): `backup/android-test50-exact-source-owner-accepted-20261106`; не изменять.

**Реальный статус:** Windows CELIKOM **да**, Android CELIKOM source substitution **нет**. Нужна действительная граница текущего decoder source; MediaSession — не она. Не выдавать исходный SDK/CI за реальный audio PASS, не переустанавливать Яндекс на основном телефоне.
