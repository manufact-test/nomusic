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

## Stage 6 owner-only library CLI (no public upload endpoint)

The library manager registers files without automatically publishing them. Commands run on PHP 8.3 inside the private application, with an existing private MySQL database and `STORAGE_PATH` configured. All IDs printed are internal database identifiers; the music service Track ID is a separate string. Commands do not reveal a private storage path or a signed URL.

```bash
php bin/library-add-track.php --track-id=123456 --duration-ms=201000 --title=ReviewedTitle
php bin/library-add-asset.php --staging-file=owner-reviewed.mp3 --duration-ms=201000 --confirm-reviewed
php bin/library-link.php --track-db-id=1 --asset-id=1
php bin/library-approve.php --replacement-id=2 --confirm-reviewed
php bin/library-activate.php --replacement-id=2 --confirm-activate
php bin/library-disable.php --replacement-id=2 --confirm-disable
```

**Examples are placeholders, not instructions to execute on the current Hostinger.** Use only the measured duration and the owner's verified mapping. `library-add-asset` accepts a basename directly inside private `shared/staging` (derived as a sibling of `STORAGE_PATH`), rejects symlinks/traversal, enforces MIME/size/SHA-256 and never imports a browser upload. `link` creates a **pending** inactive candidate, `approve` records the reviewed decision while keeping it inactive, and only `activate` enables server-side selection. `disable` revokes it. Strict argument validation rejects unknown/duplicate options. Stage 6.4 will invoke these through a restricted GitHub Actions owner-only workflow; do not manually change live data before that gate. User moderation, accounts and public uploads remain later stages.
