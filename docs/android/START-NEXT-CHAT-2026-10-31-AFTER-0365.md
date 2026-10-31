# Первое сообщение следующему чату — CELIKOM Android, после проверки 0.3.65

Привет! Продолжаем CELIKOM **только для Android** (HONOR NTH-NX9 / Android 13, установленная Яндекс Музыка). Подключи GitHub `manufact-test/nomusic`, рабочая ветка `feature/android-unified-preparation-seek-gate`. **Не трогай desktop/extension, backend, сайт Hostinger, обновлятор, catalog/auth, рекламу или signing.** Все предыдущие версии доступны в Git; не уничтожай резервные точки.

**СНАЧАЛА ПРОЧТИ ПОЛНОСТЬЮ НОВЫЙ ГЛАВНЫЙ ДОКУМЕНТ:** `docs/android/HANDOFF-2026-10-31-AFTER-0365-HONOR-REVIEW.md`. Затем `docs/android/ANDROID-0365-MANUAL-NEXT-SCRUB-AND-DIP-2026-10-31.md`, `docs/android/ANDROID-0364-SEEK-SCRUB-2026-10-31.md`, `docs/android/REGRESSION-GATES-2026-10-29.md`, `docs/android/ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md` и код `ProbeService`, `SourceEventArbiter`, `ReplacementEngine`, `AudioOwnership`, `AudioContinuityMonitor`, `BufferedAudio` и engine tests. Старые «LATEST 0.3.61» и «0.3.51» в нижней части `NEXT-CHAT.md` исторические и НЕ актуальны.

**Сейчас установлена опубликованная и подписанная 0.3.65/code66**, исходный code anchor `37d7ff699a7cae0e051cf5dfcb63ca7a7f23c90f`, [CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41189834456). APK доступен через CELIKOM → «Проверить обновление» и постоянную ссылку https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/ . Оригинальная подпись сохранена. Но **качество звука на HONOR снова НЕ ПРИНЯТО**. Не выпускать сразу 0.3.66. Новая документация добавляется отдельно без изменения кода/версии и без нового APK; HEAD документационной точки может быть новее code anchor.

## Что конкретно слышит владелец

1. Переход в новую песню: старого «пшика» почти нет, но теперь CELIKOM **полностью глушит текущую песню до нуля и поднимает новую с нуля**. Это явно заметная яма, а не музыкально плавное соединение двух версий. Нужна акустическая непрерывность, но без «волны»/изменения тембра от прежнего overlapped crossfade.
2. Когда песня сменяется сама, пауза и finger seek обычно нормальные. **Один ручной Next в интерфейсе Яндекс Музыки ломает перемотку**: она прыгает и подлагивает. По наблюдению владельца, проблема может сохраняться и на следующем треке, который уже сменился естественно. Нельзя лечить только первые 500ms новой песни; нужен полный event/state/ownership аудит цепочки.
3. Владелец не хочет многократные мелкие патчи и поездки за каждым APK. Сначала большая, доказательная системная доработка и регрессии, потом одна подписанная release с автоматическим апдейтом.

## НОВЫЙ ЖУРНАЛ — принципиальные находки, не повтори неверную диагностику

В исходном чате приложен `CELIKOM-combined-20261031-130513.txt` (2335 строк). Там 0.3.63 строки 4–786, 0.3.64 787–1486 и **0.3.65 строки 1487–2335** (13:02:51+03, 140.6 секунд). Файл не коммитили из соображений приватности; подробные фактические вырезки и цифры уже в новом handoff, при необходимости попроси копию. Не путай runs.

