# W72 — CELIKOM Windows 0.24.20: hidden support diagnostics + stable reconnect, 2026-11-11

## Owner instruction and confirmed source incident
The owner explicitly requested: inspect **browser extension** (NOT Android), reuse its established anti-drop and recovery protections where compatible with Windows, and deliver **one** Windows installer containing both hidden automatic support diagnostics and fixes for repeated disconnects.

Owner's actual Windows 0.24.17 file `Вставленный текст(20261111-090013).txt` shows on 2026-11-11:
- `08:59:21.563Z STOP_DISABLED`
- `08:59:21.565Z ACTIVE_ENTITLEMENT_CHECK_UNAVAILABLE`
- `08:59:21.876Z STATE_DISABLED`
- `08:59:39.617Z START_ENABLED` after owner manually reconnected.

Thus one confirmed disconnect was triggered by **Windows entitlement-check failure disabling the bridge**, not a proven Yandex decoder issue. The exact original upstream failure reason (HTTP/timeout/VPN) is not exported by W69. Do NOT claim other two disconnects have been individually proven to have the same cause.

## Extension anti-drop mechanisms actually reviewed
- `extension/src/shared/read-recovery.ts`: bounded retry of GET reads only, deadlines, cancel obsolete network generations and ignore late results, never replay writes.
- `extension/src/background/service-worker.ts`: explicit user intent generation, single in-flight entitlement, 5s reconnection recheck, discarded transport after VPN route change, online/visibility signals merely trigger a fresh authoritative check, never authorize offline audio.
- `extension/src/auth/auth-broker.ts` and `extension/tests/refresh-race.test.mjs`: token refresh is single-flight, generation-matched, and cannot overwrite a logout or a newer session.
- `extension/src/background/tab-recovery.ts` + `controller-bootstrap.ts`: narrow 500/1500/4000ms retries for Chrome injection, cancellation when a tab navigates/closes/Stop, no unbounded workers.
- `extension/src/player/player-bridge.ts`: two confirmed failed liveness checks before bridge timeout and token-bound fail-open.
- `extension/src/player/replacement-controller.ts`, `fail-open-controller.ts`: track-specific error/backoff/release guards and restoration of original audio.
- Browser MAIN/ISOLATED content scripts and their original-audio guard are **not transferable** to the native Windows host. Windows sends state heartbeats only on transitions, not every tick, so copying Chrome's heartbeat watchdog would falsely label a playing track disconnected. Native audio implementation, Yandex files and old working pause/seek were deliberately not rewritten.

## Changes shipped together in W72
W70/W71 foundations retained:
- Every general/support or song complaint sends a **hidden token-free bounded diagnostic snapshot** with platform/version, integration status and important recent event codes to the already-updated live admin. No diagnostic interface shown to ordinary users. Owner/moderator-only JSON download.
- When the periodic 15s entitlement GET briefly fails, Windows retries the idempotent GET once; if still unavailable, it fails closed and schedules a recheck. **Only a new successfully authenticated `PlaybackEntitlement.Allowed` answer can resume playback**, never a cached access decision, VPN online signal, or manually forbidden status. 401/403 and authoritative subscription/trial denial never auto-resume. Manual Stop, new Start, login/logout/closing override pending recovery; account/generation checks discard stale late results.
- Local event diagnostics suppress repetitive native polling and prioritize significant errors. Full owner TXT remains staff-only and unchanged.

Extension-derived W72 additional guards:
1. **Login/logout/refresh race fixed in `CelikomApi`**: a lock and exact session-reference verification prevent an in-flight old refresh (even a successful server reply) from resurrecting a user after Logout, or overwriting a newer login. The existing refresh lock remains for refresh-token rotation. A real asynchronous 401 → delayed refresh → Logout → stale refresh-success test verifies Windows DPAPI login stays cleared.
2. **Fresh GET route after VPN changes**: Windows entitlement GET uses `Connection: close` and no-store/no-cache to avoid keeping a stale pooled route across adapter/VPN changes. Never uses this behavior for streaming/audio Range or POST support messages.
3. **Temporary gateway failure classes**: invalid JSON/HTML response and redirect from captive-portal/proxy are treated as *transient failure to check*, never as permission. 401/403 genuine JSON access denial is terminal. Only GET checks are retried; no upload, promo redemption, support POST or other write replay.
4. **Connectivity hints**: Windows network-address-change event immediately requests a new check **only while previously suspended**, coalesced within 3s. It never turns replacement on by itself. Recovery poll runs every **5s only while suspended**; normal playback stays at **15s**. Native audio/track queue untouched.
5. **Clear safe failure diagnostics**: discrete allowlisted `ACTIVE_ENTITLEMENT_TIMEOUT`, `_NETWORK_ERROR`, `_RATE_LIMITED`, `_SERVER_ERROR`, `_BAD_RESPONSE`, `_ROUTE_REDIRECT`, `_DENIED_401`, `_DENIED_403` codes; no raw URLs, tokens, email, paths or exception text.
6. **True 15-minute support incident window**: previous W71 support summary inadvertently parsed `ExportText`'s final 1600 lines, which high-frequency `NATIVE_STATE_RECEIVED` could fill in a few minutes. W72 scans only locally stored allowlisted, timestamp-verified recent log entries from both rotations and retains 24 incident + 40 contextual events (up to 64), keeping a 13-minute-old failure even after 2,500 subsequent benign status lines. The user-triggered support snapshot is still small and privacy-redacted.

