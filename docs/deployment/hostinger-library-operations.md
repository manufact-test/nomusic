# CELIKOM Stage 6: restricted shared-library Actions

Authority: CELIKOM Master TZ MVP v1.5; Work Plan MVP v1.6 (2026-10-09). This is a restricted owner-only *internal* tool, not a public upload or moderation interface. Read [Stage 6 test protocol](../test-plans/CELIKOM-STAGE6-SHARED-LIBRARY.md).

## Verified safe baseline

Repository: `manufact-test/nomusic`, branch `feature/api-range`, PR #6 **open, unmerged**. Current live Hostinger server and extension 0.4.4 are not redeployed by library Actions. The request file is `.github/deploy/hostinger-library-request.json` and starts as `{"operation":"validate"}`. Editing only this file on the active branch triggers `.github/workflows/hostinger-library.yml`; the request is also used on a manual workflow dispatch. Never run old workflow revisions or commit secrets/audio to requests.

- `validate`: local-only schema/test check, **no SSH**, no MySQL and no live writes. Run 37916327886 passed.
- `inspect`: pinned existing SSH key/host identity, verified private layout, read-only three-table counts and public health/config. Run 37916411482 passed, returning one Track, one AudioAsset, one mapping. Public config replacements on, analytics off. Temporary files in private incoming are cleaned.
- `add-track`, `add-asset`, `link`, `approve`, `activate`, `disable`: implemented but **not yet invoked on live DB**. Owner approval of exact mapping/action is mandatory before switching the JSON away from read-only modes.

## Safety invariants

The workflow is serialized with Stage 5 Hostinger workflows. It rejects wrong repository/branch, stale SHA, malformed arguments or extra JSON fields. Pinned host key and SSH key fingerprint are verified. The PHP handler is uploaded temporarily under private `celikom/incoming`, checks active production release/private storage, loads the same `LibraryManagementService` as internal CLI, and never runs general shell commands or untrusted SQL. No full server deploy needed to inspect the catalog. It never logs private media, staging filenames, keys, environment, signed URLs or SQL errors.

All writes require `confirm_owner: true` plus a purpose-specific reviewed/activation/disable flag. A per-GitHub-commit private *one-time claim* is recorded **before mutation**; a retry after any ambiguous outcome requires fresh owner review and a new commit. `activate` and `disable` additionally require `expected_active_replacement_id` (`"0"` for none), compared under the Track lock inside a MySQL transaction. This prevents stale workflow instructions from silently replacing an unexpectedly changed mapping. Existing Stage 5 live mapping must not be changed without owner consent.

**Important:** boolean flags are an explicit-operation safeguard, not proof of human identity. Repository write and Actions access must remain tightly controlled, and production mutation should be preceded by a fresh backup/rollback plan and owner approval. If a staging file is ever approved for `add-asset`, the remote handler requires exactly one valid, regular private MP3/WAV in staging, not named or copied through GitHub. No user-upload route exists.

## Allowed request schema examples (illustrative, do not execute on live site)

```json
{"operation":"validate"}
```

For a read-only inspection:

```json
{"operation":"inspect"}
```

Potential future **reviewed** operations (do not copy IDs into production without a real check):

```json
{"operation":"add-track","track_id":"123456","duration_ms":201000,"confirm_owner":true}
```

```json
{"operation":"link","track_db_id":"2","asset_id":"1","confirm_owner":true}
```

```json
{"operation":"approve","replacement_id":"2","confirm_owner":true,"confirm_reviewed":true}
```

```json
{"operation":"activate","replacement_id":"2","expected_active_replacement_id":"0","confirm_owner":true,"confirm_activate":true}
```

There are also `add-asset` (duration + both owner/review flags) and `disable` (replacement ID + expected active ID + both owner/disable flags). This runbook does not constitute authorization to run them. Keep the request in `validate` mode until a specific operation is approved.

## Current state / handoff (2026-10-09)

Stage 6.1–6.6 complete, Stage 6.7 Hostinger deployment and data integrity passed. The library request remains `{"operation":"validate"}` and no Stage 6 live library mutation has been authorized or performed. Stage 6 formal two-profile owner acceptance is pending. Chrome MAIN-world intermittent stack overflow recurred after hotfix and is tracked as [issue #7](https://github.com/manufact-test/nomusic/issues/7). Next development work is Stage 7 protected uploads + exact anti-duplicates on disposable test data; see [Stage 7 runbook](../test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md). Public uploads must remain OFF until Stage 10 entitlement, pending cannot become approved automatically. No new production mapping/audio/DB change without fresh owner permission.
