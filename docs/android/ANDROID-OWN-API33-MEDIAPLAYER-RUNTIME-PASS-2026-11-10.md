# CELIKOM Android — первый реальный Android 13 MediaPlayer PASS после Windows W60

**Дата: 10 ноября 2026.** Ветку и лабораторию НЕ создавали заново. Продолжение `ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md` с фактическим Android runtime вместо JVM-моделей.

## Проверенная точка

- **Экспериментальная ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
- **Полный кодовый HEAD, проверенный в GitHub CI:** `bb26aca9652850c69fbd0896a26bec22601826b0`.
- **Точный immutable rollback:** `backup/android-own-api33-real-mediaplayer-source-reload-pass-20261110` @ `bb26aca9652850c69fbd0896a26bec22601826b0`.
- **Главное доказательство:** [Android 13 OWN MediaPlayer runtime #42835181030 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181030), внутри CI явно зафиксировано `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE`, отдельно `PASS: real Android 13 OWN MediaPlayer prepare, seek, pause, paused/playing source reload, Next B`.
- **Другие CI с тем же SHA:**
  - [ARMv7 own-audio host + 50 020 source-plan assertions #42835181029 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181029).
  - [OWN-only scoped module build #42835181289 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181289).
  - [Native-Yandex research module source safety/build #42835181034 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181034).
- Не путать c [ARM64 Linux own-source-plan #42831135970 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42831135970): первый результат — **реальный Android 13 эмулятор**, второй — JVM на Linux.

## Что реально проверено на Android 13, не на Windows/Linux

Чистый Android 13 API 33, Google APIs `x86_64`, новый пустой эмулятор GitHub Actions. Установлен **только собственный** `pro.celikom.armv7loaderhost.audio`; ни оригинальный Яндекс, ни клон, ни учётка не устанавливались/не открывались. Эмулятор запущен с `-noaudio`; успешная процедура НЕ является человеческим доказательством слышимого звука.

Специальный тест `OwnAndroidMediaRuntimeProbe` через явное adb-условие `celikom_own_probe=true` работает с **одним** системным Android `MediaPlayer` и `MediaDataSource`, содержащим собственные 8-секундные PCM WAV-тоны 440/660/330 Гц. Не применяются интернет, аккаунт, музыка третьей стороны, файлы пользователей, АудиоRecord/MediaProjection или лицензии.

Для PASS необходимы **все** стадии:

1. Оригинальный A 440 Hz: `prepareAsync`, настоящий Android `MediaPlayer.start()`.
2. `seekTo(2200ms)` и настоящий `OnSeekComplete`, `pause()`, проверка позиции и `isPlaying()==false`.
3. Решение `OwnSameTrackReloadPlan.decide` выбирает **именно** альтернативный A 660 Hz для Start; старый `MediaPlayer` сначала `release()`, затем один новый `MediaPlayer`/MediaDataSource.
4. `prepareAsync → seekTo(previousPosition) → OnSeekComplete`. Пауза **сохраняется**, позиция отклоняется не более чем на безопасный тестовый допуск 550 мс.
5. Возобновление и обратный Stop на оригинальный A 440 Hz, снова `OwnSameTrackReloadPlan.decide`; старый player release, новый prepare и seek, воспроизведение возобновляется лишь **после завершения seek**. Позиция проверяется с допуском 800 мс.
6. Next B 330 Hz: source-plan **не** выбирает альтернативу A; B проигрывается оригиналом.
7. Строгая проверка: четыре Prepare, три Release между источниками, одна Pause, два именно source-position restore и один конечный `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE`.

Стандартный `AudioSmokeScreen` остаётся отдельным собственным интерактивным стендом, но конкретный Android-runtime PASS относится **к запускаемому adb реальному MediaPlayer-probe**. Он не доказывает слышимое качество, Chrome/Windows/Яндекс или поведение при кроссфейде.

## Файлы и технические исправления

- `armv7-loader-host/app/src/main/java/pro/celikom/armv7loaderhost/OwnAndroidMediaRuntimeProbe.java` — реальные Android callback, исходно созданная `OwnSameTrackReloadPlan` используется **для действительного выбора** при Start/Stop/Next; без фиктивных решений. Счётчики и статусы — только enum и числа, не реальные треки, ссылки или авторизационные данные.
- `armv7-loader-host/app/src/main/java/pro/celikom/armv7loaderhost/MainActivity.java` — точный пакетный guard + разрешение только явно запрошенного собственного `celikom_own_probe`; обычная OWN audio UI и прежний ARMv7 host сохранены.
- `armv7-loader-host/app/build.gradle.kts` — optional `-PcelikomOwnEmulator=true` строит **исключительно свою** отдельную x86_64 APK с `BuildConfig.CELIKOM_OWN_EMULATOR=true`; не требует нативного JNI/NDK, который для WAV-исследования не используется. **По умолчанию** `armeabi-v7a` и строгая загрузка `celikom_host_probe` остаются неизменными.
- `armv7-loader-host/ci/run_own_android_emulator_probe.sh` — все adb-команды в **одном** shell-процессе, чтобы переменные APK/PKG не обнулялись. Результат выгружается в CI в виде фиксированного PASS/FAIL code; никаких дампов треков, звука или Yandex.
- `.github/workflows/android-own-mediaplayer-device-runtime.yml` — воспроизводимый clean API33 emulator с KVM, только собственный пакет и проверки safety.
- Промежуточные CI failures **не были ошибкой MediaPlayer**: сначала YAML step name с двоеточием не парсился, затем `reactivecircus/android-emulator-runner` запускал каждую строку `script` в отдельном `sh` (терялись переменные APK/PKG), ещё одна параллельная попытка столкнулась с битым SDK NDK zip при скачивании; всё исправлено и итоговый точный SHA получил **SUCCESS во всех четырёх релевантных CI**.
- В собственном тесте первоначальная обычная перемотка ошибочно считалась `positionRestoreCount`; поправлено на **2 восстановления именно при новой загрузке источника**, и итоговый PASS подтверждает это.

## Что переносимо, а что нет

**Работает как концепция:** один системный плеер, выбрать источник до подготовки, сохранять play/pause и позицию при пересоздании, отклонять устаревшие события, а без альтернативы оставлять оригинал. Работает на реальном Android-плеере **наших собственных синтетических тонов**.

**НЕ доказано для Yandex Android:** факт выбора **живой** реализации `Lemb` из восьми вариантов, связь `trackId+edition+generation` с конкретным `Lga4/Lero/Lmb4` и реальным decoder prepare; возможность безопасно подать туда наш `FileInfo`/approved stream без нарушения кодеков/DRM/подписи; аудио-качество на HONOR с «Дым»/«Раскол», радио, MyWave, кроссфейдом.

**Результат для CELIKOM Android аудиоподмены — всё ещё NO-GO**, хотя общее системное Android source-reload поведение теперь впервые доказано эмпирически.

## Следующий практический этап

Не повторять сотни полустатических DEX may-flow. Получить **только разрешённый и безопасный** пассивный runtime evidence: какой именно `Lemb` экземпляр/trackId/edition/generation Android оригинала реально выбран перед декодером на **отдельном** ARM Android test-host, без модификации оригинального APK/DRM/signature и без пользовательского аккаунта. Если безопасной instrumented-среды нет, остановить ложную «почти готово» подмену: отдельно совершенствовать OWN воссоздание источника либо исходный Test.50, не выдавая тестовый стенд за релизный Android CELIKOM.

**НЕ ТРОГАТЬ:** владелец HONOR, эталон Test.50 `backup/android-test50-exact-source-owner-accepted-20261106`, Windows (owner-accepted 0.24.9), расширение, API/production/БД, Play Protect, издательскую подпись, DRM. Не выдавать сборку на телефон без отдельного запроса владельца.
