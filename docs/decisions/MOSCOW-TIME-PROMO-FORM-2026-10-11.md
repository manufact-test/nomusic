# Moscow time and promo form — 11.10.2026

Owner requested removal of the explanatory paragraph from code creation, grouping lifetime with duration, and showing the deadline only after choosing «До указанной даты». The activation-window selection and its semantics are accepted and retained, including the initial «Выберите» option. A code with cap 2 can grant access to two different accounts once each. Lifetime remains restricted to 100% and still requires a separate owner confirmation.

The actual creation form uses scoped layout and a CSP-hashed script. Deadline is hidden/disabled until fixed-date selection, then appears directly below the selector and is required. Lifetime hides/disables the days field; changing discount below 100 disables and clears lifetime. Server validation remains authoritative.

Moscow (`Europe/Moscow`) governs user input/display, extension access labels regardless of computer timezone, admin promo lists, moderation/report/audit timestamps including CSV, incident timestamps, reward expiry display, and operational/financial date-filter boundaries. New reward allocation months and availability follow Moscow calendar boundaries. Previously recorded reward policy, ledger, allocations, entitlements and deadlines are not rewritten, reset or backfilled. Absolute timestamps, API ISO dates, storage, 72-hour trial, sessions, elapsed durations and incident compensation keep UTC internally.

UTC archival analytics aggregates remain preserved. The operational overview computes Moscow intervals from retained raw events, without reinterpreting existing UTC daily rows as Moscow days. Historical raw-event retention limits continue to apply; no archived history is silently shifted or regenerated. Billing remains disabled; provider-dependent work, discounts below 100%, recurring billing and real payments are not implemented by this patch.

Future Android stage 16 must use the same Moscow product timezone; no Android implementation is claimed by this fix.

Unified client version 0.4.27 includes only the Moscow access label and synchronized version identifiers. No separate functional client. No migrations or live promo grants/incidents/test uploads. PR #6 remains unmerged; stage 15 excluded, remaining stage 14/16/17/18 constraints unchanged.

CI/MySQL/native Chromium 38164907938 PASS: 177 client tests, 17 playback PoC regressions, real server-rendered promo form desktop/mobile, Moscow deadline and UTC conversion, month boundary, immutable prior allocations, no real incident. MariaDB 38164904828 PASS. Configured private client ZIP 38164624565 PASS (same client source; subsequent commits affect server/test code only). Pre-deployment snapshot 38164945424 PASS: 12 audio objects / 39 SQL tables.

Deployment 38165076903 PASS (verify + deploy); backend deployed `0.4.27-4488693f440c50c15a4ce401aa0000ff1c0f3f8f`.

Full configured unified ZIP: `CELIKOM-0.4.27-full.zip`, 2441234 bytes, SHA-256 `f5e64b5203941f52a815d2333209fe71ff86a6ba5e5c05ea17eab9e20e4b9e31`. Owner manual verification of new form and promo activation remains pending.
