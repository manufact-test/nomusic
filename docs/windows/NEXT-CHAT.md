# CELIKOM Windows — CURRENT HANDOFF / 15 NOVEMBER 2026

**This top block is authoritative.** The archived handoff below is retained for history only and is superseded; do not follow its old "first message" or task status.

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Current code/release-workflow checkpoint: `bbf964512513cbf9e1942f6598534521c3b7aa69`.
- W155 application-code checkpoint: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`; W156 package/draft-release checkpoint: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- Exact backup before the PowerShell-only P-256 provisioning block: `backup/windows-main-pre-powershell-only-p256-provision-20261115` @ `7c516ad69dbad3f56781a56cd9f7b4ae8c3d7870`.
- Exact backup before the release-workflow repair: `backup/windows-main-pre-release-workflow-repair-20261115` @ `6c921032e7dd0d05718e150d9665eab52ba02c23`.
- Exact backup before this documentation update: `backup/windows-main-pre-powershell-owner-handoff-docs-20261115` @ `bbf964512513cbf9e1942f6598534521c3b7aa69`.
- Target bootstrap version: **0.24.38**. GUI, UpdateSupervisor and Inno installer metadata are aligned.
- Main CI run `43735322258`: **SUCCESS**. Windows integration CI run `43735322290`: **SUCCESS** on `bbf96451`.
- W151–W154 are code/test/CI-ready, but owner-PC acceptance is pending. Use the single grouped plan in `docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md` only after the final package.
- W155 runtime-chain audit is complete; no concrete runtime gap was found. Do not repeat broad audits or add speculative improvements.
- W156 release workflow derives the P-256 public pin from the protected private-key secret, builds exactly one EXE and one ZIP, and creates an unpublished Draft Release with SHA256SUMS. The Actions artifact is skipped for the owner-bootstrap path. Production publication defaults OFF.
- The owner provisioning helper now uses built-in Windows PowerShell 5.1, Windows CNG, Notepad and the browser only. No Node.js, GitHub CLI, PowerShell 7 or extra developer tools are needed. It creates the local keypair and opens the GitHub Environment page for the single secret upload.
- **No owner action is requested now.** Finish repository-side checks first. When the only remaining blocker is key provisioning, request one consolidated action: run the PowerShell helper and add the PEM as Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` in protected `windows-stable-production`. Never ask for the private PEM, password or token in chat.
- The protected Environment must have an authorized required reviewer and allow only branch `main`. No public-key variable is needed; the workflow derives the public pin from the private secret. `CELIKOM_STABLE_DEPLOY_ROOT` is only needed for future production-feed publication after migration.
- **Release workflow defaults:** version `0.24.38`, sequence `1`, blank expiry generates a 7-day UTC expiry, `publish_to_production=false`. After the owner adds the protected key secret, the assistant commits the one-shot marker `.github/release/owner-bootstrap-0.24.38.trigger`; this starts the workflow automatically. The owner only approves the protected environment if requested. Keep publication OFF; do not click Publish release on the resulting draft.
- **End-user automation contract:** one manual bootstrap install over 0.24.37 is required because that installed version has no P-256 pin. Once the bootstrap is installed and DNS/TLS plus the signed feed are activated, subsequent CELIKOM updates must be detected, verified, downloaded and installed automatically. End users must never need Node.js, GitHub CLI, PowerShell commands, passwords, tokens or signing keys.
- **Visibility:** the repository itself is public, but GitHub Draft Releases are listed only for users with push access until published. Existing Releases contain two unpublished Android drafts; no Windows 0.24.38 draft exists yet. Public source code remains public.
- Not done: owner P-256 key provisioning, final EXE/ZIP, owner installation/acceptance, DNS/TLS/feed migration. No production feed has been published.
- Never use Authenticode/PFX, disable SmartScreen/Defender/UAC, publish the production feed early, create a TEST product/branch, touch Android/extension, or reopen excluded #53/#54/#56/#57/#58. #52 remains open pending owner-PC acceptance.

## Current first message for the next chat

Привет! Продолжаем CELIKOM Windows. Работай только в `manufact-test/nomusic`, ветка `main`. Сначала проверь live HEAD и последние CI, затем прочитай W119, W150, W155, W156, W154 и этот NEXT-CHAT.

