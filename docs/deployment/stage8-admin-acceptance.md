# CELIKOM — Stage 8 private moderation acceptance and rollback

Status 2026-10-10: **STAGE 8 OWNER ACCEPTED & CLOSED**. Owner explicitly allowed closure without further manual UI verification after final picker cosmetic fix. Technical gates PASS; Stage 9 paused until separate owner-requested document work. Historical deployment instructions below are reference only; do not re-run acceptance or change real tracks. Branch `feature/api-range`; PR #6 OPEN/UNMERGED and Issue #7 OPEN.


## Formal Stage 8 closure (10.10.2026)

Owner accepted the admin UI and authorized closing Stage 8 without repeat manual checks. Final change: rejection reason selector styled in CELIKOM mint using customizable native `select` CSS on compatible Chromium, with fallback and no outer focus halo. It does **not** alter approval/rejection rules, rights checks or audio. [Final gated deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/37995952723), [pre-deploy backup](https://github.com/manufact-test/nomusic/actions/runs/37995694271), [isolated recovery PASS](https://github.com/manufact-test/nomusic/actions/runs/37995808661), [read-only postdeploy audit PASS](https://github.com/manufact-test/nomusic/actions/runs/37996133162). All original data and five audio hashes unchanged. Release: `0.4.4-6121a91b570e384095d65c9f9562347eb735e967`.

**Do not begin Stage 9 until after the user's document task is handled.** Stage 10 public `Предложить песню` remains a required MVP feature; no audio / rights checkbox on a mere suggestion. Keep admin credentials private. No live moderation actions performed in closeout.

## Deployment verified on 2026-10-09

- Owner authorized ongoing safeguarded technical deploy/rollback actions. Pre-deploy [10-table/5-file snapshot](https://github.com/manufact-test/nomusic/actions/runs/37984859454) and [isolated recovery](https://github.com/manufact-test/nomusic/actions/runs/37985091060) passed.
- [Deploy 37985244995](https://github.com/manufact-test/nomusic/actions/runs/37985244995) created immutable release `0.4.4-ac2b41dd010afef934da2ab8b434e8c0f08048b9` and applied additive migration 003. Existing Stage 7 owner token was NOT rotated; `FEATURE_OWNER_REPORTS=0`, public uploads disabled.
- Independent [post-deploy integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37985609247) passed for preexisting data counts, original active replacement, entire private audio hashes and configuration. The only permitted schema migration row addition was checksum-verified 003.
- [Owner CLI provisioning](https://github.com/manufact-test/nomusic/actions/runs/37985814317) succeeded, enabled `FEATURE_ADMIN=1` in private `.env`, confirmed HTTPS login 200 and anonymous private audio 403. Login `owner`; initial password in Hostinger-private `celikom/shared/stage8-owner-login-once.txt` mode 0600, NOT in public GitHub artifacts or chat. Remove this plaintext copy once the owner has securely retrieved credentials and logged in.
- [Postbootstrap snapshot](https://github.com/manufact-test/nomusic/actions/runs/37985992296) contains all 16 tables and five audio objects; [isolated file and MySQL restore](https://github.com/manufact-test/nomusic/actions/runs/37986120772) passed. Backups are within Hostinger, not yet independent offsite DR.
- No real music moderation performed: approved #1 (Yandex 144530503) intact; #2 (799133075) and #3 (38436680, «Вспышка») stay pending. Stage 8.7 owner actions remain necessary to accept the *interface*; do not approve these pending items without actual rights validation.


## Existing gates / safety

- PR #6 remains OPEN/UNMERGED; Issue #7 recurrent MAIN-world RangeError stays OPEN.
- Default config has \`FEATURE_ADMIN=0\`, \`FEATURE_OWNER_REPORTS=0\`, \`FEATURE_UPLOADS=0\`. \`API_TEST_TOKEN\` is read-only and **cannot submit reports**, moderate, or log in as admin.
- Nothing may automatically approve \`pending\`. The accepted "Вспышка" (Yandex ID 38436680 / replacement #3) and synthetic pending (799133075 / #2) remain inactive until a separate owner-authorized administrative decision. Existing approved replacement #1 (144530503) must not change.
- Migration \`003_admin_moderation.sql\` adds admin tables, sessions, throttling, audit, report queue and request reviews without destructive data changes. It must be applied **only to isolated DB** until owner explicitly authorizes production changes.
- The owner bootstrap is CLI-only and reads the password through STDIN; do not pass a password as a command argument, commit it, put it in GitHub secrets unless specifically needed, or paste it into ChatGPT.
- Deployment must maintain TLS with secure host-only cookies and private StorageAdapter directory outside webroot. Anonymous URLs \`/admin\`, \`/admin/login\`, \`/admin/audio/:id\` do not exist while admin feature is disabled.

## Safe technical gate (no owner work)

1. Run the existing \`CI\` action (PHP 8.3/MySQL disposable \`celikom_test\`, JS and Chromium) for exact branch HEAD.
2. Ensure \`server/tests/admin.php\` completes: admin login, login throttling, session expiry, roles, CSRF on mutating endpoints + CSV, private range MP3, upload pending confidentiality, explicit rights-check approval, 4-worker row-lock race, disable/explicit owner reactivation, complaints, suggestion processing, audit and real overview values.
3. Confirm report intake disabled with \`FEATURE_OWNER_REPORTS=0\`, requiring separate \`REPORT_OWNER_TOKEN\` when privately enabled. Do not enable for client/public use before accounts.
4. Verify \`/api/v1/resolve\` continues to return **only** active approved data; rejected and disabled mappings do not resolve. Existing signed range playback should remain unaffected.
5. Confirm PR #6 stays open and Issue #7 not automatically closed.

## Private Hostinger gate (completed with owner permission; historical steps)

**Authorization granted and deployment completed on 2026-10-09.** Take a private storage/DB backup and verify restoration path. Prepare a separate private admin environment or a controlled, backed-up additive migration. Do not enable public uploads. Apply 003 migration only after backup and approval. Provision an owner in the terminal with a strong unique password using non-echoing input: e.g. \`read -sr pw; printf '%s\n' "$pw" | php server/bin/admin-create.php <login>; unset pw\` (execute from a trusted shell; adapt path to deployment). Avoid outputting, storing, or sharing the password.

Enable only \`FEATURE_ADMIN=1\` for the approved private origin. Keep \`FEATURE_OWNER_REPORTS=0\` unless a distinct private report test is planned. Verify strict HTTPS, session cookies, admin login, two queues, audit overview, logout and private Range player. Verify unauthenticated preview returns 403. In an **isolated** dataset, seed one synthetic pending MP3 and suggestion; manually review them; confirm exact resolve after approval and fail-open after disable. Never select the real owner recordings for irreversible actions without explicit instruction and legal rights review.

## Manual owner acceptance gate (Stage 8.7)

Owner signs in to a private URL, opens *Загруженные версии*, listens to one authorized pending fixture, views true Track ID and difference in audio duration, confirms rights before approving, checks resolve and disable. Separately open *Предложить песню* queue with a no-MP3 request; mark reviewed/rejected and see the audit entry. Check logout and reopen. For any real song, confirm rights documentation before activation. Acceptance is not achieved by CI alone.

## Not forgotten — mandatory MVP

At **Stage 10**, render a distinct public \`Предложить песню\` action alongside \`Загрузить версию\`. Auto-populate the exact current Yandex Track ID, artist/title and a strict \`https://music.yandex.ru/track/{id}\` link. Do not require MP3 or an audio-rights declaration. User auth, dedupe and anti-spam must be enforced before public exposure. The admin Stage 8 track_requests queue is the destination. No request automatically publishes audio.

## Rollback

Keep admin and report gates default OFF and take verified DB/storage snapshot before any future deployment. If private test access is unsafe, set \`FEATURE_ADMIN=0\` (and \`FEATURE_OWNER_REPORTS=0\`), invalidate sessions in \`admin_sessions\` after backing up, and restore the last known good release. Do not roll back the entire production DB or touch the previously approved track to solve an admin-only issue; additive schema can stay dormant.
