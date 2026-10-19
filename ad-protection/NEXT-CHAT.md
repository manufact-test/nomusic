# NEXT CHAT — CELIKOM Ad Protection

Checkpoint: **2026-10-20 · Stage 0 COMPLETE · Stage 1 IN PROGRESS (desk research complete / live experiments not done)**.
Existing branch: feature/api-range · repo: https://github.com/manufact-test/nomusic · isolated directory: ad-protection/.

## Required reading
1. ad-protection/README.md and MASTER.md
2. ad-protection/ROADMAP.md
3. ad-protection/docs/STAGE1-FEASIBILITY-2026-10-20.md
4. ad-protection/docs/STAGE1-EVIDENCE-MATRIX.md
5. ad-protection/docs/STAGE1-BROWSER-TEST-PROTOCOL.md
6. ad-protection/docs/ARCHITECTURE.md
7. ad-protection/docs/TEST-MATRIX.md
8. ad-protection/docs/RESEARCH-SOURCES.md
9. ad-protection/standalone/manifest.json and ad-protection/tests/stage0.test.mjs

## Research result
- Stage 0 has an inert no-op independent MV3 extension. **No advertising is blocked today.**
- Chrome MV3 DNR and ISOLATED DOM content scripts are credible candidates for separately identifiable visual ads; request rules cannot decode in-stream audio, and ordinary MV3 cannot use webRequestBlocking.
- Historical third-party Yandex-specific selectors exist, but their current functionality is NOT proven. YaBlocker does not even declare a music.yandex.ru page match. A desktop MIT WebView project globally patches fetch/XHR; do not copy that architecture.
- All relevant licenses/policy notes and exact links are in research docs. No third-party code or lists were copied.
- **Audio advertising architecture D1 separate / D2 player-state / D3 in-stream / UNKNOWN is unclassified.** This blocks a responsible GO for complete ad suppression.
- No live authenticated Yandex Music free/non-Plus account, ad session or Chrome runtime test was available in the Stage 1 desk pass. No claims of full coverage, no Stage 1 final GO, no Store readiness, no integration.
- Chrome Web Store minimum functionality, narrow permissions, MV3 local code, privacy and Yandex terms need fresh review before shipping.

## Next substantial work block
1. Establish **authorized** Chrome non-Plus/Plus comparison and collect redacted baseline observations as described in the browser test protocol. Do not commit cookies/tokens/signed URLs or raw HAR.
2. Categorize each real visual/video/audio ad; especially prove whether sound is a separate ad-only request versus player state or an in-stream segment.
3. Document independent LIVE events in evidence ledger, including at least one genuine audio insertion if it occurs.
4. If safe separation is proven, move to a tightly scoped, standalone, default-off observation/prototype with fail-open and exact-domain permissions. Do not modify CELIKOM engine or parent manifests.
5. If audio cannot be safely distinguished, declare NO-GO for **full** Chrome ad protection; do not quietly ship banner-only.
6. Only after meaningful batches, update documentation. Work within ad-protection/ exclusively; no PR merges.

## Absolute boundary
Do not edit extension/, android/, server/, website/, root docs, workflows, parent manifests, PR #6 or any unrelated code. No separate repo. CELIKOM integration remains Stage 7 and requires explicit owner authorization.

Current independent test command: from ad-protection/ run npm test. The standalone shell and Stage 0 tests remain unchanged; no claim that they ran during desk review.
