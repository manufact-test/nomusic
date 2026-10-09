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
