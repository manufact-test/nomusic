# CELIKOM Android Test.66 — 08.11.2026

## Диагностика с реального HONOR
В `CELIKOM-combined-20261108-164848.txt` находятся три прогона (Test.62/64/65). У Test.65: 15 наблюдаемых треков; «ИСКАЛА» (Земфира) / «Гармония» (ARTIK & ASTI) дали HTTP 451 через ~0.42 / 0.14 с, `hybrid_identity` перешёл к `no_unique_candidate`; обе песни отсутствуют по строгому сравнению title/artist/duration в свежем **только approved** каталоге из 133 песен. Пользователь видел известный заголовок в шторке и некорректный нижний статус «Определяем песню». На «Новогодняя» полный переход 1.90 с, «Скажи» 1.57 с, другие успешные часто 0.46–0.9 с. Доказательств решения разной скорости нет.

## Исправление
Ветка `feature/android-0385-test66-catalogue-first-ui-regression-20261108` на Test.65. `AlbumProbe` публикует UI свой текущий результат сравнения с собственным свежим approved-каталогом независимо от Track ID. `PlaybackUi` передаёт достоверное состояние `catalogueFresh/catalogueStatus`; `AppPresentation` и `NotificationState` показывают статус каталога *до* или *без* точного Yandex Track ID: доступная версия / нет подходящей в approved / несколько похожих / нет данных. Устаревший каталог не используется для категорического утверждения. Заголовок виден и в Activity, а кнопки подачи остаются привязаны к подтверждённому Track ID. В ожидании проверки CELIKOM пишем «Проверяем наличие версии CELIKOM…», а не «Определяем песню», которую уже назвал Media3. Пауза не обнуляет результат approved-каталога.

Статус модерации не угадывается: серверный `ReplacementCatalogueService` намеренно публикует только одобренные замены, для `pending` нужен подтверждённый Track ID и отдельный live endpoint. `source/title` не доказывают идентичность издания. Звуковой механизм (seek/BUFFERING/fade/prefetch) и сетевую проверку не меняли. Добавили `notification_status_published` с фактически отправленным в Android текстом для следующей HONOR-диагностики. Новые host-тесты со свежим и устаревшим каталогом, известными и неизвестными песнями; устаревшее golden ожидание «Определяем песню» заменено.

## CI, подпись, доставка
- [GitHub Actions #42487539077](https://github.com/manufact-test/nomusic/actions/runs/42487539077) **SUCCESS**, source commit `b355c6ac3b1fe4ebc6447ee7c48e13451c770bb7`. Full host + Android D8 & isolated signed test build PASS.
- APK `CELIKOM-Android-0.3.85-TEST-66-CATALOGUE-FIRST-SIGNED.apk`, `0.3.85-test.66`, code `86152`, package `pro.celikom.nativeprobe.test`.
- SHA-256 `1714f9172196d98ab4b3b94941a5a9fc581524c616ae9ecd2a48902807e40dcf`; signing cert `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, `signature_v3_verified=true`, `signer_matches_original=true`.
- [APK в Library CELIKOM / Android / Test](https://chatgpt.com/library?file_id=libfile_8823b6330ee4819181ee7e9e9c82a462&account_id=personal). Там же JSON-проверка и квитанция сборки. [GitHub artifact #13619279521](https://github.com/manufact-test/nomusic/actions/runs/42487539077/artifacts/13619279521).
- Stable/OTA/Hostinger/backend/desktop/Test.50 **не тронуты**. Физическая проверка уведомления на HONOR ещё нужна; реальная скорость/акустика Test.66 не проверена.

## Физическая приёмка
На HONOR включить «ИСКАЛА», «Гармония», одобренную песню «Пушка» и песню без одобренной версии: шторка должна сразу показывать статус одобренного каталога, а не бессрочное «Определяем песню». Посмотреть как статус меняется при паузе, next, 451; экспортировать combined, сравнить `notification_status_published` с тем, что пользователь увидел. Отдельно сравнить реальные задержки холодного vs warm, не объявлять RASKOL 42884423/«Дым» 39949113 исправленными.
