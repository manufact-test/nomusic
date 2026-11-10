# CELIKOM Android — что действительно переносится из Windows 0.24.7–0.24.11

**10 ноября 2026.** Проверка реальных исходников Windows, а не пересказ предположений. Эта точка продолжается в `experiment/android-native-yandex-fileinfo-hooklab-20261109`; никакой Test.50/owner HONOR/production не меняли.

## Доказанная база ПК — не подменять её предположениями

Из ветки `experiment/windows-stop-lifecycle-20261110`, документы
`W57-OWNER-0247-REAL-AUDIO-SUCCESS`, `W60-LIVE-SOURCE-RELOAD`,
`W61-CONSUMER-UX-FAST-TOGGLE`, `W62-EXTENSION-PARITY-AND-OWNER-AUDIO`,
`W63-OWNER-02411-EXTENSION-UX-TRACK`, код
`windows-companion/w22/native-resource-adapter.mjs` и
`windows-companion/w60/current-source-refresh.mjs`:

- **0.24.7** владелец услышал реальную подмену в установленной Яндекс.Музыке Windows. После исправления W56 signed URL перестал ломаться от PC `DownloadInfoSource` query append, появился HTTP206 вместо прежнего 403.
- **0.24.8** владелец подтвердил переключение источника на **той же играющей песне** при Start/Stop, но с заметным разрывом.
- **0.24.9** владелец подтвердил рабочие аудио, Pause, Seek, Next, MyWave, Start/Stop без прежних «пшиков». Эталон `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110`.
- **0.24.10** аудио сохранилось, но UI был отклонён. **0.24.11** — приватный кандидат с исправлениями интерфейса, его пользовательский результат ещё не подтверждён; нельзя объявлять более новой audio-accepted базой вместо 0.24.9.
- На Windows подмена реализована через оригинальный `getFileInfo/getFileInfoBatch`, exact track ID и ревизию async request, выбор подписанного CELIKOM-ресурса ДО его загрузки родным проигрывателем, без второго плеера и без внешней синхронизации двух аудио.
- W60 использует **только издательский Electron-controller Windows 5.126.1**: `7123.VE.reloadEntity("QUALITY_CHANGE")`, сохраняющий позицию и playing/paused через оригинальный native reload. ЭТОГО API **НЕТ** в подтверждённом Android DEX-контракте. Нельзя тупо переносить JavaScript-вызов на Android.

## Прямая матрица Windows → Android

| Windows подтверждённый принцип | Android подтверждённое состояние | Решение |
| --- | --- | --- |
| Один штатный плеер, менять source до prepare | Android `sw7.y0/z0` DTO→`Leed`, `Locv.i0` model `Ljgv`, фабрики `Lcq7`; `Lero→Lmb4→Lha4→Lm48` читают байты в **одной возможной** ветке | Оставить single-player/source-first; **НЕ выдавать DTO-конвертер за выбранный decoder source** |
| Точный текущий track ID и отмена старого promise | Android `Ljgv` выведен из URI-подобных данных, но в DEX возможны 8 типов `Lemb`, prefetch и coroutine | Требуется независимый факт `selected track+edition+generation` вместе с `selected source instance`. Текущий `NativeSourceInstanceFence` — только pure-Java модель |
| Start/Stop same-track через native reload с сохранением clock | Публичного Android аналога `reloadEntity("QUALITY_CHANGE")` не доказано | В существующем **OWN-only ARMv7 Android MediaPlayer стенде** добавлен проверяемый источник для той же песни, сохранение текущей позиции и паузы, если действительно меняется source; с одним MediaPlayer и без изменения Яндекса. Это исследование платформенного поведения, **не** Yandex |
| W56 `&celikom_native_query_guard=0` предотвращает **конкретное** Windows-присоединение `?vsid` к signed URL | Никаких фактов об идентичном Android URL append нет, `NativeGrantContract` обоснованно запрещает невыданные сервером query параметры | **НЕ переносить guard в Android без сетевого доказательства**, не ослаблять подписи/HMAC и не менять API/БД |
| Windows plain MP3/raw требует codec/transport, удаляет legacy key/iv ТОЛЬКО для валидной подтверждённой native-подмены | Android модели/классы могут содержать key/iv/DRM контракты, путь decoder ещё не доказан | Нельзя просто удалить key/iv из реального Android источника или подменить зашифрованный поток raw. Никаких обходов DRM или подписи |

