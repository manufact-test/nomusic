# Test matrix · drafted in Stage 0

This is a **plan**, not test execution evidence. Mark actual observations after Stage 1. Use a dedicated authorized test account; do not commit credentials, cookies, tokens or captured user data.

| Case | Baseline observation needed | Expected future result |
|---|---|---|
| Top/side banner | Free account and, if applicable, Plus account in Yandex Music Chrome | No banner, normal page geometry |
| Popup / subscription promo | Exact screen/trigger | No unwanted visual ad, no broken UI or navigational lock |
| Video ad overlay | Distinct video overlay events, if observed | No ad and no permanent overlay |
| Audio ad between tracks | Distinguish from original music; identify player/session state | No audible ad with uninterrupted normal track changes |
| Playing original Yandex music | With and without optional standalone module | No stalls, false positives or missing music |
| Music seeking / audio streaming | Seek, next, playlist queue | No broken requests, especially partial content/Range |
| SPA navigation/reload | Collection, radio, playlist, page refresh | No observer leaks or repeated injections |
| Multiple tabs | Two Yandex tabs; close/reopen | No cross-tab corruption |
| Network errors | Offline/reconnect, timeouts | Fail-open, music restored |
| 2+ hour session | Actual listening with ad-observation log | No playback regression, CPU/memory bounded |
| Disabled module | Remove/disable standalone | Baseline experience unchanged |
| CELIKOM integration (Stage 7 ONLY) | Repeat all original + replacement tests | Both audio pipelines unaffected |

## Record format for Stage 1+

- Date/browser version, account subscription condition, geographic behavior if relevant.
- Trigger, URL or UI route (no personal data), ad class and what actually happened.
- Reproduction steps and number of trials; expected vs actual; environment constraints.
- Code/test fixture link if authorized. Evidence can show absence of observed ads but never prove all future ads absent.

## Hard gate

No "fully blocks advertising" release claim unless all ad categories encountered in the defined target Chrome test environment have passed actual end-to-end playback tests. Android and other platforms require independent validation.


## Stage 1 research checkpoint — 2026-10-20

Desk review only. No live ad session or playback test was performed, so the above cases remain PLANNED and none is PASS.

Detailed research ledger: STAGE1-EVIDENCE-MATRIX.md.
Reproducible authorized test recipe: STAGE1-BROWSER-TEST-PROTOCOL.md.
Technical constraints and decision: STAGE1-FEASIBILITY-2026-10-20.md.

**Additional mandatory negative controls:** Never hide functional login/paywall/consent dialogs, break first-party audio/CDN/HTTP Range, mute actual songs, silently skip a song, or claim video blocking merely because its DOM layer disappeared. Audio pass requires actual audible ad suppressed without silence/stall while original music continues.

## Additional synthetic / code-level tests — 2026-10-20

Read-only research test sources currently include `tests/observer.test.mjs`, `tests/observer-lifecycle.test.mjs`, `tests/observer-stress.test.mjs`, `tests/manual-markers.test.mjs`, `tests/har-evidence.test.mjs`, `tests/evidence-correlation.test.mjs`, `tests/align-observation.test.mjs`, `tests/align-quality.test.mjs`, `tests/audio-safety.test.mjs`, `tests/lab-end-to-end.test.mjs`, `tests/visual-fixture.test.mjs`, `tests/research-boundary.test.mjs`, and `tests/stage0.test.mjs`.

Seven new observer stress/privacy cases were executed in a V8 mocked runtime and passed: callback flood bounds; 400-node descendant scan cap; pagehide/pageshow; 20 retained markers; URL/token field stripping; malformed export refusal; safe script order and manifest. This is **not a Chrome test and not equivalent to executing the final full Node suite**.

Mandatory next checks: locally run `cd ad-protection && npm test` against exact new branch HEAD; load `observer/` unpacked in clean Chrome profile, confirm user-visible popup and tab messaging; exercise DOM/SPA navigation and repeated reload; compare observed ads with normal playback and count skipped roots; long real session and Chrome permission-policy review. All existing visual/audio/playback cases in the table remain PLANNED / NOT LIVE TESTED, not PASS.
