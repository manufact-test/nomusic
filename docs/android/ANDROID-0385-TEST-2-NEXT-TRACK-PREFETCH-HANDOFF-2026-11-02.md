# CELIKOM Android — handoff после CELIKOM Test 0.3.85-test.2 (2026-11-02)

> **Текущий приоритет владельца: звук в начале песен и при смене треков.** Исправление белого текста в форме авторизации уже включено в общий тестовый APK, но отдельной проверки/сборки текста больше не делать. Следующие диагностические файлы владелец предоставит в новом чате. Этот документ — точка продолжения, а не разрешение выпускать стабильную версию.

## 1. Три разные точки: НЕ ПЕРЕПУТАТЬ

| Назначение | Package / версия | Source / SHA | Состояние |
| --- | --- | --- | --- |
| **Неприкосновенный ОРИГИНАЛ** | `pro.celikom.nativeprobe`, CELIKOM `0.3.85`, versionCode **86** | `053b7d59beb53db5f30b942feba35e51a1ab256a` | Опубликованная стабильная версия; перемотка на HONOR **принята владельцем**. Ни исходник, ни OTA не обновлять. |
| **Первая контрольная CELIKOM Test** | `pro.celikom.nativeprobe.test`, `0.3.85-test`, code **86085** | `32a4afa7c381758502bf47d7b3facd200e74842a` | Владелец установил; звук в начале песен остался проблемным. APK SHA-256 `bf1fc8b39a08b3c1f5f5b2d1483f0fe0fb013bbd7041671867dea77e2b5e4bee`. Это **НЕ** оригинал. |
| **Последняя общая Test, требует прослушивания** | `pro.celikom.nativeprobe.test`, `0.3.85-test.2`, code **86087** | Функциональный commit `f3bc62b553275b3e3d38084a65d2eafedb5af889` | Signed APK и JSON receipt собраны и сохранены, CI успешна; акустически ещё **НЕ ПРИНЯТА**. |

Резервные GitHub-ветки проверены 2026-11-02 и остаются на исходных SHA:

- `backup/android-0385-honor-seek-accepted-20261102` → `053b7d59beb53db5f30b942feba35e51a1ab256a`
- `backup/android-0385-honor-seek-accepted-recovery-20261102` → `053b7d59beb53db5f30b942feba35e51a1ab256a`
- `backup/android-0385-test-first-owner-check-20261102` → `32a4afa7c381758502bf47d7b3facd200e74842a`

Сохранена также промежуточная **Test-only** `0.3.85-test.1` / code **86086**, built from `09b08fbaa9fb0e30e72bb0d1020c9ce857308772` (APK SHA-256 `c030111f0caac0b79fcd079690f26a353ce693ec43bbc6fe38ef6bc3a72395a7`): исправлены цвета полей нативной авторизации, но владелец не желал отдельной установки из-за косметики. APK/JSON сохранены в Library. Не путать Test-only код с оригиналом.

## 2. Последняя собранная APK и проверяемые контрольные данные

