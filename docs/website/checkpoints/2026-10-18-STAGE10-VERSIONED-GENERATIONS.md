# CELIKOM website — Stage 10 v4.5: versioned SQL and private release generations

**Date:** 2026-10-18. **Scope:** offline GitHub Actions on disposable MySQL, private media and private generation pointer. **Status:** evidence for an eventual safe release design; no host deployment or owner acceptance.

## Starting point

v4.4 can restore encrypted CMS data (11 real MySQL tables) + all private media into an isolated, fresh disposable database under an exclusive `CmsWriteQuiescence` lock. Its durable cleanup journal allows disposal after a crashed worker. It deliberately has no production restore, migration or public cutover entrypoint.

## Implemented in v4.5

1. **Explicit v1 → v2 schema migration:** `website/tests/fixtures/002_ci_generation_only.sql` adds a version table and a `release_generation` column to `site_settings` **only in a newly restored database**. The class `website/app/src/CmsSandboxGeneration.php` requires the canonical fixture path AND exactly three hard-allowlisted SQL statements. A migration is rejected when already or partly applied; no in-place retry of MySQL DDL after failure.
2. **Immutable private generations:** `gen-baseline` contains verified copies of version-1 media and points at the original `celikom_site_test` CI database. `gen-<16-hex>` contains verified copies of the restored generation's media and points at its separate `celikom_site_ci_replay_<16-hex>` database. Each generation has a strict owner-only JSON metadata record and 0700/0600 private media. A separate owner-only `.celikom-ci-active-generation.json` selects the active offline generation.
3. **Read-only health before switching:** checks real MySQL `site_state`, CMS owner, versioned DDL/marker, every private image via the authenticated SQL metadata and SHA256, and the absence of unaccounted media files. In CI the rendered approved v10 HTML is also compared between the v1 and v2 databases. The switch is a single, atomic filesystem rename of the private selection record after validation; a failed pre-switch leaves the old record. Rollback selects the retained v1 again, without dangerous reverse ALTER statements.
4. **Isolation:** executable code checks `CI=true`, `CELIKOM_SITE_SANDBOX_RESTORE=1`, host `127.0.0.1`, source DB name `celikom_site_test`, private target paths and exclusive flock lease. It never rewrites `website/public/`, app templates, original styles/scripts, real Hostinger paths, live web routing or launch approval. Neither `public_html` nor production resolves this pointer.
5. **Failure tests:** `Stage10VersionedGenerationTest.php` stages a coordinated encrypted backup, restores a fresh real MySQL generation, verifies a failed first DDL leaves v1 selected, rejects partial schema retry, discards and recreates from the authenticated original archive; checks migration/approved site rendering/private media. It tests an unapproved SQL path, source database misbinding, malicious active pointer, damaged staged media, failure before pointer rename, activation/rollback, rejection of deleting an active generation, and `SIGKILL` of an independent PHP worker immediately following atomic pointer selection. It additionally kills a separate worker after a real `ALTER TABLE` and replays a fresh generation from backup instead of repairing partial DDL in place.
6. **CI:** the new test is inserted after v4.4 real MySQL recovery and before Stage 9 media/UI regression in the existing `.github/workflows/celikom-website-checks.yml`. Earlier backup, snapshot, cross-process flock, full recovery, private media, 503/noindex and Chromium v10 tests remain.

## Recovery logic demonstrated

- Fault **before** the private pointer swap: old generation is still selected and its SQL/media unchanged.
- Fault **after** the private pointer swap: new generation is selected; the surviving owner process can independently validate it then switch back to the retained old generation. Both MySQL database generations still exist until explicitly discarded.
- Fault after nontransactional MySQL DDL: do NOT rely on a SQL ROLLBACK. Active pointer stays on old generation, and v4.4 cleanup journal is used to remove the entire broken disposable DB/media. A fresh v2 generation may be created from the previously verified snapshot.
- A damaged staged image, schema mismatch, or tampered pointer causes fail-closed health; do not activate or delete source data.

## Critical exclusions

**NOT a production deployment or actual atomic cross-resource cutover.** This is an offline private pointer model; no live PHP request, DNS, webserver document root, DB connection router, cron writer, or real Hostinger volume consumes the generation pointer. Filesystem rename atomicity and POSIX flock on GitHub runner do NOT prove atomicity/durability across MySQL+PHP+media on Hostinger, multi-host/NFS semantics, durable fsync across a power failure, or network access. The v4.4 recovery journal and the v4.5 offline pointer are different mechanisms; real production operation needs a unified recovery ledger, crash/fsync design, retention and owner permissions. The image+content JSON snapshot still requires authenticated offsite encryption. Protected v10 artwork/source, rights and legal review, SSL/domain and operator runbook remain release blockers.

**Hard requirements unchanged:** no Hostinger/production/SSH; deploy workflow contains `&& false`; site & admin stay 503/noindex without owner approval; PR #6 remains open and unmerged; no edits to approved v10, its 5 CSS+2 JS, server/, extension/, android/; Stage 9 and Stage 10 remain UNACCEPTED.

## Next block

Investigate durable generation state machine and roll-forward/rollback under actual disposable PHP HTTP routes and read-only healthchecks. Design an operator-approved unified deployment protocol with secure offsite media handling before considering any live rollout. Do not enable legacy SCP deployment, introduce release flags, or touch Hostinger automatically.
