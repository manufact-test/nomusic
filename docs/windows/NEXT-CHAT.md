**W32: разобрались почему пользователь не видел изменений: последний TXT 2.txt AppVersion=0.24.2.0 (old W28 CodeBaseline); W31 audio probe shipped 0.24.3. Кнопка «Обновить модуль» в старом CELIKOM не обновляет саму программу. W32 0.24.4 в разработке: постоянный footer реального AppVersion и настоящей ASAR версии/хеш-сопоставления native renderer, кнопка «Обновить CELIKOM из ZIP или EXE», in-place Inno silent same AppId, отбор только более новой версии, одноразовый ticket и восстановление/установка native модуля после успешной смены бинарника. Backup backup/windows-w32-before-one-click-updater-20261109 SHA 837f9984... W32 docs docs/windows/W32-OWNER-EASY-UPDATE-20261109.md. CI and owner audio test must be verified separately. Владельцу с 0.24.2 нужна ОДИН раз новая установка 0.24.4 поверх (без удаления), затем все будущие обновления через новую кнопку внутри приложения.

**W31 0.24.3 диагностический установщик готов, CI 3/3 SUCCESS.** Functional SHA 5a1e1c8997bc71781fbc9d457e040b18b0d1539d; [W20 installer CI 42649304206](https://github.com/manufact-test/nomusic/actions/runs/42649304206), [one ZIP with EXE artifact 13689337441](https://github.com/manufact-test/nomusic/actions/runs/42649304206/artifacts/13689337441), [W23 genuine Yandex CI 42649304284](https://github.com/manufact-test/nomusic/actions/runs/42649304284), [preview 42649304248](https://github.com/manufact-test/nomusic/actions/runs/42649304248), all success. User owner 0.24.2 FAIL after W30 live CORS, audio probe 0.24.3 from real renderer checks only 32 byte Range first 4 grants; no player changes. Send one installer/clean install, export TXT, inspect AUDIO_PROBE_HTTP_*, MIME_*, BYTES_* and CSP. Not proof audio fixed. Independent backup backup/windows-w31-pre-browser-http-probe-20261109. Full doc docs/windows/W31-OWNER-BROWSER-AUDIO-PROBE-20261109.md.

W31 owner audio FAIL after live W30 native CORS: actual owner 0.24.2 TXT (2026-11-09 15:46) still has RESOLVE_APPROVED / SOURCE_MAPPED / MEDIA_HTTP_UNVERIFIED and immediate Yandex pause; normal songs fine. W31 0.24.3 adds browser-context 32-byte signed-audio fetch probe (CSP/CORS/HTTP MIME/first bytes) from native Yandex with no secrets, no player modifications; see docs/windows/W31-OWNER-BROWSER-AUDIO-PROBE-20261109.md. Backup backup/windows-w31-pre-browser-http-probe-20261109 at 71702b89... Existing live backend W30 CORS verified. **CI AND AUDIO STILL REQUIRE VERIFICATION; do not claim playback fixed.**

**W30 финальный статус сервера:** live PHP/HTTPS CORS исправлен и независимо проверен CI https://github.com/manufact-test/nomusic/actions/runs/42647185895 SUCCESS: opaque:null 204/ACAO null, native 204/native, browser 204/browser, health200, auth API not broadened. GET/HEAD без токена 403 ожидаемо. Исходники перенесены также в backend feature/api-range HEAD 7e648eacaeb50cc371842590ed7a30284e440d2a (backup backup/api-range-pre-w30-desktop-audio-cors-20261109). No further install, owner audio still UNVERIFIED. 

**W30 private Hostinger Windows-audio CORS live HOTFIX, 2026-11-09 — server HTTPS PASS, audible owner test UNVERIFIED.** Owner TXT 0.24.2 confirmed normal songs RESOLVE_MISS/SOURCE_ORIGINAL play and approved RESOLVE_APPROVED/SOURCE_MAPPED stop, media HTTP status unobservable. Live backend verified missing native audio CORS: opaque/null and musicapplication://desktop OPTIONS 404, browser 204. Server code restricted new origins to numeric signed audio GET/HEAD/OPTIONS; auth/admin remain closed. One-file clone/snapshot/rollback deployment run https://github.com/manufact-test/nomusic/actions/runs/42646675471 SUCCESS. First run 42645545587 auto-rolled back due LiteSpeed stale cache. Second deploy used ephemeral cache invalidation; live HTTPS audio origin:null 204 ACAO:null, browser 204, health200, auth:null no CORS. Old release backed up, no DB/audio edits, Windows binary remains 0.24.2 and does NOT need reinstall. Owner next test: Stop/Start CELIKOM, Yandex restarted if cached, approved + ordinary track Play/Pause/Seek/Next. Do not claim audible fix before owner reports success. Backup code backup/windows-w30-before-owner-audio-cors-diagnosis-20261109. Full docs docs/windows/W30-OWNER-AUDIO-CORS-20261109.md. Future feature/api-range full deploy must preserve new CORS patch.

**W29 код bceb51b51f8c32da51c0f5cf98ec39679f166173 — CI SUCCESS 4/4 (2026-11-09).** Реальный owner 0.24.1 TXT обнаружил 3 синтетических native file-info ответа до прихода оригинального результата. В 0.24.2 синтетические ответы удалены, оригинальный формат Yandex обязателен, batch не генерирует недостающие треки; кнопки диагностики и открытия Яндекса больше не обрезаны. W22 #42638433704, W23 #42638433590, W20 #42638433588, Companion Preview #42638433646 — SUCCESS. Установщик один, ZIP artifact #13683048267: https://github.com/manufact-test/nomusic/actions/runs/42638433588/artifacts/13683048267. **Реальное аудио на учётной записи владельца всё ещё НЕ ПРОВЕРЕНО.** Backup `backup/windows-w29-before-owner-audio-fix-20261109`; полная передача `docs/windows/W29-OWNER-NATIVE-ENVELOPE-20261109.md`.

**W29 — владелец прислал настоящий TXT (0.24.1) 2026-11-09.** Подтверждено: модуль ACTIVE, доступен подписанный источник для четырёх track ID, Яндекс отдаёт getFileInfo, но три раза наш код отправил SOURCE_SYNTHETIC_RESPONSE после 130 ms и лишь затем получил штатный ответ NATIVE_FILEINFO_OK. На уровне HTTP и реального звука подтверждений нет; ранее владелец сообщал о мгновенной паузе. W29 0.24.2 устраняет искусственные ответы single/batch; меняет источник только в существующих нативных метаданных, иначе возвращает оригинал; не маскирует ошибки; не придумывает записи очереди. Диагностика теперь отмечает NATIVE_FILEINFO_WAIT. Исправлен обрезанный текст кнопок Яндекса и диагностики. Backup: `backup/windows-w29-before-owner-audio-fix-20261109` at `7c1858e`. **CI/прослушивание пока не подтверждены; не заявлять исправленную паузу.** Подробности `docs/windows/W29-OWNER-NATIVE-ENVELOPE-20261109.md`.

**W28 проверено (2026-11-09):** функциональный SHA `4418f4fa190d247694696558b8016cd7d7e2cc8a` (CELIKOM 0.24.1); [Windows installer CI 42634928360](https://github.com/manufact-test/nomusic/actions/runs/42634928360) — SUCCESS, [internal installer artifact 13681259210](https://github.com/manufact-test/nomusic/actions/runs/42634928360/artifacts/13681259210). [Genuine-Yandex CI 42634928333](https://github.com/manufact-test/nomusic/actions/runs/42634928333) — SUCCESS: ownerNativeLogCreated=true, ownerNativeLogRedacted=true, managedRefreshCycleVerified=true, originalBytesRestored=true, originalSignatureRestored=true, error="". **Audio="NOT_TESTED_NO_ACCOUNT"; владелец ещё не подтвердил исправление паузы!**

> **W28 — В РАЗРАБОТКЕ (2026-11-09):** диагностика Windows в приложении; первичный owner audio FAIL остаётся, настоящий звук не подтверждён. Версия 0.24.1; новая кнопка «Скачать диагностику» на главной, рядом с «Открыть Яндекс.Музыку». TXT с allowlist событий .NET bridge + Electron main/renderer; лог без токенов, ссылок аудио, паролей, почты и персональных данных. Ожидается реальный owner TXT, после которого чинить паузу. Документ [W28](W28-OWNER-DIAGNOSTICS-20261109.md).\n> **W27 — OWNER REAL AUDIO TEST FAIL (2026-11-09):** Владелец установил W26, штатный Яндекс с выключенной подменой работает, но с включённой подменой новый трек (в частности Гуф «Новогодняя») сразу ставится на паузу. При включении «Старт» посреди песни оригинал продолжает играть без подмены. В GUI нет пользовательской выгрузки диагностики и PNR. **Никаких заявлений о работающей подмене!** Следующий этап: встроенная безопасная диагностика → корень мгновенной паузы → реальная подмена и управление. Полный протокол: [W27 OWNER AUDIO FAILURE](W27-OWNER-AUDIO-FAILURE-20261109.md).
# CELIKOM Windows — актуальная передача W26 (2026-11-09)

**Главное требование:** единый установщик; CELIKOM подключается к обычной установленной Яндекс.Музыке и использует родной плеер (Play/Pause/Seek/Next/очередь/радио). Никакого отдельного плеера, ручных модов, запуска терминала и отключения защит Windows.

**Репозиторий:** manufact-test/nomusic. **Ветка:** experiment/windows-companion-integration-20261108.
**Проверенная функциональная точка:** 7226f1ce595f9ee49781cea50a2ce9d237730503. **Исходная контрольная точка W25:** febe369b0aba49e703daa7214e86270bac0ba1b7.

## W26 — что сделано и проверено

- Исправлен сценарий зависания: подтверждённый CELIKOM source grant больше не ждёт бесконечно застрявший нативный Yandex getFileInfo. Нативный ответ может предоставить исходные метаданные; если он не приходит, возвращается корректная форма ответа с тем же аудиоресурсом Yandex и нашим MP3/AAC source вместо зависания.
- Добавлены fallback-поля responseTime и url и bitrate MP3, используемые native file-info. При отсутствии подтверждённой подмены штатный ответ Яндекса НЕ обрезается и продолжается естественным образом. Локальный bridge timeout согласован с ограничением времени source lookup.
- **Проверено:** [real Yandex + recovery CI 42625065029](https://github.com/manufact-test/nomusic/actions/runs/42625065029) SUCCESS; 38/38 JS тестов, 61/61 .NET Bridge; успешно W24_ACTUAL_HOST_INSTALL_VERIFIED / W24_ACTUAL_HOST_RESTORED, native renderer attached, local bridge state reached, original files byte-identical restored, error="".
- **Adapter CI [42625065074](https://github.com/manufact-test/nomusic/actions/runs/42625065074)** SUCCESS: 20/20 adapter and 10/10 source controller tests. Тест stalled getFileInfo с одобренным grant проходит.
- **One-installer CI [42625065045](https://github.com/manufact-test/nomusic/actions/runs/42625065045)** SUCCESS, GitHub artifact 13677423231 с именем CELIKOM-W24-INTERNAL-NATIVE-UNSIGNED. Нужна только одна обычная установка CELIKOM.
- Производственный сервер, Android, расширение и компьютер владельца не трогали.

## Что ещё не доказано

На CI нет авторизованного аккаунта Яндекс.Музыки, поэтому **реальная слышимая подмена трека не проверена**. Равно как настоящая Pause/Seek/Next при звучащем заменённом треке. Нельзя выдавать offline fixtures за результат прослушивания. Сборка является внутренней тестовой версией.

## Следующий существенный шаг

Один аудиотест с настоящей учётной записью в обычном Яндекс.Музыке: установка CELIKOM, авторизация отдельно в CELIKOM, подключение кнопкой, прослушивание заранее известного одобренного трека, проверка Pause/Seek/Next и отключения. При дефекте — диагностика конкретного аудио и исправление, без повторного создания установщика. Восстановление оригинала предусмотрено.

---

# CELIKOM Windows — актуальная передача W25 (2026-11-09)

Репозиторий: manufact-test/nomusic
Ветка: experiment/windows-companion-integration-20261108
Проверенный код: 47352cd6983895e02b37d7af6f03712733c4c553
Бэкап: backup/windows-w25-native-main-relay-verified-20261109
Бэкап до внедрения relay: backup/windows-w25-pre-main-relay-20261109

## Требование владельца

ОДИН обычный установщик CELIKOM Windows. Родные Яндекс.Музыка, интерфейс, аккаунт Яндекса, музыка, радио, плейлисты, пауза, перемотка, Next, мультимедийные клавиши; CELIKOM лишь подменяет источник аудиотрека через собственное API. Никакого второго плеера, ввода Яндекс-пароля в CELIKOM, ручных PulseSync-модов, Windows Sandbox/VM/терминала, отключения Defender или специальных действий у пользователя. Отдельный логин CELIKOM остаётся для проверки подписки.

## Подтверждённые результаты

- Настоящий официальный Yandex 5.126.1 x64 в одноразовой Windows Server 2022, Defender ON: [W25 native-host CI 42622540129](https://github.com/manufact-test/nomusic/actions/runs/42622540129) SUCCESS.
- Наш .NET native integration manager установил свою пару изменённых EXE и ASAR только после сохранения оригинальных файлов и проверки SHA. Яндекс запустился; наш основной Electron-модуль загрузился; renderer подтвердил внедрение и подключение к настоящему ресурсу file-info.
- W25 перенёс все запросы localhost в доверенный Electron main process, потому что прямой fetch из окна Яндекса не проходил. Native renderer теперь использует очередь exact-ID запросов и получает одобренные аудиогранты через executeJavaScript без токена локального моста. Реальная связь main→CELIKOM→renderer подтверждена.
- В реальном запуске: nativeHostLoaded=true, rendererInjected=true, resourceHookAttached=true, companionBridgeStarted=true, nativeBridgeStateReached=true, mainProcessRelayReached=true, rendererStateDelivered=true, managedRestoreConfirmed=true, originalBytesRestored=true, originalSignatureRestored=true, error="".
- 35 JS тестов PASS: native renderer single/batch, Next/Stop, сохраняются методы Yandex pause/seek, реле, контроль источника и origin. 61 .NET bridge тест PASS. Исходный EXE восстановлен байт-в-байт, его подпись опять Valid.
- Единый установщик с собственным CELIKOM GUI и native host + renderer: [W24 installer CI 42622515498](https://github.com/manufact-test/nomusic/actions/runs/42622515498) SUCCESS. Artifact id 13677290496, имя CELIKOM-W24-INTERNAL-NATIVE-UNSIGNED. После установки пользователь может нажать «Подключить CELIKOM» и при необходимости «Восстановить Яндекс». Без Node/отдельных модов. Деинсталляция сначала пытается восстановить оригинал.
- Действующий W21 guarded rollback: 27 тестов. W24 native builder: 13 тестов.
- Компьютер владельца не изменяли. Android, браузерное расширение, сервер, продакшен не изменяли.

## Что ПОКА не доказано

Нет авторизованной Яндекс.Музыки на одноразовом CI. РЕАЛЬНОГО СЛЫШИМОГО ЗВУКА подменённого трека не тестировали, и нельзя утверждать, что родная пауза/seek/Next при слышимой подмене уже работают. Только реальное подключение и offline позитивные контрактные тесты.
Установщик внутренний и неподписанный: возможны предупреждения Windows; в CI Defender включён и Яндекс запускался. Принимается только строго проверенная версия Яндекса 5.126.1 с ASAR SHA 5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215.

## Следующий шаг

Один реальный тест на Windows 10 владельца с обычным Яндексом и собственным аккаунтом. Поставить единый CELIKOM, войти отдельно в CELIKOM, нажать подключение, слушать заранее подтверждённый трек, проверить слышимую подмену, паузу, seek, Next, радио, отключение и восстановление. Никаких терминалов или ручной правки клиента. При проблеме диагностировать именно звук и плеер, не строить новый UI с нуля.

Детальная текущая запись: docs/windows/W25-NATIVE-MAIN-RELAY-INTEGRATION-20261109.md.
Ранний продуктовый контракт: docs/windows/W19-OWNER-PRODUCT-CORRECTION-20261109.md.
