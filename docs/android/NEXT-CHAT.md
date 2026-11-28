# CELIKOM Android A1 — актуальное состояние

Дата: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Код: BETA36 NAV56 (owner APK delivered; phone diagnostic pending)

## Что уже проверено

- **BETA32 MP3 override — НЕ РАБОТАЕТ:** ломал воспроизведение. Не повторять MP3/AAC override без новой доказанной причины.
- **NAV54 работает до чтения альтернативных байтов:** BETA34 и BETA35: FIRST_OPEN_CANDIDATE_ACCEPTED=ONE, DATASOURCE_ARMED=ONE, AUDIO_OPEN=ONE, AUDIO_READ=MANY. Сохранять.
- **BETA35 NAV55 на Honor 50 — слышимой подмены НЕТ.** Диагностика CELIKOM-A1-Diagnostics-1795873462104.txt: CELIKOM_REPLACEMENT=NOT_CONNECTED.
- NAV55 подтвердил точный класс **o96**, интерфейс wh6 и тот же объект при select, attach и read. Фактический путь прямой (LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT=MANY), не up1. Повторять проверку holder не нужно.
- LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY, но LIVE_RENDERER_ALT_SOURCE_READ_SAME=NONE; NO_ROUTE_CURRENT_PERIOD=FEW, DATASOURCE_UNRESOLVED_CURRENT_PERIOD=FEW. В диагностике также есть TCA_CREATOR_WRAPPER_NOT_FLOW=FEW и TCA_CREATOR_WRAPPER_NO_ALBUM=FEW.
- **NAV56 / BETA36 code change:** live lookup теперь сохраняет exact creator/source proof через firstOpenSourceCommitted после успешного first-open arm. После commit он не переопрашивает ограниченные wrapperBirths/BETA/Flow registries; до commit строгая creator-проверка остаётся. Audio route/admission/codec не менялись.
- Добавлен JVM regression fixture: committed DataSource должен разрешаться после очистки creator history; rejected first-open не получает этот обход.
- **BETA36 NAV56 CI:** validation run `46153378323` PASS; export-enabled run `46154387456` PASS. JVM + publisher-first ARM13 PASS; verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `stage_a=NO_GO` — это не акустическая проверка. `owner_phone_touched=false`; signer verified, `UPDATE_EXISTING` matches installed owner cert.
- Owner-only draft: [BETA36 APK](https://github.com/manufact-test/nomusic/releases/download/untagged-51969331ea5269f59bc6/CELIKOM-A1-RAMIL-AU-BETA36-HONOR50-20261128.apk) · [release and files](https://github.com/manufact-test/nomusic/releases/tag/untagged-51969331ea5269f59bc6). Size 71,606,252 bytes; SHA-256 `e632bbb881d5eb63dc774f4bd8de379ab4ad93d7603751d22009f32d55294ba0`. Source commit `07ee94b19199173b962517427815c0dbcd7e9e89`. Acoustic replacement remains unproven.

## Что выяснили по оригинальному Яндексу

Read-only анализ подписанного Yandex 2025, CI run `46144076359`: **PASS**.

- Точный `DataSource.open`: 18 прямых вызывающих методов.
- Точный `DataSource.read`: 23 прямых вызывающих метода.
- Ни один из них и ни один найденный upstream-метод не подтвердился как ExoPlayer Loadable.
- Связь этих вызовов с `Lo96` / `MediaPeriod` не доказана. Активный renderer/source link статически не установлен.
- Отдельно найден статический путь `Lp96` → `Lo96` → `Lwh6` / `Lup1` → native holder. Это только структура оригинального кода, не доказательство, что именно этот period активен на телефоне.
- Анализатор исправлен: повторные callsite больше не считаются отдельными рёбрами. Получено 856 289 уникальных связей; 6 regression tests PASS.

## Следующий шаг

1. На Honor 50 установить BETA36 поверх BETA35. Не удалять CELIKOM и не очищать данные.
2. Воспроизвести проблемный трек («Ау», 00:43–00:54) и, если возможно, второй проблемный трек. Экспортировать диагностику CELIKOM и передать её в следующий чат.
3. В диагностике проверить `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` и связанные события текущего MediaPeriod/DataSource.
4. Если событие появилось — переходить к проверке renderer → decoder. Если нет — исследовать точное соответствие DataSource активному MediaPeriod. Holder/NAV55 заново не проверять.
5. NAV56 CI и APK уже готовы: не повторять CI, не собирать новую версию и не менять MP3/AAC override или publisher codec request без причины из диагностики.

## Не трогать

`main`, Windows, сервер, каталог, авторизацию, OTA и второй плеер. Работать только в указанной Android experiment-ветке.

Исторические BETA-документы — архив. Для продолжения читать сначала только этот файл; к архиву обращаться лишь при конкретной необходимости.
