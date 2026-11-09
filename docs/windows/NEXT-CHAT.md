# CELIKOM Windows — актуальная передача W40, 2026-11-09

**W39 verified:** read `docs/windows/W39-NATIVE-ORIGIN-CLASSIFICATION-20261109.md`. Actual original Yandex `NATIVE` renderer sends an `Origin` categorized `UNLISTED_OTHER`, HTTP 403 response has `ACAO_ABSENT`; Chromium records `MissingAllowOriginHeader`. Trusted main request with deliberately invalid token still sees `MAIN_HTTP_403`+`MAIN_ACAO_NATIVE`. CI #42700805271 and post-test-fix #42701221204 SUCCESS. Original EXE/ASAR were restored to verified originals.

**W40** only narrows the previously unknown Origin to a safe scheme family without logging the actual value. CI https://github.com/manufact-test/nomusic/actions/runs/42701895118 — check verdict. Pre-W40 backup `backup/windows-w39-actual-native-origin-cors-evidence-20261109` at `805a6142fb0055311b61609315fa0ed99caf72b8`. No new installer or native audio fix. No backend changes without proof; avoid generalized permissive CORS.

**Owner** 0.24.4 + native module 0.24.4 stay installed. No TXT/reinstallation needed. Android/Test.50, site, production, extension not touched.

## Archived W39 transfer



**Главное:** `docs/windows/W39-NATIVE-ORIGIN-CLASSIFICATION-20261109.md`, затем W38/W37/W36/W35.

