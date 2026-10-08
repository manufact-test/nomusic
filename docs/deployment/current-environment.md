# CELIKOM — current test environment

Recorded from the owner's hosting setup on 2026-10-08.

- Project: CELIKOM.
- Provider: Hostinger, dedicated PHP/HTML website.
- Temporary test/API origin: https://darkred-camel-588676.hostingersite.com
- hPanel site dashboard: https://hpanel.hostinger.com/websites/darkred-camel-588676.hostingersite.com
- Purpose: Stage 5 private live MP3/WAV tests. This is a temporary testing address; the final client domain is undecided.
- MySQL database: `u235811320_celikom`; MySQL user: `u235811320_celikom`. Creation confirmed from the owner's hPanel screenshot.
- SSH endpoint: `92.113.19.189:65002`; SSH user: `u235811320`. SSH status ACTIVE confirmed from the owner's hPanel screenshot.
- Status when recorded: website and database created; server deployment pending. HTTPS/API health have not yet been confirmed.
- Direct SSH from the chat runtime fails with `Network is unreachable`. Use GitHub Actions for remote execution after one-time key/secret setup. The connection-preflight workflow only observes public SSH host keys; it does not authenticate or deploy. Host keys still need to be checked against a trusted owner-side connection before use for deployment.

Domain-specific extension build:

```bash
CELIKOM_API_BASE_URL=https://darkred-camel-588676.hostingersite.com npm run build:extension
```

Deployment procedure: [Hostinger private-test runbook](hostinger-private-test.md). Keep database passwords, API access codes, signing keys and user audio outside Git. Update this execution record when deployment checks complete.
