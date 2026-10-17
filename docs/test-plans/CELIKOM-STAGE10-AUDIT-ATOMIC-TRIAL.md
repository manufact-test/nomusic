# Stage 10.0–10.1 audit and atomic trial foundation — 2026-10-10

## Baseline and evidence

Audited `feature/api-range` at `8a24929b4aa7bf72b4905a469f0a5d1384f6544b`.
The attached Master MVP v1.5 (Stage9 closed/Stage10 next), Plan v1.6 §15,
Issue #9, current handoff, status and Stage10 unified plan define scope.
PR #6 is open/unmerged; Issue #7 is open. Baseline CI [38060737015](https://github.com/manufact-test/nomusic/actions/runs/38060737015) passed.

Read-only live `/api/v1/config` returned replacements=true, auth=true,
analytics=false, upload_enabled=false, positive cache 120s and negative cache 15s.
Private on-host env/SQL/audio integrity was not inspected during this package.
The installed owner Chrome 0.4.4 was not accessed or changed.
Code rollback reference: `backup/stage10-before-atomic-trial-20261010` at audited HEAD;
a local git bundle also preserves the baseline. No Hostinger deployment or live data writes.

The branch already contained incomplete Stage10 scaffolding despite documents
saying NOT STARTED. TrialService and EntitlementService referenced nonexistent
users.trial_started_at/trial_ends_at columns. TrialService did not use the ledger,
EntitlementService used second-resolution PHP time, and BearerAuthenticator omitted
active-account/verified-email checks. Baseline CI did not exercise these services.

The playback engine is present in the same extension as auth/UI. The remaining
integration gap is real: api-broker reads apiTestToken from Chrome storage;
auth-broker keeps user credentials in extension-origin IndexedDB;
Application Resolve only accepts API_TEST_TOKEN. No user-bearer playback is claimed.

## First safe package

- Add restartable migration 007 creating account_trials (one row per account),
  linked to existing migration 006 entitlement_ledger. Do not rewrite prior migrations
  or backfill from historical Stage9 first_activated_at.
- Explicit TrialService activation locks the users row, verifies active status and
  verified email, samples database UTC clock, creates exactly 432000 seconds and
  writes ledger + trial in one transaction. Concurrent/reinstalled devices share
  the same immutable deadline, including after expiry. Nested external transactions
  are rejected without committing/rolling them back.
- Read-only EntitlementService checks status/email, database-clock half-open interval
  and matching canonical ledger, returning allowed/source/valid_until/reason.
  Dates are UTC ISO 8601 with microseconds. Billing/grants/freeze are later sources.
- Harden the currently unused bearer scaffold to match Stage9 active/verified rules.
- Wire seven disposable MySQL test groups into existing CI: no implicit activation,
  exact duration, account denials, database-clock expiry boundary, rollback on ledger
  and trial insert failure, two independent worker races, bearer restrictions,
  migration rerun and unchanged catalog.

No new public endpoint or automatic activation is enabled in this package.
Existing auth/activate retains Stage9 behavior until the integration package.
No public uploads, approved/pending mappings, MP3, admin, 90-day refresh policy,
Chrome version or playback code changes.

## Validation and next package

Local `npm run ci` passed JavaScript tests, repository validation and both builds;
PHP is unavailable locally, so database/runtime validation must pass GitHub CI
(PHP 8.3, disposable MySQL 8, existing HTTP/Chromium/audio regressions).
See the latest branch CI for the authoritative runtime result.

Next: integrate explicit verified-session activation and GET entitlement with
user-bearer Resolve and user/session/expiry-bound signed Range capabilities;
then connect the same background auth broker to the existing playback engine.
Never pass refresh/access tokens into Yandex MAIN-world. Preserve 90-day rolling
independent device sessions and fail-open original audio.
Do not expose cached signed URLs after logout/denial. Prevent pending streaming.
Upload vs Suggest Song follow behind default-off feature gates. Hostinger needs
snapshot + disposable restore + guarded deployment + read-only integrity audit.
Stage10 and Issue #9 remain OPEN until owner playback acceptance on approved
144530503 in a clean unified installation without apiTestToken. PR #6 and Issue #7 stay OPEN.
