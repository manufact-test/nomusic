> Актуальный блокер 09.11.2026: read-only CI 42690904213 подтвердил нарушение сортировки DEX string_ids после текущей замены адреса AppMetrica. CI 42691145641 подтвердил существование альтернативных строк той же длины, сохраняющих порядок; в код клона они НЕ применены. Оригинальный Яндекс запускается, клон пока падает на YMApplication. Подробности: docs/android/ANDROID-NATIVE-DEX-STRING-ID-ORDER-2026-11-09.md. Не публиковать APK и не трогать HONOR/Test.50.

> АКТУАЛЬНОЕ 09.11.2026: ошибочная PID-диагностика исправлена! Оригинальный подписанный Яндекс успешно запускается в изолированном ARMv7-translated Android 11, CI 42686813136. Параллельный клон устанавливается (5+5 split) но ПАДАЕТ на `ru.yandex.music.YMApplication`. Проверки CI 42688277066 и 42689510730: `HAS_CODE=true`, loader path включает `base.apk`, класс есть в DEX, заголовки/контрольные суммы и compression корректны. Нельзя утверждать, что защита подписи причина. Подробнее: `docs/android/ANDROID-NATIVE-DEX-LOADER-RUNTIME-2026-11-09.md`. TrackId FileInfo param0 статически доказан, runtime связь с декодером всё ещё НЕ доказана. Original HONOR и принятый Test.50 не трогать.

> АКТУАЛЬНОЕ ОБНОВЛЕНИЕ: подписанный #170gpr **FileInfoApi.a и OldFileInfoApi.a имеют `trackId` строго в параметре 0**, `codecs` в 1, `quality` в 3 — CI 42677418284/42677690317/42677831933 SUCCESS. Модель `NativeTrackIdentityGate.java` 10 015 JVM assertions PASS, hooklab CI 42677264985 SUCCESS — НЕ native audio proof. Структурный 5/5 clone + НОЛЬ resolved provider collisions CI 42678096410 SUCCESS, но нет реальной установки, входа или Play Protect. ARM emulator HVF_UNSUPPORTED повторяется, auto-run отключен. Следующий реальный рубеж — безопасный native runtime FileInfo param0+edition+decoder pre-prepare и пауза/перемотка RASKOL/«Дым», без изменения установленного официального Яндекса и Test.50. Полные подробности — `ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md`.

> 09.11.2026 — TRACK ID: `FileInfoApi.a` подписанного Яндекса принимает несколько String-параметров, `DownloadInfoApi` имеет маршрут `tracks/{trackId}/download-info`. **Не доказано**, что download-ID соответствует звучащему треку или что `FileInfoDto` содержит достаточную связку track+edition. Для этого добавлен whitelist-only static annotation audit `audit_native_track_identity_static.py`, первый новый workflow 42673655477 упал до создания job; второй 42674235050 пока без подтверждённого PASS. Дальше нужен native read-only correlation `trackId + edition + generation → источник до prepare`. ARM macOS emulator повторно FAIL 42672246229 (`HV_UNSUPPORTED` даже с `-accel off`): этот путь не гонять снова. Offline 5/5 split structural PASS 42670648029 остаётся доказанным, но без runtime/логина/подмены.

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
