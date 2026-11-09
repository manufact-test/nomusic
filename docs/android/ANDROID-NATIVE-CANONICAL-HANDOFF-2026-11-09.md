> **Актуальное обновление 09.11.2026:** [ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md](ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md) заменяет устаревшие статусы далее. Own Audio Smoke владелец проверил на слух, собственный ARM rootless hook работает. Но на самом нативном Яндексе никаких runtime hooks или аудиоподмен пока не подтверждено. Исходный HEAD перед docs handoff: 5e2a98158f89b266530b9e7dd7ba8e9e04107812.

# CELIKOM Android — каноническая передача следующему чату (09.11.2026)

**Статус:** эксперимент сохранён. Есть реальный, успешно собираемый и статически проверенный read-only модуль для **нативного Яндекса**, но нет подтверждённого запуска с LSPatch, подмены звука, теста Play Protect на устройстве или готового APK для пользователя.

## Репозиторий и точка восстановления

- **GitHub:** `manufact-test/nomusic`
- **Экспериментальная ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`
- **Подтверждённый HEAD до данного документа:** `be77237f70fdf783016eea8bc6d0b44ab8596e8f` — восстановление всех предыдущих записей, включая старый длинный `docs/android/NEXT-CHAT.md`, доступно через историю Git.
- **Базовая исследовательская ветка:** `experiment/android-native-yandex-gate1-20261109`, базовый HEAD `c285fc65262d79a731883bea14b23bbb2a076b9b`.
- **Принятый владельцем эталон Android Test.50** и основная стабильная ветка не изменялись. Никаких изменений на HONOR, сервере, в базе, каталоге и исходном официальном Яндексе.

## Неизменяемые продуктовые требования владельца

**CELIKOM должен работать ВНУТРИ обычного интерфейса нативной Яндекс.Музыки**: пользователь самостоятельно входит в Яндекс в его собственном приложении; CELIKOM незаметно помогает проигрывать разрешённые альтернативные версии через **единственный** плеер Яндекса, с его паузой, перемоткой, Next, радио, плейлистами и Bluetooth. **Не** WebView, не второй проигрыватель, не внешний оверлей с отдельными Play/Pause, не ввод учётных данных Яндекса в CELIKOM.

Требования к безопасности: без root, без отключения Play Protect, без обхода подписи/маскировки под издателя, без извлечения OAuth-токенов, без публикации чужих APK, без изменения официальной установленной Яндекс.Музыки на HONOR без отдельного разрешения. Владелец разрешил только подготовку и исследования **для отдельного тестового устройства**.

## Что точно найдено в настоящем APK

На оригинальном, подписанном сертификатом издателя `ru.yandex.music` **2026.10.3 #170gpr / 24026531**, 5 split APK:

1. `com.yandex.music.shared.player.content.remote.fileinfo.FileInfoApi` → `resources/v2/file-info`; `OldFileInfoApi` → `get-file-info`; `DownloadInfoApi` → `tracks/{trackId}/download-info`. [Реальный DEX-аудит PASS](https://github.com/manufact-test/nomusic/actions/runs/42609347093).
2. `FileInfoDto` содержит `urls, codec, key, bitrate, quality, gain, r128`. Нативный код переводит его в `eed` через **`sw7.y0(FileInfoDto,boolean):eed`** или **`sw7.z0(OldGetFileInfoDto,boolean):eed`**. Точные определения методов в исходном DEX подтверждены. [Форма DTO](https://github.com/manufact-test/nomusic/actions/runs/42609925869), [методы](https://github.com/manufact-test/nomusic/actions/runs/42613455742).
3. Ранее исследованный `PlayAudioApi` использует маршрут `plays`, вероятно события прослушивания, **не** доказанный путь выбора аудиопотока. Его **не использовать** для подмены.
4. `#170rur` и `#170gpr` не побайтово идентичны, хотя сигнатуры методов совпадают. Работать только с **точной #170gpr**. [Сравнение PASS](https://github.com/manufact-test/nomusic/actions/runs/42607424390).
5. Никакого фактического доказательства, что изменённый `eed` поступает в **тот же** нативный декодер **до prepare**, пока нет. Подмену источника не реализовали.

