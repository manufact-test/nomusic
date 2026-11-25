# CELIKOM Android A1 — BETA15, диагностика владельца, передача работы (25.11.2026)

**Статус: АУДИОПОДМЕНА НЕ РАБОТАЕТ.** Это подтвержденный owner-диагностический handoff, **не новая сборка** и не разрешение ослаблять гейты. Работу продолжать с сохраненной точки, без переделки архитектуры.

## Проверенные артефакты
- GitHub `manufact-test/nomusic`, одна Android ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Последний CODE checkpoint BETA15 `d2e8aad25d64dc840c722fb97bbe5811f8c52856`. После данного документа HEAD продвинется **только документами**; взять его в GitHub перед правками.
- OWNER TXT `CELIKOM-A1-Diagnostics-1795622037670.txt` (25.11.2026). Build `A1_TRACKID_BETA15_ORIGINAL_CHILD_GATE_DIAGNOSTIC_20261125`. Лог помечен `LOG_TRIMMED`, так что не выводить точный порядок из обрезанных событий.
- JVM CI 45641859216 SUCCESS; publisher-signed native ARM13 + owner-signed export 45641859377 SUCCESS; FlokiNET delivery 45644488030 SUCCESS (APK verified anonymous HTTPS/size/SHA256, ссылка — `A1_DOWNLOAD_URL` в job). Это **не аудиопроверка**.
- Owner уже установил BETA15 и прислал TXT. Тест: Honor 50, Рамиль «Ау», album 38902809, track 144530503, 00:43–00:54. Не запрашивать повторную установку этой же версии.

