# Architecture boundaries · Stage 0

## Topology

Existing (must remain unchanged for Stage 0–6):

    repository/
      extension/         ← production CELIKOM Chrome module (untouched)
      android/           ← active Android PoC (untouched)
      server/            ← untouched
      website/           ← untouched
      ad-protection/     ← entirely isolated research and implementation

Standalone research package:

    ad-protection/
      standalone/manifest.json     ← inert MV3 sandbox in Stage 0
      tests/stage0.test.mjs        ← no-cross-impact checks
      docs/                       ← requirements, tests, source review

Nothing in package.json at repository root or extension/ imports ad-protection/.
No site access, request modification or background service is active in Stage 0.

## Stage 2–5 design sketch (not implemented)

- Low-privilege standalone extension with only the minimum Yandex Music host permissions.
- Content script for narrowly scoped visual UI changes; observer lifecycle with bounded work.
- Prefer MV3 declarativeNetRequest only for positively identified ad network patterns, with explicit exclusions for audio/CDN/API/HTTP Range endpoints.
- Separate audio research adapter only when evidence shows safe ad discrimination; never indiscriminately mute or block all media.
- Runtime flags for experimental adapters; diagnostics default to privacy-preserving counters, no payload collection.
- Protect ordinary playlist navigation, audio playback, replacement fallback, account sign-in and upgrade notices relevant to service access.
- Fail-open if classification uncertain or module fails; do not fail closed on all network traffic.

## Integration contract for Stage 7 (future only)

1. Explicit user GO after standalone Chrome coverage + policy review.
2. Install-time/build flag default OFF. All module scripts, rules, permissions and UI references conditional on flag.
3. No ad-module code in music replacement/player core. Small declared interface in integration adapter only.
4. Rollback: rebuild CELIKOM with flag OFF and verify manifest/rules contain none of the optional module's permissions or registrations.
5. Regression test against baseline original and replaced streams (including media seeking/Range), reconnection, multiple tabs and Android independence.
6. This document is a boundary design, NOT a claim of implementation or guaranteed zero risk.

## Third-party source policy

Research references and design ideas may be studied. Do not paste code from repos lacking explicit licenses; MIT notices must be maintained; GPL/AGPL code requires careful compliance analysis and is not a default source for proprietary CELIKOM.
