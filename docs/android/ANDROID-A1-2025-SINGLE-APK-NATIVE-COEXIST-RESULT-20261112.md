# CELIKOM Android A1 — единственный LSPatch2 APK рядом с оригинальным Яндексом: реальный ARM13 (12.11.2026)

## Главное

**Структурная сборка одного APK CELIKOM и его одновременная установка со штатным издательским Яндексом на Android13 ARM64/ARMv7 ДОКАЗАНЫ.** Реальный MAIN нативной копии **пока не запускается стабильно**: Java `IllegalStateException` в коде приложения Яндекса, только 1/25 Activity RESUMED. **Stage A NO-GO, Stage B LOCKED, музыки и пользовательской APK пока нет.**

### Источники и сохранённые контрольные условия

- Подлинный ранее загруженный в **неопубликованный Draft Release** Yandex Music **2025.10.4 #120.1gpr**, 16 splits, полный XAPK SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45 961 661 байт. Заново у владельца ничего не запрашивать, не выпускать исходники бинарей в публичные артефакты.
- PIN upstream LSPatch v1.2-487 `-l 2`. **Подписанная издателем оригинальная base.apk подана в LSPatch ПЕРВОЙ**, до независимой подписи: это проверенно важное условие ранее успешного оригинал-name MAIN native 75s [43191788591](https://github.com/manufact-test/nomusic/actions/runs/43191788591). Чужой модуль ChromaSync не использован.
- Сохранён исходный байтовый payload `assets/lspatch/origin.apk` и loader/config assets при переносе во внешний пакет с независимым namespace `pro.celikom.yandex.nativeclonelab`; 16 independently signed split APK собраны в один, одинаковая собственная одноразовая подпись. Осмысленные clone-only manifest корректировки: 5 global provider, 7 scoped provider, одна duplicate signature permission declaration. Издательский оригинал не менялся.

### Реальный CI

**[43199953381](https://github.com/manufact-test/nomusic/actions/runs/43199953381)**, ветка `experiment/android-a1-2025-singleapk-publisher-base-lspatch2-20261112` @ `7523e1bc22988dc00e229767bba1c3b678bd56fe`:

1. Exact private source SHA и signer 16/16: PASS. Отдельная ветка, ARM Android 13 ephemeral.
2. `single_apk_structural=true`, `source_split_count=16`, `output_count=1`, `publisher_input_nested_origin_preserved=true`, `all_signed_loader_abis_page_aligned=true`: PASS. 16 native .so в outer; 1 внешний stub DEX (host DEX остаётся внутри исходного origin).
3. `clone_install=INSTALLED` (1 APK); `publisher_install=INSTALLED` (16 оригинальных APK). Одновременная установка двух независимых приложений: PASS.
4. Native MAIN CELIKOM `stable=false`, `resumed_observations=1/25`, `JAVA_CRASH / ILLEGAL_STATE`, первый frame `YANDEX_APP`, маркера `SIGNATURE` в первом исключении нет. **Fail**, даже после сохранения publisher-signed LSPatch input + объединения в один APK.

**[43199178247](https://github.com/manufact-test/nomusic/actions/runs/43199178247)**, другая изолированная ветка `experiment/android-a1-independent-sig-compat-arm13-20261112`: тоже 16->1 APK, clone+original concurrently installed; обе версии LSPatch level0 и level2 runtime `JAVA_CRASH / ILLEGAL_STATE` на **NON_MAIN** thread, resumed 1/25. Но там входом в LSPatch был уже own-signed merged host, поэтому это НЕ тот же causal construction, что 43199953381.

## Последняя причинная граница

Доказано отдельно:
- Оригинальный package name + publisher-input -> LSPatch2 -> independently signed 16 split MAIN 75s: **PASS** [43191788591](https://github.com/manufact-test/nomusic/actions/runs/43191788591).
- Независимое имя CELIKOM и официальный Яндекс одновременно установлены; даже один LSPatch2 APK с genuine publisher-signed input всё ещё **JAVA_CRASH** [43199953381](https://github.com/manufact-test/nomusic/actions/runs/43199953381).

Следующая инженерная задача не «заново включить -l2», а **найти конкретный clone-namespace Java app-init invariant** в non-main crash. Начинать с изолированной read-only диагностики конкретной исходной нитки и первого исключения, сравнения штатных package/context/provider flows; никаких скачиваний неизвестного latest, новых 16/16 переподписей ради зелёных счётчиков и переноса B42 до стабильного native MAIN. Не публиковать raw stack, vendor classes, аккаунты или proprietary bytes. Источник audio B42 готов отдельно, но ни нативного декодера, ни MyWave, ни музыки пока не проверяли.

**Ничего не трогали:** пользовательский HONOR 50, установленный оригинальный Яндекс, эталон Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`, frozen A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`, Windows/Chrome/backend/prod. Отдельный точный backup перед новым single-APK тестом: `backup/android-a1-2025-singleapk-publisher-input-experiment-pre-runtime-20261112`.

Реального consumer CELIKOM APK нет, Stage A NO-GO, Stage B LOCKED. #41 остаётся открытым.
