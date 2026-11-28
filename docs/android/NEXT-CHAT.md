# CELIKOM Android A1 — актуальное состояние

Дата: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Код BETA34: `a513e1045bc5fdd76beb06e697399c9b48c6e351`

## Что уже проверено

- **BETA32 MP3 override — НЕ РАБОТАЕТ:** ломал воспроизведение. Не повторять MP3/AAC override без новой доказанной причины.
- **NAV54 работает до чтения альтернативных байтов:** BETA34 и BETA35: FIRST_OPEN_CANDIDATE_ACCEPTED=ONE, DATASOURCE_ARMED=ONE, AUDIO_OPEN=ONE, AUDIO_READ=MANY. Сохранять.
- **BETA35 NAV55 на Honor 50 — слышимой подмены НЕТ.** Диагностика CELIKOM-A1-Diagnostics-1795873462104.txt: CELIKOM_REPLACEMENT=NOT_CONNECTED.
- NAV55 (`80f42ed`) подтвердил точный класс **o96**, интерфейс wh6 и тот же объект при select, attach и read: все четыре HOLDER_OTHER_WH6/LO96/SELECT_SAME/ATTACH_SAME_AT_READ=MANY. Фактический путь прямой (LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT=MANY), не up1. Повторять проверку holder не нужно.
- LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY, ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY. Но LIVE_RENDERER_ALT_SOURCE_READ_SAME=NONE; NO_ROUTE_CURRENT_PERIOD=FEW, DATASOURCE_UNRESOLVED_CURRENT_PERIOD=FEW. Вторая категория связана с отказом creator lookup; первая — с отсутствием живого/сохранённого маршрута для проверки. Причина отсутствия связи ещё не доказана. Не считать, что decoder получил альтернативные байты.
- BUFFER_EOS_ACCESS=NO_HOOK; EOS неизвестен. PERIOD_ADAPTER_RENDERER_STREAM_UNAVAILABLE=MANY; прямой o96 не доказывается через adapter-only наблюдение. Не выдавать структурную проверку за PCM/audio proof.
- BETA35 build `517905c`, CI `46148935304` PASS; owner draft `celikom-a1-owner-46148935304-1`. JVM `46147441043` PASS. ARM13 только запуск, NOT_AUDIO. Экспорт ошибочно сохранил метку BETA34_NAV54 в BETA_BUILD; исправить при следующей реальной сборке, отдельную APK ради метки не делать.
- Счётчики относятся ко всему процессу, а не только к одному треку.

## Что выяснили по оригинальному Яндексу

Read-only анализ подписанного Yandex 2025, CI run `46144076359`: **PASS**.

- Точный `DataSource.open`: 18 прямых вызывающих методов.
- Точный `DataSource.read`: 23 прямых вызывающих метода.
- Ни один из них и ни один найденный upstream-метод не подтвердился как ExoPlayer Loadable.
- Связь этих вызовов с `Lo96` / `MediaPeriod` не доказана. Активный renderer/source link статически не установлен.
- Отдельно найден статический путь `Lp96` → `Lo96` → `Lwh6` / `Lup1` → native holder. Это только структура оригинального кода, не доказательство, что именно этот period активен на телефоне.
- Анализатор исправлен: повторные callsite больше не считаются отдельными рёбрами. Получено 856 289 уникальных связей; 6 regression tests PASS.

## Следующий шаг

Проверка класса и identity holder завершена. Не повторять NAV51–NAV55. Реальный разрыв — между доказанным прямым o96 и DataSource альтернативных байтов. В текущем коде связь проверяется через TrackWrapper → StageBAudioEvidence.linkedSourceInstanceForCreatorOrBeta → NativeExoAlternateByteRoute.readStatusForSource; этот путь на телефоне не дал совпадения. Не приписывать отсутствие совпадения определённому экземпляру DataSource или decoder без доказательства. Сначала установить точную причинную связь и только затем менять функциональный маршрут. Не ослаблять проверку источника, не возвращать MP3/AAC override и не экспортировать APK ради новых счётчиков. При следующей функциональной сборке исправить BETA_BUILD.

## Не трогать

`main`, Windows, сервер, каталог, авторизацию, OTA и второй плеер. Работать только в указанной Android experiment-ветке.

Исторические BETA-документы — архив. Для продолжения читать сначала только этот файл; к архиву обращаться лишь при конкретной необходимости.
