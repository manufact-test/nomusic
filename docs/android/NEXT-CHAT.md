# CELIKOM Android — NEXT CHAT (10.11.2026)

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
