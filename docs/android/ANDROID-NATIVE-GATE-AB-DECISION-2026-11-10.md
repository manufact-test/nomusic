# CELIKOM Android — завершённые Gate A/B и переход к собственному плееру (10.11.2026)

## Итог: A = NO-GO (по доступным публичным интерфейсам), B = NO-GO (нет лицензированного встроенного Яндекс-каталога)

Это **ограниченный технический вывод по проверенным официальным интерфейсам**, не доказательство, что никто в мире не способен сделать модифицированный проигрыватель. Следующий разработчик НЕ должен перезапускать тот же DEX hooklab, Native Gate 0.1 или эмулятор в надежде получить недоказанный доступ. Работа продолжается только по Gate C — первостороннему CELIKOM player.

### Gate A: официальный неизменённый Яндекс + соседний Android CELIKOM

1. [Android app fundamentals](https://developer.android.com/guide/components/fundamentals): разные Android package UID/process sandbox. Без документированного взаимодействия с самим publisher чужие внутренние объекты, URL resolver и выбранный decoder DataSource недоступны.
2. [Media3 Session.Callback](https://developer.android.com/reference/androidx/media3/session/MediaSession.Callback) и [control playback](https://developer.android.com/media/media3/session/control-playback): MediaController выполняет выдаваемые owner player/session команды (play/pause/seek/playlist), не получает право вмешиваться в supplier or DataSource/ExoPlayer source factory. Untrusted controllers могут иметь только read access. Windows `reloadEntity` — внутренний JS метод десктопного плеера; нет публичного Android эквивалента, доступного другой обычной APK.
3. [Android audio playback capture](https://developer.android.com/media/platform/av-capture) требует явного MediaProjection capture consent, записи PCM и разрешённой audio capture policy publisher. Это НЕ смена аудиоисточника внутри чужого decoder, не подходит one-player source replacement.
4. Ранее [native-source signed evidence](ANDROID-NATIVE-T-TRANSACTION-OCV-LERO-OWNER-20261110.md) подтверждает точные сигнатуры, factory and reader calls, но ни одно live current player/track+edition+generation → before decoder prepare. Прохождение synthetic CI не компенсирует отсутствие официального IPC. Google Play Protect уже заблокировал Native Gate на HONOR — не повторять.

**Verdict:** `NATIVE_ORIGINAL_NO_GO_PUBLIC_SURFACE`. Не создавать ещё один DEX/constructor observer, unsigned APK или Chrome/WebView mirror как обходной «native proof». Возобновить только при **НОВОМ проверяемом интерфейсе/разрешении**.

### Gate B: встроенный полный каталог Яндекс.Музыки

1. [Лицензионное соглашение Яндекс Музыки](https://yandex.ru/legal/music_mobile_agreement/ru/): сервис, программа и база данных имеют отдельных правообладателей; коммерческое изменение, перепаковка и распространение в изменённом виде требуют разрешения. Собственный CELIKOM не может копировать установленный Яндекс APK или выпускать «его внутри» как самостоятельный коммерческий продукт без соответствующих прав.
2. [Условия использования сервиса](https://yandex.ru/legal/music_termsofuse/ru) ограничивают воспроизведение/использование материалов и плеера предоставленными способами; наличие подписки пользователя на Яндекс не предоставляет CELIKOM права на воспроизведение всего каталога внутри собственного клиента.
3. Публичная [Partner API](https://yandex.com/support/music-artists/ru/performers-and-copyright-holders/partners-api) — Bandlink/smartlink для артистов, **не** API полноценного стороннего воспроизведения Яндекс.Музыки. [Открытая Python библиотека](https://ym.marshal.dev/) прямо обозначает себя **неофициальной**; в коммерческий клиент её приватные методы не переносить. Публичного лицензированного full-catalog third-party Android playback SDK в этом целевом проходе **не найдено**.
4. [Yandex JS audio player](https://yandex.ru/dev/jsapi/) — универсальное воспроизведение предоставленных пользователем аудиофайлов, **не лицензированный доступ к каталогу Яндекса**.

**Verdict:** `CATALOG_LICENSE_NOT_FOUND`. Нельзя честно обещать потребителям полную Яндекс.Библиотеку в CELIKOM. Можно отдельно открывать оригинальную Яндекс.Музыку стандартным Android intent/browser, но это не даёт seamless replacement.

## Gate C: делаем сейчас, не архивная клонированная сборка Яндекса

У CELIKOM уже есть **настоящий разрешённый собственный контент** и действующие API:
- `GET /api/v1/replacement-catalog`: по коду `server/src/Application/ReplacementCatalogueService.php` отвечает metadata-only schema 1, source `celikom_owner_catalog_snapshot`, complete=true, до 5000 доступных approved track ids, title, artist, album, duration, replacement_available. Готовый `android/native-companion/addon/.../LiveCatalogueStore.java` проверяет подпись контракта/полноту.
- `GET /api/v1/resolve?service=yandex&track_id=<id>` только для аутентифицированного аккаунта CELIKOM и серверного entitlement, возвращает кратковременную подписанную ссылку `/api/v1/audio/<replacement_id>?token=...&expires=...&sid=...`. `AudioController` валидирует token и `AudioAccessService` для sid и поток HTTP Range. Каталог metadata не является фактом аудиодоступа.
- `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/entitlement`, `POST /api/v1/auth/activate`: существующий сервер authoritative trial/subscription. Любая неясная/просроченная серверная проверка ⇒ stop & clear player, без offline bypass.

Именно на этих endpoints создаём **отдельное first-party CELIKOM Android приложение**: своя идентичность, собственный Media3 ExoPlayer + MediaSessionService, защищённая сессия, каталог доступных альтернатив, один source clock для pause/seek/Next, background/Bluetooth, 5-секундная entitlement revalidation, fail closed. Это **не** замена полного каталога Яндекса; пользовательский UX надо позиционировать честно. Публичный релиз невозможен без обязательной проверки коммерческих прав на музыку, полной настройки подписки, аппаратной QA, Play Protect и release signing.

**Решение после Gate A/B:** native hooklab **заморозить**; строить только `experiment/android-owned-player-delivery-20261110`. Windows, extension, Android Test.50, original Yandex/HONOR, production/API/DB не менять. Не импортировать proprietary Yandex layout/strings/assets/код.
