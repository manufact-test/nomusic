# CELIKOM Android — подписанный FileInfo → типизированные модели → интерфейсы / media candidate (10.11.2026)

**Только READ-ONLY доказательства из неизменённого издательски подписанного Яндекса Music 2026.10.3 #170gpr:** 5 APK / 6 DEX / 230 533 тела методов. Никакой подмены музыки на Android не сделано, официальное приложение и Test.50 не менялись.

**Точная точка исследуемого кода:** 78b0437f17888ce49a4c1bea0ba06ca96cb455b9.
**Бэкап этой исследовательской точки:** backup/android-signed-typed-dispatch-field-audit-ci-green-20261110 (создать/проверить отдельно от пользовательского Test.50).
**Вся историческая работа остаётся:** docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md, docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md.

## Что удалось наблюдать в оригинальном DEX, по порядку

1. **Точная точка FileInfo:** в Lhee.a два вызова sw7.y0/z0 преобразуют FileInfo DTO в Leed с move-result-object; результат подаётся в Lxa7.<init> как аргумент. Lxa7 extends Lya7 и содержит поле Object. В Lged.a виден вызов Lhee.a, проверка варианта Lxa7, чтение его Object-поля и check-cast к Leed. Это конкретный структурный путь с ограниченным регистровым may-flow, не доказательство edition/decoder.
2. **Coroutine дальше:** Lfed.invokeSuspend вызывает Lged.a и возвращает результат; Lgee.invokeSuspend вызывает Lhee.a и возвращает результат. Большая ветвящаяся Lfqr.invokeSuspend (1528 DEX инструкций) после Lged.a типизирует Leed, читает несколько его полей и вызывает Ldiv.<init>. Ldiv — типизированная модель с десятью полями. Но прямое межкорутинное тождество объекта и его текущая принадлежность активному треку не установлены.
3. **Следующее структурное преобразование:** Lygv.r имеет точную сигнатуру r(Ldiv,Lavt,Lp7i):Ljgv, обращается к нескольким getter-методам Ldiv и создаёт Ljgv с шестью параметрами. Lygv.a/b вызывают Lygv.r. Следовательно, реальные подписанные DEX знают такую типизированную модель; само по себе это не доказывает, что результат именно данной coroutine попал туда в runtime.
4. **Кандидаты преобразований перед плеером:** Ljgv фигурирует в типизированных методах Lcq7.D/T/i0, Lo4y.a/b/c/d, Llvc.a, Larv.g, Lygv.*. Внутри этих методов возникают обфусцированные модели Lkq7, Lga4, Lnro, Lt6f. Lkq7/Lga4 реализуют Le48, Lnro наследует Le93, Lt6f наследует Lmir. Ни у одного из этих типов не доказано наследование именно названного public Media3 DataSource/MediaSource.
5. **Важная проверка возможной Media3-связи:** поиском реальной иерархии методов обнаружена *потенциальная* цепочка семи invoke/virtual-рёбер Larv.g → Lero.<init> → Lero.<init> → Lga4.c → Le48.a → Ldl8.a → Lsu5.invoke → Lro7.y0. Lro7 — один из четырёх ранее обнаруженных обфусцированных классов, реализующих Media3 ExoPlayer. Однако ребро Le48.a → Ldl8.a — **одна из 16 возможных реализаций интерфейса**, без доказательства типа receiver. Ldl8.a содержит switch, Lsu5.invoke — 721 инструкцию и switch с НЕЗАВИСИМЫМИ кейсами. Lro7.y0 наблюдается в одном из кейсов, а это не подтверждает цепочку данных от FileInfo.
6. **Критическая проверка конкретного receiver, а не только графа:** проверены все 230 533 тела методов и 3 680 622 инструкции DEX на прямые чтения/записи именно полей Lga4 типа Le48. У Lga4 два разных поля такого типа. Конструктор создаёт Lzcd и кладёт его в **field-1**, а Lga4.c вызывает Le48.a через **field-2**. Подмена этих слотов в анализе дала бы ложный вывод. В field-2 есть прямые статические записи из Lcq7.i0 (наблюдается Lya4), Linq.a / Ljue.<init> (наблюдается Lkc6), а также несколько записей неизвестного непосредственного происхождения. **Прямого нового Ldl8 в этом слоте не обнаружено.** Это не исключает его через непрямой объект, reflection или coroutine, но семишаговая цепь к Lro7 **не может считаться настоящим decoder source proof**.
7. **Реальные обнаруженные альтернативы receiver:** Lya4.a строит Lza4, Lzcd.a строит Lbdd; Lkc6.a сам имеет switch и внутри вызывает и Le48.a, и Lya4.a в разных ветвях. Никакая из этих структур пока не связана с фактическим current-track decoder prepare. Допустимо продолжать именно с ними, а не подменять их абстрактным Ldl8.

