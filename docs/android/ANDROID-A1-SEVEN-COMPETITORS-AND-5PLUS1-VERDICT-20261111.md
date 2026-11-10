# CELIKOM Android A1 — разбор семи публичных конкурентов и итог одно-APK эксперимента (11.11.2026)

## Материалы / метод проверки
Сверены актуальные README публичных репозиториев; не копировался исходный чужой бинарный код, не декомпилировался APK для распространения. Отличаем **техническую документацию автора** от подтверждения на собственном устройстве. Архитектура и запреты неизменны: нативный Яндекс внутри CELIKOM, ровно один музыкальный движок, Play Protect включён, официальный Яндекс на HONOR не трогаем, защита подписей/входа не обходится.

| Источник | Публично подтверждённое назначение | Что подходит CELIKOM Android | Что НЕ доказывает |
| --- | --- | --- | --- |
| [Hazzz895/FckCensor](https://github.com/Hazzz895/FckCensor) | Надстройка замены информации и аудио Яндекс.Музыки, установка через PulseSync | Архитектура каталога и выбора альтернатив, первичная Windows-аналогия | Не является rootless одним APK с нативным Android Яндексом |
| [Hazzz895/FckCensorData](https://github.com/Hazzz895/FckCensorData) | Публичная база подмен для FckCensor | Форматы сопоставления/версионирования записей | Не решает подпись и native Android запуск |
| [S4YN3X/F_ckCensor](https://github.com/S4YN3X/F_ckCensor) | Windows desktop patch, скрипт внутри desktop Яндекс.Музыки | Приёмы exact track mapping, включение/выключение, URL и диагностики | Desktop JS/Electron патч не является Android in-process decoder hook |
| [aeviww/yandex-music-client](https://github.com/aeviww/yandex-music-client) | Неофициальный клиент Tauri/Vue/Rust с собственным UI/очередью/плеером | Раздельный выбор source и async cancellation на уровне концепции | Свой плеер и UI прямо запрещены master-ТЗ Android |
| [mrvokintos/YandexMusicMod](https://github.com/mrvokintos/YandexMusicMod) | Десктопный форк с заменами и отдельным мобильным проектом | Каталог и desktop lifecycle концептуально | Android-native Яндекс-плеер с независимой подписью не доказан |
| [gagayhhad-tech/ym-liberty-android](https://github.com/gagayhhad-tech/ym-liberty-android) | Собственный Android WebView/Cordova/Web Audio клиент с MediaSession | Идеи фоновых событий/кэша без копирования UI | Явно **не** нативный штатный Яндекс-плеер, не соответствует утверждённой архитектуре |
| [Desai0/ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) | Нативный модуль к совместимому Android Яндексу; rootless — патчер исходного APK + модуль; root — LSPosed | Самая близкая техническая модель: in-process audio replacement, кэш перед воспроизведением, оригинал при неготовой записи | Их README не подтверждает безопасную установку независимого клона рядом с официальным Яндексом; предупреждает о возможном удалении официальной установки из-за подписей. Публичного кода Android-модуля в README нет |

Важно: предыдущий исследователь сообщил о `sigBypassLevel=2` в предоставленном ChromaSync-Clone-3.0.1.apk; сырые байты именно в этом контексте не были доступны для перепроверки. Такая конфигурация **не разрешена** для CELIKOM по master-ТЗ, поэтому не копируем её в нашу сборку.

## Наш доказанный прогресс именно к одному APK

Прогон [CI 42912195579](https://github.com/manufact-test/nomusic/actions/runs/42912195579), код `c0c7d04c91899fcb45652e428f3b954d2d922ccc`:

1. Полностью сохранены оригинальные пять publisher-signed split APK Яндекс.Музыки на **чистом disposable Android 11 x86/ARMv7 emulator**.
2. Пять отдельно re-signed split APK с другим ID `pro.celikom.yandex.nativeclonelab` объединены в **один APK**, с контрольной проверкой содержимого всех **6 DEX** и **3 native libraries** (SHA256 совпадают с 5 входными clone split). Издательский Yandex code в оригинале не менялся.
3. **Настоящий PackageManager PASS**: оригинал (5) + единственный клон (1) установлены одновременно; независимая подпись, `sigbypass=off`.
4. **Настоящий native startup FAIL**: клонированный MAIN завершился `EXIT_SELF(0)` до Activity/Window, `:AppMetrica` остаётся; в error-логах MAIN фигурирует `java.lang.IllegalStateException`, но ни traceback, ни причина не раскрыты.
5. Этот код ещё не включает LSPatch audio module в клоне; никаких слышимых подмен, доступа к CELIKOM API, trial, native/Yandex login, Play Protect verdict или HONOR установки нет. CI-бинарники удалены, никакой небезопасный APK пользователю не отправлен.

### Инженерный вывод
**Устранили проблему 5 APK против одного и доказали безопасное сосуществование пакетов на CI Android 11.** Но изолированный изменённый package ID **не может быть объявлен живой нативной Яндекс.Музыкой**, пока MAIN не работает; повторная перепаковка уже показала тот же EXIT_SELF, так что очередная бессмысленная серия подобных пересборок запрещена. Для продолжения нужна проверяемая безопасная native runtime инъекция/старт без обхода защиты подписи/Passport/DRM. Исправление мелкого компоновочного бага не решает неработающий главный процесс.

Рабочая ветка `feature/android-parallel-clone-single-apk-merge-20261111` и точный исследовательский backup `backup/android-parallel-one-apk-5plus1-install-pass-ui-blocked-20261111` сохранены. MASTER-ТЗ приоритетно, Android Test.50/Windows/stable/prod/HONOR нетронуты.

**Этап B — обязательно напомнить владельцу после принятого им проверенного на устройстве LSPatch-аудиоэталона; пока переход не разрешён.**
