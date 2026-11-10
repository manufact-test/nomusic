# CELIKOM Android — подписанный DataSource-совместимый source/open, две ветви Lga4

**10 ноября 2026. Крупный READ-ONLY исследовательский этап, без изменений Яндекса и пользовательских устройств.**

- **Точный проверенный код:** 6b5bfde53d81a29920f32a3c6b13b730b216e669.
- **Откат / замороженная ветка:** backup/android-signed-dual-source-dataspec-open-ci-green-20261110.
- **Исходный объект:** издательски подписанный неизменённый Yandex Music 2026.10.3 #170gpr, 5 split APK, 6 DEX. Подпись/hash проверяется до анализа в одноразовом GitHub Actions.
- **Предыдущее исследование:** docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md. Там выявлен FileInfo DTO → sw7.y0/z0 → Leed → Lxa7 и типизированная цепь к Ldiv/Ljgv; семишаговый возможный путь к Lro7 не считался доказательством.

## Главное новое: подтверждены ДВА разные DataSource-производящих поля

**Только статические инструкции DEX, не runtime-подмена:**

1. **Lga4 имеет два разных поля типа Le48.** Одно читается в Lga4.b/c (условно *secondary*, старое field-2), другое в Lga4.d (условно *primary*, старое field-1). Поля сопоставлены по точному DEX field-ref, а не по одному лишь одинаковому типу. Оба пути собираются в Lha4, который реализует Lm48.
2. **В Lcq7.i0:** secondary заполняется новым Lya4, конструктору которого передаётся статический Lk27. Метод Lya4.a создаёт Lza4. Lza4.b(La58):long непосредственно конструирует исключение и бросает его; read тоже бросает, getUri возвращает null, close ничего не делает. **Такой экземпляр не является рабочим аудиопотоком.** Идентификация secondary как основного источника была бы опасной ошибкой.
3. **В том же Lcq7.i0:** primary заполняется результатом **Lcq7.A(Leyc,Lthq):Luiq**, который затем помещается в первое поле Le48 в Lga4. Leyc.d получает значение Lavt из Ljgv, но точный переход *того же* FileInfo объекта через Leyc/дальнейший выбор Lthq ещё не доказан: метод содержит ветвление и разные промежуточные объекты. В других конструкциях primary может содержать Lzcd (по умолчанию) либо прийти через Lga4.g(Le48); secondary — через Lga4.j, Linq, Ljue и другие writers. Это реальные варианты, а не один глобальный источник.
4. **Lga4.d:** вызывает Le48.a() для primary и передаёт полученный Lm48 в **Lha4.<init>**. Другой Lm48 передаётся в Lga4.d из Lga4.b/c (secondary). Оба участника попадают в разные параметры обёртки. Нельзя смешивать их или выводить "наш URL уже у decoder" из соседства вызовов.

## НОВОЕ: найден полный ОБФУСЦИРОВАННЫЙ DataSource-совместимый контракт

**Подтверждено структурными сигнатурами издательского DEX:**

