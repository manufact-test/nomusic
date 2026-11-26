# CELIKOM website — Stage 10 v4.7: protected offsite envelope and operator release boundaries

**Date:** 2026-10-18 · **Branch:** `feature/api-range` · **Status:** CI-only engineering checkpoint. **NOT an actual production/offsite upload or owner approval.**

## Goal and scope

v4.2–v4.6 provided a single MySQL+content/media snapshot, cooperative CMS write quiescence, encrypted whole MySQL, disposable MySQL restore, versioned schema/SQL generations, and journaled HTTP simulation. **One critical gap remained:** content+media JSON carried complete original private media bytes in plaintext and was only protected by local `0600` filesystem permissions. It could never be transferred or retained as an unencrypted remote backup.

This checkpoint develops a **separate-key encrypted transport container**, exercises end-to-end recovery from that container into actual CI MySQL, and adds a static operator/writer safety boundary inventory. Nothing is sent to external storage.

## Code delivered

### 1. `website/app/src/CmsOffsiteEnvelope.php`

- `seal()` authenticates the **already verified** coordinated restore-point manifest, separately encrypted complete MySQL archive, and content+private-media JSON. It emits **only one** owner-only `celikom-offsite-*.sbox` ciphertext file into a separately protected directory, never plaintext images, account rows, or manifest there.
- A dedicated **independent** 32-byte XChaCha20-Poly1305 key, from `CELIKOM_SITE_OFFSITE_KEY`, MUST differ from `CELIKOM_SITE_FULL_BACKUP_KEY`. Neither goes into CLI arguments, logs, repository or transport. The keys are NOT embedded inside the archive. Source files are still sensitive, even after sealing: offline cleanup/retention are required.
- Authenticated libsodium secretstream records store a fixed ordered 3-file inventory, SHA256 digests, file lengths, and encrypted 64KiB chunks with a mandatory final authentication tag. The transport budget is bounded and it rejects extra trailing bytes, truncation, invalid key, tampering, malformed file names, symlinks, unsafe private directory/file modes, and oversized containers. All file writes are exclusive, owner-only `0600`; the final ciphertext file is only published after writing completes and verifying the entire archive.
- `inspect()` verifies without creating plaintext. `unseal()` allocates a **new private 0700 folder**, decrypts all three 0600 artifacts, verifies final record and each file hash, and independently calls `CmsConsistentBackup::inspect` to authenticate the DB, content/media equality and binary media. On ANY failure, the temporary directory is cleaned (file unlink is **not** a guaranteed secure disk erase). It never touches the live database.
- Hard operational guard: `CI=true` and `CELIKOM_SITE_SANDBOX_RESTORE=1`. This class is **not** a production backup command, remote storage client, scheduling job or live release authorizer.

### 2. `website/tests/Stage10OffsiteEnvelopeTest.php`

The new test uses disposable MySQL 8 and creates a synthetic private PNG with the correct SQL metadata. It runs:

`CmsConsistentBackup::capture` → encrypted offsite transport → authentication-only verification → decrypt to a distinct private folder → `CmsConsistentBackup::inspect` → actual `CmsSandboxRecovery::replay` into a *new* disposable MySQL schema → authenticated binary media preview.

Negative assertions: missing independent key, key re-use, wrong transport key, wrong underlying full-DB key, altered/truncated/appended ciphertext, symlink ciphertext, exposed 0644 file/0755 parent, transport or ciphertext under webroot, mixing original plaintext/ciphertext directories, no plaintext in ciphertext, no leftover decrypted files after failed extraction, and no unexpected original MySQL modification. An unrelated source/Hostinger is never connected.

### 3. `website/tests/Stage10OperatorBoundaryTest.py`

- Read-only operator **static inventory** covers production `public/index.php` and `public/admin/index.php` release gates; CMS admin POST shared lock, owner-provisioning CLI, private media derivative CLI, read-only pending-review CLI; coordinated snapshot exclusive lock; encrypted offsite CI guard and separate key; CI-only recovery/generation/router; permanent hard-disabled production deploy; explicit unresolved owner/backup/file-rollback blockers.
- Documents known internal SQL/media writer surfaces: `AdminAuth` (login throttle, account metadata, audit), `CmsDraftStore`, `CmsRevisions`, `CmsMediaAssignment`, `CmsMediaStore`, `CmsMediaDerivative`. These are accessed via one guarded HTTP POST boundary and the two guarded CLI writer entrypoints, **not** by a global MySQL read-only switch. Any added webhook, cron, worker, background cleanup or manual SQL remains outside this proven inventory until explicitly audited.
- Includes fault-injection mutations that deliberately remove writer freezes, consent blocker, isolation guard, hard-disabled deploy, or insert sandbox code into public routes: static matrix must fail closed.
- Prints `production_ready=false` regardless of passing checks: **a green safety audit does not grant approval**. Test runs in the no-deploy website CI workflow. Foundation checkout reads `.github/workflows/deploy-celikom-website.yml` solely for its disabled guard.

