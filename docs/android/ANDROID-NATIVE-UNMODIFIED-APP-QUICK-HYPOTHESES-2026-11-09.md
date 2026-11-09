# CELIKOM Android — быстрые гипотезы без патча Яндекса (09.11.2026)

## Решение после короткого исследования

**Обязательная продуктовая цель:** треки играют через единственный родной проигрыватель Яндекс.Музыки. На HONOR пользователя остаётся установленный оригинальный `ru.yandex.music`, скачанные песни/аккаунт/Play Protect не трогаем.

**Результат быстрого цикла:** из проверенных платформенных интерфейсов не выявлен **подтверждённый** rootless-механизм подмены нативного `FileInfoDto → eed → decoder` в неизменённом стороннем APK. Это NO-GO для *нынешних гипотез*, но не математическое доказательство, что такого механизма не существует.

## Проверки

| Гипотеза | Проверенный факт | Вердикт для прозрачной подмены |
|---|---|---|
| MediaSession / MediaController | Внешние команды Play/Pause/Next, очередь и метаданные маршрутизируются в родной player | Не дают права заменить его source/decoder |
| MediaBrowserService / Intent | На точной подписанной #170gpr (5 split APK) объявления MediaBrowserService **2**, VIEW **9**, MEDIA_PLAY_FROM_SEARCH **1**. Это навигация/запуск воспроизведения, а не доказанный контракт на замену источника | Не выявлена нужная точка |
| Exported ContentProvider | 11 провайдеров, **3** явно exported=true, **7** false, **1** unspecified; **2** grantUriPermission=true. Сам exported не означает метод загрузить источник текущего трека | Подтверждённого source-input нет; дальнейшее исследование провайдеров допустимо только без чтения данных/токенов |
| VPN/proxy | VpnService видит маршрутизируемые пакеты; TLS content защищён, и обход доверия сертификатов не подходит продукту. VPN не меняет уже подготовленный MediaSource напрямую | Нет надёжного неизменённого приложения |
| Accessibility/UI Automation | Управление интерфейсом/жесты, не исходный DTO/декодер; ухудшает UX и совместимость | Не подходит |
| AudioPlaybackCapture / MediaProjection | Позволяет с разрешения копировать *выходной* звук при ограничениях, но не внедрять аудио в чужой decoder | Не подходит |
| Обычный отдельный CELIKOM APK | Android sandbox изолирует чужой UID/process и не даёт in-process hook без поддержки целевого приложения | Недостаточно |
| LSPatch/LibXposed | **PASS на настоящем HONOR**: собственный armv7 witness показал `Module hook armed=YES; onCreate intercepted=YES`. Требует, чтобы *целевой APK* был подготовлен патчером | **Подходит для патченной нативной копии**, не доказывает работу в неизменённой официальной |
| Конкурент ChromaSync-Mobile | Официальный GitHub README: no-root инсталляция требует совместимого исходного Яндекс APK + патчер + модуль; root-вариант LSPosed. Публичный репозиторий содержит только README (не исходный код модуля) | Подтверждает выбранный путь патченного native; «скопировать структуру» можно как архитектуру, не как чужой код |

## Фактический CI

- <https://github.com/manufact-test/nomusic/actions/runs/42649327835> — SUCCESS, отдельный read-only `audit_unmodified_yandex_ipc.py` и синтетические тесты.
- Подписанный издателем #170gpr, versionCode 24026531: **142 activities**, **7 aliases**, **35 services**, **30 receivers**, **11 providers**. MediaBrowserService 2; никаких вызовов чужих API, журналов личных данных, установок/патчей или публикации APK.
- <https://github.com/manufact-test/nomusic/actions/runs/42637284714> — исходный clone feasibility SUCCESS: **9 провайдеров** со старым package-bound authority, **2 точные** package string и **35** содержащих package string в DEX. Надёжная параллельная native-копия пока не доказана.
- <https://github.com/manufact-test/nomusic/actions/runs/42643802887> — own ARM hook witness собран, а владелец прислал оба `YES` на HONOR; это реальный hook PASS, но НЕ native Yandex PASS.

## Принятое направление

1. **Не расходовать время на новые варианты VPN, второй проигрыватель, WebView, accessibility hacks, перехват системного аудио.** Они не соответствуют цели.
2. Принять **rootless in-process patched native Yandex** как рабочую гипотезу следующего этапа, по принципу конкурента. Уже есть version-locked read-only hook на `sw7.y0/z0`. Развивать по этапам: runtime hook в совместимом *отдельном разрешённом стенде* → связка `track+edition → FileInfoDto → eed` до prepare → корректный единственный native source с fallback, seek/pause/next.
3. **Не копировать исходники конкурента**: публично виден только README. Не обходить подписи, Play Protect или авторизацию Яндекса; не брать логин/пароль/OAuth-токены.
4. **На основном HONOR не устанавливать переподписанный `ru.yandex.music`**: пакет уже установлен с другой подписью. Для параллельного пути нужно отдельно доказать безопасный новый packageId, все split APK, provider authorities, DEX self-identity и обычную авторизацию; или получить отдельное тестовое устройство. Пока такого доказательства нет, никаких действий на HONOR.
5. Не публиковать перепакованный Яндекс и не менять Test.50, production, расширение, сервер, DB, музыку. Сохранить текущий PASS owner witness как контрольный.

## Почему остановили поиск здесь

Пользователь просил потратить **немного времени** на быстрые гипотезы. Этот цикл дал проверку внешних контрактов и обоснованный приоритет архитектуры. Дальнейшее глубокое исследование неподтверждённых обходов без устройства/доказанной совместимости превратится в бесконечную полировку, а не в продукт.

**Итог:** unmodified Google Play Yandex + in-process audio swap без root — пока **не доказан**. Патченный нативный Яндекс — выбранная исходная архитектура для следующего этапа, с сохранением существующей официальной установки до отдельного разрешения.

## Проверенные публичные источники

- ChromaSync-Mobile: https://github.com/Desai0/ChromaSync-Mobile
- Android App Sandbox: https://source.android.com/docs/security/app-sandbox
- MediaSession: https://developer.android.com/media/media3/session/control-playback
- MediaBrowserService: https://developer.android.com/reference/android/service/media/MediaBrowserService
- AudioPlaybackCapture: https://developer.android.com/media/platform/av-capture
- VPN: https://developer.android.com/develop/connectivity/vpn
- Android network security config: https://developer.android.com/privacy-and-security/security-config
