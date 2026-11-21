# Promo admin navigation and reported 504 — 11.10.2026

Owner reported 504 while opening creation and switching views. Screenshot shows the activation table and a row mixing creation with two viewing links. Extension itself was reported working; no client version acceptance beyond the existing record is inferred.

Creation is now a separate page and action, apart from a compact selected submenu «Промокоды / Активации». The selected view is a label, not a duplicate request link. Empty lists explain their state. Creation no longer queries or displays code lists. Dedicated GET paths: `/admin/promos`, `/admin/promos/new`, `/admin/promos/activations`; legacy query links remain compatible. Owner role, session, CSRF, lifetime confirmation and all grant/revoke semantics are preserved.

Original 504 cause is not established. On-host read-only render checks completed below 0.001s for all three existing views (38162519293). Authorized existing HTTPS views returned 200 in 0.013–0.021s (38162742422). The diagnostic reuses the existing private owner credential, emits only route number/status/time and deletes only its own temporary session. It does not create codes or grants or rotate credentials. Pre-fix direct paths correctly returned 404 because they were not yet deployed.

Fresh protected snapshots passed: 12 audio objects / 39 SQL tables. No migrations, resets or billing activation are part of this patch. The unified extension stays 0.4.26; no reinstall is needed for this server-side change.

MariaDB 38162862533 PASS, including authenticated direct-path checks and finite/lifetime form submission in disposable fixtures. CI/MySQL/native Chromium 38162865797 and deployment 38162862461 PASS. Backend `0.4.26-03938e9abf0db8d641abad42b0f07271d3b18c23` is deployed. Post-deploy HTTPS confirmation 38163057100 PASS: all six legacy/direct authenticated routes returned 200 in 0.011–0.019s; snapshot retained 12 audio objects / 39 SQL tables. Owner manual confirmation of the updated admin is pending; the reported 504 is not silently declared resolved.

The credential-based diagnostic is removed after this one investigation, so subsequent recovery runs do not perform owner logins.
