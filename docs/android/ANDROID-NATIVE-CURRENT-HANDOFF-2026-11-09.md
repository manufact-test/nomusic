# CELIKOM Android — актуальная передача, 09.11.2026

## Точка входа
Репозиторий: manufact-test/nomusic.
Рабочая ветка: experiment/android-native-yandex-fileinfo-hooklab-20261109.
Исходный HEAD перед этой документационной передачей: 5e2a98158f89b266530b9e7dd7ba8e9e04107812.
Предыдущий резерв: backup/android-native-raskol-dym-source-guard-clone-research-20261109.
Точную новую точку передачи брать из HEAD рабочей ветки и нового backup branch. Последний этап — только документы, код не менялся.

**Задача:** CELIKOM должен подменять разрешённые версии треков в НАТИВНОЙ Android Яндекс.Музыке с одним её собственным плеером. Вход в Яндекс выполняет пользователь только внутри Яндекса. Никакого WebView, второго проигрывателя, ввода Yandex credentials в CELIKOM, root, обхода Play Protect, подмены подписи издателя или извлечения OAuth-токенов.

**Ограничение владельца:** HONOR 50 NTH-NX9 Android 13, официальный ru.yandex.music установлен и содержит нужные загрузки. Владелец не разрешал удалять/заменять его и не имеет запасного телефона. НЕ просить удалять приложение и не менять production, Test.50, Windows, extension, backend, каталог. При любых установочных рисках — стоп и согласование.

## Что реально проверил сам владелец

1. На основном HONOR успешно открылся отдельный собственный ARMv7 loader APK.
2. Отдельный own LSPatch/libxposed witness на этом HONOR: Native host STARTED; Module hook armed YES; onCreate intercepted YES. Это настоящий rootless ARMv7 hook, но ТОЛЬКО в собственном приложении.
3. Собственный Audio Smoke Test: Module hook ARMED YES; Source changed BEFORE PREPARE YES; Prepare=3, Pause=1, Resume=1, SeekComplete=1, Next=1, Errors=0; Last STOPPED. После скриншота владелец УСТНО подтвердил, что все звуки слышны, Pause/Resume/Seek/Next работают. CI own APK: https://github.com/manufact-test/nomusic/actions/runs/42652387877 — SUCCESS. Fallback был проверен ручной кнопкой, а не автоматической аварией. НЕ просить повторять own-tone тесты.
4. Все три own APK — самостоятельные приложения, НЕ модифицированная Яндекс.Музыка. Отсутствие блокировки установки own APK не доказывает Play Protect acceptance для изменённого Яндекса.

## Главные регрессии прежней Android-архитектуры — тестировать первыми

- RASKOL / Космонавты «Нас не понимают вообще», Yandex track ID 42884423; Лёша Свик «Дым», ID 39949113: native pause/seek у пользователя задерживались/не срабатывали. В Test.74 Android framework session видел seek на 3.102–3.282 с раньше старого внешнего Yandex Media3-контроллера; Pause Media3 иногда не отражал вообще. Старый CELIKOM воспроизводил альтернативу через ВТОРОЙ MediaPlayer, оттого управление и слышимый звук расходились. См. docs/android/ANDROID-TEST74-HONOR-PROVEN-YANDEX-REMOTE-LAG-2026-11-08.md и ANDROID-TEST70-HONOR-203805-ARCHITECTURE-2026-11-08.md.
- «Пшик»/щелчок на первом подключении: старый Test.31 командовал 160 мс blend двух аудиопотоков, но владелец всё равно слышал артефакт; иногда были мгновенные повторные выдачи альтернативы после seek. Нельзя пытаться лечить это только длительностью fade; нужен один источник и один decoder clock, выбор до prepare. См. docs/android/ANDROID-0385-TEST31-OWNER-REJECTED-FORENSIC-2026-11-04.md.
- Рандом, Next, cold start: старые задержки 2–8+ сек, sparse Range поток мог исчерпать буфер после подключения, исходный звук переключался обратно. Перед допуском alternative проверять точную track+edition, права, codec, duration, key/crypto, HTTP Range, полную готовность стартового участка; ограничить ожидание, не переключать аудио туда-сюда после старта.
- Test.50 — лучшая принятая версия старой архитектуры, резерв backup/android-test50-exact-source-owner-accepted-20261108. Его НЕ переписывать и не считать решением native-player проблем.

## Текущий код и подтверждения CI

