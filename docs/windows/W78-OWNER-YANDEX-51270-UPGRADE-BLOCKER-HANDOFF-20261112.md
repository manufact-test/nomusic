# W78 — ОСТАНОВКА: Windows 0.24.24 перестал подключаться после обновления (12.11.2026)

> **Статус на момент передачи: NOT FIXED.** Владелец НЕ подтверждал восстановление. Никаких новых установщиков/запусков обновления/затирания Яндекса без проверенной recovery-процедуры и его решения. Это задача восстановления уже работавшего Windows, **не планирование нового релиза и не переписывание продукта**.

## 1. Основа и точные точки GitHub

- Репозиторий: `manufact-test/nomusic`.
- **Эта документация / рабочая handoff-ветка:** `handoff/windows-w78-yandex-51270-upgrade-blocker-20261112`, создана из `798c70f8ba7c6fb466c82da12632f2658e0a50a6` (read-only checker V3, Windows PowerShell CI green). Итоговый backup и HEAD указать после записи.
- Исходный код проблемной W77: `experiment/windows-w77-kishlak-audio-path-20261112` (HEAD при передаче `818472b8031409f8ef20d342da67c99e009eb0f9`), установщик **0.24.24**, native host **0.24.24**. Финальный CI [43241899043](https://github.com/manufact-test/nomusic/actions/runs/43241899043), SHA256 EXE `E0E3A7BC3ED8D0C194471A2BCAECD88187A5A53567F76CD777346E2AD5AF4068`. **CI GREEN ≠ физический ПК работает.**
- Предшествовавшая работавшая у владельца версия: **0.24.23** (W76), native **0.24.23**; ветка `experiment/windows-w76-track-parity-audit-20261112`, CI [43209453291](https://github.com/manufact-test/nomusic/actions/runs/43209453291), EXE SHA256 `CC3711E3A2D7933838D429A2FF5F18C961E5C673115ED1989DC9B4FFCC453175`. Подготовленный rollback EXE в ChatGPT Library: `/CELIKOM/Windows/CELIKOM-0.24.23-W76-ROLLBACK.exe`. **Не запускать вслепую:** откат GUI не откатит изменённый Яндекс и может не пройти version gate.
- Резерв до W77: `backup/windows-w77-pre-kishlak-incident-20261112` → `9e4fd1d6e56e8e102c4a244a0e46fc6ffdf191fc`.
- Резерв собранной W77 (не рабочий эталон): `backup/windows-w77-02424-kishlak-deferred-recovery-ci-green-20261112`.
- Публичная запись об аварии: [GitHub issue #44](https://github.com/manufact-test/nomusic/issues/44).
- Наученная проблема: с W77 исправляли **потерянную подмену следующей песни** «Кишлак — Самый лучший день» (ID `102494056`) после `LOCAL_HTTP_TIMEOUT`. **Эта задача НЕ повод ломать уже работающую установку.** Расширение и сервер не трогать.

## 2. НОВЫЕ ФАКТЫ от владельца (самое важное)

Владелец скачал и установил W77 EXE поверх работавшего CELIKOM. После этого на экране: «**Файлы Яндекс.Музыки изменились. Подключение заблокировано**», в попапе «**Нужно подключить**», «**Файлы Яндекс.Музыки изменились. Подключение …**»; кнопка Start не подключает Яндекс. Владелец справедливо отмечает, что до этого всё подключалось; требуется устранить **регрессию**, а не планировать релиз через недели.

Точный файл владельческой read-only диагностики: загруженный в прошлый чат `CELIKOM-YANDEX-CHECK.txt`, 107 строк, `CHECK=CELIKOM_NATIVE_READ_ONLY_V3`, `UTC=2026-11-12T18:49:43Z`. **Не путать с синтетической Windows CI-диагностикой.** Показатели:

```text
APP_VERSION=0.24.24.0
YANDEX_EXE_VERSION=5.127.0.r22015925
INTEGRATION_ASSET_VERSION=0.24.24
YANDEX_DIR_EXISTS=True
CELIKOM_DIR_EXISTS=True
BACKUP_DIR_EXISTS=True
YANDEX_PROCESS_RUNNING=False
YANDEX_EXE_EXISTS=True
YANDEX_ASAR_EXISTS=True
OFFICIAL_51261_ASAR=False
MANIFEST=READABLE
MANIFEST_SCHEMA=1
MANIFEST_STATE=RESTORED
MANIFEST_ROOT_MATCH=True
ORIGINAL_EXE_BACKUP_HASH_OK=True
ORIGINAL_ASAR_BACKUP_HASH_OK=True
CURRENT_EXE=CHANGED_OR_UNKNOWN
CURRENT_ASAR=CHANGED_OR_UNKNOWN
HOST_PAIR_RESULT=UNRECOGNIZED_CHANGE_NO_AUTOREPAIR
ACTION=NO_HOST_FILES_CHANGED
CHECK_COMPLETED=YES
```

Последовательность в **реальных** companion-events:
```text
2026-11-12T15:36:11.937Z|GUI_STARTED
2026-11-12T15:36:16.593Z|NATIVE_UPGRADE_REQUEST
2026-11-12T15:36:22.622Z|NATIVE_RESTORE_OK
2026-11-12T15:36:24.167Z|NATIVE_UPGRADE_FAILED
2026-11-12T15:36:33.620Z|START_HOST_PREFLIGHT_BLOCKED
2026-11-12T15:36:49.051Z|START_HOST_PREFLIGHT_BLOCKED
```
Далее повторные `START_HOST_PREFLIGHT_BLOCKED`. Большое количество `NATIVE_STATE_RECEIVED` — шум, не доказательство работы музыки.

**Что это доказывает:** сохранённые оригиналы в backup проходят проверку целостности, manifest доступен и в состоянии `RESTORED`; **оба текущих файла Яндекса** (`Яндекс Музыка.exe` и `resources/app.asar`) сейчас **не совпадают ни с оригиналом, ни с записанной CELIKOM-подменой** из snapshot; установленная версия Яндекса **5.127.0**, тогда как W77 `NativeIntegrationManager` поддерживает только **5.126.1** и закреплённый SHA256 оригинального app.asar. После успешного восстановления старой интеграции попытка установки новой **провалилась**. Есть вероятное обновление Яндекса между состояниями/во время операции; **точный момент и источник изменения файлов пока НЕ доказан**. Нельзя утверждать, что новые файлы повреждены — это может быть новая официальная версия Яндекса. Также нельзя утверждать, что W77 сама перезаписала оба текущих файла: установщик копировал CELIKOM assets, а restore завершился OK.

**Нельзя** пытаться `NativeIntegrationManager.Install()` на состоянии `Changed` или делать форсированную замену «чтобы заработало». `NativeIntegrationManager.Restore()` также при `Changed` намеренно отказывается изменять файлы. Не удалять `NativeHost/snapshot`, `recovery.json`, старые backup, `session.dpapi`, не переустанавливать Яндекс или CELIKOM без решения и защищённого отката.

## 3. Подтверждённая дополнительная ошибка в доставке W77

`windows-companion/w20/installer/CELIKOM.iss` на обычной установке EXE обновляет файлы **только приложения CELIKOM** (включая `integration/host.cjs` и `renderer.js`), а [Run] исполняет `--complete-update` **только** с явным `/CELIKOMAPPUPDATE=1` и ранее записанным update ticket. Прямая установка EXE, которую предложили владельцу, **не эквивалентна** встроенному `AppUpdateManager` обновлению. В W77 Start видел старый native host и запускал `ConnectYandexAsync`:
```csharp
if (upgrading) {
  _bridge.SetEnabled(false);
  NativeIntegrationManager.Restore();  // succeeded (NATIVE_RESTORE_OK)
}
NativeIntegrationManager.Install();   // failed (NATIVE_UPGRADE_FAILED)
```
`Install` проверяет точную поддерживаемую версию и hash оригинала, допускает только `5.126.1`; `Inspect` различает `Active`, `Restored`, `Interrupted`, `Changed`, сравнивая реальные файлы с `recovery.json`.

**Изоляция корня:** есть две связанные, но не тождественные проблемы: (А) некорректный/неатомарный update path `Restore() → Install()`, который может оставить пользователя без интеграции при ошибке после успешного Restore; (Б) обновившаяся или неизвестная версия Яндекса 5.127.0, не проходящая старый preflight. **Что было первым, ещё не доказано.** Новому разработчику нужно устранять обе, не разрушая backup и пользовательские данные. Наивный откат до W76 не вернёт поддержки уже нового Яндекса автоматически.

## 4. Как продолжить работу — строго по приоритету

1. **Не просить у владельца новые скрипты, пока не использованы данные выше.** Изучить: `windows-companion/w24/Celikom.NativeInstaller/NativeIntegrationManager.cs`, `windows-companion/w21/Celikom.Recovery/PairRecovery.cs`, `windows-companion/w24/Celikom.NativeInstaller/NativeModuleIdentity.cs`, `windows-companion/w15/Celikom.Companion/MainWindow.cs` (Start, ConnectYandex, CompleteApplicationUpdate), `windows-companion/w15/Celikom.Companion/StartupHostPreflight.cs`, `windows-companion/w20/installer/CELIKOM.iss`; read `docs/windows/W77-KISHLAK-DEFERRED-RECOVERY-20261112.md`.
2. В отдельной ветке и с точным backup **воспроизвести** имитированную W76 → W77 установку с уже активной интеграцией, новой official Yandex 5.127.0, обновлением между Restore и Install, отказом в preflight. Прежний CI был на чистом disposable runner **без реально пропатченного Yandex**; его PASS не покрывал данный сценарий.
3. Разработать **безопасное transaction-like обновление**, которое не снимает старую работающую интеграцию до готовности и проверки нового состояния (включая версию Яндекса, полноту ресурсов, корректное восстановление при exception). При неожиданных файлах — не переписывать вслепую, сохранить backup и дать корректное понятное сообщение. При 5.127.0 — **сначала** проверить подлинность новой official версии и совместимость; не выдавать добавление `5.127` в allowlist за поддержку без тестов.
4. Подготовить безопасный способ восстановления **именно текущего состояния владельца** (manifest RESTORED, files CHANGED, Yandex 5.127.0). Не слать новый EXE как «точное исправление», пока не проверен этот state. Любые операции с файлами владельца — только после локальных read-only проверок и согласованного recovery-шага.
5. Покрыть тестами активную установку, готовую замену, неудавшееся обновление, внезапный Yandex auto-update, отмену, повторный Start, сохр. DPAPI, неприкосновенность оригинала, отказ без повреждений; только после green CI и аккуратного владельческого smoke QA вернуться к подмене Кишлака, Big City Life, 13 КАРАТ.
6. Писать владельцу коротко: **что установлено; что поменял; что проверить**. Без отчётов про релиз, двухнедельных прогнозов, бессмысленных повторных ZIP и просьб переустановить всё.

## 5. Диагностический инструмент / библиотека

После нескольких ошибок в собственной диагностике (PowerShell reserved `$Host`, упаковка старого CMD) выпущен **V3** read-only и проверен фактический ZIP round-trip через Library. Файл в Library: `/CELIKOM/Windows/CELIKOM-READONLY-CHECK-V3-20261112.zip`. Исходник V3 и Windows 5.1 smoke: `.github/scripts/windows-w78/CELIKOM-W77-READONLY-HOST-CHECK.cmd` и `.github/workflows/windows-w78-diagnostic-checker-smoke.yml` на branch `experiment/windows-w78-readonly-checker-validation-20261112`; CI [43254945785](https://github.com/manufact-test/nomusic/actions/runs/43254945785) PASS. **Не требуется скачивать его повторно: реальный отчёт уже получен.** Не путать этот ZIP с бракованным предыдущим архивом, который удалён из Library.

Непроверенный W77 EXE в библиотеке переименован `/CELIKOM/Windows/CELIKOM-0.24.24-W77-DO-NOT-INSTALL.exe`; **не распространять**. В библиотеке также есть W76 rollback EXE, но он не восстанавливает неизвестные файлы Яндекса сам по себе.

## 6. Критерий завершения

Реальный компьютер владельца запускает Яндекс и CELIKOM, видит `NativeInstallState.Active` и подтверждённое соответствие native modules; Start работает и получает реальный доступ, оригинальные файлы и backup сохранены. Только после этого — тест песни Кишлака (ID `102494056`, проблемный фрагмент около 1:00), 13 КАРАТ «ты» (ID `106040459`) и «Биг сити лайф» (ID `40371622`), без ложных обещаний «206 значит подмена звучит». Без физического owner QA считать **NOT FIXED**.
