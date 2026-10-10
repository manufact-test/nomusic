# Stage10 — 0.4.9 stream reliability; owner playback still required

Date: 2026-10-10. Branch: feature/api-range. Stage10 / Issue9 OPEN.

## Evidence from the owner and working archive

Owner 0.4.8 diagnostics: exact Track ID 144530503, bridge healthy, three activations/restores; terminal remote-stream-http after REPLACEMENT_ACTIVE. HTTP status was not recorded, so the owner's exact failing response remains unknown.

Owner supplied `CELIKOM-0.4.1-API-Diagnostics(1).zip`; its actual manifest is **0.4.4**. SHA256: `ad681910bf501d926bae549429c21521ab0eb8f4add665d82d1f4ad66a00b86c`. Original uploaded ZIP and installed 0.4.4 are untouched. Byte comparison with delivered 0.4.8: replacement-player.js, replacement-controller.js, sync-engine.js and original-audio-guard.js are IDENTICAL. Broker/client differ because Stage10 substitutes verified account authorization for legacy API_TEST_TOKEN. Do not revert to the test token or remove account access checks.

Expanded pre-fix on-host HTTP test [38071162980](https://github.com/manufact-test/nomusic/actions/runs/38071162980) downloaded all nine signed 512KiB ranges successfully, then a pending-track Resolve returned **503 service_unavailable**. This proves a transient server failure under the test load, not the exact status of the owner's failed range. The earlier four-byte smoke did not exercise a complete file. Complete-range evidence alone does not prove real Yandex playback.

## Narrow correction

Core commit: `649c7bfd51d3ca594f09cd5d76953a6cab8f2d6a`.

- Backend reuses one lazy PDO connection within the Application/request. Catalog and session/entitlement checks previously opened two connections per signed audio request. Every Range still checks signed URL, active catalog mapping, independent live session and current entitlement; no cached authorization or public media access introduced.
- Backend 503 logging records sanitized PDO SQLSTATE/driver codes only; no SQL, credentials, URLs or paths.
- MP3 pump retries only temporary 429/502/503/504 HTTP responses, at 500ms and 1000ms, maximum three attempts for the SAME chunk and signed URL. Error body discarded. 403/200/other failures immediately fail open. Destroy cancels pending retries. Existing MSE/bounded512KiB validation and synchronization retained.
- On exhaustion, safe diagnostics include HTTP status, chunk offset and attempt count in playback.lastRestore.detail. No signed URL/token/error body enters diagnostics.
- Trial stays 3 days; accounts/passwords/sessions and earlier one-time reset retained. No additional trial reset.

Local CI passes: 122 extension tests and 17 PoC tests. New regressions cover transient 503 recovery without losing buffered audio, persistent 503 exhaustion, immediate 403/200 failure, destroy during retry. Full PHP8.3/MySQL8 [CI38071519212](https://github.com/manufact-test/nomusic/actions/runs/38071519212) PASS, including native Chromium audio and existing backend integration/security tests.

Private Chrome build [38071516201](https://github.com/manufact-test/nomusic/actions/runs/38071516201) PASS. ZIP `CELIKOM-0.4.9-stage10.zip`, SHA256 `1a108e4be054cbb853448b976add158dc3d3fad466de81e7c1734343a896814d`; exact Hostinger origin, manifest0.4.9, no credentials. Saved deliverable available.

## Rollout gates

Pre-deploy private snapshot [38071516204](https://github.com/manufact-test/nomusic/actions/runs/38071516204) PASS: 24 tables + 5 audio objects. Pre-deploy isolated restore [38071662946](https://github.com/manufact-test/nomusic/actions/runs/38071662946) PASS: private configuration/audio and actual MySQL schema restored in disposable scratch; live data untouched. Guarded deployment [38071753196](https://github.com/manufact-test/nomusic/actions/runs/38071753196) PASS; active release `0.4.9-bdd6a70568458d7ef85f1f531ed10bcd9b468579`, historic credentials retained. Post-deploy preservation audit [38071914225](https://github.com/manufact-test/nomusic/actions/runs/38071914225) PASS: unchanged env/media/historic row counts and migrations. Expanded real HTTPS smoke [38071914275](https://github.com/manufact-test/nomusic/actions/runs/38071914275) PASS: all nine 512KiB signed MP3 ranges, normal user-bearer resolve, exact three-day trial, two independent sessions, refresh/logout revokes only one device, anonymous/before-trial/pending denied. This run completed without HTTP retries in the smoke. Post-release snapshot [38072070059](https://github.com/manufact-test/nomusic/actions/runs/38072070059) PASS: 24 tables + 5 audio objects. Final post-release isolated recovery in progress.

## Owner gate

Update the SAME current unpacked extension in place to 0.4.9 and reload the Yandex tab. Existing account; no second profile or registration required for the first retest. Test actual approved144530503 audio, Pause/Play/Seek/Next/Return/Stop. If failure persists, capture Diagnostics immediately; status and offset will now be present for HTTP failures. Do not claim successful music substitution without owner confirmation.

PR6 remains OPEN/unmerged; Issue7 OPEN without proven RangeError fix; Issue9 OPEN. Approved144530503/#1 and pending799133075/#2,38436680/#3 unchanged; uploads/suggestions remain disabled until unified playback/security owner gate. Original0.4.4 retained.
