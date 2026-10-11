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

Threat boundary: фиксированный HTTPS origin, no redirects, bounded 64 KiB JSON, timeouts, токены в native RAM, backups disabled; нет стороннего content/WebView bridge, DRM bypass/stream extraction/system interception. Debug signing не production signing; plain APK не публикуется открыто. CI artifact — CMS AES-256-GCM envelope к временному recipient certificate; private key только вне git/CI. Это не ключ подписи приложения. Реальные accounts/sessions/grants/incidents/media/catalog/reward policy/ledger/allocations автоматические проверки не меняют.

Validation 11.10.2026: Android workflow 38168453192 PASS (code 35759e880b64be8da5659e8a111bda718511e701): unit, lintDebug, assembleDebug и 1 native instrumentation test на API 35/Android 15. Seek/position tolerance <250ms проверена в эмуляторе, не на физическом устройстве. General CI 38168457150 PASS. Первоначальный SDK setup failure исправлен explicit packages; не относится к playback. Локальный repository lint расширен на Kotlin/XML/properties/Python/cert и PASS.

Encrypted artifact 11713145609 получен, CMS AEAD успешно расшифрован вне CI. APK ZIP integrity PASS, 10,824,476 bytes, SHA256 dc54faa3427d6bf5fbc17d9638116f5ffe07bfd28ace1083de4abdfe3405ba52. Закрытая диагностическая поставка владельцу, не публичная Beta/официальный release. Physical device/real login/service playback/focus/process kill/network не объявлены выполненными.
