# Intermittent access reconnecting — 2026-10-14

Owner reported extension 0.4.37 stalled at `access_reconnecting`, with repeated `config` and `auth/me` transport timeouts at approximately 8000 ms and HTTP status null. Track identity and MAIN bridge were healthy. Owner then confirmed spontaneous recovery and requested investigation of repeated occurrences.

Read-only Hostinger diagnostic: https://github.com/manufact-test/nomusic/actions/runs/38552381767
Active backend remained `0.4.37-b05ddfc858940c0c86979e3af2056f3cafa7dada`. DB connect + SELECT 1: 1.14 ms. In-process health/config/unauthenticated auth check: 0.15/1.41/2.24 ms. Nine on-host public HTTPS checks completed in 12–21 ms with expected HTTP 200/401. Auth and entitlement flags remain enabled. The unauthorized auth test does not test the owner's actual session.

External measurements from this execution environment included one health request taking 10.693 seconds, of which TLS establishment accounted for 9.670 seconds. Other requests took approximately 4.8–6.9 seconds. This demonstrates a delayed connection can outlast the client's old 8-second auth timeout, but does not establish whether the owner's historical delay arose in their ISP, VPN, hosting edge or another network segment. No evidence of slow PHP/MySQL was found in the current probes; past intermittent backend load is not ruled out by a present-time probe.

Client hardening in extension 0.4.38:
- Raise bounded auth/control request wait from 8 seconds to 20 seconds; existing account-creation/login timeout remains 20 seconds.
- Raise catalog API wait from 6 seconds to 20 seconds so a cold connection does not fail earlier in resolve.
- Coalesce only simultaneous config/auth-me/entitlement GET checks with the same session generation and credential. Clear the pending entry after success or failure; no new authority cache and no reuse across credentials or login/logout generations.
- Never automatically retry POST mutations, rotate refresh credentials on transport failures, or authorize offline playback.
- Preserve existing ten-second access verification cache, retry behavior, denial/revocation handling and fail-open playback.

Validation: all 197 extension tests PASS locally and in configured private build https://github.com/manufact-test/nomusic/actions/runs/38553001519. New deterministic tests cover a healthy response after 10 seconds, a genuine outage bounded at 20 seconds, concurrent request coalescing, failure recovery, different credential isolation and renewed checks after settlement. Native Chromium support flow and configured-package security gate PASS in that build. Full monorepo regression: https://github.com/manufact-test/nomusic/actions/runs/38553007536 (tracked separately).

Configured ZIP: `CELIKOM-0.4.38-full.zip`, 2445712 bytes, SHA256 `4c0b947245fe7939ae10c6fbd125c4eba35443ee626c32be36c164a19365c85b`. No backend deployment, data mutation, new access grant, session reset or audio change accompanied this client update. Install in the same existing unpacked directory, reload extension and then Yandex tab to preserve installation path and avoid stale page scripts. Owner verification remains pending. Long network outages can still suspend playback safely; this is resilience hardening, not a guarantee of uninterrupted connectivity.
