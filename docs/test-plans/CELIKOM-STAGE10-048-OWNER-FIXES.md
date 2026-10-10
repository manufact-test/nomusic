# CELIKOM 0.4.8 — owner corrections, 10.10.2026

**Stage 10 / Issue #9 OPEN. Real Yandex playback NOT accepted.** Owner reported that 0.4.7 briefly displays active replacement, then restores original or stops with no actual substitution. Owner login worked after page reload; no evidence of account loss. A fixed empty area below the auth form was reported with screenshot. Owner explicitly changed trial from five to **three days** and authorized restarting existing private-test account trials.

## Applied corrections

- Installed-worker heartbeat now responds immediately, separately from asynchronous entitlement HTTP checks. In 0.4.7 each liveness reply could wait for auth/me and entitlement requests (each has an 8-second network timeout), while MAIN has a 12-second visible-page watchdog. This is a demonstrated defect and plausible contributor to reported fallback; it is NOT proof that all causes of the owner's real playback failure are fixed. Authorization denial/network failure still disables playback and returns original; Range access remains server-enforced. Existing watchdog and extension-removal safety retained.
- Auth panel uses natural content height with a bounded internal scroll region. Removed the forced 315px height/min-height responsible for the screenshot's blank area. Controls and verification/recovery preserved.
- New trials last exactly **259200 seconds / 3 days** on the database clock. New migration 008 atomically replaces the duration constraint while permitting legacy five-day rows during rollout. Applied 007 was NOT edited. Owner's explicit three-day amendment supersedes the duration in attached Master v1.5; original DOCX attachments were not changed.
- Existing trial bindings were backed up and cleared by CLI-only guarded operation. User/password/email verification/device/session rows unchanged. Old ledger entries kept; a zero-duration admin `owner_trial_reset` audit entry grants no access. Next functional Start creates a fresh three-day trial in the same account.
- Reset retry matches ONLY backed-up original user/ledger/time bindings. It cannot delete a newly started trial or add duplicate reset audit events. Operation was changed back to read-only `audit` immediately after success.

## Passed gates

| Gate | Evidence | Result |
| --- | --- | --- |
| Core PHP/MySQL/extension CI | [38065682079](https://github.com/manufact-test/nomusic/actions/runs/38065682079) | PASS: 118 extension tests + 17 PoC tests; eight trial integration groups; unresolved entitlement heartbeat regression |
| Private Chrome 0.4.8 ZIP | [38065678861](https://github.com/manufact-test/nomusic/actions/runs/38065678861) | PASS |
| Pre-deploy snapshot | [38065999333](https://github.com/manufact-test/nomusic/actions/runs/38065999333) | PASS: 24 tables, five audio objects |
| Pre-deploy isolated restore | [38066120356](https://github.com/manufact-test/nomusic/actions/runs/38066120356) | PASS |
| Full verify + guarded deploy | [38066262445](https://github.com/manufact-test/nomusic/actions/runs/38066262445) | PASS |
| Post-deploy preservation/checksum audit | [38066447299](https://github.com/manufact-test/nomusic/actions/runs/38066447299) | PASS |
| Authorized reset + real HTTPS three-day/two-device/Range smoke | [38066571127](https://github.com/manufact-test/nomusic/actions/runs/38066571127) | PASS |
| Post-reset access/media audit | [38066674707](https://github.com/manufact-test/nomusic/actions/runs/38066674707) | PASS |
| Post-reset snapshot | [38066674679](https://github.com/manufact-test/nomusic/actions/runs/38066674679) | PASS |
| Post-reset isolated restore | [38066862776](https://github.com/manufact-test/nomusic/actions/runs/38066862776) | PASS |

Two initial snapshot attempts from ubuntu-latest hit SSH connection timeout before any mutation. Retry from ubuntu-22.04 passed; guarded SSH jobs now use that pool with identical pinned target, key and host fingerprint. Hosting cause is not definitively established. HTTP API stayed reachable. No SSH safety check was relaxed.

## Current deployment and next check

Active server release: `0.4.8-86467ba5e374910c6c7a7f229f3fdbeb958c0729`. replacements/auth/entitlement ON; analytics/public uploads OFF. Approved **144530503/#1** and pending **799133075/#2**, **38436680/#3** unchanged; MP3 hashes verified. PR #6 OPEN/unmerged, Issue #7 OPEN (no proven RangeError fix).

ZIP: `CELIKOM-0.4.8-stage10.zip`; SHA-256 `8518f92de3a7ddee652969bb62df1a86adaabb3b112cb20c6fcb39d52fcfd93b`. Packaged manifest/version and Hostinger API origin independently checked; no test token needed.

Update installed 0.4.7 IN PLACE: overwrite its existing unpacked folder, reload the Chrome extension, then reload the Yandex tab. One enabled CELIKOM per profile; original 0.4.4 retained as reserve, not deleted. Existing email/password works; no new registration. Trial starts on next Start. First retest requires only the owner's existing profile. Clean second profile/two-device acceptance follows later, not another product.

[Exact Chrome checklist](CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Owner must hear actual approved replacement and verify Play/Pause/Seek/Next/Return/Stop. If fallback persists, collect popup Diagnostics immediately after failure to identify lastRestore/replacementError/recentLog. Public Upload/Suggest remain off until playback/security acceptance, then test them in THIS SAME client before Stage 10 closure. No billing or Android live acceptance claimed.
