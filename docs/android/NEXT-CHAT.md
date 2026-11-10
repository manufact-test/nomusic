## UPDATE 10.11.2026 — verified publisher-access feasibility gate (NO-GO)

New research: `docs/android/ANDROID-NATIVE-PUBLISHER-HOST-FEASIBILITY-2026-11-10.md`. Android's app sandbox and MediaSession do **not** provide a generic source replacement hook into unmodified Yandex; `AudioPlaybackCapture` is output-only. Official Yandex archived job postings **confirm partner SDK/API integration work (MTS Music)**, but neither a publicly usable audio source extension nor permission for CELIKOM is documented. Precise unsolved prerequisite: **publisher-approved pre-prepare native source host**, including authoritative track+edition+generation and rights-cleared source contract. Clone `EXIT_SELF(0)` is confirmed; actual cause remains unknown (not proven anti-tamper). Native replacement remains **NO-GO**; no changes to code, APK or phone, no new CI because docs/research only. Backup pre-docs: `backup/android-native-publisher-host-gate-20261110` at `0cf4ee3be8b092a316eacdaa0dce988e20b8c49b`. Do **not** restart LSPatch x86 or AppMetrica experiments. Next action only with an explicitly documented or authorized publisher-supported interface; otherwise raise owner-level feasibility decision.

---

# CELIKOM Android — NEXT CHAT (10.11.2026)

## FINAL CHECKPOINT 10.11.2026 — atomic pre-prepare admission model, 2/2 CI SUCCESS

**Кодовый HEAD до документов:** `6ee199858e25ceddcc229cd1ad51b0bb5526b8ab`. **Backup:** `backup/android-native-preprepare-final-code-20261110`. **Главный новый отчёт:** `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md`. **Подготовлен текст для следующего чата:** `docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md`.

**[CI 42780177178](https://github.com/manufact-test/nomusic/actions/runs/42780177178) 2/2 SUCCESS**: Java модель `NativePrePrepareAdmission.java` атомарно проверяет точный track+edition+generation, FileInfo и descriptor перед prepare; 35 032 assertions PASS, включая 5 000 Next. `NativeSourceGate` исправлен: stale/rejected offer больше не возвращает ALT другого трека; 10 037 assertions PASS. `NativeTrackIdentityGate` 10 015 assertions PASS; Gradle read-only module builds. Всё **только тестовая модель**, не нативная подмена.

**Ключевой NO-GO без изменений:** подписанный оригинал работает, но clone MAIN `EXIT_SELF status=0`, собственного UI нет; издатель запрещает shell ART profiling, а публичного лицензированного native audio-source extension подтверждено не было. Дополнительный статический аудит всех шести DEX не доказал `eed → decoder pre-prepare`. Не устраивать снова x86 AppMetrica/loader, не обходить защиту/подпись, не переходить на WebView или второй плеер. Следующий рубеж — **авторизованный настоящий native host/source extension**, а не новые схемы перепаковки без доказательств. Test.50/HONOR/Windows/server/DB/production не тронуты.

---


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


**Сначала прочти:** `docs/android/ANDROID-NATIVE-HANDOFF-2026-11-10.md` (главная передача), `docs/android/ANDROID-NATIVE-STRICT-MAIN-UI-GATE-2026-11-09.md`, `docs/android/ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md`, `docs/android/ANDROID-NATIVE-DEX-STRING-ID-ORDER-2026-11-09.md`, `docs/android/ANDROID-NATIVE-TRACK-IDENTITY-EVIDENCE-2026-11-09.md`.

**GitHub:** `manufact-test/nomusic`; рабочая ветка `experiment/android-native-yandex-fileinfo-hooklab-20261109`. **Новый HEAD смотри по ветке после последнего docs-коммита.** Точный переданный функциональный/CI HEAD до docs-коммита: `0a249c0c6ab53823b208f31f2a2027f27aa023a2`.
**Backup перед документацией:** `backup/android-native-pre-final-handoff-20261110`; предыдущий `backup/android-native-dexsafe-main-ui-nogo-evidence-20261109`; Test.50 `backup/android-test50-exact-source-owner-accepted-20261108` (не трогать).

**Честный итог:** подписанный оригинал Яндекс.Музыки `2026.10.3 #170gpr`, пять split APK, в изолированном Android11+ARMv7 запускается и работает. 5+5 параллельная установка с separate clone PASS. Подтверждён `FileInfoApi` `trackId` param0, `codecs` param1, `quality` param3. Synthetic NativeSourceGate/JVM and separate own audio smoke PASS, не нативный Яндекс.

**Текущий NO-GO:** manifest-only clone с побайтно оригинальными DEX ставится рядом, но **main process и foreground UI не работают**: жив только `:AppMetrica` helper. Был неверный success 42695956456; исправленный строгий тест [42696772783](https://github.com/manufact-test/nomusic/actions/runs/42696772783) правильно FAIL. Причина выхода MAIN пока неизвестна. Старый патч AppMetrica нарушал DEX `string_ids`, теперь fail-closed. Безопасная структурная CI [42697151607](https://github.com/manufact-test/nomusic/actions/runs/42697151607) SUCCESS, read-only hooklab [42697074970](https://github.com/manufact-test/nomusic/actions/runs/42697074970) 2/2 jobs SUCCESS.

**Текущий следующий ход:** доказательно найти, почему у клона исчезает MAIN (Android `ApplicationExitInfo` reason codes, Activity/ART only sanitized), устранить без обходов защит, доказать полноценный foreground UI original+clone; затем read-only `trackId+edition → настоящий decoder pre-prepare` и лишь потом native single-source replacement. Первый аудио-регресс на реальном native Yandex: RASKOL ID 42884423 и «Дым» ID 39949113, затем «пшик» и быстрый Next/радио. Не повторять старый own audio smoke.

**Запреты:** не удалять официальный Яндекс на HONOR 50 Android13; не отключать Play Protect; не брать пароли/токены Яндекса; не публиковать clone/vendor APK; не менять Test.50, Windows, расширение, сервер, БД или production; не делать второй плеер. Работай автономно крупными блоками, останавливайся только для действительно нужной ручной проверки или после существенного законченного результата. Документируй GO/NO-GO точно.
