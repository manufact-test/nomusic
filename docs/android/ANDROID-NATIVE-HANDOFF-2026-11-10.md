# CELIKOM Android — передача следующему ведущему разработчику (10.11.2026)

## 10.11.2026 — новое: FileInfo → Media3 short-path audited, no decoder runtime proof

**Code HEAD before docs:** `b807fe3b312823961b1c4d55fd669fcbc1df57d1`. **Backup:** `backup/android-native-crossdex-source-hop-readonly-20261110`.

**READ-ONLY signed original 5 splits / 6 DEX:** [CI 42777930530](https://github.com/manufact-test/nomusic/actions/runs/42777930530), [42778116766](https://github.com/manufact-test/nomusic/actions/runs/42778116766), [42778216759](https://github.com/manufact-test/nomusic/actions/runs/42778216759), [42778331313](https://github.com/manufact-test/nomusic/actions/runs/42778331313) all SUCCESS. 230,533 method bodies / 837,500 invoke links scanned. 33 Media3 classes / 384 refs exist; strict names createMediaSource/prepare not detected. Graph joined **across all six DEX**: **0 bounded 1–3-hop** links from 1 converter-caller and 6 `eed` model consumers to recognizable Media3/ExoPlayer classes. This is **only a bounded static negative**, not proof decoder absent. **No actual trackId + edition → decoder pre-prepare** yet.

**Runtime still NO-GO:** [42776115700](https://github.com/manufact-test/nomusic/actions/runs/42776115700) strict Android11 original+clone: MAIN self-exits `reason=1 status=0`; clone foreground UI absent; original runs. Publisher-signed manifest `debuggable=false` and `profileable shell=false`; no authorized ART method trace. Do not circumvent signature, OAuth/Passport, Play Protect, DRM, or force modified Yandex onto HONOR. Do not do another unsorted DEX patch or second-player architecture.

**Full new report:** `docs/android/ANDROID-NATIVE-SIGNED-SOURCE-HOP-EVIDENCE-2026-11-10.md`. Next productive gate: obtain a legitimately permitted in-process native host/integration API, then observe source-boundary ownership and real track+edition before prepare. No manual owner action, no new install now. Test.50, Windows, extension, backend, DB, production all untouched.

---


## UPDATE 10.11.2026 — publisher ART profiling denied; exit(0) caller still not attributed

**Latest code HEAD before this docs commit:** `360fec15b719543b909035daee99b30e3257c7ad`.
**Current code backup:** `backup/android-native-profileability-gate-exit-evidence-20261110`.
Earlier backup: `backup/android-native-pre-activity-start-trace-20261110`.

Real isolated Android 11 [ART startup-profiler CI #42775069981](https://github.com/manufact-test/nomusic/actions/runs/42775069981) reported `trace_available=false`, no trace file, no secret/raw trace or third-party APK distributed. Clone MAIN still exits `ApplicationExitInfo REASON_EXIT_SELF=1, status=0`; helper :AppMetrica alone alive, original Yandex still alive; UI gate FAIL.

**The publisher-signed original manifest explains the supported-access limit**: [structural CI #42775600758](https://github.com/manufact-test/nomusic/actions/runs/42775600758) SUCCESS, `profileable_declaration_present=true`, `profileable_shell_granted=false`, `publisher_debuggable=false`, `ordinary_shell_method_tracing_authorized=false`. Android official profileable specification states shell tools require app debug mode or explicit profileable shell permission. Neither is available here. **Do not add `debuggable` or `profileable` to a publisher app, run as root, or bypass Android policy.** New code rejects future `CELIKOM_PROFILE_MAIN_LAUNCH=1` if signed publisher doesn't grant tracing; startup profiler workflow is manual-only archived for authorized future cases.

**Additional signed-Dex static audit:** [CI #42775940114](https://github.com/manufact-test/nomusic/actions/runs/42775940114) SUCCESS, 6 original DEX / all methods decoded. The scanner investigated adjacent immediate-register arguments at 7 known termination callsites (5 `System.exit`, 2 `Process.killProcess`); **all 7 = `NOT_PROVEN`**, so `status=0` does **not** identify the actual caller. Three of the `System.exit` sites remain inside `Lck7.uncaughtException`, but no live invocation proof. Do not misread `NOT_PROVEN` as proof of a dynamic or nonzero argument.

**Current hard verdict: NO-GO for clone MAIN/UI and native audio;** unchanged original and 5+5 installation are not enough. No trackId/edition→actual decoder trace, no RASKOL/«Дым» native regression or replacement sound. A technical route forward requires a legitimate publisher-approved profiling/integration capability or independently verified authorized native source API. Do not reverse a publisher protection to make clone work. Windows, Test.50, official HONOR Yandex, extension, backend/DB/production not modified. No owner manual action.

---


## UPDATE 10.11.2026 — EXIT_SELF(0), runtime and Windows cross-audit

**Code HEAD before docs:** b2e0f785083ea687631c95d1e2173a563cae9b4d.
**Backup:** backup/android-native-exit0-pid-scoped-static-audit-20261110.
**Verdict: NO-GO native clone MAIN/UI and replacement.** Signed original Yandex still runs; 5+5 installs concurrently only in disposable emulator. Clone MAIN starts/dies repeatedly and records Android 11 ApplicationExitInfo reason=1 (EXIT_SELF) **status=0**. No clone main Activity creation/resumption or focused window; :AppMetrica alone survives. [Manifest-only runtime 42708994496](https://github.com/manufact-test/nomusic/actions/runs/42708994496), [consistent sorted AppMetrica 42708994506](https://github.com/manufact-test/nomusic/actions/runs/42708994506): both FAIL and same symptom. Sorted-provider experiment is now **manual-only workflow** (commit b2e0f785); do not auto-repeat.

**New static evidence:** six genuine signed DEX [42710445292](https://github.com/manufact-test/nomusic/actions/runs/42710445292) PASS. Total direct calls: 5 System.exit and 2 Process.killProcess. Class Lck7 implements Thread.UncaughtExceptionHandler and its uncaughtException calls System.exit three times and throwable logging. YMApplication.onCreate contains two calls installing a default uncaught handler. This is a plausible hidden-exception route, **not proven as executed**.

**MAIN PID scoped runtime:** [42711030929](https://github.com/manufact-test/nomusic/actions/runs/42711030929) and [42711030869](https://github.com/manufact-test/nomusic/actions/runs/42711030869) correctly FAIL main UI. On clone MAIN PID(s), AndroidRuntime-tag logs and generic Exception/Error markers were detected. However **FATAL EXCEPTION=false, bounded Throwable=[], Caused by=[]**, creation-stage categories unavailable: no actual Java fatal or precise caller established. Do not claim Java crash is proven. Only categorical output; raw logs/PIDs/account data/vendor APK not published. Structural safe package CI #42711031353 SUCCESS and read-only hooklab CI #42711031318 SUCCESS do not prove native UI/audio.

**Windows / Analytics (read-only review):** Windows W45 proved and corrected origin music-application://desktop for audio-only CORS (CI 42707502289 SUCCESS). Android native Retrofit is not subject to browser CORS; no direct technical fix to transplant. Reused Windows bounded stage diagnostics and fail-closed reporting only. docs/analytics/event-catalog.md remains draft, ingestion not enabled. Windows branch, Test.50, HONOR, extension, backend, DB, production untouched.

**Next:** establish lawful, read-only concrete runtime self-exit caller/condition on disposable emulator, no signature, Passport or Play Protect bypass. If impossible without publisher security evasion, clone feasibility stays NO-GO; pursue only authorized native integration. No native Yandex live trackId→decoder hook, no real audio replacement, RASKOL 42884423/Дым 39949113 remains untested. Do not repeat already-passed standalone Audio Smoke or issue a user APK.

---


## Актуальное продолжение: MAIN EXIT_SELF + согласованный AppMetrica A/B (10.11.2026)

**Новый кодовый HEAD до этого docs-коммита:** `9c117e994c1562c5f820de843fa15e04d58b8e38`.
**Контрольная ветка:** `backup/android-native-exit-self-ab-evidence-20261110`.
Полный отчёт: `docs/android/ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`.

Строгая диагностика [42704598401](https://github.com/manufact-test/nomusic/actions/runs/42704598401) выявила: MAIN клона действительно стартует (`am_proc_start`), затем исчезает (`am_proc_died`), а Android 11 относит выход именно MAIN к `REASON_EXIT_SELF=1`. Java/ART/DEX crash не подтверждён, `:AppMetrica` остаётся, UI/фокус отсутствуют. Старый парсер причин выхода исправлен и проверен юнит-тестами. Подписанный исходный Яндекс продолжает работать.

Контролируемая правка одного AppMetrica provider string с соблюдением сортировки `string_ids` и согласованным манифестом **не помогла**: [42706194581](https://github.com/manufact-test/nomusic/actions/runs/42706194581) FAIL, тот же `REASON_EXIT_SELF`. Независимый manifest-only A/B [42706195477](https://github.com/manufact-test/nomusic/actions/runs/42706195477) также FAIL. [42705716074](https://github.com/manufact-test/nomusic/actions/runs/42705716074) статически нашёл 7 точек явного завершения в оригинальных DEX, но **не определил реальный вызов**. Причина/условие выхода внутри приложения пока НЕ доказаны. Не утверждать, что виновата подпись, anti-tamper или AppMetrica.

**NO-GO на нативный клон и аудиоподмену.** Не повторять согласованный/несогласованный AppMetrica-эксперимент и не делать произвольных DEX-правок. Следующая работа — только подтверждение точного self-exit источника через разрешённую read-only диагностику в изолированной среде; если для этого нужен обход издательских защит, прекратить эту ветку и рассматривать официальную интеграцию. Ни Play Protect, ни вход в Яндекс, ни decoder не обходить. Test.50/HONOR/остальные платформы не трогали.

---


## Точка сохранения

- Репозиторий: `manufact-test/nomusic`
- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`
- **Последний кодовый и проверенный до этой передачи HEAD:** `0a249c0c6ab53823b208f31f2a2027f27aa023a2` (после коммита документов ориентироваться на HEAD ветки)
- Резерв до передачи: `backup/android-native-pre-final-handoff-20261110`
- Резерв предыдущего подтверждённого этапа: `backup/android-native-dexsafe-main-ui-nogo-evidence-20261109`
- Независимый эталон Android Test.50: `backup/android-test50-exact-source-owner-accepted-20261108` — **НЕ МЕНЯТЬ**

Сначала открыть `docs/android/NEXT-CHAT.md`, этот документ и `docs/android/ANDROID-NATIVE-STRICT-MAIN-UI-GATE-2026-11-09.md`. Затем обращаться к `docs/android/ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md`, `ANDROID-NATIVE-DEX-STRING-ID-ORDER-2026-11-09.md`, `ANDROID-NATIVE-TRACK-IDENTITY-EVIDENCE-2026-11-09.md` и `ANDROID-NATIVE-MANIFEST-ONLY-CONTROL-2026-11-09.md` за деталями.

## Неизменная цель

CELIKOM должен работать **в нативной Яндекс.Музыке** — только один плеер Яндекса, его интерфейс, очередь/радио, пауза, перемотка и Bluetooth. Пользователь входит в Яндекс исключительно **внутри самого Яндекса**. Нельзя строить второй проигрыватель, WebView-авторизацию или независимые синхронизируемые аудиопотоки. Подмена источника — только разрешённой правообладателем альтернативы, **до prepare** и с точным треком/редакцией.

У владельца HONOR 50 (Android 13) с установленной официальной Яндекс.Музыкой. Нельзя удалять или заменять официальный пакет, менять Google Play Protect, собирать пароль/токены Яндекса, выпускать или распространять перепакованный Яндекс, трогать Test.50, Windows, расширение, сервер, БД или production. Любые эксперименты с копией — только на отдельном чистом эмуляторе; подписание и APK не публиковать.

## Что действительно подтверждено

1. Собственный отдельный ARMv7 loader/LSPatch и собственный Audio Smoke Test владелец уже проверил на HONOR: перехват, свой источник **до prepare**, Pause/Resume/Seek/Next работали, `Errors=0`. **Не просить повторять эти проверки**. Они НЕ доказывают нативную подмену в настоящем Яндексе.
2. `NativeSourceGate`: 10 031 синтетический PASS, включая 2 500 быстрых Next; `NativeTrackIdentityGate`: 10 015 JVM assertions PASS и сборка read-only hooklab. **Это модели**, не реальные native decoder/audio результаты.
3. На подлинных пяти подписанных split APK Яндекс.Музыки `2026.10.3 #170gpr`, `versionCode=24026531` статически доказано: `FileInfoApi` и `OldFileInfoApi` принимают **`trackId` в параметре 0**, `codecs` в 1, `quality` в 3. CI [42677831933](https://github.com/manufact-test/nomusic/actions/runs/42677831933) SUCCESS. Нужная реальная связь `trackId + edition + generation → source/decoder pre-prepare` **НЕ доказана**.
4. Изолированный Android 11 x86 Google APIs с трансляцией ARMv7 позволяет установить подлинный оригинал и независимый clone **параллельно (5+5 split APK)**. Оригинал действительно запускается и остаётся в работе: [42686813136](https://github.com/manufact-test/nomusic/actions/runs/42686813136).
5. В старом clone-патче одно изменение строки AppMetrica сохранило длину и контрольные суммы DEX, но **сломало обязательную сортировку DEX `string_ids`**; статический PASS [42690904213](https://github.com/manufact-test/nomusic/actions/runs/42690904213). Теперь `patch_one_dex` **fail-closed**, такой повреждённый DEX создавать нельзя.
6. Вариант `CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX=1` оставляет **все шесть DEX побайтно оригинальными** и структурно пересобирает 5 split APK: [42697151607](https://github.com/manufact-test/nomusic/actions/runs/42697151607) SUCCESS. Исходный Яндекс не меняется, две оригинальные `signature` permission-декларации не переобъявляются в отдельной *одноразовой тестовой копии*. Это не обход защиты, не подтверждение входа.
7. Сборка отдельного read-only CELIKOM hooklab: два job SUCCESS [42697074970](https://github.com/manufact-test/nomusic/actions/runs/42697074970). **Ни одного перехвата в настоящем нативном Яндексе ещё нет.**

## Главный блокер — CURRENT NO-GO

Был ложноположительный SUCCESS [42695956456](https://github.com/manufact-test/nomusic/actions/runs/42695956456): при запуске clone оставался только вспомогательный процесс `pro.celikom.yandex.nativeclonelab:AppMetrica`. Реальный `MAIN` процесс **не жив**, активного главного окна clone **нет**. У настоящей Яндекс.Музыки MAIN launcher использует процесс приложения по умолчанию (подписанный manifest [42696018566](https://github.com/manufact-test/nomusic/actions/runs/42696018566)).

Новый строгий тест [42696772783](https://github.com/manufact-test/nomusic/actions/runs/42696772783) **ОЖИДАЕМО FAIL** с `MAIN_UI_NOT_READY_AUXILIARY_PROCESS_ALONE_INSUFFICIENT`. Оригинал продолжает работать. Так и должно быть: зелёная галочка вспомогательного `:AppMetrica` не равна запуску полноценного клона!

При manifest-only эксперименте прежняя `YMApplication ClassNotFoundException` не обнаружена, но **причина завершения основного процесса всё ещё не установлена**. Текущая `classify_activity_exit_info` неверно ищет буквенные `REASON_CRASH` вместо формата Android `reason=4 (APP CRASH(EXCEPTION))`; не интерпретировать её нулевые флаги как отсутствие падения. Исправление парсера пытались сделать, но инструмент отклонил изменение: **в код не вошло**.

## Что делать дальше, крупными блоками

1. **Точечно диагностировать завершение именно MAIN процесса** в чистом Android 11 эмуляторе: сопоставить результат `am start -W`, `pidof`/именованный `ps`, foreground Activity, штатные причины `ApplicationExitInfo` и безопасную классификацию AndroidRuntime/ART. Не публиковать сырые журналы, содержимое аккаунта или APK. Добавить unit tests, исключающие false PASS от `:AppMetrica`.
2. Найти причину отсутствия рабочего главного экрана и исправить её **без обхода подписи, Passport и Play Protect**. После этого подтвердить одновременно оригинал и clone со **своим MAIN foreground UI**, иначе NO-GO. Не вносить прежний ломавший сортировку DEX-патч.
3. Только после законного и работающего native-host — read-only трассировка действительного `FileInfo` параметра `trackId` и редакции до реального decoder prepare (не путать Retrofit API с доказательством фактического декодера). Затем одна native audio source, а не второй плеер.
4. Первые реальные регрессии: **RASKOL / Космонавты — «Нас не понимают вообще» ID 42884423**, **Лёша Свик — «Дым» ID 39949113** (Pause/Seek); «пшик» в начале, запоздалые радио/рандом/Next и гонки. Проверка на HONOR — **только когда действительно готов безопасный отдельный тест без удаления официального Яндекса**, с разрешения владельца.

## Границы правдивости

Нет готового native CELIKOM APK, успешной авторизации Passport в клоне, вердикта Play Protect, входящего в нативный декодер read-only hook, подтверждённой реальной подмены, акустической проверки RASKOL/«Дым». Не ставить эти пункты в PASS по одному лишь структурному тесту и не повторять own audio smoke, прошедший ранее.

Следующий разработчик продолжает **от текущей ветки**, не создаёт проект заново, сохраняет резерв перед рискованными изменениями, ведёт CI и документацию, обращается к владельцу только ради действительно необходимой ручной проверки либо после крупного объёма законченной работы.
