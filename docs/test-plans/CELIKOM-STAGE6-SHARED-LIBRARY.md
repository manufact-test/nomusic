# CELIKOM-STAGE6-SHARED-LIBRARY — controlled implementation gate

**Authority:** CELIKOM Master ТЗ MVP v1.5 and CELIKOM План работ MVP v1.6 (2026-10-09). Master ТЗ prevails on conflict. **Status:** 6.1–6.5 green; Stage 6 NOT yet accepted. Next gate: 6.6. PR #6 stays open.

## Current source-derived architecture

- `tracks`: exact `service + service_track_id` unique identity. No metadata-only automated mapping.
- `audio_assets`: SHA-256 unique, private `storage_driver/storage_key`; a single file can support multiple Track IDs.
- `track_replacements`: pending/approved/rejected/disabled, is_active, version. Unique generated active_track_id forbids two approved active mappings per Track.
- `PdoCatalogRepository` resolves only approved, active, non-disabled rows. `ResolveService` issues per-replacement signed URLs and positive/negative TTL; the private file remains behind `StorageAdapter`.
- `TestAudioImporter` already deduplicates files across Track IDs but directly creates approved active mappings; this must remain a restricted reviewed-fixture operation, not an upload or moderation mechanism.
- `ApiClient` coalesces in-flight resolve, uses capped positive/negative cache; `ReplacementController` also suppresses repeated negative retries. Server TTL values are not yet fully authoritative in the client.
- CSP-safe `MediaSource/blob` playback using 512 KiB signed HTTP Range must not regress to direct Hostinger `audio.src`.

## Development gates

| Package | Increment | Acceptance |
| --- | --- | --- |
| 6.1 | Current server/catalog + multi-client cache fixture tests and this protocol | Disposable MySQL and compiled extension tests green, no server mutations |
| 6.2 | Transactional internal LibraryManagementService | Idempotent Track/Asset/link/activation; concurrency and duplicate checks |
| 6.3 | library-add-track, library-add-asset, library-link, library-activate CLI | Validated inputs, explicit owner review and activation, no direct SQL for owner |
| 6.4 | Restricted owner-only GitHub Actions integration | Allowlists, stale-run guard, existing secrets, no arbitrary remote command |
| 6.5 | Positive/negative TTL reconciliation across API/ApiClient/Controller | Correct expiry and refresh after approve, safe fail-open, no per-second polling |
| 6.6 | Shared-library/Range/playback/security regression | Two clients one mapping; two IDs one asset; unknown/original; no leaks |
| 6.7 | Controlled Hostinger gate and documentation/handoff | Existing MP3 unaffected, no new music, separate Stage 6 acceptance |

## Stage 6.1 automated fixtures

PHP tests use a generated one-second WAV and disposable `celikom_test*` MySQL only. They establish that two different exact Track IDs share the same persisted AudioAsset, yield distinct mapping IDs, expose no storage key and resolve via separate service instances. They also verify that pending/approved-inactive records cannot stream; a test-only, transactionally selected approved candidate revokes the original without changing a second Track. **Test fixture SQL is not the production LibraryManagementService**.

The extension suite simulates two distinct `ApiClient` instances against one synthetic server. A new approve becomes visible after the existing 15-second negative TTL, not before. Server-side replacement switching becomes visible after the existing 120-second positive TTL. Requests are counted to guard against polling each tick. Existing tests continue to cover invalid tokens/URLs, authorization, fail-open and network errors.

## Remaining to finish Stage 6 after 6.4

- CLI/management implemented; production write operations have not been exercised, and owner-only release acceptance is still required in 6.7.
- Server-driven cache policy, signed token expiry and the controller's extra retry guard.
- Actual two-browser-installation owner-only gate after green CI; no new Track/music without approval.
- User uploads, moderation admin, accounts, billing and Android remain later stages.

## Safety

Do not touch Hostinger deployment request JSON, live MySQL/audio, secrets, signed URLs or active extension 0.4.4 for this package. No real media or private backups in Git/CI artifacts. Keep PR #6 open and unmerged without explicit owner approval.

