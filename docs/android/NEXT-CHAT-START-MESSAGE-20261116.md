Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с сохранённой точки. Ничего не начинай с нуля и архитектуру не меняй.

**Продукт:** Android mobile app. Не Windows и не браузерное расширение.  
**GitHub:** \`manufact-test/nomusic\`  
**Единственная рабочая ветка:** \`experiment/android-a1-metrica-init-state-observer-arm13-20261112\`  
**Последний CI-green code checkpoint:** \`70009b4e05a592e7036c8457ca027b2445202c1f\`  
**CI #178:** [SUCCESS, 114/114 тестов](https://github.com/manufact-test/nomusic/actions/runs/43825896825)  
**Точный backup:** \`backup/android-a1-media3-player-contracts-ci-green-20261116\`  
**Последний runtime-hook change:** \`a655712d210189f3bc611847235de3ed4d985c1a\`. После него hooks не менялись.

### Сначала прочитай только актуальные документы

1. \`docs/android/NEXT-CHAT.md\`
2. \`docs/android/ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md\`
3. \`docs/android/ANDROID-A1-COMPETITOR-AND-TRACK-FLOW-REVIEW-20261116.md\`
4. \`docs/android/ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md\`

### Что уже сделано — не повторять

- Сверка конкурентов завершена. Готового Android-native решения для нашей архитектуры не найдено.
- Старые маршруты LyEa/LaC7/LCK1 и LzD7/LMG7/LDp0/Lou3 закрыты как недоказанные. Не возвращаться.
- Известный ByteBuffer → native audio sink путь исследован; он не доказывает идентичность текущего выбранного трека.
- CI #178 проверил точную подписанную сборку 2025 и нашёл 5 concrete Media3 ExoPlayer implementors в ограниченной ancestry из 10 owners. Parser sanity прошёл.
- В ancestry найден обфусцированный Player-контракт \`LfH7;\`. Его точная сигнатура \`else()LkD7;\` совпадает с методом \`Lp24.else()LkD7;\`, который вызывает Player API. Это кандидат, не доказанный current MediaItem getter.
- Полный результат и оговорки — в \`ANDROID-A1-MEDIA3-PLAYER-ANCESTRY-20261116.md\`.

### Единственная следующая задача

Проверь **только** кандидат \`LfH7.else()LkD7;\` → \`Lp24.else()LkD7;\`:

1. Установи по точному DEX descriptor, является ли \`LkD7;\` MediaItem или его wrapper. Не угадывай по имени.
2. Проследи тело \`Lp24.else()LkD7;\`: точный delegate/receiver и object identity результата.
3. Проверь ту же сигнатуру у других concrete implementors только если она там реально объявлена или унаследована.
4. Если это MediaItem, проследи тот же объект до source/decoder boundary и уже известного ByteBuffer/native sink. Не смешивай current playback с queue/prefetch/download.
5. Если identity не доказывается на этом коротком участке — зафиксируй точный разрыв и не расширяй поиск.

### Не делай лишнего

- Не повторяй ancestry scan, competitor sweep, полный interface census и старые аудиты.
- Не создавай новый audit framework, не добавляй тесты ради количества и не запускай CI после каждой мелочи.
- Не меняй runtime hooks, vendor behavior, APK или оригинальное приложение.
- Не добавляй второй player/decoder/AudioTrack.
- Не читай значения приватных полей, Track/Album IDs и названия, URL/DataSpec, токены, данные аккаунта или audio bytes.
- Не трогай NAV17, Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Не проси владельца о ручной проверке без конкретного необходимого измерения.

Работай крупным блоком, без промежуточных отчётов каждые несколько минут. Остановись только если действительно нужна ручная проверка или найден конкретный блокер.
