# CELIKOM Android — передача после физической проверки 0.3.65, 31.10.2026

**СТАТУС: 0.3.65/code66 опубликована, но пользователем по качеству звука НЕ ПРИНЯТА. В этом заходе исправления, новые APK и релизы ЗАПРЕЩЕНЫ: только анализ и документация.** Это актуальнее всех прежних handoff-документов, особенно устаревшего `NEXT-CHAT.md` с датой 0.3.61.

## 1. Репозиторий и безопасная точка продолжения

- GitHub: `manufact-test/nomusic`; рабочая Android-ветка `feature/android-unified-preparation-seek-gate`.
- Последний **подписанный исходный код 0.3.65**: `37d7ff699a7cae0e051cf5dfcb63ca7a7f23c90f`. CI Android SDK36, D8, архив, сертификат, autopublish: https://github.com/manufact-test/nomusic/actions/runs/41189834456 — SUCCESS.
- Постоянный APK: https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/ . Обновление приложения через кнопку **«Проверить обновление»**. Manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json . Версия 0.3.65/code66, SHA256 APK `81301b78f15cf70ea151f7f260dac5bd4f1966adec0ca1242fe20970041f68f5`, 8,734,793 bytes. Оригинальный signer SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Была проверена SHA256 обоих URL и manifest. Signing secrets не хранятся в Git.
- **Документационный коммит после 0.3.65 может сдвинуть HEAD, но не должен менять Android-код, версию, release-spec, workflow или APK.** Актуальный подписанный code anchor остаётся SHA выше. GitHub workflow `android-0348-validation.yml` запускается только при изменениях в `android/native-companion/**` или указанных workflow; docs-only push сам по себе НЕ запускает новую подписанную публикацию.
- Только Android: **НЕ ТРОГАТЬ** desktop/extension, backend, catalog, accounts, Hostinger update center/site, Yandex ad module. Сохранить прежний signer/package/updater. Пользователь не принимает мелких отдельных APK. Yandex плавные переходы пока выключены.

## 2. Новое сообщение владельца (итог физического прослушивания 0.3.65)

1. В начале трека вместо старого «пшика» слышна очевидная **полная яма громкости: исходная песня затухает до нуля, потом CELIKOM появляется с нуля**. Это приятнее «пшика», но НЕ бесшовное соединение. Пользователь ожидает непрерывный, музыкально незаметный переход; предлагаемый им overlap нельзя считать автоматически безопасным без синхронизации.
2. Когда новый трек начинается сам и пользователь не нажимает кнопку Next, пауза/возобновление/перемотка **по субъективной оценке работают нормально**.
3. **После ручного Next в Яндекс Музыке** перемотка начинает прыгать/лагать. По словам пользователя, дефект может продолжиться и на следующих треках после их естественного завершения. Не сводить задачу к одному первому треку; проверить целую цепочку `natural → manual Next → multiple scrubs → natural next → scrubs → pause`.
4. Пользователь подозревает, что наши прежние выводы по диагностике и успешным тестам слишком оптимистичны. Следующий разработчик обязан сначала проверить модель событий и доказательность диагностики, не выпускать промежуточные «ещё чуть-чуть исправленные» APK.

## 3. НАСТОЯЩИЙ журнал с телефона

Владелец приложил **`CELIKOM-combined-20261031-130513.txt`** (2335 строк, 580222 bytes). **Не коммитить полный пользовательский журнал в публичный репозиторий.** Это combined из трёх запусков: 0.3.63 — строки 4–786 (12:01:49+03); 0.3.64 — 787–1486 (12:23:30+03); **0.3.65 — 1487–2335 (13:02:51+03; 140.58s)**. Новому чату нужен только последний сегмент для новых выводов; по необходимости попросить вновь приложить оригинал. Примеры `sed -n '1487,2335p' FILE | jq -Rr 'fromjson? | select(.event=="replacement_sync") | ...'`.

