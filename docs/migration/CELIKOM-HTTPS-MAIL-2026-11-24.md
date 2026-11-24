# CELIKOM — HTTPS transactional email (FlokiNET)

FlokiNET ticket #477936: outgoing SMTP 25/465/587 requires a refundable EUR 150 deposit. Do not purchase the unblock. The alternative selected for evaluation is Brevo transactional HTTPS API (443), free plan up to 300 sends/day; provider approval and live delivery remain unverified. See https://developers.brevo.com/reference/send-transac-email and https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan.

## Server-only configuration

- In Brevo, activate transactional sending, verify a sender at our own domain and authenticate the domain with the provider-issued DNS records (DKIM/DMARC and any verification records). Preserve existing MX/SPF records; never add a second SPF record. Do not invent DNS values or publish an unverified sender.
- Create a dedicated API key, restrict it to the VPS address if supported; keep it out of Git, GitHub Actions, client packages, chat and shell history.
- Check PHP-FPM has PHP curl enabled, CA certificates available and HTTPS connectivity to api.brevo.com. Install php8.3-curl if absent on the Ubuntu 24.04 staging host; do not change the CI sandbox.
- Deploy only reviewed backend code into the guarded staging release. Keep the existing private .env and the mail code pepper unchanged. Set CELIKOM_MAIL_TRANSPORT=brevo, CELIKOM_BREVO_API_KEY (private), CELIKOM_MAIL_FROM (verified address). SMTP remains available by an explicit config change, not automatic fallback.
- The existing registration/recovery/support flows and limits are unchanged. API calls use fixed HTTPS host, TLS verification, bounded timeout/response, one recipient, no retry or redirects. An HTTP 201 with messageId means accepted by provider, NOT delivered.
- Test using synthetic accounts: register, receive and use code, request reset, receive and use code, test a support message; verify actual inbox delivery and headers. Verify disabled/invalid provider config still fails closed and reset response remains generic. Codes expire after 10 minutes; delayed/free-quota queued mail is not acceptable as a successful delivery test.
- Review provider privacy/data processing, retention and sender identity before real user mail; emails contain addresses, one-time codes and support messages. Do not send catalog/audio, passwords, database dumps or real test logs to the provider.
- Do not switch public API or turn on new commercial flags before the full migration acceptance. Record only sanitized test outcomes. Rollback: restore prior private config/release; do not route through SMTP on FlokiNET while blocked.

## Local regression
`php server/tests/mail-transport.php` — offline request contract, errors, input validation and old test sink/SMTP readiness. No secrets, network, or database required. Included in server foundation CI. Real delivery remains a separate gate.

## 24.11.2026 — delivery checkpoint

- Owner completed all seven Brevo DNS records in Njalla; Brevo confirmed domain authenticated and branded. Sender `noreply@celikom.com` verified; DKIM and DMARC green. Owner explicitly chose full-access API key; keep it server-only and recommend IP restriction after checking egress. Do not request key in chat.
- FlokiNET SSH host test using HTTPS POST to Brevo returned HTTP 201 / `CELIKOM_BREVO_ACCEPTED`; owner supplied screenshot of message received in Gmail inbox from the verified sender. SMTP unblock deposit is unnecessary. This proves direct provider delivery, not yet PHP/FPM application integration.
- Commit `6ac2ff6b60f98adcf85269d0c0040e6d06225dac`: CI run 45390870777 passed repository/runtime tests including `CELIKOM_MAIL_TRANSPORT_TESTS_OK`; final artifact upload failed due to GitHub storage quota. Windows integration run 45390870712 succeeded. Still deploy reviewed backend code in staging, verify PHP curl, securely install API key, then test real registration/reset/support. No public cutover yet.

## 24.11.2026 — PHP staging delivery confirmed

- Owner deployed the hash-verified mailer from commit `6ac2ff6b` into `/srv/celikom/app/staging-20261122`, retaining existing .env bytes and other settings. PHP curl is available. `CELIKOM_BREVO_KEY_SAVED`, `CELIKOM_PHP_BREVO_OK` and `CELIKOM_MAIL_STAGING_READY` confirmed; Gmail inbox screenshot confirms receipt of the real CELIKOM verification message. The test was a direct PHP mailer call as www-data, not an account registration.
- Root-only secret retained at `/root/celikom-secrets/brevo-api.key` (0600, parent 0700); staging .env contains the runtime copy (0640). Backup `/root/celikom-mail-backup-0sddsoeb`. Do not print or request the key again. Two earlier attempts stopped before writes due to decoding; final byte-preserving deployment succeeded. Next: disposable DB end-to-end registration/reset, real inbox codes, session revocation, support mail, then cutover gates. No public API switch or paid entitlement activation.
- FlokiNET persistent spool verified by owner listing of commit `c4479f77b6cd2f54ffbd915f24ae41f259320968`, run 45393144795; both portable and Windows jobs succeeded. 55 GiB free on VPS. Still need separate approved publication/delivery path.
