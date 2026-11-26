# Extension 0.4.86 — paused background bridge retention
26 November 2026. Owner-only candidate; public promotion is NOT authorized.

## State / rollback
Owner had designated 0.4.85 as the current testing reference, not a customer stable release, and then reported intermittent issues during a longer WITHOUT-VPN listening run. Exact pre-change main is 187c57eaf45f4125ae85a93874acf1304044b104. 85 ZIP stays available as rollback: Library libfile_defefd80d12c8191bda63f2ec078842f, SHA256 0e3af87b830b980ef6427ebf5492adbf0e378debcaa52c10b594e47d7bd9b63c. Baseline provenance remains accepted 78, not 73. Do not bring back withdrawn 79–84 playback experiments.

## Evidence
Input: Вставленный текст(20261126-085542).txt, version 0.4.85.
The retained history contains four bridge-unhealthy teardowns on the SAME paused track106618973, with exactly ~120000ms spacing. Pause position remains 2.437s. The same track is repeatedly resolved/prepared again at that position, despite no actual track change. At visible return the bridge is remounted, and resuming at 2.437s synchronously engages a fresh admission mute with NO replacement element. Re-preparation takes881ms, followed by a decoder seek; a retained snapshot still has replacement3.302s versus native4.126s. This supports the owner's report of roughly two seconds of silence on resume. It is not evidence that the stored native position was lost.

Recorded API requests succeed (roughly70–109ms in the retained network window); final audio stream is complete and readyState4. This run does not support blaming VPN. Timings of every audio body transfer and CPU/GPU samples are absent, so do not claim all other symptoms or external routing have been ruled out.

The retained restore history also contains replacement-ended and one Replacement ended before original at natural song boundaries. Their presence alone is NOT proof of network drops. They are not corrected by this bridge change, and the diagnostic does not capture every earlier symptom.

## Root cause and bounded correction
The isolated PlayerBridge considered a connection stale after4 seconds in ALL visibility states. MAIN already used a120-second hidden watchdog versus12 seconds visible. Browser hidden-page timer batching to minute cadence therefore caused isolated reconnect/teardown loops although the hidden MAIN lease had not expired.

PlayerBridge now uses the SAME120-second hidden bound and retains its original4-second visible health window. On return from a genuinely hidden interval, allow one4-second verified-worker response window, capped by the pre-existing lastSeenAt+120s deadline. Duplicate visible notifications do not renew it. MAIN similarly uses one visible12-second response window capped by its existing lastHeartbeatAt+120s bound, so it does not retroactively apply the visible timeout to the elapsed hidden interval. Only the existing worker-confirmed heartbeat refreshes the lease; unanswered checks still expire. No new polling loop is added; visibility listener is removed on destroy.

This is liveness bookkeeping, not a longer song preparation delay. Authorization/trial/entitlement deadlines, signed grants, Stop, manual-original, disabled extension and expired MAIN watchdog behavior are unchanged.

A second narrow correction confines synchronous first-play admission to the actual intro (<=0.25s), matching the existing intro hold. A resumed mid-song original without a prepared replacement stays audible while normal preparation runs; resuming at2.437s cannot be treated as an intro and muted solely for that reservation. Ordinary ready-asset activation remains under the existing guard and sync rules. This does NOT introduce84's unbuffered-yield/token-renewal mechanism. Replacement controller, stream player, sync engine, adapter, API/auth implementation and early selected-track warm-up are byte-unchanged from85.

## Verification
400/400 extension tests PASS; manifest validation PASS; security build gate PASS (67 packaged client files). Includes:
- Packaged MAIN+ISOLATED eight-minute paused/background scenario with minute-spaced callbacks: SAME decoder, SAME activation count, ZERO restores, retained2.437s position and successful resume.
- Hidden bridge minute-spaced verified ticks do not trigger INIT loops.
- Visible4-second and hidden120-second expiry remain effective.
- Returning visible grace waits for verification, cannot be renewed by duplicate events or extend the hidden deadline.
- MAIN foreground handover is independently bounded and still restores original without a verified reply.
- Mid-song resume without a replacement cannot synchronously apply intro mute.
- Original first-play intro mute/timeout tests now explicitly start at0.1s instead of their former fake9-second default; separate mid-song physical-mute regression covers the intentionally changed behavior.
Existing My Wave, pause/seek, Stop, disabled/hung worker, support/upload and access suites pass. No real Chrome/Brave listening run was executed here; these are packaged VM/clock/behavior tests, not proof every audible problem is fixed.

## Candidate
celikom-extension-0.4.86.zip;2,493,810bytes.
SHA256 c3a95cc15ad296e149ea3d618b8dc74ea56a42c7603ee0ce54a0480981c035f2.
Owner delivery Library libfile_a1a18de43f04819181e286d403e2db38.
No backend, Windows, Android, production, promotion manifest or paid service changes. Existing CI may independently build/spool; its completion is not fabricated or a reason to withhold the locally verified archive.

Owner check: update SAME unpacked folder, Reload extension AND Yandex; verify86. Play, pause, leave Yandex in the background for several minutes, return and resume. Also continue normal background listening and send a fresh diagnostic after a symptom. Keep85 rollback; do not mark86 public stable before owner acceptance.
