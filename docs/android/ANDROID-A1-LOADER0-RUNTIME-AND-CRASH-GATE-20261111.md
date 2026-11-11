> **Доказан следующий блокер:** [A/B на ARMv7-mirror в disposable emulator](ANDROID-A1-ARMV7-MIRROR-NATIVE-CRASH-GATE-20261111.md), CI [42980968489](https://github.com/manufact-test/nomusic/actions/runs/42980968489): прежнего dlopen Java error нет, но теперь Android `REASON_CRASH_NATIVE / status 11`, MAIN/UI NO-GO. Debuggerd cause investigation CI [42981555329](https://github.com/manufact-test/nomusic/actions/runs/42981555329) ещё надо проверить. Никаких изменений на HONOR, отдельная ветка бэкапа @ 89de4fd.

> **Подтверждённая причина (11.11.2026):** [EM_386 → EM_ARM в эмуляторном native bridge, CI 42980016274](ANDROID-A1-LSPATCH-NATIVE-BRIDGE-ELF-ROOT-CAUSE-20261111.md). LSPatch metaloader выбирает x86 .so при PackageManager ARMv7; Android linker ожидает ARM. Root cause экспериментального CRASH установлен, UI всё ещё FAIL. Ранее записанные ниже «причина неизвестна» относятся к более ранним прогонам. Backup: `backup/android-a1-elf-machine-mismatch-proven-20261111` @ `8da1b888308bf7531485cd40e4d98b1907982b72`. No bypass, no HONOR install.

# CELIKOM Android A1 — проверенные результаты LSPatch zero-bypass (11.11.2026)

## Доказанное

- CI 42912195579: официальные 5 split APK Яндекса и один отдельно подписанный клон одновременно установлены на disposable Android 11 (x86 с ARMv7 bridge). Данные шести DEX и трёх библиотек сохранены; прямой клон прекращает MAIN с EXIT_SELF(0).
- CI 42913442978: прямой клон прекращает MAIN даже в одиночку, без официального Яндекса. Соседство не является необходимой причиной.
- CI 42917410602: собственные signature-права клона без ослабления издательских прав не решают MAIN EXIT_SELF(0).
- CI 42919749078: однокомпонентный LSPatch loader с сигнатурным обходом строго 0 после безопасной перестройки ZIP layout проходит статическую проверку DEX и библиотек; am start -W зависал.
- CI 42975010817: с неблокирующим am start загрузчик LSPatch level=0 устанавливается как один APK; вместе с оригиналом (5 + 1) нет установочного конфликта. Android принимает намерение запуска, однако нет MAIN/UI, возникают am_crash и REASON_CRASH (не прежний EXIT_SELF). Диагностика AndroidRuntime показала UnsatisfiedLinkError (native-library error). Приложение НЕ РАБОТАЕТ.
- CI 42976444763: завершился ожидаемым **runtime FAIL**. Android logcat CRASH buffer строго ограниченный MAIN PID показал fatal_category=NATIVE_LINK; native_link_dlopen_failed=true; native_link_library_lspatch_named=true; lspatch_bootstrap_mentioned=true. Клон падает с liblspatch.so и в одиночку. Нет явного wrong-ELF/missing-library marker; точная первопричина неизвестна. Unit tests PASSED, сырые логи и секреты не публиковались.
- **CI 42977185868 (ПОСЛЕДНИЙ ПРОВЕРЕННЫЙ):** перепаковка с сохранением native ZIP page-alignment и завершающая строгая проверка **подписанного** APK прошли. Все четыре варианта liblspatch.so — armeabi-v7a (ELF32/EM_ARM=40), arm64-v8a (ELF64/EM_AARCH64=183), x86 (ELF32/EM_386=3), x86_64 (ELF64/EM_X86_64=62) — ZIP_STORED и **смещение данных % 4096 == 0**. 6 host DEX/3 host .so целы, sigBypassLevel=0, 1 clone и 5 official пакетов одновременно установлены. **MAIN всё равно REASON_CRASH / NATIVE_LINK / dlopen failed liblspatch.so; UI FAIL.** Workflow FAILURE именно из-за строгого native runtime, не из-за unit/static ABI проверки. Значит, простое ZIP page-alignment НЕ причина, его больше не «чинить». Причина может относиться к загрузке из контейнера, Android linker namespace, x86/ARMv7 native bridge либо особенностям LSPatch; это ГИПОТЕЗЫ без доказательств.

## Присланный ChromaSync APK — проверено офлайн

SHA256 4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d; внешнее имя app.chromasync.yamclone, вложенный origin.apk и LSPatch bootstrap, внутри нативный Яндекс 2025.10.4 #120.1rur (не наш 2026.10.3 #170gpr).
Конкурент настроен на sigBypassLevel=2. Такой обход подписи в CELIKOM НЕ включать. В ChromaSync внешние LSPatch библиотеки содержат ELF для 4 архитектур (ARMv7/ARM64/x86/x86_64), вложенный host имеет 16 native .so для 4 ABI. Наш исследуемый #170gpr содержит только 3 native .so. Различие ABI и разные версии запрещают бездоказательный перенос выводов.
Внешний ChromaSync всё ещё имеет непереименованный AppMetrica ContentProvider и НЕ является доказательством параллельной установки на пользовательском HONOR. Чужой APK/модуль/код не перенесены в наш репозиторий.

## Инженерный вывод

В direct clone ошибка EXIT_SELF(0), в эксперименте с LSPatch zero-bypass ошибка Android REASON_CRASH + UnsatisfiedLinkError. Это два разных блокера. На x86 эмуляторе с ARMv7 трансляцией нативный загрузчик может падать из-за ABI/native-bridge. НЕ утверждать, что это происходит на настоящем ARM64 HONOR без evidence.

Следующий разработчик: сначала посмотреть закрытый результат CRASH buffer, определить конкретно было ли liblspatch.so, неверный ELF класс, missing native library или другая причина; затем исправить только доказанное. Не бесконечно крутить упаковку, разрешения и подписи. Проверять строгий MAIN/Activity resumed/window focus на disposable Android до owner APK.

## Ограничения и точка отката

Владелец тестирует на ЕДИНСТВЕННОМ HONOR 50 NTH-NX9 Android 13. Второй телефон НЕ обязателен. Оригинальная Яндекс.Музыка не удаляется и не изменяется; Play Protect всегда ON; APK для HONOR НЕТ до рабочего native MAIN/UI и проверенной независимой установки. Логин, звук, entitlement, trial, платежи и Play Protect НЕ проверены. Никакого WebView и второго аудиодвижка.
Точная предыдущая точка отката backup/android-a1-loader0-pre-crashbuffer-diagnostics-20261111 @ 7a335eaca0e4b55a6d1cf91f1e24ff680544e374.
Замороженный Test.50 backup/android-test50-exact-source-owner-accepted-20261106 @ 5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1; Windows audio backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110 @ 44e69d78b459ed512862819280ebdb8b3dbc7e7d.

**Обязательное напоминание о Stage B:** как только LSPatch A1 реально работает (слышимое аудио, пауза/seek/Next/MyWave) и принят владельцем с точным бэкапом, напомнить начать собственный инжектор вместо LSPatch. Сейчас до этого этапа НЕ дошли.

CI: https://github.com/manufact-test/nomusic/actions/runs/42975010817
New scoped CI: https://github.com/manufact-test/nomusic/actions/runs/42976444763
Repo: https://github.com/manufact-test/nomusic