- У 0.3.65: **41 seek**, **22 muted `replacement_scrub_hold`**, **0 `replacement_scrub_fallback`**, но **21 `audio_command_anomaly` вида `commanded_silence`** длительностью **43–194ms**, и **18 запусков 500ms exclusive dip** (17 завершились). Старый вывод «fallback=0 — значит проблема решена» **НЕВЕРЕН**.
- На уже полностью cached «Не стесняйся» (`48592143`): stream complete на t=7324ms, finger seek на t=10185ms завершается за 58ms, но отмечен 147ms commanded silence на t=10331ms. «Метамир» и «Хлоп-Хлоп» аналогично имеют 6 command gaps каждый после загрузки. Здесь причина **не медленный HTTP**: `ReplacementEngine.seek()` сам останавливает decoder и оставляет оригинал muted в cached fast path, а clock gate/реальное возобновление добавляют лаг.
- На частичных HTTP песнях «Каменные цветы» и «Крылья» во время scrubs Yandex восстановлен, но **каждый rejoin запускает новый полный 500ms dip**. Например для «Каменные цветы» после начального входа ещё 5 запусков на t=120148/121430/122583/124139/124938ms. Это объясняет субъективное «прыгает» даже без `scrub_fallback`.
- Все 7 зафиксированных межтрековых `source_discontinuity` имеют `reasonCode=1, userSeek=true`, но и index, и alias меняются, `SourceEventArbiter` классифицирует BOUNDARY, а `ReplacementEngine.sourceBoundary()` сбрасывает `explicitSourceSeek/sourceSeekedThisTrack`. Поэтому **не доказано**, что причина «сломалось навсегда после Next» — неочищенный флаг; требуется настоящий replay Media3 последовательности, а не догадка по тексту `userSeek`.
- `AudioContinuityMonitor` измеряет лишь **команды**, не speaker/BT/waveform; `hardwareOutputMeasured:false`. Версии 0.3.63/64/65 были «зелёными» в host-тестах, но субъективно бракованы. Старый `TestHonor064ManualNext` вручную вызывает `ReplacementEngine.sourceBoundary`, то есть **не тестирует реальную кнопку Next → Media3 → ProbeService → SourceEventArbiter**. Расширь тесты на эту цепочку и на **следующий естественный трек**.

## История попыток и неверных гипотез

- 0.3.62: overlap двух версий ~160ms equal-power. Ухо слышит тембровую волну, в конце была ошибка ownership `fade_failed` (исправлена).
- 0.3.63: уменьшили overlap до 40ms; шов остался, frequent seeks возвращали Yandex.
- 0.3.64: 260ms silence-while-seeking с fallback для сети. На partial HTTP ищем блоки 200–350ms, возникали source swaps, 28 commanded gaps.
- 0.3.65: разделили поведение по `streaming.complete()`: на partial Yandex audible во время seek + 500ms dip, на cached/local 260ms старого source-muted hold. Теперь 0 fallback, зато 21 gap и повторные 500ms fade. Полный down-to-zero/up-to-full **является намеренной реализацией**, а не случайным hardware багом; клиент теперь просит музыкально соединить две версии без провала. Простой старый overlap 40/160ms тоже уже проверен и не подходит.

## Что делать тебе, в этом порядке

1. Изучи код и фактическую цепочку Media3. Зафиксируй backup ветку от **последнего кодового** HEAD. Не делай APK/новую версию ради первого патча.
2. Построй **красные** регрессионные тесты, воспроизводящие точные реальные последовательности `manual Next → cached seek 58ms → clock gate/command gap 147ms → natural next → seek`, а также `partial stream → repeated seek → 500ms dip repeatedly`. Используй `ProbeService`/arbiter, а не фиктивный вызов `sourceBoundary` в обход Media3. Нужен тест, который на 0.3.65 падает, с измерением source/decoder command gaps и sequence/epoch.
3. Аудит единого output ownership/state machine: fast cached seek НЕ должен оставлять оба выхода немыми на 40–194ms; partial seek не должен снова и снова запускать 500ms полное затухание. Возможны сохранение оригинала во время silent decoder seek + one final verified join, coalesce multiple scrubs «последний target wins», continuous native-session continuity. Не вводи новое независимое управление громкостью в обход `AudioOwnership`, не ломай паузу, Bluetooth, route, subscription/account fence и boundary.
4. Для начала песни рассмотри контролируемое, действительно синхронизированное короткое перекрытие с проверкой drift/фазово-тембровой совместимости, асимметричной кривой, или другой реально бесшовный дизайн. Не повторяй простой equal-power 40/160ms и 500ms dip. Ограничения захвата аудио чужого приложения на Android изучи официально; **не обещай PCM phase alignment** без разрешений/доказательства возможности. Не добавляй пользователю кнопки/диагностические элементы без необходимости; отдельную диагностику ранее разрешали только для администраторов.
5. Пройди полный host + API36/D8 + real addon test suite + новые replay tests, физический HONOR test plan. Одна общая signed release после системной работы, автораздача через stable manifest/Hostinger. Не выдавай успех CI за акустическое подтверждение.

**Главное:** пользователь пришёл именно за исправлением ошибочного подхода и диагностических пробелов, а не за очередным `fade=80ms`. Обязательно опирайся на полный новый `HANDOFF-2026-10-31-AFTER-0365-HONOR-REVIEW.md` и честно разделяй доказано / гипотеза / ещё не измерено.
