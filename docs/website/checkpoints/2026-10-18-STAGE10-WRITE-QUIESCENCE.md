# CELIKOM website — Stage 10 v4.3: cooperative CMS write quiescence

**Date:** 2026-10-18. **Scope:** website/ and its Website CI workflow. **Status:** significant technical preparation, NOT a live release, NOT formal Stage 9/10 acceptance. The original approved v10 files are byte-preserved. PR #6 stays open.

## Problem solved in this block

The v4.2 coordinated backup used one MySQL REPEATABLE READ snapshot across encrypted DB and content/media JSON, but could not guarantee that a media file would remain unchanged or present while those two archives were assembled. Also, there was no admission control for new HTTP writes during backup.

## Implementation

- **CmsWriteQuiescence.php** introduces an advisory cross-process writer/snapshot protocol using Linux/POSIX flock on a dedicated, private 0600 regular file named .celikom-cms-writes.lock (configuration CELIKOM_SITE_WRITE_GATE_FILE). Parent must be owner-only and entirely outside the public web tree. The lock file is checked against symlinks, unexpected hard links, unsafe permissions, inode mismatch and invalid paths.
- **Shared LOCK_SH** covers each admin POST request **before session verification and any DB writes**, including login throttling/audit, content/FAQ changes, publication/revision restoration, media upload and private image selection. A write request encountering an exclusive backup lease fails closed with 503 and Retry-After: 5. Reads remain available where otherwise authorized. Actual CMS availability is still determined by the separate release gate.
- The CLI owner-provisioning command and the private media derivative preparation command also acquire the same writer lease. New CLI-only backup-coordinated-cms.php acquires **exclusive LOCK_EX**, runs CmsConsistentBackup::capture while holding that lease, emits only a minimal nonsecret result, then releases. The capture method now requires an active exclusive lease by type and runtime invariant. Previous standalone backup tools remain non-coordinated maintenance exports and MUST NOT be promoted to complete live restore points.
- Lock is released via try/finally/destructor even after most application errors. A crashed/killed process releases its advisory flock at the OS level. The snapshot does not attempt to change the database/server to global read-only mode.
- Environment for isolated HTTP tests (Stage9AdminHttpTest.py and Stage9MobileAdminBrowserAudit.py) now provisions the private lock path. Both the local website/public layout and future public_html layout are covered by separate explicit webroot resolution for the admin entrypoint.

## Tests and evidence

- Stage10WriteQuiescenceTest.py launches independent PHP workers. Verifies multiple shared writers, no concurrent exclusive snapshot, no writer during exclusive snapshot, release after simulated killed worker, rejection of missing configuration, public gate path, world-readable file and symlink.
- Stage9AdminHttpTest.py acquires an exclusive flock from the Python test process and sends a real valid-CSRF login POST to PHP. Confirms HTTP 503 and Retry-After instead of allowing a DB write. Then releases lock and runs the existing CMS login, draft, FAQ, publish/restore and private upload flows.
- Stage10ConsistentSnapshotTest.php now rejects coordinated capture without the required exclusive lease and after lease release. It also runs the actual coordinated owner CLI against disposable CI MySQL and private synthetic media, then re-verifies the CLI manifest using --verify. Legacy tests for concurrent MVCC read view and complete restored DB+binary media remain.
- Check latest Actions after this docs-only checkpoint. Code commit evidence and run IDs should always be taken from GitHub HEAD, not assumed from a historical success.
- CI test-only changes are isolated under website/ and .github/workflows/celikom-website-checks.yml. No production workflow edits, Hostinger calls, deployment credentials, or changes to server/, extension/, android/ or approved v10 CSS/JS.

## Critical remaining constraints

1. This is **cooperative/advisory**. Direct SQL clients, unexpected cron tasks, other hosts not sharing the same POSIX lock, and unmanaged media garbage collection **can bypass it**. Production needs inventory and explicit integration of every writer/GC path; prove provider supports cross-process flock on the actual storage layout. Cannot assume shared lock works across separate nodes or NFS.
2. The v4.2 content+media JSON remains UNENCRYPTED at rest; owner-only permissions protect local disk only. Offsite backup requires separate authenticated encryption, secure key handling, backup retention and a verified recovery procedure. Do not publish the private manifest or binary media.
3. There is STILL NO reviewed real server-side deployment coordinator or proven atomic switch/rollback of running MySQL+PHP+media, real maintenance-page admission controller, or integrated Hostinger healthchecks. The previous release lifecycle test uses **synthetic logical JSON**, not running MySQL.
4. Stage 9/Stage 10 NOT officially accepted. The public site and CMS must remain 503/noindex until manual acceptance, approved image rights/redaction, SSL/domain/legal review and safe unified release. .github/workflows/deploy-celikom-website.yml remains HARD DISABLED with && false; do not enable it.
5. Existing standalone JSON content backups are not disaster recovery. Each real restore requires the encrypted full DB, matching content/media, application generation, and tested rollback. The new CLI merely produces a coordinated archive pair; it is not a migration or deployer.

**Next step:** implement offline-only, crash-recoverable replay of actual new disposable MySQL database restore under the exclusive write gate, coupled to immutable media staging, with negative tests for migration/schema mismatch and partial failure. Preserve the production lockout and the v10 artifacts.
