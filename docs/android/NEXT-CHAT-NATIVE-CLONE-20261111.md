> **ДОКАЗАНА ГРАНИЦА ЭМУЛЯТОРА (11.11.2026):** [OWN ARMv7 vs native x86 control — CI 42982872899/42983717005](ANDROID-A1-OWNED-ARMV7-NATIVEBRIDGE-VS-NATIVE-X86-AB-20261111.md). Без Яндекса ARMv7 через NativeBridge + LSPatch `sigBypass=0` падает с `SIGSEGV` (LIBART/NativeBridge), тогда как native x86 LSPatch на том же API30 загружается и запускает Activity. Прекратить бессмысленные x86↔ARMv7 прогоны, следующий gate — **настоящая ARM Android среда** и OWN-only in-process, затем native clone, и только потом аудио. Ни Play Protect, ни телефон, ни Test.50 не изменяли. Backup `backup/android-a1-owned-armbridge-fails-native-x86-pass-20261111` @ `d305f32dabb4e4209d2fa3fbf51bd55edec09db4`. Рабочего CELIKOM APK пока НЕТ.

> **FINAL VERIFIED NATIVE CRASH WITNESS 11.11.2026:** [CI 42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329) on single clone and 5+1: **SIGSEGV** in MAIN, exact debuggerd victim PID matched; first native frame class **LIBART**, subsequent stack includes **NATIVE_BRIDGE**. `UnsatisfiedLinkError / dlopen failed` is absent after CI-only ARMv7 resource mirror. FULL MAIN/UI STILL FAIL, no phone/user audio tests. These frames implicate emulator JNI/ART/native-bridge execution but do **not** prove which component is defective or predict physical HONOR behavior. Do not ship mirrored resource APK. [Evidence report](ANDROID-A1-ARMV7-MIRROR-NATIVE-CRASH-GATE-20261111.md).

