# CELIKOM Windows — W48 true diagnostic 0.24.5 stage and owner-upgrade PASS (2026-11-10)

**Owner's actual verdict RED:** accepted mapped tracks on currently installed 0.24.4 trigger rapid UI Play/Pause oscillation and end paused/silent; ordinary untouched Yandex tracks work. This is NOT a CORS issue anymore: owner's 4.txt has 3/3 signed independent tiny MP3 HTTP 206 after W45. **No real native replacement audio ever confirmed.** Read `docs/windows/W48-REAL-PLAYER-DIAGNOSTIC-OWNER-FAIL-20261110.md`.

**Ready for one owner diagnostic trial (NOT audio-fix claim):** W48 internal unsigned same-app `0.24.5` package `CELIKOM-W48-PLAYER-DIAG-UNSIGNED` in https://github.com/manufact-test/nomusic/actions/runs/42776884046 (SUCCESS, artifact 13743709542). One-click ZIP in old CELIKOM 0.24.4 via **«Обновить CELIKOM»**, preserves owner account, auto native module refresh if version differs. Independent 0.24.4→0.24.5 same-app test https://github.com/manufact-test/nomusic/actions/runs/42777269209 **SUCCESS**: one app/uninstaller, DPAPI preserved, Yandex untouched. Genuine signed Yandex disposable host https://github.com/manufact-test/nomusic/actions/runs/42776853665 **SUCCESS**, original byte-identically restored; no account/audio verification.

**New observability:** Electron real media-start/pause, audible/silent, fast pause; passive CDP Media decoder error enum signals (fail-open), read-only redacted genuine file-info structure, `AUDIO_URL_RESOURCE_UNATTRIBUTED` instead of fake media request, recent 60m sorted export and explicit `ReplacementAudibleProof=NOT_AVAILABLE_FROM_PROBE_OR_MAPPING`; UI mapping message does not promise sound. Stage Node CI https://github.com/manufact-test/nomusic/actions/runs/42776927650 SUCCESS. Android/Test.50 untouched, W45 production backend unchanged. **If user exports fresh 0.24.5 TXT after one approved test, diagnose actual native decoder path and schema, then implement evidence-based fix.**

**Backup:** `backup/windows-w48-true-playback-diagnostics-owner-upgrade-ci-pass-20261110` @ `b8e772126c9f5498ca84f472422ee3960a251803`.

## Archived pre-W48 handoff

# CELIKOM Windows — W48 owner confirms audio RED, truthful 0.24.5 diagnostic staging (2026-11-10)

**Current first doc:** `docs/windows/W48-REAL-PLAYER-DIAGNOSTIC-OWNER-FAIL-20261110.md`. Owner actual Windows 0.24.4 sound verdict **RED:** approved substitute causes fast Play → Pause → Play → Pause, remains paused and SILENT; ordinary native Yandex tracks play. No need to ask him to repeat on unchanged 0.24.4. Morning W45 audio probes 3/3 HTTP206+MP3 bytes confirm CORS only, not genuine native playback. Old `MEDIA_REQUEST_SEEN` included independent own probe, old GUI `NATIVE_MAPPING_ACCEPTED` falsely suggested success.

**W48 source staged** on same Windows branch: Electron-native player started/paused + audible/inaudible events, explicit fast-pause, passive CDP Media-only decoder errors (no bodies or URLs, fail open), redacted genuine Yandex original file-info structure/codec/key-presence witness, `AUDIO_URL_RESOURCE_UNATTRIBUTED` instead of fake player-fetch counters, GUI honest label, 60-minute chronological diagnostic with typed engine/error evidence, new **0.24.5** same-app one-click internal **unsigned** diagnostic installer. W48 Node CI https://github.com/manufact-test/nomusic/actions/runs/42776927650 PASS; old W23 genuine Yandex disposable original restored https://github.com/manufact-test/nomusic/actions/runs/42776042891 PASS. **W20 latest 0.24.5 signed/audio status gate:** complete full CI check before giving artifact. This is an instrumentation upgrade, NOT a validated audio fix. Old Windows original and Android/Test.50 untouched. Backend W45 CORS remains active.

