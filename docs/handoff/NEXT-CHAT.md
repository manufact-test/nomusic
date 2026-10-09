# CELIKOM — актуальная передача в новый чат

Дата сверки: **2026-10-09**. Этот файл — краткое текущее состояние, а не новое продуктовое ТЗ. Архивные прежние сообщения handoff не использовать в качестве очередного действия.

## Авторитетные файлы и порядок

- **CELIKOM Master ТЗ MVP v1.5 (09.10.2026)** — основная спецификация, сохранена в Library /CELIKOM как CELIKOM_Master_TZ_MVP_v1.5_2026-10-09.docx (libfile_af7d67f2cc848191947f897a5606675c).
- **CELIKOM План работ MVP v1.6 (09.10.2026)** — последовательный roadmap 0–18, сохранён в Library /CELIKOM как CELIKOM_Plan_Rabot_MVP_v1.6_2026-10-09.docx (libfile_4841b3eb31f0819186f49ff9c42cfe4b).
- Развёрнутая передача: CELIKOM_HANDOFF_STAGE6_2026-10-09.md в Library /CELIKOM (libfile_9e57df9dff68819190bc0836ba16ee5a).
- Выполнение: ../project-status.md; операции: ../deployment/hostinger-stage5-operations.md; протокол: ../test-plans/CELIKOM-STAGE5-LIVE-AUDIO.md. Если план расходится с Master ТЗ, приоритет за Master ТЗ.

## Реальное состояние на 09.10.2026

- **Этапы 0–5 приняты в рамках owner-only private testing. Этап 6 В РАЗРАБОТКЕ: пакеты 6.1–6.6 реализованы и проверены, весь этап НЕ принят.**
- Extension **0.4.4**, активный Hostinger release **0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c** (обновлён по разрешению владельца; прежний 0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d сохранён для отката), независимый серверный API version **0.4.0**.
- API origin https://darkred-camel-588676.hostingersite.com. FEATURE_REPLACEMENTS=1, FEATURE_ANALYTICS=0. Данные и .env в приватном celikom/shared (audio, staging); backups/stage5 вне public_html.
- Первый одобренный владелецем MP3: Яндекс Track ID **144530503**, Replacement ID **1**, duration **180872 ms**. Расширение реально воспроизводит его через подписанные HTTP Range, MediaSource/blob и применяет fail-open.
- Владелец подтвердил **6/6 функциональных** + **6/6 стабильностных** сценариев на 0.4.4. CSP Яндекс Музыки блокирует прямой host audio.src; нельзя регрессировать к прямому src. В 0.4.4 исправлено аварийное отключение с возвратом оригинала.
- Не блокирующее UX-ограничение: после отключения и повторного включения расширения в chrome://extensions надо единожды обновить уже открытую вкладку Яндекс Музыки.
- Приватный snapshot .env/audio/SQL создан; файлы восстановлены в отдельный каталог, SQL — в disposable MySQL, рабочие данные не менялись. При повторном deploy SHA-256 .env/audio и counts 6 таблиц совпали; подписанный MP3 и Range проверены. Внешний 6-часовой мониторинг API активен.
- Это **не production readiness**: backup остаётся на Hostinger (нет независимого offsite), намеренный live outage и rollback не проводились; пользовательских uploads/админ-модерации, аккаунтов, trial, подписок, рефералов, Android playback ещё нет.

## GitHub / deployment

Repo https://github.com/manufact-test/nomusic
Ветка feature/api-range. **PR #6 открыт к develop, НЕ СЛИТ**, не сливать без прямого разрешения владельца. Проверять актуальный branch HEAD перед изменениями. Не трогать другие сайты Hostinger.
CI 0.4.4: https://github.com/manufact-test/nomusic/actions/runs/37900547793 (70 tests).
Repeat deploy: https://github.com/manufact-test/nomusic/actions/runs/37904158336.
Snapshot: https://github.com/manufact-test/nomusic/actions/runs/37903842547.
Restore: https://github.com/manufact-test/nomusic/actions/runs/37903962631.
Post-deploy integrity: https://github.com/manufact-test/nomusic/actions/runs/37904416817.
Signed audio: https://github.com/manufact-test/nomusic/actions/runs/37904551511.
Stage 6.4 library CI: https://github.com/manufact-test/nomusic/actions/runs/37916187759.
Stage 6.4 read-only Hostinger inspection: https://github.com/manufact-test/nomusic/actions/runs/37916411482 (1 Track, 1 AudioAsset, 1 TrackReplacement, feature on, analytics off).
Stage 6 CLI/runbook: ../deployment/hostinger-library-operations.md. Default library request: `{ "operation": "validate" }`.

Existing repository Actions secrets HOSTINGER_SSH_KEY, HOSTINGER_DB_PASSWORD are configured; do not request/reset/show them. Never expose beta token, signing key, private MP3, SQL dumps or signed URLs. PHP CLI 8.3 uses /opt/alt/php83/usr/bin/php. Use GitHub Actions for remote work; direct container SSH was previously restricted.

## Текущая разработка Stage 6 (09.10.2026)

- **6.1 accepted by CI:** tests on disposable MySQL for two exact Track IDs sharing one AudioAsset, pending and active selection; extension multi-installation cache fixture. Green Actions 37913118791.
- **6.2 accepted by CI:** transactional `LibraryManagementService`, approval/activation/disable, dedupe, token version bump; expected-active guarded activation added for 6.4. Green Actions 37913643635 and 37916187759.
- **6.3 accepted by CI:** restricted internal CLI wrappers: add-track, add-asset, link, approve, activate, disable. Green Actions 37914133541.
- **6.4 accepted for automation/read-only:** allowlisted GitHub Actions request workflow, pinned SSH, secret reuse, stale run refusal, replay-claim for writes, exact expected active mapping locked in MySQL transaction. Workflow validate run 37916327886 successful. Safe Hostinger inspect 37916411482 successful: **1 track, 1 asset, 1 mapping**, FEATURE_REPLACEMENTS=1 and FEATURE_ANALYTICS=0. No live DB writes or new music. The request was then returned to `validate` mode. No write operation has been exercised against production; Stage 6 is not accepted overall.