- Настоящий издательски подписанный Yandex Android 2026.10.3 #170gpr / code 24026531, пять split APK. Точная статическая цепочка FileInfoApi / OldFileInfoApi → FileInfoDto → sw7.y0/z0 → eed. Поля DTO включают urls, codec, key, bitrate, quality, gain, r128. См. ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md.
- android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeHookEntry.java: read-only Xposed hooks конвертеров плюс optional count-only accessor eed.a():String; без чтения значений, URL, ключей или аккаунтов, без изменения источника. CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/42662932600 . В самом Яндексе на телефоне ещё НЕ запускалось.
- NativeSourceGate.java: проектная fail-closed модель единственного источника ДО prepare, точный track+edition, generation fencing при Next, игнорирование поздних ответов, запрет post-start source flip. В настоящий native decoder пока НЕ встроена. NativeSourceGateTest.java: CI SUCCESS https://github.com/manufact-test/nomusic/actions/runs/42658954205 , 10 031 синтетических assert, включая 2 500 быстрых Next и RASKOL/Дым запоздалые события. Это Java-логика, не реальное аудио.
- Статический DEX downstream scanner: CI SUCCESS https://github.com/manufact-test/nomusic/actions/runs/42660229676 , Lged.a вызывает eed.a():String. Реальный путь от DTO к MediaSource.prepare/декодеру ещё НЕ доказан; часть классов обфусцирована. Не создавать неподтверждённый synthetic file-info ответ и не выкидывать key/IV.
- LSPatch x86/x86_64 emulator падал на liblspatch.so UnsatisfiedLinkError и с модулем, и без модуля. Эмуляторный x86 NO-GO не перечёркивает собственный ARMv7 PASS. Эти попытки не повторять.
- Внешние способы модификации НЕИЗМЕНЁННОГО официального Яндекса (MediaSession, VPN, accessibility, audio capture) не дали подтверждённого unprivileged native source replacement. Конкурент ChromaSync-Mobile rootless использует патченный native host; публичный README не даёт исходников реализации. См. ANDROID-NATIVE-UNMODIFIED-APP-QUICK-HYPOTHESES-2026-11-09.md.

## Блокер, на котором остановились

Чтобы тестировать внутри Яндекса, нужен отдельный совместимый native host, который не конфликтует с уже установленным ru.yandex.music. Переподписанный same-package APK поверх официального не устанавливается. Side-by-side требует нового packageId на пяти split APK, корректных ContentProvider authorities, ресурсов, identity строк в DEX, login/deep links и app integrity.

Ephemeral CI-only скрипт android/native-yandex-hooklab/clone_native_splits_ephemeral.py проверяет отдельный структурный вариант. Оригинальный сертификат и пять split подтверждены, но сборка клона НЕ УДАЛАСЬ: https://github.com/manufact-test/nomusic/actions/runs/42662932538 — FAIL, APKTOOL_REBUILD_FAILED_ANDROID_FRAMEWORK_MISSING. Сначала пробовали некорректный --force-manifest; с -r manifest оставался бинарным. Не повторять те же попытки. Не публиковались сторонние APK, никто ничего не устанавливал и не трогал Яндекс владельца.

**На текущий момент нет ни рабочего CELIKOM+Yandex APK, ни native аудиоподмены, ни Play Protect verdict для изменённого Яндекса.**

## Следующая работа (без начала с нуля)

1. Изучить этот handoff, docs/android/NEXT-CHAT.md, ANDROID-NATIVE-REGRESSION-PREFLIGHT-2026-11-09.md, ANDROID-NATIVE-CLONE-STRUCTURAL-TRIAL-2026-11-09.md, ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md, последний код и CI.
2. Решить независимый безопасный rootless installation path настоящего native Yandex (вся пятёрка split, ресурсы, normal login, подписи) без удаления официального приложения. Изолированные проверки CI, без релиза чужих APK; не перебор старых Apktool флагов.
3. Только после install/auth feasibility — минимальный count-only, privacy-safe native FileInfo runtime test на настоящем клиенте, с подтверждённым source selection ДО декодера. Не выдавать статический метод за доказанный decoder.
4. После этого один rights-approved replacement с проверенными codec, key/crypto, Range, duration/runway и original fallback до prepare, без второй сессии. Первыми тестами на реальном native плеере: RASKOL и «Дым» Pause/Seek; отсутствие «пшика» на первом подключении; Next/playlist/radio, быстрые переключения, Bluetooth, полное окончание трека.
5. Держать Google Play Protect включённым; при блокировке не обходить, а документировать. Никакого root, Credential/OAuth capture, обхода подписи и DRM. Не трогать Test.50 и production.

## Подтверждённые границы результата

PASS: own-source ARMv7 rootless hooks; own MediaPlayer audible controls; защитная Java-модель 10 031 assertions; точный native-Dex FileInfo candidate.
NOT PROVEN: runtime hook внутри Yandex, его собственный MediaSource decoder, корректная аудиоподмена/Seek для RASKOL/Дым, бесщелчковый native join, login в клоне, Play Protect для клона.

Дальше делать именно native Yandex. Не возвращаться к очередным synthetic sound лабораториям.
