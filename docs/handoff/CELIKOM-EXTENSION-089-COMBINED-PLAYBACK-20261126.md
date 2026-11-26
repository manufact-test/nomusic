# Extension 0.4.89 — combined listening fixes, 26 November 2026

Owner explicitly rejected the narrow88 delivery and asked for ALL accumulated listening issues to be handled together. Do not ask the owner to install88 or deliver another one-fix build.89 is being checked as one combined candidate; no acceptance/public promotion.

## Changes under verification
- E1: prewarm public server policy at explicit Start and authorized playback heartbeats; refresh within15s of the existing60s policy deadline. No descriptor/audio warms without existing entitled access. Failed warmups do not renew policy or hammer the endpoint;5000ms cooldown. Actual resolve still uses withAccess and current server policy; maintenance/denial wins. This removes a cold config round trip from subsequent switches rather than increasing intro mute bounds.
- E4: cold native M4A/WAV/approved-complete-MP3 uses one bounded full-file signed Range (maximum30MiB) instead of512KiB plus a second round trip. Existing possible cache reuse requires a new1KiB signed Range with exact strong content/version ETag. Bodies/headers/cancellation remain bounded, sequential, byte-preserving; no transcoding/remux/parallel bursts/server changes. Server AudioController read-only code confirms no512KiB Range ceiling.
- Pause: fully downloaded, strongly identified paused audio can refresh its expiring descriptor and verify a fresh signed1KiB Range against the SAME content/version/gain before updating its grant. Keeps decoder, position and gain graph, with no guard reacquisition or cold reload. Starts within90s of expiry, including after a throttled background timer, ONLY while paused/eligible. Expired audio cannot play pending verification. Denial/removal/content change/Stop/new track fail open or invalidate old work. Unknown/incomplete/weak-ETag resources keep the old expiry fallback. Paid entitlement, token validation and heartbeat rules are unchanged.
- Pause race: rapid pause/resume superseding pending play/AudioContext resume fulfils the latest play intent immediately; does not wait for a500ms/background snapshot. Stop/late old rejection/current autoplay denial remain fenced.
- E2: when the ordinary track began at<=250ms and loading caused a late intro join, move the existing decoder seek before original mute and verify position/readiness against a fresh snapshot. No new source/pump/rate mechanism, no MediaSource live-join, no changes to the complete-file admin-approval route. Explicit user seeks and mid-song starts keep their existing path. Cancellation/new track cannot acquire a late guard.
- E3: retained diagnostics showed natural boundaries, not proven mid-song dropouts. Keep existing ending cancellation and six-natural-track regression coverage; no speculative tail mute.
- E5: carry88 persistent UI/native-duration mismatch detection, invalid visible-target protection and explicit revalidated Yandex page reload. Historical evidence does NOT prove why Yandex metadata and original stream diverged. Do not claim the underlying divergence is permanently fixed. No automatic reload or guessed track/source writes.
- Split audio preparation timings and signed revalidation count/readiness in private diagnostics, so later slow loads can be separated into native download/source readiness/gain/alignment.

Preserve final78 features and85/86/87 fixes. No Android/Windows/product architecture/backend/prod/infra/paid-feature changes. Only extension source/tests, its existing native synthetic browser test and this checkpoint.

## Verification and private owner delivery — 26 November 2026
Source commit: `a1c19b812ef5ebdfd19500d3721b2b29750deca7`.
Extension build run: `45832979883` (Floki runner, conclusion SUCCESS).
- `npm run test:extension`: 431 passed, 0 failed.
- `npm run build:extension`: produced `celikom-extension-0.4.89.zip`.
- `npm --prefix extension run validate`: production manifest 0.4.89 validated.
- `npm run security`: PASS, 67 client files, bounded permissions, no source maps/private key patterns.
- ZIP checksum verification: PASS.
- Private spool test suite: 4 passed, 0 failed.

Private Floki owner-delivery run: `45833819502` (conclusion SUCCESS).
- Independently re-read and verified the private spool receipt, package size, SHA-256, checksum sidecar, ZIP CRC, unique/safe archive paths, manifest version, API origin and exact host permissions.
- Immutable copies verified at `/srv/celikom-releases/private/extension/` and `/srv/celikom-releases/owner-downloads/`.
- Existing owner-download route added without disabling Basic Auth. Unauthenticated requests to both the new route and the prior 0.4.73 route returned HTTP 401 with Basic challenge.
- Owner URL: `https://celikom.com/downloads/extension/celikom-extension-0.4.89.zip`.
- Size: `2,499,254` bytes.
- SHA-256: `88db3f3ab927b8123676733a242d84fabe683ca79eb4cb17cac2703f1f1c4b0a`.

This is a PRIVATE OWNER CANDIDATE, not public/customer promotion or owner acceptance. CI is Node-based regression/build/security validation; it is NOT real Yandex listening acceptance. The local Chromium launcher exists but its engine binary is absent. Do not claim real Chrome/Brave/Yandex playback acceptance or that the underlying E5 native/UI divergence has been root-caused. Owner must install and listen to this one combined candidate.

## Release boundary
No website/customer promotion or accepted baseline replacement. Do not call all bugs eliminated. Real Yandex/VPN listening and E5 root cause remain acceptance limits.
