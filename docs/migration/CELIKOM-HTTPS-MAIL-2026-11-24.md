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
