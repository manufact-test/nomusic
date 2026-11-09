# VPN/network recovery hardening — extension 0.4.39

2026-10-14: owner confirmed OpenVPN Connect desktop client, sometimes enabled/disabled while Yandex plays. Product must support ordinary VPN usage and recover from route changes without repeated reload/reinstall. Split-tunnel exceptions are not a requirement for customers.

0.4.38 reduced early timeout failures but did not solve the later report: config/auth-me HTTP 504, network errors and 20-second timeouts. User eventually recovered automatically. Independent on-host and GitHub-runner probes at 11:25 UTC were fast (PHP/MySQL 1–2 ms, on-host HTTPS 13–42 ms, external runner 178–285 ms). These present-time probes do not prove which component produced the earlier owner's 504. Hosting shared load numbers alone are insufficient to diagnose overload without CPU/quota context. No actual VPN profile or traffic trace has been inspected.

Implemented in `458764a5bf75da5acb645182b44087cc3ab5886c`:
- Shared read-recovery helper: up to three GET attempts within one 20-second total deadline, with 500/1000 ms delay. Retry transport failures and gateway 502/503/504, including streamed-JSON route failures. Drain/cancel unusable gateway bodies. Never retry a transport POST; account denials remain immediate.
- Auth read coalescing retained. Connection reset cancels old GET attempts, releases pending entries and preserves stored session credentials.
- Catalog reset invalidates cached resolutions/configuration and fences pending resolution cleanup so an old promise cannot clear the new same-ID request.
- Worker online/offline events are hints to revalidate, not authority or proof that API is available. Reset transport/access checks and reverify an already-enabled client; never enable a stopped client from an online event.
- Access epoch + promise identity fencing: old connection success/failure/denial cannot overwrite fresh verification, suspend restored playback or clear a newer pending check. Logout/Stop/manual Original behavior is preserved.
- Retry path also works without an online/offline event, because VPN changes may leave the browser online flag unchanged.

Validation:
- 206 extension tests PASS locally and configured private CI: https://github.com/manufact-test/nomusic/actions/runs/38559780183
- Full PHP/MySQL/extension/browser regression PASS: https://github.com/manufact-test/nomusic/actions/runs/38559788504
- Native Chromium support flow, pinned Hostinger API packaging and secret/permission checks PASS.
- Deterministic tests include 504 then success, streamed response route failure, total deadline/count bounds, no POST replay, immediate denial, reset during pending read/write, stale response fencing, credential preservation, stopped-client behavior and recovery without connectivity events.

ZIP `CELIKOM-0.4.39-full.zip`: 2447123 bytes, SHA256 `6e9e2e3f34258bb637996dc2ffe6b03514a12edbe168b00f3fe4f11ce72f795a`.

No Hostinger deployment, schema change, account/grant/session reset or audio/catalog mutation for this client patch. Backend remains `0.4.37-b05ddfc858940c0c86979e3af2056f3cafa7dada`. Real OpenVPN switching validation on the owner's computer is still pending; automatic tests do not prove the historical gateway cause is removed. Sustained VPN/ISP/hosting outage still requires original-audio fallback until the API verifies access. No permanent offline entitlement or alternative endpoint bypass was introduced.

Owner checks: install in same unpacked directory, reload extension and Yandex tab once. Verify normal playback with VPN connected; while playing, disconnect and reconnect VPN once, allow route to settle and confirm automatic return without Start/reload/reinstall. If it fails, copy diagnostics after reconnect with VPN stable. PR #6 remains open/unmerged; Issue #7 remains open.
