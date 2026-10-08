# CELIKOM-STAGE4-API — 0.4.0

Authority: master TZ v1.3 and work plan v1.4, Stage 4. This document records implementation acceptance boundaries, not new product requirements.

| Check | Automated evidence |
| --- | --- |
| health/config, feature defaults, malformed route/body/auth | PHP response contracts |
| exact track ID, only approved active mapping, shared asset, dedup/idempotence | real MySQL migrations + importer/repository tests |
| signature valid/forged/expired/changed version; missing/disabled asset | PHP fail-open contracts |
| full/HEAD, first/middle/suffix/open-end, malformed/multiple/unsatisfiable range, If-Range | PHP contracts plus real HTTP byte comparisons |
| file decoding + metadata, seek to 0.5 s, play/pause | native headless Chromium with actual signed WAV over PHP HTTP |
| API positive/negative cache, coalescing, bounds, minimum version, malicious URL | compiled ApiClient tests |
| network unavailable, wrong duration, expiry, stale load and original guard ordering | compiled playback engine + existing two-world fixtures |
| analytics disabled, repeated UUID retries, financial/history rejection, partial batch | client/PHP + real SQL dedup/aggregates/retention |
| package isolation and fixed origin permissions | allowlist build + manifest validation |

Local PHP 8.3 unit tests and compiled extension checks run in the workspace. CI must run MySQL, real PHP HTTP and Chromium; tests fail in CI if DB/browser runtime is missing. Local environments without these runtimes explicitly defer integration checks. The synthetic 1-second WAV is generated at test time, never committed as user music. The old embedded test signal remains developer-only.

Headless Chromium allows autoplay for the decoder check. That proves native decode/seek of the actual endpoint, not normal autoplay permission. The fixture origin is explicitly enabled only in APP_ENV=test; production CORS permits only Yandex. Real MP3 codec/seek, HTTPS, server limits, Yandex CSP and normal gestures require Stage 5 on the chosen hosting domain.

Live runbook: `docs/deployment/hostinger-private-test.md`. Stop the gate if drift oscillates, binding-change retries loop or original recovery fails. Keep sanitized diagnostics, use reviewed files with measured durations, and include a 2–3 minute same-track session after seek. No billing/admin/Android completion is inferred from these API tests.
