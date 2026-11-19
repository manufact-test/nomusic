# CELIKOM Android A1 — канонический переход после NAV45

**Дата:** 19.11.2026. **Состояние:** диагностика NAV45 с HONOR 50 изучена; новый APK не нужен до доказанного следующего шага. Это документационный checkpoint. Исходники NAV45 и подписанные файлы не менялись.

## Репозиторий и неприкосновенные точки

- GitHub: `manufact-test/nomusic`.
- Единственная рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Подписанный NAV45 **код и выпуск**: `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8` — [Android 13 ARM CI #44552661805, SUCCESS 27/27](https://github.com/manufact-test/nomusic/actions/runs/44552661805), artifact ID `14545670017`.
- **NAV40:** исходный принятый и подписанный `34cb32c88a11743a64c9f4814fa71957223a1391`; неизменная ветка `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` проверена на том же SHA. Ничего в ней не переписывать. Не трогать подписанные NAV43/44/45, эталон Android Test.50, Windows и production.
- Полный результат телефона: [ANDROID-A1-NAV45-OWNER-PHONE-BLANK-MEDIAITEM-ID-20261119.md](ANDROID-A1-NAV45-OWNER-PHONE-BLANK-MEDIAITEM-ID-20261119.md). История и текущая каноническая точка: [NEXT-CHAT.md](NEXT-CHAT.md).

## Последний файл владельца

`CELIKOM-A1-Diagnostics-1795102532842.txt` от 19.11.2026. В нём есть исторические части NAV44; для вывода использовать **последнюю секцию NAV45** с `NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY`.

- `CURRENT_MEDIAITEM_SOURCE=REGISTERED` и `CURRENT_MEDIAITEM_LOGICAL_ID=REGISTERED`.
- `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF=NONE`, `DIFFERENT=FEW`, `UNAVAILABLE=NONE`, `SLOT_CHANGED=NONE`. Два разных объекта Java не доказывают, что это разные песни.
- `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH=NONE`, `DIFFERENT=NONE`, `BLANK=FEW`, `UNAVAILABLE=NONE`. Хотя бы один оригинальный `MediaItem` содержит пустой final String; **путь MediaItem ID закрыт как непригодный для достоверной идентичности**.
- `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`, `...NO_LINK=MANY`, `...SLOT_CHANGED=NONE`; оригинальные Player PeriodID ↔ SLOT_B ↔ `TrackWrapper` ↔ поздний `Flow` подтверждаются на части чтений, но не на всех. `BUFFER_EOS_ACCESS=NO_HOOK`; подтверждения именно слышимого PCM нет.
- `METRICA_EXCEPTION_SUMMARY/MUSIC_APP=FEW` — без доказанного отношения к наблюдателю.
- **Статус продукта:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Нельзя выдавать наблюдение за рабочую подмену.

## Точная следующая задача для нового чата

Нужно не плодить NAV46/47 ради новых счётчиков. В уже доказанном исходном маршруте `ru.yandex.music.data.audio.o` Track → creator-owned `tCa` TrackWrapper → исходный `LiLb` MediaSource → текущий `SLOT_B` / `PlaybackInfo.PeriodID` найти **строго доказанный по издательски подписанному исходнику** источник точного `trackId + albumId + editionId` и актуальности этого выбора (generation/Next/MyWave).

1. Прочитать канон `NEXT-CHAT.md`, отчёт NAV45 и соответствующий код `StageBAudioEvidence.java`, `NativeRendererStreamEvidence.java`, `ExitCallsiteWitness.java`. Работать только в указанной ветке.
2. Проверять лишь узкий оригинальный Track/type/accessor путь уже имеющимся signed-XAPK read-only CI-парсером. Само наличие `long` в `Track.copy` **не доказывает `trackId`**. `Ldjv.a():String` из FileInfo/DownloadInfo — отдельная ветка, автоматически приравнивать нельзя. Названия песен, картинки, UI MediaSession, пустые `MediaItem` не использовать как удостоверение выбранной редакции.
3. Любой идентификатор и редакция должны относиться к **тому же актуальному исходному источнику и поколению проигрывания**; пусто, устарело, конфликт или неопределённость → оставить оригинал. Сохранить Play/Pause/Seek/Next/MyWave в **единственном оригинальном плеере**.
4. Только если доказана реальная новая безопасная точка, сделать минимальный read-only фикс, проверить JVM + подписанный Android 13 ARM CI, отдать **один** owner-signed APK и ZIP для проверки. Никакой подмены/хуков звука без отдельного доказательства того же выбранного source/PCM и exact ID+edition; никаких ложных заявлений о готовности.
5. Если точку обоснованно найти нельзя — зафиксировать конкретный NO-GO и препятствие, не запускать безграничный аудит. Пользователю сообщить кратко.

## Артефакты и ограничение Library

Последний проверенный NAV45 APK `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-ReadOnly-20261119.apk`, SHA256 `8254721d6ac19221aecff389615b8fcf08e62cb29a4c5843096be1588aec0c27`. ZIP `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-20261119.zip`, SHA256 `07b6a2e84568ff59181bf06217b430e47ebacb08ef77313792f9d2055d3ba9d9`. Оба проверены и представлены в предыдущем чате через прямые ссылки, но **загрузка в персональную ChatGPT Library не прошла из-за квоты**. Нельзя утверждать обратное, удалять старые APK без просьбы, выдумывать sandbox-ссылку или обещать новую сборку без результата. При необходимости перевыложить именно проверенный artifact `14545670017` в Library после освобождения места. 

## Правило общения владельца

По-русски, кратко и по делу. Не задавать повторных вопросов, не пересоздавать архитектуру, не начинать заново, не предлагать долгие новые исследования. Результат важнее отчёта. Следующий чат должен **продолжить реальную разработку**, а не просто переписать канонические документы.
