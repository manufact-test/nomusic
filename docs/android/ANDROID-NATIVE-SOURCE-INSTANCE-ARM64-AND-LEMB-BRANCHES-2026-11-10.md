# CELIKOM Android — source-instance / generation fence и реальные Lemb-ветви оригинального Яндекса

**10.11.2026.** Следующий этап после `ANDROID-NATIVE-SIGNED-LERO-LMB4-EXECUTION-CHAIN-2026-11-10.md`. Продолжаем **сохранённую** лабораторию, не создаём новый Android-проект.

## Контрольная точка

- **Последний CI GREEN код:** `59aa2d14bf32fd0f5eb553c09ec88738d84353a0` (предыдущий зелёный `3aaab880fff4326b596f63a52a89a0f4d0085fef`).
- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
- **Последний rollback:** `backup/android-signed-source-instance-failclosed-arm64-ci-green-20261110`. Предыдущий rollback: `backup/android-signed-source-instance-arm64-lemb-ci-green-20261110`.
- До этого этапа: код `f04745f7dcd4455996eadf56dc0be6c52a44c63f`, откат `backup/android-signed-lero-lmb4-reader-case-ci-green-20261110`.
- Все действия — GitHub, read-only original signed DEX и **OWN-ONLY** Java model. Не использованы личный HONOR, пользовательский аккаунт, аудиофайлы, URL, оригинальный APK-патч, DRM, production, API или Windows.

## 1. В оригинальном Яндексе Lero — не гарантированный выбранный источник

В pinned издательски подписанном Yandex Music `2026.10.3 #170gpr` (5 APK, 6 DEX / 230 533 тела методов) выполнены два исследования:

- `audit_native_lemb_selection_dispatch.py`: точные `Lemb.t/remove` callsites, отношения интерфейсов и владельцы вызовов. **Восемь конкретных реализаций Lemb**: `Lalt, Lchg, Lero, Locv, Lojz, Lt67, Lt6f, Lxq7`.
- **Всего 4 прямых invoke-site Lemb.t/remove в 4 методах:** `Lchg.t`, `Lchg.remove`, `Lciv.e` и `Larv.g`. Сам `Lciv.e` считывает сохранённый `Lemb` field-ref и вызывает `t`; `Lchg.t` передаёт `t` внутреннему `Lemb`. Ни один из этих callsites **сам по себе не устанавливает конкретный runtime receiver или выбранный ExoPlayer**. В `Lchg` общий обфусцированный multiplexer с большим числом интерфейсов — его нельзя считать однозначным Lero.
- В `audit_native_source_real_callers.py` расширен фокус до `Larv/Lkvs/Lchg/Lciv/Lxq7` и их точных конструкторов/методов. Наличие классов/метод-рефов **не** равно фактическому текущему аудиопути.
- Дополнительный factory census показал разные `Lemb`-классы в **условных** вариантах фабрик (значения приватных строк не экспортировались):
  - `Lkvs.A`: `Lero`, `Lojz`, `Lalt`, `Lt6f`.
  - `Locv.i0`: `Lero`, `Lxq7`, `Lchg`, `Lt67`.
  - `Larv.g`: два site `Lero` и один `Lt6f`.
- Впервые стало ясно, что просто найти путь `Lero.t → Lwq7(default) → Lmb4.a → Lha4.open/read/close` **НЕДОСТАТОЧНО**. Необходим **доказанный выбор экземпляра Lero** среди альтернатив конкретно для текущего трека. В противном случае возможна опасная подмена фонового/preload-источника.