| Сигнал команды/события | 0.3.63 | 0.3.64 | 0.3.65 |
| --- | ---: | ---: | ---: |
| `replacement_sync` со `state=seek` | 38 | 36 | 41 |
| `replacement_scrub_hold` (260 ms) | 0 | 30 | 22 |
| `replacement_scrub_fallback` | 0 | 8 | **0** |
| `audio_command_anomaly=commanded_silence` | 0 | **28** | **21** |
| `replacement_exclusive_dip_start` (500 ms) | 0 | 0 | **18** |
| завершённые 500ms dip | 0 | 0 | **17** |
| подтверждённые `replacement_source_boundary` | 9 | 5 | 7 |
| `replacement_recovery` | 5 | 2 | 2 |

**Оговорка:** длины/сценарии трёх запусков разные, сравнивать абсолютные числа как «качество на минуту» некорректно. 0.3.65: 8 распознанных треков, 7 подтверждённых границ и 41 decoder seek за ~140s. `replacement_recovery` в этом запуске только `replacement_completed` и `source_end`, то есть нельзя объявить все подёргивания «крашами» или длительным network stall.

### 3.1 Уже скачанные песни тоже дают слышимые остановки — прежняя гипотеза была неполной

- «Не стесняйся» (`48592143`): поток **полностью cached на 7324ms**. Затем user seek на **10185ms** (позиция 32430, drift 26107), `replacement_scrub_hold` 260ms, callback seek за **58ms** (10240ms), clock advancement в 10327ms; `audio_command_anomaly=commanded_silence` на 10331ms длительностью **147ms**. На этой песне ещё 5 аналогичных командных провалов; максимальный по этому треку **194ms**. То есть даже быстрый decoder seek оставляет без программно командованного звука заметный интервал.
- «Метамир» (`42601865`): cached на 41579ms; на 42721ms команда быстрого seek, callback **44ms**, отмечен **142ms** commanded silence на 42851ms. На треке 6 таких событий, хотя сам seek быстрый.
- «Хлоп-Хлоп» (`42498648`): cached на 58235ms; на 65950ms seek callback **53ms**, зафиксирован **136ms** commanded silence на 66084ms. Всего 6 событий, вплоть до 183ms.
- «Скажи» (`27317260`) и «Бошки Дымятся» (`108484219`) также показывают краткие command gaps. Итого **21** `commanded_silence` в 0.3.65; значения из логов **43–194ms**. На всех этих примерах **нет** `replacement_scrub_fallback` — отсутствие fallback больше НЕ является критерием успеха.
- Ключевая ветка `ReplacementEngine.seek()`: если `streaming.complete()` или local file, `shortScrub=true` оставляет Yandex muted, decoder pause/seek/ramp; 260ms таймер лишь аварийный. Это создаёт **0 звука, пока decoder не подтвердит seek и clock**. В реальном журнале clock/wakeup добавляют задержку уже после 20–77ms самого seek.

### 3.2 Частично загруженные песни — обратная крайность: 500ms dip при каждой перемотке

- «Каменные цветы» (`48591846`): поток готов на 115710ms, полностью cached только на **125669ms**. Первый вход CELIKOM — dip 116017→116532ms. После перемоток новые dips стартуют на **120148, 121430, 122583, 124139, 124938ms**. Часть событий прерывается очередным seek. На 123980ms decoder seek занял **419ms**, residual 362ms, потребовалась ещё коррекция 31ms. Это не единичное «появление» песни — 500ms полное затухание повторяется при scrubs.
- «Крылья (Другая версия)» (`50163063`): cached только на **140580ms**, три дополнительных dip после seek на **132867, 134302, 135540ms**. Разница с cached path реальна и заметна по ощущениям.
- По выборке 0.3.65: 18 dip запущено, 17 завершилось; отсутствие `commanded_silence` на этих частичных streams не доказывает плавность — лог мониторит команды и маркирует intentional dip иначе.

### 3.3 ДИАГНОСТИКА НЕ ДОКАЗЫВАЕТ «нажатие Next» и реальный звук

