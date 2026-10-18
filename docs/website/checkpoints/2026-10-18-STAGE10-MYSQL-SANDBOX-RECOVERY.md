# CELIKOM website / Stage 10 — v4.4 real MySQL recovery and crash cleanup drill

**Date:** 18.10.2026. **Code branch:** `feature/api-range`. **Status:** CI-only engineering evidence; neither live release nor formal owner acceptance.

## What v4.4 adds

The previous v4.3 snapshot had consistent encrypted MySQL, plaintext private content/media and a cooperative file lock. The Stage 10 release simulator still used a synthetic JSON logical database. v4.4 closes a **narrow but important gap**: verified recovery of actual SQL rows into a brand-new disposable MySQL database, reconstruction of actual private image files, forced-error cleanup, and recovery of resources left after a killed process.

New class `website/app/src/CmsSandboxRecovery.php`:
- Hard-denies execution unless `CI=true`, `CELIKOM_SITE_SANDBOX_RESTORE=1`, MySQL host precisely `127.0.0.1`, and source database precisely `celikom_site_test`. Only generated destinations with the `celikom_site_ci_replay_` prefix are ever created/dropped; source is never migrated, deleted, truncated or restored into.
- Requires an active exclusive `CmsWriteQuiescence` lease, private owner-only recovery directory outside public web root and a verified v4.2/v4.3 coordinated manifest. Rejects bad source key, altered backup, public destination, noncanonical schema file and missing CI guard BEFORE any recovery write.
- Writes a private, 0600, atomically renamed journal BEFORE its first `CREATE DATABASE`. The journal binds a randomly generated isolated database name and media directory. Cleanup checks exact format/name/id, refuses corrupted journal/symlinks/unexpected media, drops ONLY the named isolated CI DB, deletes staged media and clears journal **last**.
- Restores private PNG/JPEG/WebP bytes to a fresh 0700 folder, each file 0600. Rechecks SHA256 against original media row metadata. Creates real MySQL 8 disposable target DB and applies the existing `001_website_cms.sql` there ONLY. Compares each table's live `SHOW COLUMNS` with source schema before importing; rejects conflicting MySQL DDL instead of silently using `CREATE TABLE IF NOT EXISTS`.
- Replays authenticated full-DB rows under a target InnoDB transaction, handles the seeded `site_state` row, verifies counts of **all 11 full-DB tables** against `CmsFullDbBackup::inspect` (the four-table overlap in `CmsRecoveryPair` is NOT sufficient for full-table parity), confirms staged media against recovered SQL, and compares published revision pointer.
- On normal failure, restores nothing in source: rolls back SQL insert transaction, drops only isolated target database and deletes staged media through the journal. A real worker killed by `SIGKILL` cannot execute catch/finally, but a subsequent isolated cleanup can use the durable journal to remove the orphan target and bytes.
- A successful replay is an **isolated recovery generation for validation**, not a public cutover. Explicit cleanup is required after audit; the journal deliberately persists until then.

New `website/tests/Stage10SandboxRecoveryTest.php`, wired to the existing website MySQL CI job, verifies:
1. Wrong key, public destination, altered schema file, execution outside CI — no writes.
2. Seven forced failures: journal-created, media-staged, database-created, schema-checked, first-row-inserted, rows-committed, verified. All clean up isolated SQL/media; source is unchanged.
3. Actual conflicting MySQL table schema and tampered staged PNG rejected; no orphan target.
4. Successful real MySQL recovery and authenticated private media preview, recovery of audit log, no change to original data.
5. Malicious journal attempting to point at `celikom_site_test` refused.
6. Independent PHP worker is killed with **SIGKILL after real CREATE DATABASE**; next process uses the retained journal to remove partial MySQL schema/media. No Hostinger or production actions.

## Evidence and limitations

- [Website CI run for v4.4 code](https://github.com/manufact-test/nomusic/actions/runs/39120016089) — the **real MySQL and media recovery CI test completed successfully** and syntax/asset safeguards passed. Confirm entire run final conclusion, Chromium parity and general CI against current HEAD before claiming end-to-end green.
- `Stage10JointRecoveryTest.php`, Stage10ConsistentSnapshotTest.php, all Stage 9 CMS tests, browser layout and HTTP release gates remain in the CI suite.
- **Not solved by this change:** actual in-place/online MySQL migration or rollback, atomic transition of public HTML/JS/PHP release generation, owner-controlled production maintenance/release approval, coordination with rogue SQL writers or cron/GC, shared-filesystem flock proof on Hostinger, encrypted offsite content/media, authorized public popup screenshot, full real-server healthchecks, operator runbook.
- **Do not interpret CI-only DROP DATABASE as a production migration implementation**. This class intentionally has **no** production CLI and refuses any DB other than the disposable test one. Real production failure-safe cutover requires independently reviewed infrastructure and explicit owner approval.

**Invariant:** PR #6 open/unmerged; `.github/workflows/deploy-celikom-website.yml` still disabled with `&& false`; Hostinger and live DB untouched; approved v10 artwork/grid, 5 CSS + 2 JS unchanged; no code under `extension/`, `server/`, `android/` touched; Stage 9/10 NOT formally accepted or closed.

## Next engineering task

Design and test a versioned **forward migration** from a schema fixture to a new schema inside disposable MySQL, with compatibility checks and reversible generation/cutover contract, then validate atomic-ish media directory promotion and restore read-only healthchecks in offline test environment. Do not introduce a production deploy path.