> **Текущий checkpoint 11.11.2026:** [ARMv7-mirror CI 42980968489](https://github.com/manufact-test/nomusic/actions/runs/42980968489) устранил наблюдавшийся `dlopen failed / EM_386 vs EM_ARM`, но обнаружен **новый `REASON_CRASH_NATIVE`, status 11; native UI FAIL**. [Точный протокол и ongoing tombstone CI 42981555329](ANDROID-A1-ARMV7-MIRROR-NATIVE-CRASH-GATE-20261111.md); CI-ONLY emulation, no HONOR APK, no spoofing/signature bypass. Backup `backup/android-a1-emulator-armv7-mirror-native-crash-gate-20261111` @ `89de4fd6d0d58a2fcde51f44e034a91001a5b481`. Всё ниже о простом `UnsatisfiedLinkError` — исторические результаты до подтверждённого ABI-mirror A/B.

> **СВЕЖИЙ VERIFIED CHECKPOINT 11.11.2026:** корневая причина `dlopen` установлена: [CI 42980016274](https://github.com/manufact-test/nomusic/actions/runs/42980016274), `EM_386` (x86 lib) при ожидаемом `EM_ARM` (ARMv7 process/bridge). Сначала читай [ROOT CAUSE AND NEXT ABI FIX](ANDROID-A1-LSPATCH-NATIVE-BRIDGE-ELF-ROOT-CAUSE-20261111.md). Все последующие исторические формулировки «неизвестно» устарели. Рабочего native UI/звука пока нет, владелец HONOR не тестирует. Backup `backup/android-a1-elf-machine-mismatch-proven-20261111` @ `8da1b888308bf7531485cd40e4d98b1907982b72`.

# ПЕРВОЕ СООБЩЕНИЕ ДЛЯ СЛЕДУЮЩЕГО ЧАТА — CELIKOM Android native A1 (11.11.2026)

[$github](app://connector_76869538009648d5b282a4bb21c3d157)

Привет! Продолжаем **CELIKOM Android**. Ты новый ведущий разработчик. **Не начинай с нуля, не переключай архитектуру, работай крупными самостоятельными блоками.** Пользователь одобрил тестирование на своём единственном HONOR 50 после безопасного доказательства параллельной установки; второго телефона не требовать.

**Repo:** manufact-test/nomusic
**Активная исследовательская ветка:** experiment/android-native-a1-lspatch-clone-loader0-20261111
**Сначала прочитай в GitHub:**
- docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md — утверждённый master, главнее всего;
- docs/android/ANDROID-A1-LOADER0-RUNTIME-AND-CRASH-GATE-20261111.md — актуальная фактическая диагностика;
- docs/android/ANDROID-A1-UPLOADED-CHROMASYNC-RESEARCH-AND-TESTS-20261111.md — разбор реально присланного конкурентного APK;
- docs/android/ANDROID-A1-CHROMASYNC-APK-OFFLINE-COMPARISON-20261111.md — технический разбор metaloader и signature;
- android/native-yandex-hooklab/README.md и этот NEXT-CHAT, затем код и CI.

## Утверждённая цель

**Один независимый APK CELIKOM, внутри которого настоящая нативная Яндекс.Музыка с её UI, авторизацией, библиотекой, MyWave и штатным единственным плеером.** CELIKOM заменяет только разрешённые аудиоисточники внутри штатного decoder pipeline. Никакого WebView, второго проигрывателя, расхождения таймингов или замены на свой интерфейс. LSPatch — **исследовательский этап A**, потом собственный injection adapter в этапе B.

## Реально сделано и доказано

1. Пять publisher-signed split APK оригинального Yandex 2026.10.3 #170gpr и **один** separately signed experimental clone APK pro.celikom.yandex.nativeclonelab одновременно устанавливаются на disposable Android 11 x86+ARMv7 bridge. Оригинал работает. 6 DEX и 3 native .so клона сохраняют SHA256. CI 42912195579 и 42913442978.
2. Прямой независимый клон MAIN завершается EXIT_SELF(0), иногда отмечен IllegalStateException; без оригинального Яндекса он также не запускается. Отдельная проба с собственными signature-permissions не помогла (CI 42917410602). Не повторять пустую перепаковку.
3. Владелец заново прислал **ChromaSync-Clone-3.0.1.apk**, проверен по реальным байтам SHA256 4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d. Там иной Яндекс 2025.10.4 #120.1rur, outer stub + embedded origin.apk, LSPatch+модуль и **sigBypassLevel=2**. Чужой модуль/код не переносили; обход подписи **не разрешён**. В competitor 4 ABI LSPatch, 4096 alignment; его сосуществование с оригинальным Яндексом не доказано.
4. Реализована собственная лабораторная независимая метаобёртка на pinned upstream LSPatch v1.2-487 **sigBypassLevel=0**, без music-module и без издательской подписи, с repair только ZIP-layout, неизменными 6 DEX/3 libs, своей lab-подписью. CI 42975010817: intent запуска принят, но MAIN/UI не работает; теперь Android фиксирует **REASON_CRASH** вместо EXIT_SELF.
5. Последний большой заход: отдельный scoped **Android CRASH buffer** (не только main buffer) доказал **UnsatisfiedLinkError / dlopen failed, именно liblspatch.so** в MAIN PID даже когда клон установлен один (CI 42976444763). Не обнаружены explicit wrong-ELF и missing-library markers; root cause всё ещё не доказана.
6. **Последний подтверждённый CI 42977185868:** ZIP-восстановление с сохранением 4096 alignment и проверки всех **четырёх ELF ABI** в конечном ПОДПИСАННОМ APK завершились успешно (armeabi-v7a/arm64-v8a/x86/x86_64: верная ELF class+machine, ZIP_STORED, offset%4096=0). **Но MAIN всё равно падает** с NATIVE_LINK / dlopen failed на liblspatch.so даже в одиночку. Workflow FAILURE вызван жёстким native UI gate. Гипотеза о кривом выравнивании исключена; не трать новый цикл на перепаковку. Причина может быть в загрузчике/линкере/эмуляторном ARM bridge — пока не доказана.

## Точные границы

- Временная версия native A1 НЕ воспроизводит музыку, НЕ прошла вход, замену, pause/seek/Next/MyWave, 3-дневный trial и Play Protect. **Нет готового для пользователя APK.** Не выдавай unit PASS или установку за рабочий плеер.
- Основной HONOR 50 NTH-NX9 Android 13. Официальную Яндекс.Музыку не удалять и не обновлять от нашей подписи; Play Protect не выключать; никакой установки на телефон без безопасного отдельного native MAIN/UI и строгой проверки. Другой телефон НЕ обязателен.
- Ни signer spoof, ни LSPatch sigBypass 1/2, ни обход Passport/DRM, ни копирование чужого модуля. Не трогать production, server, stable Android, Test.50, Windows и расширение.
- Принятый Test.50 backup/android-test50-exact-source-owner-accepted-20261106 @ 5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1. Windows backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110 @ 44e69d78b459ed512862819280ebdb8b3dbc7e7d.
- Точка до нового crash-buffer: backup/android-a1-loader0-pre-crashbuffer-diagnostics-20261111 @ 7a335eaca0e4b55a6d1cf91f1e24ff680544e374. Обязательно сделай ещё отдельный backup перед новыми рискованными правками.

## Что делать дальше

**Первое:** разберись в итоговой проверке подписанного APK: liblspatch.so все четыре ELF ABI, STORED и data offset % 4096 == 0; сравни отдельно с Android x86+ARMv7 bridge и native ARM, пойми конкретно, почему dlopen возвращает ошибку. Не выводи причинность из одного маркера. Переходи к нативному UI только если loader реально стартовал. Дальше собственный read-only CELIKOM hook, затем single-clock audio source, пауза/seek/Next/MyWave, а не очередные маленькие фиксы.

**ОБЯЗАТЕЛЬНЫЙ REMINDER:** когда владелец реально примет работающий слышимый LSPatch A1 и точный backup, сам напомни: «Эталон CELIKOM на LSPatch готов и сохранён. Теперь можем начать собственный механизм внедрения вместо LSPatch — этап B». Пока рано.

Общайся по-русски, кратко. Большие самостоятельные заходы; отчёт только по реально сделанному/проверяемому. Не теряй точные ветки, SHA, CI и бэкапы.