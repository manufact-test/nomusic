# CELIKOM — Stage 7 owner-only upload acceptance (isolated environment)

Last updated: 2026-10-09. Requirements: Master ТЗ MVP v1.5 §§11–13 and Plan MVP v1.6 Stage 7.
This runbook is **preparation only**, not permission to deploy or alter the live library.

## Invariants

- Protected production Hostinger: `https://darkred-camel-588676.hostingersite.com`; live approved Track 144530503 / Replacement 1. **Do not migrate, enable uploads, write real MP3, change configuration, or deploy Stage 7 to this environment** without a new explicit authorization.
- Working ref `feature/api-range`. PR #6 remains open; never merge without owner authorization. Stage 6.7 issue #7 remains unresolved.
- Public `/api/v1/config.upload_enabled` remains `false` until account/entitlement Stage 10. `FEATURE_OWNER_UPLOADS` defaults to `0`. The internal privileged upload bearer is independent from playback `API_TEST_TOKEN` and must never be committed.
- Every new upload and track suggestion is pending. No Stage 7 route can approve, activate, resolve or stream unreviewed media. Stage 8 will implement moderation.

## Gate A: automated CI on disposable infrastructure (no human or live deploy)

CI workflow `.github/workflows/ci.yml` uses disposable MySQL (`celikom_test`), a private temp audio directory, ephemeral bearer tokens and synthesizes a 2.5s sine-wave MP3 **using FFmpeg installed only on the CI runner**. No real track/audio, credentials or live server is involved.

CI covers file integrity, measured duration, rejection of corrupted/truncated/bogus MP3, ID3, SHA-256 identity and renamed requests, multi-Track reuse of one AudioAsset, retry/idempotency, rights declaration, owner-only gate, API 401/415/413, pending isolation in /resolve and /audio, and four-worker concurrent same-Track uploads. Chromium verifies playback and seek of independently generated MP3 on the **test-only fixture endpoint**; this does not expose pending audio through production routes.

A green run is necessary, not sufficient for owner acceptance.

## Gate B: build artifact pinned to *separate* private testing origin

This gate needs a different HTTPS origin, private database, separate audio storage and independent credentials. Do not use the existing production Hostinger URL or DB, even with a different path.

Provision (only after explicit owner approval for the intended test environment):

1. Create a disposable isolated MySQL database named `celikom_test_stage7`; do not import production credentials or any real approved mapping. Initialize migrations `001_*.sql` and `002_pending_uploads.sql` through the standard `server/bin/migrate.php`. Ensure the database contains **no preexisting approved replacement**.
2. Configure distinct private `STORAGE_PATH` outside the host webroot and server release folders. Set `APP_ENV=test`, `FEATURE_REPLACEMENTS=1`, `FEATURE_ANALYTICS=0`, `FEATURE_OWNER_UPLOADS=1`, and `FEATURE_UPLOADS=0` only on this *isolated* environment. Use independently generated 40+ character `UPLOAD_OWNER_TOKEN`, `API_TEST_TOKEN` and audio signing key in a private `.env`. Never record tokens in CI logs, GitHub, the chat or screenshot.
3. Set `upload_max_filesize` strictly above 30 MiB and `post_max_size` above `upload_max_filesize` plus multipart overhead (e.g. 32M and 34M); set a bounded request timeout and restrict total request-body size at the ingress. Ensure the PHP temporary upload directory is private, writable and has adequate free space. Keep firewall/auth controls and rate limits in place. Test that the storage folder is unreachable via direct HTTP.
4. Build Chrome ZIP via `CELIKOM_API_BASE_URL=https://<isolated-host> npm --prefix extension run build`. Validate `manifest.host_permissions` contains only Yandex Music and the chosen isolated host, and `api/config.json` has exactly that origin. CI-generated default artifacts with an empty API URL are **not** owner acceptance builds. Never distribute an archive pointing at live Hostinger as an upload-ready package.
5. Verify read-only `GET /api/v1/health` and `GET /api/v1/config` in staging. An anonymous upload and a request with only `API_TEST_TOKEN` must be 401. A distinct upload owner token may write pending records, but no pending ID appears in /resolve or /audio. Keep logs free of authorization headers, query tokens and file names.

## Gate C: 10–15 minute owner acceptance (only after Gate A+B are green)

1. Open Yandex Music in private-test Chrome and start a known track. CELIKOM Add version must show current **exact Track ID as read-only**; the input must be blank/disabled if the track is ambiguous or no duration is available. Do not edit the Track ID manually.
2. Choose one owner-authorized MP3 at most 30 MiB and check rights declaration. Enter the separate owner upload token privately. Upload; observe percentage progress and `pending`, not `approved`.
3. Rename the same bytes, select that file, retry for the same Track ID. It must return a duplicate of the pending candidate, without adding another physical AudioAsset. If desired, test a second exact Track ID in the isolated fixture environment only.
4. Confirm that /resolve is still not found for the uploaded candidate and that the signed Range endpoint cannot serve it. Playback of any pre-existing approved audio must remain unaffected.
5. Test a fake `.mp3`, a wrong track/ambiguous state and a network interruption; check safe recovery and that a retry cannot publish content. Note popup lifetime: closing the Chrome popup can abort an in-flight request; reopen and re-select the file to retry with a new request ID. A partially received request must not become an active mapping.

## Post-acceptance safety

Immediately set `FEATURE_OWNER_UPLOADS=0` again in the isolated environment; archive only sanitized test observations and delete disposable credentials when testing ends. Stage 7 code can be considered owner-accepted only with owner confirmation and reproducible CI evidence. **Do not claim Stage 6.7 completed**; the intermittent JS `RangeError` in issue #7 and the two-profile browser gate are separate.

## Known limitations

- Fingerprint job statuses are persisted, but there is no actual Chromaprint/perceptual fingerprint computation yet. Exact SHA-256 dedupe works only for identical bytes; re-encoded audio may not be identified as the same song.
- Frame-duration inspection is not a complete audio security decoder. Native Chromium in CI checks a synthetic MP3, and Stage 8 owner moderation is still required for real content and rights.
- The owner-only gate is a temporary pre-Stage10 capability. It does not implement public uploads, user sessions, subscriptions, billing, an administrative approve UI, or offsite disaster recovery.
