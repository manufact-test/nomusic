> **ВАЖНО — АКТУАЛЬНОЕ РЕШЕНИЕ ВЛАДЕЛЬЦА (10.11.2026).** Архитектура согласована окончательно: **один APK CELIKOM с нативной Яндекс.Музыкой и одним её аудиодвижком; LSPatch только для закрытого прототипа, после принятия эталона — напомнить владельцу и начать собственный независимый механизм внедрения по согласованию.** WebView/собственный музыкальный UI не выбирать.
>
> **[ПОЛНОЕ АКТУАЛЬНОЕ ТЗ](CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md)** · **[НОВЫЙ ТЕКСТ ПЕРВОГО СООБЩЕНИЯ](NEXT-CHAT-NATIVE-CLONE-20261110.md)** · **[РЕШЕНИЯ ВЛАДЕЛЬЦА](ANDROID-PLAN-A-OWNER-DECISIONS-CHECKPOINT-20261110.md)**.
>
> Старые заявления ниже о «главном ТЗ» (WebView, собственный API-клиент, отдельный музыкальный плеер, companion) **исторические и не имеют приоритета**. При противоречиях выполнять новое master-ТЗ.

---

# АКТУАЛЬНОЕ ТЗ ВЛАДЕЛЬЦА — ПРОДОЛЖИТЬ ПЕРВЫЙ CELIKOM С ЯНДЕКСОМ ВНУТРИ (10.11.2026)

**ВМЕСТО ПРЕЖНИХ ПРОТИВОРЕЧИВЫХ ОПИСАНИЙ ниже сначала прочитать** [полное исправленное ТЗ](ANDROID-PLAN-A-OWN-YANDEX-CLIENT-HANDOFF-20261110.md) и [первое сообщение следующему чату](START-NEXT-CHAT-ANDROID-YANDEX-CLIENT-PLAN-A-20261110.md). **План А: восстановить именно нашу раннюю версию, в которой при открытии CELIKOM Яндекс уже открывался внутри, и продолжить её, используя все собственные Android, Windows, extension и server наработки.** Нужны привычный Яндекс внутри CELIKOM и подмена аудио **в его же плеере**, без собственного музыкального UI, отдельного музыкального плеера или двух потоков. **Не утверждать до проверки, была ли первоначальная реализация WebView или нативным клиентом; найти точный исходник и ограничения по коммитам.** Предыдущий текст «план А — самостоятельный Yandex API client + наш Media3/ExoPlayer» ОТМЕНЁН. Liberty Android не готовая база под заданный UI; изучать технические интерфейсы без копирования GPL-кода. Рабочая документационная ветка `feature/android-yandex-client-plan-a-20261110`; код старых веток и бэкапы не менялись.

---

# ВАЖНО — НОВЫЙ УТВЕРЖДЁННЫЙ ПЛАН А (10.11.2026): собственный Android-клиент CELIKOM + каталог Яндекса + ОДИН плеер

**ПЕРВЫМ ДЕЛОМ ОТКРЫТЬ [полное новое ТЗ](ANDROID-PLAN-A-OWN-YANDEX-CLIENT-HANDOFF-20261110.md) и [первое сообщение следующему разработчику](START-NEXT-CHAT-ANDROID-YANDEX-CLIENT-PLAN-A-20261110.md).** Рабочая новая ветка `feature/android-yandex-client-plan-a-20261110`. Владелец ВЫБРАЛ эту архитектуру **как план А**: наш собственный Android интерфейс и один плеер получают разрешённые оригинальные записи, каталог, плейлисты и «Мою волну» Яндекса через пользовательский аккаунт и собственную безопасную интеграцию; наша платная CELIKOM подмена выбирается по trackId ДО play. Имеющийся ниже архив про сторонний companion + официальную установленную Яндекс.Музыку, hooklab, WebView и автономный Media3-only **НЕ ЯВЛЯЕТСЯ текущим ТЗ**. Не возобновлять прежнюю неделю DEX исследования. GPL-исходники Liberty не копировать; изучить интерфейсы, писать самостоятельно; обязательна проверка разрешённого потокового доступа. Отдельно обязательно изучить наши свежие Windows наработки `experiment/windows-stop-lifecycle-20261110`. Исходники/старые ветки не изменены этим handoff. 

---

## АКТУАЛЬНАЯ NATIVE ANDROID ТОЧКА (10.11.2026): ПОДМЕНЫ ЕЩЁ НЕТ, НО СЕРЬЁЗНАЯ ОШИБКА HOOK-WITNESS УСТРАНЕНА

