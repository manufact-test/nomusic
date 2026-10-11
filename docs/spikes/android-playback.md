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

## Разрешение владельца и содержательный PoC 0.2.0

11.10.2026 23:25 МСК владелец разрешил продолжить реализацию при региональном блокере CI и проверить подмену лично на телефоне с доступным регионом. Это разрешение на проверку содержательной версии с реальным механизмом, а не признание предыдущего fixture APK готовым или тестов выполненными.

Теперь в приложении есть официальный сайт Яндекса внутри Android WebView и общий extension core/Yandex adapter/OriginalAudioGuard на document start. Native MediaPlayer получает только валидированный подписанный URL альтернативы из общего CELIKOM API. Оригинальная музыка не извлекается/не записывается. Нет системного перехвата или модификации native Яндекса; сторонние auth pages не получают адаптер/credentials bridge. Нативный мост ограничен main frame и exact HTTPS origin и может лишь сообщить освобождение конкретного audio lease.

Последовательность: точный track/media/catalog duration → общие config/activate/entitlement/resolve → prepare/seek/start альтернативы с нулевой громкостью → повторная проверка master binding → guard оригинала → громкость альтернативы по актуальному намерению пользователя. Poll 250 мс и page watchdog 1.5 с; guard release на pause/seek/track/source change/hidden/dead heartbeat. Пропавший polling, ошибка audio/network/access, законченный signed URL и stale generations возвращают оригинал. Explicit Original/logout/background не возобновляют подмену сами. Пауза/перемотка/новый точный трек могут продолжить включённый режим только после повторной проверки. Доступ и public config перепроверяются во время playback; объявленный incident скрывает музыкальные кнопки и показывает русское пояснение о заморозке. Network error не объявляет incident.

Native account: стабильный installation ID, AES-GCM Android Keystore сохранение сессии, общий login/register/verify-email/request-reset/reset-password/refresh/logout, entitlement и promo redeem. Trial начинает только явное включение подмены на воспроизводимом известном треке; серверный activate идемпотентен. Lifetime promo и reward ledger остаются серверными; новых реальных grants/migrations/deployments нет. Время интерфейса Europe/Moscow. Backend platform/version headers пока не классифицируют устройство отдельно.

Технические тесты включают общий JS guard с owned media double и production native playback controller с настоящими owned MediaPlayer и isolated API/surface double: sync/pause/access revoke/stale resolve/unknown track. Это не подмена реального Яндекса; её проверит владелец. Отдельный real-site probe по-прежнему видит региональный экран на CI runner.

0.2.0 остаётся private Stage16 PoC, не полной Beta17. Физические playback/focus/routes/background/process restart, подтверждение конкретного service surface, production signing и Android перенос upload/suggest/reports/benefits/devices/analytics ещё не приняты. Android foreground background playback ещё не реализован: текущий PoC останавливает подмену при уходе в фон. После успешного owner service proof можно продолжить 17 без Alpha15 и без платёжного провайдера. Публичная выдача клиентам закрыта до приватизации18; PR6 не сливать.

### Итог технической проверки 0.2.0

Исходный Android код `e65de5a0d28be59b6fd76c546c269dfddcbcfab0`; Android workflow38173802054 PASS, job114571794221, общий CI38173806601 PASS. JS guard3/3, unit7/7, lint/build и API35 instrumented6/6 (owned fixture players, signed grant validation/Moscow lifetime display, production playback controller, native account UI, encrypted session recreation/tamper and real-site probe harness) завершились успешно. Native UI проверен визуально: тёмная палитра CELIKOM, зелёный акцент, читаемые system bars; screenshots только encrypted/internal.

APK `CELIKOM-Android-0.2.0.apk`:10968664 bytes, SHA256 `4aa2e6510d3935f2ac1994d47a8bd5f4b8d098e3d5435c36dc2edd2c0b209585`; сохранён для закрытой передачи владельцу. Encrypted-only CI artifact11714619304, retention1d; публичного APK нет. Это debug PoC, не production signing. Реальный playback остаётся `playback_confirmed=false`: screenshot реального сайта снова показывает региональный gate, snapshot без track/media. Native harness PASS не выдаётся за service PASS. [Личная проверка](ANDROID-OWNER-CHECK-2026-10-11.md) — следующий шаг владельца, разрешённый им23:25МСК.
