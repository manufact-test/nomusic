# CELIKOM Android — pinned signed FileInfo → media / MediaSession audit

**10 ноября 2026 г.** Исследовательская ветка `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**Проверенный код:** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
**Бэкап:** `backup/android-signed-source-bridge-media-session-ci-green-20261110`.
**Обе независимые CI завершены успешно:**
- [Native Android module / unit tests #42804081053](https://github.com/manufact-test/nomusic/actions/runs/42804081053) — **SUCCESS 2/2**, проверены собственные Xposed-модуль и тесты; Яндекс не запускался.
- [Pinned publisher-signed DEX research #42804081064](https://github.com/manufact-test/nomusic/actions/runs/42804081064) — **SUCCESS**, сверка исходного издательского XAPK и всех пяти частей, 6 DEX, без изменения/публикации APK.

## Что действительно нашли

В исходном подписанном `ru.yandex.music 2026.10.3 #170gpr`:

- Просканированы **230 533 тела методов** и **837 500 структурных связей вызовов** между методами шести DEX; граф объединял одноимённые тройки `(class, method, proto)` по всем DEX.
- От `FileInfoDto / OldGetFileInfoDto` до `sw7.y0/z0` и модели `eed` найден **один непосредственный вызывающий метод: `Lhee;->a`**. Среди шести методов, потребляющих модель, есть `Lged;->a` (остальные указаны в редактированном безопасном выводе CI).
- Из исходного APK ранее установлены **четыре обфусцированных реализации Media3 ExoPlayer**: `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`. Ни одна пока НЕ доказана как реальный проигрыватель текущего трека.
- Новый анализатор `audit_native_shared_caller_bridge.py` проверил **общих предков вызовов** между конвертером/моделью FileInfo и API этих реализаций, платформенными `MediaCodec/AudioTrack/MediaExtractor/MediaPlayer`, на расстоянии до четырёх вызовов с каждой стороны. **Совпадений — ноль** во всех четырёх сочетаниях (конвертер/модель × Media3/Android framework). Ранее уже проверялись простые цепочки 1–3 вызова. Отрицательный результат **НЕ означает**, что связи нет: Kotlin coroutine callbacks, интерфейсная диспетчеризация, обфускация и native boundary не моделируются полноценным dataflow.
- Новая проверка достоверности уже существующего пассивного `MediaSession`-хука: в реальном APK есть **две разные вызывающие процедуры** для `android.media.session.MediaSession.setMetadata(MediaMetadata)` (`Lr5j;->a0`, `Lx6j;->h0`) и **две** для `setPlaybackState(PlaybackState)` (`Loz00;->k`, `Lq5j;->V`). Значит, точки реально встречаются в кодовых вызовах этого APK. Но конкретно **во время проигрывания пользовательского трека** они не подтверждены.
- `MediaSession.setMetadata/setPlaybackState` публикуют сведения/состояние; **не являются** точкой замены source или доказательством связи `trackId + edition + generation` с native decoder.

## Переиспользование настоящего Windows-успеха

Проверена независимая ветка Windows `experiment/windows-companion-integration-20261108`, HEAD `2338c2109ad55beb583397cfbf7161726d678777`, W58. Пользователь **подтвердил на ПК 0.24.7 реальное воспроизведение наших песен внутри приложения Яндекса**, а также Pause, Seek, Next, Previous и «Моя волна» без обнаруженных им лагов. Этот успех относится **только к Windows**, не Android.

Реальный механизм: `windows-companion/w22/native-resource-adapter.mjs` обрабатывает `getFileInfo/getFileInfoBatch`, ждёт оригинальные сведения Яндекса, отдельно проверяет одобренный CELIKOM-grant, заменяет **один аудиоисточник до чтения плеером**, не подменяет очередь/часы. Поколение и отмена устаревших ответов защищают Next/радио. Windows Stop отменяет будущие подмены, но уже отданный Яндексу источник может продолжать играть из буфера; это не доказательство новых подмен после Stop.

Перенесены в Android **только совместимые чисто Java-контракты** `NativeGrantContract`, `NativeReplacementLifecycle`, `NativePrePrepareAdmission`. Они прошли CI, но **не подключены** к реальному Android source/decoder.

Windows-особенность `?vsid`, портящая подписанный URL, устранена там локально. **Не копировать** Windows-параметр `celikom_native_query_guard` в Android без собственного доказательства такого же поведения.

## Следующий реальный инженерный шаг

1. **От `Lhee;->a` и `Lged;->a` до фактического Android datasource/decoder:** исследовать DEX register-level producer/consumer, переходы через `invoke-interface`, coroutine continuation и obfuscated native/Java classes; не повторять уже проверенные именованные ExoPlayer-поиски. Работать со сверенным подписанным исходником read-only, выдавать только обезличенные типы/счётчики, не копировать содержимое/секреты.
2. Если статического доказательства недостаточно, нужен **изолированный ARM Android-стенд с допустимым доступом к нативной проверке**. Предыдущие x86/ARM-translation LSPatch стенды ломались в самом загрузчике и НЕ проверяли CELIKOM. GitHub Linux ARM без /dev/kvm — не Android host. Не ставить патченную Яндекс Музыку на главный HONOR.
3. Только после доказательства **current trackId + edition + generation → fileinfo → exact pre-prepare decoder source** подключить уже написанную `NativeReplacementLifecycle`, провести отдельные проверки настоящей аудиоподмены, а затем Pause/Seek/Next/радио и сложные «Раскол» `42884423`, «Дым» `39949113`.

**Состояние:** Android audio replacement = **НЕ РАБОТАЕТ / НЕ ПОДТВЕРЖДЕНО**. Нет основания выдавать установочный CELIKOM Android APK с обещанием работы в официальном Яндексе. Ничего не менять в Test.50, HONOR, Windows 0.24.7, расширении, server/API, БД/production, официальном Яндексе, аккаунтах, DRM, Play Protect и подписи. ChromaSync оказался платным и требует ручного патчера; не просить его у владельца и не писать Яндексу.
