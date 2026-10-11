# Stage 14: independent security and resilience audit — 2026-10-11

Baseline: feature/api-range ed44cb194c7be2e3b22676adb06a1c0a3a46026d.
Authorities: CHECKPOINT-2026-10-11, Master MVP 1.5 and Plan 1.6 attachments.
Client 0.4.24 installed; server 0.4.23 before this package. Stage 15 excluded.
This work does not certify real billing or close Issue #7/#10/#11/#12/#13.

## Findings and remediation

| Finding | Evidence / risk | Change and regression |
| --- | --- | --- |
| Worker commands lacked a common sender check | Auth/API checked sender but status, enabled, original and add-track commands did not | Exact own popup URL and extension id; rejected page/content/foreign/malformed senders make no writes or activation |
| Auth JSON buffered whole body before size check | Chunked body without Content-Length could exceed the limit while buffering | Stream byte limit 16 KiB and cancellation; oversized chunked response leaves secret store empty |
| Delayed Start could undo later Stop/Original/logout | Start awaited network before writing enabled=true | Intent generation rejects obsolete completion and obsolete heartbeat cache; delayed Start/Stop, Start/Original and Start/logout regressions |
| Contribution limiter covered account only | Multiple accounts on one device/IP could bypass that scope | Existing account cap plus stable installation UUID and REMOTE_ADDR HMAC buckets; no raw IP or forwarded-header trust; writes only, Range excluded |
| Build scanning and dependency review had no explicit gate | Source lint existed; bundle and future dependency additions needed a boundary | Build gate checks credential patterns, maps/signing files, MV3/CSP/permissions; dependency inventory rejects unreviewed new npm/Composer packages |
| Nested private configuration/signing files were not forbidden uniformly | Root-only .env check did not cover nested files | Repository lint rejects nested .env/private-key filenames and binary signing stores |

No migrations, backfill, trial reset, reward-policy update or real incident are needed.
Owner/API credentials and legacy 0.4.4 are retained. Main-world bridge is an
untrusted page interface, not a cryptographic identity. Account tokens stay in
extension-origin IndexedDB; page cannot invoke account commands. Short-lived
session-bound audio capabilities and actual media elements remain visible to
page code as required for web playback; they are not durable account credentials.

## Existing protections reviewed

| Boundary | Source / checks |
| --- | --- |
| Customer credentials | AuthService KDF, opaque hashed access/refresh, replay revocation, independent sessions; BearerAuthenticator verified active account |
| Admin | AdminAuth Secure/HttpOnly/SameSite=Strict host cookies, CSRF, IP/login throttle; AdminPanel role gates, no-store/CSP/frame restrictions, escaped HTML and CSV formula escaping |
| Audio/storage | Approved active mapping only, version/session-bound expiring signature; byte-exact Range; LocalStorageAdapter rejects traversal/symlinks/public roots and creates private files |
| Upload/request | Container/full-frame/size/rights validation, random keys, pending-only, exact SHA-256/idempotency/transaction/race tests |
| API/CORS | Exact allowed origins, no credentialed wildcard, no-store JSON; safe 503 codes without SQL/password/path; client fixed HTTPS origin, omitted cookies and rejected redirects |
| Privacy | No service cookies/passwords/browser history; aggregate technical events; analytics default OFF, configurable raw-event retention; HMAC identity scopes |
| Recovery/kill switch | Existing snapshots/disposable restore/guarded release; owner service incident, FEATURE_REPLACEMENTS and contribution flags; fail-open watchdog and transport recovery |

## Required evidence for this package

Local: lint, 171 extension tests, 17 PoC tests, manifest/build and security gate.
PHP/MySQL/native Chromium are required in GitHub CI; local missing PHP/browser
is a deferred check, not PASS. MariaDB quota/auth tests must also pass before rollout.
Rebuild pinned single client with exact existing Hostinger API; verify reproducibility,
ZIP SHA256 and no privileged credentials. Preserve PR #6 OPEN/unmerged.

Run snapshot and isolated restore before backend rollout, then read-only integrity
comparison. No real incident, live account/trial changes or real upload for tests.
Commercial fixtures remain isolated; provider webhook/checkout/fraud checks remain
pending actual integration. Do not use test BillingAdapter on live.

## Release limitations retained

Independent encrypted offsite disaster recovery and signing-key custody need a
configured destination/key under owner control before client release (Stage 18).
A same-provider snapshot is not offsite recovery. Provider log policies/rotation,
access-log query redaction and sustained capacity observability need operational
verification; source error-log redaction alone does not certify provider access logs.
The credential-pattern scan is a bounded check, not a guarantee of all secrets in
Git history. Runtime PHP/Node/OS and Actions have their own patch/CVE obligations;
there are currently no third-party application npm/Composer packages.
Source privacy, Android release signing/distribution and real payments remain open.

After the independent checks pass, Android technical PoC 16 can begin without
Alpha or provider selection. Android playback requires proof of an exact permitted
surface and fail-open; companion scope is the fallback when proof is absent.
Owner limited free-access promo task remains independent Stage12 work, not implemented
by this security package and no grants issued.