## Что написано и проверено

Код и сценарии: `android/native-yandex-hooklab/`.

- Modern libxposed API102 модуль `NativeHookEntry.java`: exact version/package gate, точное отражение двух `sw7.y0/z0` методов, вызов оригинала `chain.proceed()`, логирование **только агрегированных счётчиков**, никаких прав доступа, URL/ключей/учётных данных, изменения аргументов или результатов. [Сборка и синтетические тесты PASS](https://github.com/manufact-test/nomusic/actions/runs/42611563341).
- `ephemeral_patch_lab.py`: загружает в изолированный CI исходный XAPK, проверяет подпись издателя и 5 частей, временно встраивает CELIKOM через **JingMatrix/LSPatch v1.2-487** с **`sigbypass=0`**, подписывает одноразовым лабораторным сертификатом, проверяет идентичность частей и модуля, удаляет APK/ключи после теста. [Упаковка PASS](https://github.com/manufact-test/nomusic/actions/runs/42613009821).
- Дополнительная проверка: все четыре `liblspatch.so` (ARMv7, ARM64, x86, x86_64) действительно **присутствуют**, имеют правильную архитектуру ELF, **ZIP_STORED** и **4096-байтное выравнивание**. [PASS](https://github.com/manufact-test/nomusic/actions/runs/42623602723).
- `diagnose_emulator.py` — безопасная диагностика только категории запуска и имена библиотек, не полный logcat. Тесты разделяют оригинальный APK, LSPatch+CELIKOM и LSPatch **без** CELIKOM.

## Итог трёх независимых запусков (ключевой блокер)

| Проверка | Результат |
|---|---|
| Оригинальная #170gpr на Android11 x86 AVD с ARMv7-трансляцией | **PASS**: установлена, процесс активен 5/5 замеров. [CI](https://github.com/manufact-test/nomusic/actions/runs/42621833205) |
| Та же #170gpr, переподписана LSPatch, с CELIKOM | **NO-GO**: установлена, падает до модуля, `liblspatch.so` / `UnsatisfiedLinkError`, процесс 0/5. [CI](https://github.com/manufact-test/nomusic/actions/runs/42622523007) |
| Та же LSPatch-сборка вообще БЕЗ CELIKOM модуля | **NO-GO**: **тот же сбой** `liblspatch.so`. [CI](https://github.com/manufact-test/nomusic/actions/runs/42622723034) |
| Android11 x86_64 + ARM-трансляция, модифицированная | **NO-GO**: опять `liblspatch.so`. [CI](https://github.com/manufact-test/nomusic/actions/runs/42624416091) |
| Android13 x86_64 AVD | **NO-GO до запуска**: `INSTALL_FAILED_NO_MATCHING_ABIS`, исходная нативная библиотека `armeabi-v7a`. [CI](https://github.com/manufact-test/nomusic/actions/runs/42614243825) |

**Что можно заключить:** на проверенных x86-эмуляторах ломается **LSPatch native loader до запуска CELIKOM**, поэтому переписывать наш модуль по этим логам бессмысленно. **Нельзя** утверждать, что LSPatch не работает на настоящем ARM, пока его там не проверили. Static APK PASS ≠ runtime PASS ≠ Play Protect PASS.

## Следующий разумный этап

1. **Не тратить время на тот же x86 AVD без конкретного исправления загрузчика**. Проверить возможность отдельного **нативного ARM Android 13+** тестового устройства, Play Protect ON, без аккаунта/переноса данных владельца и без трогания его HONOR. Если нет доступного ARM-стенда, честно зафиксировать ограничение, а не выдавать фиктивный APK.
2. До установки определить управляемую подпись, процедуру резервирования/отката и проверку APK/сплитов. Важно: переподписанная `ru.yandex.music` **не обновляет** официальную поверх той же package ID; подмена подписи выключена. Никогда не удалять установленный Яндекс владельца ради эксперимента.
3. На настоящем ARM подтвердить **запуск модифицированного Яндекса**, загрузку libxposed и hooks, затем (на разрешённом тестовом треке) связь *точный track+edition → FileInfoDto → eed → родной декодер до prepare*; не собирать OAuth/токены/чужое аудио.
4. Лишь после runtime доказательства делать минимальный **single-native-player source selector** с оригинальным fallback, корректными codec/duration/Range/Seek, отсутствием «пшиков», и тестами Pause/Seek/Next/Radio на отдельных копиях. Проверка Play Protect обязательна и не заменяется CI.

**Не писать пользователю, что подмена уже работает, — не работает.** Ближайшая задача — завести реальную ARM тестовую среду или доказать альтернативную безопасную интеграцию; не переписывать с нуля, не возвращаться к WebView и двойному плееру.

## Документация по деталям

- `docs/android/ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md` — независимые тесты crash и ELF.
- `docs/android/ANDROID-NATIVE-YANDEX-ROOTLESS-HOOKLAB-2026-11-09.md` — сборка и Xposed-модуль.
- `docs/android/ANDROID-NATIVE-FILEINFO-GATE2-2026-11-09.md` — реальная структура получения аудиоисточника.
- `docs/android/ANDROID-NATIVE-GPR-VERIFIED-2026-11-09.md` — происхождение/подпись оригинальной #170gpr.
- `docs/android/NEXT-CHAT.md` — текущий указатель. Предыдущее длинное содержимое сохранено в Git на `be77237f70fdf783016eea8bc6d0b44ab8596e8f`.


## Дополнение: подготовка отдельного нативного ARM-стенда

Добавлен безопасный **read-only** `android/native-yandex-hooklab/probe_arm_device.py` и синтетические тесты. Исходный host #170gpr включает `config.armeabi_v7a`: тестовый Android 13+ должен **поддерживать 32-битный ARMv7 ABI (`armeabi-v7a`)**. Современный ARM64 с 64-bit-only Android не годится. Probe проверяет ABI/API, Google Play package, отсутствие установленного Яндекса и известную модель основного HONOR; не устанавливает и не изменяет приложения. Play Protect ON и статус *отдельного разрешённого телефона* не могут быть достоверно подтверждены adb и требуют визуальной проверки.

Оценён альтернативный CI: macOS ARM64 GitHub-hosted runner существует, но вложенная виртуализация ограничена, поэтому его нельзя выдавать за готовый Android 13 ARM device; настоящая ARM-виртуализация в cloud CI не доказана. Возможен частный ARM device farm, но перед передачей проприетарного перепакованного APK третьей стороне нужны отдельное согласование и учёт рисков. Все предыдущие no-go x86 результаты неизменны. Нативная подмена и запуск на ARM остаются неподтверждёнными.

## Без запасного телефона

Найден путь к удалённому физическому ARM-стенду вместо покупки или вмешательства в HONOR: Google Developer Device Platform (кандидат Samsung Galaxy A52 5G, Android 14) и Samsung Remote Test Lab. **ABI `armeabi-v7a` и Play Protect ещё не проверены**, перепакованный Яндекс в облако не передавался. План и ограничения: `docs/android/ANDROID-NATIVE-NO-SPARE-CLOUD-ARM-GATE-2026-11-09.md`.

## Официальный Яндекс на основном HONOR не удалять

Владелец явно отказался удалять официальную Яндекс.Музыку и терять музыку на тренировках. Параллельная копия возможна лишь при **новом package ID**, успешной проверке пяти split APK, manifest/provider/callback совместимости и отдельного clone-scope модуля. Готового APK нет. См. docs/android/ANDROID-NATIVE-PARALLEL-CLONE-GATE-2026-11-09.md.

## Актуальное доказательство от владельца: own ARM hook PASS (09.11.2026)

На HONOR 50, Android 13, успешно запущен независимый CELIKOM ARMv7 Hook Witness с реальным libxposed-модулем: `Native host: STARTED`, `Module hook armed: YES`, `onCreate intercepted: YES` (скриншот `Screenshot_20261109_184208.jpg`, 18:42). Таким образом, **rootless LSPatch/libxposed реально работает на ARM устройстве внутри собственного подписанного пакета**, в отличие от x86 AVD. Никакого запуска модуля в `ru.yandex.music`, декодирования или подмены звука это не доказывает. Оригинальная Яндекс.Музыка на HONOR не изменялась. Дальнейший фокус — совместимый параллельный native-клиент без конфликта пакета, иначе standstill; не переносить на HONOR переподписанный `ru.yandex.music`. Полный результат: `docs/android/ANDROID-NATIVE-ARMV7-OWNER-WITNESS-2026-11-09.md`.

## Короткий анализ альтернатив неподменённому APK — завершён 09.11.2026

CI [42649327835](https://github.com/manufact-test/nomusic/actions/runs/42649327835) проверил подписанный оригинал: внешние media browser / VIEW / provider интерфейсы присутствуют, но подтверждённый публичный контракт замены `FileInfoDto → eed → decoder` **не найден**. MediaSession, VPN+TLS, Accessibility, AudioPlaybackCapture не дают прямой инъекции в чужой native decoder. Конкурент ChromaSync-Mobile README тоже требует патчить совместимый Яндекс без root. Поэтому после timeboxed проверки возвращаемся к in-process patched native Yandex как приоритетному варианту. *Это не означает права удалять оригинальную Яндекс.Музыку с HONOR и не доказывает, что standalone app сможет незаметно подключаться к неподменённому APK.* Полные доказательства/ограничения: `docs/android/ANDROID-NATIVE-UNMODIFIED-APP-QUICK-HYPOTHESES-2026-11-09.md`.

## Owner-safe synthetic audio smoke, 09.11.2026

На основе подтверждённого физического own ARMv7 Xposed hook подготовлен третий отдельный пакет `pro.celikom.armv7loaderhost.audio`: тест pre-prepare source swap и Pause/Seek/Next/Fallback через единственный Android MediaPlayer. Собран и проверен CI: https://github.com/manufact-test/nomusic/actions/runs/42652387877 (SUCCESS), версия исходников `504cf3e6`. APK в личной Library ChatGPT, в основной установленный Яндекс ничего не внедрялось. Это **только самостоятельный синтетический лабораторный плеер, не Yandex**; реальный пользовательский аудиотест ещё ожидается. Не засчитывать это как исправление Seek/Next в настоящем Яндексе. См. `docs/android/ANDROID-NATIVE-ARMV7-AUDIO-SMOKE-2026-11-09.md`.

## Preflight известных регрессий (09.11.2026)

По диагнозам Test.31/70/74/76 подтверждён архитектурный риск двух игроков: ~3.1–3.3с задержка external Media3 у RASKOL/Дым и невозможность синхронизации паузы, акустический «пшик» даже с 160ms blending. В новой ветке `NativeSourceGate` устанавливает fail-closed правила единственного native источника до prepare, [CI 42658954205](https://github.com/manufact-test/nomusic/actions/runs/42658954205) 10 031 model assertions PASS; signed DEX downstream `Lged.a/Leed.a` [CI 42660229676](https://github.com/manufact-test/nomusic/actions/runs/42660229676) читается статически; optional read-only Xposed model-accessor hook добавлен (никакой подмены/чтения данных). Но **полноценная версия Яндекса ещё не собрана**, real decoder/Play Protect не подтверждены. См. `docs/android/ANDROID-NATIVE-REGRESSION-PREFLIGHT-2026-11-09.md`.
