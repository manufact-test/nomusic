# CELIKOM Android — publisher-signed FileInfo register / coroutine CFG witness

**10 ноября 2026, точный исследованный исходник:** Yandex Music 2026.10.3 #170gpr (5 издательски подписанных split APK / 6 DEX). Исследование выполняется **только read-only на одноразовом GitHub Actions runner**. Ни один APK Яндекса не изменён или опубликован, на устройство владельца ничего не ставилось.

## Повторяемый новый код

- android/native-yandex-hooklab/audit_native_register_bridge.py — считывает только сверенный оригинальный XAPK, повторно строит шести-DEX вызовный граф и анализирует реальные DEX инструкции у **точных** seed-methods и их непосредственных вызывающих методов.
- android/native-yandex-hooklab/tests/test_native_register_bridge.py — проверка форматов DEX 35c/3rc, object move, direct coroutine callers, условных ветвлений и уничтожения значений при перезаписи регистров.
- .github/workflows/android-native-register-bridge-audit.yml — независимый CI без модификации Яндекса, без скачивания/выгрузки медиаданных и без экспорта бинарников.
- [Новая CI-проверка оригинальных DEX #42806655214](https://github.com/manufact-test/nomusic/actions/runs/42806655214) — **SUCCESS**. Кодовая точка: 8b7bc64f89249e5434da739851bececce2adb121.

## НОВОЕ: точные структурные наблюдения (НЕ decoder proof)

1. Lhee;->a на двух реальных инструкциях вызывает конвертеры sw7.y0/z0, **оба раза есть move-result-object**. При ограниченном анализе путей регистр результата достигает вызова конструктора **Lxa7;-><init>**. Это уже более сильная зацепка, чем общий предок вызовов; сам Lxa7 пока не доказан как audio source.
2. Lged;->a **непосредственно вызывает Lhee;->a**. Полученный в move-result-object регистр при ограниченной CFG-пропагации может поступать в вызовы Leed;->a, Lta7;->c, Lwa7;->a и в return-object. Это **may-flow внутри одного тела метода**, не interprocedural, не edition/track proof.
3. Lfed;->invokeSuspend вызывает Lged;->a, результат может возвращаться из coroutine. Lgee;->invokeSuspend аналогично вызывает Lhee;->a. Lfqr;->invokeSuspend вызывает Lged;->a, но в пределах строго ограниченного CFG анализа **прямого использования возвращённого регистра не обнаружено**. Это не исключает передачи через поля coroutine state machine, callbacks, heap или интерфейс.
4. В Lfqr;->invokeSuspend присутствуют интерфейсные вызовы с обфусцированными целями Lcod;->collect, Leod;->emit (среди прочих). **Не доказано**, что они передают именно FileInfo или что их получатель — decoder. У исследуемого метода много других interface/coroutine вызовов, поэтому простое совпадение в методе ничего не разрешает.

## Границы строго фиксированы

- CFG-исследователь отслеживает **may-flow только известных объектных регистров**, ограничен 240 шагами / 8000 посещённых состояний на источнике. Не моделирует exception edges, switch payload, heap aliases, field spills, reflective/native calls, dynamic dispatch resolution, coroutine resume или то, какой конкретно трек воспроизводится.
- Поэтому даже найденный Leed;->a — **НЕ доказательство** реальной связки текущих trackId + edition + generation → decoder source before prepare. Поле decoder_preprepare_input_proven намеренно false. NativeGrantContract, NativeReplacementLifecycle, NativePrePrepareAdmission, NativeSourceGate **не подключались** к декодеру.
- Структурный путь заканчивается на обфусцированных Lxa7, Lta7, Lwa7 и coroutine state machine; ни Media3 datasource/decoder, ни конкретная decoded audio URI не сопоставлены. В официальном Android Яндексе CELIKOM аудио **не подменяет**; исходные CI не являются runtime-тестами.

## Инженерный приоритет

**Следующий полезный, а не синтетический шаг:** разобрать реальные типы/сигнатуры Lxa7 конструктора и использования, Leed;->a / Lta7;->c / Lwa7;->a, затем spills/resume Lfqr;->invokeSuspend и dispatch interface collect/emit на том же сверенном DEX. Сопоставлять точный объект с действительно создаваемым native Android datasource и decoder pre-prepare. Если статического значения недостаточно — только изолированная совместимая ARM Android-среда с законной возможностью read-only диагностики; не возвращаться к x86 LSPatch/AppMetrica, не обходить подписи/DRM/Play Protect.

**Нельзя менять:** принятый владельцем Test.50, его HONOR/официальный Яндекс, Windows 0.24.7, расширение, production/API/БД. Windows real audio PASS не равен Android audio PASS.
