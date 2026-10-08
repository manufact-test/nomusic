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
- Default SSH CLI: PHP 8.2.33. Project CLI: `/opt/alt/php83/usr/bin/php`, PHP 8.3.33 with `pdo_mysql` and `fileinfo`. The website's HTTP PHP runtime has not yet been measured.
- Status when recorded: website and database created; server deployment pending. HTTPS/API health have not yet been confirmed.
- Direct SSH from the chat runtime fails with `Network is unreachable`. Use GitHub Actions for remote execution. The connection-preflight workflow pins the server key observed at the owner-confirmed hPanel endpoint and verifies the client key fingerprint; it authenticates for read-only runtime/path checks and does not deploy. First-contact host-key observation is not independent identity verification.
- Next setup dependency: the owner must configure `HOSTINGER_DB_PASSWORD` as a repository Actions secret using the password chosen for the CELIKOM database. No passwords or private keys belong in this document.

Domain-specific extension build:

```bash
CELIKOM_API_BASE_URL=https://darkred-camel-588676.hostingersite.com npm run build:extension
```

Deployment procedure: [Hostinger private-test runbook](hostinger-private-test.md). Keep database passwords, API access codes, signing keys and user audio outside Git. Update this execution record when deployment checks complete.
