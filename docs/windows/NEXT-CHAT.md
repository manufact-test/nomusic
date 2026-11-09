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