## Какие новые исследовательские файлы созданы

- android/native-yandex-hooklab/audit_native_typed_wrapper_coroutines.py + tests/test_native_typed_wrapper_coroutines.py — типы, обёртки, точные coroutine windows и результаты регистров.
- android/native-yandex-hooklab/audit_native_postfileinfo_lifecycle.py + tests/test_native_postfileinfo_lifecycle.py — модель Ldiv, сигнатура Lygv.r и downstream Ljgv consumption.
- android/native-yandex-hooklab/audit_native_jgv_media_candidates.py + tests/test_native_jgv_media_candidates.py — реальные фабрики и потенциальные Media3 кандидатные классы; диагностика switch-ловушек.
- android/native-yandex-hooklab/audit_native_obfuscated_dispatch_bridge.py + tests/test_native_obfuscated_dispatch_bridge.py — 41 потенциальное виртуальное ребро, строго с пометкой ambiguous receiver, не dataflow proof.
- android/native-yandex-hooklab/audit_native_ga4_field_receiver.py + tests/test_native_ga4_field_receiver.py — точная проверка полей Le48, прямых writer-site и конструкторного типа; без раскрытия приватных имён полей.
- Пять независимых workflow в .github/workflows/android-native-typed-wrapper-coroutines.yml, android-native-postfileinfo-lifecycle.yml, android-native-jgv-media-candidates.yml, android-native-obfuscated-dispatch-bridge.yml и android-native-ga4-field-receiver.yml.

## CI на исходном подписанном приложении

- [Типизированные DTO и coroutine #42808158803](https://github.com/manufact-test/nomusic/actions/runs/42808158803) — SUCCESS.
- [Реальные потребители Ldiv/Ljgv #42808680756](https://github.com/manufact-test/nomusic/actions/runs/42808680756) — SUCCESS.
- [Кандидаты фабрик/media #42809032271](https://github.com/manufact-test/nomusic/actions/runs/42809032271) — SUCCESS.
- [16-way возможный dispatch и конструкторы #42809849405](https://github.com/manufact-test/nomusic/actions/runs/42809849405) — SUCCESS.
- [Фактический DEX field reader/writer #42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588) — SUCCESS.
- [Уточнение конкретных Lya4/Lkc6/Lzcd #42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855) — SUCCESS.
- Android hooklab по-прежнему **только read-only module**, не патченый Яндекс и не реальная аудиоподмена. Проверка Android-модуля новой точки: https://github.com/manufact-test/nomusic/actions/runs/42810750850 — **SUCCESS 2/2**, оба задания завершены успешно.

## Что именно мешает полному Android source swap

НЕТ подтверждённой непрерывной цепочки **активный trackId + edition + generation → FileInfo → конкретная текущая Ljgv / Le48 instance → actual native MediaSource/DataSource → decoder prepare**. Старый метод общего caller/синтетические контракты и новый возможный Le48 dispatch не равны доказательству. Особенно опасны async coroutine resume и переключатели в обфусцированных lambda.

Следующий ответственный шаг — дополнительно проследить конкретную запись в field-2 Lga4 через Lya4/Lkc6 и непрямые writers, затем в реальной ARM Android среде read-only подтвердить тот же объект на границе decoder source. Без такого подтверждения НЕ подключать NativeGrantContract / NativeReplacementLifecycle / NativePrePrepareAdmission и НЕ публиковать установочный APK как «работающий».

**Нельзя трогать:** Test.50, HONOR владельца, официально установленный Яндекс, Windows CELIKOM 0.24.7, расширение, API, БД, production, подписи, DRM и Play Protect. Не предлагать ChromaSync или повтор старых x86 LSPatch/AppMetrica экспериментов. Windows подтверждённый аудио PASS не переносится на Android автоматически.
