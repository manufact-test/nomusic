# Android: установленная Яндекс Музыка + CELIKOM, 12.10.2026 МСК

## Требование владельца и отклонённая поставка

Владелец отклонил WebView-сценарий Android 0.2.0: ему нужен CELIKOM рядом с уже установленной Яндекс Музыкой, без обязательной авторизации в ещё одном веб-плеере. Музыка должна работать с выключенным экраном, в фоне, через наушники и автомобиль. Встроенный сайт не является заменой этому требованию. Региональный gate, CAPTCHA и отдельный login на устройстве владельца не дали проверить даже WebView playback. Stage16 не принят, Stage17 не начат; Stage15 исключён.

Замечания владельца: стандартная Android-иконка вместо CELIKOM; обрезание/масштабирование текста; вводящие в заблуждение статусы «Звучит оригинал» без подтверждённого плеера и «Приложение в фоне»; добавить простой канал техподдержки в обоих клиентах. Адрес поддержки ещё не выбран. Исправления оформления не решают отсутствие нужного playback-сценария.

## Конкретный кандидат: подключение как обработчик аудиосессии

Яндекс официально описывает поддержку сторонних эквалайзеров на Android и включение их через настройки Музыки. Android AudioEffect предоставляет OPEN/CLOSE_AUDIO_EFFECT_CONTROL_SESSION и DISPLAY_AUDIO_EFFECT_CONTROL_PANEL; EXTRA_AUDIO_SESSION обозначает конкретную сессию, а не весь STREAM_MUSIC. DynamicsProcessing (API28+) позволяет менять входной gain в dB отдельной сессии. Поэтому перспективный эксперимент — companion, который получает открываемую Яндексом audio session через штатное подключение эквалайзера, слушает MediaSession state и воспроизводит только альтернативу из CELIKOM API. Это гипотеза, не подтверждённая интеграция или доказанное разрешение на любой способ подмены.

Нужные доказательства до реализации общего продукта:

1. Реальный Яндекс отдаёт OPEN/CLOSE session корректно, в том числе при next/seek/смене качества/маршрута, либо явно открывает нашу панель через стандартный intent. Никакого перебора чужих session IDs.
2. Его MediaSession предоставляет точный устойчивый Track ID/URI и актуальные play/pause/seek/position. Сервисный MEDIA_ID опционален; название/исполнитель не считаются точным ID.
3. Session-local effect реально подавляет только оригинальный поток, сохраняет ход оригинального плеера и не меняет громкость CELIKOM/других приложений. Setter success недостаточно.
4. Original, ошибка, потеря доступа, закрытие сессии и смерть companion возвращают оригинальный звук; не оставляют mute. Не перезаписывать сторонние пользовательские настройки общего effect engine.
5. Управление Яндекса/гарнитуры/автомобиля остаётся master, альтернативный плеер следует ему. Не публиковать конкурирующую media session без проверки routing команд.
6. Реальные screen-off/background, звонки, отключение наушников, Bluetooth A2DP и Android Auto проверяются отдельно. Перенаправление на удалённую колонку/Cast не равнозначно звуку, производимому на телефоне.

Обработка должна затрагивать только ненулевую подтверждённую аудиосессию согласованного плеера. Global session0/STREAM_MUSIC mute, обход DRM/TLS, модификация APK Яндекса и обещание универсального root-перехвата не используются.

## Изолированный технический эксперимент

`android/native-research` — отдельный research Gradle project, не новый продуктовый клиент. Два собственных APK с разными application IDs/UIDs: source проигрывает созданный нами WAV220Hz и сообщает свою сессию; controller использует session-local DynamicsProcessing и собственный WAV440Hz. Нет INTERNET permission, аккаунтов, CELIKOM API, Яндекс credentials или оригинальной сервисной музыки. Эти APK не выдаются пользователям как готовый CELIKOM.

Instrumentation сначала проверяет waveform RMS собственных сессий через Visualizer в SCALING_MODE_AS_PLAYED. AOSP Visualizer имеет INSERT_FIRST: эти samples находятся перед DynamicsProcessing и не подтверждают downstream attenuation. Поэтому итоговое измерение использует только общий выход двух owned WAV: оконная проекция на220/440Hz отделяет оригинал от альтернативы, baseline → gain -100dB только исходной ненулевой сессии → release. К session0 НЕ подключается gain/mute: она используется исключительно лабораторным измерителем. Громкость STREAM_MUSIC временно выставляется максимальной только в owned emulator для измерения quiet8bit sine и возвращается в finally; это не продуктовый способ подмены. Проверяет сохранение хода source и отсутствие подавления собственной альтернативы. RECORD_AUDIO нужен только лабораторному измерителю Visualizer; необходимость этого разрешения в продукте не установлена. Ни UiAutomation shell identity, ни root не используются для создания/изменения effect; UiAutomation предоставляет только обычное runtime permission измерителю и останавливает собственный fixture после теста.