## Verified independent gates
1. Exact Windows 0.24.20 source **`66ffb6348f821416adabb9de4ce110adef1d5b7b`**, pinned backup `backup/windows-w72-02420-extension-anti-drop-and-support-ci-green-20261111`. Working branch `experiment/windows-w72-extension-anti-drop-guards-20261111`.
2. Windows native/.NET contract, WinForms interactions, original Yandex untouched, install/uninstall and disposable MySQL support redaction/RBAC/dedupe CI: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42998876460. Native contract **138 checks**; W72 regression tests include 401 delayed refresh after Logout, fresh/no-cache GET, invalid JSON/redirect handling, 5s/15s interval and 13-minute incident preserved after 2500 poll entries.
3. Actual independent Windows W69 0.24.17 → W72 0.24.20 in-place upgrade: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42999441879. Same-user DPAPI encrypted saved login preserved and decryptable, one AppId/uninstaller, 0.24.20 native, untouched Yandex, uninstall preserves saved login by default.
4. Exact **private unsigned** install EXE (not a public signed release): `CELIKOM-W72-SUPPORT-ANTI-DROP-GUARDS-UNSIGNED.exe`, size **43,542,513** bytes, SHA256 `1cc9321d8aeb1482a8c23aad8cc1285bb1896f81402ea60c6692b483c180ccd9`; GitHub CI artifact **13845601337**. Saved byte-for-byte identical in Library at `/CELIKOM/Windows/CELIKOM-W72-SUPPORT-ANTI-DROP-GUARDS-UNSIGNED.exe` (ID `libfile_01af2848721481918220f25bdf06d1d5`) AND familiar `/CELIKOM/Windows/CELIKOM-Windows-Setup.exe` (stable ID `libfile_9cef6593f5e88191a339835933fbc550`), both roundtrip SHA verified. Direct ChatGPT session copy `/mnt/data/CELIKOM-Windows-Setup-0.24.20.exe` verified.
5. W69 0.24.17 owner-accepted backup `backup/windows-w69-02417-uninstall-login-choice-ci-pass-20261110` and its version-specific EXE remain untouched. W71 compiled checkpoint backup `backup/windows-w71-02419-support-and-network-recovery-ci-green-20261111` also exists.

## Live backend and owner acceptance / remaining risks
Browser-extension developer already deployed the current shared server support/admin contract to Hostinger; active release `browser-support-076-b807cd691074` was validated by https://github.com/manufact-test/nomusic/actions/runs/42989025119 and https://github.com/manufact-test/nomusic/actions/runs/42990954657. **W72 does NOT deploy or overwrite shared PHP**; never use its inherited W70 PHP snapshots to roll back the newer browser admin. Live native audio/health/auth read-only probe https://github.com/manufact-test/nomusic/actions/runs/42991785939 succeeded.

Owner should install a **single** W72 0.24.20 EXE over existing 0.24.17 (do not uninstall), confirm preserved sign-in and native module, run 20–30 minutes of ordinary music/MyWave, test pause/seek/Next/Start/Stop, optionally change VPN once, and send one general support ticket + one song complaint to verify hidden diagnosis in current admin. Another interruption must be investigated through the automatically attached event codes. No additional files should be required for support.

**NOT YET VERIFIED ON OWNER'S REAL PC:** successful reconnect after owner-style 3 drops. Automated tests and CI prove contract and upgrade behavior only, not full live environmental reproduction. Source/stream-specific audio failures (HTTP signed Range, player fast pause, queue and decoder) remain separate and must not be claimed cured by entitlement recovery. Public signing and paid checkout integration remain deferred.

## Post-install owner feedback 2026-11-11 — OPEN (W73)

Owner installed Windows 0.24.20 and confirmed song-complaint diagnostic delivery, but reports the **expected email is absent for an ordinary general-support message**. This does **NOT** invalidate the compiled W72 recovery and install CI, but it means the owner has **not** accepted general support's end-to-end email path. The live mail delivery was not verified by W72 CI. `Сообщение отправлено` means the support API accepted the ticket, not that SMTP was delivered.

**Do not silently fix from this obsolete snapshot or redeploy W72 PHP.** See the latest requirement and source comparison in `docs/windows/W73-TZ-WINDOWS-GENERAL-SUPPORT-EMAIL-AND-DIAGNOSTICS-PARITY-20261111.md`. Next developer must distinguish incoming general support notification to the staff mailbox from an admin reply delivered to the customer. The browser extension deliberately does not auto-email a customer upon submitting a ticket. Actual live `delivery` status, SMTP, and customer/admin email paths must be checked before changing anything. W72 compiled source `66ffb6348f821416adabb9de4ce110adef1d5b7b` and backup stay unchanged.