**6.5 accepted by CI:** server `ResolveCachePolicy` and /config + resolve expose matching bounded TTLs (positive 5–120s, negative 5–60s, defaults 120/15). ApiClient respects server TTL, validates response types, caps positive cache by signed audio expiry minus 30s and doesn't cache network failures; ReplacementController permits negative retries from 5s instead of forcing 15s. CI: https://github.com/manufact-test/nomusic/actions/runs/37917754208 — **75/75 JavaScript tests**, PHP TTL contract and MySQL integration passed. No server deploy or new music; active 0.4.4 installation is unchanged. This enables server-side library changes to appear on **subsequent resolve calls after TTL**, not forced mid-song hot swap.

**6.6 accepted by CI:** https://github.com/manufact-test/nomusic/actions/runs/37918863810 — 78/78 JavaScript tests; real disposable MySQL testing of one AudioAsset shared by two exact Track IDs via independent API instances, byte-exact HTTP 206/HEAD/416, CORS, signed tokens, isolated disable, real row-lock contention with two PDO connections and stale-active refusal, native Chromium signed Range audio and fail-open. No Hostinger deploy or new media. Commit 822b85107a24598a830d09c1f98874add2ade84d.

**Stage 6.7 server accepted for technical checks, browser acceptance PENDING.** Owner explicitly authorized server release upgrade. Backup 37919980695, isolated restore 37920125314, deploy 37920299328 to 0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c, post-deploy hash/count audit 37920496968, real signed Range audio 37920657691 — success. Private API-configured Chrome package 37920985864 is ready, ZIP checksum passed. **Exactly next:** owner downloads package and installs unpacked in an independent Chrome profile, enters existing private test token locally, checks two isolated installations and playback/stop/manual-original. 0.4.4 is still the displayed extension version, but the new package contains the 6.5/6.6 code; the old installed extension was NOT updated. No new music or mapping changes. Do not merge PR #6. Stage 6 not yet finally accepted.

Keep PR #6 OPEN against develop until user explicitly approves merge. Branch `feature/api-range` current HEAD must always be refreshed. Stage 6 server is active on release `0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c`; old release `0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d` is retained as rollback target. The owner's installed Chrome extension remains the older 0.4.4 build until locally replaced, while the new private build still reports version 0.4.4.

## First-message template

Продолжаем CELIKOM, завершаем этап 6.7. Master ТЗ v1.5, План v1.6. GitHub manufact-test/nomusic, feature/api-range, PR #6 не сливать. Сервер Stage 6 установлен по разрешению пользователя: release 0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c (Actions deploy 37920299328). Перед этим сделан snapshot 37919980695, восстановлен на отдельной MySQL 37920125314; после — env/audio hash + SQL counts audit 37920496968 и real signed MP3 HTTP 206 37920657691 прошли. Приватное расширение с уже настроенным адресом Hostinger создано Actions 37920985864 (ZIP SHA OK), но на ПК пользователя не установлено. Дальше провести приёмку в двух изолированных профилях Chrome для существующего Track ID 144530503 и несуществующего ID, controls/fail-open/TTL. API test token никогда не просить прислать в чат. Новые песни и связи не менять, не считать Stage 6 принятым без теста пользователя.

## 2026-10-09 — Chrome History hook recursion hotfix (owner validation pending)

Owner reported three `Uncaught RangeError: Maximum call stack size exceeded` entries in Chrome extension Errors, traced to `player/main-world-bundle.js` `celikomObservedHistory` around line 1044 and intermittent Yandex Music SPA blank `Application error` / frozen page when returning to an old tab. Root cause identified in `YandexMusicAdapter` lifecycle: wrapper used mutable `adapter.nativeHooks[name]` as its native target. If a third-party/Yandex wrapper retained CELIKOM's wrapper through unmount, on remount the registry could point back into the old wrapper chain and recurse. The source also used this mutable-hook pattern for media, fetch and XHR.

Fix [1d69906](https://github.com/manufact-test/nomusic/commit/1d69906aa04cf7704a89eab9342dd5d73ab936e0): each wrapper closes over its immutable original target and has a per-installation `lifecycle.active` flag; retained stale wrappers stay callable but no longer emit snapshots or inspect the network after unmount. Two regression tests reproduce third-party History wrap/unmount/remount and retained fetch/media functions. [CI 37926905183](https://github.com/manufact-test/nomusic/actions/runs/37926905183) green: **80/80 JS** plus PHP/disposable MySQL/native Chromium. [Hostinger-configured hotfix package 37927113445](https://github.com/manufact-test/nomusic/actions/runs/37927113445) assembled with valid ZIP SHA and exact private API origin; no server redeploy. Workflow/last documentation CI [37927119332](https://github.com/manufact-test/nomusic/actions/runs/37927119332) green.

**Next:** owner replaces files in existing unpacked CELIKOM folder, uses Reload in `chrome://extensions`, closes/reopens Yandex Music tabs, clears past Chrome Errors and exercises navigation, tab-background/foreground, play/pause/seek, Stop/Return original. A blank-page error in Yandex is a plausible consequence of History recursion, not conclusively attributed until owner reproduces or confirms gone. Stage 6.7 browser acceptance remains **pending**; do not merge PR #6 or change existing music/DB. Extension manifest version remains `0.4.4` to preserve established unpacked-install identity; the hotfix is distinguished by Git commit and artifact.