W38 настоящая Windows Яндекс-Музыка (CI #42695804499) доказала в своём `NATIVE` renderer: `CDP_LOAD_FAILED_CORS` с точным `MissingAllowOriginHeader`. Trusted Electron main для **намеренно INVALID токена** получал `HTTP_403` / `ACAO_NATIVE`. Видна настоящая транспортная проблема контрольного запроса; **реальный подписанный 206 и аудиодекодер всё ещё не проверены**.

W39 проверяет категории реального outgoing `Origin` и returned `Access-Control-Allow-Origin` по passive CDP. CI https://github.com/manufact-test/nomusic/actions/runs/42700903189 — проверь окончательный результат. Не изменяй PHP/server, настройки security Яндекса, key/iv или codec до однозначной проверки причин. W38 backup `backup/windows-w38-native-cors-missing-acao-confirmed-20261109` at `ec7b0ad7a264612728fd4f1af99d5bdc18c58bfc`.

Owner `0.24.4` / module `0.24.4` сохраняются. Нет нового установщика/пользовательской диагностики. Android, Test.50, расширение, production не трогать.

## Archived W38 transfer



**Сначала:** `docs/windows/W38-NATIVE-CORS-ENUM-20261109.md`, затем `docs/windows/W37-NATIVE-CDP-BOUNDARY-20261109.md` и W36/W35.

**Доказано:** W36 CI #42693758356 получил `NATIVE_FETCH_BLOCKED_TYPEERROR` в настоящем оригинальном renderer при `MAIN_HTTP_403`; W37 CI #42694895709 пассивно обнаружил `CDP_LOAD_FAILED_CORS` на этом **намеренно invalid-token** запросе. В обоих случаях original signed EXE/ASAR restored. Точный код CORS (preflight vs Origin/headers etc.) ещё выясняется в W38 CI #42695804499. Do NOT change backend or native codec/key/IV before evidence.

**Backup:** `backup/windows-w37-native-cdp-cors-confirmed-20261109` at `f1e33c534d7aa1f5e7ea7c1ae7aa089945d14927`. Owner CELIKOM Windows 0.24.4 + module 0.24.4 unchanged and stays installed; no new installer or TXT necessary. Android/Test.50 untouched.

## Archived W37 transfer



**Новая передача:** `docs/windows/W37-NATIVE-CDP-BOUNDARY-20261109.md`. W36 genuine native renderer failure independently verified in SUCCESS CI #42693758356: `NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_NONE` vs trusted Electron main `MAIN_HTTP_403` + `MAIN_ACAO_NATIVE`. Vendor original bytes/signature restored. **Do NOT claim CSP specifically, audio transport fixed, decoder compatible or audible substitution.**

**Accepted W36 backup:** `backup/windows-w36-native-renderer-fetch-blocked-ci-pass-20261109` at `474290941f2d4ea10db3a75adfc07683669b1515`.

**W37 CI-only:** passive Chromium CDP Network/Log classification on approved native view, no interception/security bypass/owner changes. Run https://github.com/manufact-test/nomusic/actions/runs/42694895709 — check final status and filtered categorical evidence before any follow-on code. If inconclusive, no installer.

**Owner** keeps Windows CELIKOM 0.24.4 + matching native 0.24.4. No reinstall, no re-export TXT required now. Android/Test.50, extension, Yandex account, live backend/production all untouched.

## Archived W36 transfer



**Новое W36 (CI-only, не выпуск):** изучи `docs/windows/W36-ISOLATED-RENDERER-BOUNDARY-20261109.md` перед W35/W34/W33. Резерв `backup/windows-w36-pre-renderer-boundary-fix-20261109` at `d999ac40ccc80c21f82ce7c5014ec6976a4cbb43`.

Исправлена именно временная/событийная недоработка W33 genuine-Yandex CI-only диагностики: ждать approved Yandex `dom-ready` и проверять ответ invalid-token GET из настоящего renderer против Electron main, с редактированными категориями ошибок. CI: https://github.com/manufact-test/nomusic/actions/runs/42691438851 (проверить финальный verdict). Отдельно unit tests на readiness/retry и обычный W23 native smoke, без подмены аудио.

**Владелец:** CELIKOM Windows `0.24.4` + native module `0.24.4` остаются установлены, обновлять/переустанавливать **ничего не нужно**. Исходная проблема — 4/4 `AUDIO_PROBE_FETCH_BLOCKED`, реальной подмены не доказано. В W36 не меняли ни `toDownloadInfo`, ни backend, ни Android, ни аудиопроигрыватель. Пока signed 206 и native decode не доказаны, не выпускать installer.

## Сохранённая передача W35



**ГЛАВНОЕ:** продолжать проект, не с нуля. На компьютере владельца CELIKOM 0.24.4 + native module 0.24.4 совпадают (owner TXT 3.txt), но подменное аудио моментально останавливается. Новая установка сейчас НЕ нужна. Никакой аудиоподмены в оригинальном Windows Яндексе ещё не подтверждено.

**Рабочая ветка:** `experiment/windows-companion-integration-20261108`. Последний HEAD бери из ветки (документация W35 — конец этого этапа). Независимый backup: `backup/windows-w35-pre-final-handoff-20261109` at `a62b969d21236b94ea07b9d5b433495c2ea6802e`.

**Читай по порядку:** 
1. `docs/windows/W35-HANDOFF-AFTER-ANDROID-REVIEW-20261109.md` — полный статус, следующий порядок действий, все ограничения.
2. `docs/windows/W34-ANDROID-CROSS-AUDIT-20261109.md` — выводы из мобильной ветки и осторожности по file-info/криптографии.
3. `docs/windows/W33-OWNER-0244-AUDIO-FETCH-BLOCKED-20261109.md` — последняя реальная диагностика, тесты CORS/CSP и ограничения CI.
4. `docs/windows/W32-OWNER-EASY-UPDATE-20261109.md` — уже решённое обновление из ZIP и отображение версий.
5. `docs/windows/W35-START-NEXT-CHAT-20261109.md` — готовое первое сообщение следующему чату.

**Владелец:** `AppVersion=0.24.4.0`, `NativeModuleVersion=0.24.4`, `NativeModuleMatchesApp=true`. Треки без подмены играют. 4/4 approved audio probes: `AUDIO_PROBE_FETCH_BLOCKED`, HTTP/MIME/decoded audio не подтверждены. CORS live серверной audio-route работает; публичный web-CSP Яндекса не допускает частный аудиодомен, но **точный native desktop CSP не доказан**. CI-only запрос в genuine Windows Yandex #42682820621 был inconclusive; обычный smoke #42682821206 SUCCESS и оригинальные vendor-байты восстановлены.

**Android cross-check:** read-only latest observed `experiment/android-native-yandex-fileinfo-hooklab-20261109` HEAD `36ca37bd0ce1e37cea1bc005789b0a970cbe6464`; Android DTO has urls/codec/key/gain/r128; Windows `toDownloadInfo` removes `key/iv` and overwrites codec/transport/gain → potential separate native-decoder mismatch after transport is addressed, NOT proof. Latest Android CI #42688277066: **unmodified original emulator app process alive**, cloned app fails classloading (`YMApplication` hint); still NO Android native audio or login proof. No changes to Android.

**NEXT:** debug Windows actual signed original renderer invalid-token fetch vs trusted main at correct `dom-ready`/approved event **in disposable CI only**; do not modify owner installation. After transport is proven, inspect actual Windows original file-info/decoder and implement narrow fail-safe single-source solution. Never ship another EXE based on SOURCE_MAPPED alone. Android/owner Yandex/backend/production/extension/Test.50 untouched.

**История:** long previous `NEXT-CHAT.md` preserved as `docs/windows/NEXT-CHAT-ARCHIVE-BEFORE-W35-20261109.md` and in Git history. W34 owner handoff preserved. No actual audio fix claimed.
