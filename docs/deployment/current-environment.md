> [Snapshot нового live schema 38129853027 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129853027):
> 8 audio объектов, все 32 SQL таблицы (включая reward_ledger/reward_policy) и env.
> [Restore нового schema 38129932202 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129932202):
> закрытые файлы и SQL восстановлены изолированно, live данные не заменялись.
> ZIP 0.4.16 готов к одной содержательной owner-проверке; результаты ещё не получены.

> [Live unified audit 38129760860 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129760860):
> обычный user bearer, трёхдневный trial, независимые устройства, refresh/logout
> только одного устройства, signed HEAD/206 и полный MP3 девятью диапазонами,
> загрузка MP3 и отдельное предложение без файла, dedupe, pending denied playback.
> Проверка выполнена на новом live release, без отдельного API_TEST_TOKEN для клиента.
> Сохранность прежних catalog/media/accounts/trials/sessions подтверждена после
> удаления только временных QA-записей. Старый audit сначала отказал новой версии
> по allowlist до каких-либо записей; разрешён только audit точного release SHA,
> старые reset-trials/enable операции для этого release не разрешены.
> [Stage12 audit 38129629193 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129629193).
> Ручная проверка новых наград ещё ожидается; рабочий playback не считается
> повторно принятым владельцем лишь по автоматическому HTTP smoke.

> **11.10.2026 — Stage12 развёрнут, подготовка ручной проверки 0.4.16.**
> Hostinger release `0.4.16-dd54afb774baefc90c2c059a6231c85a0442b9b6`,
> [deploy 38129391202 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129391202).
> Миграции 009–012 additive; старые owner credentials и flags сохранены, не ротированы.
> [Enable 38129558574 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129558574):
> изменён только FEATURE_REWARD_ELIGIBILITY=1, digest аккаунтов/устройств/сессий/
> trials/catalog/media/policy сохранён, HTTPS rewards без bearer = 401.
> Owner-раздел «Награды за вклад» включён; правила остаются выключенными/нулевыми.
> FEATURE_BILLING_VIEWS=0, FEATURE_REFERRAL_ATTRIBUTION=0, реальные платежи/применение
> скидки/списание бонуса/paid entitlement не включены. Исторические авторы не backfill.
> Полный Chrome ZIP 0.4.16 SHA256 `5a89f46b17163d09479f561473a6a683d5f49d4d019bddbb52d64f3496e916eb`;
> включает правку отступа без трека, pin на прежний Hostinger API, оба MV3 worlds.
> Это одно расширение, установленную резервную 0.4.4 не удалять. Ручная проверка:
> новая загрузка → approve версии → pending-вклад → grant/revoke/журнал в админке,
> затем обычный playback/оригинал и отсутствие отступа. Не давать отдельный текст на QA.
> Старые документы ниже — история, не актуальное «сервер 0.4.11 не обновлялся».
> Этап 12 частичный; не закрывать до qualification/реальных скидок и owner acceptance.

# CELIKOM — current private-test environment

Recorded: 2026-10-09. Source of truth for requirements remains CELIKOM Master TZ MVP v1.4 and Work Plan MVP v1.5. This file captures measured deployment facts, not a production-security approval.

## Hostinger / API

- Dedicated Hostinger PHP website: https://darkred-camel-588676.hostingersite.com (temporary test hostname).
- Hostinger hPanel: https://hpanel.hostinger.com/websites/darkred-camel-588676.hostingersite.com
- Private application: /home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
- Public site document root: sibling public_html; release package, SQL migrations, credentials and user audio live outside web root.
- SSH: 92.113.19.189:65002, account u235811320. GitHub Actions SSH key and DB password are already configured as secrets; do not ask user to reveal or rotate them.
- Application CLI/runtime: PHP 8.3.33 with pdo_mysql and fileinfo. MySQL user/database: u235811320_celikom.
- Active immutable server release: **0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d**. The server API reports version **0.4.0** by design; Chrome extension version is **0.4.4**. Deployment workflow was fixed to independently validate the API package version.
- Feature flags: FEATURE_REPLACEMENTS=1, FEATURE_ANALYTICS=0. Signed audio and owner-only temporary API token stored privately; no secrets are in Git or artifacts.

## Real audio and playback

- Reviewed private MP3 is stored under shared/audio and associated with exact Yandex Track ID 144530503 via approved MySQL replacement ID 1; measured duration 180872 ms; audio length 4345176 bytes.
- Browser owner acceptance: 6 of 6 functional and 6 of 6 stability scenarios on 0.4.4. CSP-compatible MediaSource blob backed by 512 KiB HTTP Range streaming.
- Re-enabling a disabled Chrome extension on an already-open Yandex Music tab can require refreshing that page once; accepted for current MVP. Does not block playback or safety.

## Verified Hostinger operations on 2026-10-09

- Read-only production integrity (private env, approved DB mapping, on-disk SHA-256, public health/config): https://github.com/manufact-test/nomusic/actions/runs/37903708919
- On-host private recovery snapshot (private config + audio + SQL for six database tables): https://github.com/manufact-test/nomusic/actions/runs/37903842547
- Isolated config/audio restoration and recovery of the same SQL schema/records into a disposable runner MySQL instance: https://github.com/manufact-test/nomusic/actions/runs/37903962631
- Repeated immutable production-server deployment with migration idempotence, PHP/MySQL runtime and HTTPS checks: https://github.com/manufact-test/nomusic/actions/runs/37904158336
- Post-deployment SHA-256 equality for original private env/audio and six MySQL row counts against the pre-deploy snapshot: https://github.com/manufact-test/nomusic/actions/runs/37904416817
- Internal authorized resolve + public HTTPS signed-audio HEAD/Range/CORS/206: https://github.com/manufact-test/nomusic/actions/runs/37904551511
- External public endpoint monitoring configured at a six-hour interval. Alert only on confirmed health/config/authorization failure; no tokens are needed.
- New operations runbook: [Hostinger Stage 5 operations](hostinger-stage5-operations.md).

## Limits and release safety

- The snapshot is **on the same Hostinger account**, not an offsite disaster-recovery backup. Secure independent backup/rotation is future production hardening.
- Restore was exercised for files in isolated storage and SQL on disposable MySQL; the live site's database was not overwritten. No intentional live outage/rollback drill was run; the activation rollback was previously validated on isolated fixtures.
- Public client release is **not authorized**: accounts, billing, end-user upload/moderation, permissions hardening and repository privacy remain later stages.
- PR #6 remains **open and unmerged**; project source work remains on feature/api-range. Separate future enhancement: auto reconnect after Chrome disable/re-enable.

Never print, commit or attach private keys, database credentials, API bearer tokens, private backup contents or signed audio URLs.
