# CELIKOM — current test environment

Recorded from the owner's hosting setup on 2026-10-08.

- Project: CELIKOM.
- Provider: Hostinger, dedicated PHP/HTML website.
- Temporary test/API origin: https://darkred-camel-588676.hostingersite.com
- hPanel site dashboard: https://hpanel.hostinger.com/websites/darkred-camel-588676.hostingersite.com
- Purpose: Stage 5 private live MP3/WAV tests. This is a temporary testing address; the final client domain is undecided.
- MySQL database: `u235811320_celikom`; MySQL user: `u235811320_celikom`. Creation confirmed from the owner's hPanel screenshot.
- SSH endpoint: `92.113.19.189:65002`; SSH user: `u235811320`. SSH status ACTIVE confirmed from the owner's hPanel screenshot.
- The owner added the `CELIKOM GitHub Actions` public key in hPanel and configured the `HOSTINGER_SSH_KEY` repository Actions secret. Authenticated read-only checks passed: https://github.com/manufact-test/nomusic/actions/runs/37823014501
- Confirmed site directory: `/home/u235811320/domains/darkred-camel-588676.hostingersite.com`; document root: its `public_html` directory.
- Default SSH CLI: PHP 8.2.33. Project CLI: `/opt/alt/php83/usr/bin/php`, PHP 8.3.33 with `pdo_mysql` and `fileinfo`. The website's HTTP runtime also passed on PHP 8.3.33 with those extensions and an actual MySQL connection. PHP selection is scoped to this site's `.htaccess`.
- Deployment passed on 2026-10-08: https://github.com/manufact-test/nomusic/actions/runs/37824995803 . Active release: `0.4.0-e0461f56b77e6fea86493e25c39af4a8eddbabb6`. CI for the same application revision passed: https://github.com/manufact-test/nomusic/actions/runs/37825005035 .
- Database initialization and migration `001_catalog_and_analytics.sql` succeeded; the second migration pass was a no-op. Private shared configuration and audio/staging directories are outside `public_html`. Signing, privacy and beta-access keys were generated on the server and are not in Git or logs.
- HTTPS health/config passed on the hosting side and from the external GitHub runner. The external runner also verified Yandex CORS and unauthenticated resolve rejection (401). The temporary runtime/DB probe was removed.
- Current flags: replacements disabled, analytics disabled. No owner audio has been imported, and the live Yandex MP3/WAV gate is still pending.
- Direct SSH from the chat runtime fails with `Network is unreachable`. Use GitHub Actions for remote execution. The connection-preflight workflow pins the server key observed at the owner-confirmed hPanel endpoint and verifies the client key fingerprint; it authenticates for read-only runtime/path checks and does not deploy. First-contact host-key observation is not independent identity verification.
- The owner configured `HOSTINGER_DB_PASSWORD` as a repository Actions secret. Future deployments are requested through `.github/deploy/hostinger-request.json`; the workflow verifies the immutable revision before deployment. Public files and the previous release are restored if the hosting-side HTTPS gate fails; this rollback was exercised with isolated filesystem/HTTP fixtures, not a deliberate live outage.
- Next dependency: owner-reviewed MP3/WAV in `celikom/shared/staging`, exact Yandex Track ID and duration. Import through the private CLI; then enable replacements and run the real-page playback checklist. The beta access code can be retrieved privately by the owner over SSH for the extension.

Domain-specific extension build:

```bash
CELIKOM_API_BASE_URL=https://darkred-camel-588676.hostingersite.com npm run build:extension
```

Deployment procedure: [Hostinger private-test runbook](hostinger-private-test.md). Keep database passwords, API access codes, signing keys and user audio outside Git. Update this execution record when deployment checks complete.
