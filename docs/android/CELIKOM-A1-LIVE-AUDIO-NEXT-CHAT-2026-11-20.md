# CELIKOM Android A1 — точка передачи, 20.11.2026

## Репозиторий и границы

- GitHub: https://github.com/manufact-test/nomusic
- Единственная рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Код последнего завершённого этапа: `745179b11b0f837d1cdf9d46cbe142f225c2ffe3`; текущий HEAD до обновления документов: `63b341a3201884aed10eb6f6996ccb12f28c3b3f`.
- Не менять архитектуру. Не пересобирать и не менять NAV40 (`34cb32c88a11743a64c9f4814fa71957223a1391`), NAV45 (`c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`), Test.50, Windows и издательскую Яндекс.Музыку.
- Цель: **одна официальная Яндекс.Музыка и её родной плеер**, на HONOR 50 / Android 13. CELIKOM подменяет только одобренные треки; никаких второго плеера/логина. Сначала получить реально играющий звук, затем Pause/Seek/Next/MyWave, потом VPN и полировка.

## Что реально сделано

1. В оригинальном исходном пути установлены наблюдатели: `Track + Album -> creator-owned tCa -> native Player.e(Sl6,long) -> original MediaPeriod.prepare -> Exo DataSource`. Исходная связь сохраняется и если creator создаёт tCa до Track Flow. Не путать статическую доказанность и проверку на телефоне.
2. Исследованы *конкретные*, подписанные исходные Retrofit `FileInfoApi`/`DownloadInfoApi`: методы с аннотацией trackId абстрактные. Код теперь отслеживает реальный конкретный `InvocationHandler.invoke` только для точно связанных экземпляров прокси и `trackId` оригинального запроса в том же scoped Track. Кандидат сверяется с оригинальным `tCa(String)`, `Track` и `Album`. При несоответствии => original. **Но реальная работа этого перехвата на телефоне ещё не доказана.**
3. **Непосредственно подключён путь закодированных альтернативных байтов к существующему оригинальному Exo `RetryingBalancingDataSource.if(UC2)`, `read([BII)I`, `close()V`**. `NativeExoAlternateByteRoute` читает HTTPS Range. Не создаёт второго плеера. Фильтр допускает только уже подтверждённое право, серверный grant и точный оригинальный экземпляр DataSource; ошибка до первого alt byte — оригинал, после alt byte нельзя смешивать аудиопотоки.
4. Подтверждён конкретный байтовый offset поля `UC2.else:J` подписанного оригинала по исходному конструктору, `toString`, диапазону и length-read. Это position для seek, а не догадка о bitrate.
5. `NativeEarlySourceLifecycleBridge` принимает подтверждение полного тройного ID и одобренный grant в существующий `NativeReplacementLifecycle`; решение ALTERNATE может выдаваться на реальном `MediaPeriod` pre-prepare и вооружает ТОТ ЖЕ оригинальный DataSource. Тесты JVM показывают положительный сценарий передачи закодированных байтов, seek, отмену Next, неверные треки/grant/источник. Отсутствует фактический production caller для полного ID/grant.

## Проверенное CI

- [JVM #44730902321 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44730902321): последние код и тесты маршрута/гонки Next, commit `745179b1`.
- [ARM13 clone #44730740418 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44730740418) и [paired AppMetrica #44730740525 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44730740525), code `8f67f481` (до последнего чисто тестового `745179b1`).
- [Signed original UC2 position #44728951933 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44728951933).
- [Signed API parameter annotations #44729237330 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44729237330): FILE_INFO и DOWNLOAD_INFO имеют **только trackId**, НЕ albumId/editionId. Никаких выдуманных дополнительных API-аргументов.

## Что НЕ готово — прямо и без «всё работает»

- Не доказаны ***первоначальные*** albumId + editionId именно того оригинального текущего source и до prepare. Нельзя считать `Album` Java object автоматически проверенным `album_id`; совпадение из ответа собственного сервера не доказывает исходный native album/edition.
- Не подключено фактическое авторизованное получение CELIKOM resolve/grant из работающего CELIKOM-компаньона к native pre-prepare. В репозитории уже есть `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/NativeApi.java` с `resolve`, а на сервере `server/src/Application/ResolveService.php` с разрешённым каталогом и signed URL, но native Android A1 контрольный путь пока физически не сшит. Нельзя переносить bearer-токен Яндексу или экспортировать его в лог.
- `NativeEarlySourceLifecycleBridge.startForAuthenticatedOwner()` **не подключён к пользовательской кнопке**, `onSourceBoundPublisherFileInfo` и `offerAuthenticatedApprovedAudio` не имеют production callback. Поэтому **CELIKOM_REPLACEMENT=NOT_CONNECTED, подмена не звучит**, owner APK НЕ готов и НЕ выпущен.
- Ни один Android13 CI «SUCCESS» не означает услышанный оригинальный/альтернативный звук на HONOR 50.

## Как продолжить БЕЗ новых дебрей

1. Начать с текущего HEAD и этих кодовых точек: `NativeEarlySourceLifecycleBridge.java`, `NativeExoAlternateByteRoute.java`, `ExitCallsiteWitness.java`, `StageBAudioEvidence.java`, `NativeApi.java`, `NativeGrantContract.java`. Не перебирать многомесячные старые ветки и не переделывать систему.
2. **Непосредственно соединить control plane**: реально подтверждённый исходный triple ID (Track/Album/Edition того же source) -> owner-authenticated CELIKOM resolve/grant -> исходный MediaPeriod before-prepare -> уже написанный alternate Exo byte route. Никакой активации на частичном ID.
3. Выпустить одну действительно играющую тестовую версию Android после готовности цепи, дать пользователю APK через подтверждённый путь Library/файл. Первый фикс-кейс: RASKOL «Нас не понимают вообще», trackId 42884423; второй Лёша Свик «Дым», trackId 39949113. Проверять только реальное звучание и родное управление.
4. **НЕ** тратить время на новые общие DEX-сканы, бессмысленные guard-патчи, диагностические APK, архитектурные перезапуски, тему VPN или косметику до первой звуковой подмены. Если реальный оригинальный albumId/editionId не удаётся подтвердить, прямо сказать об этой блокировке. Не выдумывать успех.

## Ритм работы с владельцем

Работать продолжительными продуктивными заходами, без промежуточных мини-отчётов. Писать лишь при необходимой помощи/тесте владельца или при существенном достижении. Сохранять коммиты и сразу обновлять документы. Не говорить «APK готов» до реальной сборки и проверки. **Приоритет — звучащая официальная Яндекс.Музыка через CELIKOM, а не идеальная диагностика.**