## Stage 6.3 CLI implementation notes

Added internal PHP 8.3 wrappers `bin/library-add-track.php`, `library-add-asset.php`, `library-link.php`, `library-approve.php`, `library-activate.php` and `library-disable.php`. They use `LibraryManagementService`, strict allowlisted `--arg=value` parsing, required explicit confirmation flags and sanitized failures. Asset source must be one regular file with a safe basename in private sibling `shared/staging`; an arbitrary path or symlink is rejected. No HTTP route was added. Stage 6.4 must build the restricted GitHub Actions runner before any owner-only Hostinger modification. The current live Stage 5 file and feature flags are unchanged.

## Stage 6.4 restricted GitHub Actions integration

New workflow `.github/workflows/hostinger-library.yml`, restricted input `.github/deploy/hostinger-library-request.json` and validator `.github/scripts/hostinger-library-contract.mjs`. The initial request is `{"operation":"validate"}` and **does not SSH, connect to production MySQL or edit audio**. Later owner-authorized operations include inspect, add-track, add-asset, link, approve, activate, disable. Each request has an exact allowlisted JSON schema, confirmed write intent, pinned repository/branch, a stale-HEAD check and a shared Hostinger concurrency group. Remote requests are verified again by PHP, and only the approved Stage 6 manager is loaded, never arbitrary commands. A per-commit remote one-time claim prevents workflow retries from repeating mutations. `activate` and `disable` require an exact expected active replacement ID, checked under the same Track row lock. No staging filenames, audio, credentials or signed URLs enter the request file. No changes to Stage 5 live server are performed by the first 6.4 commit.

Only after a later owner-approved request changes to a write operation will the workflow attempt a controlled write; initial acceptance covers validation/CI and its runner wiring, not a real production database mutation. Actual Hostinger and owner-only browser acceptance remain 6.7.

## Verified 6.4 evidence (2026-10-09)

- All-source CI + new Action safety tests: https://github.com/manufact-test/nomusic/actions/runs/37916187759 — pass.
- First Actions `validate` (local-only, no SSH): https://github.com/manufact-test/nomusic/actions/runs/37916327886 — pass.
- Actions `inspect` through pinned SSH and private remote read-only SQL: https://github.com/manufact-test/nomusic/actions/runs/37916411482 — pass: one Track, one AudioAsset and one TrackReplacement; public config shows replacements enabled, analytics disabled. No production database writes, no new audio and no deploy. The operation request returns to `validate` afterwards.
- Real live write/activation/disable is **not tested and not authorized by this 6.4 gate**. The next deliverable is 6.5 cached resolve behavior followed by Stage 6.6 regression and 6.7 owner acceptance.

## Stage 6.5 TTL integration (CI passed)

The server accepts optional private `RESOLVE_CACHE_TTL_SECONDS` (default 120, bounded 5–120) and `NEGATIVE_CACHE_TTL_SECONDS` (default 15, bounded 5–60). `ResolveCachePolicy` keeps config and per-track responses consistent. Positive response caching cannot exceed the audio token lifetime minus 30s; this does not change token expiration or permissions. No live environment variable or Hostinger config changes are required for the defaults. Package 6.5 also updates ApiClient and ReplacementController with regression tests before acceptance.

**6.5 evidence:** [CI run 37917754208](https://github.com/manufact-test/nomusic/actions/runs/37917754208) passed 75 JavaScript tests (0 failures), PHP TTL config/resolve contract and disposable MySQL integration. Exact cache fallback still uses the old 120s/15s defaults for legacy server responses; no signed URL is kept beyond the 30-second safety margin. Changing an approved mapping is observed after the relevant TTL **on a subsequent resolve**, not as an automatic mid-playback hot swap. No deployment or live library modification occurred.

**Next:** 6.6 full security, multiple-installations and fallback regression; 6.7 owner-only host/browser gate. Keep PR #6 open.