**Pre-W48 frozen source:** `backup/windows-w47-owner-audio-failure-before-truthful-diagnostics-20261110` @ `8d1096eecc038ff1bf8e8e163d0382a47cf3106e`.

## Archived W47 handoff

# CELIKOM Windows — W47 first owner report after W45 CORS, 2026-11-10

**Read first:** `docs/windows/W47-OWNER-POST-CORS-REPORT-20261110.md`. Owner sent morning `4.txt`, installed CELIKOM Windows 0.24.4 and matching native module. At 07:19 UTC three approved tracks (42498653, 85025192, 78608850) all show **real browser-context tiny audio probe HTTP 206 + audio/mpeg + MP3 magic**. No morning `AUDIO_PROBE_FETCH_BLOCKED`. W45 production CORS confirmed fixed. **No evidence yet that original Yandex decoder played replacement.** `MEDIA_REQUEST_SEEN/HTTP_UNVERIFIED` may include 32-byte independent probe itself; no real native player response status or confirmed audible Pause/Seek/Next. Await **owner's audible playback verdict** before modifying source or creating installer. If still silent, investigate true Yandex media fetch and file-info descriptor codec/key/iv/transport; do not confuse probed 206 with playback.

Working branch `experiment/windows-companion-integration-20261108`; W45 release backed up, Android and owner installed versions untouched. No new installer needed for CORS. W46 cross-audit includes Android native file-info risks.

## Archived W46 handoff

# CELIKOM Windows — W46 Android native cross-audit saved, 2026-11-10

**New cross-audit:** `docs/windows/W46-ANDROID-NATIVE-CROSS-AUDIT-20261110.md`. Inspected current Android native hooklab branch `experiment/android-native-yandex-fileinfo-hooklab-20261109`, latest Android native handoff/exit audit and genuine signed Yandex Android FileInfo static API evidence, plus older Media3 research. NO Android changes made. Key Windows next risk: W22 `toDownloadInfo` deletes `key/iv`, forces `codec/transport/gain`; genuine decoder may reject the synthetic descriptor. Do NOT copy original encrypted keys back blindly; first inspect original Windows native file-info/decoder shape and real signed Range 206 after W45 CORS. Android clone remains NO-GO (MAIN self-exits); no native Android audio success to transplant.

**Important:** W45 CORS is already LIVE, independent HTTPS W42 rerun PASS. Owner will test installed Windows 0.24.4 in the morning; no reinstall now. Avoid overwriting narrow `music-application://desktop` CORS when Android backend/0.3.93 catalogue migration releases. Keep Android/Test.50/server/Windows installer untouched during read-only research.

## Archived W45 production handoff

# CELIKOM Windows — W45 production CORS activated, 2026-11-10

**Сначала:** `docs/windows/W45-HYPHENATED-NATIVE-CORS-RELEASE-GATE-20261110.md`. Владелец разрешил W45 в текущем чате (“Делай”), live CI https://github.com/manufact-test/nomusic/actions/runs/42707502289 **SUCCESS**. Применена **одна точная вставка** в `Application.php` через новый неизменяемый релиз, не заменялся весь файл. Правильный Windows Yandex Origin `music-application://desktop` теперь получает CORS только для числового аудиомаршрута. Исходный SHA production `ec7f5d0d87978c823ece2dcfa2e76a021d4e2af09eb4f5c4d5fe52b6ab6c897e`; текущий ожидаемый `920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0`.

**Реальное HTTPS подтверждение после выпуска:** `OPTIONS 204` + ACAO native, bad-token `GET 403` + ACAO native, authorization/foreign Origin still blocked, legacy origins remain, health 200; независимый W42 rerun https://github.com/manufact-test/nomusic/actions/runs/42704976449 **SUCCESS**. Backup/private rollback `backups/w45-native-cors-d11481668524` + prior original release; automatic rollback was armed, not triggered. Owner Windows CELIKOM 0.24.4 + native module 0.24.4, original Yandex, Android/Test.50 untouched.

