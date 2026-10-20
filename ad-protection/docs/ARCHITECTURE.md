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


## Stage 1 research amendments — 2026-10-20

Architecture decision **for later prototypes only**: ISOLATED-world DOM adapter for verified visual ad nodes; optionally tightly constrained DNR for independently confirmed ad-only network requests. No MAIN-world patching, no broad fetch/XHR interception, no externally executed code, no automatic disabling of subscription/policy dialogs. Audio handling is currently UNKNOWN and is the highest release blocker.

Do not request all_urls or install host/permission changes in Stage 1. Never assume a blocked first-party media request is safe. Keep module fail-open, disable-able and entirely local. Details: docs/STAGE1-FEASIBILITY-2026-10-20.md.

## Actual isolated Stage 1 research implementation — 2026-10-20

- `observer/`: separate MV3 extension, `music.yandex.ru` URL match only, content `world: ISOLATED`; no explicit permissions, background, DNR, webRequest, server or production imports. Passive CSS candidate/HTMLMediaElement event observation, manually timestamped ad/normal events, popup export.
- `observer/core.js`: bounded last 20 manual markers, 80 recent events; cumulative counters. `observer/content.js`: no page monkeypatching; limits 1000 mutation records per callback, 160 added nodes per record, 160 queued roots, 40 roots/flush and 120 matches/scan. Skipped work increments `droppedRoots` (incomplete evidence warning). Observation disconnects on pagehide, reconnects on pageshow.
- `observer/export-core.js`: allowlisted numeric counts and event labels only, rejects raw URLs, unknown kinds, unexpected event shapes, invalid data and oversized payloads; loaded before popup.js. JSON download and clipboard expose only normalized object.
- `analysis/`: offline Node scripts analyzing local HAR, correlating manually marked windows using explicit clock offset and non-reversible ephemeral HMAC fingerprints, and producing a `HOLD` safety assessment. They cannot propose network block rules or prove audio causation.
- `visual-lab/`: opt-in synthetic HTML fixture for reversible DOM hiding only, never injected on live Yandex. No claim that selectors are current.
- Stage 0 `standalone/` no-op manifest remains intact. Tests and all docs are isolated under `ad-protection/`.

**Important:** Research observer is not a Stage 2 usable ad-blocking prototype. Actual audio D1/D2/D3 behavior remains unknown; safe control of music/CDN/Range requests is unproven. All integration, including permissions and manifest wiring, remains strictly future-gated. See `docs/STAGE1-OPERATIONAL-CHECKPOINT-2026-10-20.md`.
