# CELIKOM · Ad Protection (isolated R&D)

**Status:** Stage 0 COMPLETE · Stage 1 IN PROGRESS / HOLD (observer and offline lab available; live ad tests pending)  
**Date:** 2026-10-20  
**Repository:** manufact-test/nomusic · **branch:** feature/api-range  
**Scope today:** standalone browser extension for Yandex Music; NO integration with CELIKOM.

## Purpose

Research and, only if feasible and compliant, implement an optional module for advertising in Yandex Music: page banners, overlays, promotional video, and audio ad insertions. The owner requires a **complete user-facing result** within the validated Chrome scope; a banner-only implementation must not be presented as finished.

Do **not** promise 100% coverage before real testing. The official Android application is a separate technical problem; do not assume Chrome methods work on Android.

## Ground rules — mandatory

1. All work remains INSIDE this ad-protection/ folder until the explicitly approved final integration stage.
2. Do not edit extension/, android/, server/, website/, root package manifests, shared GitHub workflows, or CELIKOM product documentation during independent development.
3. Never merge or close preexisting CELIKOM PRs as part of this effort; no change to production behavior, entitlement checks, or music replacement.
4. Standalone research extension only. Current standalone/manifest.json has NO ads logic, injections, site privileges, content scripts, or network interception.
5. Everything added must be removable by deleting ad-protection/ without impacting the rest of the repository.
6. No account credentials, cookies, or tokens in commits; test accounts/consent only, no remote credential collection.
7. Analyze Chrome Web Store rules and Yandex terms transparently; do not hide functionality to evade review.
8. Do not reuse third-party code unless its license and notices are checked. Existing GPL projects are research references, not copy-and-paste sources for a proprietary app.
9. Stage 1 is an investigation. If reliable full ad handling is impossible or violates distribution requirements, record NO-GO rather than introducing a partial feature.

## Directory map

- MASTER.md — goals, hard requirements, gates
- ROADMAP.md — stages 0–7 and acceptance checks
- NEXT-CHAT.md — current handoff / instructions for new chat
- docs/ARCHITECTURE.md — independence boundaries and integration contract
- docs/TEST-MATRIX.md — observations and regression scenarios
- docs/RESEARCH-SOURCES.md — source/licensing inventory
- standalone/ — installable, inert Manifest V3 research shell (NO blocking in Stage 0)
- observer/ — independent read-only MV3 observation extension with popup and safe JSON export; not an ad blocker
- analysis/ — local read-only HAR analysis, marker alignment, ad/normal comparison and HOLD safety diagnostics
- visual-lab/ — synthetic reversible banner fixture; never injected into Yandex Music
- tests/ — Stage 0, observation, privacy, synthetic analysis, CLI and UI/fixture tests
- package.json — independent npm scripts; not added to root workspaces

## Verify Stage 0

From repository root:

    cd ad-protection
    npm test

On a test machine you can load ad-protection/standalone as an unpacked extension. At Stage 0 it intentionally does nothing. Do not install it expecting to block advertising.

**Stage 1 research:** read docs/STAGE1-FEASIBILITY-2026-10-20.md, docs/STAGE1-EVIDENCE-MATRIX.md and docs/STAGE1-BROWSER-TEST-PROTOCOL.md. No ad blocking is implemented or live-tested. The Stage 1 gate is HOLD pending real authorized non-Plus Yandex Music advertising evidence. No production integration.

## Operational Stage 1 checkpoint — 2026-10-20

Code: `d7ca9cb95724f2f9124269421971539ae92e4e42`. New `observer/export-core.js` strictly allowlists downloaded/copied observations; 20 retained manual markers (consistent with HAR 20-window cap), up to 80 recent events. Observer DOM mutation processing has explicit per-batch, per-root and per-scan limits, with `droppedRoots` indicating potentially incomplete observations. Manual events are not proof of advertisements.

**Use `observer/` for the research extension, not `standalone/`.** See `docs/LIVE-CHROME-TEST-HANDBOOK.md` for clean-profile installation and careful authorized testing. See `docs/STAGE1-OPERATIONAL-CHECKPOINT-2026-10-20.md` and `NEXT-CHAT.md` for full status. The locally shared evidence-viewer ZIP from a previous conversation was not committed to GitHub; provide the ZIP again if the next chat needs it.

From `ad-protection/`: `npm test`. Seven new stress/privacy cases passed an isolated V8 mock run in the latest development chunk. The **full final repository suite and live Chrome Yandex playback are not verified in this checkpoint**; perform them next. Do not treat earlier synthetic test passes as actual ad-blocking coverage.

## Offline quality check for actual observer exports

After separate, consented Chrome observation runs (NOT synthetic proof), save each
`celikom-observation.json` under a distinct local filename. From `ad-protection/`:

```sh
node analysis/assess-session-set.mjs --ad=audio-1.json --ad=audio-2.json --normal=music-1.json --normal=music-2.json
```

The standalone tool reads **only local observer JSON**, never raw HAR, and emits
allowlisted counts, missing controls, DOM overload warnings and cap warnings.
A negative control must contain an explicit `normal-music` manual mark and no
manual ad marks. A positive ad capture requires a manual ad mark; CSS candidates
alone cannot qualify. Two independently captured audio-ad and ordinary-music
sessions are the minimum for **manual comparison only**. Even a complete result
always remains `UNKNOWN / HOLD` and allows **zero blocking rules**. The
separate local HAR tools remain essential for audio, Range/206 and causal checks.
