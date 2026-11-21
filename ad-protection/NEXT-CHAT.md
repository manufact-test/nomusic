# NEXT CHAT — CELIKOM Ad Protection (CURRENT HANDOFF · 2026-10-20)

**Repo:** https://github.com/manufact-test/nomusic
**Branch:** `feature/api-range`. **Last CODE commit:** `d7ca9cb95724f2f9124269421971539ae92e4e42` (newer docs commit on same branch: read GitHub HEAD).
**Stage:** Stage 0 COMPLETE; Stage 1 feasibility HOLD — research observation tools implemented, but live Yandex Music ad/network evidence missing. Stage 2–7 NOT ACCEPTED; no blocking or integration.
**Boundary:** Only `ad-protection/`. Do not alter `extension/`, `android/`, `server/`, `website/`, root manifests/workflows, PR #6 status or unrelated CELIKOM code.

## Mandatory first reads (in order)

1. `ad-protection/docs/STAGE1-OPERATIONAL-CHECKPOINT-2026-10-20.md` (newest complete implementation snapshot).
2. `ad-protection/README.md`, `MASTER.md`, `ROADMAP.md`.
3. `ad-protection/docs/LIVE-CHROME-TEST-HANDBOOK.md`, `STAGE1-BROWSER-TEST-PROTOCOL.md`, `TEST-MATRIX.md`.
4. `ad-protection/docs/STAGE1-EVIDENCE-MATRIX.md`, `STAGE1-FEASIBILITY-2026-10-20.md`, `RESEARCH-SOURCES.md`, `ARCHITECTURE.md`.
5. Current code: `observer/core.js`, `observer/content.js`, `observer/export-core.js`, `observer/popup.*`, `observer/manifest.json`; `analysis/*.mjs`; `visual-lab/`; `tests/` and `standalone/manifest.json`.

## Implemented and verified versus unverified

- MV3 `observer/` matches Yandex Music, ISOLATED page observation, native HTMLMediaElement lifecycle counts, candidate classes, manual labels for real audio/video/window and ordinary tracks, limited JSON download/copy.
- Observer state: **20 manual markers**, recent event cap 80, capped mutation processing (1000 records/callback, 160 added/record, 160 pending roots, 40/flush, 120 subtree matches). Dropped observation is counted in `droppedRoots`; absence of candidates means nothing if droppedRoots >0. Pagehide/pageshow handled. Export-core strips unapproved strings and invalid fields.
- Local offline HAR CLI summarizes requests, manually aligns observer marks using explicit offset, compares ad/control windows via random keyed fingerprints, flags audio Range/206 risks. **No DNR, no network interception, no actual audio-ad suppression.** Always UNKNOWN/HOLD.
- Visual lab only hides **synthetic** banners in a separate fixture; not Yandex Music implementation.
- **Latest code-run checks:** seven observer stress, lifecycle and export cases passed an isolated V8 mock on 2026-10-20. Previously generated Node/synthetic test sources exist, but the **full final npm test/Chrome run is not yet verified**. Do not report live blocking success.
- A previous chat attached a local report-viewer ZIP, **not committed as source** in GitHub. It is optional. If needed, request ZIP reattachment rather than pretending it is available in repo.

## Next substantial block

1. On current HEAD run `cd ad-protection && npm test`; fix regressions. Recheck no scope escape via GitHub compare.
2. Verify clean-profile Chrome MV3 `observer/` installation, popup tab messaging, download, counters, pagehide/pageshow, multi-tab and SPA navigation. Do NOT test unauthorized accounts or bypass subscriptions/georestrictions.
3. Obtain authorized real non-Plus audio and visual ad observations, with normal playback negative controls. Capture sanitized notes and local-only HAR if permitted. Use documented CLI and exact timing offsets. No raw HAR, tokens, cookies or signed media URLs in chat or GitHub.
4. Classify genuine audio insertion as separate request (D1), player state (D2), in-stream (D3), or UNKNOWN; ensure no music/HTTP Range breakage. If separation fails, recommend NO-GO for full ad protection instead of declaring banner-only done.
5. Work **in batches** (several coherent tasks before reporting). The owner specifically wants documents updated when requesting chat handoff or after an exceptionally large block, not after every small task.

## Absolute safety / PR

PR #6 remains open and unmerged. It has head branch `feature/api-range`; commits on that branch naturally update its diff, even when files are isolated. Do not merge/close/rebase the PR without consent. No modification outside `ad-protection/`. Do not claim production readiness or Store permission.

## Definition of progress

Stage 1 research tooling is real; Stage 1 GO is **not** granted. The crucial next evidence is real authorized audio ad behavior, plus ordinary audio/queue/seek negatives. Only subsequent independently approved standalone stages may consider visual/audio suppression; final CELIKOM integration is Stage 7 and requires user approval.
