# CELIKOM extension 0.4.81 — VPN recovery owner candidate, 2026-11-25

## Exact candidate and delivery
- Source main commit **4cc7814454111f89eb5fe779e5093e6ab584a71d**.
- ZIP **celikom-extension-0.4.81.zip**, **2,491,245 bytes**.
- SHA-256 **9ddf20fef3c597eb8e91af7c51a4938fde85df792923473c934fe53e258b2380**.
- Local and isolated FlokiNET builds are byte-identical. Owner ZIP was saved and delivered through this conversation as a private file.
- **NOT promoted to the website:** protected promotion45657466101 failed before any runner step. Do not offer a celikom.com0.4.81 URL as available until independent promotion succeeds.
- Previous0.4.80 ZIP/root copy and download remain unchanged. Source/build candidate0.4.81 is not yet owner-accepted for real VPN listening.

## Diagnostic evidence
Owner supplied0.4.80 report (2026-11-25 16:32UTC), described normal playback mostly good and fragments after VPN.
- Last12 recorded joins:11 activated with native masterTimeMs100, confirming the previous intro fix; one track48592143 had resolveMs4768, prepareMs5148 and masterTimeMs3737.
- Config requests include two transport failures followed by a1905ms success; later API rows200. At export replacement active, no current error, drift-2ms, over130s buffered.
- Older failures are outside the48-entry transition trace/20-entry log window. Do not claim every reported fragment has been attributed from this one bounded sample. New bounded restore history helps distinguish these on the next report.
- Code reproduction: network hints always sent unavailable and destroyed a decoder even while the last server grant had not expired. Audio Range code retried temporary HTTP statuses but immediately failed on fetch/body network reset. A slow positive lookup could then enter a late partial-MSE seek.

## Scoped changes
1. On network hints, immediately revalidate via existing authority checks but preserve only the ORIGINAL unexpired server grant, capped by the existing10s/actual entitlement expiry. No fresh grant from browser hints, no offline grace extension. Independent deadline timer suspends even a hung recheck. Definite denial/incident clears authority immediately. Stop/logout, identity/epoch races and shorter server expiry remain fenced.
2. Retry only the same UNAPPENDED MP3 byte range on transient fetch/body TypeError, alongside bounded existing temporary HTTP retries. Maximum3 attempts share one15s range budget. Verified buffered audio and decoder are retained. No duplicate append, no decoder-write retry, no retry on401/403, HTML edge block, malformed MIME/Range/body or revoked signature.
3. Positive MP3 resolution after native playback has advanced uses the already accepted complete-file preparation/alignment path, keeping original audible until fresh alignment. If an intro MSE decoder finishes after the intro was released, replace that decoder once with complete-file preparation. Normal paused100ms intro stays on the accepted fast path. No rejected MSE live-join, new playback architecture, gain/seek/UI redesign or native-client hook.
4. Add bounded12-entry restore history (reason, track, phase, time, HTTP status; no URLs) and join mode to full playback diagnostics. Public diagnostics access rules unchanged.

## Validation and limits
- Local and isolated FlokiNET **381/381 extension tests** PASS. Added grant-preserving/revoked/expired/hung/Stop/logout races, identical-range header/body retries, byte-preserving append, fixed retry budget, cancellation and late-join alignment cases.
- Extension artifact45656926920 SUCCESS:381 tests,4 spool tests, manifest, origin/permissions, security, checksum; receipt source/run/attempt and ZIP hash/size agree.
- Full repository CI45656927103 attempts1 and2 failed BEFORE runner setup (no steps/logs). This is **not a full-CI pass or a code-test failure**; exact provider reason unavailable through the current connector. Do not infer billing or enable paid features.
- Protected promotion45657466101 likewise failed before any steps: no SSH command, root copy, nginx reload, backend file edit or DB change happened in this candidate rollout.
- A local native Chromium smoke was attempted but its binary/runtime could not start; do not claim a new real-browser/VPN result. Real MAIN/ISOLATED integration and media logic are covered by the381 tests; actual listening remains owner retest.
- Server Application.php/CORS0.4.80 correction, permissions and all API feature/payment flags unchanged in this turn. No Android/Windows source or artifact changes; concurrent main commits preserved.
- Pending promotion request reset to inert no-op. Do not hand protected credentials to the isolated CI runner to work around the unavailable hosted job.

## Reproduce / next
npm ci; npm run test:extension; npm run build:extension; npm --prefix extension run validate; npm run security.
Private spool: /srv/celikom/ci-runner/runner/celikom-build-spool/4cc7814454111f89eb5fe779e5093e6ab584a71d-45656926920-1/ .
Future normal protected promotion must independently verify the known receipt/hash and preserve Basic gate and previous releases; it must not execute spool code as root.

Owner: replace the same extension folder with0.4.81, reload existing extension and Yandex. During playback toggle VPN, then switch several replacement tracks. If a fragment recurs, export support diagnostics; new restore history and joinMode/networkRetries distinguish authority, byte transport and late adoption. Complete-file late adoption can require more download time/bandwidth than normal intro streaming; original stays audible while it prepares.
