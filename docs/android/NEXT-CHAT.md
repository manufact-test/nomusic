> Последний runtime-итог 09.11.2026: оригинальный ARM macOS emulator CI 42669152016 FAIL ещё до установки из-за `HV_UNSUPPORTED` (недоступная nested virtualization). Отдельный original software-emulation gate `-accel off` CI 42672246229 ожидает результата. Offline structural five-split PASS CI 42670648029 остаётся действительным, но **никаких on-device native Yandex / clone / Play Protect / audio доказательств нет**. Coexistence run CI 42671525588 завершился без job-записей, причину не выдумывать. Подробности в CURRENT-HANDOFF.

> ОБНОВЛЕНИЕ: Phase2 offline structural clone **5/5 PASS**, GitHub Actions 42670648029. Новое: `docs/android/ANDROID-NATIVE-PROVIDER-IDENTITY-PHASE2-2026-11-09.md`. Все ограничения: клону ещё НЕ подтверждены установка, запуск, Yandex login, Play Protect, native decoder и audio. Ни один APK не распространялся. Дальше clean ARM emulator side-by-side test, без телефона владельца.

> Обновление 09.11.2026: ARSCLib альтернативно перепаковал первый split, но остановлен пятью совпадающими ContentProvider authorities: CI 42668435366, `ARSC_PROVIDER_AUTHORITY_COLLISION`. Побочный клон на HONOR НЕ устанавливать. Отдельный чистый ARM-эмуляторный оригинал Яндекса: CI 42669152016, статус на момент записи ожидает проверки. Подробнее в `ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md` и `ANDROID-NATIVE-ARM-EMULATOR-ISOLATED-2026-11-09.md`.

# CELIKOM Android — NEXT CHAT, актуальный указатель

**Сначала обязательно прочесть** docs/android/ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md. Он содержит полный актуальный статус после owner-проверки звука. Старый накопленный NEXT-CHAT.md сохранён в Git history.

GitHub: manufact-test/nomusic.
Рабочая ветка: experiment/android-native-yandex-fileinfo-hooklab-20261109.
Функциональный HEAD до handoff-only коммита: 5e2a98158f89b266530b9e7dd7ba8e9e04107812.
Предыдущий резерв: backup/android-native-raskol-dym-source-guard-clone-research-20261109.
Новый handoff-only commit = HEAD текущей рабочей ветки; код в нём не менялся.

**Уже пройдено владельцем:** HONOR 50 Android 13; отдельные собственные ARMv7 LSPatch/libxposed приложения открываются. Hook witness: Module hook armed YES / onCreate intercepted YES. Audio Smoke: Source changed BEFORE PREPARE YES, Pause=1, Resume=1, SeekComplete=1, Next=1, Errors=0, и владелец подтвердил на слух, что всё работало. Не просить повторить. Это НЕ нативный Яндекс.

**Новая логика:** NativeSourceGate.java, CI 42658954205 SUCCESS (10 031 синтетических assert, 2 500 Next); не подключена в реальном Яндексе. Read-only native FileInfo module CI 42662932600 SUCCESS: sw7.y0/z0 -> eed и optional eed.a():String; на реальном Yandex host ещё НЕ выполнялся. Собственный Android тест и реальный native Yandex decoder — разные вещи.

**Следующий блокер:** native Yandex signed #170gpr code 24026531, пять APK, нужен side-by-side rootless compatible host без удаления официального ru.yandex.music. Последняя Apktool clone CI 42662932538 FAIL на framework resources rebuild. Готового clone APK, нормальной авторизации и Play Protect verdict НЕТ.

**Первые дефекты для native-player теста:** RASKOL/Космонавты «Нас не понимают вообще» ID 42884423 и Лёша Свик «Дым» ID 39949113 — native Pause/Seek и ~3.1–3.3 с лаг внешнего Media3; «пшик»/двухплеерный crossfade при первом подключении; запоздалый Next/радио/cold joining.

**Продукт:** только native Яндекс, один его проигрыватель, pre-prepare source substitution после отдельного настоящего decoder доказательства, rights-approved versions. Без второго плеера, WebView, root, обхода подписей/Play Protect, сбора Яндекс токенов, удаления официальной установки, перепаковки чужих APK в публичные артефакты. Test.50 backup/android-test50-exact-source-owner-accepted-20261108 неприкосновенен.

**Полная передача:** docs/android/ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md.