- **Только НОВАЯ нативная ветка**, `experiment/android-native-yandex-fileinfo-hooklab-20261109`. Не Test.50, не Test.51, не старое «как эквалайзер», не Windows и не второй плеер.
- [Большой блок: t()-transaction + точная ocv.i0→ero owner/source цепь](ANDROID-NATIVE-T-TRANSACTION-OCV-LERO-OWNER-20261110.md). В старом наблюдателе `t()` считался успешным ДО того, как исходный Yandex `t()` завершался; мог показывать ложные reader-success после исключения/конкурентного Next. Исправлено: BEGIN→pending reader→только успешный original `chain.proceed()`→COMMIT; ошибка, remove, clock rollback, повторный t, спорные одновременные callback отменяют/не повышают «успех».
- `NativeOwnerConstructionWitness`: новый ThreadLocal scope exact `ocv.i0()V`, два зарегистрированных `ero` конструктора, совпадение той же Java-ссылки, запрет смешивать поток/реэнтрантность/двух детей. `NativeSourceDispatchWitness.onOwnerChild` требует также тот же `ocv` в `t`, exact `ero`, exact `mb4` и успешные чтения. Логируются только счётчики, никаких URL/треков/ключей/аудио/изменения чужого APK.
- **[CI #42871291865 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42871291865)**, проверенная версия **`276ab6fc44014c8419c8e31ce4250bf7cf8f451d`**, независимый immutable rollback **`backup/android-native-transaction-owner-observer-ci-green-20261110`**; 20029 синтетических source-t/reader race assertions, 10022 owner-child, остальные JVM/Android module 2/2. **Это не устройство и не аудиотест!**
- **[Signed #170gpr DEX preflight #42871064983 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42871064983)**: 5 signed APK, 6 DEX, 7/7 методов, 2/2 конструктора `Lero`, 1 поле `Lero→Lmb4`, 1 точный `Locv.i0` и 1 прямой ctor invoke внутри `i0`. Но строгая same-straightline связь new-instance→invoke = 0, поэтому регистрационный доказанный новый объект в одном basic-block НЕ утверждать.
- **STOP-SHIP:** native Gate 0.1 ранее заблокирован Google Play Protect на основном HONOR и выведен из выдачи/CI upload. Не присылать больше диагностические APK, не обходить Play Protect или подпись Яндекса. Нет разрешённого in-process official Yandex source→actual selected track+edition+generation→decoder-before-prepare bridge; **нет работающей новой подмены и нет основания просить ручную проверку**. Продолжение см. [GO/NO-GO](ANDROID-NATIVE-PUBLISHER-BRIDGE-GO-NOGO-20261110.md). Owner-accepted Test.50 SHA `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1` отдельно проверен как НЕИЗМЕННЫЙ.
- Следующий настоящий критерий: разрешённый host, который запускает настоящий Yandex под нормальной Android защитой и доказывает *same current selected player/source* на decoder preprepare. До него никакая правдивая готовая one-player APK не выпускается. Не заменять очередной синтетической моделью.

---

## АКТУАЛЬНАЯ ОСТАНОВКА ПО АРХИТЕКТУРЕ (10.11.2026): NATIVE ONE-PLAYER RELEASE = NO-GO

- **[Технический GO/NO-GO и официальные ограничения Android / Media3 / Play Protect](ANDROID-NATIVE-PUBLISHER-BRIDGE-GO-NOGO-20261110.md)**. Это не Test.50 и не Test.51, не Windows, не второй MediaPlayer. Предыдущий эксперимент Native Gate заблокирован Play Protect на HONOR, **STOP-SHIP**, файл помечен в Library `REJECTED_DO_NOT_INSTALL` и его сборка/выдача в CI отключены.
- В исходной новой нативной ветке исправлен **фактический пропуск создания Lero**: `Locv.i0` может строить `Lero` прямо, минуя `Lkvs.A`; теперь наблюдатель отслеживает оба точных конструктора через `==`, отдельно от фабрики, и связывает с `Lmb4.a/Lha4.open/read/close` при реальном вызове. **[CI signed DEX 1+1 ctor / 7 methods / 1 field — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42866551757)**, **[CI Java regression + Android module — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42866551803)**. Проверенный исходник `b3752aad5d2b34d1816d323baeb41453ff81c3ba`; backup `backup/android-native-dual-constructor-source-observer-signed-ci-green-20261110`.
- **НЕ доказаны** реальный native Yandex selected source, текущий `trackId+edition+generation`, decoder descriptor before prepare или установка штатного подписанного Yandex с нашим разрешённым модулем. Стоковый Android sandbox не позволяет произвольному соседнему APK менять private DataSource оригинального Яндекса. MediaSession команды не являются доступом к аудиодекодеру, и сторонний controller может иметь только чтение. Без нового **разрешённого in-process bridge** рабочий Android native one-player APK при заданных условиях не может быть выпущен.
- **НИЧЕГО НЕ ПРОСИТЬ У ВЛАДЕЛЬЦА УСТАНОВИТЬ** и не предлагать следующий лабораторный APK как working version. Только согласованный новый легитимный механизм интеграции откроет путь к пользовательской QA. Owner Test.50 frozen, HONOR, original Yandex, Windows, extension, production/API/DB не трогать.

---

> **STOP-SHIP / НЕ УСТАНАВЛИВАТЬ (10.11.2026).** Владелец проверил `CELIKOM Native Gate 0.1` на HONOR 50: **Google Play Protect заблокировал установку без варианта продолжить**. Это НЕ прошедший пользовательскую проверку APK, несмотря на green CI и корректную криптографическую подпись. Отладочная подпись и объявленный `NotificationListenerService` — потенциально значимые факторы, но **конкретная причина срабатывания не установлена**. Не отключать Play Protect, не искать обход «Установить всё равно», не перекомпилировать для сокрытия детекта, не переустанавливать Яндекс, не просить пользователя повторно устанавливать эту сборку. Задача Native Gate **отклонена**; файл в Library и старый Actions artifact — архивные, НЕ для распространения. CI-этап сборки/загрузки APK отключён. `Test.50`, stable, Windows, HONOR и оригинальный Яндекс не изменялись. Резерв `backup/android-native-before-play-protect-rejection-20261110`. Новая native source-first подмена не готова: продолжаем только законные собственные/изолированные тесты и статический анализ до реального разрешённого selected-decoder witness.\n\n## АРХИВ / ОТКЛОНЕНО Play Protect: MediaSession Gate (10.11.2026)

- **Новая нативная одно-плеерная архитектура**, НЕ Test.50, НЕ Test.51 и НЕ «эквалайзер». Готова отдельная подписанная *диагностическая*, **НЕ аудиоподменяющая** APK `CELIKOM Native Gate` для проверки публичных возможностей уже работающего оригинального Яндекса на HONOR.
- **[Полный документ, приватность, ручной чек-лист, SHA256](ANDROID-NATIVE-HONOR-PUBLIC-SESSION-GATE-2026-11-10.md)**. [GitHub CI #42863386941 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42863386941). Точный проверенный код `f565c5650fcf018ae946597e0fc47b2ecb50bc53`; frozen backup `backup/android-native-public-session-gate-signed-ci-green-20261110`; APK SHA256 `1c4672a72dc1a2f2be030e5edff3600a8a2cbe1c5c3c618d5ffc3063d6cd1bd6`. APK из GitHub Actions извлечена, SHA сверен с build receipt, копия в Library `/CELIKOM/Android/Native/CELIKOM-Native-Gate-0.1-READONLY.apk`.
- Проверка №1 **без разрешений**: публичный media service binder; №2 **добровольно и только с явным системным широким доступом к уведомлениям**: `MediaSessionManager.getActiveSessions` уже работающего Яндекса и ONLY BOOLEAN platform/Media3 command flags. NotificationListener callbacks пусты; интернета, сохранения данных, треков, паролей/URI, playback команд и подмены источника нет. Android запрещает разрешение — **не обходить** Play Protect/restricted settings. После проверки отозвать доступ. На телефоне ещё не проверено.
- **Даже CHANGE_MEDIA_ITEMS=true НЕ означает native source-first подмену**. Это всего лишь проверка доступных MediaSession команд. Реальный выбранный decoder/source, `trackId+edition+generation` и альтернативная аудиодорожка пока НЕ доказаны. Путь через исходную нативную архитектуру остаётся NO-GO, пока не появится разрешённый источник до decoder prepare. Отдельный native read-only Lero/Lmb4/Lha4 код/DEX с прежним CI-green сохранён.
- Основной Яндекс на HONOR, owner-accepted Test.50, Test.51, Windows, расширение, API, DB и production НЕ изменялись.

---

## АКТУАЛЬНАЯ NATIVE ANDROID ТОЧКА — source→reader nested execution, CI GREEN (10.11.2026)

- **ЭТО НОВАЯ ОДНОПЛЕЕРНАЯ НАТИВНАЯ РАЗРАБОТКА, НЕ TEST.50, НЕ TEST.51 И НЕ DynamicsProcessing.** Ветка `experiment/android-native-yandex-fileinfo-hooklab-20261109`. Старый Test.50 «как эквалайзер» — независимый принятый эталон; случайная Test.51 не используется.
- **[Детальный отчёт](ANDROID-NATIVE-SIGNED-LERO-READER-EXECUTION-2026-11-10.md).** Native реальный код `6146109dd77352dbc73563c26dcaf1dfd6ff6c38`, rollback `backup/android-native-lero-lmb4-ha4-signed-readonly-chain-ci-green-20261110`.
- **[JVM + Android module #42860807834 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42860807834)**; **[signed 5-APK, 6-DEX exact method/field check #42860839260 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42860839260)**: семь точных определений методов `Lkvs.A / Lero.t/remove / Lmb4.a / Lha4.b/read/close` и ОДНО поле `Lero→Lmb4` действительно существуют в оригинале.
- Код через точную reference identity соединяет factory `Lkvs.A` → `Lero.t` → принадлежащий `Lmb4.a` → реальный `Lha4` open/positive read/close **только если hooks фактически исполнятся в разрешённом host**. 10 000 synthetic cycles, защита от разных объектов/поколений/потоков/exception. **Никакой аудиоподмены в Яндексе пока нет и на HONOR ничего не устанавливалось.**
- **Жёсткий единственный блокер:** исполняемый разрешённый native ARM Android host, который может доказать *actual selected current track+edition+generation → настоящая decoder source before prepare*. Без этого Xposed-модуль остается наблюдателем, обычный отдельный Android APK не сможет изменить чужой player из sandbox. Не повторять x86 LSPatch/clone/AppMetrica, не подменять это OWN WAV тестами.
- Отдельно проверено направление ARM TCG без KVM: официальная Android Emulator software `-accel off` **неподдерживаемая и очень медленная**, а публичная лабораторная сборка `lhns/android-arm-tcg` для установки больших APK требует обхода проверки подписи в системном oat. Это **запрещено для CELIKOM**, не использовать как доказательство нормальной защищённой установки Яндекса. Play Protect/DRM/signature не обходить.
- Owner-accepted Test.50, Test.51, официальный установленный Yandex/HONOR, Windows, расширение, API/БД, production, server НЕ трогать. Никакого «готово» и user APK до доказанной native подмены.

---

## ВАЖНО: НОВАЯ НАТИВНАЯ ANDROID ВЕТКА (10.11.2026)

- **ЭТО НЕ Test.50/эквалайзер!** Работа по исходной native-Yandex one-player архитектуре продолжается **только** в `experiment/android-native-yandex-fileinfo-hooklab-20261109`. Случайная Test.51 из другой ветки не относится к этой задаче и не должна переноситься сюда.
- [Новый read-only runtime-кандидат Lemb factory→t same-instance](ANDROID-NATIVE-LEMB-INSTANCE-RUNTIME-WITNESS-2026-11-10.md): exact `Lkvs.A(zcb,gmb):emb` + восемь `Lemb.t(dmb)/remove` реализаций; наблюдение `==` объекта без URL, звука, токенов и модификации Яндекса. Кодовой SHA `9073ea35d3f5ef2a996b197d237f4265ab0ab564`; CI требует подтверждения после текущего push.
- Текущий результат **не является работающей подменой**: source factory→t может быть фоновым; не доказаны активный current `trackId+edition+generation`, decoder prepare и разрешённый in-process host. Пока NO-GO к user APK.
- Исторический, принятый владельцем Android Test.50 и вся прежняя работа с DynamicsProcessing не имеют отношения к этой ветке и запрещены к изменениям. HONOR, Windows, расширение, API/БД, production и официальный APK не трогать.

---

# CELIKOM Android — актуальная навигация к передаче (10.11.2026)

**Начальная точка:** `docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md` — готовый текст первого сообщения новому разработчику.

## НОВЕЙШАЯ CI GREEN — Android 13 real MediaPlayer rapid Start/Stop/Next race PASS (10.11.2026)

- **Точный код:** `50735e6d56481ea0ce3da8fdcb03589cad90608c`; **неизменяемый rollback:** `backup/android-own-api33-rapid-reload-race-pass-20261110`. **Читать первым:** `docs/android/ANDROID-OWN-API33-RAPID-RELOAD-RACE-PASS-2026-11-10.md`.
- **Реальный Android 13 Google APIs x86_64 emulator / OWN-WAV only / noaudio**: обычный source reload с сохранением Pause/Seek/Next **PASS** и **новый быстрый стресс** 12 round / 48 media-player creates / max1 concurrent / 47 release, 12 B prepared, 6 Paused+Seek **PASS**. CI зафиксировал **`RESULT=PASS CODE=OWN_DECODER_LIFECYCLE` И `RESULT=PASS CODE=OWN_ASYNC_RACE_PASS`** в одном run [#42837053639 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837053639).
- Починен настоящий баг OWN UI: второй Start/Stop **до `onPrepared`** сбрасывал pending restore position в 0; теперь `restoreSeekMs>0` действует с начала prepareAsync. 36 искусственно вставленных stale-tickets отсекаются generation guard, но **реальное число framework late callbacks не измерено** — не путать.
- **Android ARMv7 host [#42837003150 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003150), own scoped module [#42837003307 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42837003307), native research [#42837003096 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42837003096)** на соседнем SHA `31c34b23`; после него менялась **только workflow safety-check** (проверено compare). Оригинальный Yandex/owner Test.50/Windows/API/production НЕ менялся.
- **Android Yandex runtime selected Lemb / trackId+edition+generation → real decoder preprepare НЕ ДОКАЗАН**. Обычные Android `AudioPlaybackCallback`/MediaSession уведомления не открывают объект DataSource чужого плеера. Android CELIKOM source swap по-прежнему **NO-GO**, не выдавать собственный тестовый APK за готовую подмену.

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ ANDROID RUNTIME PASS — API33 OWN MediaPlayer, source reload/Seek/Pause/Next (10.11.2026)

- **CI GREEN код:** `bb26aca9652850c69fbd0896a26bec22601826b0`, **точный immutable backup:** `backup/android-own-api33-real-mediaplayer-source-reload-pass-20261110`, **главный документ:** `docs/android/ANDROID-OWN-API33-MEDIAPLAYER-RUNTIME-PASS-2026-11-10.md`.
- **Впервые реальные Android 13 native MediaPlayer callbacks в эмуляторе, не JVM модель:** собственный WAV A 440 Hz → Seek 2.2 с → Pause → SAME-TRACK Start alternative A 660 Hz с сохранением Pause и позиции → Resume → Stop, original A 440 Hz с сохранением Playing/позиции → Next B original 330 Hz. Источник выбирается через тот же `OwnSameTrackReloadPlan.decide`; старый плеер сначала release, новый один. На реальном Android CI `RESULT=PASS CODE=OWN_DECODER_LIFECYCLE`.
- **[Android 13 OWN runtime #42835181030 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181030)**; на том же SHA [OWN ARMv7 host+50 020 tests #42835181029 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181029), [scoped own module #42835181289 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181289), [native-Yandex research build #42835181034 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181034).
- **Жёсткая граница:** Android emulator x86_64 использует только OWN-пакет, WAV и `-noaudio`; не доказывает слышимый звук, Android-Яндекс, выбранный Lemb из 8 реализаций, trackId+edition+generation или декодер Яндекса. Реальная Android CELIKOM-подмена всё ещё **NO-GO**. Original/Test.50/HONOR/Windows/API/production не трогать.

## ПРЕДЫДУЩАЯ CI GREEN — Windows 0.24.9 audio lessons → OWN Android same-track reload (10.11.2026)

- **Проверенный code SHA:** `a7f83f0ab836bbeeb12538c6a389c9569d326610`; **замороженный rollback:** `backup/android-windows-w60-owned-reload-armv7-arm64-ci-green-20261110`; главный документ: `docs/android/ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md`.
- **Наконец сопоставили реальные исходники Windows:** `w22/native-resource-adapter.mjs` + `w60/current-source-refresh.mjs` и свежие W57/W60/W61/W62/W63. Owner audio/Pause/Seek/Next/MyWave/Start/Stop **PASS на Windows 0.24.9**, W63 (0.24.11) пока пользовательский UI-кандидат. Windows работает через проверенный `getFileInfo` и Electron `7123.VE.reloadEntity("QUALITY_CHANGE")`; Android **не имеет доказанного идентичного API**.
- Из принципов Windows портирован **реально собираемый ARMv7 OWN-only Android стенд:** `OwnSameTrackReloadPlan.java`, новые Start/Stop в `AudioSmokeScreen` для той же 8-секундной искусственной песни A. **Только при смене источника** релиз единственного `MediaPlayer` и создание нового; position/paused восстанавливаются после `prepareAsync→seekTo`, быстрые повторные нажатия защищены revision, Next B остаётся оригиналом. **Не Яндекс!**
- **CI SUCCESS:** [OWN ARMv7 Android build + safety + 50 020 assertions #42830966825](https://github.com/manufact-test/nomusic/actions/runs/42830966825); [ARM64 Linux JVM test #42831135970](https://github.com/manufact-test/nomusic/actions/runs/42831135970). Нет физического Android-аудио теста и live Yandex decoder evidence, оригинал не меняли.
- **Windows W56 query guard не переносить на Android:** вызван конкретным Windows `DownloadInfoSource` append `?vsid`; подтверждения такого Android транспорта нет; `NativeGrantContract` правильно отклоняет неподписанные дополнения. Не копировать JS Electron reload, ключи/IV, DRM и URL в неподтверждённый Android путь.
- **Единственный главнейший blocker:** выбранный live `Lemb` receiver (из восьми вариантов) + тот же current `trackId/edition/generation` → истинный decoder preprepare. Без отдельного ARM Android test host нельзя обещать owner APK. Test.50/HONOR/Windows/production не трогались.

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — строгий source-instance fail-closed на ARM64 (10.11.2026)

- **Исходники и тесты SHA:** `59aa2d14bf32fd0f5eb553c09ec88738d84353a0`; **точный бэкап:** `backup/android-signed-source-instance-failclosed-arm64-ci-green-20261110`. **Главный отчёт:** `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- После предыдущего green `3aaab880` поймали дополнительную ошибку исследовательского допуска: после событий `OUT_OF_ORDER` более поздний чистый `open/read/close` мог снова дать `syntheticSequenceComplete=true`. Исправлено: **любое rejected-событие текущего поколения навсегда лишает его статуса complete**; stale-вызовы старых поколений новое не портят. Добавлены регрессии.
- **[Нативный ARM64 Linux JVM #42828086262 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42828086262)**: 44 480 OWN-ONLY assertions + 27 concurrency checks, 4 800 stale callbacks. **[Read-only Android module #42828086264 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42828086264)**. Signed original Lemb factory source census [#42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492).
- `NativeSourceInstanceFence` — чистая локальная Java-модель без подключения к `NativeHookEntry`. Нет live Android ARM runtime decoder proof, selected trackId/edition/generation / Lemb source match, Android аудиоподмена **НЕ** работает; HONOR/Test.50/Windows/production не трогали.

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ CI — Lemb source alternatives + exact source-instance generation fence (10.11.2026)

- **CI GREEN SHA:** `3aaab880fff4326b596f63a52a89a0f4d0085fef`; **точный бэкап:** `backup/android-signed-source-instance-arm64-lemb-ci-green-20261110`. **Читать первым:** `docs/android/ANDROID-NATIVE-SOURCE-INSTANCE-ARM64-AND-LEMB-BRANCHES-2026-11-10.md`.
- Подписанный original #170gpr: **8 concrete Lemb implementations**, 4 direct `Lemb.t/remove` callsites в `Lchg.t/remove`, `Lciv.e`, `Larv.g`. Даже доказанный ранее `Lero→Lwq7→Lmb4` может быть **не выбранным** источником.
- В factory `Lkvs.A` есть 4 условных типа `Lero/Lojz/Lalt/Lt6f`; в `Locv.i0` — `Lero/Lxq7/Lchg/Lt67`; в `Larv.g` — `Lero/Lt6f`. Показаны типы/ветвления, **не** значения URL/строк и не то, какая ветка сработала на устройстве.
- Добавлена **исключительно OWN-ONLY** `NativeSourceInstanceFence`: отдельный pure Java контракт точной `Object ==` идентичности selected/owner/reader/loader/task/DataSpec, preprepare-once, поколений Next/Radio, Stop, Seek/reopen, монотонных часов и fail-closed. **К `NativeHookEntry` НЕ подключена, аудио не трогает.**
- **CI:** [ARM64 Linux JVM #42826864698 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826864698) (44 478 deterministic + 27 concurrency assertions; 4 800 запоздавших вызовов), [Lemb factories #42827236492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42827236492), [signed Lemb callers #42826778879 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42826778879), [Android native module #42827236060 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42827236060).
- **Android Yandex live source selected/predecoder доказательства нет; аудиоподмены нет.** ARM64 Linux — не Android runtime. Перед подключением нужны независимые trusted selected trackId+edition+generation + точно выбранный Lemb и actual decoder prepare в изолированной ARM Android среде. Test.50/HONOR/Windows/production не трогать.

## ПРЕДЫДУЩИЙ CI GREEN — точный Lero → Lwq7 task → Lmb4 DataSource.open/read/close (10.11.2026)

- **Проверенный SHA:** `f04745f7dcd4455996eadf56dc0be6c52a44c63f`; **замороженный откат:** `backup/android-signed-lero-lmb4-reader-case-ci-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-LERO-LMB4-EXECUTION-CHAIN-2026-11-10.md`. Signed original 5 APK/6 DEX/230533 bodies: `Lga4.c():Lha4` move-result **в том же basic block** записывается в `Lero.Lha4` и передаётся в `Lmb4.<init>` word1; конструктор кладёт его в точное поле `Lmb4:Lm48`; `Lmb4.a` читает тот же field-ref, cast `Lha4`, вызовы `b(La58)`×2/`read([BII)`/`close()`.
- В `Lero.t` **проверен actual DEX selector** и захват точного `Lero.this` в `Lwq7.<init>(I,Object)`. Mode **не** входит в 2 explicit packed-switch кейса `Lwq7.e` и выполняет **default fallthrough**, где `Lwq7` считывает то же captured field → `Lero.Lmb4` → `Lmb4.a`. У `Lero.t` есть `execute/get`, но это не runtime-аудио подтверждение.
- **CI SUCCESS:** [source read #42821377729](https://github.com/manufact-test/nomusic/actions/runs/42821377729), [selector/capture #42822722957](https://github.com/manufact-test/nomusic/actions/runs/42822722957), [exact source field #42823360505](https://github.com/manufact-test/nomusic/actions/runs/42823360505), [Android module #42823360398](https://github.com/manufact-test/nomusic/actions/runs/42823360398) 2/2.
- **Критическая граница:** точный выбранный `trackId+edition+generation` в живом ExoPlayer и `decoder PREPARE` всё ещё НЕ доказаны. Android replacement audio НЕ работает, runtime hooks/прошивки не тронуты. Следующий этап: отдельный пассивный ARM Android player/source witness. Не повторять x86 LSPatch; не трогать Test.50/HONOR/Windows/production.

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — URI-модель → Lcq7.i0 → Lga4/Lero/Lha4 → DataSource (10.11.2026)

- **Проверенный исходник:** `f327f5b9bcfee028e754f9a803f29ade347cb240`, **rollback:** `backup/android-signed-uri-locv-source-cfg-green-20261110`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-URI-TO-DATASOURCE-LIFECYCLE-EVIDENCE-2026-11-10.md`. В оригинальном подписанном six-DEX `Locv.i0` читает URI-подобные данные, `Lw4y.z` парсит scheme/host/path/query (значения не экспортированы); результат попадает в coroutine `Llky`, `Lfwm.M` возвращает `Ljgv`, который bounded CFG передаёт `Lcq7.i0` и `Lcq7.D`.
- У `Lcq7.i0` только 2 прямых вызывающих: `Lo4y.c` и `Locv.i0`. Результат — **обёртка**; реальный `Lga4` извлекается через `iget-object` с условным путём к `Lnro/Lero`. Предыдущий анализатор ошибочно сохранял taint обёртки при `iget-object`; ошибка в DEX 22c nibble-kill исправлена и протестирована.
- В том же signed DEX: `Lcq7.A` результат → точный primary `Le48`-slot `Lga4`; `Le48.a` результат `Lm48` → argument word 3 `Lha4.<init>`; `Lha4.f` вызывает `Lm48.b(La58)`, `Lha4.read` — `Lv38.read`. `Locv.t/remove` условно вызывают `Locv.i0`, но это **НЕ доказательство live decoder prepare**.
- **CI:** [source register #42819113120 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819113120), [actual i0 CFG #42819106641 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42819106641), [taint fix #42817633107 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42817633107), [Android module #42819113420 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42819113420).
- **ANDROID audio PASS — НЕТ.** Нельзя считать модель соответствующей активному `trackId/edition/generation` или выбранному pre-prepare DataSource. Контракты замены не подключались, HONOR/Test.50/Windows/API/production не трогались.

## ПРЕДЫДУЩИЙ ПРОВЕРЕННЫЙ КОД — obfuscated DataSource + два Le48-источника (10.11.2026)

- **CI GREEN SHA:** `6b5bfde53d81a29920f32a3c6b13b730b216e669`; **независимый откат:** `backup/android-signed-dual-source-dataspec-open-ci-green-20261110`.
- **Читать ПЕРВЫМ:** `docs/android/ANDROID-NATIVE-SIGNED-DATASPEC-OPEN-SOURCE-EVIDENCE-2026-11-10.md`. Установлен подписанный DEX DataSource-совместимый контракт Lm48(b(La58):J, getUri, close) + родитель Lv38(read([BII):I), 33 реализации; проверены реальные Lha4.open/read и Lz3f.a→Lm48.b(La58).
- Lga4.b/c используют secondary Le48, Lga4.d primary Le48; secondary в Lcq7.i0 = Lya4 → Lza4 (открытие/чтение выбрасывает исключение), **primary = Lcq7.A→Luiq** (ленивая фабрика Lm48). Оба источника передаются в Lha4, нельзя их путать. Общее соседство с ExoPlayer **не доказывает** текущий trackId/edition/generation и live decoder PREPARE.
- **CI:** [field2 #42813687276 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42813687276), [two slots #42814211492 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814211492), [inherited API #42814967628 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42814967628), [source/open #42815048696 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42815048696), [Android module #42815048701 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42815048701).
- **Нет Android audio PASS** и точной идентичности FileInfo→текущий экземпляр Lm48 перед prepare. Ничего в player/replacement не подключено; Test.50/HONOR/Windows/API/production не тронуты.

## ПРЕДЫДУЩАЯ CI GREEN ТОЧКА — оригинальный FileInfo → typed model → реальный Le48 field (10.11.2026)

- **Проверенный код:** `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`. **Бэкап:** `backup/android-signed-typed-dispatch-field-audit-ci-green-20261110` → ровно `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md` — реальные DEX данные от Lhee/Lged через Leed/Ldiv → Lygv.r → Ljgv → Lcq7/Lo4y/Larv; неоднозначный 16-way Le48 dispatch и точный writer/reader аудит двух разных Le48-полей класса Lga4.
- **CI SUCCESS:** [typed coroutines #42808158803](https://github.com/manufact-test/nomusic/actions/runs/42808158803), [Ldiv/Ljgv consumers #42808680756](https://github.com/manufact-test/nomusic/actions/runs/42808680756), [media candidates #42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855), [virtual dispatch #42809849405](https://github.com/manufact-test/nomusic/actions/runs/42809849405), [exact field writer #42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588), [Android module #42810750850](https://github.com/manufact-test/nomusic/actions/runs/42810750850) SUCCESS 2/2.
- **НЕ decoder proof:** найденная семишаговая близость к Lro7.y0 зависит от выбора одного из 16 виртуальных receiver и разных switch-веток. Фактически Lga4.c использует Le48 field-2, а конструктор инициализирует Lzcd в ДРУГОЙ field-1. Field-2 наблюдался с Lya4/Lkc6 и неизвестными writes, без подтверждённого current-track source. Android audio replacement по-прежнему НЕТ.

## Предыдущая подтверждённая точка

- **Точный проверенный код:** `8b7bc64f89249e5434da739851bececce2adb121` — [signed DEX CI #42806655214](https://github.com/manufact-test/nomusic/actions/runs/42806655214) SUCCESS, [Android module CI #42806655152](https://github.com/manufact-test/nomusic/actions/runs/42806655152) SUCCESS 2/2.
- **Rollback:** `backup/android-signed-register-cfg-ci-green-20261110` → `8b7bc64f89249e5434da739851bececce2adb121`.
- **Сначала изучать:** `docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md`. Выявлены Lxa7.<init>, Lged.a → Lhee.a и прямые coroutine callers; это may-flow, не Android decoder proof.

## Главное, читать по порядку

1. **Новый результат подписанного Android APK:** `docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md` — 6 DEX / 837 500 вызовов, прямой FileInfo caller `Lhee;->a`, model consumer `Lged;->a`, без ложного decoder proof, 2+2 прямых вызова MediaSession.
2. **Актуальный краткий статус + исторические ссылки:** `docs/android/NEXT-CHAT.md`. В этом накопительном документе старые «LATEST» и старые SHA — архив; верный кодовый SHA см. выше.
3. **Windows, реально работающий продукт:** `docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md` и `docs/windows/W57-OWNER-0247-REAL-AUDIO-SUCCESS-20261110.md`; код `windows-companion/w22/native-resource-adapter.mjs`. Windows `0.24.7` пользователь принял.
4. **Что из Windows уже аккуратно перенесено в Android:** `docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md` — строгий grant, Track ID, Next, Stop, поколения.
5. **Где находятся реально существующие кандидаты ExoPlayer:** `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md` — четыре обфусцированных класса и отрицательные результаты поиска.
6. **Старые исследования/отказы:** `docs/android/ANDROID-NATIVE-SIGNED-SOURCE-HOP-EVIDENCE-2026-11-10.md`, `docs/android/ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`; они нужны, чтобы не повторять x86/clone тупики, а НЕ как главная задача.

## GitHub, проверка, откат

- Репозиторий: https://github.com/manufact-test/nomusic
- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`; перед работой считать текущий HEAD, docs-коммит может быть новее кода.
- **Предыдущий проверенный код (shared-caller этап):** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- **[Подписанный APK статический CI #42804081064 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42804081064)**.
- **[Android Xposed read-only модуль CI #42804081053 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42804081053)**.
- Резервная ветка точно проверенного кода: `backup/android-signed-source-bridge-media-session-ci-green-20261110` → `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- До нового аудита: `backup/android-pre-real-signed-bridge-proximity-audit-20261110` → `0a1f035113fb826f88ebf827a46e5edc66635c7f`.
- Эталон владельца **Test.50** (реально проверен ref `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`): `backup/android-test50-exact-source-owner-accepted-20261106`; не изменять.

**Реальный статус:** Windows CELIKOM **да**, Android CELIKOM source substitution **нет**. Нужна действительная граница текущего decoder source; MediaSession — не она. Не выдавать исходный SDK/CI за реальный audio PASS, не переустанавливать Яндекс на основном телефоне.
