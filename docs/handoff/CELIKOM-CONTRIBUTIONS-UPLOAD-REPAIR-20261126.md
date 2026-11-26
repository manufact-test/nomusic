# Upload and song proposal repair — 26 November 2026

## Report and confirmed cause

Owner could not upload MP3 to track 127629881 in Extension 0.4.91, with or without VPN. Screenshot attempt prefix: 3EC3C4AB. This is an attempt identifier, not an error category.

Sanitized read-only server audit found two matching HTTP 503 responses (298 ms and 224 ms) and application service_unavailable errors. API upload limits were correctly configured: Nginx 32m, FastCGI upload_max_filesize 30M / post_max_size 32M. File size or VPN was not the identified cause.

Deployed runtime at /srv/celikom/app/staging-20261122/tools:
- mp3-validator was mode 0640, uid 1000 / gid 33: www-data could read but could not execute it.
- decode-slot-0.lock was mode 0640: www-data could not open it for writing.
- decode-slot-1.lock was missing; tools directory was deliberately not writable by www-data.

This migrated runtime state prevents normal MP3 admission before storage/moderation. Do not rewrite the extension or bypass MP3 validation to address it.

## Bounded live repair

Administrative run 45885648380, SUCCESS:
- Verified existing binary SHA-256 d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939.
- Set only tools/mp3-validator to 0750.
- Set tools/decode-slot-0.lock to 0660.
- Created empty tools/decode-slot-1.lock as uid 1000 / gid 33, mode 0660.
- Binary bytes unchanged; no PHP source deployment, PHP restart, broad chmod, auth/entitlement/feature changes, or existing catalog changes.
- Ran deployed MP3 normalization and decoder as www-data against an existing approved MP3, reading that audio without changing it. PASS. Repair included rollback on failure.

Exact guarded repair is retained at .github/scripts/floki-upload-runtime-permission-repair-20261126.sh. Do not apply generic 0640 file normalization to executable tools or writable decoder lock files during future transfers/deployments.

## Verified contribution flow

Owner also requested verification of separate song proposals and their relationship with uploads.

42 relevant extension tests passed: popup upload integration, background broker, offscreen worker, upload contract and journal. No extension playback/diagnostic source changes.

Administrative run 45886142531, job 140137203510: SUCCESS. Real HTTPS PHP multipart/API checks used an isolated temporary synthetic ordinary account, its real user bearer session and normal activation path; email delivery/signup verification was not under test. Temporary track ID and generated pure-tone MP3 were reserved for this check.

Observed PASS:
1. Extension-origin CORS preflight; unauthenticated writes rejected.
2. Empty track moderation presence.
3. Separate song proposal accepted HTTP 202 / pending, repeated proposal returns the same request, one pending queue row.
4. MP3 upload of exactly 7,523,280 bytes accepted HTTP 202 / pending; repeat returns same replacement with duplicate=true.
5. Queue row is pending/inactive and belongs to the test account.
6. Status endpoint reports pending; another proposal for the now-uploaded song is rejected with HTTP 409 / track_pending.
7. Existing derived admin proposal progress changes to uploaded for the matching song.
8. Pending audio is not returned for playback and is not streamable.
9. Only this probe's synthetic records/account/media were cleaned up. Existing user songs, sessions, trials and moderation were preserved.

The previously reported VPN playback interruption and expanded playback diagnostics remain explicitly deferred, unchanged. Extension stays 0.4.91: owner can retry the same file without reinstalling. Actual owner's resubmission remains to be confirmed.