## Точная новая причина, установленная BETA15
- Серверная цепь работает: `OWNER_RESOLVE_APPROVED=ONE`, `OWNER_RESOLVE_MPEG=ONE`, `OWNER_SIGNED_GRANT_VALID=FEW`, `OWNER_AUDIO_RANGE_VALID=ONE`, `OWNER_LEGACY_REQUEST_BOUND=ONE`, `GRANT_ADMITTED=ONE`, `EXACT_PREPARE=FEW`, `DECISION_ALTERNATE=ONE`. Сетевые/JSON/response ошибки = NONE.
- Подмена не включилась: `DATASOURCE_ARMED/AUDIO_OPEN/AUDIO_READ=NONE`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`.
- Новый BETA15 bridge установлен и вызывается: `ORIGINAL_MEDIAITEM_SOURCE_ANCHOR=FEW`, `ORIGINAL_MEDIAITEM_IDENTITY_CONFLICT=NONE`, `ORIGINAL_CHILD_HOOK_REGISTERED=ONE`, `ORIGINAL_CHILD_ENTER=FEW`.
- **Критичный отказ:** `ORIGINAL_CHILD_CREATOR_MATCH=NONE`, `ORIGINAL_CHILD_CREATOR_MISSING=FEW`. В `lLb.if(dA9,QAa,Of6,gA9)` функция `StageBAudioEvidence.exactOriginalMediaItemCreator(item)` вернула null. Поэтому `ORIGINAL_CHILD_SETTER_MATCH/MISSING/SOURCE_DIFFERENT=NONE`: проверка setter вообще не выполнялась. `ORIGINAL_MEDIAITEM_DESCRIPTOR_LINK=NONE`, `WRAPPER_DESCRIPTOR_LINK=NONE`, factory/data-source link NONE — следствия.
- При этом `TRACK_WRAPPER_LINK=FEW`, `FLOW_TRACK_ALBUM_LINK=FEW`, `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH=FEW` — отдельная структурная дорожка. `EXO_SOURCE_INSTANCE/OPEN/READ=MANY` — **не связанные с альтернативой** события, не доказательство CELIKOM audio.
- `EXACT_BETA_CREATOR=NONE`, хотя `ORIGINAL_CREATOR_KEY_CONFIRMED=FEW`: не считать подтверждение строкового ключа полным доказательством исходной Java identity цепи.

## Исходный код: возможные причины, пока НЕ разделенные
- `StageBAudioEvidence.onOriginalMediaSourceConstructed(source,item)` сохраняет weak Java identity refs `source,item,wrapper` под исходным `cA9` scope. Максимум 16 живых anchors, конфликты fail-closed.
- `exactOriginalMediaItemCreator(item)` может дать null при: (1) null item; (2) **нет точного Java `==`** в anchors, duplicate или conflicted; (3) weak `wrapper/source` уже потеряны; (4) `findByWrapper(wrapper)` отсутствует/двусмыслен; (5) `exactCreatorTrackAlbumOrBetaBeforeSourceSet(wrapper)` отвергает строгий original Track+Album/Flow/birth или beta fallback. **Нельзя утверждать, что конкретно случилось.**
- Сам факт `anchor=FEW` и `child=FEW` не доказывает, что это *один и тот же* MediaItem. `ORIGINAL_CHILD_CREATOR_MISSING` охватывает все перечисленные причины. Нельзя «чинить» это last-seen item, ID вместо ссылки, слабыми допущениями, глобальным кэшем, неверной песней или пропуском авторизации.

## Следующий пул работ — строго в этом порядке
1. **P1 — точечная кодовая проверка:** текущий HEAD + `StageBAudioEvidence.java`, `ExitCallsiteWitness.java`. В неизмененном publisher-signed 2025 original проверить только точный `iLb.<init>(...Of6...)` → `lLb.if(...Of6...)` путь и почему hooks видят разные/совпадающие call chains. Не исследовать всю декодерную архитектуру заново.
2. **P2 — диагностировать один guard:** превратить монолитный `exactOriginalMediaItemCreator==null` в узкие finite reason buckets: no anchor identity vs duplicate/conflict, weak ref loss, wrapper-link absent/ambiguous, original Track+Album creator failure vs beta fallback. Разделить доказанный `item==` и отказ поздней стадии. Не писать реальные ID/URI/tokens/bytes, использовать bounded finite counters, сохранить strict fail-closed.
3. **P3 — тесты:** JVM positive/negative на exact item, wrong item, stale selection, duplicate, weak/GC, original Track/Album, beta deny и повторный трек; в CI signed original XAPK gate и native ARM13. Без модификации оригинала и без открытия альтернативы при неустановленной идентичности.
4. **P4 — только доказанная причина → минимальная правка → build:** после выявления точной причины исправить только этот binding/lifetime/scope, не трогая grant/Range/selected-source guards. Собрать подписанную APK, проверить native ARM13; выдать владельцу **только** проверенный `A1_DOWNLOAD_URL` из FlokiNET workflow `.github/workflows/android-a1-owner-floki-download.yml` в `main`. Если автодоставка не сработает, через `main` `.github/deploy/a1-owner-download-request.json` с успешным source run+attempt. Проверить новым TXT `CREATOR_MATCH` → `DESCRIPTOR_LINK` → `FACTORY/SOURCE_LINK` → `DATASOURCE_ARMED` → `AUDIO_OPEN/READ` → слухом альтернативу. До этого НЕ утверждать, что подмена есть.

## Границы
Не создавать вторую Android ветку; не переделывать проект, бэкенд и API — текущий grant работает. Не трогать LyEa, LCK1, NAV40/NAV45, Windows, extension, stable Android v95 и старые закрытые исследования. Не угадывать ID/source/очередь, не ослаблять безопасность. Все действия пользователя ограничены **установкой APK и отправкой TXT** на одном Honor 50 без ADB/PC.

## BETA16 — 25.11.2026: причина отказа creator ещё не доказана

Из owner BETA15 TXT подтверждены source anchors и child enters, но не exact creator match; setter не проверялся. Для точного выяснения причины в `StageBAudioEvidence.exactOriginalMediaItemCreator` добавлены **только конечные reason counters**: null item, отсутствие anchors / live other item / expired anchors, exact item duplicate/conflict, lost weak wrapper/source, missing/ambiguous wrapper link, original Track+Album failure, beta Track/Flow/issuer rejection. Вся действующая Java identity и authorization/Range логика осталась fail-closed; IDs и URL не экспортируются.

JVM harness дополнен проверками exact item, wrong item, conflict, weak loss, missing creator и repeated wrapper. Build marker: `A1_TRACKID_BETA16_CREATOR_REJECT_REASON_DIAGNOSTIC_20261125`. APK: `CELIKOM-A1-RAMIL-AU-BETA16-HONOR50-20261125.apk`. Оригинальный workflow name сохранён для FlokiNET. Source export run `45651541265` (commit `a24ec32af24a1eec1918a208031acf2dab93745d`); отдельный JVM regression run `45651822165` (CI-only commit `09ce464489ff80eae797f63074dc1ca7878701c6`). Статусы проверить, не считать зелёный CI звуком.

После обеих SUCCESS и успешной независимой FlokiNET доставки получить только свежий `A1_DOWNLOAD_URL` из delivery run. Один телефон: поверх BETA15 установить BETA16, включить Рамиля «Ау» из альбома, 00:43–00:54, прислать TXT. Только её новые reason buckets могут определить минимальную точную правку; не делать source/ID/beta fallback по догадке.

### BETA16 — CI regression, исправление теста и актуальный запуск

Первый экспорт `45651541265` и первая standalone JVM `45651822165` завершились **failure** по одному тестовому ожиданию: `ORIGINAL_CHILD_ITEM_ANCHOR_CONFLICT` регистрируется дважды, поскольку guard вызывается прямо и затем внутри `onOriginalMediaItemDescriptor`. Для этого сценария ожидается `FEW`, не `ONE`. Код идентификации/source authorization не изменён.

Исправление теста: commit `37903af55bf738cc9e1dfa4d2b0ac9ae615ac647`; standalone JVM `45652189632`. Затем найден и исправлен остаточный BETA15 export filename в `ci/owner_phone_diagnostic_artifact.py` и его тесте; финальный commit `18cb4afc5ece3c04c5dd64af32125dcf409d1448`. **Финальный pending подписанный owner ARM13 run: `45652314715`**. APK и ссылка из старого run не подходят, нужен verified delivery именно от финального успешного run. Пока он queued/не завершён — звук/готовая APK не подтверждены.
