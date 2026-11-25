# CELIKOM extension 0.4.80 — owner timing/CORS report, 2026-11-25

## Owner candidate
- Source main commit: **6c1b3491f790e4160464f75af722d64bf8521bc5**.
- Download: https://celikom.com/downloads/extension/celikom-extension-0.4.80.zip .
- Size: **2,490,430 bytes**; SHA-256 **e7304c49db0fdc2c11e5eeb4f1428bda796ddf44aca2729fa2d01520cf1481c0**.
- Existing Basic protection retained. 0.4.73 and 0.4.79 ZIP/routes preserved. No public automatic release.
- Owner confirmed 0.4.79 installs/opens and plays alternatives, but reports original fragments before replacement on track changes. 0.4.80 actual Yandex/VPN acceptance remains pending.

## Evidence and targeted correction
Owner diagnostic identifies installed bridge/controller0.4.79. Seven recent activations prepared in554–1221ms; native clock was already241–901ms into the track at activation. Recorded API calls all200; steady replacement active with7ms drift and no connection error. Trace includes intro-start-ready:intro-start-timeout: the400ms native intro fence releases before ordinary authenticated lookup plus audio loading finishes. This timing issue is independent of the separate CORS error; do not call the screenshot proof of ongoing outages or assume VPN caused this sample.

Changes:
1. Permit existing verified paused metadata warmup while the prior guard is transitioning. This starts lookup/decoding at native readyState1. Ambiguity, duration, session, track/media checks remain; guard engagement/activation still requires readyState>=2.
2. Retain one bounded1500ms intro hold while the native clock remains paused. Cancel the older transition timer when this hold owns the deadline; snapshots do not renew it. Prepared replacement resumes the native player exactly once under its guard. Unknown/unavailable tracks and failures restore the original; pause/load/source changes cancel stale native starts. No native-source experiment, new playback architecture, MSE live-join, gain, seek or approval-join redesign.
3. Live preflight baseline45650898370: valid chrome-extension origin OPTIONS auth/me405 without CORS; Yandex origin204 and arbitrary web origin405. Add a scoped extension-origin transport predicate to Application.php for GET/HEAD/POST/OPTIONS under /api/v1/ only, exact chrome-extension://[a-p]{32}. No wildcard, cookies or credentials grant. Bearer/session, paid/trial access and signed audio checks remain mandatory. Existing native Windows origin exceptions unchanged and still audio-only.
4. Official Chrome guidance notes extension-origin host permissions normally permit cross-origin access; the installed screenshot can reflect withheld/stale permissions or a prior request. The missing server preflight support is independently reproduced and repaired, not proof that every Chrome install depended on it. See https://developer.chrome.com/docs/extensions/develop/concepts/network-requests .

## Checks
- **368/368 extension tests**, including delayed450/1200ms positive intro verdicts, real MAIN/ISOLATED bridge/controller integration, a fixed deadline under repeated snapshots, preparation reservation, cancellation and no stale replay.
- Full CI45651328437 SUCCESS: dedicated PHP CORS origin/method/route boundary tests plus existing auth/access/security and native Chromium signed Range decode/seek checks.
- Extension artifact45651329460 SUCCESS:368 tests,4 private-spool tests, manifest/security, exact origin/permissions; byte-identical local and Floki ZIP with the digest above.
- Protected live rollout45652652451 SUCCESS: five extension preflights204/exact origin, unauthenticated auth/me and entitlement401, untrusted web/null/malformed extension auth origins denied, native audio CORS unchanged, health/config200, app hash checked. Immutable private/owner ZIP copies, nginx syntax/reload, old/new Basic gates verified.
- Independent external probes after rollout: health/config200; auth/me without bearer401 with extension CORS; preflight204 with Authorization/Content-Type/Range allowed; owner ZIP anonymous401.
- No real owner Yandex listening or VPN result is claimed by these synthetic and HTTP checks.

## Deployment incident — retain for future operators
At approximately16:12:50–16:15:47UTC the deployment script created Application.php with0600 because umask077 narrowed the requested mode. CLI PHP lint ran as root and did not detect runtime unreadability. Both initial rollback attempts restored original bytes with the same restrictive mode, so rollback did NOT restore availability. Live API returned500.
- Dedicated recovery45652145816 restored source-only Application.php to0644; health200 verified. No DB/session/song/feature configuration changes.
- Corrected atomic replacement explicitly preserves readable source mode before rename, retains ownership, checks expected original/new hashes, lints, tests live behavior and rolls back on failure. Final application SHA **4f07e4b2026adfc7e742557d86fda2458a4dc28d5d5c9e3a9af54c0042422aac** matches the committed source; original SHA **ca2a855e6da8b56174130a50cf277b9778600830627bf1b2250192b19152418a**.
- Original source backup: /root/celikom-extension-cors-20261125/Application.php (root-private). Do not copy its0600 backup mode onto a runtime source file.
- This was our deployment error, not evidence that FlokiNET failed. Future deployments must verify runtime-reader permissions and actual HTTP recovery; restored hashes alone do not prove recovery.
- GitHub writes intermittently returned GraphQL/internal errors; concurrent Windows main commits were retained using fresh main heads/expected SHA. Browser fallback was not signed in; no user credentials requested.
- The shared maintenance request is reset to inert no-op afterward. Do not overwrite another chat's armed request, and do not advance main while its stale-main gate is pending.

## Next owner action
Replace contents of the same extension directory with0.4.80, reload the existing extension and Yandex tab. Clear old chrome://extensions error entries once to distinguish new occurrences. Check several successive replacements, a first-word intro and one mid-song approval if convenient; VPN after ordinary playback. If failure returns, use support diagnostic JSON and include whether a fresh CORS entry appeared. Do not remove the extension or re-register the account just to update.

Android/Windows source and artifacts are outside this change. Hostinger stays frozen and available for rollback; paid flags and production DB untouched.