Workflow `android-native-research.yml`: Android API29/35 x86_64; build/lint/instrumentation. JSON классифицирует собственный эксперимент как candidate, unsupported/denied или effect-not-proven. Зелёный workflow сам по себе не означает работоспособность native Яндекса. Начальная попытка9287b9f остановилась на receiver lint; совместимый ContextCompat receiver добавлен4027e6a. Попытка4027e6a выявила недостаточную амплитуду quiet8bit сигнала при default stream volume. После калибровки d14288e workflow38177371712 завершился, но upstream waveform не показал attenuation: classification effect_not_proven_by_waveform наAPI29/35, не service PASS. Downstream частотное измерение добавлено afa1032. Workflow [38177741159](https://github.com/manufact-test/nomusic/actions/runs/38177741159) завершился PASS build/lint/instrumentation на обеих версиях. Оба результата — `owned_cross_app_candidate`, distinct_uids/session_nonzero/source_keeps_playing/measured_attenuation/measured_restore/output_alternate_unaffected=true. Это подтверждает собственный cross-app механизм без root, но не интеграцию Яндекса.

| Android | Исходный сигнал до / во время / после release | Альтернатива до / во время | Job |
| --- | --- | --- | --- |
| 10 (API29) | 7.0205 / 0.0054 / 7.0182 | 6.9893 / 7.0613 | 114583598563 |
| 15 (API35) | 7.0337 / 0.0198 / 7.0426 | 7.0517 / 7.0640 | 114583598458 |

Величины — амплитуда оконной частотной проекции лабораторного 8bit waveform, не SPL и не запись пользовательской музыки. Подавление исходной частоты более99.7%; альтернатива сохраняется, после release исходная амплитуда восстанавливается. Проверен явный release, а НЕ восстановление после crash/kill. `yandex_tested=false`, `physical_routes_tested=false`: нет доказательства exact Track ID, реального OPEN/CLOSE Яндекса, screen-off, Bluetooth или автомобиля. Следующий технический шаг — минимальный native companion probe с штатной панелью AudioEffect и наблюдением MediaSession на реальном устройстве; диагностировать только необходимую информацию и не собирать credentials/аудио. До этих доказательств не выдавать его за готовую Beta.

## Другие проверенные направления

| Вариант | Результат исследования |
| --- | --- |
| Только MediaSession/notification access | Возможный state/control, но сам по себе не гарантирует exact ID или отдельное mute |
| Audio focus | Может подавить/приостановить master; не считать способом сохранения работающего беззвучного Яндекса |
| AudioPlaybackCapture | Копирование разрешённого звука, не замена исходного потока |
| Xiaomi Sound Assistant / Samsung Sound Assistant | Производители заявляют отдельные громкости/совместный звук; возможный ограниченный fallback, не универсальный публичный Android API или автоматический per-track Original |
| Shizuku/ADB | Расширенный кандидат, не испытан: SystemApi PlayerProxy/privileged configs зависят от shell permissions/прошивки. Android11+ wireless debugging, Android10 и ниже компьютер; запуск после reboot повторяется. Exact Track ID и безопасное восстановление всё равно не доказаны |
| VpnService | Сетевой tunnel не даёт автоматически доступа к содержимому TLS и управления локальной audio session; не реализуется как подмена HTTPS/DRM |
| Foreground playback service | Штатная основа screen-off/notification/Bluetooth для собственного player, но не доказательство взаимодействия с Яндексом |

Источники (первичные, просмотрены12.10.2026):

- https://yandex.ru/support/music/ru/listening/equalizer
- https://developer.android.com/reference/android/media/audiofx/AudioEffect
- https://developer.android.com/reference/android/media/audiofx/DynamicsProcessing
- https://developer.android.com/reference/android/media/audiofx/Visualizer
- https://developer.android.com/reference/android/media/session/MediaSessionManager
- https://developer.android.com/reference/android/media/MediaMetadata
- https://developer.android.com/reference/android/media/session/MediaController
- https://developer.android.com/media/optimize/audio-focus
- https://developer.android.com/media/platform/av-capture
- https://developer.android.com/media/media3/session/background-playback
- https://developer.android.com/reference/android/net/VpnService
- https://www.mi.com/uk/support/article/KA-08490/
- https://galaxystore.samsung.com/detail/com.samsung.android.soundassistant
- https://android.googlesource.com/platform/frameworks/av/+/refs/heads/main/services/audioflinger/AudioFlinger.cpp
- https://android.googlesource.com/platform/frameworks/av/+/master/media/libeffects/visualizer/EffectVisualizer.cpp
- https://shizuku.rikka.app/guide/setup/
- https://android.googlesource.com/platform/frameworks/base/+/master/media/java/android/media/PlayerProxy.java
- https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/packages/Shell/AndroidManifest.xml

Backend/extension0.4.28, реальные accounts/sessions/trials/grants/incidents/catalog/rewards неизменны. PR6 OPEN/unmerged. Исследование не закрывает Stage16, не запускает Alpha15, не зависит от платежей и не открывает выпуск до приватизации18.
