# CELIKOM Android — exact Lero → Lmb4 → Lha4 callpath, CI GREEN (10.11.2026)

**Это только НОВАЯ нативная архитектура, не Test.50, не DynamicsProcessing и не второй плеер.**

## Контрольная точка

- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
- **Точный проверенный исходный SHA:** `6146109dd77352dbc73563c26dcaf1dfd6ff6c38`.
- **Точная резервная ветка:** `backup/android-native-lero-lmb4-ha4-signed-readonly-chain-ci-green-20261110` (указывает на этот же SHA).
- Бэкап перед началом этого блока: `backup/android-native-pre-exact-reader-execution-20261110` @ `a5252f7058c868191c0ff07837bef24efc873f8e`.
- [Сборка Android-модуля и все синтетические регрессии #42860807834 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42860807834).
- [Точная проверка **неизменённого подписанного оригинала** #42860839260 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42860839260). Исходник 2026.10.3 #170gpr: 5 split APK, 6 DEX, 230 533 тел методов; **все 7** фиксированных методов действительно определены, **ровно 1** поле типа `Lmb4` у `Lero`.
- Оба CI подтверждают **форму кода** и работу модели, **НЕ** наличие успешного hook внутри настоящего Яндекса и НЕ звучание.

## 1. Реальный предмет разработки, без возврата к старой схеме

Целевой путь оригинального нативного плеера:

`FileInfoDto → sw7.y0/z0 → eed` (точный оригинальный DEX)
→ *непроверенные корутины/фабрики* `Ljgv/Lcq7`
→ `Lkvs.A(zcb,gmb):emb` / `Lero.t(dmb)`
→ конкретное поле `Lero→Lmb4`
→ `Lmb4.a()`
→ `Lha4.b(La58)` (open)
→ `Lha4.read(byte[],int,int)`
→ `Lha4.close()`.

**Нельзя обозначать весь маршрут сплошной доказанной цепью.** Только отдельные прямые подписанные вызовы, фабрика, поле и методы доказаны статически. Вход текущего `trackId+edition+generation`, какой именно экземпляр `Lemb` выбран плеером, реальный native pre-prepare и декодер Яндекса НЕ установлены.

## 2. Что конкретно написано в native hooklab

- `HookSpec.findLeroReaderField`: точная проверка **единственного** нестатического `mb4` поля класса `ero`; отсутствующее или неоднозначное поле — fail closed, приватные строки, URL, токены не читаются.
- `HookSpec.findReaderExecution` и `findReaderSourceMethod`: точные `mb4.a():void`, `ha4.b(a58):long`, `ha4.read(byte[],int,int):int`, `ha4.close():void`, без приблизительных сигнатур.
- `NativeSourceDispatchWitness`: 16 слотов / 15 секунд для `Lkvs.A` factory result по точной reference identity `==`. Ровно та же `Lero` должна попасть в `t`, после чего по типизированному полю связывается с конкретным `Lmb4`; запоздавшие, снятые, чужие или несвязанные экземпляры не считаются. Логи — **только счётчики**.
- `NativeReaderExecutionWitness`: впервые выделен самостоятельный proof-of-nesting `Lmb4.a→Lha4.b/read/close`, только если фактические методы вызвались внутри **одного потока и одного стека** на **том же** `Lha4` объекте, `read` вернул положительное число байт и `a()` завершился нормально. При другом объекте, исключении, несовпадении потока, отсутствие положительного read или позднем callback событие не считается полной цепью. Референсы хранятся только на стеке выполнения `ThreadLocal` и удаляются в finally.
- `NativeHookEntry`: за `onAttached` exact signed host/version/classloader gate и Xposed `PROTECTIVE` observer добавлены *только наблюдательные* hooks. Оригинальные args/result, source/decoder, пользовательский звук не изменяются. Прежде чем `Lero.t` поставит асинхронную работу, её ссылка на `Lmb4` фиксируется (только типизированное поле, не данные). По завершении `Lmb4.a` записывается только счётчик полной цепочки, не сам объект/содержимое.
- `audit_native_runtime_hook_shapes.py`: отдельный целевой подписанный DEX preflight метода и поля, 5 синтетических reject-test, ни один байт оригинального приложения не изменён и не публикуется.

## 3. Тесты

- `NativeReaderExecutionWitnessTest`: 10 000 успешных синтетических цепочек + mismatch по `ha4`, закрытие без read, исключение, реэнтрантность, кросс-поток и поздние события.
- `NativeSourceDispatchWitnessTest`: синтетический `ero` с единственным `mb4` полем; проверка точной формы методов, совпадение reference из factory в `t` и `a`, отказ другого объекта того же класса, истечение 15 секунд и remove.
- Полный старый HookSpec/NativeSourceGate/TrackIdentity/Admission/Grant/SourceInstanceFence, защищённый scope модуль и Xposed сборка: SUCCESS.
- Подписанный исходный код Yandex DEX: точная форма target reader source methods **7/7** и `Lero→Lmb4` поле **1/1**, checksum/source pin SUCCESS.
- Тесты **не делают** source swap, не используют аккаунт и не дают акустического PASS.

## 4. Что именно НЕ готово

Это не инжекция в официальный Яндекс на HONOR и не рабочая мобильная CELIKOM Native. **Отдельное обычное Android-приложение из-за sandbox не может изменить скрытый источник звука другого APK.** Для исполняемого runtime witness нужен отдельно разрешённый **совместимый ARM Android host** с работающим in-process модулем и с настоящим publisher player, не только наш OWN host или эмулятор без Yandex. В прошлых попытках x86 LSPatch падал до модуля; отдельный Yandex clone сам завершался; их не повторяли. Android native source selection по-прежнему **NO-GO** до этого доказательства.

**Нельзя выдавать APK с read-only Xposed-модулем за работающий клиент.** Нельзя просто слить предыдущую Test.51 с этой веткой: Test.51 — эксперимент другого продукта со вторичным декодером; принятая Test.50 — неизменяемый эталон, они не решают инжекцию в настоящий Yandex.

## 5. Единственный следующий реальный допуск

1. Получить технически совместимый и разрешённый отдельный ARM Android host для настоящего Yandex native. Без отключения Play Protect, обхода подписи/DRM, подмены установленного оригинала на HONOR или доступа к учётным данным пользователя.
2. Пассивно получить последовательность реальных callbacks `Lkvs.A → Lero.t → owned Lmb4.a → Lha4.open/read/close`, подтвердить, что это **не preload**, и связать с тем же текущим `trackId + edition + generation` и объектом источника, который реально получает decoder до prepare.
3. Только после этого подключить давно написанные `NativePrePrepareAdmission`, `NativeGrantContract` и `NativeReplacementLifecycle` к **одному** родному плееру и сделать first-party alternative source/fallback. Без реального player selected witness подмена не включается.
4. Потом аккуратный ARM QA: пауза, перемотка «Дым» `39949113`, «Раскол» `42884423`, Next, радио, фон, Bluetooth и сертификат установки.

**Строгий scope:** Windows, browser extension, owner Test.50, Test.51, официальный HONOR/Yandex, API, БД, production, сервер, подписи, DRM и Play Protect не менялись.
