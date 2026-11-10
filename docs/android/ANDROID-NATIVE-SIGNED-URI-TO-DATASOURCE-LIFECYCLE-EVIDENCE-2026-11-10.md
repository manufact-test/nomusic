# CELIKOM Android — signed URI/model → source-factory → DataSource lifecycle (10.11.2026)

## Status / immutable checkpoint

**Signed original:** Яндекс Музыка 2026.10.3 #170gpr, 5 издательских split APK / 6 DEX / 230 533 method bodies. Только статическое READ-ONLY исследование в GitHub Actions. APK никуда не публикуется, не изменяется, не устанавливается; URL, строки, токены, аудио и личные данные в отчёт не экспортируются.

**Проверенный исследовательский исходник:** \`f327f5b9bcfee028e754f9a803f29ade347cb240\`.
**Точная резервная ветка:** \`backup/android-signed-uri-locv-source-cfg-green-20261110\` (создать только после зелёного CI этой точки).
**Предыдущее:** \`docs/android/ANDROID-NATIVE-SIGNED-DATASPEC-OPEN-SOURCE-EVIDENCE-2026-11-10.md\`.

### 1. Новый конкретный путь из URI в модель источника

Подписанный DEX содержит \`Locv.i0()\` (176 инструкций). Метод извлекает локальный источник типа \`Lwzi\` из собственного поля \`Locv\`, разыменовывает поле \`Lozi\` с URI-подобным объектом, далее:

1. \`Lw4y.z(Uri-like):Lglz\` — 186 инструкций, реально использует \`getScheme\`, \`getHost\`, \`getPathSegments\`, \`getQueryParameter\`; значения URI/параметров не считывались и не публиковались. Это структурно подтверждённый *парсер* URI, но не «наш» и не обязательно URL активного trackId.
2. Возвращённый \`Lglz\` регистрово достигает аргумента конструктора coroutine \`Llky.<init>\` внутри \`Locv.i0\` (CFG may-flow, не фактический resume).
3. \`Lfwm.M(Llky):Object\` вызывается в том же \`Locv.i0\`; результат \`move-result-object\` приводится к \`Ljgv\` (модель дорожки / источника).
4. Новый bounded register-CFG трассировщик после исправления DEX opcode semantics находит, что *тот же локальный регистр результата \`Lfwm.M\`* достигает **второго аргумента \`Lcq7.i0(Lxfs,Ljgv,Lacb)\`** и второго аргумента альтернативного \`Lcq7.D(...,Ljgv,...)\`. Эти переходы условны: синтетические branches/coroutine/select нуждаются в runtime-подтверждении.
5. Отдельно \`Lo4y.c(Lxfs,Ljgv,Lwzi)\` напрямую передаёт свой входной параметр \`Ljgv\` в \`Lcq7.i0\`.

Важно: DEX не устанавливает, что URI именно того трека, который **сейчас** звучит, что \`Ljgv\` содержит верный \`edition\`, либо что при crossfade/Next ещё актуально поколение запроса. Локальный static may-flow — это не end-to-end runtime proof.

### 2. Настоящий выход Lcq7.i0 — **обёртка**, а не Lga4!

В полном подписанном графе у \`Lcq7.i0\` ровно два прямых вызывающих метода:

- \`Lo4y.c\`: \`Lcq7.i0\` → \`move-result-object\` → \`iget-object\` из обёртки → \`check-cast Lga4\` → **условная** передача извлечённого поля в \`Lnro.<init>\`. \`Lnro\` наследует \`Le93\`.
- \`Locv.i0\`: \`Lcq7.i0\` → \`move-result-object\` → \`iget-object\` из обёртки → \`check-cast Lga4\` → **условная** передача извлечённого поля в \`Lero.<init>(Lwzi,Lga4)\`. \`Lero\` реализует \`Lemb\` и вызывает \`Lga4.c\` в перегруженном конструкторе.

**Критически исправлен старый аналитический false positive:** \`audit_native_typed_wrapper_coroutines.profile_tracked_results\` ранее убирал taint \`iget-object(0x54)\` через весь старший байт \`words[0] >> 8\`, хотя DEX 22c кодирует destination в нижнем nibble этого байта. Из-за этого код мог ошибочно утверждать, что *обёртка* напрямую передана конструктору. Исправлено на \`(words[0] >> 8) & 15\`. Добавлены регрессионные тесты: \`iget-object v1,v1\` **убивает объектное тождество**, тогда как \`move-object\` его сохраняет; \`const/4\` корректно убивает регистр; отдельный CFG наблюдатель помечает точную **проекцию поля** и путь в конструктор как условный.

Это не косметика. Прежний «доказанный» прямой объектный маршрут был НЕВЕРЕН; исправленный новый маршрут содержит настоящую heap-проекцию и ветвления. В результате нельзя перепутать URI-обёртку с \`Lga4\`.

### 3. От модели до реальной процедуры открытия байтов

Подтверждённые **локальные** signed DEX факты (по предыдущему и этому этапу):

- \`Lcq7.i0\` вызывает \`Lcq7.A(Leyc,Lthq):Luiq\`; \`move-result-object\` регистрово достигает **точного primary поля типа Le48 в Lga4** в пределах одного straight-line блока, без перезаписи.
- \`Lga4.d\` вызывает \`Le48.a():Lm48\`; результат достигает **argument word 3** конструктора \`Lha4.<init>\` в том же базовом блоке. Secondary Le48 — другой слот, нередко \`Lya4 → Lza4\`, и в ряде случаев кидает исключение вместо чтения. Нельзя подменять secondary вместо primary.
- \`Luiq.a\` лениво получает / кэширует \`Lm48\` через \`Lz3f\`; в \`Lz3f.a\` есть реальный вызов \`Lm48.b(La58):J\`. \`Lha4.f\` вызывает \`Lm48.b(La58):J\`; \`Lha4.read\` вызывает наследуемый \`Lv38.read([BII):I\`. \`Lm48\` реализует DataSpec-like API, унаследованный \`Lv38\` — read; классов-реализаций 33.
- \`Lga4.d\` создаёт \`Lha4\`; его другие методы \`b/c\` вызывают \`d\`. \`Lmir.t/remove\` используют \`Lga4.c/d\` и обёртки \`Lha4\`.
- В \`Locv\` методы \`t(Ldmb):void\` и \`remove():void\` **условно** вызывают \`Locv.i0()\` после \`Locv.j0()\`. Оба принадлежат lifecycle-классу, реализующему \`Lemb\`; \`Lero\` тоже реализует \`Lemb\`. Это связь со стадиями построения/пересоздания источника, **но смысл Media3 prepare и выбор живого receiver ещё НЕ доказаны**.

### 4. Что осталось недоказанным

Нельзя делать следующие выводы из одного статического графа:

- \`Locv\` выбран **текущим** Media3 ExoPlayer, а не фоновым/предзагруженным источником.
- URI, \`Ljgv\`, \`Lcq7.i0\` и \`Lha4\` относятся к **одному и тому же** \`trackId+edition+generation\` через корутину/кэш.
- \`Lha4\` реально дошёл до \`DataSource.open\` **перед** decoder prepare выбранного трека, без DRM, шифрования или другого независимого пути.
- Android CELIKOM уже заменяет звук. **НЕ заменяет.**

Поэтому **не подключать** \`NativeGrantContract\`, \`NativeReplacementLifecycle\`, \`NativePrePrepareAdmission\` и \`NativeSourceGate\` к декодеру; без native доказательства раннее включение даст старые Pause/Seek/«Раскол»/«Дым» регрессии. Windows native-fileinfo PASS подтверждён отдельно и не переносится на Android автоматически.

### 5. Исследовательские файлы и результаты CI

Создано:
- \`audit_native_source_factory_register_handoff.py\` + \`tests/test_native_source_factory_register_handoff.py\` + \`.github/workflows/android-native-source-factory-register-handoff.yml\`: точная запись \`Lcq7.A\` в первичный Le48, аргумент \`Lha4\` и полный signed direct caller census.
- \`audit_native_source_real_callers.py\` + \`tests/test_native_source_real_callers.py\` + \`.github/workflows/android-native-source-real-callers.yml\`: точные \`Lo4y/Locv\` callers, отдельная \`iget-object\`-проекция + ограниченный CFG, URI/корутинный вход в \`Ljgv\`, lifecycle \`Locv.t/remove\`.
- Улучшен \`audit_native_typed_wrapper_coroutines.py\` + тесты: исправлено декодирование регистра-приёмника \`iget-object\` и \`const/4\`.

Последние green run:
- [Source factory + lifecycle caller census #42819113120](https://github.com/manufact-test/nomusic/actions/runs/42819113120) — **SUCCESS**.
- [Signed wrapper/coroutine strict regression #42817633107](https://github.com/manufact-test/nomusic/actions/runs/42817633107) — **SUCCESS**.
- [Exact signed URI-model and i0 field projection #42819106641](https://github.com/manufact-test/nomusic/actions/runs/42819106641) — **SUCCESS**.
- [Read-only Android module at latest code #42819113420](https://github.com/manufact-test/nomusic/actions/runs/42819113420) — **SUCCESS 2/2**.

Следующий большой этап: вывести изолированный **пассивный** идентификатор связи URI / model / source-generation на границе actual DataSource.open и decoder prepare без URI, токенов, аудио или модификаций официального Яндекса; проверить, что \`Locv.t/remove\` относятся к реальному выбранному MediaSource, а не фоновому prefetch. Для runtime-части нужен **отдельный ARM-test host**, не пользовательский HONOR и не старый x86 LSPatch. Если реальный preprepare не доказан, по-прежнему NO-GO к Android аудиоподмене.

**Запреты сохраняются:** Test.50, основной HONOR, установленный Яндекс, Windows 0.24.7, расширение, production, API, БД, подписи, DRM, Play Protect; без ChromaSync и обращений к Яндексу.
