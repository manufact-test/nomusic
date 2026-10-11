# Этап 16 — Android PoC, 11.10.2026

Владелец принял работу расширения/промокодов и разрешил следующий этап. Android playback/Beta ещё не приняты. Этап 15 исключён; провайдер оплаты не блокирует независимую работу. Chrome 0.4.28 остаётся единым клиентом.

| Surface | Основание | Решение сейчас |
| --- | --- | --- |
| Собственные MediaPlayer CELIKOM | Собственные WAV, известные fixture IDs/state, управление обоими потоками | Допустимый инженерный harness; не музыкальная интеграция |
| Яндекс в controlled WebView | Нет доказательства поддержки mobile playback/login/exact state и допустимости конкретной интеграции | Не подключён, не confirmed |
| Mobile browser с extensions | Нет проверенного browser/version/service surface | Не supported surface |
| Native Яндекс | AudioPlaybackCapture копирует разрешённый звук с согласием; не гарантирует Track ID/mute/sync исходного плеера | Не используется для подмены |

Первичные официальные источники просмотрены 11.10.2026:

- https://developer.android.com/media/platform/av-capture — согласие, RECORD_AUDIO и политика исходного плеера ограничивают захват; копирование не доказывает exact state/control.
- https://developer.android.com/media/optimize/audio-focus — focus является lifecycle аудио, не способом управления чужим плеером.
- https://developer.android.com/develop/ui/views/layout/webapps/load-local-content — собственный WebView допустим для своих ресурсов; это не доказательство интеграции с Яндексом.
- https://developer.android.com/reference/android/media/session/MediaSessionManager — чтение сторонних sessions требует специальных permissions/notification access; наличие controller само не доказывает точный Track ID или управление громкостью только одного чужого потока.
- https://yandex.ru/legal/music_mobile_agreement/ru/ — native client не модифицируется/декомпилируется; допустимость будущего service integration должна быть установлена отдельно, без вывода разрешения из возможности Android API.
- https://developer.android.com/build/releases/about-agp и https://kotlinlang.org/docs/whatsnew2220.html — закреплённые версии сборки, без dynamic dependencies.

В android/spike: Kotlin/Compose shell, original/alternate native MediaPlayer, exact fixture track/state, seek/play/pause, manual Original, fail-open и lifecycle/focus suspend; общий HTTPS account probe. Fixture IDs намеренно отличаются от настоящего каталога. Вход не запускает trial, entitlement читается общим сервисом. Platform/app_version передаются диагностическими headers; backend пока их не хранит, dev registration/feature flag не заявлены готовыми.

| Проверка | Граница | Статус |
| --- | --- | --- |
| Unit policy | Original не отменяется resume/error, suspend без autorun, unknown Track ID, stopped restart | PASS 38168453192 |
| Android lint/build | Compose target 36/min 26; без открытого APK artifact | PASS 38168453192 |
| Native emulator | Реальные MediaPlayer playheads/seek/pause/resume, Original/fail-open/Next/suspend | PASS 38168453192 |
| Physical device | Услышанный результат, фон/возврат и реальная потеря focus | Не выполнено |
| Network loss | Только injected failure собственного replacement, remote playback отсутствует | Не считать проверкой мобильной сети |
| Process death | Unit initial state; реальный kill/restart не проверен | Частично |
| Яндекс mobile | Конкретный допустимый service surface и reproducible demo | Blocker |

Текущий decision: **NO-GO включению Яндекс playback в Android Beta**, поскольку конкретный механизм не доказан. Это отсутствие доказательства, не утверждение о невозможности любой Android интеграции. Собственный demo не закрывает service PoC; companion-only scope не принимается за владельца. Этап 16 частичный, 17 не начат.

