# CELIKOM Android A1 — точный наблюдатель завершения MAIN (11.11.2026)

## Основание: реально переданный ChromaSync-Clone-3.0.1.apk

Проверенный прежним чатом SHA-256 образца: 4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d. Его побайтовые сведения сохранены в ANDROID-A1-CHROMASYNC-APK-OFFLINE-COMPARISON-20261111.md. В текущем runtime бинарник не примонтирован, поэтому повторный побайтовый анализ здесь не заявляется.

ChromaSync: независимый clone package, нативный Yandex 2025.10.4 #120.1rur, LSPatch metaloader с вложенным origin.apk, собственный LibXposed API102 модуль, sigBypassLevel=2. CELIKOM: независимый нативный Yandex 2026.10.3 #170gpr, metaloader+origin.apk уже воспроизведены, но нативный MAIN трижды уходит в EXIT_SELF(0), в том числе без модуля. Установка и упаковка доказаны, запуск UI не доказан. ChromaSync не проверялся на HONOR и не доказывает безопасную параллельную установку.

Различия версии, модуля и level2 реальны; нельзя выдавать конкретную причину EXIT_SELF за доказанную. Level2 меняет механизм проверки подписи и не разрешён для CELIKOM: НИКАКИХ level1/2, vendor-signature spoof, авторизационных обходов, Play Protect bypass или изменения официального приложения.

## Новый изолированный эксперимент

От статического аудита известны пять вызовов System.exit, два Process.killProcess и класс ck7 с обработчиком uncaughtException, но фактический runtime caller ещё неизвестен. Старые ART-трассы исчерпали буфер 8 MiB или были нулевыми.

Добавлен исходный, без разрешений, исключительно исследовательский LibXposed-модуль, область действия ровно pro.celikom.yandex.nativeclonelab. На истинном ARM13 в CI, только при CELIKOM_A1_EXIT_WITNESS=1, он вставляется как ЕДИНСТВЕННЫЙ собственный диагностический модуль в один lab APK с LSPatch sigBypassLevel=0. Модуль наблюдает java.lang.Thread.dispatchUncaughtException, System.exit, Runtime.exit и android.os.Process.killProcess; каждый hook делегирует chain.proceed() без изменений аргументов, результата, исключений или поведения приложения. Зарегистрированные hooks могут не перехватить нативный или ранний вызов: отсутствие маркеров не доказывает отсутствие вызовов.

В логах допускаются только фиксированные enum-маркеры без Throwable message, текстов stacktrace, URL, токенов, персональных данных и vendor bytecode. Python-классификатор связывает их исключительно с новыми PID процесса MAIN из ActivityExitInfo, отвергает фальшивые поля. Положительный маркер указывает конкретную семью вызова; отсутствие маркера оставляет NO-GO. Наличие ARMED — доказательство только постановки hook, но НЕ его выполнения.

Билд отдельной ветки: experiment/android-a1-exit-callsite-witness-20261111; исходный резерв: backup/android-a1-before-exit-callsite-witness-20261111 @ cc4cb0f. Workflow .github/workflows/android-native-a1-exit-callsite-witness.yml. 1-day artifact содержит ТОЛЬКО наш исходный модуль, без APK Яндекса. Тестовый host, ключи и исходные vendor splits эфемерны. CI строгий: даже если сборка и тесты зелёные, MAIN EXIT_SELF продолжает означать А1 NO-GO.

Ветка НЕ интегрируется в основу без проверки результатов. Не трогать Test.50, Windows, расширение, production, HONOR или официальный Яндекс. Этап B по-прежнему заблокирован до слышимой проверки Stage A владельцем.
