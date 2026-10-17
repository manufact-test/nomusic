# Stage 14 operations and recovery

Do not manufacture a global incident to test UI. Use disposable integration tests.
Do not reset/backfill account trials, sessions, catalog, reward policy or ledgers.

1. Run CI with PHP 8.3/MySQL, native Chromium and isolated MariaDB before release.
2. Build the single client pinned to the existing HTTPS API and verify ZIP checksum
   and security gate. Keep reserve 0.4.4; update existing unpacked installation.
3. Use restricted Stage5 snapshot and isolated restore workflows before server deploy.
   Check current HEAD lease before each request; no live database replacement.
4. Deploy immutable verified package via existing guarded Hostinger workflow, retaining
   existing environment/flags/credentials and applied migrations. Snapshot counts are
   point-in-time evidence, never a permanent expected user/catalog count.
5. Read-only audit compares environment/media hashes and canonical table state to the
   pre-deploy snapshot. Confirm approved 144530503/#1, roles, contribution rate scope,
   API anonymous refusal and existing flags. Real user/manual moderation is untouched.
6. Roll back release pointer to retained previous immutable package if health fails.
   This package has no migration; do not restore old SQL over new user data.

Contribution limits are fixed-hour attempt budgets: account 10 uploads/20 requests;
device 20/40; IP 60/120. Account limit was already present. Each accepted scope uses
an atomic SQL increment, so parallel workers cannot authorize more than its ceiling.
Scopes intentionally count malformed/retry attempts; idempotent result handling does
not grant unlimited free abuse requests. Shared-NAT budgets are higher than account
budgets. Audio Range/HEAD is outside these write quotas. Only server REMOTE_ADDR is
used; if adding a proxy, explicitly configure its trusted chain before using headers.
Bucket keys are keyed hashes; no raw address/device metadata is stored there.

Before customer distribution: configure independent encrypted backup destination,
retention and owner key custody; test provider-loss recovery; verify provider access
logs omit signed query tokens and rotate logs; add disk/free-space alerts using
read-only operational probes. Do not claim these source-independent operations were
executed merely because a runbook exists. Android APK signing key must stay outside
Git and public build logs/artifacts; Stage18 privacy gate remains mandatory.
