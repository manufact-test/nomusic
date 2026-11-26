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

## W178 implementation and next owner candidate (26 Nov, follow-up)

**Changes made in main, but owner has NOT tested audio:**
- `3e6814c7281358b1ddd0a886b0b5d2c399974c99`: Windows-only narrow live-current-track catch-up for subsequent PLAYING/PAUSED queue entities that Yandex may have preloaded before interception. At most one authorized `adapter.prime` per observed current song/activation generation, and `reloadEntity("QUALITY_CHANGE")` only with a verified signed grant; never for an original-only track. W175 initial one-shot check retained. Added privacy-safe renderer `RESOLVE_QUEUED/RESOLVE_DEQUEUED/RESOLVE_REPLY_RECEIVED` and C# `RESOLVE_LOCAL_SESSION_MISSING`, `RESOLVE_SESSION_REFRESH_FAILED`, `RESOLVE_SESSION_CHANGED`, `RESOLVE_SERVER_NO_GRANT`, `RESOLVE_GRANT_REJECTED` distinctions. There are no exported URLs, tokens, account IDs, or response bodies.
- `52a1c03d10abec9be191d2bc95722003fdc6b7e8`: corrected W178 unit test separator before running CI.
- `4a807e9148f8d14b7a950047d522df06e7cbe585`: added native renderer/live-current W178 unit checks to the existing isolated FlokiNET Windows cross-build; changed diagnostic name from `RESOLVE_SERVER_NOT_FOUND` to neutral `RESOLVE_SERVER_NO_GRANT`. This distinction is necessary: `found:false` does not by itself prove absence of a catalog record.
- Isolated Floki native regression and .NET Windows Companion/UpdateSupervisor cross-compile: [run 45707188284](https://github.com/manufact-test/nomusic/actions/runs/45707188284) SUCCESS. Linux extension/server portable checks in [run 45707188311](https://github.com/manufact-test/nomusic/actions/runs/45707188311) SUCCESS; the subsequent Windows-hosted part failed before running steps because of runner allocation, not a failed application assertion.
- `28587670e9efda35c73eb3a49d9702d2d72b3b8c`: all three Windows version metadata bumped to **0.24.57**; new owner-only release trigger with P-256 sequence **4**, signed-release workflow defaults and trigger aligned. `approved:null` in customer manifest left unchanged; no public rollout.
- Signed release [run 45707797672](https://github.com/manufact-test/nomusic/actions/runs/45707797672) **FAILURE twice before ANY steps**. Protected Windows `prepare` job has `runner_id=0`, `steps=[]`, label `windows-2022`; `private_stage` and public `publish` skipped. No signed 0.24.57 EXE exists from this run; no owner site publication and NO new download link to provide. Do not relabel, reuse, or mutate previously signed 0.24.56 EXE, and do not send unsupported GitHub URLs.
- A new 0.24.57 Floki cross-build run `45707797544` was in progress at this documentation checkpoint. Check actual terminal status before asserting new version compile PASS. Floki isolated runner does not hold protected P-256 signing or root deployment secrets.

**Next mandatory steps:** Check terminal 0.24.57 Floki compile status. On recovery of trustworthy Windows-hosted runner, retry exactly [run 45707797672](https://github.com/manufact-test/nomusic/actions/runs/45707797672); inspect original signed `prepare`, `private_stage`, independent root publisher + full owner-auth HTTPS200 installer SHA before linking to `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.57.exe`. Do not issue that URL until verified. On owner install, test known mapped Yandex track 144530503 and ordinary/unmapped Next tracks, send fresh privacy-safe diagnostic to discriminate server no grant vs bridge queue vs decoder. Investigate reported broken API music-library admin at `https://api.celikom.com/admin/login` separately with owner-authorized server checks; previous no-step GitHub-hosted audit was not proof of failure. No changes to paid/Android/extension/Hostinger. Only after audible owner acceptance authorize customer release and real OTA test.

### Final source verification (26 Nov)

- Exact 0.24.57 source/metadata commit `28587670e9efda35c73eb3a49d9702d2d72b3b8c`: [Floki cross-build 45707797544](https://github.com/manufact-test/nomusic/actions/runs/45707797544) **SUCCESS**, including W178 native renderer tests and `dotnet build` for both Windows Companion and Update Supervisor. This is not an actual owner installer, and Linux pipeline's optional unsigned PE publish step was intentionally SKIPPED (no `[qa-exe]` flag).
- [Protected P-256 signing 45707797672](https://github.com/manufact-test/nomusic/actions/runs/45707797672) was retried a THIRD time; still FAILED before any steps, Windows hosted `runner_id=0`, `steps=[]`. No exact 0.24.57 signed installer, no verified owner publication, no link. Do not repeat runner retries endlessly or weaken signing isolation.

## W179 follow-up — public GitHub runner recovery and exact Floki admin route probe (26 Nov)

- Owner opened manufact-test/nomusic; GitHub API confirms private=false, default branch main. New current-main commit at this checkpoint: c336f9442cc6b1cb38423fe44ea128874633f089.
- Signed owner release [45707797672](https://github.com/manufact-test/nomusic/actions/runs/45707797672), attempt 4, now reaches GitHub Actions but is **WAITING on the protected windows-stable-production environment**. pending_deployments reports owner manufact-test can approve. This is the P-256 signing-secret gate, not runner allocation or a failed build. Approval must be by owner in GitHub UI; do not remove environment protection. Push-triggered run has no production-publish input, and windows-customer-stable.json remains approved:null.
- Current main Windows integration [45813153648](https://github.com/manufact-test/nomusic/actions/runs/45813153648): portable build job SUCCESS; inspect Windows job final state. Generic CI [45813153516] was still running at this checkpoint.
- Added .github/workflows/celikom-floki-api-readonly-audit.yml and .github/scripts/celikom-floki-api-readonly-audit.mjs at commit c336f9442cc6b1cb38423fe44ea128874633f089. Workflow [45813153575](https://github.com/manufact-test/nomusic/actions/runs/45813153575) SUCCESS. It made no authenticated requests and read no secrets:
  - Floki /api/v1/health 200, /api/v1/config 200.
  - /admin/login 200; form, CSRF, login, password inputs and login cookie present.
  - Anonymous /admin -> 303 /admin/login.
  - Anonymous /api/v1/auth/me and /api/v1/resolve -> expected 401.
  This proves route/form availability only, not owner login or admin actions/DB.
- **Correction:** the pre-existing .github/scripts/celikom-api-monitor.mjs uses https://darkred-camel-588676.hostingersite.com; previous green API monitor run [45759107905](https://github.com/manufact-test/nomusic/actions/runs/45759107905) checked Hostinger, not Floki. The new audit above is the first exact unauthenticated Floki API/admin-form proof in this thread.
- floki-maintenance-request.sh remains safe no-op. Do not claim production DB audit ran. Any DB/admin identity check requires a separate explicitly reviewed read-only maintenance payload.
- Playback remains unaccepted: 0.24.57 needs signed owner release, root Floki promotion + full owner HTTPS SHA, installation/listening, and fresh diagnostics before calling it fixed.


### W179 terminal CI state (26 Nov 11:45 UTC)

- Current-main Windows integration [45813153648](https://github.com/manufact-test/nomusic/actions/runs/45813153648): **SUCCESS**, including portable Linux package job and full Windows integration job.
- Generic CI [45813153516](https://github.com/manufact-test/nomusic/actions/runs/45813153516): **SUCCESS**.
- Exact Floki public API/admin form audit [45813153575](https://github.com/manufact-test/nomusic/actions/runs/45813153575): **SUCCESS**.
- Protected 0.24.57 signed owner release [45707797672](https://github.com/manufact-test/nomusic/actions/runs/45707797672) remains **WAITING** for owner approval of environment windows-stable-production; no installer has been created yet in this attempt.

