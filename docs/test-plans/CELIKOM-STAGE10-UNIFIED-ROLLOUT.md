**HISTORICAL 0.4.7 evidence:** owner subsequently reported real playback failure. Latest deployed correction is 0.4.8, trial 3 days, explicit backed-up owner reset; see [current patch evidence](CELIKOM-STAGE10-048-OWNER-FIXES.md). Stage10 remains OPEN.

# Stage 10 — unified 0.4.7 rollout evidence, 10.10.2026

**State: OWNER PLAYBACK GATE / NOT COMPLETED.** Branch `feature/api-range`, implementation `efdb54d4ad6e53de9b09f8dbd675d24bf66ad25e`. Active private Hostinger release `0.4.7-02c4b4f8073b4b76c407b7ed469e2500301ac665`. Stage 9 accepted/closed; Issue #9 remains OPEN. Attached Master v1.5 / Work Plan v1.6 were read; original DOCX files were not changed.

## Implemented in ONE extension

- Atomic verified-account trial: explicit functional Start → one ledger row and one account trial, database UTC clock, exactly 432000 seconds. Registration/login/read-only checks do not activate or extend it. Parent account lock prevents concurrent device double starts. Ledger and trial roll back together. Existing additive migration 006 retained; new checksummed 007 adds account_trials.
- Normal user access token + EntitlementService authorize approved-only Resolve. No Chrome apiTestToken setup/UI required. Access/refresh credentials remain extension-owned; content/page receives only short-lived signed audio capabilities. Audio v2 signs the session ID and expiry; each HEAD/Range checks unrevoked session and current entitlement. Removing/changing sid cannot downgrade a signature.
- Existing rolling 90-day refresh and independent installation IDs preserved. Logout invalidates local access/cache and prevents a late refresh from resurrecting credentials. Heartbeat denial restores original playback; access validity is clipped to server entitlement expiry.
- Same popup contains accounts, verification/recovery, playback and contribution forms. **Upload version:** MP3 + file-rights confirmation + pending moderation. **Suggest song:** separate exact-current-track action, no MP3/rights checkbox, independent queue, dedupe/throttle. Stable contribution account identity spans refresh/devices. Live public writes remain OFF pending owner playback/security gate.
- Legacy private API_TEST_TOKEN and owner credentials remain only to preserve original installed 0.4.4 during acceptance. They are not required by the clean-install 0.4.7 flow. Do not retire this compatibility path until owner acceptance.

## Verification and recovery

| Gate | Evidence | Result |
| --- | --- | --- |
| Atomic foundation CI | [38061679541](https://github.com/manufact-test/nomusic/actions/runs/38061679541) | PASS |
| Unified PHP 8.3 / MySQL 8 / extension CI | [38062566353](https://github.com/manufact-test/nomusic/actions/runs/38062566353) | PASS: 117 extension + 17 PoC tests; eight trial integration groups; real HTTP/Range/native Chromium media regressions |
| Private Chrome 0.4.7 build | [38062561877](https://github.com/manufact-test/nomusic/actions/runs/38062561877) | PASS; historical workflow/artifact name says Stage9, actual manifest is 0.4.7 |
| Pre-deploy snapshot | [38062748986](https://github.com/manufact-test/nomusic/actions/runs/38062748986) | PASS |
| Pre-deploy isolated file/MySQL restore | [38062917002](https://github.com/manufact-test/nomusic/actions/runs/38062917002) | PASS |
| Guarded deploy with full verification | [38063016987](https://github.com/manufact-test/nomusic/actions/runs/38063016987) | PASS; existing owner credentials preserved |
| Post-deploy env, media, row-count, migration checksum audit | [38063162893](https://github.com/manufact-test/nomusic/actions/runs/38063162893) | PASS |
| Guarded entitlement enable + real HTTPS smoke | [38064228041](https://github.com/manufact-test/nomusic/actions/runs/38064228041) | PASS |
| Post-enable read-only access/media audit | [38064299366](https://github.com/manufact-test/nomusic/actions/runs/38064299366) | PASS |
| Post-enable snapshot | [38064299394](https://github.com/manufact-test/nomusic/actions/runs/38064299394) | PASS: 24 SQL tables and five audio objects |
| Post-enable isolated restore | [38064407087](https://github.com/manufact-test/nomusic/actions/runs/38064407087) | PASS: config, all five audio objects and MySQL schema/mapping recovered; live deployment untouched |

The real HTTPS smoke uses an explicitly isolated temporary verified QA account and two sessions, not a public verification bypass. It verifies no trial before activation, one 5-day deadline across two devices, approved #1 Resolve, signed HEAD/206, denial for both pending tracks, refresh, first-device logout revoking its previously issued audio URL while second-device entitlement stays allowed. Temporary QA account/trial/ledger/events/devices/sessions are deleted in finally. Protected catalog and MP3 hashes are checked before and after.

Earlier guarded smoke attempts hit transient connection/HTTP 503 failures and reverted the feature flag. No failed attempt was treated as acceptance. Argument-free CLI diagnostics were added; pacing HTTP fixture requests stabilized the full scenario. This does not establish a definitive hosting root cause; repeat/network/fail-open behavior remains part of owner observation.

## Exact live state

`replacements=true`, `auth=true`, `entitlement=true`, `analytics=false`, `upload_enabled=false`. Only FEATURE_USER_ENTITLEMENT was enabled. Approved Track ID **144530503**, replacement #1, 180872 ms unchanged. Pending **799133075/#2** and **38436680/#3** unchanged and inactive. Original installed Chrome **0.4.4** untouched; no browser installations were removed or upgraded remotely.

Chrome ZIP SHA-256: `cc4939db175706f5f81f107d23be0d10b98f051a15c4e9081a6d0ec9ce6aee6b`. Packaged `api/config.json` contains only the correct private-test API base URL, no secrets. Install from `CELIKOM-0.4.7-stage10.zip` in a clean separate profile.

## Next authorized step

[Owner Chrome playback checklist](CELIKOM-STAGE10-CHROME-ACCEPTANCE.md): actual approved audio replacement, Play/Pause/Seek/Next/Return/Stop without technical token, second physical profile, logout/refresh. After owner playback/security acceptance, perform backup/restore and enable public Upload/Suggest in this SAME client; verify pending/admin/dedupe manually before closing Stage 10. Billing/payments and future ledger sources are not claimed delivered. No live Android APK acceptance is claimed.

**PR #6 OPEN/unmerged; Issue #7 OPEN; Issue #9 OPEN.** No proof of a RangeError fix, no merge, no stage closure.
