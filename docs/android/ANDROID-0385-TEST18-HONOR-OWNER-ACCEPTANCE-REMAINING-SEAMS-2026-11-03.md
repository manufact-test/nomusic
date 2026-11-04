# CELIKOM Android — Test.18: принятие владельцем и точные остаточные проблемы
Дата: 2026-11-03. **Владелец признал Test.18 новым лучшим акустическим кандидатом для дальнейшей работы; это не означает, что все seek и pause исправлены.** Не публиковать полные личные журналы или видео.

## Контрольные точки
- Тестовая версия `0.3.85-test.18/code86103`, отдельный пакет `pro.celikom.nativeprobe.test`; functional SHA `19ebf98344b02ec8a8088595ee8dca7740c0396c`; HEAD до нового docs `1a19ccec674d41b7417f29715d853eb693595687`.
- **Новая неприкосновенная backup Test.18**: `backup/android-0385-test18-best-owner-20261103` на SHA `1a19ccec674d41b7417f29715d853eb693595687`.
- Старая независимая backup Test.15: `backup/android-0385-test15-best-owner-20261103` на SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003`. Test.16/17 отвергнуты.
- CI Test.18 SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/41704016656 ; correct signed artifact: https://github.com/manufact-test/nomusic/actions/runs/41704016656/artifacts/13265222571 .
- Stable `0.3.85/code86`, Hostinger OTA/stable.json, подписанный оригинал, backup-ветки, PR #37 и Android permissions не менять. Новые эксперименты только на `feature/android-0385-test15-permissionless-recovery-20261103`.

## Из приватного Test.18 HONOR прогона
Только сегмент `run_start` version `0.3.85-test.18` от 23:25:47 (+03) в локальном `CELIKOM-combined-20261103-232845.txt` и локальном видео `SVID_20261103_232559_1.mp4`. Первые сегменты файла — старые Test.16/17, их не смешивать. Ни сырьё, ни полный список прослушиваний в GitHub не помещать.

Владелец слышит почти бесшовные переходы на многих песнях, но первый мгновенный аккорд остаётся слышимым, особенно у Триагрутрика и Johnyboy.

30 `album_observation`, **24 первых joins** до следующего трека, **50 всех joins** с повторными входами после перемоток. Интервал «album observation → replacement_transition_complete» для 24 начальных joins: медиана **329 мс**, **18/24 до 500 мс включительно**, **4/24 >1000 мс**. Это телеметрический handover, **не акустический PCM gap**. Первые холодные треки 3924 и 2334 мс; нельзя утверждать причинную разницу с Test.15 без парных условий сети/кэша.

- **Триагрутрика «Биг сити лайф»**, id `40371622`: 118444→118792 = **348 мс**. На начале с резкой атакой даже такой стык может быть слышен.
- **Johnyboy «Метамир»**, id `42601865`: 141201→142835 = **1634 мс**. В 141366 `replacement_lookahead_prefetch_current_wait`, необходимый ранее начатый transfer готов только в 142389 (`replacement_download.elapsedMs=2184`), затем prepare/prewarm/guard; **файл был не готов**, здесь нельзя лечить одними интервалами polling.
- **RASKOL «Нас не понимают вообще»**, id `42884423`: join **209 мс** (97599→97808), initial alignment seek/ACK/complete отрабатывает. Однако на видео Yandex UI перематывают примерно 0:46→3:22, тогда как Media3 `playback_health` t101787 читает sourcePositionMs=4254. В этом промежутке нет `SAME_ITEM_SEEK` / `source_discontinuity` и **нет нового** `replacement_seek_request`. Значит, CELIKOM не получает новые транспортные координаты от внешней сессии; не ломать принятый internal seek/ACK, который способен обработать опубликованные позиции.
- **«Дым» Лёша Свик**, id `39949113`: владелец сообщил, что пальцем перематывается хорошо, но Pause→Play **не проверена**. ВАЖНО: это **не свидетельство исправленной перемотки подмены**. Уже на предыдущем треке «Скажи» t148756 сработало `replacement_stop_state reason=replacement_stop_cannot_mute_original`, t148790 `replacement_trial_stop reason=cannot_mute_original`: защитное отключение всей автоподмены. При «Дым» t156895 сработало recognition, **не было** replacement resolve/prepare/join; `playback_health` t158030/t163080: `replacementArmed=false`, `replacementReady=false`. Поэтому в этом эпизоде владелец перематывал **оригинал Яндекса**, не звук CELIKOM. Защита от двух одновременных потоков сработала, но подмены не было.

## Архитектурный вывод — не чинить каждую песню отдельно!
Есть **три системных класса** с похожими внешними симптомами:
1. **Внешняя Media3 session не публикует seek или отдаёт старую позицию** (RASKOL, исторически и Дым в Test.15/16). При этом собственные seek/ACK работают, когда есть входные данные.
2. **Текущий audio file не готов в момент старта** (Johnyboy: promoted speculative transfer), поэтому появление нашей подмены реально задержано.
3. **Cannot mute original** → корректное fail-closed прекращение trial, после чего на остальных песнях звучит только Яндекс (включая Дым). Нельзя это принимать за победу исправлений seek.
Никаких trackId-исключений; trackId — только безопасная связь диагностики с метаданными.

## Направление следующей разработки, без новой микро-APK
1. В `ProbeService` текущий controller через `SessionToken(TYPE_LIBRARY_SERVICE)`. Проверить **второй независимый, read-only Media3 controller с `getConnectedToken()` / прямым `TYPE_SESSION`**, сравнивать свежесть position, isPlaying, playWhenReady и событие discontinuity двух наблюдателей; generation/lifecycle, no commands. Это **гипотеза, НЕ исправление**. Официальные источники: https://developer.android.com/reference/androidx/media3/session/MediaController ; https://developer.android.com/reference/androidx/media3/session/MediaController.Builder ; https://developer.android.com/media/media3/exoplayer/listening-to-player-events . Legacy MediaBrowser уже тестировался, unavailable; не повторять как новую идею.
2. Для первых нот замерять отдельно source first-playing, lookup, transfer/queue, decoder-prewarm, verified guard и собственный output clock. Не путать `commandDelayMs` десятки миллисекунд с полной задержкой. Пересмотреть полнофайловый lookahead с безопасной foreground-приоритетностью и кэшем; не возвращаться к параллельным audio workers или опасным fade/gain. Официальная концепция preload: https://developer.android.com/media/media3/exoplayer/preloading-media/preloadmanager .
3. Изучить `cannot_mute_original` и корректную, неопасную recovery-стратегию; **никогда** не запускать два слышимых потока. Добавить host regression на fail-closed и повторную доступность эффекта.
4. Собственный `AudioTrack.getTimestamp()` может отслеживать лишь output CELIKOM, **не чужой PCM Яндекса**: https://developer.android.com/reference/android/media/AudioTrack . Не заявлять phase-verified join, пока это не измерено.
5. Защитить frozen seek/ACK, pause/resume обычных треков, original stable, permissions; полный CI, подписанный APK и **одна совокупная Test** только после обоснованного пакета.

Будущая акустическая проверка Дым должна сначала подтвердить, что подмена **включена и активна**, затем отдельно finger scrub и Pause→Play. Если статус `replacementArmed=false`, результат относится только к Яндексу. Никаких дополнительных permissions, Accessibility, NotificationListener, root или скрытых API.
