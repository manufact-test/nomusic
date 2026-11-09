# CELIKOM Android — CURRENT NEXT CHAT (2026-11-09)

> **Основная передача:** [ANDROID-NATIVE-CANONICAL-HANDOFF-2026-11-09.md](ANDROID-NATIVE-CANONICAL-HANDOFF-2026-11-09.md). **Прочитать её целиком до любых изменений.** Старый длинный текст этого файла (около 200 КБ) полностью сохранён в истории Git, например в коммите `be77237f70fdf783016eea8bc6d0b44ab8596e8f`; удалена только накопленная избыточность из актуального указателя.

## Точка входа

- GitHub: `manufact-test/nomusic`
- Ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`
- Код: `android/native-yandex-hooklab/`
- Требования: **нативный Яндекс — единственный плеер**. Не WebView, не второй плеер, не root, не обход подписи, не отключение Play Protect, не сбор паролей/токенов. Оригинальный HONOR, Test.50, стабильная основа и сервер не тронуты.
- Точная проверяемая версия Яндекса: `ru.yandex.music 2026.10.3 #170gpr`, код `24026531`.
- Доказанный статический кандидат: `FileInfoDto → sw7.y0/z0 → eed`, с `urls, codec, bitrate, key`. **В рабочем приложении подмена ещё не функционирует**.
- Есть успешно собранный read-only модуль libxposed 102 и проверенная временная упаковка пяти native APK через LSPatch `sigbypass=0`. [Сборка](https://github.com/manufact-test/nomusic/actions/runs/42611563341) · [проверка упаковки и ELF](https://github.com/manufact-test/nomusic/actions/runs/42623602723).
- На Android 11 x86 и x86_64 эмуляторах LSPatch падает до запуска модуля с `liblspatch.so` / `UnsatisfiedLinkError`, причём **без модуля CELIKOM падает точно так же**. Оригинальный Яндекс в контрольном эксперименте работает. [Контроль оригинала PASS](https://github.com/manufact-test/nomusic/actions/runs/42621833205) · [LSPatch без модуля NO-GO](https://github.com/manufact-test/nomusic/actions/runs/42622723034) · [x86_64 NO-GO](https://github.com/manufact-test/nomusic/actions/runs/42624416091).
- Следующий необходимый этап — изолированная **нативная ARM Android13+** тестовая среда с Play Protect ON. Пока нет такого подтверждения, не обещать рабочий APK. Не повторять те же x86 проверки и не трогать HONOR.

## Подробности

- [Корневой технический блокер](ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md)
- [Тестовый модуль и сборка](ANDROID-NATIVE-YANDEX-ROOTLESS-HOOKLAB-2026-11-09.md)
- [DEX-аудит источника](ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md)
- [Полная актуальная передача](ANDROID-NATIVE-CANONICAL-HANDOFF-2026-11-09.md)

**Примечание:** переподписанная `ru.yandex.music` не устанавливается поверх официальной с другим сертификатом; прежде чем менять способ установки, требуется отдельное согласование. Пользователь разрешил подготовку только для отдельного тестового устройства.

## Новая подготовка (отдельный ARM-стенд)

Добавлен `android/native-yandex-hooklab/probe_arm_device.py`: **только чтение**, 8 синтетических unit-тестов. Важно: #170gpr требует `armeabi-v7a` — *просто ARM64 недостаточно*, если Android 64-bit-only. Скрипт блокирует основной HONOR 50, уже установленный Яндекс, эмуляторы, Android ниже 13 и отсутствие Google Play. Play Protect ON **нельзя** подтвердить наличием Play Store: требует проверки на отдельном устройстве. Никаких новых runtime PASS, подмены звука или публикации APK нет.

## Нет запасного телефона

Обновлён путь без покупки устройства: Google Developer Device Platform — физический Galaxy A52 5G (Android 14, Device Streaming), альтернативный Samsung Remote Test Lab. Прежде чем устанавливать что-либо, нужна проверка `armeabi-v7a` и Play Protect. План: `docs/android/ANDROID-NATIVE-NO-SPARE-CLOUD-ARM-GATE-2026-11-09.md`. Внешних загрузок APK и удалённых запусков не было; требуется отдельное разрешение для передачи перепакованного Яндекса облачному сервису.

## Решение владельца: основной Яндекс не удалять

На HONOR допустимо тестирование **только если установленная официальная Яндекс.Музыка остаётся нетронутой**. Параллельная копия с отдельным package ID рассматривается как эксперимент, но пока **не собрана**: docs/android/ANDROID-NATIVE-PARALLEL-CLONE-GATE-2026-11-09.md. Рабочий профиль без изменения package ID не устраняет конфликт подписи. Не устанавливать текущую переподписанную ru.yandex.music на HONOR.

## Взято полезное из Windows W28 (read-only review)

Проверена Windows branch `experiment/windows-companion-integration-20261108` @ `7c1858e6` (W28). Подтверждены работающие renderer hook, source grant bridge, таймауты/защита от запоздавшей подмены и безопасная диагностика. **Настоящий звук в Windows ещё FAIL/не подтверждён**, нельзя копировать синтетический file-info ответ (особенно key/iv/codec) в Android. Выводы и порядок Android: `docs/android/ANDROID-NATIVE-WINDOWS-W28-LESSONS-2026-11-09.md`. Windows-код не изменяли.

## Проба параллельной копии без установки на HONOR

Добавлен **только read-only** аудит `audit_parallel_clone.py` + CI `.github/workflows/android-native-yandex-clone-feasibility.yml`: считает совпадения package/authorities/DEX оригинального подписанного #170gpr, APK удаляются после теста. **Не создаёт и не публикует клон.** Подробности: `docs/android/ANDROID-NATIVE-CLONE-STATIC-GATE-2026-11-09.md`.

## Проверены риски клонирования #170gpr (CI PASS)

[CI 42637284714](https://github.com/manufact-test/nomusic/actions/runs/42637284714): 5 официально подписанных split APK, 6 DEX; 11 провайдеров, 9 package-bound authorities, 109 ссылок на старый пакет в manifest, из них **86 — имена Java-классов, не требующие слепой замены**; в DEX 2 точные строки package ID и 35 других содержащих ID. Бездумное клонирование НЕ готово. В нашей ветке добавлен собственный ARMv7 loader host без Яндекса; его CI и реальный запуск надо подтвердить отдельно. docs/android/ANDROID-NATIVE-CLONE-STATIC-GATE-2026-11-09.md.

## Подготовлен реальный тест загрузчика без Яндекса (CI SUCCESS)

Собран собственный отдельный `CELIKOM ARM Loader Lab` для ARMv7 (no Yandex, no permissions): [CI 42638725850](https://github.com/manufact-test/nomusic/actions/runs/42638725850) — SUCCESS; [внутренний APK artifact 13683314600](https://github.com/manufact-test/nomusic/actions/runs/42638725850/artifacts/13683314600). **Это не рабочий CELIKOM и не проверка аудио.** На HONOR пока ничего не установлено; официальный Яндекс сохраняется. Дальше — ручной запуск отдельного тестового приложения с Play Protect ON, только когда владельцу будет удобно. Подробности: `docs/android/ANDROID-NATIVE-OWNED-ARMV7-LOADER-2026-11-09.md`.

## PASS владельца: ARMv7 on-device, отдельное приложение

9 ноября 2026 владелец установил независимый CELIKOM ARM Loader Lab на HONOR 50 (Android 13) и прислал скриншот открытого приложения. **ARMv7 JNI-host PASS**, установка без блокировки; официальный Яндекс не изменялся. В первой сборке Xposed module отсутствовал: это НЕ доказательство перехвата Яндекса. Новый этап — отдельный own-host hook witness с новой package ID, его два статуса видны прямо на экране. Подробности: docs/android/ANDROID-NATIVE-ARMV7-OWNER-WITNESS-2026-11-09.md.

## Готов отдельный ARMv7 hook-witness APK — CI SUCCESS

Сборка [42643802887](https://github.com/manufact-test/nomusic/actions/runs/42643802887) — SUCCESS; исходный коммит e9791456; [artifact 13687465487](https://github.com/manufact-test/nomusic/actions/runs/42643802887/artifacts/13687465487). APK также в библиотеке ChatGPT владельца под CELIKOM-ARMv7-HOOK-WITNESS-Test.apk. Новый package pro.celikom.armv7loaderhost.witness; не обновляет предыдущий собственный APK и не затрагивает официальный ru.yandex.music. **Реальный Xposed hook ещё не подтверждён!** Следующая проверка: владелец запускает этот APK и сообщает два статуса Module hook armed / onCreate intercepted. Детали: docs/android/ANDROID-NATIVE-ARMV7-OWNER-WITNESS-2026-11-09.md.

## НОВОЕ: подтверждён собственный ROOTLESS libxposed hook на реальном HONOR — PASS

Скриншот владельца `Screenshot_20261109_184208.jpg`: `Native host: STARTED`, `Module hook armed: YES`, `onCreate intercepted: YES` в отдельном CELIKOM ARMv7 Hook Witness. Значит, libxposed реально выполнился в своём ARMv7 приложении на HONOR 50 Android 13; проблема x86 loader не применима к этому ARM own-host. **НЕ означает работы в нативном Яндексе или аудиоподмены!** Следующий блокер — безопасная отдельная native-Yandex интеграция без удаления официального ru.yandex.music и без Play Protect bypass. Подробности в `docs/android/ANDROID-NATIVE-ARMV7-OWNER-WITNESS-2026-11-09.md`.
