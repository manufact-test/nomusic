# CELIKOM Android Test.47 — устранение гонки при Next и сохранение кэша (06.11.2026)

## Статус

- Изолированный пакет `pro.celikom.nativeprobe.test`, `0.3.85-test.47`, versionCode `86132`.
- Ветка: `feature/android-0385-test47-session-stability-20261106`.
- Предыдущая подписанная Test.46: functional source `e0ec5f7e80938ce18c2747e14f3425bcd360c34b`, APK SHA-256 `14a91c03c153f7ce3af32b6be286641f52b51d96af7ba36033a2febaa4f5541d`.
- Предварительно создана резервная точка Test.46: `backup/android-0385-test46-pre-test47-20261106` → `77f393785371dd9a01f8c27f655e5682584730d4`; Test.33 `53d94d66a32b332b62848e0895285d81dda226e9` и её backup остаются отдельно, без изменений.
- Функциональный SHA подписанной сборки: `9c90a73fc87a0b9b12d6c4da66c98028b14073cc`; [GitHub Actions #42206692807 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42206692807) — host regression, SDK36/D8 и отдельная подписанная тестовая APK.
- [Прямая APK Test.47 в ChatGPT Library](https://chatgpt.com/library?file_id=libfile_8dc571f14c5481919d79fca6929cfed6&account_id=personal), размер 8 824 985 байт, SHA-256 `8a02d9f66ada3d02d6793b57dfcd66872ced15836a6a5e67166bc908fb7fbd15`. Подписант совпадает с оригиналом, v3-подпись подтверждена. **Физическая акустическая приёмка не выполнена**.

## Источник и разделение трёх сессий

Приватный owner export `CELIKOM-combined-20261106-114211.txt` (7869 строк, 3 MiB). Архив содержит независимые сегменты:

| Версия | Старт JSONL | Длительность | Unified joins | Runway waits | Lookahead cancels | Commanded silence ≥40ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Test.44 | 4 | 390.45s | 45 | 8 | 8 | 1 (50ms) |
| Test.45 | 3661 | 263.53s | 37 | 8 | 12 | 2 (96ms, 65ms) |
| **Test.46** | **6733** | **101.34s** | **14** | **5** | **1** | **2 (167ms, 155ms)** |

Числа относятся к командному аудио-транспорту, не к PCM или измеренному speaker output. `manualNextButtonObserved:false` не позволяет точно классифицировать каждое `SEEK_TO_OTHER_ITEM` как нажатие Next; причинность ручного и естественного переключений требует owner-оценки.

### Доказанный проигрыш из Test.46, 42–45 секунд

1. `42258ms` — speculative lookahead `48592121` запущен при перестановке очереди.
2. `42925ms` — пользователь перешёл к этому треку, а download ещё в своей **1100ms отложенной очереди**.
3. `43125ms` — свежий current resolve успешно авторизовал песню, но старый код ожидал именно полный speculative файл.
4. `44325ms` — истекли дополнительные **1200ms** ожидания; speculative transfer отменён, `44335ms` — начало validated sparse.
5. `45402ms` — стартовал переход (около 2.39с после boundary; source original сохранялся audible).

Этот дефект не зависит от конкретного Track ID: если Next происходит в пределах 1100ms между запуском speculative загрузки и её отправкой, полный файл физически не может быть готов, но старый код всё равно тратит 1200ms до аварийного fallback.

### Длительная навигация и кэш

Test.44/45: в сумме 44 удаления готовых файлов, значительная часть по `entry_limit` при лимите 12 и оставшихся 70–95MiB данных (потолок 96MiB). Это подтверждает, почему ранее успешно закэшированная песня позже может снова стать `stream`. Изменение повышает число записей до 16 **не увеличивая лимит байтов 96MiB**. Треки с крупными файлами по-прежнему вытесняются по памяти.

### События, которые не выдаём за исправленные

- Test.46: два `commanded_silence` по 167 и 155ms после `SAME_ITEM_SEEK` к концу песни, при сохраняемом единственном владельце `REPLACEMENT`. Утверждать о фактической тишине на динамике нельзя: не измерялся PCM; принятый быстрый in-place seek Test.33/предшественников не переписывали.
- В Test.46 также был `quiet_buffering_snapshot` и повторное Media3 подключение около 74с: текущая подготовленная песня не перехватывала системный pause/buffering. Слепое форсирование Yandex Play запрещено, watchdog оставлен.
- Акустический «бжык» и отличие Yandex crossfade ON/OFF не определяются точно по одному transport journal. Два независимых PCM-потока и задержки системного DSP сохраняются; обещать идеальную фазовую стыковку нельзя.
- Четыре mobile ID с backend `found:false`: `34483761`, `53886987`, `108864304`, `61007010`. Каталог/загрузки — другой чат; никаких title-only Android обходов.

## Один связанный пакет Test.47

1. **Next во время speculative queue grace:** после свежего live resolve перед ожиданием смотрим, действительно ли полный файл мог уже начать скачиваться. Если `downloading` всё ещё в гарантированной 1100ms отложенной очереди, текущая песня сразу начинает прежний безопасный validated sparse путь, без ложного ожидания дополнительных 1200ms. Устаревший callback/speculative файл не получает права на аудио.
2. **Текущий decoder впереди speculation:** если на текущей песне ещё выполняется первичная подготовка, не запускаем конкурирующую полную фоновую загрузку следующей. Media3 sample повторит попытку после readiness; никакой бесконечной очереди deferred callbacks.
3. **Консервативное сохранение тёплых треков:** 16 вместо 12 проверенных complete files в пределах прежних 96MiB, только после повторного server resolve. Содержимое подписано/проверено тем же контрактом, как ранее.
4. **Снижение побочных затрат частой навигации:** повторные sampling ticks не засоряют журнал одинаковым `replacement_lookahead_prefetch_promoted_inflight` каждую четверть секунды. Лог при смене phase сохраняется.
5. **CI guards:** новая `Test47CurrentFirstStability` на real ReplacementEngine с fake transport: early Next, отмена stale download, foreground precedence, ready prefetch, дедупликация; адаптированные старые handoff/long-prefetch/cache тесты, тесты согласованного лимита и неизменности системного источника.

## Стабильность и границы изменений

- Не трогать owner-accepted Test.33 (исходный commit, backup branch и подписанный эталон), Test.23/Test.28 backup refs, production `0.3.85/code86`, desktop Chrome, Hostinger/OTA, backend/catalog, credentials/permissions.
- Стабильный seek/completeSeek и отклонённый strict Test.40 не изменены. Оригинал сохраняет аудио, пока подготовка/проверка current не завершена.
- Фоновая speculative full-download задержка 1100ms не удалена: изменена только её отмена при доказанном приоритете текущего трека.
- Проверка на HONOR после единственной подписанной APK: активный ручной Next в первые секунды, естественный Next, 10–20 минут shuffled browse, повтор ранее прогретой песни, Yandex smooth transition ON/OFF, случаи сохранения корректной original audio. Сравнивать с Test.46 и golden Test.33; собрать один combined log и субъективную оценку.

## Контроль качества

- Локальная полная fake-engine/phone regression suite: **PASS**; 15 виртуальных часов, 300 переключений, source/pause/seek, Test.33 accepted seek guard, Test.47 race guards.
- APK, SDK36/D8, source provenance, original signer и отсутствие stable publisher: обязателен отдельный GitHub CI success; локальный хост не доказывает подписанную сборку.
- GitHub CI #42206692807: **SUCCESS**; `native-android` и `build-celikom-test / build-test-app` завершились успешно. Подписанный Test.47 только в отдельном пакете `pro.celikom.nativeprobe.test`; stable publisher SKIPPED, `stable_published=false`, `stable_ota_touched=false`, `hostinger_write_performed=false` в build receipt. По поручению владельца решение о возможном переносе тестовой в основную версию отложено до проверки на HONOR и нового обсуждения.
