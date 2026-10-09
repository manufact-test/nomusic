# CELIKOM Stage 5 — live MP3 stabilization and acceptance

Updated: 2026-10-09. Source of live results: owner's direct testing in Chrome/Yandex Music; automated results are separate evidence. This document does not supersede the Master TZ MVP v1.4 or Work Plan MVP v1.5.

## Verified so far

- Approved user-supplied MP3 associated with Yandex Track ID `144530503`, measured duration 180872 ms (3:00.872); approved mapping replacement ID 1 in private Hostinger MySQL/audio store; analytics disabled and replacements enabled.
- HTTPS `resolve` authentication, signed MP3 response, Content-Range byte response (`206`), audio/mpeg and allowed Yandex CORS confirmed in GitHub Actions run [37846857378](https://github.com/manufact-test/nomusic/actions/runs/37846857378). Hostinger edge may omit `Accept-Ranges` although actual range behavior works.
- Live debugging established Yandex Music's `media-src` CSP blocks direct media URL from the Hostinger origin. The CSP permits `blob:`; extension 0.4.3 uses MediaSource audio/mpeg and bounded 512 KiB HTTPS Range fetches, no whole-file JS Blob.
- Extension build/test [37848261630](https://github.com/manufact-test/nomusic/actions/runs/37848261630): **67 tests passed**; main CI [37848269651](https://github.com/manufact-test/nomusic/actions/runs/37848269651) succeeded.
- Owner confirmed on 2026-10-09 that the **real** hosted version played in Chrome (not synthetic demo). Owner subsequently reported **6 of 6** first-round tests passed: (1) pause/play; (2) seek 30–60 seconds both ways; (3) seek near end; (4) volume/mute; (5) next track uses original; (6) manual Return Original works.
- This is owner's functional smoke acceptance; the longer stress, refresh, disabled-extension watchdog and repeat-deploy gates below remain open. No general availability/client release is implied.

## Owner's next live regression block (real MP3, empty Test Track ID)

1. **Continuous playback**: start near 0:00 and listen at least 2 minutes (the test MP3 is only 3:00 long); no PREPARING/RESTORING loop, double sound, premature silence or unexplained status change. Capture diagnosis near end.
2. **Refresh while active**: reload Yandex Music once with replacement active; expect no stuck mute, duplicate audio or stale bridge. Start explicitly if necessary and report whether it resumes automatically.
3. **Rapid controls**: while the replacement is active, next → previous → next / change songs quickly. Only exact-ID track 144530503 gets the alternative audio; all others remain original. No unexpected replacement of another song.
4. **Background tab**: switch away for 30–60 seconds, return; master and replacement remain aligned or fail open safely without doubled sound.
5. **Extension-disable watchdog**: with replacement active, turn off CELIKOM in chrome://extensions, then return to Yandex Music; original must become audible without lasting forced mute (safety watchdog, nominal 12s plus scheduling). Re-enable extension and refresh once before continuing.
6. **Manual bypass persistence**: Return Original; wait at least 10 seconds and reopen popup. It must *not* start replacing the same Track ID until explicit Start/new Track ID.
7. **Failure safety** (optional, no credentials or network tampering): Stop/Start rapidly during PREPARING or close/reopen tab; no stuck mute or loop.
8. **Expired audio URL** (developer/automated scenario): 10-minute signed-URL TTL expires and original is safely restored; new explicit Start obtains a fresh link. Do not require owner to watch for 10 minutes.

For failures ask only for developer **Copy diagnostics** JSON from the active Yandex Music tab (never include `Authorization`, `API_TEST_TOKEN`, or signed `audio_url?token=...`). Playback counter changes after explicit control/track changes are expected; unexplained same-ID restores are not.

## 2026-10-09: historical 0.4.3 emergency-disable regression — FIXED in 0.4.4

The owner passed five of six extended live stability checks in 0.4.3:
continuous playback, page refresh, rapid next/previous, 30–60s background tab, manual return-original persistence.

**Test 6 failed:** the owner switched the CELIKOM extension OFF under `chrome://extensions/` during replacement, but the alternative audio continued and original did not restore. **Do not close Stage 5, issue client beta or deem safety watchdog accepted.** Immediate user workaround is to leave the extension off and refresh the Yandex Music tab, which discards the stuck DOM audio state.

Cause indicated by code review: MAIN-world watchdog accepted `HEARTBEAT` from an injected ISOLATED-world script without confirming the actual enabled extension worker. After disabling, stale content timers can remain alive, preventing the 12s/120s watchdog from expiring. MAIN also renewed the lease on generic messages, not just heartbeats. The proposed **0.4.4** patch validates each heartbeat with `CELIKOM_CONTEXT_PING` answered by the real service worker, stops and releases after two misses and prevents generic messages from renewing the lease. Automated regression simulates worker gone while ISOLATED-world script timers still run.

Acceptance condition (must be retested by owner, not inferred from tests): on real MP3, switching the extension off restores original and stops alternate audio automatically, with no page reload or permanent mute. After re-enable and page refresh, normal exact-ID replacement still works. Also recheck 30–60s background playback so liveness polling doesn't falsely abort. Keep Stage 5 open until this passes.

## 2026-10-09: 0.4.4 owner retest — LIVE BROWSER GATE ACCEPTED

The owner clarified that the apparent pause on disabling was normal playback-control behavior, **not** a stuck mute or irrecoverable original. The original track, pause, seeking and all other controls worked correctly. The extension-disable fail-open was confirmed fixed with CELIKOM 0.4.4. The owner reports all other scenarios operate correctly: **6/6 initial smoke and 6/6 extended live tests accepted**. Previous 0.4.3 failure is historical and superseded by this retest.

**Known acceptable MVP limitation:** after disabling CELIKOM in `chrome://extensions/` and later re-enabling it, an already-open Yandex Music tab may lack the content-script controller. Pressing Start/Stop before refreshing yields a misleading "Open Yandex Music" / unsupported-page message; refresh Yandex Music once to inject scripts and reconnect. Record as UX enhancement (automatic reinjection/reconnection after re-enable); no further owner-side retesting required for this MVP gate.

**Status:** real Chrome+Hostinger MP3 integration/live playback accepted. Remaining Stage 5 work is operational and infrastructure-related; client release not authorized.

## Remaining infrastructure gates

- Repeat deployment while preserving `celikom/shared/env`, `celikom/shared/audio` and the approved mapping; current release is not automatically updated by extension build.
- Validate rollback and documented backup/restore on safe dedicated environment; avoid disrupting the first working public test.
- Health, HTTPS availability and error logging/monitoring, with secret-safe operation. Complete before formally closing Stage 5.
- PR #6 remains unmerged; don't assert later stages 6–18 complete.
