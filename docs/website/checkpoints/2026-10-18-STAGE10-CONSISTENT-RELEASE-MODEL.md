# CELIKOM Website — v4.2 / Stage 10: coordinated backups and offline release lifecycle

**Date:** 2026-10-18. **Branch:** feature/api-range. **Scope:** website/ and its CI. **Status:** substantial Stage 10 engineering preparation, NOT production readiness, not a formal Stage 9/10 acceptance. No Hostinger connection or real deployment. PR #6 is open, not merged.

## Completed engineering block

### 1. One InnoDB read view for a pair of CMS archives

- CmsFullDbBackup.php and CmsBackup.php gained an optional existingSnapshot switch. Original standalone transaction behavior remains unchanged; under a caller-owned transaction they neither begin nor commit/roll back it.
- New CmsConsistentBackup.php begins one repeatable-read transaction on one PDO connection, establishes the shared read view, exports (a) the fully encrypted website database and (b) content/revisions plus private media bytes, and confirms cross-copy row equality and media integrity using CmsRecoveryPair.
- Only after successful validation does it atomically rename a 0600 restore-point manifest binding the two artifacts by filename and SHA256. Failed captures clean up partial artifacts. The manifest is NOT a public release approval and its SHA256 hashes are NOT a cryptographic signature.
- CmsConsistentBackup.inspect re-verifies actual files, mode, private path, no symlinks, cryptographic DB authentication, row parity and image integrity.
- Content/media export remains plaintext JSON with base64 images, protected by 0600 but must be additionally encrypted before offsite transmission or storage. The complete DB stream is encrypted by an independent key.

### 2. CI actually proves consistency under another editor's write

- Stage10ConsistentSnapshotTest.php creates two separate disposable MySQL connections. The first begins its common snapshot and exports complete DB; the second commits a concurrent CMS draft version update; the first then exports content/media. Both backups retain the same pre-change InnoDB view although the fresh database contains the edit.
- Negative tests: no transaction for caller-owned exporters; wrong decryption key; public target directory; edited manifest checksum; public file permissions; missing image during capture; incomplete capture cleanup.
- Existing Stage10JointRecoveryTest.php continues to restore the actual encrypted DB into a new isolated MySQL schema and private image bytes, verify render parity, users and audit. Both test families complement one another.

### 3. Journal-based offline release/rollback model

- New Stage10ReleaseLifecycleTest.py stages exact public/app/database website trees; checks byte hashes; saves previous code, private-media tree and **synthetic logical DB state** in a disposable checkpoint before writes.
- Rehearses state transitions for database, media, app, schema, public entrypoints and a real PHP local HTTP healthcheck for both / and /admin/. Without owner's release marker these are expected to be 503/noindex.
- Exercises six interruption points, including interruption before a journal write, healthcheck failure, staged source tampering, corrupted rollback backup and a successful activation followed by deliberate rollback.
- A new simulator instance reads the persisted journal and verifies exact rollback of prior code, synthetic DB and images while protecting unrelated site files and unmanaged owner files.
- IMPORTANT: the database in this lifecycle model is a JSON fixture. This is NOT a working production SQL migration, transactionally atomic filesystem+MySQL release or server-capable deployment script. Actual MySQL restoration is tested separately by the PHP CI tests.

### 4. Verified results / preserved scope

- Tested code HEAD: 77592c2797efe1bd53293f2d930050492108645c.
- Website CI 39117243995 — SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/39117243995
- Website push CI 39117241577 — SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/39117241577
- General CI 39117244004 — SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/39117244004
- Compare against v4.1 starting HEAD 9800f3840c0e2f2773eb9547cf557b6c6f58d839: only three PHP backup classes, two Stage10 test files and the Website CI workflow changed. Original v10 template, 5 original CSS, 2 original JS and reference; extension/, server/, android/ remain unchanged. Deployment workflow is still hard-disabled with && false. PR #6 remains open.

## Still BLOCKING a real launch

1. Live production writes/media garbage collection must be stopped or coordinated during a shared snapshot; the current shared InnoDB read view alone does not freeze physical private images.
2. Real server-side generation switching, crash-durable journal, owner-controlled maintenance, migration sequencing, healthcheck, full SQL/media restore and rollback must be built and proved in a disposable environment before any deployment can be considered.
3. Content/media archives need offsite encryption, independent secret custody, retention policy, tested recovery plan. SHA256 manifest alone is not an authenticity signature.
4. Hosting path permissions, SSL and domain checks, approved lawful popup asset, legal/visual QA, manual owner authorization and formal Stage 9 and Stage 10 acceptance are missing.
5. Public release-gate must remain 503/noindex. Do not enable the old scp workflow, create release approvals or publish site/CMS.

**Next work:** design and test the actual CMS writer quiescence barrier (including private media and housekeeping) plus stronger disposable MySQL restore/migration rollback integration. Keep all real Hostinger accesses forbidden until explicitly authorized and production design verified. Save documents only after another major block or on user request.