**Исследовательский CI:**
- [Lemb exact sites #42826778879 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826778879).
- [Lemb source factory branch census #42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492).
- [Signed Lchg/Lciv/Lkvs/Locv source owners #42826990572 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826990572).

## 2. Новая независимая защита от ложного совпадения поколений

Создан в `android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeSourceInstanceFence.java` **pure-Java, OWN-ONLY модель**. Её **не подключали** к `NativeHookEntry` или плееру Яндекса. Никакой активной подмены.

Один активный generation и точная идентичность `Object`-ссылок (именно `==`, **не** `Object.equals`) отслеживаются для гипотетически **доверенных, независимо верифицированных** границ:

`selected source → source owner/reader → before-prepare descriptor → scheduled task → dispatched task → DataSpec.open → read → close`.

Свойства:
- Next, радио и повторный запуск создают новое поколение, старые task/open/read/close отклоняются как `STALE` без повреждения нового.
- Неправильный owner/source/task/spec блокирует текущую цепочку и очищает все сохранённые object references. Любые null/недостоверные объекты — fail closed.
- Смена источника **после prepare запрещена**; Pause не требует нового источника, Seek может открыть новый `DataSpec` **только в рамках того же источника** и без второй подготовки.
- Stop и откат монотонных часов отменяют наблюдение, не возобновляют старый источник.
- Снимок содержит только `phase`, `generation` и счётчики; не хранит / не раскрывает track ID, edition, URL, tokens, metadata и медиа. Внутренние ссылки живут лишь до отмены/смены поколения.
- `syntheticSequenceComplete` означает **только успешный искусственный набор событий**. Он никогда не доказывает player-selected receiver или декодер, **не даёт разрешения на AUDIO ALTERNATE**.

**Регрессии**:
- `tests/src/NativeSourceInstanceFenceTest.java`: **44 480 проверки после дополнительной регрессии**, в том числе 5 000 детерминированных циклов Next/радио, invalid source, повтор той же «песни», Stop, Seek+reopen, clock rollback, exact-reference против `equals()`.
- `tests/src/NativeSourceInstanceConcurrencyTest.java`: ещё **27 явных проверок**, плюс **4 800** намеренно запоздавших действий в параллельных потоках, 8 одновременных запросов pre-prepare (пропускается только один), гонка двух задач.
- JVM-tests подключены к read-only workflow `.github/workflows/android-native-yandex-hooklab.yml`, Android-module build остаётся отдельным 2/2 gate. Workflow дополнительно запрещает использование новой модели внутри `NativeHookEntry`.
- **Независимый настоящий ARM64 Linux-host**: `.github/workflows/android-native-source-instance-arm64-jvm.yml` собирает и запускает эти же тесты на `ubuntu-24.04-arm`, подтверждает `uname -m = aarch64`. Это **не Android runtime** и не ExoPlayer/decoder.
- [ARM64 Linux JVM #42828086262 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42828086262) (новейший), [предыдущая #42826864698 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826864698).
- [Синтетические Java tests + Android build #42826380279 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42826380279).
- [Новейший read-only Android module #42828086264 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42828086264); ранее [#42827236060 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42827236060).

## Дополнительная строгая регрессия после первого ARM64 прохода

Первоначальная модель позволяла `syntheticSequenceComplete=true` после успешного `open/read/close`, даже если раньше внутри **того же** поколения был `OUT_OF_ORDER`. Исправили: `rejectedCount==0` обязателен для complete; нет «отмывания» аномальных source-событий задним числом. Вызовы `STALE` от **старого** поколения намеренно не увеличивают `rejectedCount` нового. Это модель, а не реальное наблюдение аудио.

## 3. Непреодолённая граница: selected source / actual decoder / текущий track ID

**NO-GO к рабочему Android APK** до появления *настоящего* доверенного witness:

1. Какой из восьми `Lemb` реально выбран для текущего трека (не отложенный preload, кэш, радио-Next или старое поколение).
2. Связаны ли тот же объект, `trackId + edition + generation`, native `FileInfo` и выбранный `La58` внутри live плеера через coroutine/heap.
3. Совпадает ли этот источник с data source, переданным **реальному декодеру непосредственно до prepare**.
4. После этого — на отдельном **изолированном ARM Android** устройстве проверить одноисточниковость, Pause/Seek/Next/радио и обрывы. Нельзя переносить вывод из одного ARM64 Linux/JVM или Windows native PASS на Android.

Если такого изолированного Android-хоста нет, продолжать корректный source-only analysis и OWN-ONLY тесты, **не заявлять «заработало»**, не устанавливать на личный HONOR и не изменять Яндекс/DRM/подписи/Play Protect.

**Отдельно:** Test.50 остаётся защищённым эталоном. Фоновая подмена, mid-track переключение и второй `MediaPlayer` запрещены. Никаких изменений Windows 0.24.7, Chrome, API/БД, production. Не повторять провалившиеся x86 LSPatch/AppMetrica эксперименты.
