# CELIKOM Android — API33 real MediaPlayer rapid source-reload race PASS (10.11.2026)

## Точная сохранённая точка

- Экспериментальная ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
- **Проверенный код SHA:** `50735e6d56481ea0ce3da8fdcb03589cad90608c`.
- **Rollback immutable branch:** `backup/android-own-api33-rapid-reload-race-pass-20261110` → точный SHA `50735e6d56481ea0ce3da8fdcb03589cad90608c`.
- [**Реальный Android 13 emulator / own MediaPlayer CI #42837053639 SUCCESS**](https://github.com/manufact-test/nomusic/actions/runs/42837053639). В логах текущего запуска **две разные фактические отметки**:
  - `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE` — старый полный реальный A-original→Seek/Pause→A-alternative→A-original→Next B тест продолжает работать.
  - **`RESULT=PASS CODE=OWN_ASYNC_RACE_PASS`** — новый 12-раундовый тест быстрых Start/Stop/Next с `MediaPlayer.prepareAsync/release`, попеременными B Playing / B Pause+Seek.
- На предыдущем кодовом SHA `31c34b231d850448143e0455dff4dd8d1f89e1b0` зафиксированы [OWN ARMv7 host #42837003150 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003150), [OWN-only ARMv7 scope #42837003307 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003307) и [native Android hooklab 2/2 #42837003096 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003096). Различие SHA `31c34b23 → 50735e6d` — **ТОЛЬКО workflow** `.github/workflows/android-own-mediaplayer-device-runtime.yml` (в его safety gate добавлена проверка нового сценария). Остальной исходный Java-код одинаков. Предыдущая точка **`bb26aca9`** из `ANDROID-OWN-API33-MEDIAPLAYER-RUNTIME-PASS-2026-11-10.md` сохранена.

## Практическая находка

В интерактивном собственном Android audio-smoke `AudioSmokeScreen.toggleReplacement` был **реальный локальный баг**: второй Start/Stop в промежутке между `prepareAsync` и `onPrepared`, когда задана ненулевая позиция восстановления, **не считал** её отложенным seek, потому что `restoreSeekPending` становится true только в `onPrepared`. При повторном toggle состояние могло быть считано как позиция 0. Это исправлено: если `restoreSeekMs>0`, восстановление позиции и `resumeAfterPrepare` сохраняются с самого начала prepare. Код `4ab3e66d` и затем собранные последующие SHA.

## Новый Android runtime тест

Новый `armv7-loader-host/app/src/main/java/pro/celikom/armv7loaderhost/OwnAndroidAsyncRaceProbe.java`, явно включаемый adb `--ez celikom_own_race true` только для **нашего отдельного пакета** `pro.celikom.armv7loaderhost.audio`. Запуск осуществляется тем же `armv7-loader-host/ci/run_own_android_emulator_probe.sh` после независимого основного PASS, в отдельном процессе и с очищенным logcat.

**12 раундов** в реальном Android 13 `x86_64` Google APIs emulator (`-noaudio`) моделируют:

1. Собственный 440 Гц A → `prepareAsync` (до prepared).
2. Срочный Start → `OwnSameTrackReloadPlan.decide` выбирает собственные 660 Гц A; старый `MediaPlayer` и `MediaDataSource` сначала release/close, создаётся один новый.
3. Срочный Stop → исходный A 440 Гц; текущий player точно так же освобождается до создания следующего.
4. Next → B 330 Гц остаётся оригиналом; фабрика не подставляет A alternative.
5. Фактический `OnPrepared` **последнего B**, затем в чётных раундах `start` и `isPlaying`, в нечётных — `start/pause/seekTo(1400)`, настоящий `OnSeekComplete`, диапазон позиции и проверка паузы.
6. Строгие счётчики: **48** созданий Android MediaPlayer; максимум **1** активный, **47** release до финального завершения; **12** B prepared, **6** paused, **6** seeks.
7. Дополнительно **36 намеренно сгенерированных** запоздавших ticket проверяются на revision mismatch. Они **синтетические**, не заявляется, что Android действительно прислал столько устаревших `OnPrepared`: framework обычно снимает listeners при release. Допуск успешности не зависит от количества реально пришедших поздних Android callbacks.

Оба теста валидируют только штатную Android платформу и собственный код CELIKOM. Никаких оригинальных/патченных Яндекс APK, учётной записи, захвата аудио, звука в файл, обхода подписи/DRM/Play Protect, пользовательского HONOR, сервера, Windows или изменения Test.50.

**Граница:** noaudio эмулятор **не** доказывает слышимый звук; JNI ARMv7 **не** проигрывал настоящий Yandex; не доказаны активный `Lemb` receiver, `trackId+edition+generation`, авторизованный CELIKOM alternate перед native decoder prepare. Рабочая подмена внутри Яндекса Android — **NO-GO**.

## Проверка сторонних SDK API и реальный блокер

Публичные Android API предоставляют внешнюю информацию о состоянии воспроизведения, **не внутреннюю ссылку на DataSource**:

- `AudioManager.AudioPlaybackCallback` и `getActivePlaybackConfigurations()` фиксируют изменения playback activity. Официально: https://developer.android.com/reference/android/media/AudioManager.AudioPlaybackCallback
- `MediaSessionManager.getActiveSessions` требует `MEDIA_CONTENT_CONTROL` либо включённый владельцем `NotificationListenerService` и возвращает список `MediaController`, а не приватные поля `Lemb/Lga4/Lmb4`. Официально: https://developer.android.com/reference/android/media/session/MediaSessionManager

Следовательно **простая внешняя MediaSession/NotificationListener интеграция не заменяет** настоящий выбранный `Lemb` экземпляр и не разрешает произвольную подмену его signed URL/DRM.

## Дальнейшее действие, строго без бесконечных DEX-сводок

Платформенный source-reload и активные гонки **уже доказаны**. Следующий полезный шаг для настоящей Android-подмены — единственное безопасное **runtime** свидетельство из выбранной дорожки в целевом Android app на **отдельной совместимой ARM Android среде**: какой конкретно `Lemb` из восьми реализует реально выбранный source и когда его `DataSource.open` пересекает native decoder prepare, с тем же `trackId+edition+generation`. Исключить background preload и корутинное устаревание.

До этого **не монтировать** `NativeSourceInstanceFence`, `NativeSourceGate`, `NativePrePrepareAdmission` в установленный Yandex или Test.50, не выдавать владельцу эксперимент как готовый APK, не заменять оригинальную подпись, не включать DRM обходы и x86 LSPatch. Если среды нет, дальнейший безопасный вектор — развитие отдельной Test.50 эксперим. ветки на имеющейся архитектуре, без её изменения в принятом backup.

**Не трогать:** Test.50 owner-accepted, личный HONOR, текущий установленный Яндекс, Windows 0.24.9, браузерное расширение, production, API, БД, права, подписи, DRM и Play Protect.
