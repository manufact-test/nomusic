# CELIKOM server

Stage 4 PHP 8.3/MySQL API. Enable PDO MySQL and fileinfo. The private catalog returns only exact service/Track ID approved active replacements. Signed versioned audio endpoints stream private MP3/WAV with 200/206/416 and HEAD; no filesystem keys or paths are exposed.

```bash
composer install
php bin/migrate.php
php -S 127.0.0.1:8080 -t public public/index.php
```

Configure a private `.env` using `.env.example`; keep FEATURE_REPLACEMENTS and FEATURE_ANALYTICS disabled until configured. No runtime packages are needed: bootstrap provides deterministic PSR-4 loading. Composer validates requirements and provides optional autoloading.

Routes: GET `/api/v1/health`, GET `/api/v1/config`, GET `/api/v1/resolve?service=yandex&track_id=ID`, GET/HEAD `/api/v1/audio/ID?expires=...&token=...`, POST `/api/v1/events/batch`. Resolve/events require private beta Bearer API_TEST_TOKEN; audio needs only its scoped signature. This temporary access is not the later account/entitlement system.

`php tests/smoke.php` runs unit contracts. `composer test` additionally runs migrations/catalog/analytics checks when disposable DB_NAME starts with `celikom_test`; it clears that test database's CELIKOM tables. Never point integration tests at production. `npm run test:server` also runs real HTTP and native Chromium audio checks when a test DB is configured.

Reviewed fixture import: `php bin/import-test-audio.php --file=/PRIVATE/audio.mp3 --track-id=ID --duration-ms=MEASURED --confirm-reviewed`. This owner-only preparation does not implement end-user uploads/moderation.

Deploy layout and rollback: `HOSTINGER.md` in the package, or `docs/deployment/hostinger-private-test.md` in the repository. The server ZIP is built using an explicit allowlist and contains no `.env`, user audio or tests. Accounts, uploads, admin, billing and Android remain separate stages.
