Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с сохранённой точки. Ничего не начинай с нуля, архитектуру не меняй.

**Продукт:** Android mobile app. Не Windows и не браузерное расширение.  
**GitHub:** `manufact-test/nomusic`  
**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Последний кодовый checkpoint:** `815abcb4f9f43224506392b67efc07b3e34cf26b`  
**CI #148:** [SUCCESS, 102/102](https://github.com/manufact-test/nomusic/actions/runs/43753653243)  
**Точный резерв:** `backup/android-a1-lya-route-closed-ci-green-20261115` @ `815abcb4f9f43224506392b67efc07b3e34cf26b`  
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`. После него runtime hooks не менялись.

### Сначала прочитай только эти актуальные документы
1. `docs/android/NEXT-CHAT.md`
2. `docs/android/ANDROID-A1-LYEA-ROUTE-CLOSURE-AND-AUDIO-SINK-RETURN-20261115.md`
3. `docs/android/ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md`
4. `docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md`
5. `docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md`

Не трать время на старые handoff-файлы, если эти документы уже отвечают на вопрос.

### Что уже закрыто
CI #148 закрыл LyEa / LaC7 / LCK1 как неподтверждённый маршрут. Поле LyEa связано с параметром конструктора, но обе нужные LCK1-корутины не имеют общего доказанного receiver identity; LzA9 — abstract interface без найденного тела точного метода. **Не возвращайся к этой ветке, не сканируй повторно implementers/callers, не запускай новые тесты для неё.**

### Твоя единственная следующая задача
Продолжай с уже найденного native audio sink:
- `LcLb.O` / `Lbd6.O` → `LbJ2.native(ByteBuffer, long, int)` — передача ByteBuffer-параметра уже доказана.
- Три ByteBuffer field slots и семь writer methods уже известны.
- Узкий следующий участок: `LcC0.n(JJ)Z` и `Lkd6.n(JJ)Z`, где уже найдены записи результата `Lad6.final(I)ByteBuffer` в соответствующие поля. Проследи ту же ссылку через field read до sink, не объединяя разные ветки/альтернативные записи.
- После этого найди владельца именно текущего выбранного Track/Album и свяжи его с тем же decoder/render path. Очередь, prefetch и download не считать активным playback.

Цель — доказать одну цепочку **current selected Track + Album + edition/generation → тот же decoder output → native audio sink**. Если на коротком участке identity не доказывается, зафиксируй точный разрыв и не выдумывай обход.

### Не делай лишнего
- Не создавай новый audit framework.
- Не повторяй готовые проверки и не расширяй поиск на соседние классы «на всякий случай».
- Не добавляй тесты ради количества и не запускай CI после каждой мелочи. Только минимальный тест на реально изменённую логику; полный CI после законченного блока.
- Не меняй runtime hooks, APK или vendor-код, пока выбранный Track не связан с декодером доказательно.
- Не трогай NAV17, оригинальный Яндекс, Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Не читай/экспортируй значения полей, названия/ID треков и альбомов, URL, DataSpec, токены, данные аккаунта или аудиобайты.
- Не проси владельца о ручных действиях без конкретной необходимости.

Работай крупным блоком, иди прямо по задаче и сохраняйся после законченного результата. Промежуточные отчёты и лишние исследования не нужны. Остановись только если действительно нужна моя ручная проверка или обнаружен конкретный блокер.
