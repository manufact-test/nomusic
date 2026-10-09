# CELIKOM — актуальная передача в новый чат

> **START HERE — 09.10.2026, Stage 8 deployed, owner acceptance 8.7 pending.** Historical Stage 6→7/7→8 sections below are archival and not current work orders. Requirements: Library Master TZ MVP v1.5 Appendix G, Work Plan MVP v1.6 Section 13. Technical evidence: [status](../project-status.md), [Stage8 runbook](../deployment/stage8-admin-acceptance.md). Don't repeat Stage 7 manual tests. PR #6 stays OPEN/UNMERGED; issue #7 remains OPEN.

## Latest — Stage 8.7 two-step moderation UX shipped (09.10.2026)

Owner requested: pressing approve/reject must first open a separate confirmation panel; approval has a mandatory rights/audio checkbox and optional note; rejection has a required reason selector (duplicate/wrong track/bad quality/rights/other) and optional note except custom reason requires text. The final confirm button is the only POST. Existing protected moderation transaction and audit semantics preserved; last decision and comment rendered per track and in audit. Implementation deployed at `0.4.4-8fdd303cefff1c25a8a6958ef04b8e5f56e6c500`, [CI](https://github.com/manufact-test/nomusic/actions/runs/37994628141), [backup](https://github.com/manufact-test/nomusic/actions/runs/37994689194), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37994790977), [deploy](https://github.com/manufact-test/nomusic/actions/runs/37994917008), [post-deploy audio/data audit](https://github.com/manufact-test/nomusic/actions/runs/37995105785) PASS. NO real approvals or rejection performed. Next step **owner checks UI manually**; do not declare Stage 8 accepted until owner confirms. PR #6 / Issue #7 remain OPEN; Stage 10 mandatory public `Предложить песню` beside upload stays in roadmap. Do not update master DOCX until a handoff is requested.

## 2026-10-09 latest — Stage 8 mint-green admin UI owner review

The owner approved the Stage 8 dashboard design/refinement. It has been **deployed** to Hostinger in immutable release `0.4.4-1e1460437d3410192802a8c9310ea7e7de9e7cc1`; [gated deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/37990431204), [predeploy full snapshot](https://github.com/manufact-test/nomusic/actions/runs/37989881372), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37990008446), [post-deploy read-only integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37990757090) all PASS. CI with added Admin metadata/paging tests: [37989681564 PASS](https://github.com/manufact-test/nomusic/actions/runs/37989681564). CI and Stage5 audit workflow MySQL image switched from Docker Hub to verified official public ECR mirror after upstream pull failures; test coverage NOT removed.

Design: light background, mint accents matching `#66e0bf` Chrome extension (not exhausting black+neon); Russian status labels, compact header with download/logout, mobile-responsive audio cards; duration min:sec; technical metadata collapsed; 10/25/50 entries with numeric paging and bounded SQL on uploads, requests, reports, and audit. Existing fixture `celikom-ci` displayed as synthetic test item. Old #1 track has no verified artist/title in DB; **do not invent metadata or touch its approved audio**. The owner can use protected `Уточнить название и исполнителя` after verifying Yandex Track ID; audited DB tracks.artist/title change only, CSRF+role/Track ID guarded.

Next: owner opens `https://darkred-camel-588676.hostingersite.com/admin/login`, checks actual UI, filters 10/25/50, sections, private MP3 playback, logout. **Do not click approve/reject/disable on real pending** without actual rights review. Stage 8 owner manual acceptance 8.7 still OPEN. Stage 10 mandatory `Предложить песню` public button remains committed product requirement. PR #6 OPEN/UNMERGED; Issue #7 OPEN. Do not modify master DOCX until next handoff, and do not repeat accepted Stage7 manual tests.

## Current next action: Stage 8.7 owner login/acceptance (not Stage 8 implementation)

Stage 8 code and additive `003_admin_moderation.sql` **deployed** to Hostinger with `FEATURE_ADMIN=1`, `FEATURE_OWNER_REPORTS=0`, public uploads OFF. URL: `https://darkred-camel-588676.hostingersite.com/admin/login`, login `owner`. The generated password is **not** in GitHub or conversation: owner can view it through private Hostinger File Manager/SSH in `celikom/shared/stage8-owner-login-once.txt` (0600, outside public_html). Delete this one-time plaintext copy after successfully securing admin access; SQL stores only password hash. PR #6 still open, Issue #7 still open. Existing owner-upload credential was not rotated.

Verification evidence: [predeploy backup](https://github.com/manufact-test/nomusic/actions/runs/37984859454), [predeploy restore](https://github.com/manufact-test/nomusic/actions/runs/37985091060), [deployment PASS](https://github.com/manufact-test/nomusic/actions/runs/37985244995), [original-audio/config/data audit PASS](https://github.com/manufact-test/nomusic/actions/runs/37985609247), [owner bootstrap / HTTPS login 200 and no-cookie audio 403 PASS](https://github.com/manufact-test/nomusic/actions/runs/37985814317), [16-table postbootstrap snapshot](https://github.com/manufact-test/nomusic/actions/runs/37985992296) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37986120772). These are **automated gates**, NOT owner manual UI approval. Never change the approved #1 replacement or activate real pending #3 or synthetic #2 without explicit rights review.

Owner checks login, two separate queues, authentic pending audio preview, status filters, audit and logout. Prefer using a separately authorized synthetic fixture for status-change workflows instead of moderating the real tracks. Follow [Stage8 acceptance](../deployment/stage8-admin-acceptance.md). After owner 8.7 PASS, close Stage8 and proceed Stage9 in proper order. **Mandatory MVP** Stage10: public `Предложить песню` button beside `Загрузить версию`, NO MP3 and NO rights checkbox, strict current Track ID; backend queue already exists. Do not forget it. User authorized self-directed, guarded technical maintenance/deploys with backup/rollback, not blind irreversible moderation or credential disclosure.



## Что завершено

- **Stage 7 ПРИНЯТ владельцем** по результатам реальной Chrome/Hostinger загрузки и безопасных автоматических тестов; не требовать повторной приёмки косметических правок.
- Сохранена приватная pending запись: **«Вспышка» — Легенды Про, CENTR**, Yandex `38436680`, Replacement **#3**, приватное MP3 6 486 945 байт с подтверждённым hash, `is_active=0`. Есть отдельная CI синтетическая запись `799133075` / Replacement #2 pending; эти записи нельзя одобрять без Stage 8 модерации. Пользователь также показал зелёный результат для «Животные» — Скриптонит; это пользовательское наблюдение, НЕ отдельный DB-аудит.
- Старый approved track `144530503` / Replacement #1, duration 180872ms, сохраняется. Live backend Hostinger `https://darkred-camel-588676.hostingersite.com`; последняя атомарная Stage 7 server-hotfix доставка: [37971964370](https://github.com/manufact-test/nomusic/actions/runs/37971964370) PASS. UI итог: [37976314199](https://github.com/manufact-test/nomusic/actions/runs/37976314199) PASS; CI [37976319421](https://github.com/manufact-test/nomusic/actions/runs/37976319421) PASS; код в ветке `feature/api-range`.
- Баг: Chrome popup полностью раскрывал большую форму, затем менял высоту назад. Исправлено на последнем commit `429000ad49d933a1ffc9fbd8270caab0582176a0`: убрать анимацию `height`, оставить soft opacity fade. Владелец разрешил не делать ещё одну ручную проверку.
- В браузере пользователя был **один оригинальный CELIKOM и три отдельные Stage7 тестовые установки**; пользователь самостоятельно нашёл оригинал, три остальные **удалил**. Не утверждать конкретный Chrome extension ID; он не был достоверно зафиксирован. На временных копиях подмена прежнего approved трека давала «ошибка подмены»; отсутствие персонального read-only API token в новых установках — гипотеза, НЕ доказательство. Оригинальное расширение не удалять/не перенастраивать.
- PR [#6](https://github.com/manufact-test/nomusic/pull/6) **OPEN / UNMERGED**. Issue [#7](https://github.com/manufact-test/nomusic/issues/7) **OPEN**, периодический MAIN-world RangeError/restorePrototypeHooks, первопричина не закрыта. Формальный Stage 6.7 dual-Chrome-profile check не подтверждён, несмотря на фактическую работу подмены.

## ОБЯЗАТЕЛЬНО: «Предложить песню» — часть текущего MVP

Это **новое утверждённое требование, нельзя забыть**. Не подменять им «Загрузить версию».

- Для пользователя при текущей песне Яндекс Музыки: `Загрузить версию` **ИЛИ** `Предложить песню`.
- **Предложить песню**: отправляется точный автоматически обнаруженный service=Yandex / Track ID + артист/название + каноническая ссылка на трек; **не нужно MP3**, **не нужна галочка про права на загруженный файл**; можно предусмотреть необязательный комментарий (например, запикивание).
- Обычный пользователь ничего не должен искать и загружать; **админ видит заявку**, выбирает статус, при возможности находит легально размещаемую версию или права. Никакой автоматической публикации по одной заявке.
- **Stage 8:** реализовать административную очередь заявок и модерацию `track_requests`, дедупликацию/rate-limit/аудит. Stage 7 уже имеет приватный owner-only `POST /api/v1/track-requests` и `track_requests`, это foundation, а НЕ публичный UI.
- **Stage 10:** вывести публичную кнопку `Предложить песню` рядом с пользовательской загрузкой с необходимой auth/entitlement/anti-abuse защитой. Не выпустить MVP без этой кнопки.
- В финальном Stage 10 UX чётко разделять декларацию прав на MP3 (только если файл загружается) и предложение без файла.

## Следующее действие: Stage 8 — admin moderation

Сверить текущий GitHub HEAD и реальные схемы `tracks/audio_assets/track_replacements/upload_submissions/track_requests`; изучить существующий [Stage8 plan](../test-plans/CELIKOM-STAGE8-MODERATION.md) и Master/Plan. Начинать с безопасной модели `admins` / auth / CSRF / audit_log и минимальных очередей **(A) MP3 uploads pending** и **(B) track-only song requests**. Затем карточка с приватным прослушиванием, просмотром Track ID/ссылки, approve/reject/disable с транзакционными гарантиями и аудитом; admin overview по реально доступным данным. До проверенного owner-gate разработки — только CI + disposable MySQL; доступ к живым pending-файлам без разрешения не менять. Не запускать очередной браузерный тест Stage 7.
Не начинать аккаунты, billing, Android. Не мёржить PR #6 и не закрывать Issue #7.

---

## Архив прежней передачи (09.10.2026, ДО ручной приёмки Stage 7)


**Сверено: 09.10.2026.** Этот файл фиксирует факты исполнения; приоритет требований: Master ТЗ MVP v1.5, затем План работ MVP v1.6. Оба файла обновлены в Library /CELIKOM датированными дополнениями. Новый файл передачи: `CELIKOM_HANDOFF_STAGE7_2026-10-09.md` (`libfile_f798ed7dfd4c81918293e9e894d04edd`), план этапа 7: `CELIKOM_STAGE7_PLAN_2026-10-09.md` (`libfile_1a2c915a3c7c8191997ac58a54e48fce`). Канонические Library IDs: Master `libfile_af7d67f2cc848191947f897a5606675c`, Plan `libfile_4841b3eb31f0819186f49ff9c42cfe4b`. План следующего этапа: [Stage 7 uploads / anti-duplicates](../test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md).

## Проверенный результат

Этапы 0–5 приняты в owner-only тестировании. **6.1–6.6 готовы и имеют зелёный CI; 6.7 серверная часть готова, но весь этап 6 НЕ закрыт формально** (нет подтверждения двух независимых профилей Chrome и осталась периодическая ошибка JS). Владельцу после установки hotfix удалось примерно 30 минут пользоваться Яндекс Музыкой без видимых зависаний, подмена работала; полная owner acceptance ещё не доказана.

- [80/80 JavaScript tests, PHP, disposable MySQL и Chromium CI](https://github.com/manufact-test/nomusic/actions/runs/37926905183) — успех, hotfix commit `1d69906aa04cf7704a89eab9342dd5d73ab936e0`.
- [Private Chrome hotfix archive](https://github.com/manufact-test/nomusic/actions/runs/37927113445) — создан, SHA-256 ZIP проверен. Manifest по-прежнему `0.4.4`; установленная сборка имеет более новый код.
- По прямому разрешению владельца: приватный [snapshot](https://github.com/manufact-test/nomusic/actions/runs/37919980695), [проверка восстановления на изолированной MySQL](https://github.com/manufact-test/nomusic/actions/runs/37920125314), [деплой](https://github.com/manufact-test/nomusic/actions/runs/37920299328), [аудит .env/audio/6 таблиц](https://github.com/manufact-test/nomusic/actions/runs/37920496968), [реальный signed HTTP 206](https://github.com/manufact-test/nomusic/actions/runs/37920657691) — всё PASS. Ни файлы, ни активная привязка не менялись.
- Hostinger: `https://darkred-camel-588676.hostingersite.com`, активный серверный release `0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c`; предыдущий `0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d` оставлен для отката. PHP API 0.4.0, replacements ON, analytics OFF.
- В живой библиотеке только согласованная запись: Yandex Track ID **144530503**, Replacement ID **1**, duration **180872 ms**. Аудио и .env находятся в приватном shared, вне public_html. Audio воспроизводится через 512 KiB signed HTTP Range → MediaSource/blob (прямой Hostinger audio.src блокируется CSP). Fail-open возвращает оригинал.
- GitHub `manufact-test/nomusic`, ветка `feature/api-range`, **PR #6 открыт и не слит** (база develop), не сливать без разрешения. Перед работой проверять HEAD. Request `.github/deploy/hostinger-library-request.json` оставлять `{"operation":"validate"}`. Не менять live DB, аудио или сервер без отдельного разрешения. Резервная копия пока у того же провайдера, не offsite DR.

## Особо важно: ошибка не закрыта

[Открытый Issue #7](https://github.com/manufact-test/nomusic/issues/7).

Chrome показал `Uncaught RangeError: Maximum call stack size exceeded` в `player/main-world-bundle.js`. Ранее стек указывал на `celikomObservedHistory`; параллельно пользователь иногда видел неотзывчивую Яндекс Музыку / `Application error` при возврате на давно открытую вкладку. В hotfix 1d69906 исправили обращение перехватчиков History/media/fetch/XHR к изменяемому `nativeHooks` на захват исходной функции + флаг lifecycle; все автотесты прошли.

**Но после очистки Chrome Errors пользователь снова увидел новую ошибку через ~30 минут**, хотя сам сайт и подмена работали нормально. Скрин указывал на `YandexMusicAdapter.restorePrototypeHooks()` (около строки 1044 итогового bundle). Не установлены точные шаги воспроизведения и первопричина, нельзя утверждать, что ошибка исчезла или безвредна. Не делать рискованный фикс без воспроизведения; при повторении собрать полный stack, проверить смену сессий/heartbeat, unmount и влияние внешних wrappers. Наблюдение переносится в этап 7; формальное закрытие 6.7 отложено.

## Работа следующего чата: Stage 7

**Этап 7: загрузки + антидубли**. Подробный порядок и тесты: [docs/test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md](../test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md). Сначала инвентаризация реальных PHP/DB/Chrome файлов, затем небольшими проверяемыми пакетами: pending upload schema → UploadService → SHA-256 dedupe/idempotency → fingerprint statuses → защищённые приватные endpoints → Add version UI → disposable DB/Chrome tests. Использовать существующие `LibraryManagementService`, `StorageAdapter`, `audio_assets` и `track_replacements`, не переписывать их заново.

**Публичные uploads выключены** (`FEATURE_UPLOADS=false` до этапа 10). Любой upload только pending; ручной approve будет в этапе 8; никакая пользовательская загрузка не может автоматически попасть в resolve. Реальная тестовая загрузка, новая запись на Hostinger и публикация требуют отдельного согласия. На этапе 7 не делаем аккаунты, billing, rewards или Android.

Владельца потребуется подключить только **в конце этапа 7 на 10–15 минут**, когда будет готов приватный Chrome ZIP: выбрать текущий Track ID, загрузить MP3, убедиться в pending и распознавании дубля. Не просить приватные токены в чат/GitHub.

## Первое действие в новом чате

Сначала обновить PR HEAD, прочитать мастер-ТЗ §§11–13 и новый Stage7 runbook. Проверить фактическую схему данных, маршруты и текущий popup. Предложить точечный контракт 7.0 и начать реализацию на `feature/api-range` через GitHub только в изолированном CI. Сообщать фактический прогресс. Отдельно отслеживать issue #7. Не начинать с нового браузерного hotfix без диагностических оснований.

**Нельзя утверждать, что Stage 6 полностью принят или что Stage 7 развёрнут в прод.**

## 2026-10-09 — Stage 7.0–7.7 code handoff (newest entry; supersedes earlier NEXT work-order text)

Latest source: `feature/api-range`. The Stage 7 server/private upload + Chrome UI foundation is committed and CI-green; do not confuse that with accepted/deployed. See `docs/test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md` and `docs/project-status.md`. CI: https://github.com/manufact-test/nomusic/actions/runs/37941932390 and https://github.com/manufact-test/nomusic/actions/runs/37942113245 (success). Check latest HEAD and new CI for subsequent documentation commits.

New files: `server/migrations/002_pending_uploads.sql`; `server/src/Application/{UploadService,Mp3Inspector,AudioFingerprintService,DeferredFingerprintService,UploadRateLimiter,TrackRequestService}.php`; `server/tests/uploads.php`; `extension/src/upload/contract.ts`; `extension/tests/upload-contract.test.mjs`. Updated: `server/{src/Application.php,public/index.php,config/app.php,.env.example}`; `server/tests/http.mjs`; `scripts/test-server-foundation.mjs`; `extension/{src/popup/popup.ts,src/shared/messages.ts,popup/popup.html,popup/popup.css}`. Reuse Stage 6 library and private StorageAdapter; pending never resolves.

**Next before owner manual acceptance:** review latest CI, ensure private extension artifact for owner test, prepare a disposable non-live upload API/DB/storage (without enabling uploads on active Hostinger). Test browser UI exact read-only ID, status pending, renamed duplicate and no public Resolve. Fingerprint worker not implemented; do not claim recompressed audio dedupe. Note PHP ini limits must support selected MP3 size in the future private test. Explicit user approval is required for any Hostinger/server/DB change, real upload, new live asset, deploy request, or merging PR #6. Public FEATURE_UPLOADS stays false to Stage 10; private FEATURE_OWNER_UPLOADS defaults off.

**Carry-over issue:** https://github.com/manufact-test/nomusic/issues/7 — intermittent post-hotfix `RangeError: Maximum call stack size exceeded` in MAIN bundle around `restorePrototypeHooks()`. Root cause not reproduced; do not mark fixed or harmless. Stage 6.7 two-Chrome-profile check absent. Keep PR #6 open, main/develop untouched.

## 2026-10-09 — latest Stage 7 safe hardening handoff (supersedes older CI snapshot)

Latest validated CI: [37945005475](https://github.com/manufact-test/nomusic/actions/runs/37945005475), **PASS** with PHP/MySQL, genuine multipart, 4-worker race, FFmpeg-generated *seekable* 2.5-second MP3 and Chromium native decode/seek/play with test-only signed-byte-compatible Range fixture. Earlier intermediate failed CI runs during test fixture iteration are superseded by this full passing run. Latest source remains `feature/api-range`; check current HEAD before further changes.

`Mp3Inspector.durationMs()` now reads the whole MP3 and rejects malformed/truncated/junk tail; `UploadService` saves measured audio duration, validates duplicate metadata and refuses idempotency retries after a pending candidate has been moderated. Independent owner staging setup/manual protocol: `docs/deployment/stage7-owner-upload-acceptance.md`. Any extension artifact produced by default CI with blank `api/config.json.baseUrl` is for automated verification only, **not** usable for owner upload to an HTTPS staging API.

**Next decision:** Owner permission is required before provisioning isolated external staging HTTPS/MySQL (or modifying any Hostinger resource), configuring its owner token, and producing a correctly origin-pinned private Chrome ZIP. Until then, no live uploads, DB migrations or deployment. Stage 7 is technically CI-complete but not manually accepted. Issue #7 RangeError, formal Stage6.7 two-profile gate, and PR #6 merge remain open.
