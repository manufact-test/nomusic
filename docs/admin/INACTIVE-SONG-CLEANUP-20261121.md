# Remove rejected and disabled versions from admin lists

## Confirmed problem and owner scope

Owner could select rejected uploaded versions and enter the exact count, but deletion failed. Live read-only inspection of admin-bulk-restore-067968ce4eae found four rejected rows, all four referenced by upload_submissions. Existing BulkModerationService intentionally refused ANY FK-referenced replacement with candidate_has_history_reject_instead. That was appropriate for an unreviewed pending upload but unusable for already rejected records. Disabled rows had no selection checkbox and were excluded from delete validation. Owner explicitly requested both rejected and disabled cleanup.

## Behavior

- Owner can select rejected and disabled inactive versions and use the existing delete/count/confirmation flow. Approved/active versions stay ineligible. Moderator/viewer deletion permissions are unchanged.
- A rejected/disabled row with upload/reward/complaint/other FK history is removed from every admin upload filter, count, page and search by an existing bulk_moderation_tombstones marker with cleanup_status=retained_history (16 characters). Its relational history and audio references stay intact; no FK, reward or complaint is erased. The row stays rejected/disabled and its version increments. One replacement_bulk_archive audit entry records the operation.
- Without such references, existing physical deletion and private unshared-file cleanup remain. Shared audio is never deleted. Pending uploaded rows with history still require rejection/disable first; they are not silently removed.
- New approved replacements of the same Track ID retain their identity, status, version and audio. The owner is deleting an old version, not the entire Track.
- Removed historical rows cannot be selected again or reactivated through a stale individual form. Removal-marker checks in both transaction paths use current locking reads (FOR UPDATE), so an older REPEATABLE READ snapshot cannot miss a concurrently committed removal.
- Checkbox data carries its status. When selection contains rejected/disabled versions, only deletion is available; approval/rejection requires a pending-only selection. Confirmation/result text explains list removal and preserved history, with readable conflict messages.

Five production files change: AdminPanel.php, BulkModerationService.php, BulkModerationView.php, ModerationService.php, bulk-moderation.js. CSS is hash-checked and unchanged. Existing tombstone table is reused; no production migration, client update, upload/playback/billing/entitlement change, or automatic deletion of owner records.

## Verification

Disposable MySQL HTTP tests cover the prior 50-item moderation/rights/roles/CSRF/partial conflicts and new cases: referenced rejected/disabled removal, disappearance from all/filter/search results, unchanged newer approved mapping/shared audio, upload history retention, exactly one audit, repeated/forged-version deletes, stale individual reactivation denial and physical deletion of an unreferenced disabled version. Real Chromium verifies select-all/none/form association and pending-vs-inactive action availability at 1440/768/390px.

A behavioral concurrency regression interleaves another committed archive immediately after the old individual form's first nonlocking snapshot read and before its row locks. The archived disabled version must remain inactive; the current locking removal-marker lookup rejects resurrection. This is exercised through production ModerationService with two PDO connections, not a reimplementation of its logic.

Hosting probes preview existing inactive rows only; they NEVER execute deletion of owner songs. Candidate and active checks require stable catalog counts/versions/statuses, preserve search and empty pending queues, exercise actual owner-authenticated HTTPS inactive checkboxes/delete-count preview, deny stale approved preview and missing CSRF/anonymous access, and check public config. An ephemeral session for an existing owner is removed in finally.

## Deployment

Branch fix/admin-rejected-cleanup-20261121, based on accepted admin restore e32b994f5e2032bb9943534a26653d6d66a42d67. Application change 9883dc0d1424a35ecbb85a4316521bb8fce7fddb; locking-read refinement 1b532497bf6e2669ef5cab76dd9ec9d15d0388fe. Both initial rollout and locking refinement passed guarded hosting deployment. Follow-up test run 44886103631 passed the concurrency regression, then correctly stopped a redundant redeploy on the before-hash guard. The release helper now verifies an identical already-installed target instead of copying it again.

Only exact known admin source hashes are accepted (explicit stable/intermediate hashes, never arbitrary files). Each real update clones current, backs up Admin and previous-release, and checks no files outside the allowed Admin delta changed. MP3 cleanup, all other shared service code/configuration and actual songs are preserved. Final verification succeeded on 2026-11-21 at 11:44 Moscow (08:44 UTC): workflow 44886138940; verify job 136791887543; hosting verification job 136792117129. Both referenced-history/inactive tests, the real two-connection race, pending and inactive Chrome UI at all three widths, and catalog search passed. Authenticated HTTPS checks passed and the helper confirmed the already-installed exact target without another application change.

Active release: admin-rejected-cleanup-1b532497bf6e. Its backup is /home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/backups/admin-rejected-cleanup-1b532497bf6e/ (Admin/ plus previous-release and launcher metadata). Final helper/test HEAD c9c6d1c254a2856e566a94af2212a2b12fb80702 contains the same application bytes. Production rollout/checks changed no owner song statuses, versions, active mappings or catalog counts; owner confirmation of an actual selected deletion remains pending. No extension reinstall is required.

After owner starts removing historical rows, prefer a forward fix. A later rollback to admin code unaware of retained_history would make those preserved rows visible again and lose the stale-reactivation fence. Never erase tombstones or FK history to hide that behavior. No owner rows are removed by deployment itself.
