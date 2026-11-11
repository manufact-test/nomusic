# CELIKOM Android A1 — точный наблюдатель завершения MAIN (11.11.2026)

## Основание: реально переданный ChromaSync-Clone-3.0.1.apk

Проверенный прежним чатом SHA-256 образца: 4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d. Его побайтовые сведения сохранены в ANDROID-A1-CHROMASYNC-APK-OFFLINE-COMPARISON-20261111.md. В текущем runtime бинарник не примонтирован, поэтому повторный побайтовый анализ здесь не заявляется.

ChromaSync: независимый clone package, нативный Yandex 2025.10.4 #120.1rur, LSPatch metaloader с вложенным origin.apk, собственный LibXposed API102 модуль, sigBypassLevel=2. CELIKOM: независимый нативный Yandex 2026.10.3 #170gpr, metaloader+origin.apk уже воспроизведены, но нативный MAIN трижды уходит в EXIT_SELF(0), в том числе без модуля. Установка и упаковка доказаны, запуск UI не доказан. ChromaSync не проверялся на HONOR и не доказывает безопасную параллельную установку.

Различия версии, модуля и level2 реальны; нельзя выдавать конкретную причину EXIT_SELF за доказанную. Level2 меняет механизм проверки подписи и не разрешён для CELIKOM: НИКАКИХ level1/2, vendor-signature spoof, авторизационных обходов, Play Protect bypass или изменения официального приложения.

## Новый изолированный эксперимент

От статического аудита известны пять вызовов System.exit, два Process.killProcess и класс ck7 с обработчиком uncaughtException, но фактический runtime caller ещё неизвестен. Старые ART-трассы исчерпали буфер 8 MiB или были нулевыми.

Добавлен исходный, без разрешений, исключительно исследовательский LibXposed-модуль, область действия ровно pro.celikom.yandex.nativeclonelab. На истинном ARM13 в CI, только при CELIKOM_A1_EXIT_WITNESS=1, он вставляется как ЕДИНСТВЕННЫЙ собственный диагностический модуль в один lab APK с LSPatch sigBypassLevel=0. Модуль наблюдает java.lang.Thread.dispatchUncaughtException, System.exit, Runtime.exit и android.os.Process.killProcess; каждый hook делегирует chain.proceed() без изменений аргументов, результата, исключений или поведения приложения. Зарегистрированные hooks могут не перехватить нативный или ранний вызов: отсутствие маркеров не доказывает отсутствие вызовов.

В логах допускаются только фиксированные enum-маркеры без Throwable message, текстов stacktrace, URL, токенов, персональных данных и vendor bytecode. Python-классификатор связывает их исключительно с новыми PID процесса MAIN из ActivityExitInfo, отвергает фальшивые поля. Положительный маркер указывает конкретную семью вызова; отсутствие маркера оставляет NO-GO. Наличие ARMED — доказательство только постановки hook, но НЕ его выполнения.

Билд отдельной ветки: experiment/android-a1-exit-callsite-witness-20261111; исходный резерв: backup/android-a1-before-exit-callsite-witness-20261111 @ cc4cb0f. Workflow .github/workflows/android-native-a1-exit-callsite-witness.yml. 1-day artifact содержит ТОЛЬКО наш исходный модуль, без APK Яндекса. Тестовый host, ключи и исходные vendor splits эфемерны. CI строгий: даже если сборка и тесты зелёные, MAIN EXIT_SELF продолжает означать А1 NO-GO.

Ветка НЕ интегрируется в основу без проверки результатов. Не трогать Test.50, Windows, расширение, production, HONOR или официальный Яндекс. Этап B по-прежнему заблокирован до слышимой проверки Stage A владельцем.

## Native ARM13 confirmed owner and static conditional route (11 Nov)