W155 runtime-chain audit завершён. W156 release workflow реализован: P-256 public pin выводится из protected Environment secret, итоговая сборка создаёт ровно один EXE, один ZIP и SHA256SUMS в неопубликованном Draft Release. Целевая версия 0.24.38; workflow defaults — sequence 1, expiry автоматически 7 дней, `publish_to_production=false`.

Последний проверенный release-workflow checkpoint: `bbf964512513cbf9e1942f6598534521c3b7aa69`. Main CI `43735322258` и Windows integration CI `43735322290` — SUCCESS. Точный backup перед текущей документацией: `backup/windows-main-pre-powershell-owner-handoff-docs-20261115` @ `bbf964512513cbf9e1942f6598534521c3b7aa69`.

Не начинай новые исследования и не меняй архитектуру. Продолжай только конкретные оставшиеся шаги W155/W156. Provisioning helper теперь работает на встроенном Windows PowerShell 5.1 и открывает GitHub Environment settings + Notepad; Node.js, GitHub CLI и PowerShell 7 владельцу не нужны. Не проси владельца действовать, пока repository-side work не завершена. Когда понадобится, запроси одну консолидированную операцию: создать локальный ключ и добавить его как Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` в защищённое `windows-stable-production`. Никогда не проси присылать PEM, пароль или токен в чат.

Окружение должно иметь required reviewer и разрешать только `main`. Публичный ключ workflow выводит из protected secret автоматически. Production feed остаётся fail-closed и не публикуется до миграции DNS/TLS. Не трогай Android/extension и не открывай #53/#54/#56/#57/#58.

После одного ручного bootstrap over 0.24.37 и активации DNS/TLS + signed feed все последующие обновления для пользователей должны идти автоматически. Не собирай промежуточные пакеты; после подтверждения секрета владельцем добавь one-shot marker commit, дождись protected environment approval и создай один Draft Release. Затем проведи одну общую W154-приёмку. Не нажимай Publish release.


---

# CELIKOM Windows — CURRENT HANDOFF / 15 NOVEMBER 2026

**This top block is authoritative.** Everything under the historical archive is retained for technical history only. Do not follow its old task status, old first messages, or superseded setup instructions.

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Current `main` HEAD before this documentation update: `0a2df7d5d104854c492dc7114ec6c4175a195df8`.
- Current code/release-workflow checkpoint: `44a3e55ed9e70a4f2aa4b3ac562c122575f0a189` (one-shot marker trigger included).
- W155 application code: `c1afdd5fc9b3ec90bb760857bf584dc494d7774e`; W156 package/release code: `23a4ec4a232139b9cfea986dec629d1d9b8776dd`.
- Exact backup before this documentation handoff: `backup/windows-main-pre-final-handoff-docs-20261115` @ `0a2df7d5d104854c492dc7114ec6c4175a195df8`.
- Latest Main CI `43736028010` and Windows integration CI `43736027854`: **SUCCESS** on `0a2df7d5`.
- Tasks 1–4 (W151–W154) are complete at code/test/CI level. They are not owner-PC accepted; perform one grouped W154 acceptance only after the final package.
- Task 5 implementation is complete at code/test/CI level. The runtime audit is closed. Do not reopen it or invent further updater changes.
- The approved owner helper is `.github/scripts/windows-stable-provision-key.ps1`. It uses built-in Windows PowerShell 5.1, Windows CNG, Notepad and browser only. No Node.js, GitHub CLI, PowerShell 7, package manager, token or password is required on the owner PC.
- **Remaining path only:** one bounded repository preflight; one owner-side local P-256 key generation and protected Environment secret upload; one marker commit to trigger the protected release workflow; one signed unpublished Draft Release containing exactly one EXE, one ZIP and SHA256SUMS; then one grouped W154 owner acceptance.
- Do not commit `.github/release/owner-bootstrap-0.24.38.trigger` until the owner confirms the secret is saved; committing it triggers the workflow immediately.
- The only owner secret is `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` in protected Environment `windows-stable-production`. Require an authorized reviewer and deployment branch policy allowing only `main`. Never ask for the private PEM, password or token in chat. The workflow derives the public pin; no public-key variable is required.
- Target bootstrap version: **0.24.38**. Defaults: sequence `1`, automatic 7-day UTC expiry, `publish_to_production=false`. The workflow creates an unpublished Draft Release; do not publish the draft or production feed.
- DNS/TLS and production-feed publication remain intentionally deferred until infrastructure migration. The bootstrap contains the public P-256 pin and future origin. After DNS/TLS + signed feed are activated, all subsequent updates must be automatic.
- No final EXE/ZIP has been built or delivered. Owner remains on 0.24.37; no owner installation/acceptance has happened.
- **No other work is authorized.** Do not revisit Tasks 1–4, #53/#54/#56/#57/#58, broad audits, speculative fixes, Android, browser extension or unrelated server code. #52 stays open until owner-PC acceptance.

## Current first message for the next chat

Привет! Продолжаем CELIKOM Windows как ведущий разработчик. Работай только в `manufact-test/nomusic`, только ветка `main`. Ничего не начинай с нуля и не меняй архитектуру.

Сначала получи live HEAD и последние CI. Затем прочитай W119, W150, W155, W156, W154 и этот NEXT-CHAT. W150 задаёт scope, W119 — постоянные правила продукта. Исторический архив ниже не является списком новых задач.

**Текущий статус:**
- W151–W154 (Tasks 1–4) завершены по коду/тестам/CI. Не возвращайся к ним. Owner-PC acceptance будет один раз по W154 после финальной сборки.
- W155 runtime audit завершён: конкретных пробелов не найдено. Не повторяй аудит и не придумывай улучшения.
- W156 release workflow и PowerShell-only provisioning реализованы. Current release-workflow checkpoint: `44a3e55ed9e70a4f2aa4b3ac562c122575f0a189`. Последний проверенный main/doc HEAD: `0a2df7d5d104854c492dc7114ec6c4175a195df8`; Main CI `43736028010` и Windows integration CI `43736027854` — SUCCESS.
- Целевая версия — 0.24.38. Release workflow defaults: sequence 1, expiry 7 дней автоматически, `publish_to_production=false`. Он создаёт один неопубликованный Draft Release: EXE, ZIP с этим EXE в корне и SHA256SUMS.
- Точный backup перед документационной передачей: `backup/windows-main-pre-final-handoff-docs-20261115` @ `0a2df7d5d104854c492dc7114ec6c4175a195df8`.

**Делай только это, без побочных задач:**
1. Выполни один короткий preflight текущего release workflow, key helper, version alignment и protected Environment contract. Не повторяй широкие аудиты и не меняй рабочий код без конкретного доказанного дефекта.
2. Когда всё готово, попроси владельца выполнить одну консолидированную операцию: скачать raw `.github/scripts/windows-stable-provision-key.ps1`, запустить встроенным Windows PowerShell 5.1 и сохранить созданный PEM как Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` в `windows-stable-production`. Скрипт сам откроет GitHub Environment и Notepad. Владелец присылает только строку успеха и публичный fingerprint. Никогда не проси PEM, пароль или токен.
3. Только после подтверждения, что secret сохранён, создай точный backup и одним commit добавь marker `.github/release/owner-bootstrap-0.24.38.trigger` в `main`. Это автоматически запускает protected workflow. Если GitHub запросит Environment approval, владелец подтверждает его.
4. Дождись CI/workflow и проверь, что создан ровно один Draft Release с одним EXE, одним ZIP и SHA256SUMS. Не загружай публичный Actions artifact. Не нажимай Publish и не включай production feed.
5. Выдай одну финальную сборку и один групповой W154 acceptance plan. Не делай промежуточных сборок. Не объявляй автоматические production-обновления действующими до миграции DNS/TLS и подписанного feed.

**Жёсткие правила:** не останавливайся после каждого маленького этапа, не присылай длинные отчёты и не спрашивай разрешение на каждое действие. Работай крупными последовательными блоками до реального внешнего блокера. Не придумывай дополнительные задачи, не трогай Android/extension, не открывай старые Issues #53/#54/#56/#57/#58. Никакой Authenticode/PFX, никакого отключения SmartScreen/Defender/UAC, никаких промежуточных EXE/ZIP.

Единственный ручной шаг для владельца — bootstrap поверх 0.24.37. После будущей активации DNS/TLS и signed feed все следующие обновления для пользователей должны проходить автоматически.

---

# Historical handoff archive — superseded by the current block above