## Release operator preflight — REQUIRED, NOT YET COMPLETE

| Area | Minimum evidence before any live operation | Current state |
|---|---|---|
| Owner approval | Dated written authorization naming domain, release generation and rollback window | **BLOCKED: not given** |
| Legal and image rights | Explicit approval for final popup PNG; license/redaction; privacy/GDPR/legal pages reviewed | **BLOCKED** |
| Hosting topology | Document Hostinger `public_html`/private paths, exact MySQL user privileges, node count, cron, SSL and route semantics | **UNKNOWN, not tested** |
| All writers and media GC | Audit HTTP/admin POST, CLI provisioning, image derivatives, raw SQL, scheduled jobs, media deletion, backups and external workers for shared freeze or maintenance mode | **Only repository paths audited** |
| Durable host primitives | Independently prove POSIX `flock` across **all relevant workers**, atomic rename, persistent fsync/power-loss behavior, permissions and storage location | **CI runner only** |
| Archive encryption | Separate 32-byte transport key; key escrow, restricted rotation and offline recovery test; never same key as DB | **CI implementation proven; operator setup missing** |
| Remote storage | Authenticated upload/download, encryption at rest, immutable retention, access log, secure deletion policy, remote-vs-local integrity checks | **NOT IMPLEMENTED** |
| Disaster recovery | Restore downloaded encrypted offsite copy into new SQL/medias and verify real HTTP, publication, admin auth, private images | **CI local copy only** |
| Unified release ledger | Server-side generation pointer, app+DB+media health, atomic routing contract, durable recovery journal, rollback and reattempt rules | **Offline model only** |
| Visual and SEO | Verify v10 breakpoints, actual domain CSS/JS, favicon, HTTPS, 503/noindex and eventual intentional robots state | **Local CI parity only** |
| Risk window | Confirm operator presence, explicit maintenance admission, no uninstrumented writers, monitoring and rollback drill | **NOT approved** |
| Rollback verification | Read-only checks after rollback; no backward SQL DDL; log old DB/media retained and separately dispose new generation only after review | **Disposable CI only** |

## Mandatory operator sequence (future design, NOT executable on Hostinger)

1. **Collect evidence only:** inventory live SQL and files, third-party workers, backups, SSL and rights. Ensure admin/public remain 503/noindex. Confirm the disabled GitHub workflow.
2. **Require explicit owner signoff:** this repository does not contain release secrets or approval files. Without signed release authorization, stop.
3. **Establish verified writer quiescence:** include media GC and direct SQL, never infer silence from browser inactivity or the advisory lock alone.
4. **Create and seal restore point with separate keys:** retain original coordinated local artifacts securely and make a **separately verified encrypted remote copy**. Verify using the actual downloaded remote object, not its original disk copy.
5. **Restore-test before publication:** in a separate SQL schema and private media generation with negative healthchecks, perform independent read-only HTTP/DB validation.
6. **Stage candidate, keep old generation immutable:** app/PHP, DB, media and release router must agree on generation; do not mutate v1 with a down-migration.
7. **Switch only under explicit release authorization and monitored change window:** if any healthcheck or journal phase is inconclusive, fail closed and reconcile old generation.
8. **Re-test and retain rollback state:** record immutable artifacts and proof; cleanup only with separate operator confirmation. Ensure monitoring catches post-release errors.

**STOP conditions:** compromised or missing encryption keys, inability to restore remotely, incomplete writer coverage, mismatch of v10 artwork, missing legally approved popup, failed SSL/HTTPS, unverified hosting file semantics, broken database/media pair, corrupt unconfirmed release journal, or owner approval absent.

## Proof boundary and next step

A passing GitHub Actions job provides **CI-only evidence** that the crypto framing and disposable SQL/media reconstruction work and that known repository release gates remain closed. The offsite container **has not been uploaded** anywhere, and key management, backup retention, ransomware immutability, verified remote download, Hostinger topology, real production synchronization/maintenance mode, power-loss fsync, domain and legal approvals remain open.

**Next:** offline-only design/implementation of an explicit protected retention and remote archive intake verification contract, plus testable operator signoff evidence that cannot be forged by a simple file marker; audit any newly introduced SQL/media writer. Do not connect to Hostinger or enable production deploy.

**Invariants:** `feature/api-range`, PR #6 OPEN/unmerged; `.github/workflows/deploy-celikom-website.yml` hard-disabled with `&& false`; `/` and `/admin/` stay 503/noindex; approved v10 and 5 CSS/2 JS unchanged; no `server/`, `extension/`, `android/` modifications; Stage 9/10 **NOT formally accepted or completed**.
