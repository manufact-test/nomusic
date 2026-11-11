# Android A1 — доказана точная причина dlopen в x86↔ARMv7 эмуляторе (11.11.2026)

**Статус: ROOT CAUSE CONFIRMED FOR EMULATOR; native MAIN/UI всё ещё FAIL; никакого пользовательского APK.**

## Доказательства (строго из реального эмуляторного CI)

**CI [42980016274](https://github.com/manufact-test/nomusic/actions/runs/42980016274), HEAD 8da1b888308bf7531485cd40e4d98b1907982b72:** безопасный классификатор Android CRASH buffer по точному MAIN PID вывел:

```json
"native_link_failure_mode": "ELF_ARCH_INVALID",
"native_link_machine_mismatch": {"seen": true, "actual": "EM_386", "expected": "EM_ARM"},
"native_link_path_family": "ZIP_ASSET_LOADER",
"native_link_dlopen_failed": true,
"fatal_category": "NATIVE_LINK"
```

- Ошибка идентична для одиночного независимого клона **до установки оригинала** и в тесте coexistence, поэтому конфликт с официальной установкой **не является причиной именно этого аварийного отказа**.
- Android PackageManager для оригинала и нашего независимого экспериментального клона сообщает **primaryCpuAbi=armeabi-v7a**; Android 11 x86 emulator также содержит `x86`, `armeabi-v7a`, работающий native bridge и `ro.dalvik.vm.isa.arm=x86`. Эмулятор переводит ARMv7-код в x86.
- Из [CI 42977185868](https://github.com/manufact-test/nomusic/actions/runs/42977185868): подписанный APK содержит все 4 корректные библиотеки `liblspatch.so` (EM_ARM/EM_AARCH64/EM_386/EM_X86_64), uncompressed, каждая 4096-aligned. Значит **неисправность не в отсутствующей архитектуре, ошибке ZIP page alignment или подписи упаковщика**.
- По проверенным исходникам **JingMatrix/LSPatch v1.2** `meta-loader/.../LSPAppComponentFactoryStub.java` выбирает `archToLib` по `VMRuntime.vmInstructionSet()` и запускает `System.load` прямо по пути `base.apk!/assets/lspatch/so/<abi>/liblspatch.so`. В ARMv7-приложении на x86 ARM bridge это может выбрать x86 `EM_386`, хотя native bridge требует `EM_ARM`. Реальный Android linker теперь доказал именно такую несовместимость ELF. Это **подтверждение ошибки этого эмулятора/текущего loader0**, а **не заключение** о поведении на физическом ARM HONOR 50.
- Unit/classifier suites — PASS. Workflow намеренно **FAIL**, поскольку MAIN/Activity resumed/focused window не получен. Исходный `EXIT_SELF(0)` прямого клона остаётся отдельным возможным блокером даже после исправления загрузчика.

## Что делать дальше

1. **Не повторять** ZIP repack, signature permissions, ZIP-align, замену сертификата либо отключение Play Protect. Root cause установлен.
2. Исправить **только исследовательский LSPatch metaloader ABI selection** под ABI, назначенный Android процессу (`ApplicationInfo.primaryCpuAbi` или эквивалентный проверенный механизм), а не x86 ISA машины-транслятора. Использовать только pinned upstream GPL-3.0 source на изолированном CI, `sigBypassLevel=0`, никаких модулей конкурента/обхода подписи. При неизменной трансляции протестировать именно `EM_ARM` loader. Зафиксировать SHA и source/compiled parity; если это недоступно — честно удержать NO-GO.
3. Строгий runtime gate: **не просто прошёл dlopen**, а живой MAIN, `Activity resumed`, `window focused` для clone, работающий original control и независимая установка 5+1. Затем read-only hook собственными силами, после доказательства — source/decoder и аудиотесты.
4. Если эмуляторный ARM bridge в принципе не поддерживает LSPatch JNI после выбора правильной ELF, не делать ложный вывод об ARM HONOR. Проверить другой честный disposable native-ARM стенд / поддерживаемый ARM-runtime; телефон владельца **не трогать до выполнения agreed security/native UI gate**.
5. Без sig bypass/Passport/DRM; без публикации login, URL, токенов или бинарников сторонних APK; не трогать Test.50/Windows/extension/backend/production.

## Контрольные точки

- Исходная ветка перед работой: `backup/android-a1-loader0-dlopen-4abi-alignment-final-handoff-20261111`.
- Отдельный pre-diagnostics backup: `backup/android-a1-loader0-before-linker-cause-matrix-20261111` @ `248f081c166dc5e34800d2b3fd419515dabcecf7`.
- Точный код с доказанной причиной: `backup/android-a1-elf-machine-mismatch-proven-20261111` @ `8da1b888308bf7531485cd40e4d98b1907982b72`.
- Диагностическая лестница: [42978775074](https://github.com/manufact-test/nomusic/actions/runs/42978775074) (ZIP_ASSET + UNKNOWN) → [42979464115](https://github.com/manufact-test/nomusic/actions/runs/42979464115) (PackageManager ARMv7 и allowlisted linker terms) → **[42980016274](https://github.com/manufact-test/nomusic/actions/runs/42980016274) (EM_386 versus EM_ARM доказано)**.
- **Stage B REMINDER:** только когда владелец *услышал* работающую замену в native LSPatch, принял все pause/seek/Next/MyWave тесты и зафиксирован точный эталон, отдельным сообщением предложить собственный инжектор вместо LSPatch. Сейчас Stage B ещё не начался.
