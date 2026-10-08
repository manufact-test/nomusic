# CELIKOM Stage 2 Player Integration Test Plan

## Scope

Version `0.2.1` validates the production `ServiceAdapter`, `YandexMusicAdapter` and `PlayerBridge`. It observes the original player but does not replace or mute audio. A successful run therefore must not change what the user hears.

## Automated gate

| Check | Expected result |
| --- | --- |
| Album route Track ID | Exact catalog entry is selected |
| Landing/fetch Track ID | Exact entry is selected without `/track/{id}` in the page route |
| Ambiguous queue | No Track ID is selected |
| Master media | Detached playing audio beats known short ad video |
| Event contract | Native events map to stable uppercase events |
| SPA track change | One `TRACK_CHANGED` contains previous and current exact IDs |
| Adapter lifecycle | Repeated mount is idempotent; unmount restores wrappers and listeners |
| Bridge lifecycle | Repeated start installs one listener and one heartbeat |
| Stale event | Lower sequence and foreign session are ignored |
| Manifest boundary | MAIN and ISOLATED scripts exist and start at `document_start` |
| Previously open tab | Missing controller is injected automatically in MAIN/ISOLATED order |
| Bootstrap integration | Packaged scripts establish a healthy bridge and return exact Track ID |
| Injection denied | Diagnostic contains a failure code and popup polling does not retry |
| Lost INIT | Heartbeat retries INIT; connection does not wait forever |
| Async startup error | Runtime diagnostic still responds with `startupError` |

Run:

```bash
npm run test:extension
npm run validate
```

## Live Yandex Music gate

1. Disable or remove the old `CELIKOM Playback PoC` extension so only one observer is active.
2. Build with `npm run build:extension`.
3. Open `chrome://extensions`, enable Developer mode and load `extension/dist/unpacked`.
4. Refresh the already-open Yandex Music tab once after installing this build.
5. Open CELIKOM, press `Старт`, then start a track in Yandex Music.
6. Confirm the status becomes `Трек найден` and the popup shows the current title and artist.
7. Hover the title and confirm its Track ID matches the URL when the route contains `/track/{id}`.
8. Press `Скопировать диагностику` after each scenario below and preserve the JSON.

| Scenario | Expected result |
| --- | --- |
| Direct track / album | Exact ID, non-ambiguous confidence at least 70 |
| Landing/main or search | Exact ID from state/fetch metadata even without a track route |
| Playlist or queue | Exact ID changes with the playing track |
| Pause/resume | `PAUSE` then `PLAY`; same Track ID and media ID |
| Seek forward/back | `SEEK`; current time follows the original player |
| Next/previous | One new exact Track ID; no stale previous event becomes current |
| SPA navigation | Bridge remains ready/healthy without page reload |
| Advertisement | Short `strm.yandex.ru` video is `known-ad-media`; audio remains master |
| Stop/start | UI changes state; original Yandex audio is never modified |
| Page refresh | One controller and one healthy bridge initialize again |

## Acceptance

Stage 2 closes after automated CI is green and one live regression covers direct/album, landing/search, queue next/previous, pause, seek and SPA navigation. Any wrong or ambiguous ID blocks Stage 3 replacement work; a missing ID is diagnostic but remains fail-closed.

### Accepted — 2026-10-08

The owner reported completing the manual checklist on `0.2.1`: «Готово, всё прокликал». This is the acceptance evidence for scenario coverage, not an independently recorded browser run.

The supplied snapshot independently confirms `READY`, `startupError: null`, exact non-ambiguous Track ID `45886281` at confidence 260 on `/search`, a playing detached audio master, advertisement rejection, a healthy protocol-v1 bridge and no connection error. Its log also records Start, Stop and original-audio confirmation. GitHub CI run 9 passed for `160869b58e51f46a0ea69e0a41a47e6cf2eb13b4`; PR #4 was merged into `develop`. Stage 3 is unlocked; its playback gate remains separate.

