# Restore lost bulk moderation and search — 2026-11-21

## Observed cause

Owner reported missing selection checkboxes/select-all/approve-selected while uploading five tracks. Live inspection of upload-cleanup-823c0613c212 showed that the entire bulk subsystem was missing, and the earlier catalog search had also disappeared. Current AdminPanel SHA-256 was 132562772781065a03837c074053ae10ca0168c07a61a1a19537ea4804758dbc. BulkModerationService, BulkModerationView and bulk-moderation.js were absent; the CSS lacked its bulk block; ModerationService had lost optional expected-version/batch arguments.

The retained accepted admin-song-search-4bf2ac511142 release still contains the complete implementation. The current admin is from the older full server snapshot 0.4.57-e48e05f75629becc7efd2198dc7459a1ac91b825. Commit e48e05f75629becc7efd2198dc7459a1ac91b825 is dated Nov 13 and named “ops(windows): run final integrated 0.24.36 package and publish”; its hosting request names the Windows gain sidecar migration. This identifies the source snapshot, not the exact time it became active or an individual responsible. The MP3 cleanup rollout subsequently cloned that active snapshot and changed only upload classes/private tools; its exact-delta gate proves it did not edit admin files.

Do not deploy historical complete server checkouts from a client branch. Windows/Android server changes must be merged into the current shared server or applied as guarded deltas preserving existing capabilities.

## Restoration

Only six production files under src/Admin change:

- AdminPanel.php: restore accepted bulk routes, checkbox form/script inclusion and whole-catalog search. Preserve the CURRENT Windows support-diagnostic download block exactly, rather than overwriting it with the older accepted block.
- ModerationService.php: restore the original optional expected-version and batch-ID parameters, locked version check and batch audit. Existing six-argument individual decisions retain their behavior.
- BulkModerationService.php, BulkModerationView.php, bulk-moderation.js: exact retained accepted bytes.
- admin-style.css: exact additive retained bulk styles.

Original mechanism is reused, not redesigned: max 50 selected records on the current page, separate confirmation and rights checkbox, per-record transactions/audit, stale-version conflicts, owner/moderator authorization, viewer/anonymous/CSRF denial and safe deletion history rules. No client source changes, new extension package, audio/playback changes or production database migrations.

The original 019_bulk_moderation_tombstones.sql is recovered into repository history for disposable CI. Hosting already has the table; smoke requires it before activation and never runs migrations. A compatibility navigation_seen table exists only in disposable test fixtures because this historical repository base predates the live navigation migration.

## Validation and deployment

First verification run 44884616620 passed MySQL HTTP moderation contracts, exactly 50 approvals with per-record audit, stale/missing partial conflicts, rights/CSRF/role protections, protected deletion history and catalog search. Real Chromium tested select-all/none, HTML form association and layout at 1440/768/390px.

First deployment stopped BEFORE activation because the owner had meanwhile approved all five tracks and the original smoke required a pending sample. No rollback of the owner’s decisions occurred. Smoke now supports an empty pending queue: preserve its empty state, verify search on an existing approved sample, and require bulk preview of already-approved entries to be rejected. No replacement is uploaded/approved/rejected/deleted for the hosting smoke. A short-lived session for an existing owner is removed in finally; no new account/admin is created.

Deployment clones the actual current release, backs up its whole Admin directory and previous-release pointer, guards every replaced file by before/after SHA-256, requires new files absent, and checks that NOTHING outside those six files differs. Candidate CLI and active authenticated HTTPS checks preserve replacement counts, versions and statuses. Failed active checks automatically restore the prior release. Existing MP3 normalization/classes/decoder and shared environment stay intact.

Status: successfully activated on 2026-11-21 at 11:26 Moscow (08:26 UTC).

- Final workflow 44884836379: verification 136787755840 and deployment 136787947671 passed.
- Active release: admin-bulk-restore-067968ce4eae. Backup: /home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/backups/admin-bulk-restore-067968ce4eae/. previous-release records the exact predecessor; Admin/ and public-index.php retain replaced sources and launcher metadata.
- Exact six-file delta check, candidate smoke and active authenticated HTTPS smoke passed. Empty pending queue renders correctly, search works, approved entries cannot be bulk-previewed for approval, missing CSRF/anonymous access are denied, public config remains healthy. Aggregate replacement count/version/active/pending state stayed unchanged.
- No production migration, song moderation, audio-asset write or client package update. Current Windows support download block was preserved; MP3 normalization and decoder remain intact outside the six-file delta.
- Owner reports all five real songs already approved. No request to upload more songs is needed; visible selection on newly pending real uploads remains for the next normal owner use. Pending rows/select-all/confirmation/batch execution were exercised with 50 disposable fixtures and real Chromium, not by remoderating owner songs.

Do not blindly re-run the successful deployment: before-hash guards intentionally reject an already-restored admin. Roll back only if current still equals this release; atomically restore backup/previous-release and launcher mtime, never overwrite a subsequent deployment from another chat. Branch fix/admin-bulk-restore-20261121; application code restored in dee3537a99f263709c6df6b38bb47f7dd0b3594b; deployment smoke update 067968ce4eaefac0d406c386d86993557827d0c7. Exact file hashes: .github/scripts/admin-bulk-restore/manifest.json.


## Subsequent inactive cleanup

Release admin-rejected-cleanup-1b532497bf6e adds owner deletion of disabled versions and safe removal of referenced rejected/disabled history from admin lists. Bulk selection/search remain installed; current upload/audio/playback/configuration remain untouched. See docs/admin/INACTIVE-SONG-CLEANUP-20261121.md before any rollback, because that release preserves removed history behind tombstones and prevents stale reactivation.