Threat boundary: фиксированный HTTPS origin, no redirects, bounded 64 KiB JSON, timeouts, токены в native RAM, backups disabled; нет credential bridge к сторонней странице, DRM bypass/stream extraction/system interception. Debug signing не production signing; plain APK не публикуется открыто. CI artifact — CMS AES-256-GCM envelope к временному recipient certificate; private key только вне git/CI. Это не ключ подписи приложения. Реальные accounts/sessions/grants/incidents/media/catalog/reward policy/ledger/allocations автоматические проверки не меняют.

Validation 11.10.2026: Android workflow 38168453192 PASS (code 35759e880b64be8da5659e8a111bda718511e701): unit, lintDebug, assembleDebug и 1 native instrumentation test на API 35/Android 15. Seek/position tolerance <250ms проверена в эмуляторе, не на физическом устройстве. General CI 38168457150 PASS. Первоначальный SDK setup failure исправлен explicit packages; не относится к playback. Локальный repository lint расширен на Kotlin/XML/properties/Python/cert и PASS.

Encrypted artifact 11713145609 получен, CMS AEAD успешно расшифрован вне CI. APK ZIP integrity PASS, 10,824,476 bytes, SHA256 dc54faa3427d6bf5fbc17d9638116f5ffe07bfd28ace1083de4abdfe3405ba52. Закрытая диагностическая поставка владельцу, не публичная Beta/официальный release. Physical device/real login/service playback/focus/process kill/network не объявлены выполненными.

## Проверка реального сайта, 11.10.2026 23:05 МСК

Владелец просит следующую содержательную готовую версию с реальной подменой, без установки промежуточных diagnostic APK. Новые диагностические APK ему не доставлять; собственные fixtures не считать закрытием этапа 16.

Commit `8bab30bbb6537880541cbdf3d0cff51208bab53d`: Android workflow 38170400164 PASS, общий CI 38170404247 PASS. Unit/lint/build и два instrumented tests завершились. Второй тест загружает настоящий `https://music.yandex.ru/track/144530503` в Android System WebView 124.0.6367.219, default mobile UA, Android API35. В страницу на document start внедрён общий extension core/Yandex adapter; диагностика ограничена фиксированным HTTPS origin, без stream extraction, чтения cookies/credentials или системного перехвата. Чужие origin не получают adapter; SSL errors не обходятся. Проверка не запускает trial и не меняет реальный аккаунт.

Сайт загрузился, но на снимке показал «Yandex Music is currently not available in your region» и кнопку Log in. Snapshot: adapter=true, trackId=null, confidence=0, mediaPresent=false, durationMs=0, catalogSize=0; playback_confirmed=false. Play control не найден и не нажат. Следовательно, PASS означает исправную сборку/диагностический harness, **не** воспроизведение/подмену Яндекса. Региональное ограничение наблюдалось на CI runner; это не доказательство невозможности WebView на устройстве в поддерживаемом регионе. Географический блок не обходился.

Снимок, JSON и APK опубликованы только в CMS AES-256-GCM encrypted artifact (retention 1 день); ключ остаётся вне GitHub. Публичный лог содержит лишь ограниченный snapshot. Незашифрованный снимок проверен внутренне, владельцу новый APK не передан.

Официальная документация Яндекс Браузера Android описывает extensions Chrome/Opera и developer load unpacked manifest.json: https://yandex.com/support/browser-mobile-android-phone/ru/personal-settings/extensions . Это отдельный кандидат для проверки, а не подтверждение поддержки текущего MV3 extension или воспроизведения конкретной версии браузера. Не подменяет согласованный standalone Android scope.

Для следующего доказательства нужен легитимный доступ к сервису из поддерживаемого региона и, если сервис потребует, разрешённая пользовательская сессия Яндекса. Затем проверяются точный Track ID/позиция, управление только исходным потоком, fail-open/Original, синхронизация, lifecycle и entitlement. На текущем runner это доказательство недоступно. Этап 16 остаётся частичным, 17 не начат. Нативный клиент Яндекса не перехватывается. Backend/extension/live данные не изменены; PR #6 не сливался.
