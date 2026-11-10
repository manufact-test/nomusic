# Browser extension access audit — 2026-11-10

Status: source review in progress; isolated regression run pending. This document is not production approval.

## Scope and preserved versions
- Accepted extension: 0.4.73, `63d8cd891e1db82e0245122391fd4ab5cdd323be`.
- Server reviewed: `7e648eacaeb50cc371842590ed7a30284e440d2a`.
- No playback source changes, production deployment, migrations, real payments, trial resets, account/session changes or Android/Windows application changes.
- The workflow uses disposable MySQL and synthetic fixture audio; it has no production secrets.
- Local execution environment became unavailable; current runtime checks use isolated GitHub Actions instead.

## Findings requiring release attention
1. The checked server has a billing lifecycle foundation, NOT a connected payment-to-playback implementation: no concrete BillingAdapter is registered by Application; public checkout/webhook routes are absent; all Application and AudioAccessService EntitlementService constructions use default billingEnabled=false. FEATURE_BILLING_VIEWS only exposes a read model. Merely enabling that flag or showing a successful checkout cannot grant paid playback.
2. A legacy API_TEST_TOKEN bearer deliberately bypasses account entitlement and can mint v1 unbound audio URLs. It is not present in the accepted account-only client. Before commercial launch verify privately that it is unset on the actual deployment, or remove/isolate legacy access in a coordinated server change. This review does not establish a leaked token. Production configuration was not inspected.
3. Trial is per verified account, not per human. A new independently verified email can create a new account/trial; registration throttling reduces bulk requests but is not proof of one person/one trial. No invasive device fingerprinting or payment requirement was introduced.
4. Already delivered audio bytes and transferable short-lived signed URLs cannot be made secret from their authorized recipient by hiding JavaScript. The server remains the access boundary; URL expiry, session revocation and entitlement are rechecked on each new HTTP Range request. Existing delivered bytes are not retroactively revoked.

## Source-confirmed controls (runtime results pending)
- Explicit verified activation, one stored trial per account, parent row lock across devices, exactly 259200 seconds on the database clock, immutable ledger/window agreement.
- Anonymous/expired/revoked accounts cannot resolve account-bound media. Signature binds replacement/version/expiry/session; removing/changing sid cannot downgrade an account URL.
- Browser display-preview cache is not authorization. Fresh checks gate descriptors; heartbeat revalidates playing/cached audio, source restores to original on denied/unavailable access.
- Playback authority cache is bounded to ten seconds and finite entitlement deadline; network failure does not renew authority. Wall-clock checks in the client are not a server security boundary.
- Promos require owner-issued grants, verified account, activation limit and one-use records; lifetime owner promos are intentional exceptions.
- Payment foundation checks verified canonical events, server quote amount/currency, unique events/charges, exact grant windows, refund/chargeback revocation and concurrent writes. These fixture adapter checks are not real provider verification.

## Before payment activation
Confirm the exact current provider/backend branch and deployed release; wire one verified billing-enabled decision consistently into entitlement, resolve and Range, without enabling it just because billing views are enabled. Verify real provider sandbox checkout, webhook authenticity, server amount/currency, replay, out-of-order events, refund, renewal failure and paid expiry through HTTP. Verify ordinary account expiry restores original, payment grants the same account access on independent sessions, and admin promos remain valid. Only then perform a coordinated production rollout; no production rollout is authorized by this audit.

## Evidence
Isolated workflow: `.github/workflows/desktop-access-readiness-audit.yml`.
Final run URL and measured results will be appended after completion.
