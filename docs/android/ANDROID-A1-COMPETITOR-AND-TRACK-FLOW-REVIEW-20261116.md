# CELIKOM Android A1 — competitor and current Track Flow review

> **Current follow-up (16.11.2026):** the latest Player/MediaItem and playlist handoff findings supersede the old stop note below. Read [ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md) before doing more work. The competitor sweep remains closed; do not repeat it.


**Дата:** 16.11.2026  
**Репозиторий:** manufact-test/nomusic  
**Рабочая ветка:** experiment/android-a1-metrica-init-state-observer-arm13-20261112  
**Подтверждённая кодовая основа:** 88b81e394ea2d61f0b25a0a5dd38bb41663150f5  
**CI #161:** [SUCCESS, 108/108](https://github.com/manufact-test/nomusic/actions/runs/43763991624)  
**Точный backup:** backup/android-a1-flow-field-writer-trace-ci-green-20261115 @ 88b81e394ea2d61f0b25a0a5dd38bb41663150f5

## 1. Сверка конкурентов

### FkCensor — наиболее полезная техническая подсказка

Источник: https://github.com/S4YN3X/F_ckCensor/blob/main/assets/inject.js

Публичный код перехватывает resource methods getFileInfo и getFileInfoBatch. Для Track ID с replacement он возвращает изменённый fileInfo/downloadInfo с альтернативным URL, codec и transport raw. То есть замена происходит на границе получения file metadata — до того, как штатный web player использует источник.

**Что полезно:** сохраняется существующая модель плеера; меняется описание аудиоисточника до дальнейшей обработки.

**Что нельзя переносить:** это web/desktop resource API. Эквивалентный Android-native callsite в подписанном DEX не найден. Сам факт, что desktop hook работает, не доказывает наличие такого же метода в Android.

### FckCensor

Источник: https://github.com/Hazzz895/FckCensor

В проекте есть Track-ID-based replacement registry и интеграция с PulseSync. Это подтверждает практический подход «сначала определить Track, затем связать его с replacement», но не даёт готовой точки нативного Android decoder hook.

### ChromaSync Mobile

Источник: https://github.com/Desai0/ChromaSync-Mobile

README описывает Android-модуль с LSPatch/LSPosed, локальными треками, кешированием альтернативной дорожки и её использованием, когда файл готов. Но публичное дерево репозитория содержит только README.md — исходников модуля нет. Поэтому конкретный метод перехвата и идентичность Track → decoder проверить нельзя.

### ChromaSync Desktop

Источник: https://github.com/Desai0/ChromaSync

В открытом script.js есть защита от гонки обновления обложки через request/change identity. Это предотвращает применение устаревшего результата UI, но не является доказательством audio source replacement или native audio sink.

### YandexMusicMod и YM Liberty

Источники:
- https://github.com/mrvokintos/YandexMusicMod
- https://github.com/gagayhhad-tech/ym-liberty-android

Обнаруженные реализации используют собственную модель плеера/WebView или отдельный playback flow. Прямого готового Android-native участка, который можно безопасно перенести в A1, не найдено.

### Наша Windows-версия

Документы:
- https://github.com/manufact-test/nomusic/blob/main/docs/windows/W127-CURRENT-DECODER-QUEUE-IDENTITY-RECONCILIATION-20261114.md
- https://github.com/manufact-test/nomusic/blob/main/docs/windows/W131-VERIFIED-SOURCE-LEFT-STALE-MAPPING-INVALIDATION-20261114.md

Полезен принцип: decoder-source witness сверяется с фактически текущей queue/player identity; stale mapping инвалидируется при source-left или смене состояния. Windows использует CDP и собственный host/renderer contract, поэтому код напрямую в Android не переносить.

**Вывод по конкурентам:** готового решения для нашей Android A1 архитектуры не найдено. FkCensor показывает подходящую pre-decoder точку на web player boundary, но Android-эквивалент ещё не доказан. Повторный общий competitor sweep не нужен.

## 2. Текущий Track Flow — что действительно доказано

Результат bounded read-only signed-DEX анализа CI #161:

- LzD7 — interface; найден один direct implementer: LMG7.
- YMApplication.onCreate подписывает LDp0 collector.
- Flow path:
  1. LzD7.if() → LC3a Flow.
  2. LBD7.if(LzD7) → LBy4 Flow.
  3. LBC3 → LzC3 → LAC3 → LO6.native.
  4. Ljm4.for(Flow, CoroutineScope, LDp0 collector).
  5. LDp0.if(Track) → LGp0.new(Track).
