# CELIKOM Android Test.45 — два сравнения Test.44, недоступные версии и длинный Next

2026-11-06. Только отдельная Android Test-ветка `feature/android-0385-test45-honor-20261106`. Test.45 **не является эталоном** без прослушивания владельцем. Стабильная Android 0.3.85, OTA, backend, desktop и эталонные backup refs не изменены.

## Диагностика Test.44: 23:34:18–23:40:40 (+03:00)

Получены два private combined-журнала владельца (`...233741.txt`, `...234040.txt`). Второй — продолжение **того же** запуска `0.3.85-test.44`, а не независимая установка; в начале присутствуют архивные Test.43. Приватные журналы и скриншоты в git **не загружать**.

| Уникальный Test.44 | До 23:37:41 | После 23:37:41 |
| --- | ---: | ---: |
| `replacement_transition_complete` | 31 | 17 (14 same-song, 3 exclusive single turn) |
| `replacement_resolve(found:true)` | 31 | 14 |
| `replacement_resolve(found:false)` | 2 | 3 (две разные ID) |
| `replacement_join_exception` | 0 | 0 |
| `backend_result(ok:false)` | 0 | 0 |
| Медиана source boundary → обычный same-song join | ~0.60 c | ~0.56 c |
| Максимум source boundary → обычный same-song join | 2.81 c | 5.00 c |

В каждом отрезке owner сравнивал работу с опцией плавного перехода Яндекс.Музыки и без неё. **Ни приватный JSON, ни Android Media3 API не содержат фактическое значение этой настройки**; нельзя по журналам присвоить режим определённому интервалу и тем более объявить исчезновение «пшика». Также нельзя принимать `audio_command_anomaly` с `classification=expected_same_song_blend` за дефект: это намеренное одновременное командование громкостью оригинала и замены. Все `replacement_join_transport_summary` имеют `sourcePcmMeasured=false,phaseVerified=false` и фиксируют только транспортный drift. Ни одна из двух частей не подтверждает акустический эталон.

## Конкретные отказы каталога

- Для четырех уникальных определённых Yandex track IDs сервер `resolve` ответил **HTTP 200, found:false, replacement_id=0**: `34483761`, `53886987`, `108864304`, `61007010`; последний `108864304` повторился. Обе песни, показанные владельцем на последних скриншотах, соответствуют `108864304` и `61007010` (album lookup однозначен по названию, автору и длительности).
- На всех других многих треках backend `found:true`, поэтому не выявлено глобального отказа сети/сессии/подписки. Звук оставался только оригиналом преднамеренно после `found:false`.
- Desktop-подмена, по слову владельца, ранее играла. Нужно **read-only сопоставить сохранённый `tracks.service_track_id` с мобильным Yandex ID и проверить active/status/storage**. Серверный `ResolveService` скрывает причины в общем `found:false`: отсутствие активной exact-ID записи, неразрешённый MIME (но Android отправляет `audio_formats=mp3,m4a`), либо несуществующий файл. Без доступа к живой БД **причина не установлена**, нельзя объявлять владельцу, что он не одобрил загрузку, или бездумно применять title-only fallback к иной редакции.
- Test.45 **не меняет** backend/каталог/Track ID. Отсутствующие версии не считаются устранёнными.

## Установленный источник части длинных Next

Сопоставлены source boundary, prefetch promotion, fresh resolve, current wait, download callback, sparse start и join:

| Частный кейс | Source boundary → join | Причина |
| --- | ---: | --- |
| Трек ~299 c, source 56.039 | 2.522 c | Full-file successor downloaded поздно, `current_wait` ~1.108 c, затем локальная подготовка |
| Трек ~273 c, source 60.677 | 2.806 c | Full-file in-flight, **1200 ms ожидания впустую**, cancel, restart sparse и alignment |
| Трек ~298 c, source 82.323 | 2.593 c | Та же схема: **1200 ms впустую** перед sparse |
| Трек ~139 c, source 366.255 | 5.001 c | До resolve ~2.0 c, затем sparse warm + decoder demand, runway/seek: другой случай, **Test.45 его не чинит** |

Безопасный узкий Test.45: только для progressive cold Android, если на момент **свежего current resolve** ранее предзагружаемый полный файл длинной песни **≥240000 ms всё ещё скачивается**, wait для его готовности **400 вместо 1200 ms**. Если файл успевает закончить в первые 400 мс — прежний reuse; если нет — вызывается уже существующий verified sparse fallback, прежний speculative token отзывается. Для коротких треков (в т.ч. фактический быстрый 203700 ms с успешным 749 ms wait), фазы `resolving`, всех frozen full-file путей и готового кэша поведение **не изменено**. Данных для улучшения качества стыка по PCM нет: Test.45 **не перестраивает** fade, не включает Test.40 strict gate, не возвращает persistent DSP Test.37.

Test `Test45LongPrefetchHandoff.java`: длинный promoted current не блокируется после 400 ms, новая работа идёт под свежим resolve, старые speculative callbacks не получают владение звуком; короткий и frozen режимы сохраняют прежние дедлайны. Полный host/Android CI и APK signed provenance — в отчёт дописать после подтверждения сборки.
