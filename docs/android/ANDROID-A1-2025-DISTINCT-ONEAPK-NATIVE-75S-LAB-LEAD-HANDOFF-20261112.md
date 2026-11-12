# CELIKOM Android A1 — экспериментальный отдельный ONE APK: нативный 75s PASS, handoff 12.11.2026

**Статус: лабораторный технический прорыв, НЕ потребительская сборка. Stage A NO-GO, Stage B LOCKED, issue #41 остаётся открытым.** Готовый APK для пользователя НЕ выдавать, пока не проверены настоящие Yandex UI, авторизация и слышимая подмена B42.

## Главный новый подтверждённый результат

Два независимых последовательных реальных ARM13 GitHub CI (Redroid Android 13, arm64/armv7):
- [#43217132456 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43217132456), source commit `a513233db19b6670f3178bfcde83f3536d0e4794`.
- [#43217178231 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43217178231), source commit `5891ee655061d2049d1e0b9fa7a83927f3b563d2`.

В каждом прогоне:
1. Загружен из **существующего unpublished private draft** и строго проверен **publisher-signed оригинал Yandex Music 2025.10.4 #120.1gpr**: точный архив 45,961,661 байт, SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, **16/16 splits**.
2. Штатный оригинал `ru.yandex.music` сначала установлен на чистый ARM13 и держится в MAIN **75 сек / 25 из 25 наблюдений**.
3. Publisher-signed **base** (не переподписанный input!) → pinned LSPatch v1.2-487 `sigBypassLevel=2` → остальные splits с собственным временным ключом → независимо названный `pro.celikom.yandex.nativeclonelab` → APKEditor объединяет 16 → **ОДИН** проверенный подписанный собственным ключом APK. Вложенный оригинальный source/input, LSPatch bootstrap, DEX/native parity и ELF alignment проверяются fail-closed. ORIGINAL и CELIKOM одновременно установлены; original сохранён и не изменён.
4. **CELIKOM отдельно названный MAIN native 75s 25/25 stable, 25/25 resumed, single clone APK installed, оригинал остаётся установлен.** Вердикт CI `LAB_ONLY_METRICA_FAILOPEN_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. Это первый доказанный нативный 75-секундный независимый ONE-APK запуск с сосуществованием оригинального Яндекса.
5. Наш единственный pass-through LibXposed lab-модуль фиксирует 1 точное `IllegalStateException` из `METRICA_SDK`, `DETAIL_NOT_INITIALIZED` и **именно этот объект Throwable** достигает обработчика аварий Android. В *лабораторной копии ТОЛЬКО* `RuntimeInit$KillApplicationHandler.uncaughtException` для **DIRECT_METRICA** с точным объектом метрики перехватывается и не передаётся далее Android; все остальные ошибки и ситуации делегируются оригинальному обработчику. Установка оригинала, подписи/аутентификация, мультимедиа и DEX/vendor код не изменялись. `lab_only_metrica_fatal_suppression_count_bounded=1`, `lab_only_metrica_fatal_suppression_observed=true`, `fatal_throwable_link_verdict=DIRECT_IDENTITY`. Здесь **не** доказано, что SDK исправно функционирует, что не возникнет скрытой поломки или что suppression безопасен для продукта.

**Важный промежуточный ложный негатив:** [#43215906750](https://github.com/manufact-test/nomusic/actions/runs/43215906750) уже показал 25/25 stable, но итог CI FAILURE, потому что наблюдатель привязывался только к *умершему* MAIN PID из ApplicationExitInfo. Исправили парсер: если native 25/25 gate PASS, он допускает строго проверенный живой `pidof` именно MAIN, не публикует PID и не принимает невалидные значения. После этого #43217132456 и #43217178231 **оба full-CI SUCCESS**, в обоих есть реальные bounded lab suppress events. Не повторять старый parser-only false FAIL.

## Важная цепочка предшествующих настоящих ARM13 проверок

- [#43204916823](https://github.com/manufact-test/nomusic/actions/runs/43204916823) — ещё до lab suppression 16→1 original-name `ru.yandex.music` LSPatch2 independently signed native MAIN 75s PASS, доказывает, что split→single merge сам по себе рабочий. Но не может стоять рядом с оригинальным Яндексом под тем же package name.
- [#43202922695](https://github.com/manufact-test/nomusic/actions/runs/43202922695): «оригинал FIRST, CELIKOM SECOND» оба устанавливаются, CELIKOM Java MAIN crash. [#43203474672](https://github.com/manufact-test/nomusic/actions/runs/43203474672): сохранение исходных authority не спасает. [#43203990462](https://github.com/manufact-test/nomusic/actions/runs/43203990462): даже смена одного root package при неизменных component/permissions не спасает.
- [#43206543625](https://github.com/manufact-test/nomusic/actions/runs/43206543625): удаление восьми optional AppMetrica manifest-компонентов НЕ исправляет crash. В успешном лаб-эксперименте все исходные компоненты сохранены; не внедрять их удаление.
- [#43213402064](https://github.com/manufact-test/nomusic/actions/runs/43213402064): собственный read-only наблюдатель связывает тот же Java Throwable `METRICA_SDK` с Android fatal dispatch по **object identity**, а не по времени.
- [#43215043898](https://github.com/manufact-test/nomusic/actions/runs/43215043898): при сохранённых всех штатных optional AppMetrica компонентах fatal exception имеет категорию **`DETAIL_NOT_INITIALIZED`**.
- [#43216424830](https://github.com/manufact-test/nomusic/actions/runs/43216424830): SDK public `activate(Context,...)` actually enters 3 times, **returns 3 times** (`THROW=0`), context is **CLONE**; позднее AppMetrica бросает NOT_INITIALIZED fatal. Следовательно, добавление ещё одного наивного `activate()` не доказано как fix. Возможны lifecycle/order/config/classloader/process differences. Нужно установить реальную семантику SDK init после успешного вызова, а не маскировать crash для продукта.

## Точные source / rollback

- **Последняя успешная лабораторная ветка:** `experiment/android-a1-2025-metrica-optional-failopen-arm13-20261112` @ **`5891ee655061d2049d1e0b9fa7a83927f3b563d2`** (на момент handoff).
- **Точный immutable резерв самого успешного состояния:** `backup/android-a1-2025-distinct-oneapk-native-75s-metrica-lab-pass-20261112` @ этот SHA.
- Предыдущий независимый подтверждённый успешный commit: `a513233db19b6670f3178bfcde83f3536d0e4794`; backup `backup/android-a1-2025-distinct-oneapk-native-75s-metrica-first-pass-20261112`.
- Резерв до изменения fatal handler: `backup/android-a1-metrica-optional-failopen-pretrial-20261112` @ `780b07daeaf86d684cea8eb53509c97042e169c4`.
- Frozen main A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`; user accepted Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108` неизменны.
- Собственный witness: `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`.
- CI script + actual 75s gate: `android/native-yandex-hooklab/ci/owner_2025_lspatch2_namespaced_clone_arm13.py`.
- PID-scoped finite-output witness parser: `android/native-yandex-hooklab/ci/a1_metrica_witness_private_parser.py`, regression fixture `ci/test_a1_metrica_witness_private_parser.py`.
- Successful workflow `.github/workflows/android-a1-2025-metrica-optional-failopen-arm13.yml`.
- Read-only no-suppression activation observer branch `experiment/android-a1-2025-metrica-activation-observer-arm13-20261112`, run #43216424830.
- Current GitHub issue [#41](https://github.com/manufact-test/nomusic/issues/41). Companion B42 source-only contract issue #42; **native integration NOT done**.

## Обязательное следующее действие для нового ведущего

1. Начни с **изучения этих исходников/CI и результатов**, не переписывай проект, не повторяй уже закрытые гипотезы. Создай собственную новую `experiment/` ветку от успешного lab sha **и точный `backup/` перед модификацией**. Не делай изменений в frozen A1/Test.50.
2. **Приоритет №1: исправить первопричину AppMetrica `NOT_INITIALIZED`, а не оставить suppression как продуктовую меру.** В read-only SDK activation эксперименте `activate()` ENTER=3 RETURN=3 THROW=0, но позже SDK смертельно падает: вероятны разные процессы/класслоадеры/порядок установки/конфигурация, но **это гипотезы**. Исследуй точные init lifecycle/SDK state, защищённо, без утечки API keys, пользовательских данных и чужого бинарного кода. Повтори полный native ARM13 75s под тем же отдельно названным пакетом **с отключённым лабораторным suppression**. Если без него невозможно, оставь честный NO-GO.
3. Только после отдельного REAL native 75s подтверждения с корректной SDK init и устойчивым UI — интегрировать готовый B42 аудиоисточник перед декодером с реальной подменой, диапазонами HTTP Range, реальным звучанием, паузой/seek/Next/MyWave; пользовательскую установку и Play Protect проверять отдельно. Не выдавать ни сборку, ни «всё готово» раньше этих gate.
4. Никаких публикаций issuer-signed XAPK, derived APK, стороннего app-кода, личных аккаунтов или signing keys в public GitHub или Actions artifact. Временный lab APK и ключи должны удаляться после workflow; не менять untouched original на устройстве владельца.
5. Владелец просит **длинные самостоятельные блоки, без бесконечных отчётов/повторных вопросов**, в конце краткий вывод, точная backup, docs и первое сообщение новому чату. Не предлагай отдельный придуманный плеер, WebView или связь с Яндексом — цель родной UI рядом со штатным приложением.

**Реальный продуктовый статус:** Stage A NO-GO / Stage B LOCKED. Оригинал Яндекс на HONOR, Windows/Chrome/production API, Android Test.50 и frozen A1 не изменялись. Нет проверенной авторизации, настоящего звука/подмены, паузы/seek/Next/MyWave, защиты/Play Protect или релизной APK.
