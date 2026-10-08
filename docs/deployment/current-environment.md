# CELIKOM — current test environment

Recorded from the owner's hosting setup on 2026-10-08.

- Project: CELIKOM.
- Provider: Hostinger, dedicated PHP/HTML website.
- Temporary test/API origin: https://darkred-camel-588676.hostingersite.com
- hPanel site dashboard: https://hpanel.hostinger.com/websites/darkred-camel-588676.hostingersite.com
- Purpose: Stage 5 private live MP3/WAV tests. This is a temporary testing address; the final client domain is undecided.
- Status when recorded: website created; database creation and server deployment still pending. HTTPS/API health have not yet been confirmed.

Domain-specific extension build:

```bash
CELIKOM_API_BASE_URL=https://darkred-camel-588676.hostingersite.com npm run build:extension
```

Deployment procedure: [Hostinger private-test runbook](hostinger-private-test.md). Keep database passwords, API access codes, signing keys and user audio outside Git. Update this execution record when deployment checks complete.
