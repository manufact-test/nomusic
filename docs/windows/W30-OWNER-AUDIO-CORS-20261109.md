# W30 — Windows owner audio failure 0.24.2; isolated audio CORS defect (2026-11-09)

## Evidence from owner TXT
- 0.24.2, NativeIntegration=ACTIVE, signed in, enabled.
- Two ordinary songs had RESOLVE_MISS and returned SOURCE_ORIGINAL: user confirms original audio plays.
- Approved song tracks 42498653, 107389859, 105929447 etc had RESOLVE_APPROVED, GRANT_DELIVERED, NATIVE_FILEINFO_OK, FILEINFO_SHAPE_DOWNLOAD and SOURCE_MAPPED. Owner confirms playback immediately pauses.
- RESOURCE TIMING: MEDIA_REQUEST_SEEN followed only by MEDIA_HTTP_UNVERIFIED, NOT success. No observed MEDIA_PLAY/PAUSE/ERROR (likely WebAudio). Not a claim that audio loads, or that CORS is uniquely proven.
- W29 eliminated previous SOURCE_SYNTHETIC_RESPONSE but audible issue persists.
- Confirmed SERVER CODE mismatch: server/config/app.php allows https://music.yandex.ru only for CORS; ordinary Yandex Windows app uses musicapplication://desktop (opaque Origin: null) or desktop.app.music.yandex.net and wants external signed audio URL. AudioController token validation, Range and stream exist, but Application.php currently omits ACAO for native origin and denies native OPTIONS, so native WebAudio Fetch may fail due CORS. This is a concrete contract defect; actual network error in owner client remains unobserved.

## Scoped server-only correction
- server/src/Application.php: Access-Control-Allow-Origin only for GET/HEAD/OPTIONS /api/v1/audio/[numeric-id] with explicit Yandex native/desktop origin or null. Protect all other /api/v1/auth, /api/v1/resolve, account and admin endpoints from expanded origins. No credentials grants. Signed URL must still pass AudioController HMAC, session and entitlement check on every GET/Range.
- server/tests/smoke.php adds real signed audio GET, HEAD, 206 Range, OPTIONS preflight, hostile origin and unrelated auth-route regressions.
- CI workflow windows-w30-audio-cors.yml: PHP 8.3 narrow stage-only tests, NO production deploy.
- No new Windows installer required for this *server* fix if deployed; current installed 0.24.2 maps valid source URL.
- Backup: backup/windows-w30-before-owner-audio-cors-diagnosis-20261109 at 4137b247187e88313642d4a025eddf9d7719e717.
- Do not deploy unreviewed broad legacy Hostinger server zip: broad deploy workflow contains database migration/snapshot/owner operations. Validate live server version and independently verify exact file before a one-file hotfix. Verify signed audio from desktop (HTTP 200/206 + CORS) before claiming audio fixed.

## Live private Hostinger activation — 2026-11-09

**Guarded GitHub Actions live run https://github.com/manufact-test/nomusic/actions/runs/42646675471: SUCCESS.**
- Preflight on active site confirmed browser audio OPTIONS Origin https://music.yandex.ru => 204/ACAO, but native opaque Origin null and musicapplication://desktop => 404/no ACAO. Real CORS defect, though not proof that this is the ONLY native audio fault.
- W30 PHP 8.3 stream/range/preflight/security tests green: https://github.com/manufact-test/nomusic/actions/runs/42643440610.
- First live attempt https://github.com/manufact-test/nomusic/actions/runs/42645545587 failed HTTP proof and AUTO-ROLLED BACK due to stale LiteSpeed compiled PHP after symlink switch.
- Second run #42646675471 checked exact original live Application.php SHA256, cloned immutable release to a new version, changed ONLY that PHP file, preserved original file and previous release path in independent backup, verified candidate behavior and syntax. After atomic symlink switch, one-time random POST-only PHP cache invalidation was run and immediately deleted.
- LIVE HTTPS: audio OPTIONS Origin null => 204/Access-Control-Allow-Origin null. Browser origin => 204/unchanged ACAO. Health => 200. Opaque origin to account auth route => no ACAO. Success markers W30_LIVE_AUDIO_CORS_204_PASS, W30_LIVE_BROWSER_CORS_PASS, W30_LIVE_HEALTH_PASS, W30_ORIGINAL_RELEASE_PRESERVED.
- Active release identifier w30-audio-cors-603564c68082 (under private Hostinger releases). Rollback backup backups/w30-audio-cors-603564c68082 and previous-release. No MySQL migrations, account data, production audio, Windows binaries or extension altered. Existing Windows CELIKOM 0.24.2 remains compatible; no installer needed.
- Real signed-range audio success and audible playback inside owner Yandex account are NOT yet verified. Ask owner to Stop/Start CELIKOM and restart Yandex if necessary; compare approved vs ordinary tracks, Play/Pause/Seek/Next, attach new diagnostic if it fails.
- Future full deployment from feature/api-range must include this scoped CORS correction, otherwise hotfix will revert. Canonical sync remains required before broad Hostinger rollout.