**Следующее:** владелец может проверить текущую 0.24.4 без переустановки: Stop/Start CELIKOM, при необходимости перезапустить Яндекс, одну подменяемую песню, обычную песню, паузу/перемотку/Next. Если не заиграет — новый TXT. CORS-фикс подтверждён, но **реальный audio decoder / key/iv/codec/transport и слышимый звук НЕ доказаны**. Не выпускать установщик наугад. Синхронизировать W45 CORS с canonical backend `feature/api-range` перед следующим полным выкладыванием серверного пакета, иначе возможен откат исправления.

**Резерв кода:** `backup/windows-w45-candidate-guard-ci-pass-20261110` at `b5785a24cb1b531e531101632f7553c673cbbb5c`.

## Архивная передача W45 до разрешения на выпуск



**Сначала прочитать:** `docs/windows/W45-HYPHENATED-NATIVE-CORS-RELEASE-GATE-20261110.md`. Рабочая ветка `experiment/windows-companion-integration-20261108`, основа владельца CELIKOM Windows **0.24.4** + native **0.24.4**, никаких переустановок.

**Точная подтверждённая причина W41**: настоящий подписанный Windows Яндекс отправляет **Origin: `music-application://desktop`**; backend разрешал `musicapplication://desktop` без дефиса. Native Chromium GET CORS blocked, MissingAllowOriginHeader. W41 genuine Yandex CI #42704012210 SUCCESS, vendor files + signature restored.

**Server stage-only fix**: exact hyphenated origin added ONLY to token-scoped audio path with unchanged HMAC/auth/range security. W30 stage CI #42704641987 SUCCESS; W42 production read-only #42704976449 confirms fix NOT active; W43 #42705379376 confirmed **full-file replacement NO-GO** (live PHP drift). W44 #42705730045 and W45 strict PHP candidate helper #42706261691 SUCCESS: one-hunk surgical live-copy fix, exact before/after SHA, all PHP tests, wrong path/re-patch forbidden.

**Release gate:** No production deployment made. Owner separate explicit permission needed for guarded one-file CORS update. Must create clone/backup, preserve old release, automatic rollback, LiteSpeed cache refresh, post-deploy original/current checks. NO new EXE. Real signed 206/audio, original Yandex Pause/Seek/Next and codec/key/IV requirements still unproven.

**W45 backup:** `backup/windows-w45-candidate-guard-ci-pass-20261110` at `b5785a24cb1b531e531101632f7553c673cbbb5c`. Android/Test.50, original owner Yandex install, extension, FOX/site, production backend/database untouched.

## Archived previous W40 handoff



**Current primary:** `docs/windows/W40-NATIVE-CUSTOM-SCHEME-CORS-20261109.md`. W40 native Windows genuine-Yandex read-only CI **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42701895118. The genuine native renderer's on-wire `Origin` is categorically `CUSTOM_SCHEME`, **not** approved `musicapplication://desktop`/`null`/known HTTPS; server denied fixed invalid-token GET as HTTP 403 with **no ACAO**, Chromium `MissingAllowOriginHeader`. Same invalid token from trusted Electron main produced 403 **with ACAO_NATIVE**. This is a *confirmed CORS mismatch for the invalid-token probe*, **NOT** proof that signed authorized audio 206 / original Yandex playback works.

**Backup:** `backup/windows-w40-custom-origin-cors-ci-confirmed-20261109` at `8d7fe03eb042d906c427a043cdf282af36a06851`. Changes exclusively disposable CI research/tests/docs. Original vendor EXE/ASAR bytes+signature restored. No owner installer, production backend, Android/Test.50, or native audio source metadata changes.

**Next:** identify exact trusted static origin scheme/host in isolated original Yandex without leaking values, design only a safe narrow signed-audio allowlist staging preflight, then real authorized 206/Range and original Windows file-info codec/key/iv decoder inspection. No wildcard CORS, no global security bypass, no proxy/open player. Owner CELIKOM 0.24.4 + native 0.24.4 remain installed; no manual action needed.

## Archived W40 start



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
