# CELIKOM Stage 13 — Incident / freeze, 0.4.22

Owner authorized this combined package on 11 October 2026: background-tab popup fix, automatic recovery and independent Stage 13. Owner acceptance of this version is pending. The previous 0.4.21 acceptance remains recorded.

## Behavior

The popup selects the actual Yandex Music tab across windows, preferring active playback when opened from another website. Status and Original/retry commands use the same selection policy. No tab is focused or navigated. Closing every Yandex tab still reports a real missing connection.

Transient worker/bridge/network/player failures restore original playback, preserve the desired enabled state and retry after five seconds with fresh, healthy player state. A playing master whose clock stops advancing for four seconds fails open; replacement resumes only after its clock advances again. Background timer throttling is excluded from this clock detector. Manual Original, Stop and logout remain authoritative. Invalidated extension contexts still restore and stop; updating an extension requires reloading Yandex once. Decode/duration/security failures retain explicit retry rather than repeatedly muting original playback.

Owner-only admin tab **Сбои интеграции** declares and resolves confirmed Yandex integration outages. CSRF is required. Start request keys and resolution are idempotent. Status is published through config and authoritative entitlement decisions; heartbeat suspends replacement while an incident is active, then resumes if still enabled. Local stalls never automatically declare a global outage.

Base trial and paid grants remain immutable. Effective expiry is calculated in UTC with microsecond precision from the union of outage intervals. Time is frozen even if the original expiry would fall within an outage. Activation during an outage receives only its affected portion. Expired-before-outage grants do not revive. Closed incidents journal only newly credited time, with a unique incident/grant key. Service mutex, credit records and audit are transactional; overlapping/concurrent resolutions cannot double credit. Other service incidents do not suspend or extend Yandex access. Revoked payments remain revoked and paid entitlement remains opt-in.

## Automatic verification

- Extension regression: background-tab routing, unhealthy candidate fallback, command target, transient access/incident suspension, bridge recovery, stalled clock, fresh-state admission, manual Original/Stop and invalidated-context safety.
- Disposable MySQL 8 and MariaDB 10.11: exact 3d6h, overlapping union, partial activation, UTC/DST, immutable trial, duplicate start/resolve, paid fixture/production opt-in/revocation, four concurrent resolution workers, audit rollback, owner permissions/CSRF/XSS and account/catalog preservation.
- Migration 014 runs twice; backup allowlists include all three new tables. Before deployment: private snapshot and isolated restore. After deployment: HTTPS/config/auth denial and read-only integrity audit.

## One combined owner review

Install the full 0.4.22 archive in the existing unpacked extension folder; Reload it and refresh Yandex Music once. Keep the working 0.4.4 backup and the existing account.

1. Start on Yandex, switch to another website/window and open CELIKOM. It should show the playing music tab and actual track, without an artificial connection error. Original must apply to that music tab.
2. Continue normal listening. After a transient player/network interruption, original playback is released and connection can recover without pressing Start. Stop and manual Original must not be overridden. An observed repeat freeze should be recorded with timing/extension error; the initial Yandex freeze cause is not established by these changes.
3. Verify the owner admin tab Сбои интеграции is present and readable. Do not announce a global production outage merely to test a button: start/resolve and compensation are already exercised on isolated fixtures. A real confirmed outage can be declared and closed through this tab.

## Deferred commercial dependencies

There is no real payment provider, checkout or live billing webhook. Real recurring pause/resume, genuine paid lifecycle and reward spending/discount application are not complete. Stage 11/12 remain partial; Stage 13 independent implementation is reviewable, but commercial criteria and owner acceptance are not claimed complete. PR #6 stays OPEN/unmerged; Yandex RangeError issue #7 stays open.