## Что реально сделано в Android на этом проходе

В существующем безопасном собственном стенде `android/native-yandex-hooklab/armv7-loader-host`:

1. `app/src/main/java/pro/celikom/armv7loaderhost/OwnSameTrackReloadPlan.java` — маленькое pure-Java правило: на той же песне A, если доступна собственная WAV-альтернатива 660 Гц, Start выбирает её, Stop выбирает 440 Гц; если нового источника нет, никакого reload, B остаётся оригиналом. Позиция ограничена длительностью 8-секундного тестового WAV, playing/paused сохраняется.
2. `app/src/main/java/pro/celikom/armv7loaderhost/AudioSmokeScreen.java` — две **рабочие для собственного хоста** кнопки Start/Stop CELIKOM в дополнение к A/B/Seek/Pause. При отличии источника старый `MediaPlayer` **сначала release**, затем создаётся единственный новый с `MediaDataSource` на локальном синтетическом WAV. После `prepareAsync()` позиция восстанавливается через `seekTo`, paused не запускается, playing запускается только после завершения seek. `revision` фильтрует поздние callbacks. Повторный Start без разницы в source — no-op; быстрый Start/Stop во время seek использует сохранённую позицию и запрещает преждевременный пользовательский seek/pause.
3. `tests/OwnSameTrackReloadPlanTest.java` — 10 000 циклов Start/Stop/Next, проверка сохранения paused/progress, отсутствия модульного hook и лишних reload. **Только JVM-модель, не слышимый Android-звук.**
4. GitHub Actions `android-native-armv7-audio-smoke.yml` компилирует основной безопасный Android-стенд + модуль только для двух собственных package names, запускает Java тесты и проверяет запреты. `android-native-owned-windows-parity-arm64.yml` запускает те же тесты на **реальном ARM64 Linux/JVM**, это **не Android MediaPlayer**.
5. Всё экспериментальное, с оригинальными собственными тонами (никаких треков/аккаунтов), без изменения/перепаковки publisher signed Yandex и без установки на личный HONOR. Проведение физического слышимого OWN теста не подтверждено.

**Последние проверки:**
- [ARM64 Linux Windows-parity #42831135970](https://github.com/manufact-test/nomusic/actions/runs/42831135970) — SUCCESS.
- [OWN ARMv7 audio APK #42830966825](https://github.com/manufact-test/nomusic/actions/runs/42830966825) — проверить завершение, до зелёного результата не считать релизным/успешным.
- [Read-only Android hooklab #42830847621](https://github.com/manufact-test/nomusic/actions/runs/42830847621) — SUCCESS для предыдущего изменения.
- [W63 Windows private CI #42824296777](https://github.com/manufact-test/nomusic/actions/runs/42824296777) — SUCCESS, пользовательская приёмка W63 ещё требуется.

## Точный следующий барьер, без дальнейшего бессмысленного DEX-кругооборота

Вместо очередных статических отчётов сосредоточиться только на одном факте: **какая конкретная реализация `Lemb` (`Lero` или другая) выбрана настоящим штатным Android-плеером перед decoder prepare и каким текущим `trackId/edition/generation` она обладает.** Подписанный DEX это не доказывает, а Linux CI/десктоп Windows не заменяют Android runtime.

Если нельзя получить отдельный совместимый ARM Android runtime-host **без изменений официального бинарника и без личного устройства владельца**, честно зафиксировать NO-GO к настоящему source replacement и не замыкаться на ещё одном раунде may-flow. Владельцу не отправлять неработающий Android release под видом готового.

Ни Windows owner-accepted 0.24.9, ни Android Test.50, ни продакшен, API, БД, расширение, исходные подписанные APK, DRM и Play Protect не трогались.
