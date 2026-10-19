# CELIKOM · Ad Protection (isolated R&D)

**Status:** Stage 0 COMPLETE · Stage 1 NEXT  
**Date:** 2026-10-19  
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
- tests/ — Stage 0 smoke tests, local only
- package.json — independent npm scripts; not added to root workspaces

## Verify Stage 0

From repository root:

    cd ad-protection
    npm test

On a test machine you can load ad-protection/standalone as an unpacked extension. At Stage 0 it intentionally does nothing. Do not install it expecting to block advertising.

**Next action:** Stage 1 only: investigate ads + policy feasibility; update documents in this folder when evidence has been collected. No production integration.
