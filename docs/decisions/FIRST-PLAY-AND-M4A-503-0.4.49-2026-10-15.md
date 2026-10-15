# 0.4.49: remaining first-play leak and observed M4A HTTP 503

Owner reports .48 improved but not fully accepted: foreign fragment roughly one switch in six, and M4A cold start can go silent and take many seconds to recover. Uploaded screenshot shows original/reconnecting; two attached diagnostics and screenshot inspected locally. No private audio exported or changed.

## Direct evidence

First report is a NEW content controller, active generation 1, activationCount 1/restoreCount 0. Before native play 1944611 has independent duration and confidence 260, but no original lease/handoff or replacement. Native time 100–460 ms is unguarded; replacement becomes active after 366 ms. .48 protected transfers from previous guarded playback, not first playback after reload or a transition from unguarded original.

Second report: 1944599 (Папиросы), replacement 27, native M4A. Two prepares fail with remote-stream-http, last HTTP 503 after 5,767,168 bytes with offset 7,340,032; outer backoff waits 5 then 10 seconds and restarts the file. Third prepare succeeds at native time ~18.5 seconds. .48 four-reader request burst is a plausible contributor to hosting limits; HTTP 503 is proven, exact server reason is not. First reserve silences native for ~1 second before first failure, then original is restored. Another MP3 transition shows old handoff expires ~127 ms into new native play because metadata preceded readiness by ~938 ms.

## Changes

- Add synchronous first-play admission in MAIN, before native play executes, only when the installed controller says enabled/not suspended, session/heartbeat current, exact non-ambiguous track confidence >=100, eligible original trigger element, independently matching duration, ready state >=2. Never act on replacement/utility/other media or unknown track. Preserve logical volume/mute and Yandex clock.
- Admission only holds original for up to 1 second while resolving. A valid authenticated positive resolve can reserve it for the existing bounded prepare deadline; full ready/duration/token checks still required before replacement playback. Negative/missing/denied result, Stop/Original, suspension and teardown restore original. Negative TTL and one-attempt resource identity prevent repeated mute on pause/resume; explicit Start can rearm. Revisioned policy prevents delayed settings messages undoing Stop.
- If metadata consumed most of an old transfer deadline, a fresh native play can renew that transfer once for one lookup window, capped at two seconds total before a positive reserve. Polls do not renew it.
- M4A keeps original bytes/container. First signed 512 KiB verifies access/strong ETag and allows authorized in-memory cache reuse. Cold download then makes ONE sequential continuation for the exact validated remainder, not many parallel small requests. Total, every body read, MIME, size, ETag and byte order remain bounded/validated (30 MiB max).
- Retry only a transient 429/502/503/504 on the SAME failed range, at most twice with 500/1000 ms bounded abortable waits; already verified first bytes are retained. Revoked/expired 401/403 never retry or reuse cache. Existing final fail-open/backoff remains if all bounded attempts fail.

First ever uncached M4A still requires its bytes and decoding. Zero cold-start silence cannot be promised with Blob playback; this reduces requests and avoids the observed restart/backoff path. Do not claim owner audible symptom fully eliminated from synthetic tests.

## Verification

262 extension tests PASS locally, including first play without previous replacement, immediate negative restore, no repeated mute, Stop, deadline fallback, exact byte continuation, transient 503 recovery and bounded/no-revocation retry. Lint/validate/security PASS. Native Chrome and full CI results recorded in handoff before delivery. Native test now injects actual M4A first-range 503, checks native decode/play/seek and physical original mute synchronously before first play plus slow metadata-first transition extending past the previous deadline.

Extension-only .49. Backend unchanged .46; no audio, mapping, moderation, gain or account changes. Preserve owner M4A 1944599/replacement 27, PR #6 OPEN/unmerged and issue #7 OPEN. Owner validation pending.
