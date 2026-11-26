# CELIKOM Ad Protection — operational checkpoint, 2026-10-20

**Code checkpoint:** `d7ca9cb95724f2f9124269421971539ae92e4e42` on `feature/api-range`.
**Overall gate:** Stage 0 COMPLETE; Stage 1 FEASIBILITY **HOLD / LIVE evidence missing**. This is not a functional ad blocker. Stages 2–7 are not accepted.
**Separation:** code/docs exclusively under `ad-protection/`. Existing CELIKOM player/replacement and websites are not imported or modified.

## Working assets (read-only)

1. `standalone/`: inert independent MV3 shell (Stage 0).
2. `observer/`: separate unpacked MV3 observation extension for `https://music.yandex.ru/*`; content scripts use ISOLATED world. Passive class candidates and native HTMLMediaElement lifecycle events. Popup adds manual `ad-heard`, `normal-music`, `video-ad-seen`, `popup-ad-seen` markers, counters, reset, clipboard and JSON download. **No blocking, muting, player or request patching.**
3. `observer/export-core.js`: strict schema/field allowlist for popup display and download. Refuses unknown events/labels, invalid counters and oversized arrays; no URL/title/token copied from unknown fields.
4. Observer mutation processing bounded by 1000 records/callback, 160 added nodes/record, 160 queued roots, 40 roots/flush, and 120 candidates/scan; skipped work appears in `droppedRoots`. Pagehide suspends observation and pageshow resumes it. Manual marker history is capped at **20** to match HAR analyzer's per-report window cap.
5. `analysis/`: local CLI for HAR summary, observer/HAR manual time alignment, comparison across ad/control HAR files with ephemeral HMAC fingerprints, conservative audio safety result `HOLD` and zero generated block rules. No raw network request interception. Commands: `node analysis/summarize-har.mjs`, `node analysis/align-observation.mjs`, `node analysis/compare-har.mjs`.
6. `visual-lab/`: synthetic local DOM fixture with reversible banner demonstration only. It is **not** registered on Yandex Music. Does not prove current selectors.
7. Previous conversation supplied an optional **local evidence viewer ZIP** independently of GitHub. That archive is NOT the canonical repository source. If needed in a new chat, re-upload the ZIP; do not assume it was committed.

## Validation provenance

- On 2026-10-20, seven new `tests/observer-stress.test.mjs` cases passed in a **V8 mocked runtime**, checking callback caps, skipped-root count, pagehide/pageshow, marker limit, schema sanitization, malformed export rejection, and absence of request-filter permissions.
- Syntax smoke checks passed for modified browser scripts. The prior project contains additional Node-based and offline tests; `npm test` **has not been run against this final GitHub checkpoint in an authenticated Chrome environment or CI**. The new test file is committed so the next operator can run it.
- Earlier synthetic CLI and offline-viewer tests were reported in previous turns. Do not convert any of these into evidence that real Yandex advertisements are blocked.
- No authorized free/non-Plus Chrome session, live audio ad recording, browser-extension UI permission flow, real video/visual ad case, two-hour real playback or policy approval occurred.
- An observer candidate class `AudioAd_` is just a hypothetical CSS marker, never proof of audible ad.
- `droppedRoots > 0` means an observational gap; do not treat lack of detected ads as negative evidence.

## Safety gate

Audio request architecture D1 (separate ad-only request), D2 (player state), D3 (in-stream), or UNKNOWN: **UNKNOWN**. No ad-only network endpoint approved, no DNR filters added. `Range` / HTTP 206 / CDN / music requests and auth/entitlement are off limits without positive evidence. Reports always have UNKNOWN/HOLD and do not permit blocking.

## Next required work

1. Run `cd ad-protection && npm test` in checked-out branch. Confirm actual Chrome MV3 popup install and run on dedicated **authorized** account with region/service availability.
2. Use `docs/LIVE-CHROME-TEST-HANDBOOK.md` and `docs/STAGE1-BROWSER-TEST-PROTOCOL.md` to capture redacted, reproducible real banner/popup/video/audio observations with separate normal playback negative controls.
3. Analyze only **local** raw HAR; never upload raw HAR or authentication headers to GitHub/chat. Inspect sanitized JSON locally; collect independent reproductions.
4. If live audio is unidentifiable or reliably safe playback cannot be proven, record a technical NO-GO for full ad protection. Do not quietly ship banners alone.
5. Continue working in coherent larger batches. Update documents/checkpoint at the end of a substantial block or when user requests chat handoff; not after every small change. Leave PR #6 open and unmerged.

**Caveat about the shared branch:** PR #6 currently uses `feature/api-range` as its head. Even edits confined to `ad-protection/` become commits visible on that existing PR's branch. No one should merge/close PR #6 without a separate decision. Review branching strategy before any integration.