- Интерфейс Lm48 имеет **b(La58):J**, **getUri()** и **close():V**.
- Lm48 **extends Lv38**, в котором присутствует **read([BII):I**.
- Взятые **вместе**, интерфейс и его родитель формируют полный характерный набор **DataSpec → long / byte[] read / Uri / close**. La58 содержит структуру с Uri-like типом, длинными позициями/длинами и builder-методами. Этот набор *структурно совместим* с DataSource, но обфускация не позволяет только по сигнатурам утверждать, что экземпляр реально выбран текущим ExoPlayer.
- В подписанном DEX обнаружены **33 конкретные реализации Lm48**, включая Lha4 и Lza4.
- **Lha4.b(La58)** реализует открытие и обращается к вспомогательному Lha4.f; **Lha4.f** вызывает **Lm48.b(La58)** на делегате; **Lha4.read** вызывает **Lv38.read([BII)**, **Lha4.d/close** закрывают активный делегат. Это точные настоящие invoke-инструкции, не анализ по названию класса.
- **Luiq.a():Lm48** через ленивое значение Lz3f получает/кэширует Lm48, проверяет Le48 и вызывает **Le48.a():Lm48**. В Lz3f.a есть прямой вызов **Lm48.b(La58):J** и конструирование результата; Lz3f.b сохраняет Lm48 в одно из полей Lz3f при обработке coroutine.
- Вышеописанное обнаруживает *конкретный реальный source/open механизм*, который прежние поиски только по открытым public Media3 именам пропускали. Но это ещё НЕ установленная цепь текущий трек → именно этот экземпляр → плеер → decoder PREPARE.

## Честная матрица доказательств

| Проверяемое утверждение | Статус |
| --- | --- |
| FileInfo преобразуется двумя точными sw7.y0/z0 вызовами | **ДА**, оригинальный DEX |
| Есть реальные обёртки Leed, Ldiv, Ljgv и фабрики Le48 | **ДА**, оригинальный DEX; межкорутинное тождество ограничено |
| Lm48/Lv38 имеют полный DataSource-подобный API | **ДА**, структурные method refs + class hierarchy |
| Lha4 и Lz3f реально содержат вызовы открытия DataSpec и чтения байтов | **ДА**, подписанный DEX, не live выполнение |
| Конкретный Lm48 уже относится к текущим trackId + edition + generation | **НЕТ доказательства** |
| DataSource объекта текущего трека действительно принят decoder/ExoPlayer до prepare | **НЕТ доказательства** |
| CELIKOM Android действительно подменяет аудио | **НЕТ** |
| На пользовательском HONOR проверены Дым/Раскол, Pause/Seek/Radio/Next | **НЕТ**, устройство НЕ трогали |

## Репозиторий и CI

**Новые (после предыдущей точки) анализаторы:**

- android/native-yandex-hooklab/audit_native_ga4_field2_value_origins.py: шесть writer-sites точного secondary field-ref, ограниченная трассировка source-регистра до new-instance, параметра, поля или invoke-result; сохраняет только типы/роли/регистровые координаты, без bytecode, строк или URL.
- android/native-yandex-hooklab/audit_native_ga4_primary_source.py: находит разные primary/secondary по фактическим ридерам Lga4.b/c/d, трассирует все прямые writers, а также профили Lcq7.A, Leyc.d, Lga4.d и Lza4.b.
- android/native-yandex-hooklab/audit_native_obfuscated_datasource_shape.py: проверяет наследование Lm48→Lv38, сигнатуры DataSpec/read/getUri/close, 33 конкретные реализации, вызовы Lm48, а также безопасные окна регистров Lha4/Luiq/Lz3f.

**Новые workflow и тесты:**

- .github/workflows/android-native-ga4-field2-value-origins.yml / tests/test_native_ga4_field2_value_origins.py
- .github/workflows/android-native-ga4-primary-source.yml / tests/test_native_ga4_primary_source.py
- .github/workflows/android-native-obfuscated-datasource-shape.yml / tests/test_native_obfuscated_datasource_shape.py

**Green CI на сохранённой точке:**

- [Writer register evidence #42813687276 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42813687276)
- [Dual-field source/read #42814211492 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814211492)
- [Full inherited obfuscated DataSource #42814967628 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814967628)
- [Expanded source/open register windows #42815048696 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42815048696)
- [Read-only Android module #42815048701 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42815048701)

Промежуточная CI с фикстурой без симуляции field table была красной, **фикс теста внесён**, новая точка проходит. Полный Android-модуль продолжает собираться, но ни один найденный источник пока не подключён к NativeGrantContract/NativeReplacementLifecycle/NativeSourceGate.

## Следующий важнейший барьер

Найти **не название очередного класса**, а достоверное тождество *текущего* FileInfo/trackId + edition + generation с **конкретным** Lm48/La58, выбранным непосредственно перед DataSource open / ExoPlayer decoder prepare. Учитывать coroutine suspension/resume, lazy Lz3f, кэш, буферы, радио/рандом/Next и устаревшие поколения запросов. Может потребоваться изолированная ARM-среда и только read-only наблюдение без передачи URL/авторизации/аудио. До реального подтверждения **НЕ подключать замену и не публиковать Android APK как рабочий**. MediaSession не считать источником музыки.

**Не трогать:** Android Test.50, основной HONOR, установленный Яндекс, Windows 0.24.7, расширение, API/БД/production, подписи/DRM/Play Protect. Не возвращаться к x86 LSPatch/AppMetrica и не предлагать ChromaSync.