- Каждый из **7** межтрековых `source_discontinuity` в этом запуске содержит `reasonCode=1`, `userSeek=true`, `automaticTransition=false`, смену `oldAlias→nextAlias` и индекса. Некоторые переходы рядом с концом песни (например «Метамир» 281982ms из 286730ms), другие далеко от конца. Из одного reason code не выводить точно, что пользователь 7 раз нажал Next; это событие позиционного изменения Media3, а не протокол реальной кнопки. Сравнивать с отдельным `onMediaItemTransition(reason)`, текущим live alias и позицией/длительностью. Документация Android Media3: https://developer.android.com/media/media3/exoplayer/listening-to-player-events .
- `SourceEventArbiter.discontinuity()` правильно отличает межтрековый BOUNDARY от same-track SEEK по index/alias; `ReplacementEngine.sourceBoundary()` очищает `explicitSourceSeek`, `sourceSeekedThisTrack`, `pendingStreamScrubJoin`. Журнал подтверждает вызовы boundary, поэтому **«глобально зависший флаг после Next» НЕ ДОКАЗАН**, хотя другое состояние/очередь или Yandex playback может переживать событие. Нужна проверка последовательности через настоящий `ProbeService` и следующий трек.
- `AudioContinuityMonitor` считает команды `sourcePlaying&&!sourceMuted` и `playerPlaying&&commandedReplacementVolume>0`, **не** измеряет реальный вывод динамика, DSP задержку, фактическую фазу, заикание Bluetooth или буфер Yandex. `hardwareOutputMeasured:false` в логах обязателен; называть это **commanded silence**, а не доказанной физической тишиной.
- `TestHonor064ManualNext` 0.3.65 вручную вызывает `ReplacementEngine.sourceBoundary("manual_next_button")` в fake-плеере; **НЕ моделирует действительное** Media3 `onPositionDiscontinuity` → `SourceEventArbiter` → `ProbeService` + асинхронные callbacks Yandex. Ранее он прошёл 48 assertions, но не обнаружил 21 реальный gap. Это серьёзный дефект охвата тестов, не свидетельство исправления кнопки Next.

## 4. Что уже пробовали — НЕ повторять без новых доказательств

| Версия | Идея/результат HONOR | Чего не решила |
| --- | --- | --- |
| 0.3.62 | равномощный overlap той же песни ~160ms; на почти последнем tick `fade_failed` / повтор через 5s — исправили финальный ownership tick | владелец слышал тембровую «волну», иной тон/скорость даже без пшика |
| 0.3.63 | сократили blend до 40ms | всё ещё заметен шов, finger seek делал частые Yandex↔CELIKOM перехваты |
| 0.3.64 | скрыли прежний оригинал во время finger seek до 260ms, после срока source fallback; короткий cached seek стал лучше | реальный HTTP partial seek 200–350ms пересекал deadline, появились swap, 28 commanded gaps |
| 0.3.65 | partial stream держит Yandex до готовности, затем 250ms source-down+250ms replacement-up; loaded seek оставлен 260ms muted | убран «пшик», но полная тишина посередине; на loaded песни 21 gap, на partial — повторяющиеся 500ms dips, ручной Next и дальнейшие треки всё ещё плохи |

Сама 0.3.65 не меняла desktop/backend/site/update-center и была подписана правильным ключом. Статус **QA RED**, хотя все host/CI тесты PASS. Не маскировать несовпадение словами «всё починили».

## 5. Технические файлы, ответственность, ограничения

- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/ProbeService.java` — настоящий Media3 controller, `onPositionDiscontinuity`, `onMediaItemTransition`, 250ms sample, последовательность событий.
- `.../SourceEventArbiter.java` + `SourceTransitionGate.java` — граница против перемотки, stale alias/index.
- `.../ReplacementEngine.java` — `update`, `sourceBoundary`, `sourceSeekRequested`, `seek`, `restoreScrubSourceAtDeadline`, `fade`, buffering/pause/route; фактические shortScrub vs partialStreamScrub и 500ms dip.
- `.../AudioOwnership.java` — **единственный** authority session effect / source gain / decoder commands; fence ownership, ticket/epoch/seek callbacks, exclusive grant, legacy guarded blend.
- `.../AudioContinuityMonitor.java` — видит только commands, НЕ hardware. `BufferedAudio.java` — per-block HTTP range + `complete()`; `ClockSupervisor.java` — drift decision.
- Тесты: `TestHonor063SeekScrub`, `TestHonor064ManualNext`, `TestHandoverClock`, `TestStreamingEngine`, `TestUnifiedAudioTransactions`, `TestSourceEventArbiter`, `TestResumeClock`, `TestLongRun`, `check_audio_architecture.py`.
- Старые дизайны: `docs/android/ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md`, `REGRESSION-GATES-2026-10-29.md`, `ANDROID-0364-SEEK-SCRUB-2026-10-31.md`, `ANDROID-0365-MANUAL-NEXT-SCRUB-AND-DIP-2026-10-31.md`. Сверять с самым новым handoff.

## 6. План следующего чата: сначала противоречивые тесты, затем одна архитектурная правка

1. **Зафиксировать baseline 0.3.65** и сохранить backup HEAD перед любыми audio изменениями. Не обновлять версию сейчас. Прочесть полную историю в этом файле, не просить Илью заново пересказывать.
2. **Красный интеграционный replay** из фактического журнала: старт auto-песни → ручной Next через Media3/index/alias → 6 быстрых seeks на cached song с playbackState=BUFFERING → естественная граница → снова 6 seeks на следующем cached song. Отдельно HTTP partial seeks, порой с коррекцией/другим seek поверх текущего. Не подменять Media3 event ручным `sourceBoundary()`; проверить реальное `ProbeService`/arbiter и обнуление всех flags/leases. Сохранять старые pause/route/stop tests.
3. Разделить **(a) реальный seek-to-new-position**, **(b) декодер готов/пошёл его clock**, **(c) output ownership**. **Не глушить оба аудиоисточника только из-за seek на уже cached файле**, пока новый decoder ещё не продвинулся. Аккуратно провести ownership через одну транзакцию на последний desired target (last scrub wins), отменяя устаревшие callbacks/dip. Устранить 21 commanded gaps и повторный join не фальшивым таймером, а строгим event/clock состоянием. Для fail-open оставить оригинал, для paused source не оживлять audio.
4. **Плавное начало — отдельная задача** с проверенной синхронизацией. Простая равномощная накладка 40/160ms раньше давала «волну» из-за несовпадения фаз/тембра, а 500ms exclusive dip буквально делает яму. Оценить один проверенный короткий crossfade (предварительный sync/drift, громкость/phase continuity, асимметричные кривые, без повторного старта на scrub), сравнив с минимальным без-overlap перехватом; подобрать по реальным записям/телефону, не по придуманных equal-power гарантиям. PCM-correlation с Yandex **не обещать**: Android playback capture доступен лишь при разрешении владельца аудио и ограничениях платформы; возможен `Visualizer` при `RECORD_AUDIO`, но его данных может не хватать для фазы/устранения comb filtering. См. https://developer.android.com/media/platform/av-capture и https://developer.android.com/reference/android/media/audiofx/Visualizer . Не запрашивать новые разрешения или запись звука без отдельного обоснования и согласия владельца.
5. **Новые release gates:** ни одного непреднамеренного commanded silence >=40ms в seek сценариях, нет множественных полусекундных dip при серии finger seeks, правильные границы after Next и после auto next, нет лишних downloads/decoder recreation/effect ownership, не сломаны пауза/resume/BT/tails/unknown tracks. Дополнить duration distributions (seek call, native callback, clock gate, DSP attach, target readiness) и источник действия + transition generation. Логика аудио не должна зависеть от `userSeek` при cross-item BOUNDARY.
6. **Только потом** один общий Android APK с тем же подписанным updater, CI SDK36/D8/host+addon tests и live manifest/SHA check. Физическая оценка HONOR — отдельное обязательное доказательство, тесты не подтверждают звук. Не добавлять новые пользовательские кнопки; в прошлом владелец разрешал новые диагностические UI только администрации.

**Неустановленный пункт:** почему после **первого** ручного Next субъективно ломаются даже естественные следующие треки. Журнал устанавливает последующие межтрековые границы и command gaps, но не доказывает именно долгоживущее состояние `sourceSeekedThisTrack`. Следующий чат должен подтвердить/опровергнуть эту причинную связь на реальном event sequence, а не строить исправление только на идее «частичный HTTP-кэш».
