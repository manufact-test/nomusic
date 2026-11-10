# CELIKOM Android — подтверждённая статическая цепочка Lero → Lmb4 → DataSource.open/read/close

**10 ноября 2026. Переход от фабрик источника к созданию, планированию и чтению байтов (только подписанный DEX, READ-ONLY).**

## Контрольная точка

- **Ветка:** \`experiment/android-native-yandex-fileinfo-hooklab-20261109\`
- **CI-проверенный исходный код:** \`f04745f7dcd4455996eadf56dc0be6c52a44c63f\`
- **Бэкап для точного отката:** \`backup/android-signed-lero-lmb4-reader-case-ci-green-20261110\` (создана, указывает на точный CI green SHA)
- **Оригинальный объект исследования:** неизменённый издательски подписанный Yandex Music 2026.10.3 #170gpr, 5 APK, 6 DEX, 230 533 тела методов.
- **Ранее найденный вход:** \`docs/android/ANDROID-NATIVE-SIGNED-URI-TO-DATASOURCE-LIFECYCLE-EVIDENCE-2026-11-10.md\`.

**Сводный результат:** реально наблюдаемые инструкции DEX связывают **\`Lga4.c → Lero.<init> → Lmb4.<init> → Lmb4.a → Lha4.b/read/close → Lm48.b(La58)/Lv38.read([BII)\`**, а конкретный режим синтетического обработчика \`Lwq7\` отправляет именно **\`Lero.t → Lmb4.a\`**. Это точное **СТАТИЧЕСКОЕ** доказательство формирования и планирования источника, но НЕ runtime-доказательство того, что он выбран текущим плеером, тем более не доказательство успешной замены CELIKOM.

## Доказательства по шагам

1. \`Locv.i0\` в оригинальном signed DEX получает из URI-подобной модели \`Ljgv\`, передаёт её в \`Lcq7.i0\`. Возвращённая обёртка распаковывается посредством \`iget-object\` + \`check-cast Lga4\`, затем **условно** передаётся \`Lero.<init>(Lwzi,Lga4)\`. Вторая возможная ветка \`Lo4y.c\` идёт в \`Lnro\`, не гарантируя выбора \`Lero\`. Проверка \`iget-object\` теперь корректно *убивает прежнюю identity-taint обёртки*.
2. **Именно трёхаргументный** \`Lero.<init>(Lwzi,Lga4,...)\` содержит \`Lga4.c():Lha4\`, немедленный \`move-result-object\`, запись возвращённого объекта в поле \`Lero\` типа \`Lha4\` и передачу **того же локального регистра** в **argument word 1** \`Lmb4.<init>(Lha4,La58,[B,Llb4)\`. Между вызовами в проверенном basic block нет условного перехода/перезаписи регистра; это сильнее общей близости графа.
3. \`Lero\` сам конструирует \`La58\` (DataSpec-like) из URI-подобных полей и создаёт \`Lmb4\`; сохраняет его в отдельном поле типа \`Lmb4\`.
4. \`Lmb4.<init>(Lha4,La58,[B,Llb4)\` кладёт конкретный первый параметр (p1) в **точное поле \`Lmb4\` типа \`Lm48\`**, не в похожее поле. В \`Lmb4.a\` видно чтение именно **того же DEX field-ref**, приведение к \`Lha4\` и два обращения \`Lha4.b(La58)\`. Класс \`Lmb4\` имеет и *другой* конструктор, принимающий \`Lmq7\`, поэтому метод содержит условные пути, и всем экземплярам приписывать \`Lha4\` запрещено.
5. В \`Lmb4.a\` (251 DEX instruction, 30 ветвлений) реальные подписанные вызовы: \`Lha4.b\` на ordinal 105 и 120, \`Lha4.read\` на ordinal 162, \`Lha4.close\` на ordinal 238. Все четыре **callsite используют регистр v8 как receiver**, но это не гарантирует, что на каждой runtime-ветви он держит тот же объект. Сам \`Lha4.read\` действительно вызывает \`Lv38.read([BII)\` на полученном \`Lm48\` и при некоторых путях вызывает \`Lha4.d/f\`.
6. **Ключевой контроль синтетического async switch:** \`Lero.t\` создаёт \`Lwq7\` с фиксированным int mode и передаёт **собственный \`Lero.this\`** третьим word аргумента конструктора. \`Lwq7.<init>(I,Object)\` сохраняет mode в int поле и \`Lero.this\` в точное object поле. \`Lwq7.e\` читает **те же два поля**, исполняет DEX **packed-switch**, причём режим, переданный \`Lero.t\`, **отсутствует среди двух явных case keys** и тем самым **идёт по DEX default fallthrough**. В этом конкретном default-блоке сделано \`iget-object Lwq7 → check-cast Lero → iget-object Lero.Lmb4 → invoke Lmb4.a()\`. **Именно эта ветка, а не любая другая callback-ветка, структурно привязана к Lero**. Проверено декодированием оригинального switch payload, регистра константы, двух точных field-ref и instruction target. Ранее ошибочный вывод «нет case → значит путь не работает» исправлен.
7. \`Lero.t\` отдаёт \`Lwq7\` в \`execute(...)\` исполнителя и обращается к \`get()\`, но **статический вызов execute/get не является записью факта исполнения на устройстве**. \`Lwq7.e\` может иметь другие switch-варианты и это нельзя игнорировать.
8. Среди других непосредственных вызывающих \`Lmb4.a\` также обнаружены \`Llir.e\` (отдельная ветка callback) и \`Loi.invokeSuspend\` (1368 инструкций / большой coroutine switch), **смешивать эти потоки или приписывать их активному trackId нельзя**.
9. \`Lero.remove\` делает обращения к наблюдательным callback-объектам из своего \`Lha4\`/DataSpec; \`Locv.t/remove\` условно запускают \`Locv.i0\`. Прерывание/отмена жизненного цикла **не доказывают** сброс прежнего поколения трека до нового \`DataSource.open\` и не гарантируют корректность Pause/Seek.

## Файлы и CI

**Новые исследовательские скрипты (без изменения runtime hook):**

- \`android/native-yandex-hooklab/audit_native_datasource_read_lifecycle.py\` — оригинальные вызовы source/open/read/close, загрузчик \`Lmb4.a\`, его callers и lifecycle \`Lero/Locv/Lmir\`; тесты \`tests/test_native_datasource_read_lifecycle.py\`; \`.github/workflows/android-native-datasource-read-lifecycle.yml\`.
- \`android/native-yandex-hooklab/audit_native_lero_async_case.py\` — точные packed/sparse switch table, default fallthrough, int mode, field capture \`Lero.this\` и direct call \`Lmb4.a\`; тесты \`tests/test_native_lero_async_case.py\`; \`.github/workflows/android-native-lero-async-case.yml\`.
- \`android/native-yandex-hooklab/audit_native_lero_loader_field_identity.py\` — DEX field-ref и конструкторная передача \`Lga4.c → Lero → Lmb4\` и локальное использование источника; тесты \`tests/test_native_lero_loader_field_identity.py\`; \`.github/workflows/android-native-lero-loader-field-identity.yml\`.

**Успешные проверки на оригинальном signed APK:**

- [Потребитель DataSource и lifecycle #42821377729](https://github.com/manufact-test/nomusic/actions/runs/42821377729) — SUCCESS
- [Точный режим Lero / Lwq7 и captured object #42822722957](https://github.com/manufact-test/nomusic/actions/runs/42822722957) — SUCCESS
- [Точное поле Lero / Lmb4 / Lha4 #42823360505](https://github.com/manufact-test/nomusic/actions/runs/42823360505) — SUCCESS
- [Android read-only module на code checkpoint #42823360398](https://github.com/manufact-test/nomusic/actions/runs/42823360398) — **SUCCESS 2/2**

Все 3 скрипта используют pinned publisher hash, read-only проверку подписи, временные каталоги и ограниченное структурное описание; ни одного vendor APK не патчили и не публиковали. Ошибки синтетических тестов и чрезмерно широкого выбора конструктора в процессе исследования устранены. Не считать промежуточные красные workflow текущей рабочей точкой.

## Оставшийся барьер

**НЕ УСТАНОВЛЕНО**: фактически выбранный объект \`Lero\` принадлежит **активному** треку, а не preload/crossfade/фоновой задаче; его \`La58\`, \`Ljgv\`, \`FileInfo\`, \`trackId\`, \`edition\`, \`generation\` — один и тот же жизненный цикл через lazy/coroutine; \`Lmb4.a\` исполняется на устройстве при decoder prepare конкретно выбранного ExoPlayer. **Работающая Android-аудиоподмена отсутствует.**

Следующий этап: отдельная изолированная ARM Android runtime-среда, только пассивная (без пользовательского аккаунта/секретов/аудио и без вмешательства в DRM/signature). Получить **только обезличенные, локальные** correlation IDs source instance → callback → DataSpec.open → prepare, проверить Next/Seek/Radio/crossfade и расхождение поколений. До реального player-selected runtime witness **НЕ включать** \`NativeSourceGate\`, \`NativeGrantContract\`, \`NativeReplacementLifecycle\` и \`NativePrePrepareAdmission\`; не выдавать рабочий APK на эту базу.

**Не трогать Test.50, HONOR владельца, официальный Яндекс, Windows 0.24.7, browser extension, production/API/БД, подписи/DRM/Play Protect.** Старый x86 LSPatch/AppMetrica не повторять; ChromaSync не предлагать.
