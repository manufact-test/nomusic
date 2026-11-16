# CELIKOM Android A1 — exact Media3 Player ancestry audit

**Дата:** 16.11.2026  
**Репозиторий:** \`manufact-test/nomusic\`  
**Рабочая ветка:** \`experiment/android-a1-metrica-init-state-observer-arm13-20261112\`  
**Кодовый checkpoint:** \`28c9bf9d3fa46a7a4aa0cebcc55fee9018602796\`  
**CI #180:** [SUCCESS, 116/116 тестов](https://github.com/manufact-test/nomusic/actions/runs/43830018094)  
**Точный backup:** \`backup/android-a1-media3-current-item-candidate-ci-green-20261116\` @ \`28c9bf9d3fa46a7a4aa0cebcc55fee9018602796\`  
**Предыдущий backup:** \`backup/android-a1-media3-player-contracts-ci-green-20261116\` @ \`70009b4e05a592e7036c8457ca027b2445202c1f\`

Read-only анализ точного issuer-signed Yandex 2025 XAPK, шесть DEX, только в памяти. Runtime hooks, приложение, APK и playback не затрагивались.


## 0. Superseding result — LfH7.else()LkD7; закрыт, CI #180

Этот раздел supersedes прежнюю гипотезу в разделах 4 и 6 ниже. Исходная ancestry-проверка CI #178 остаётся историческим baseline.

### Точный descriptor

- \`LkD7;\` определён в точной подписанной сборке как concrete class.
- Superclass: \`Ljava/lang/Exception;\`; interfaces: none.
- Instance field type descriptors: \`I\`, \`J\`, \`Landroid/os/Bundle;\`.
- Static field type descriptor: \`Ljava/lang/String;\`.
- \`LkD7;\` не является \`MediaItem\`, не является его subtype и не содержит MediaItem-typed fields. В DEX не найдено доказанного constructor-field-to-accessor identity для обёртки. Ни одна найденная ссылка \`MediaSource.Factory\` не принимает этот точный descriptor.
- Вывод: \`LfH7.else()LkD7;\` — error/exception contract, не current MediaItem getter. Семантическое имя обфусцированного класса не выдумывается.

### Тело Lp24.else()LkD7;

Точный trace на 4 инструкциях, без ветвлений:

1. Читает из \`this\` объект, объявленный как \`Landroidx/media3/exoplayer/ExoPlayer;\`.
2. Вызывает \`Landroidx/media3/exoplayer/ExoPlayer.else()LX04;\` через interface invoke.
3. Получает object result.
4. Возвращает тот же object result.

Доказано:
- receiver register имеет origin \`FIELD_READ_FROM_THIS:Landroidx/media3/exoplayer/ExoPlayer;\`;
- receiver identity на этом участке доказана;
- \`same_call_result_to_return_proven=true\`;
- новый объект не создаётся, field values не читаются.

### Та же сигнатура у пяти concrete implementors

| Concrete implementor | Effective declaration |
|---|---|
| \`LDq2;\` | Наследует concrete body от \`LA14;\` |
| \`Landroidx/media3/exoplayer/d;\` | Собственная concrete declaration |
| \`Landroidx/media3/exoplayer/m;\` | Собственная concrete declaration |
| \`Lp24;\` | Собственная concrete declaration |
| \`Lwq2;\` | Наследует concrete body от \`LA14;\` |

### Граница результата

- \`LkD7;\` — не MediaItem, поэтому путь к \`MediaSource.Factory\`, decoder и ByteBuffer/native sink для этого кандидата не запускался.
- \`runtime_player_instance_proven=false\`, \`active_selected_item_proven=false\`, \`same_native_item_to_decoder_proven=false\`.
- Кандидат закрыт. Не продолжать исследование соседних классов и не начинать новый getter search без отдельного задания.
- CI #180: SUCCESS, 116/116 тестов; шесть DEX, read-only in-memory audit.
- Runtime hooks, vendor behavior, APK и playback не менялись.


## 1. Область и валидность результата

Проверялась только ancestry двух известных Media3 roots:

- \`Landroidx/media3/common/Player;\`
- \`Landroidx/media3/exoplayer/ExoPlayer;\`

CI #175 завершился ошибкой: проверка наличия class data случайно оказалась в общем method walker. В #176–#177 результат ancestry был частичным: DEX filename regex был double-escaped, поэтому parser sanity вернул false и method inventory был пуст. Не использовать эти промежуточные результаты.

В #178 исправлены обе ошибки. Подтверждение корректного парсинга реального DEX: известный renderer owner \`LcC0;\` дал 58 объявленных методов, \`declared_method_parser_sanity.passed=true\`. Все 10 owners из выбранной ancestry имеют class data.

## 2. Найденная Player ancestry

Пять concrete implementors:

- \`LDq2;\`
- \`Landroidx/media3/exoplayer/d;\`
- \`Landroidx/media3/exoplayer/m;\`
- \`Lp24;\`
- \`Lwq2;\`

Полный ограниченный scope — 10 owners:

\`LA14;\`, \`LDq2;\`, \`Landroidx/media3/exoplayer/ExoPlayer;\`, \`Landroidx/media3/exoplayer/d;\`, \`Landroidx/media3/exoplayer/m;\`, \`LfH7;\`, \`Lhq2;\`, \`Lp24;\`, \`LrD0;\`, \`Lwq2;\`.

Важная структурная связь: \`Landroidx/media3/exoplayer/ExoPlayer;\` наследует интерфейс \`LfH7;\`. В \`LfH7\` есть методы \`play()\`, \`pause()\`, \`prepare()\`, \`getDuration()\`, \`getVolume()\` и другие Player-подобные контракты. Поэтому \`LfH7\` — обоснованный кандидат на обфусцированный Player interface. Это структурная гипотеза по точной ancestry и контрактам, а не доказательство семантики каждого обфусцированного метода.

## 3. Объём фактической проверки

- 627 объявлений методов в ограниченной ancestry.
- 271 объявление относится к interface/abstract owners.
- В результирующий JSON выведено не более 128 контрактов; \`scope_method_contract_rows_truncated=true\`. Полный перечень всех 271 методов не заявляется.
- 503 code-bearing метода проверено в ancestry.
- 26 implementation rows имели распознанные сигнатурные/вызовные роли; все они указывают на обращения к Media3 Player API, но ни одна строка не доказывает передачу Track/Album в Player selection или decoder.
- Распределение этих 26 строк: 13 у \`Lp24;\`, 11 у \`LA14;\`, 1 у \`LDq2;\`, 1 у интерфейса \`ExoPlayer;\`.
- В Player ancestry не найдено прямых полей Track, Album или Track-ID wrapper. Этот отрицательный вывод относился к известным типам в CI #178; точный descriptor \`LkD7;\` классифицирован отдельно в superseding section 0 по результату CI #180.
- \`interface_api_method_count=0\` и \`public_player_selection_method_refs=[]\` относятся к поиску по двум известным не-обфусцированным root owners. Это **не** означает отсутствие Player API: точная ancestry показала контракт \`LfH7;\`.

## 4. Историческая гипотеза — закрыта результатом CI #180

В \`LfH7;\` найден метод:

\`else()LkD7;\`

Та же сигнатура присутствует в интерфейсе \`ExoPlayer;\` и в concrete implementation row:

\`Lp24.else()LkD7;\`

Тело \`Lp24.else()\` вызывает Media3 Player API. Но текущий анализ **не** установил:

- что \`LkD7;\` действительно является MediaItem или его wrapper;
- что \`Lp24\` — runtime-selected Player конкретной сессии;
- откуда именно берётся возвращаемый объект;
- что этот объект связан с текущим Track/Album и тем же decoder source.

Следовательно, это только узкий identity-bearing кандидат. Нельзя переименовывать его в getCurrentMediaItem без проверки descriptor и тела.

## 5. Продуктовые gates

Существующие счётчики остались без положительного доказательства:

- \`active_selected_item_proven=false\`
- \`same_native_item_to_decoder_proven=false\`
- \`same_track_album_edition_generation_owner_proven=false\`
- \`codec_output_object_to_audio_sink_proven=false\)
- Track-parameter calls to Player selection: 0
- Track-parameter calls to MediaSession metadata/state: 0
- Track-parameter calls to decoder/source descriptor: 0
- Edition/Generation type descriptors: 0

Stage A / NAV17 остаётся PASS по ручному подтверждению владельца. Stage B остаётся NOT CONNECTED / NO-GO. Известный ByteBuffer/native sink путь сам по себе не доказывает, что это буфер текущего выбранного трека.

## 6. Исторический план проверки — выполнен и superseded

Не выполнять пункты ниже повторно: кандидат закрыт в section 0 по CI #180.

1. Проверить точный class descriptor \`LkD7;\`: его superclass/interfaces, поля только по типам, конструкторы и методы. Установить, соответствует ли он MediaItem или внутренней обёртке, без догадок по имени.
2. Проследить тело ровно одного метода \`Lp24.else()LkD7;\`: receiver/delegate и возвращаемую object identity.
3. Проверить точные реализации той же сигнатуры в остальных concrete implementors только если DEX подтверждает, что они её объявляют или наследуют.
4. Если объект действительно MediaItem, проследить тот же объект до source/decoder boundary, а затем связать его с уже известным ByteBuffer/native sink. Queue/prefetch/download не считать active playback.
5. Если identity разрывается — зафиксировать конкретный разрыв и не расширять аудит.

Не запускать новый competitor sweep, полный Player API census или generic caller search. Не добавлять runtime hooks, не собирать APK, не менять vendor behavior, не читать приватные значения, media IDs, URL/DataSpec, аккаунт или audio bytes. NAV17, Test.50, frozen A1/LSPatch и все другие продукты остаются нетронутыми.