- LMG7.<init> получает два объекта descriptor-типа LD3a из LyG7 и сохраняет их в собственные поля. Это только структурное наблюдение; смысл current player / StateFlow не выводить из обфусцированного descriptor.
- В LDp0.if(Track) есть вызов Lou3.else(Track). Аргумент Track читается из coroutine field; точное происхождение значения через coroutine state не доказано.

Итоговые показатели bounded trace:
- direct Player API calls: 0.
- direct MediaSession calls: 0.
- direct decoder-boundary calls: 0.
- source-descriptor call references: 12.
- same_track_reference_from_flow_to_lgp0_new_proven: false.
- current_selected_track_proven: false.
- same_native_item_to_decoder_proven: false.
- active_selected_item_proven: false.

Следовательно, этот Flow может обслуживать queue, prefetch, download или вспомогательную работу. Его нельзя считать текущим играющим Track.

## 3. Что произошло с расширенным проходом

- CI #161 — SUCCESS, 108/108; это последняя зелёная кодовая основа.
- CI #162 — одна synthetic fixture не включала Lou3 в trace owners.
- CI #163 — fixture исправлена, все 108 unit-тестов прошли, но read-only DEX scan завершился с защитным кодом CURRENT_TRACK_FLOW_METHOD_TRACE_LIMIT.
- Это ограничение сработало после расширения списка coroutine owners. Vendor binary не экспортирован и не изменён; APK не собирался.
- Экспериментальное расширение исключено из рабочей основы. Текущий код должен соответствовать checkpoint 88b81e394ea2d61f0b25a0a5dd38bb41663150f5 и backup branch выше.

## 4. Итог точечной проверки Lou3.else(Track) — CI #165

- [CI #165](https://github.com/manufact-test/nomusic/actions/runs/43767513234) — SUCCESS; 108/108 tests, read-only six signed DEX.
- Вызов `Lou3.else(Track)` из `LDp0.if(Track)` подтверждён. Для **этой exact сигнатуры** тело с исполняемым кодом в подписанных DEX **не найдено**: `body_found=false`, `instruction_count=null`, `complete_for_absence_claim=false`.
- Это **не** доказывает отсутствие работы через interface/abstract/external dispatch. Нельзя классифицировать Lou3 как queue, download или analytics без тела метода.
- Прямой Player selection/current playback identity edge отсутствует в доказательствах. В соответствии с заранее установленным стоп-правилом весь маршрут `LzD7 → LMG7 → LDp0 → Lou3` закрыт **как недоказанный**, без исследования соседних классов.
- Кодовый checkpoint: `f1ad3998b81a3c7b12d9ba19ae02c57a6199eecf`. Резерв `backup/android-a1-lou3-exact-method-ci-green-20261116`.
- Следующий шаг **не** ещё один sweep: нужен подтверждённый current-player identity-bearing callsite, связывающий выбранный Track/Album с decoder source и audio sink. Его пока не установили. Stage B остаётся NO-GO.

## 5. Статус продукта и ограничения

- Stage A / NAV17: PASS по подтверждению владельца; оригинальный Яндекс и обычное воспроизведение не трогать.
- Stage B: NOT CONNECTED / NO-GO; CELIKOM replacement audio не подключено к нативному decoder.
- Runtime hooks не менялись; последний runtime-hook commit: a655712d210189f3bc611847235de3ed4d985c1a.
- Не читать значения приватных полей, Track/Album IDs и названия, URL, DataSpec, токены, account data или audio bytes.
- Не менять vendor behavior, не подавлять exceptions, не добавлять второй player/decoder/AudioTrack.
- Не трогать Windows, browser extension, backend/API/DB, NAV17, Test.50 или frozen A1/LSPatch baseline.



## 6. Follow-up — exact Media3 Player candidate closed, CI #180

Проверка кандидата \`LfH7.else()LkD7;\` завершена. Точный descriptor \`LkD7;\` — concrete exception class, не MediaItem и не доказанная обёртка над ним. \`Lp24.else()\` вызывает \`ExoPlayer.else()LX04;\` на delegate receiver, а затем возвращает тот же object result. Кандидат закрыт; source/decoder tracing для него не выполнялся. Не расширять поиск на соседние классы без отдельного задания. Полный trace, implementor mapping и CI #180: \`ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md\`.
