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
