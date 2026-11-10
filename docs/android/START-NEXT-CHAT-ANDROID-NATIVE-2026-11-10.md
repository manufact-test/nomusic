Привет! Продолжаем **существующий CELIKOM Android**. Ты новый ведущий разработчик; ничего не начинай с нуля и работай большими самостоятельными блоками.

**GitHub:** https://github.com/manufact-test/nomusic
**Ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`
**Последний проверенный код:** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`
**Бэкап:** `backup/android-signed-source-bridge-media-session-ci-green-20261110`
**Текущий HEAD:** сначала проверь напрямую; после проверенного SHA могли быть только документационные коммиты.

**Начни с навигации:** `docs/android/00-NATIVE-HANDOFF-NAVIGATION-2026-11-10.md`, затем `docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md` и `docs/android/NEXT-CHAT.md`.

**Результат последнего крупного захода:** [CI статического исследования #42804081064](https://github.com/manufact-test/nomusic/actions/runs/42804081064) **SUCCESS**, [CI Android-модуля #42804081053](https://github.com/manufact-test/nomusic/actions/runs/42804081053) **SUCCESS 2/2**. Проверен настоящий издательски подписанный Яндекс `2026.10.3 #170gpr`: пять APK, шесть DEX, 230 533 тела методов, 837 500 связей вызовов. Единственный прямой caller конвертера `sw7.y0/z0` — **`Lhee;->a`**; среди потребителей модели `eed` — **`Lged;->a`**. Четыре конкретные реализации Media3 ExoPlayer: `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`. До четырёх переходов вверх от FileInfo и media общего вызывающего метода **не найдено** — это не доказывает отсутствие decoder-пути. Подтверждены статические вызовы `MediaSession.setMetadata` (2 вызывающих метода) и `setPlaybackState` (2), но они не являются audio source hook.

**Важный прорыв соседней Windows-команды:** CELIKOM Windows **0.24.7** реально воспроизводит наши версии **внутри настоящего десктопного Яндекса**; владелец проверил Pause, Seek, Next, Previous, «Мою волну» и Track ID. Источник подменяется через `getFileInfo/getFileInfoBatch` до native player, без второго проигрывателя. Stop запрещает **будущие** подмены, но не выдергивает уже загруженный Яндексом источник из буфера. См. `docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md` и `windows-companion/w22/native-resource-adapter.mjs` на Windows HEAD `2338c2109ad55beb583397cfbf7161726d678777`. **Не трогай успешную Windows 0.24.7.** Windows-фикс подписанного URL `celikom_native_query_guard` в Android не переносить вслепую.

**Что уже готово в Android:** `NativeGrantContract`, `NativeReplacementLifecycle`, `NativePrePrepareAdmission`, `NativeSourceGate`, безопасные read-only наблюдатели FileInfo и MediaSession. Все тесты и сборка прошли. **НО ни один аудиоисточник в настоящем Android Яндексе ещё не заменён.**

**Твоя главная задача:** от доказанных `Lhee;->a` / `Lged;->a` искать фактическую передачу FileInfo к datasource/decoder через DEX register dataflow, coroutine/obfuscated callbacks, интерфейсы и возможные native boundaries. Не ходить кругами по ExoPlayerImpl, AppMetrica, x86 LSPatch или бесконечным синтетическим моделям. Не считать совпадение времени MediaSession+FileInfo доказательством Track ID. Если понадобится реальное исполнение — только **отдельный изолированный ARM Android-стенд с разрешённым доступом**; главный HONOR и официальное приложение владельца не трогать. После доказанной текущей связи `trackId + edition + generation → FileInfo → decoder before prepare` подключать наши готовые контракты, только потом тестировать «Раскол» `42884423`, «Дым» `39949113`, паузу, Seek, радио, Next.

**Не менять:** эталон Test.50, HONOR, Windows, расширение, сервер, БД/production, учётные данные, DRM/подпись/Play Protect. ChromaSync платный и требует ручного патчера, просить его не надо; Яндексу не писать. Никаких фальшивых «уже работает» до настоящего звукового теста.

Действуй автономно, сохрани бэкап и документацию, верни коротко: **что доказано, что реально реализовано, CI, что ещё блокирует Android-звук и что нужно проверять**.