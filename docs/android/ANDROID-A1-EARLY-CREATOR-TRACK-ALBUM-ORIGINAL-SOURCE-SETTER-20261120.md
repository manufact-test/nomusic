# CELIKOM Android A1 — ранний оригинальный Track+Album на Player source setter, 20.11.2026

## Где и что изменили
Ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`, исходная база `b5917cecf871dbd140e82e62a346fefc01327a02`, runtime commit [55c73a2e](https://github.com/manufact-test/nomusic/commit/55c73a2e2eeed9c5050302c2bd4e086a94610033).

В `StageBAudioEvidence` добавлен `exactCreatorTrackAlbumBeforeSourceSet(wrapper)`. Метод возвращает именно creator-owned original Java `Track+Album` по уникальному рождению `tCa` в подписанном оригинале даже **до** позднего Track Flow. Требуются оригинальный creator scope, неизменный Album и уникальный wrapper; потеря refs, конфликт и неизвестный wrapper означают null. Строковые поля/ID не читаются.

В `NativeRendererStreamEvidence` добавлен ранний pending `EarlyOriginalSourceFrame` с оригинальными Java Track, Album, source и монотонным epoch. Сигнал на `androidx.media3.exoplayer.d.e(Sl6,long)` выдаётся **перед** `chain.proceed()`, но consumer не установлен, поэтому никакой alternate не применяется. Вложенные source setter, изменённое поколение, несоответствующий scope или исключение проваливаются fail-closed. Ранее наблюдение source производилось до результата оригинального setter; теперь `onNativePlayerSourceSetter` фиксируется только **после** успешного `chain.proceed()` (сам original вызван один раз).

Это перенос доступных **объектных ссылок** на более раннюю границу выбора source, не доказательство семантических идентификаторов, edition, real pre-prepare или звучащего PCM. `NativeReplacementLifecycle` пока законно не может выбрать alternate.

## Проверка и безопасность
- [JVM #44694252227 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44694252227): существующие regression tests + 2 новых сценария раннего setter, original Track/Album до позднего Flow, отказ при конфликте Album, вложении, failed setter и неподходящем wrapper.
- ARM13 [#44694252239](https://github.com/manufact-test/nomusic/actions/runs/44694252239), clone-alone [#44694252308](https://github.com/manufact-test/nomusic/actions/runs/44694252308) запущены; не называть SUCCESS до фактической проверки conclusion.
- Оригинальное приложение не модифицировано; реальный звук, сеть, медиа-тайминг, данные пользователя и второй плеер не затрагиваются. NAV40 `34cb32c8`, подписанная NAV45 `c95c0bf2`, Test.50, Windows — не тронуты. Нового owner-signed APK/ZIP **нет**.

## Важный оставшийся барьер
Точно подтверждённая в signed 2025 оригинале `FileInfoApi(trackId)` пока **не доказана** происходящей от того же исходного `Track` при всех ветвлениях; `albumId` / `editionId` и текущее native selection generation не подтверждены. Оригинальный source setter может выполняться до renderer, но **порядок относительно настоящего decoder prepare не доказан**. Нельзя переносить позднее renderer evidence на pre-prepare и нельзя допускать подмену без этих доказательств.

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Следующий шаг — соединить эти точные исходные Java refs с семантическими ID и исходным descriptor на верифицированном pre-prepare callsite. Unknown → ORIGINAL. Не выпускать диагностический APK только ради счётчиков.
