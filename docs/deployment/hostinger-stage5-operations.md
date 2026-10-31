# CELIKOM Stage 5 — private Hostinger operations and recovery

Updated 2026-10-09. Live owner testing on extension 0.4.4 is accepted. This document describes **private-test** controls, not a production disaster-recovery guarantee.

## Boundaries

The dedicated site is darkred-camel-588676.hostingersite.com. The code repository is manufact-test/nomusic, branch feature/api-range. The application lives in the private celikom directory next to public_html, with immutable server releases, shared/env, shared/audio and shared/staging. Neither SQL rows nor audio files nor real secret material may be stored in Git or Actions artifacts.

Use the existing GitHub Actions SSH key, pinned Hostinger ED25519 key and PHP 8.3. Do not print any file names from private audio storage, signing tokens, database credentials or signed audio URLs. Do not merge PR #6 automatically.

## Operations

The workflow is .github/workflows/hostinger-stage5-ops.yml. Its request file is .github/deploy/hostinger-stage5-request.json. Exactly one JSON property named operation is allowed, and only these three commands may appear:

| Operation | Result and safety |
| --- | --- |
| audit | Read-only check of current production MySQL approved mapping, audio SHA-256, permissions and feature state. Requires and compares the latest pre-deploy private snapshot of the env, audio file hashes, and six SQL-table row counts. Also checks public HTTPS health/config and unauthorized resolve denial. |
| snapshot | Creates a fresh 0700 recovery folder under private celikom/backups/stage5, containing a 0600 environment copy, checksummed private audio, a 0600 SQL schema/data export for CELIKOM's six tables, and a hash manifest. No contents are sent to GitHub. |
| restore-drill | Hash-checks the latest snapshot, copies environment and media to a temporary private scratch directory, verifies and cleans scratch, then streams **only SQL** into an ephemeral GitHub runner private file and imports it into a disposable MySQL 8 instance. It verifies schema migration, exact-ID mapping and approved audio metadata. Runner scratch is deleted after the job. No live database tables are written. |

Changing that request file in feature/api-range triggers the workflow; it rejects stale workflow revisions and serializes with the main deploy workflow. A caller may also use workflow_dispatch when already on that branch. Temporary remote scripts and input files are removed on success. Failed private partial snapshots remain inaccessible outside Hostinger and require manual cleanup; do not publish them.

All operations return safe summary lines without printing the backup, environment or SQL. No action in this workflow supports editing, disabling or deleting approved live audio or application configuration.

## Repeat deployment

The existing .github/workflows/hostinger-deploy.yml uses .github/deploy/hostinger-request.json for a new immutable server package and host activation. Package checksum, PHP 8.3, actual DB connection, twice-run idempotent migrations, new release symlink, HTTP health/config and external HTTPS/CORS/unauthenticated resolve are verified.

The independent server API version (0.4.0) is validated from the server's config/app.php rather than the package/extension version (0.4.4). This avoids a false rollback after updating the Chrome extension without changing the PHP API contract.

Activation keeps shared env/audio outside versioned releases. It copies previous public entry files and rolls back the public entry and symlink when a post-switch HTTPS gate fails. It does not reverse database migrations or promise instant disaster recovery from provider loss. On 2026-10-09 a full repeat deployment succeeded and a separate audit proved shared configuration hashes, audio hashes and six MySQL row counts unchanged.

## Verified evidence

- Initial production integrity: https://github.com/manufact-test/nomusic/actions/runs/37903708919
- Private snapshot: https://github.com/manufact-test/nomusic/actions/runs/37903842547
- Isolated file restore + disposable MySQL restore: https://github.com/manufact-test/nomusic/actions/runs/37903962631
- Repeat deployment: https://github.com/manufact-test/nomusic/actions/runs/37904158336
- Post-deployment data comparison: https://github.com/manufact-test/nomusic/actions/runs/37904416817
- Owner-approved signed audio and Range after deployment: https://github.com/manufact-test/nomusic/actions/runs/37904551511

## Monitoring and residual risk

Public API monitoring is configured separately as a six-hourly condition watch, alerting only on confirmed failures of /api/v1/health (200), /api/v1/config (200, replacements on, analytics off), or unauthenticated /api/v1/resolve (401). It uses no secrets or privileged API. CI/SSH audit remains available on demand.

**Known limits:** all persistent backup files are on the same Hostinger provider as production. Their successful restoration on an isolated runner proves logical recoverability, not survival of a full provider outage. Before real customer release, add automated independent encrypted offsite copies, tested key custody and retention/rotation, credential handling, a full production-grade observability/alerting system, and more extensive outage/rollback drills. Keep these as later hardening gates, not claims of completeness.

The browser requires refreshing a previously-open Yandex Music page once after the user disables and re-enables the Chrome extension via chrome://extensions; this is a non-blocking MVP limitation. Audio stop/return to original is verified.

## Next stage

Stage 5 is accepted for **owner-only private testing**, not commercial release. Continue with Stage 6 shared library as defined by the authoritative Master TZ MVP v1.4 and Work Plan MVP v1.5. Preserve the uploaded owner-reviewed MP3, its metadata, approved track ID and signed playback, and leave PR #6 open until the owner expressly authorizes merge.
