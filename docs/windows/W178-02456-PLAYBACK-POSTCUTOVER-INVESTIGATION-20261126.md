# W178 — фактическая диагностика установленной CELIKOM Windows 0.24.56 (26.11.2026)

## Результат
На момент записи аудиоподмена НЕ восстановлена, нового EXE нет. Владелец прислал свежий экспорт W54 `AppVersion=0.24.56.0`, GeneratedUTC=2026-11-25T21:22:16.4012815Z. Не путать с предыдущим W54 для 0.24.55.

Диагностика текущей сессии:
- `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted/Enabled/SignedIn=true`: это локальное состояние, не серверная авторизация.
- `21:21:41.020 RESOLVE_REQUEST track=18697033`; `21:21:41.106 RESOLVE_MISS track=18697033`; `21:21:41.109 LOCAL_RESOLVE_REPLY`; `21:21:41.110 GRANT_MISS`; `21:21:41.112 GRANT_DELIVERED`. Последнее означает доставку в renderer результата (null), **не подписанного audio grant**.
- `21:21:41.645 NATIVE_INITIAL_SOURCE_REVALIDATE track=18697033`; `21:21:41.646 RESOLVE_START track=18697033`. До конца окна (~34 сек) нет `RESOLVE_REQUEST`/завершения этой второй попытки, `RESOLVE_TIMEOUT`, `RESOLVE_BACKGROUND_TIMEOUT`, `NATIVE_INITIAL_SOURCE_RELOAD`, `NATIVE_FILEINFO_REQUEST` или `SOURCE_ACTIVE_REPLACEMENT`. Важна не только API-цепочка, но и **неподтверждённое извлечение повторного запроса из renderer-очереди native host**.
- `PlayerNetworkRequestObserved=false`, `NativeMediaUrlExactMatchObserved=false`, `PlayerAudibleEventObserved=false`; сеть/decoder/audio не доказаны.
- Track 18697033 НЕ равен контрольному одобренному 144530503 («Ау»), для которого предыдущая независимая проверка API двух тестовых пользователей подтвердила signed grant и HTTP206. Ни статус БД для 18697033, ни DPAPI-сессия самого владельца новым файлом не доказаны.
- `YandexVersion=unknown`; `NATIVE_UPGRADE_OK` не устанавливает фактическую версию Yandex. `STABLE_UPDATE_CHECK_FAILED` — самостоятельная линия OTA, не доказанная причина audio failure.

## Проверка исходников
GitHub main перед анализом: `fb5e27d2c1e942a276d456174c7b35f56f118bce`. Последний personally accepted 0.24.54: W174 / `aa713b99824f20abbe7c239bf06e356cf3f7f367`.
Проверка точных Git blob SHA в исходниках 0.24.54 vs current main:
- `w23/host.cjs`: один и тот же `9fe9e031d7fd3f22a5e3b65562f29dc45654164f`.
- `w22/native-resource-adapter.mjs`: один и тот же `e3bfdc3ed579709c342c3ae87e2e83510e35826e`.
- `w15/BridgeServer.cs`: один и тот же `61a4c2d92b58d6087ead0cbdfdf86d29a121c62d`.
- `NativeIntegrationManager.cs` и `OfficialYandexCatalog.cs`: побайтово идентичны.
- `CelikomApi.cs` после переезда изменяет default API origin, мигрирует только точный прежний origin в DPAPI и сохраняет access/refresh token; `renderer-entry.mjs` содержит новый W175 3.5s revalidation.
- `BridgeServer /v1/resolve` записывает `RESOLVE_MISS`, если `ResolveAsync` вернул null. `CelikomApi.ResolveAsync` вернёт null как при `found:false` от API, так и при неуспешном refresh после 401, либо при отклонённом `GrantValidator.FromResolve` ответе. **По W54 эти причины неразличимы**. Не списывать всё на отсутствие каталожной записи.
- `w23/host.cjs` обрабатывает queued-запросы через `tick(view)` после `__celikomBridgeNativeDrain`. Второй revalidation `RESOLVE_START` не дошёл до видимого локального bridge resolve в записанном окне — проверить состояние выбранного view и queue/abort/reload, не переписывать audio архитектуру.

## Проверка production/админки и фактическая блокировка
Владелец отдельно утверждает, что «даже админ не работает». Предыдущий cutover `#45597121291` и read-only пробы подтвердили API health/config и наличия admin route, но **НЕ доказывают сейчас работоспособность входа, интерфейса и пользовательских действий владельца**. Не утверждать, что админ исправен.

Создана резервная точка `backup/windows-main-pre-w178-audio-audit-20261126` на `fb5e27d2c1e942a276d456174c7b35f56f118bce` (без изменения main).
Read-only одноразовый audit request (live DB `findActive` для 18697033 и 144530503, активные флаги и сессии, admin+API HTTPS) был помещён в `.github/deploy/floki-maintenance-request.sh` commit `9a9c69c2a828a33b12c8367e6463d27251d1d760`, triggering GitHub Action `#45705603699`. Две попытки `run_attempt=1/2` завершились failure **до первого шага** (jobs steps=null, лог недоступен), поэтому ни один серверный SQL/HTTP probe не исполнялся; данных об API/DB не получено. Запрос обезврежен восстановлением прежнего safe-noop `61d175885531c00d7c6741d31d579e5f01ea080b`. Его maintenance run `#45705808033` тоже failure до шагов. Не пытаться обходить изоляцию self-hosted CI или давать ему root/SSH secrets.

Попытки HTTP из инструментального контейнера не прошли из-за отсутствия внешнего DNS, а browser web fetch API/сайта недоступен через текущий инструмент; это НЕ доказательство отказа целевых сайтов.

## Продолжение строго по делу
1. После восстановления санкционированного отдельного административного канала провести read-only production аудит точной записи 18697033, известной 144530503, active session/grant (без вывода токенов), admin runtime. Нужны независимые `found=false` vs `401 refresh` vs `grant invalid`, и current Yandex version.
2. Одновременно проследить, почему второй renderer background `RESOLVE_START` не привёл к новому `RESOLVE_REQUEST` и не завершился timeout: выбранный active view, lifecycle, async queue pump, navigation, renderer/host diagnostic drain.
3. Только после локализованного разрыва — узкое исправление, реальные regression tests + CI, новая уникальная версия >0.24.56 с signed sequence>3, private Floki owner publisher/real HTTPS SHA verification. Не выдавать green CI за проверку звука.
4. `.github/release/windows-customer-stable.json` остаётся `approved:null`; public channel 0.24.55, 0.24.56 отвергнута. Владелец примет только после прослушивания. Не трогать Android/extension/paid/Hostinger.
