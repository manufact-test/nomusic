# CELIKOM Android A1 — актуальное состояние

Дата: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Код: BETA36 NAV56 (CI/device verification pending)

## Что уже проверено

- **BETA32 MP3 override — НЕ РАБОТАЕТ:** ломал воспроизведение. Не повторять MP3/AAC override без новой доказанной причины.
- **NAV54 работает до чтения альтернативных байтов:** BETA34 и BETA35: FIRST_OPEN_CANDIDATE_ACCEPTED=ONE, DATASOURCE_ARMED=ONE, AUDIO_OPEN=ONE, AUDIO_READ=MANY. Сохранять.
- **BETA35 NAV55 на Honor 50 — слышимой подмены НЕТ.** Диагностика CELIKOM-A1-Diagnostics-1795873462104.txt: CELIKOM_REPLACEMENT=NOT_CONNECTED.
- NAV55 подтвердил точный класс **o96**, интерфейс wh6 и тот же объект при select, attach и read. Фактический путь прямой (LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT=MANY), не up1. Повторять проверку holder не нужно.
- LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY, но LIVE_RENDERER_ALT_SOURCE_READ_SAME=NONE; NO_ROUTE_CURRENT_PERIOD=FEW, DATASOURCE_UNRESOLVED_CURRENT_PERIOD=FEW. В диагностике также есть TCA_CREATOR_WRAPPER_NOT_FLOW=FEW и TCA_CREATOR_WRAPPER_NO_ALBUM=FEW.
- **NAV56 / BETA36 code change:** live lookup теперь сохраняет exact creator/source proof через firstOpenSourceCommitted после успешного first-open arm. После commit он не переопрашивает ограниченные wrapperBirths/BETA/Flow registries; до commit строгая creator-проверка остаётся. Audio route/admission/codec не менялись.
- Добавлен JVM regression fixture: committed DataSource должен разрешаться после очистки creator history; rejected first-open не получает этот обход.
- BETA35 build `517905c`, CI `46148935304` PASS; owner draft `celikom-a1-owner-46148935304-1`. JVM `46147441043` PASS. ARM13 только запуск, NOT_AUDIO.
- **BETA36 NAV56 CI:** run `46153378323` PASS, JVM + publisher-first ARM13 PASS; verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. `stage_a=NO_GO`; это не акустическая проверка. Владелец/его телефон CI не затрагивал. Export-enabled run `46154387456` выполняется; owner draft APK ещё не готов.

## Что выяснили по оригинальному Яндексу

Read-only анализ подписанного Yandex 2025, CI run `46144076359`: **PASS**.

- Точный `DataSource.open`: 18 прямых вызывающих методов.
- Точный `DataSource.read`: 23 прямых вызывающих метода.
- Ни один из них и ни один найденный upstream-метод не подтвердился как ExoPlayer Loadable.
- Связь этих вызовов с `Lo96` / `MediaPeriod` не доказана. Активный renderer/source link статически не установлен.
- Отдельно найден статический путь `Lp96` → `Lo96` → `Lwh6` / `Lup1` → native holder. Это только структура оригинального кода, не доказательство, что именно этот period активен на телефоне.
- Анализатор исправлен: повторные callsite больше не считаются отдельными рёбрами. Получено 856 289 уникальных связей; 6 regression tests PASS.

## Следующий шаг

1. Проверить push-triggered CI для NAV56: JVM regression, publisher-first ARM13 и сборка собственного модуля. До PASS APK владельцу не выдавать.
2. После PASS сделать owner-only BETA36 APK с постоянной подписью и установить update поверх BETA35, не удаляя CELIKOM.
3. На телефоне проверить один трек и экспорт. Главный показатель — LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS.
4. Если он появился, связь активного o96 → committed DataSource → renderer подтверждена; следующий этап — только renderer → decoder. Если не появился, исследовать точное соответствие DataSource текущему MediaPeriod. Holder/NAV55 заново не проверять.
5. Не возвращать MP3 override, не менять publisher codec request и не собирать APK только ради новых счётчиков.

## Не трогать

`main`, Windows, сервер, каталог, авторизацию, OTA и второй плеер. Работать только в указанной Android experiment-ветке.

Исторические BETA-документы — архив. Для продолжения читать сначала только этот файл; к архиву обращаться лишь при конкретной необходимости.