Real CI [43023613994](https://github.com/manufact-test/nomusic/actions/runs/43023613994) confirmed actual own LibXposed observer in dying clone MAIN, pass-through System.exit/Runtime.exit/Process.killProcess; signed original survived, clone self-exited; strict app UI gate correctly FAIL.

Second real CI [43024491519](https://github.com/manufact-test/nomusic/actions/runs/43024491519) used finite allowlisted static exit owners. It **actually observed** STATIC_RUN_B = original signed DEX class Lxx0;.run in the clone MAIN exit-call stack, alongside System.exit and Process.killProcess. No uncaught event observed; no proof of reason.

Signed-original-only static audit CI [43025413011](https://github.com/manufact-test/nomusic/actions/runs/43025413011) found Lxx0;.run is 200 DEX code units, 13 if-branches, one switch, four gotos, two return instructions; it directly calls ActivityManager.getRunningAppProcesses, Context.getPackageName, Kotlin string prefix compare, Process.killProcess then System.exit, alongside unrelated locale/package-manager code. Three constructor callsites (Lby0.a, Lby0.p, Lhi2.j); zero direct run method calls (asynchronous dispatch possible, not proven).

A bounded control-flow edge audit [43026129390](https://github.com/manufact-test/nomusic/actions/runs/43026129390) validates every graph edge and finds **one conditional arm that can reach killProcess while the other cannot**, with preceding Kotlin string-prefix comparator and running-process/package-name inspection. The actual compared values or why branch was selected at runtime remain unknown. Do not claim proven publisher protection.

Next optional direct experiment: on disposable lab clone ONLY, with signature bypass still zero, observe the RESULT of that exact Kotlin prefix check when the runtime stack is within Lxx0.run. The module never changes arguments, return value or exception. Output only fixed categories (own main/aux, original main/aux, unmatched) and boolean match, no strings or account data. If Kotlin hook fails to arm, report NO_HOOK, and never infer the comparison result from missing evidence.

No product release: Test.50, Windows, production and user's device untouched. Main lead branch remains at original frozen cc4cb0f; research isolated.

## Native process-prefix result and event-order refinement

[Actual ARM13 CI 43026569379](https://github.com/manufact-test/nomusic/actions/runs/43026569379): OWN scoped Java observer builds, test suite passes, real native Android13 boots, LSPatch0 clone wraps six matching signed-host DEX and three .so with ONE own module, original signed app stays alive. The module sees its exact Kotlin prefix comparator within Lxx0.run at runtime; finite observed categories include OWN_MAIN and OWN_AUX, with MATCH_TRUE and MATCH_FALSE. Clone still exits MAIN twice with EXIT_SELF(0), strict workflow gate fails as intended. This proves runtime comparison of process-name-like values, not which particular match selected the kill branch. No raw app names or strings from runtime logged.

A new parser-only privacy-safe correlation now records the last MAIN-thread PREFIX_CHECK marker in each **exact fresh exited MAIN PID** before its first PROCESS_KILL or SYSTEM_EXIT marker. Output is a fixed finite enum per PID collapsed into a set; no PID, time, tokens or values. An event immediately preceding termination is **temporal evidence**, not necessarily the causal predicate. Added two synthetic interleaving/background-thread tests. The scoped observation still never overrides the security policy or return values.

## Exact same-PID kill target witness (final narrow A/B, 11 Nov 2026)

[ARM13 CI 43028345936](https://github.com/manufact-test/nomusic/actions/runs/43028345936), isolated experiment SHA cc176ee80a91190e379f46899b157065201a73e4. Our OWN module compiles. Native ARM13 guest and lab LSPatch0 wrapper succeed; original issuer-signed Yandex remains alive. The strict native cloned MAIN gate still fails (two fresh MAIN PIDs, EXIT_SELF status zero). No native user UI or audio replacement.

For **both** fresh independent clone MAIN PID instances, our pass-through hooks observed:
- Lxx0.run() prefix check on OWN_AUX group: MATCH_TRUE directly preceding first termination call in each MAIN PID
- android.os.Process.killProcess is invoked with a PID **different from the executing MAIN process PID** (KILL_TARGET_OTHER on both MAIN lifecycles)
- Java System.exit and Runtime.exit are also called by the exact Lxx0.run frame, and each MAIN exits with ZERO
- The signed-original static DEX graph independently confirms exactly one conditional route towards killProcess and a preceding string prefix comparison, ActivityManager.getRunningAppProcesses, Context.getPackageName

**What is established:** This is a concrete process-lifecycle exit path; the method first targets another process PID before the MAIN process itself exits. The static/runtime evidence is tightly aligned, and the two fresh MAIN attempts reproduce identically.

**What remains unknown:** Whether the target-other PID is precisely the auxiliary process (as opposed to another PID); why Lxx0.run() is invoked twice rather than original publisher-signed host surviving; whether this is a locale/process restart routine, a package-identity bug, or security enforcement. Do NOT assert security-bypass checks, do NOT disable components or signature checks as a fix, do NOT claim working application.

**Next diagnosis only if needed:** Inspect signed original Lby0.a / Lby0.p(Context) / Lhi2.j callsites that construct/schedule the multi-branch Lxx0 runnable. Determine process-restart vs legitimate safety policy first; avoid more blind repackaging. No producer/stable/user APK from this laboratory result.

Exact rollback branch: backup/android-a1-xx0-aux-prefix-other-pid-kill-evidence-20261111 at cc176ee80a91190e379f46899b157065201a73e4. Primary lead source remains frozen cc4cb0f93489168db21502f3ef195855ae9fb743; no changes to original Yandex on user device, accepted Test.50, Windows, server or extension. Stage A NO-GO, Stage B locked.

## Signed scheduler provenance and new runtime Runnable-mode witness (11 Nov)

Signed #170gpr source-only CI 43032933630 PASS (three synthetic tests and all six immutable publisher-signed DEX). Lxx0 is a Runnable, constructed by exactly three observed callers: Lby0.a() creates Lxx0(Context,int) and hands it to Lay0.execute(Runnable); Lby0.p(Context) creates Lxx0 and also calls Lay0.execute(Runnable), while coordinating AndroidX application locales. Lhi2.j(Object) constructs Lxx0 and posts via Handler.getMainLooper(). The incoming paths include Lqx0.attachBaseContext -> Lby0.p and Lc63.onCreate -> Lby0.a, plus Lhi2.invokeSuspend -> Lhi2.j. The latter has Passport/analytics and an IllegalStateException constructor, but this does not establish that the exception causes process exit.

New isolated optional lab probe hooks Lxx0(Context,int) and Lxx0.run using official LibXposed API102 hook(Executable). Both hooks ALWAYS forward chain.proceed unchanged; the module maps only 0..7 / OTHER / UNKNOWN constructor case numbers by object identity, then correlates entering a particular Runnable mode on the same exact newly exited MAIN PID before the first exit call. The module may miss a constructor installed too late: CASE_UNKNOWN is inconclusive and should not trigger blind revisions. No strings, account data, APK source, process PIDs or raw stacks included.

Only the disposable clone with signature bypass 0 is scoped. Main A1 source frozen; do not merge until runtime proof and authorized bug fix. No consumer APK yet.
