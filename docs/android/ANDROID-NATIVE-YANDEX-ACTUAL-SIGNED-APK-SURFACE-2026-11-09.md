# CELIKOM Android · проверка настоящего нативного Yandex APK (09.11.2026)

**Статус:** Gate 0 / доказательная статическая инвентаризация выполнена. Gate 1 / реальный выбор альтернативного источника **внутри проигрывателя Яндекса** — **НЕ ДОКАЗАН / NO-GO для выпуска APK**.

**Изолированная ветка:** `experiment/android-native-yandex-gate1-20261109`, основание `f2d2ed11deea8c70048694276033498bafa9e800`. Не менять стабильный CELIKOM, Test.50, сервер, каталог, установленную Яндекс.Музыку, Windows и расширение.

## 1. Проверенный подлинный нативный APK (первый подтверждённый объект)

Дистрибутив получен из **публичной витрины RuStore**, без учётной записи Яндекса, в одноразовом GitHub Actions runner. Действия скрипта: HTTPS+домены ограничены → metadata exact pin → download in TemporaryDirectory → `apksigner verify --verbose --print-certs` → SHA256 signer pin → `aapt dump badging` → DEX read-only → удаление временного APK. **Не было инсталляции, запуска приложения, копирования в репозиторий, сохранения бинарника в artifact, обхода защиты, сбора токенов или пользовательских данных.**

