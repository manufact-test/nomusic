# CELIKOM — актуальная передача в новый чат

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
