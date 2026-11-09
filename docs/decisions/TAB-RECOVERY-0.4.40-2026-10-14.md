# Automatic Yandex tab recovery — 0.4.40

Owner request: Start once; closing/reopening Yandex, background tabs and browser
memory unloading should not require popup interaction. Explicit Stop remains final.

## Findings and changes

The controller already reads persisted `enabled` on ordinary document startup;
closing a tab itself does not clear this setting. However, the worker had no tab
lifecycle recovery hooks and cached injection failures could survive navigation.
`pagehide` also irreversibly destroyed immutable MAIN/ISOLATED controllers even
when the document entered Back/Forward Cache. These are code-level gaps; they do
not establish which specific gap caused every owner-reported interruption.

- Registered synchronous MV3 listeners for tab creation, completed navigation,
  activation, restoration from discard and replacement. Only matching existing
  Yandex host permission is used; no focus/reload/navigation is forced.
- Automatic bootstrap checks persisted enabled intent twice, never writes it,
  never activates a trial or sends explicit replacement retry (which would clear
  manual original bypass). Existing entitlement/API checks remain authoritative.
- Navigation/removal clears per-document injection failures and pending handles;
  an old promise cannot cache a failure or delete the next document's pending run.
- Persisted pagehide releases original audio and replacement, retains live bridge
  and adapter identity, and suspends replacement. Pageshow rereads stored intent,
  reconnects and requests the existing verified heartbeat/access flow. A visible
  page is not permission to play. Nonpersisted pagehide still fully destroys.
- Settings revision fences delayed storage reads so Stop during reconnect wins.
- Existing 0.4.39 bounded VPN/network retries remain intact.

## Validation

214 extension tests pass locally, including tab events/Stop race, reset of cached
injection denial, complete packaged MAIN+ISOLATED cached-page resume, verified
access gating, repeated cache cycles, Stop while away, manual original bypass,
and stale settings read. Repository lint and client security gates pass.
The private configured Chrome CI and main CI results are recorded in handoff.

## Owner check

Install 0.4.40 into the same unpacked folder, reload extension and existing Yandex
page once. Start, close all Yandex tabs, open Yandex again and play an approved
track without opening the popup. Repeat with another website active/background
Yandex, Back/Forward and tab discard/restore. Finally Stop, close/reopen Yandex:
it must remain stopped. Browser audio autoplay rules still require normal user
playback; the extension connects automatically but does not start music for them.

No backend deployment, schema change, credential reset or additional Chrome
permissions. PR #6 remains open; Issue #7 remains open.

Final validation: private Chrome CI [38580994328](https://github.com/manufact-test/nomusic/actions/runs/38580994328)
and full repository CI [38581003157](https://github.com/manufact-test/nomusic/actions/runs/38581003157)
both SUCCESS for final source (workflow-only commit 3f41cbb06b9dd72a46e54415f8d5ef4b0ca2c619).
Initial full CI failed before checkout on ECR MySQL download data limit; rerun
38580604460 passed. This was CI infrastructure, not an application test failure.
Final full ZIP SHA-256: `35fc3ec2d364c357f201f2305493556bc4132ce3b082e051e9bda7c94fdecd81`.
214 tests pass including a five-minute frozen-cache watchdog interval. Physical
owner close/reopen/Back/Forward/discard checks remain pending.