| Свойство | Факт |
| --- | --- |
| Package | `ru.yandex.music` |
| RuStore release | `2026.10.3 #170rur`, versionCode `24026531` |
| Verified publisher certificate SHA256 | `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba` |
| Publisher certificate subject | `CN=OOO Yandex, OU=Mobile Development, O=OOO Yandex` |
| Verified APK signing | v2=true, v3=true |
| Downloaded APK archive SHA256 | `dfa1091383ee9fead30f8bb34eb01b46d7705ae8ab400b8abfbc73c271e5bcde` |
| Size | 47,740,142 bytes, single APK |
| DEX | 6 files, 57,161 class definitions, 319,816 method_ids |
| Static Media3/ExoPlayer factory exact allowlist hits | 0; this **does not prove** Media3 absent: classes/methods may be obfuscated |
| Actions proof | [#42599929142 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42599929142), [#42600494250 — SUCCESS, expanded](https://github.com/manufact-test/nomusic/actions/runs/42600494250) |

Это реальный нативный APK Яндекса, но **RuStore #170rur ≠ Google Play/HONOR #170gpr**. Совпадение versionCode не доказывает идентичный внутренний код, ABI, подпись или совместимость хука.

## 2. Реальная внутренняя архитектура: что выявлено и чего НЕ найдено

В `classes.dex` на `#170rur` определены именованные классы:

- `com/yandex/music/shared/media/session/session/Media3LibraryService`
- `com/yandex/music/shared/media/session/session/Media3SessionService`
- `com/yandex/music/shared/playback/api/commands/{PlayCommand,PauseCommand,SeekToPositionCommand,SeekToFractionCommand}`
- `com/yandex/music/shared/playback/utils/api/commands/{PrevCommand,SkipCommand,SetQueuePositionAndPlayCommand}`
- `com/yandex/music/shared/music_starter/executor/{WaveQueueStartCommand,RadioStreamQueueStartCommand}`
- `com/yandex/music/shared/playback/core/api/commands/PlaybackCommand$QueueLaunch$Substituting`

В `classes4.dex` есть сетевой `com/yandex/music/shared/play/audio2/data/PlayAudioApi` с методом `a(Ljava/lang/String;Lcom/yandex/music/shared/play/audio2/data/dto/BulkPlaybacksRequestDto;)Lretrofit2/Call;` и `PlayAudioBundleRequestDto`. Это **перспективная область для дальнейшей независимой трассировки**, но она ещё **не** доказана конечной точкой выдачи URL, ни правом переназначить источник в том же проигрывателе. Слово `Substituting` внутри QueueLaunch **не доказывает подмену аудиофайла**, речь может идти о замене очереди.

В `classes3.dex` подтверждено **24 bytecode invoke** на системные `android.media.AudioTrack`, `MediaCodec` и `MediaSession`; например `Lif8;->e` вызывает `AudioTrack.write`, `Lif8;->v` вызывает `AudioTrack.play`, `Lhwi;->n` вызывает `MediaCodec.configure`. `classes6.dex` содержит ещё 5 вызовов системных media API, в т. ч. `MediaExtractor.setDataSource`. **Это низкоуровневая часть вывода/декодирования; внедрение туда рискует сломать seek, DRM и другие звуки.** Предпочтительна точка выбора разрешённого track+edition источника **до** подготовки нативного player, а не `AudioTrack.write` и не внешний Media3 controller.

Статический анализ не запускал клиент. Реальное внутреннее `trackId` плюс `album/editionId`, место выбора аудио URL/MediaItem, корректная очередь и нативные `seek/pause/next` при подмене **НЕ ПРОВЕРЕНЫ**.

## 3. Попытка найти именно версию HONOR `#170gpr`

- Текущая версия на HONOR из Test.76: `2026.10.3 #170gpr`, `24026531`.
- Публичные каталоги [APKPure](https://apkpure.net/ru/yandex-music-books-podcasts-app/ru.yandex.music/versions) и [Aptoide](https://yandex-music.ru.aptoide.com/versions) показывают `#170gpr` от 5–6 ноября 2026, но **каталожная страница не является проверкой подписанного APK**.
- [Actions #42600704884](https://github.com/manufact-test/nomusic/actions/runs/42600704884): открытый Aptoide API вернул **древний** `2020.11.1 #3608`, `23020551`; код корректно **остановился ДО скачивания**.
- [Actions #42601003707](https://github.com/manufact-test/nomusic/actions/runs/42601003707): версия через документированный `getMeta/vercode=24026531` вернула **HTTP 404**, скрипт снова **остановился ДО скачивания**. Нельзя считать #gpr полученной или подтверждённой. Нельзя подменять #rur как эквивалент #gpr.

## 4. Новый код и тесты

- `tools/android-native-gate1/inspect_android_host.py`: read-only DEX типы и известные media factory методы.
- `tools/android-native-gate1/trace_native_callers.py`: строгий парсер DEX method_data/code_item, реальные invoke callsites, игнорирует совпадения в константах и malformed payload; **не выполняет APK**.
- `tools/android-native-gate1/inventory_native_media_surface.py`: имена playback классов Яндекса, сигнатуры и android media syscalls.
- `tools/android-native-gate1/probe_rustore.py`, `audit_rustore_host_once.py`, `audit_gpr_aptoide_once.py`: provenance/version/signature гейты.
- GitHub Actions tests: [#42601003730 — SUCCESS, 24 unit tests](https://github.com/manufact-test/nomusic/actions/runs/42601003730). Synthetic contracts **не являются** интеграционным тестом.

## 5. Gate 1 NO-GO / требование для настоящей реализации

Для воспроизводимой подмены в **самом Android-приложении Яндекс.Музыки** нужно одновременно:

1. Подлинный, правомерно исследуемый, **точный #170gpr** host с проверенной цепочкой подписи и package/edition identity, из безопасного законного источника. Ни APK владельца, ни приватные credentials/данные в публичный GitHub не переносить.
2. В отдельной тестовой среде зафиксировать истинный catalog `trackId`+издание и **исполняемую** точку выбора одного источника **до native prepare**, сохраняя оригинал при отказе. В идеале исследовать границу `PlayAudioApi`→player source, но нельзя предполагать её функции по одному имени.
3. Решить rootless root-of-trust: сторонняя пересборка APK с другим сертификатом не сможет поверх официального Яндекса обновиться без удаления, а удаление требует **заранее согласованного** риск/бэкап/откат. Google Play Protect **включён**, проверяется на отдельном устройстве; подписанный статический APK не доказывает его одобрения.
4. Только после этого внедрять `CELIKOM` approve/rights/entitlement broker и проводить настоящие Play/Pause/Seek/Next/радио/плейлисты при **одном нативном проигрывателе**. WebView/два плеера/сборка обучающих APK — не принимаются.

**Вердикт на 09.11.2026:** статический блок завершён, доступные материалы не подтверждают безопасную native in-process подмену для владельца. **Нового тестового APK нет; никаких действий от владельца сейчас не требуется.** Дальнейшая разработка требует verified exact host + hook, а не очередного управления внешним Media3.