- GitHub branch: `feature/android-0385-intro-join-investigation-20261102`; PR [#37](https://github.com/manufact-test/nomusic/pull/37) **открыт, не слит**.
- **Функциональный SHA собранного APK:** `f3bc62b553275b3e3d38084a65d2eafedb5af889`. Следующая правка документации создаёт новый **docs-only HEAD**; не считать его другой проверенной аудиоверсией.
- Полный успешный GitHub Actions: [#41485796561](https://github.com/manufact-test/nomusic/actions/runs/41485796561). Автоматический `build-celikom-test` сработал **после** полной `native-android` валидации; вручную workflow запускать не нужно.
- GitHub Actions artifact `CELIKOM-Test-0.3.85-test.2-code-86087`, ID **13160669778**; содержит подписанную APK, receipt, verification.
- APK: `CELIKOM-Android-0.3.85-TEST-NEXT-TRACK-PREFETCH-SIGNED.apk` (8 759 449 байт); SHA-256 **`03387a8d2c1d08f89eb687490dc72b36e565ad8a4137960418f41267013acca9`**.
- `package = pro.celikom.nativeprobe.test`, label `CELIKOM Test`, `versionName = 0.3.85-test.2`, `versionCode = 86087`.
- Сертификат оригинальной подписи сохранён: SHA-256 **`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`**. Проверена APK Signature Scheme **V3** (V2 отсутствует согласно receipt), подписант соответствует оригиналу.
- OTA отсутствует (нет `UpdateCenter`/stable manifest), `REQUEST_INSTALL_PACKAGES` отсутствует; отдельный package/sandbox и launcher icon проверены.
- Full native host suite, cold-join experiment, **неизменённый** `check_0385_seek_baseline.py`, login-contrast contract, Android **API 36**, **D8**, упаковка и подпись — **PASS**.
- GitHub stable publisher **SKIPPED**; Hostinger не менялся; `stable.json`, `release-spec.json`, `release_contract.py`, `verify_release.py` не менялись.
- ChatGPT Library: каталог **`/CELIKOM/Android/Test/`**, три новых файла с уникальными именами: `CELIKOM-Android-0.3.85-TEST-NEXT-TRACK-PREFETCH-SIGNED.apk`, одноимённый `.verification.json`, и `CELIKOM-Android-0.3.85-TEST-NEXT-TRACK-PREFETCH-RECEIPT.json`. Старая Test 86085 и Test 86086 остаются для отката.
- Ссылки Library: [APK](https://chatgpt.com/library?file_id=libfile_f2dcb9f76f348191979b020500a4c6d3&account_id=personal), [verification](https://chatgpt.com/library?file_id=libfile_97570c4ba88081918eee2986de2a30aa&account_id=personal), [receipt](https://chatgpt.com/library?file_id=libfile_81d88cd0bd0081918558de9d03250004&account_id=personal).

## 3. Что именно изменилось и почему — звук, не текст

Владелец сообщил после первого Test: «всё осталось как было» на начале песен. Первоначальный experimental `exclusive_after_existing_clock_gate` (single-turn cold join вместо 160 ms blend) не решил субъективный дефект. Нельзя утверждать, что новая сборка тоже проверена: её только собрали.

Последняя пара личных диагностик (raw не коммитить):
- `CELIKOM-combined-20261102-172508.txt` — журнал первого Test 0.3.85-test/code86085.
- `SVID_20261102_172353_1.mp4` — видеозапись ~62.1 с со смешанным AAC mono audio.

Факты корреляции:
1. В журнале шесть `replacement_cold_join_experiment_start`. После границы нового MediaItem реальные пять переходов к замене происходили через **1.98–4.78 с**; full-file downloads длились **1.18–3.99 с**.
2. Шесть коротких фрагментов тишины/низкого уровня AAC совпадают со сменами песни; один начинается в момент перехода, когда CELIKOM для текущей песни **ещё не подключал эффекта и не запускал заменяющий декодер**. Это указывает на исходный переход Яндекса/системный аудиотракт либо запись; нельзя списывать все эти фрагменты на холодный join CELIKOM.
3. Другой возможный слышимый дефект — **поздний стык** при появлении заменяющего звука через 2–5 секунд. Журнал измеряет media transport/decoder position, но **не содержит PCM Яндекса и не измеряет speaker/output фазу**. Нельзя обещать отсутствие щелчков/неровностей только по CI.
4. Старый read-only lookahead видел следующий Media3 item примерно за 7–14 с до нескольких переходов, но `metadataComplete=false`, `authorizedForPrefetch=false`: заранее нужный файл не скачивался.

Изолированный новый **lookahead prefetch** в функциональном SHA `f3bc62b...`:
- Читает **только уже доступный Media3 timeline** следующего элемента; `Timeline.Window.getDurationMs()` используется, если `MediaMetadata.durationMs` отсутствует.
- Требует непустые title/artist, подтверждённый album ID из обложки, duration>0, непустой и non-placeholder window, включённый CELIKOM, действующий вход, current source playing, отличный следующий item и запас ≥3 с.
- Сначала старый публичный album API + строгий unique title/artist/duration (±1000ms); только unique candidate → backend resolve → разрешённый полный файл в **закрытый private bounded cache**.
- Prefetch не создаёт MediaPlayer, не управляет источником/усилением/AudioOwnership, не меняет seek/Pause/Resume/Next, не расширяет Android permissions, не подключает Yandex MediaBrowser/library.
- На реальной границе сохраняется новый server resolve; готовый файл берётся только при точном совпадении `catalogue ID | replacement ID | version | duration | MIME`. При ошибке — прежний безопасный original playback.
- Новые отчёты дают presence полей title/artist/album/duration/window placeholder для понимания, возможен ли prefetch на HONOR.
- Критическое ограничение: если Media3 next-item metadata по-прежнему неполные, эксперимент **не устранит** поздний стык. Не подменять ID по догадке; расширение доступа к данным Яндекса — только после отдельного согласования владельца.

Документы детализации: [NEXT-TRACK-LOOKAHEAD-PREFETCH](ANDROID-0385-NEXT-TRACK-LOOKAHEAD-PREFETCH-2026-11-02.md), [INTRO-JOIN INVESTIGATION](ANDROID-0385-INTRO-JOIN-INVESTIGATION-HANDOFF-2026-11-02.md), [HONOR SEEK FREEZE](ANDROID-0385-HONOR-SEEK-ACCEPTED-FREEZE-2026-11-02.md), [SIDE-BY-SIDE BUILD](ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md), [FIRST TEST CHECKPOINT](ANDROID-0385-TEST-APP-FIRST-OWNER-CHECKPOINT-2026-11-02.md).

## 4. Что делает следующий чат

**Сначала принять все новые диагностики от владельца, прочитать их полностью и сопоставить с кодом/этой контрольной точкой.** Не начинать новый аудиофикс без проверки.

1. Уточнить по файлам идентичность новой Test: `0.3.85-test.2`, code `86087`, package `.test`. Если диагностика снята со старой версии, явно отметить это и не делать вывод о новом prefetch.
2. Исследовать `source_next_readonly_observation`: `titlePresent`, `artistPresent`, `albumIdPresent`, `metadataDurationPresent`, `windowDurationPresent`, `durationSource`, `windowPlaceholder`, `metadataComplete`. Соотнести с `source_next_readonly_boundary`, `leadMs`, `prefetchState`.
3. Найти `source_next_track_identity_candidate`, `source_next_album_resolution`, `replacement_lookahead_prefetch_start/ready/failure/cancelled/promoted`, `replacement_full_file_experiment_start`, `replacement_prepared`, `replacement_transition_complete`. Отличить **prefetch cache hit** от обычного late download.
4. Свести временну́ю шкалу new-item boundary → metadata resolve → authorization → full-file download/cache → MediaPlayer prepare/prewarm → clock gate → owner grant, затем сопоставить с видео/AAC. Отдельно оценить краткий original gap до join и сам join после скачивания. Без PCM и атрибуции к динамику не объявлять акустическую причину доказанной.
5. Объяснить пользователю конкретно, что подтвердилось/не подтвердилось. При следующем изменении минимально локализовать аудиоэксперимент только в Test branch, добавить regressions, запускать общий host suite, **неизменённый** seek guard, API36/D8, автоматический Test artifact и проверку APK/signature/SHA. Следующий Test versionCode должен быть **>86087**. Никакой отдельной тестовой APK для текста.
6. Владелец **не должен снова проверять принятую перемотку, Pause/Resume** без объективно обнаруженного regression. Для нового звукового теста держать Яндекс Музыка **«Плавный переход» ВЫКЛ.** Не запускать одновременно оригинал и Test против одной Yandex сессии.
7. Проблема старта песен **ОТКРЫТА**, принят только seek, а новая Test сборка **технически валидна, но на HONOR ещё не подтверждена**. После owner-audio acceptance можно отдельно возвращаться к проверке `Плавного перехода` Яндекс Музыки.

## 5. Абсолютные запреты

Не менять stable `pro.celikom.nativeprobe` 0.3.85/code86 и его source SHA; `stable.json`, stable release spec, release contract, `verify_release.py`; не запускать stable publisher/Hostinger публикацию, не merge PR #37, не менять backup refs/подпись, принятые seek/Pause/Resume/Next. Не просить повторять уже выполненные проверки. Текущая Test версии 86087 и её receipt — новый **тестовый**, а не оригинальный чекпойнт.
