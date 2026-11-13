# Stage 1 — authorized browser test protocol

Status: written 2026-10-20; NOT EXECUTED. Required to close full-coverage feasibility.

## Environment

- Desktop Chrome stable version/build recorded at test time; clean profile with only the *independent* Ad Protection test extension when one exists.
- A permitted Yandex Music account without Plus, and optionally a second account with Plus or the same account before/after legitimate subscription change. Never attempt to change subscription entitlement.
- Record broad geographic service region as given by the authorized account. No attempts to bypass region locks or protections.
- Two clean run modes: standalone module disabled (baseline), and module enabled for strictly isolated tests. In Stage 1 there is currently only a no-op shell.
- Do not run Yandex Music with another adblocker during controlled comparisons. Record any unavoidable built-in browser protection.
- Use only non-sensitive, non-copyrighted metadata logs. A real licensed audio file or proprietary response body is not a test fixture for this repository.

## Capture procedure, baseline first

1. Verify normal Yandex Music functionality and log the Chrome version, web domain, non-Plus subscription state, route and test conditions. Do not attach account screenshot that reveals personally identifying information.
2. Run playback using ordinary user controls. Observe real banners, popups, videos, and audio interstitials without modifying requests. Record independent repetitions; absence is NOT success.
3. Use DevTools Network with request URL query strings stripped before any recorded evidence. Capture just request origin, normalized path shape, type, status, relevant response content-type and 206/Range metadata. Never export raw full HAR into GitHub because it can contain tokens, signed URL query strings or user identifiers.
4. For each observed audio insertion note player action, timing relative to previous and next songs, whether audible ad overlaps or has its own playback, whether the page signals ad status and whether transitions complete.
5. Reproduce a suspected ad-only request in a second independent run where possible. Classify as D1 (separate), D2 (player state), D3 (in-stream) or UNKNOWN. An unverified URL substring cannot be used as a DNR block rule.
6. Only after a robust D1 request or DOM signature is proven, design a standalone experimental adapter with default-OFF rules and explicitly scoped sites. Do not import into the main CELIKOM extension.
7. Run module ON and OFF using equivalent sessions. Verify correct music, playback controls and no removed functional dialogs. Record regression and side effects, not just disappearance.
8. Compare browser and ad behavior across page reload, SPA route, playlist, radio, queue next/previous, repeat, seeking and a two-hour continuous session. Also test offline/reconnect, two tabs, disable/re-enable and uninstall.
9. Record all uncaught errors, broken song events, excessive DOM rescans, false positives and unexpected 4xx/5xx/blocked media requests.
10. For eventual Stage 7 (NOT now), repeat on CELIKOM's normal and replaced tracks, especially HTTP Range (206), token refresh, and fallback after API errors.

## Category acceptance

| Type | Minimum observation requirement | Pass requires |
|---|---|---|
| Banner | At least one genuine ad on a non-Plus baseline, multiple navigation modes | Removed before noticeable presentation, normal layout, no collateral DOM hiding |
| Popup | Ad-only popup observed, separately classify functional paywall/login/consent | Genuine ad not displayed, user action dialogs unchanged |
| Video | Genuine video ad observed in baseline, note whether sound is independent | Both video and its audio suppressed, subsequent music plays |
| Audio | Independent audible ad occurrences, ideally at least 3 across 2 distinct sessions; route/region recorded | No audible ad, *no silent ad-length gap*, no stuck or skipped music, correct queue transition |
| Unobserved class | No reliable event despite valid trial | UNVERIFIED, NOT PASS. Stage 1 cannot claim full coverage |

## Hard negative controls

- Subscription / login / consent / payment / geo restriction notices that are service functionality must remain intact.
- Original music and, eventually in integration tests only, replaced CELIKOM streams must play without false block.
- Audio playback must recover if a suspected ad endpoint becomes ambiguous or changes.
- Range requests, CDN assets, artwork, playlists, telemetry used to maintain player state and service APIs must not be broadly interrupted.
- Fail-open: if ad classification fails, prioritize continuing lawful music playback over ad blocking.

## Sanitization and data retention

Allowed in GitHub: redacted UI description, CSS structure with no PII, origin+redacted path pattern, event timestamps relative to local session, MIME, request method/status, selected Range header presence/206 (not credentials or exact byte-positions if sensitive), test flags and observed outcomes.

Forbidden in GitHub: authorization headers, cookies, Yandex OAuth tokens, signed media URLs (including full query strings), raw HAR, account IDs, audio files, commercial creative contents, private emails or screenshots with identities. Collect only what is needed for research; do not transmit logs to any CELIKOM server.

## Stop conditions

Immediate stop and disable standalone rules if a song stalls, ad classification cannot be separated from music, requests to music CDN are blocked, player controls/paywall are corrupted, or extension asks for overly broad/undisclosed permissions.

No publication or integration without an explicit stage decision with real reproduced evidence. This protocol is NOT evidence of execution.

## Observer Lab quick-start amendment — 2026-10-20

The standalone passive browser instrument now lives at `ad-protection/observer/`, separate from the no-op `standalone/` shell. Use **Load unpacked** in a clean Chrome profile, reset its counters, mark truly audible/visible ads and ordinary playback explicitly, and download its allowlisted JSON (at most 20 markers). Beware `droppedRoots`: DOM changes exceeding observation limits may go unrecorded. Browser and account auth tests are still outstanding.

Full operator commands and privacy handling: `docs/LIVE-CHROME-TEST-HANDBOOK.md`. Only run CLI HAR comparisons locally; never upload raw HAR, unredacted DevTools exports or account identifiers. Treat the output `UNKNOWN/HOLD` as evidence uncertainty, not ad-block success.
