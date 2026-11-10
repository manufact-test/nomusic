# CELIKOM Android Native: истинный GO/NO-GO для штатного Яндекса (10.11.2026)

**Решение: NO-GO к выпускаемому работающему APK при текущих ограничениях.** Не путать с утверждением, что интеграция навсегда невозможна: нужна *другая разрешённая поверхность интеграции или изолированный in-process host*. Не переиздавать очередной hooklab, MediaSession-пробник или синтетическую модель как рабочую подмену.

## Неприкосновенные продуктовые требования

- Работать в официальном установленном Яндекс.Музыка без пересоздания UI.
- Один родной аудиоплеер и его собственные pause/seek/Next/радио/кроссфейд.
- Только разрешённые альтернативные версии с подтверждёнными правами и entitlement.
- Без root, без отключения Play Protect, без перехвата OAuth/DRM/ключей, без подмены подписи издателя, без изменения/удаления установленного Яндекса на основном HONOR.
- Эталон **Android Test.50** — отдельная архитектура аудиосессии/эквалайзера, **не трогать, не объединять**.

## Что реально проверено в НОВОЙ NATIVE ветке

**Источник:** издательски подписанный оригинал Яндекс 2026.10.3 #170gpr, 5 APK, 6 DEX, 230 533 method bodies.

- Цепь `FileInfoDto → sw7.y0/z0 → eed` структурно подтверждена, но до выбранного активного декодера тождество не доказано.
- В оригинальном DEX есть несколько фабрик и **восемь реализаций Lemb**; выбранный Lero и выбранный активный ExoPlayer на runtime остаются неизвестны.
- **Исправлен реальный пропуск observer:** от `Lkvs.A` отслеживалась лишь factory-returned ветвь, но `Locv.i0` может напрямую строить `Lero`, минуя эту фабрику. Добавлено точное наблюдение за *обоими* конструкторами `Lero(wzi,ga4)` и `Lero(wzi,ga4,ref)` после возврата оригинала, по reference identity. Конструктор vs фабрика не смешиваются и не считаются доказательством *selected* source. Десять тысяч синтетических source→reader и thread-race циклов, отдельная сборка модуля.
- `Lero → Lmb4 → Lha4(open/read/close)` точные методы подписанного APK подтверждены. На host по-прежнему **нет запущенного настоящего Яндекса с разрешённым хуком**, нет факта исполнения этих конкретных callbacks в реальном воспроизведении и нет связи с `trackId + edition + generation`.
- **[CI exact signed constructor/reader audit #42866551757 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42866551757)**: реальная пара `Lero` конструкторов 1+1, 7/7 точных методов, 1/1 поле `Lero→Lmb4`; **[CI native Xposed module/test #42866551803 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42866551803)**.
- Проверенный кодовой SHA `b3752aad5d2b34d1816d323baeb41453ff81c3ba`; backup `backup/android-native-dual-constructor-source-observer-signed-ci-green-20261110`. Предшествующий green native `backup/android-native-lero-lmb4-ha4-signed-readonly-chain-ci-green-20261110` @ `6146109dd77352dbc73563c26dcaf1dfd6ff6c38`.

## Почему нельзя честно выдать working APK с этим кодом

1. **Android sandbox.** Обычное внешнее приложение не может читать private source objects и менять Java/NDK DataSource внутри чужого подписанного APK. См. https://developer.android.com/privacy-and-security/security-tips .
2. **MediaSession ≠ исходный DataSource.** Android media controller отправляет разрешённые команды в MediaSession приложения-владельца. Обработчик `MediaSession.Callback.onConnect` может ограничить untrusted клиентов только чтением; даже право на `COMMAND_CHANGE_MEDIA_ITEMS` не даёт прямого доступа к `FileInfo`/decoder. Из официальной документации: https://developer.android.com/reference/androidx/media3/session/MediaSession.Callback и https://developer.android.com/media/media3/session/control-playback .
3. **Play Protect уже дал настоящий NO-GO.** Native Gate 0.1 — *не* source-swap и не проверка звучания; блокировка при sideload установке на HONOR без кнопки обхода. В нём был объявлен NotificationListenerService (широкое permission surface) плюс отладочная подпись. Google указывает, что sideload apps с разрешением `NOTIFICATION_LISTENER` могут блокироваться автоматически. Это **правдоподобное совпадение**, но точный тип предупреждения у пользователя не зафиксирован, поэтому не утверждать доказанной причины. Источник: https://developers.google.com/android/play-protect/warning-dev-guidance . Сборка и выдача пробника отключены, файл перемещён в Library `REJECTED_DO_NOT_INSTALL`.
4. В CI нет разрешённого ARM Android *in-process* host для реального Yandex decoder; ранее x86 patched Yandex падал до модуля, ARM64 Linux JVM — не Android; main HONOR/Play Protect не менять и не трогать. **Синтетический PASS ≠ installed/runtime/acoustic PASS.**

## Следующая настоящая работа, только когда изменится условие допуска

Единственный реальный прорыв — подтверждённый publisher-authorized источник изменения **до decoder prepare** в *том же* активном плеере. Это может быть официально поддерживаемое приложение/плагин от владельца проигрывателя, отдельно разрешённый тестовый in-process host или другой законный механизм, документированно позволяющий подставить чужую разрешённую дорожку в действующий MediaSource. Без него обычный CELIKOM APK не выполнит требование одного Yandex player, сколько бы DEX и тестов мы ни написали.

Когда bridge существует, идти строго по этапам: live `selected current source object` → same `trackId + edition + generation` → verified authorized alternative license/entitlement → same original decoder before prepare → controlled fallback; затем отдельное тестовое Android устройство с Play Protect и ручная проверка паузы/Seek/Next/радио/BT.

**Что НЕ делать:** повторять «модули за 5 минут», пересобирать Play-Protect-blocked Gate с замаскированными permissions, отключать защиту Google, root/hide/DRM обход, смешивать Test.50 с native, присылать несоответствующие APK на HONOR, выдавать source-code static findings за играющую новую версию.

**Статус для передачи:** Native source observer технически улучшен, CICD чистый, frozen backups есть. **Работающая CELIKOM Native Android replacement version НЕ готова.** Текущий architecture constraint не разрешён инструментами/SDK; не объявлять задачу закрытой или «ждём проверку пользователя» без реально устанавливаемого и работающего native client.
