# W158 — owner field regression: VPN continuity, recovery UI and Windows autorun

Date: 16 November 2026  
Repository: manufact-test/nomusic  
Only working branch: main  
Product: the existing single CELIKOM Windows application

## Current source and rollback

- Current main HEAD before this documentation update: eec7561aedcc1e33c835d94a75ff0d40474a5d48 (documentation-only W157 handoff commit).
- Application source checkpoint: 2948c38343cc8fba0027fe2c1a38b104b38a80ca.
- Source commit used for the existing owner-stage package: 58eb6e6ab1c303ae6ebf0cdcff96eb3bf0dc3191.
- Existing owner-stage app: 0.24.39.0; native module: 0.24.30.
- Existing private artifact: 14180750696, workflow 43760955394. It predates the new owner findings and is not accepted as the final fix.
- Exact pre-W158 backup: backup/windows-main-pre-w158-owner-vpn-autorun-ui-20261116 @ eec7561aedcc1e33c835d94a75ff0d40474a5d48.
- W157 Main CI 43760955385 and Windows Integration CI 43760955380 were SUCCESS on the previous source. This does not override the new owner-PC failures below.

Do not create another installer or ZIP until every W158 item is fixed, targeted tests pass and both required CI workflows are green. Deliver one consolidated build only.

## Owner evidence received

Files supplied with the 16 November owner report:

- Вставленный текст(20261115-213827).txt — W54 diagnostics generated 2026-11-15 21:38:19 UTC, app 0.24.39.0 / native module 0.24.30.
- Вставленный текст(20261115-212832).txt — W54 diagnostics generated 2026-11-15 21:28:27 UTC; contains the Windows autorun → manual Stop/Start sequence.
- Screenshots 1.png, 2.png and 3.png — startup/waiting state, transient VPN-disconnect state, and post-recovery state.

The owner reports that CELIKOM replacement audio often continues playing through VPN changes. In some runs there is no audible interruption at all. In other runs, when CELIKOM changes its displayed state and reports recovery, an unnecessary source transition produces a click/pop. Do not treat a UI/server disconnect as proof that the current audio source stopped.

### Screenshot-by-screenshot notes

1. The first image shows the player/track metadata (Ау — 10AGE, Ramil'), but the header says “Ожидаем” and the source line says “Источник текущего трека не подтверждён”. Keep that neutral unless the exact source can be proven; do not infer active replacement from the song title alone.
2. The second image shows the connection-loss/recovery state. Start is visually enabled/green even though the UI says the connection is unavailable and automatic recovery is running. The message says “Нет связи. Подмена приостановлена; повторим проверку автоматически.” This is the wrong action state and potentially misleading audio wording.
3. The third image shows “Сервис включён” plus the green “Версия песни CELIKOM доступна для подмены”. The latter is the approved version-presence result, not proof that the current Yandex decoder is playing that version. Keep service-enabled and replacement-active separate.


## Diagnostic findings

### 1. VPN route recovery is still not clean

The 15-minute event window in the 21:38:19 UTC capture contains:

| Event | Count |
|---|---:|
| ACTIVE_ENTITLEMENT_ROUTE_CHANGED | 25 |
| ACTIVE_ENTITLEMENT_NETWORK_ERROR | 5 |
| ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED | 5 |
| ACTIVE_ENTITLEMENT_RECOVERED | 5 |
| ACTIVE_ENTITLEMENT_TIMEOUT | 2 |
| NATIVE_ROUTE_RECOVERY_PAUSED | 19 |
| NATIVE_ROUTE_RECOVERY_RESUMED | 19 |
| NATIVE_ROUTE_RECOVERY_SOURCE_HELD | 5 |
| NATIVE_ROUTE_RECOVERY_SOURCE_KEPT | 4 |
| NATIVE_CURRENT_SOURCE_REVALIDATE | 1 |
| NATIVE_REPLACEMENT_SOURCE_RELOAD | 1 |
| NATIVE_REPLACEMENT_SOURCE_RELOAD_OK | 1 |
| START_ENABLED | 7 |
| STOP_DISABLED | 6 |

A concrete same-track failure remains:

- 21:35:27.816 — ACTIVE_ENTITLEMENT_ROUTE_CHANGED.
- 21:35:28.591 — ACTIVE_ENTITLEMENT_NETWORK_ERROR.
- 21:35:28.597 — ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED.
- 21:35:29.012 — NATIVE_ROUTE_RECOVERY_PAUSED.
- 21:35:29.013 — NATIVE_ROUTE_RECOVERY_SOURCE_HELD for track 144530503.
- 21:35:29.808 — another ACTIVE_ENTITLEMENT_ROUTE_CHANGED.
- 21:35:30.690 — ACTIVE_ENTITLEMENT_RECOVERED.
- 21:35:30.825 — STATE_ENABLED.
- 21:35:31.735 — NATIVE_CURRENT_SOURCE_REVALIDATE for the same track 144530503.
- 21:35:31.737 — NATIVE_REPLACEMENT_SOURCE_RELOAD for the same track.
- 21:35:32.648 — NATIVE_REPLACEMENT_SOURCE_RELOAD_OK.

This is direct evidence that a source was marked HELD, but the recovery path still revalidated and reloaded that same track. The log does not identify which guard rejected the no-kUrl hold. Do not guess. Inspect why SOURCE_KEPT was not emitted: in particular preserveCurrentSource / preserveCurrentTrackId, the host's current-track witness, renderer currentWasMapped, route-burst transitions and recovery state ordering. Add privacy-safe reason codes for a rejected hold if the existing diagnostics cannot distinguish those cases. Never log URLs, tokens, cookies or raw response bodies.

The capture also contains 25 route-change events and 19 pause/resume pairs. Determine why repeated route signals repeatedly toggle recovery state, while preserving the fast entitlement recheck. Coalesce redundant route transitions where safe; never discard the final route signal or grant access offline.

### 2. Autorun marks the app connected before the native player is ready

The 21:28:27 UTC capture contains this exact order:

- 21:17:37.413 — GUI_STARTED.
- 21:17:37.506 — BRIDGE_STARTED.
- 21:17:53.590 — WIN_AUTORUN_MODULE_REPAIR_REQUEST.
- 21:18:03.730 — WIN_AUTORUN_MODULE_REPAIR_OK.
- 21:18:05.253 — START_ENABLED.
- 21:18:05.259 — WIN_AUTORUN_CONNECTED_IN_TRAY.
- 21:19:23.556 — STOP_DISABLED.
- 21:19:23.562 — ACTIVE_ENTITLEMENT_MANUAL_STOP.
- 21:19:32.309 — START_ENABLED.
- Only after this manual Start: HOST_LOADED, BUNDLE_PRESENT, WEB_CONTENTS_PRESENT, APPROVED_VIEW, PLAYER_CDP_READY and PLAYER_NET_READY.

The owner reports the matching behavior after Windows reboot: CELIKOM appears already enabled, but the player is not actually connected. Start is unavailable, so the owner has to press Stop and then Start to make the native player initialize.

Code inspection confirms the risk: MainWindow.Autostart.cs calls _bridge.SetEnabled(true) and immediately records WIN_AUTORUN_CONNECTED_IN_TRAY after entitlement checks; it does not wait for a real native-host/player heartbeat. PlaybackStartGate and UpdateSafe treat bridge Enabled as the main Start gate. This can make a desired background resume look like a completed connection before Yandex has attached the native host.

Required behavior:

- Keep saved user intent, local CELIKOM process/bridge readiness, native-host attachment and current Yandex player readiness as separate states.
- A background autorun must not claim “connected” or present a completed active service before the native host/player handshake is actually observed.
- If Yandex is not open yet, preserve the user's saved Start intent and wait. When the owner opens Yandex later, attach automatically without Stop/Start.
- If Yandex is already open at Windows sign-in, attach automatically and report connected only after the real handshake/heartbeat.
- CELIKOM must not launch Yandex automatically during Windows sign-in. The owner opens Yandex.
- Explicit Stop cancels the saved resume intent and must remain authoritative across reboot.
- Keep the existing per-user/no-UAC startup behavior and StartupApproved choice handling. This is a targeted lifecycle correction, not a redesign of Windows autostart.

### 3. Recovery controls and messages are inconsistent

The second screenshot shows a green/enabled Start button while the app says the connection is unavailable and automatic recovery is pending.

Code inspection confirms why:

- RefreshCompactAccessAsync sets _resumeAfterNetworkFailure=true and _bridge.SetEnabled(false) after a transient entitlement/network failure.
- UpdateSafe passes _bridge.Enabled to PlaybackStartGate, but does not pass _resumeAfterNetworkFailure.
- PlaybackStartGate.CanAcceptStart has no recovery-pending argument. With bridge Enabled=false during recovery, Start becomes available even though CELIKOM is already recovering automatically.
- The Stop button is separately allowed while _resumeAfterNetworkFailure is true, which is the desired user escape hatch.

Required behavior:

- Start must be disabled while automatic recovery is pending. The Start event handler and visual button must use the same gate.
- Stop remains available and cancels automatic recovery/saved playback intent.
- The owner must never need to click Stop then Start to recover from VPN changes.
- Replace “Нет связи. Подмена приостановлена; повторим проверку автоматически.” when the current source is being held with an accurate short message such as “Восстанавливаем связь. Текущий звук не переключаем.”
- Do not say that playback/source is paused unless it is actually paused. Server entitlement being temporarily unavailable means no new authorization is granted; it does not by itself prove that an already-loaded current source stopped.

### 4. Current-track/version status is too long and can imply the wrong thing

The third screenshot shows “Сервис включён” and the green line “Версия песни CELIKOM доступна для подмены”. The latter is currently selected from the server presence value “approved”; it proves that a CELIKOM version is available for that track, not that the Yandex player is currently playing it.

The browser extension's concise active label is “Подмена активна”. Reuse the concise vocabulary, but do not weaken Windows source-proof rules:

- “Подмена активна” may be shown only when the existing Windows exact current-source verification condition is satisfied.
- A server presence result of approved must not be rendered as proof that the replacement is already playing. If shown, use a short availability-only label such as “Версия CELIKOM доступна” and a neutral/secondary color.
- When the source is not verified, keep a neutral “Источник текущего трека не подтверждён”. Do not turn an approved upload/presence result, cached mapping, network bytes or a no-kUrl continuity hold into a green active-playback state.
- “Сервис включён” describes the service toggle only; it must not be conflated with “Подмена активна”.
- Keep the existing compact layout. No redesign or new screens.

### 5. Diagnostic limits

The 21:38:19 capture reports:

- ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING.
- PlayerAudibleEventObserved=false.
- NativeDecoderPropertiesObserved=true.
- NativeDecoderUrlPropertyObserved=false.
- NativeMediaUrlExactMatchObserved=false.
- NativeMediaUrlSignedFieldsIntactObserved=true.
- No observed CORS failure, native audio 403, decoder error, Electron event-loop stall, high memory or high CPU.

Passive PLAYER_NET_* and resource timing events do not prove decoded or audible playback. The capture proves the internal source-hold/revalidate/reload sequence, not the waveform or the owner's pop. The owner's listening report is the evidence for the audible symptom. Do not claim audible continuity from CI or these logs.

## Strict execution order — do not skip or combine tasks

### W158.1 — Repair the autorun false-connected lifecycle

Inspect only the existing startup path and its tests: MainWindow.Autostart.cs, MainWindow.cs, BridgeServer.cs, YandexProcessLifecycleTracker.cs and relevant W15 tests.

Correct the premature “connected in tray” state. Preserve the saved intent independently from actual native/player readiness. Automatically attach when Yandex is already running or is opened later. Do not launch Yandex from Windows startup. Make explicit Stop cancel the pending intent. Add focused tests for Yandex already running, Yandex absent then opened, delayed host handshake, module repair, and Stop before Yandex appears.

### W158.2 — Close the remaining no-kUrl VPN source-hold gap

Inspect the exact host/renderer recovery path in windows-companion/w23/host.cjs, renderer-entry.mjs and the W23 tests. Explain and fix why track 144530503 was HELD and then revalidated/reloaded. The same already-mapped current track must remain untouched when it is still the current PLAYING/PAUSED track and the same-origin route is being restored.

Do not suppress legitimate recovery when the source/player actually disappeared. Next/current-track change, selected-player destruction, manual Stop, logout, entitlement denial, API-origin change, invalid/unavailable state and timeout must remain fail-closed. If a real source loss is detected, use the existing bounded recovery for the actual current track only. Keep the fast entitlement reconnect.

### W158.3 — Correct recovery button/state behavior

Add recovery-pending to the shared Start eligibility rule used by both UpdateSafe and StartAction. Start is disabled during automatic recovery; Stop remains enabled. A manual Stop cancels recovery. No user action is required to resume after a transient route failure and fresh positive server authorization.

### W158.4 — Correct only the confirmed text/color states

Use the concise extension vocabulary. Separate service enabled, server connectivity, Yandex player readiness, current playback state, and source verification. Keep “Подмена активна” strictly behind the existing exact Windows verification. Make availability-only wording short and neutral. Remove the false “подмена приостановлена” wording when the current source is being held. Do not redesign the popup.

### W158.5 — Focused regressions and final verification

Test the combined lifecycle in this order:

1. Windows sign-in with Yandex already open; then Windows sign-in with Yandex closed and opened later. No Stop/Start workaround and no automatic Yandex launch.
2. Explicit Stop before Yandex opens; no automatic resume afterward.
3. VPN A→B while an already-mapped CELIKOM replacement is playing. Same current track must not be reloaded if its source is retained.
4. VPN A→B while an original track is playing; no false active-replacement status.
5. Next/current-track change during recovery; the old track's hold must never transfer to the new track.
6. Actual player/source loss; only the bounded recovery for the actual current track is allowed.
7. Manual Stop, logout, denial and origin change; no recovery hold may survive.
8. Start/Stop buttons, recovery copy, short labels and colors must match the actual state.

Run only the relevant focused W15/W23 suites, then both required Main CI and Windows Integration CI. Do not repeat broad unrelated audits. After all W158 items and both CI workflows pass, update the documentation and prepare exactly one consolidated Windows owner build. No intermediate EXE, ZIP or installer.

## Hard constraints

- Work only in manufact-test/nomusic on main.
- Preserve the single Windows app and existing architecture. No second player.
- Do not touch Android, browser extension implementation, shared backend/API/DB or Yandex original files.
- Do not reopen updater/P-256, W155/W156, release trust, or unrelated startup/installer work.
- Keep per-user startup, no UAC/elevation, and no automatic Yandex launch.
- Do not weaken entitlement checks or source-proof safeguards.
- Do not infer audible playback from passive network events, a mapping, or the no-kUrl hold.
- No UI redesign, broad refactor, speculative changes, unrelated tests or intermediate builds.
- Work in large blocks and complete each numbered task before moving to the next. Do not stop for small progress reports; stop only for real owner input/manual acceptance or when the one final build is ready.

## Definition of done

- After reboot, CELIKOM no longer reports a false completed connection. It automatically attaches when Yandex is available, without Stop/Start.
- During transient VPN changes, an already-playing unchanged mapped source is not needlessly reloaded. Real source loss still has safe bounded recovery.
- Start is disabled during automatic recovery; Stop cancels it.
- UI wording and color distinguish service state, server connection, player readiness, track-version availability and verified active replacement.
- Focused tests and both CI workflows pass.
- Exactly one consolidated new Windows owner build is delivered after the fixes; no intermediate packages.

## W158 engineering result — 16 November 2026

**Status: application code + both required CI workflows GREEN. Owner-PC sound and UI acceptance NOT YET DONE.**

- Exact pre-W158 rollback: `backup/windows-main-pre-w158-owner-vpn-autorun-ui-20261116` @ `eec7561aedcc1e33c835d94a75ff0d40474a5d48`. No architecture change, no Yandex vendor file change, no Android/extension/backend/updater/P-256 edits.
- Application fix commit: `3f6affc242ef570120250d2e20eec791338f2ef9`. CI-lint-only existing documentation newline fix: `7492158509f97564bcb45f5a892cb9b6e529a4d0`. New reviewed owner package version: **CELIKOM Windows 0.24.40.0 / native 0.24.31** (previous 0.24.39.0 / 0.24.30 superseded for W158 acceptance).
- **W158.1:** The saved, previously owner-approved Start preference remains independent of live native readiness. Quiet Windows autorun arms the local bridge but reports WAITING, not CONNECTED. CONNECTED_IN_TRAY is emitted only on fresh native/player heartbeat; no Yandex process is started. Opening Yandex later attaches automatically; Stop clears pending state and saved Start. Original account/session/module/entitlement controls remain intact.
- **W158.2:** The source can have been mapped in the CURRENT Yandex renderer while the host's last status was only NATIVE_CONNECTED/ORIGINAL; W157 previously missed this host-side continuity witness. Furthermore, an in-flight older heartbeat could clear `networkRecoveryPending` before the resumed renderer received its state, causing the next OFF→ON transition to REVALIDATE/RELOAD after SOURCE_HELD. W158 adds a read-only exact-current mapped PLAYING/PAUSED witness, coalesces duplicate route hold markers without losing the final server recheck, and requires an echoed matching recovery epoch after successful renderer-state delivery before releasing the route hold. The existing source-proof rule is unchanged: a mapped/no-kUrl hold is UNKNOWN, never ACTIVE_REPLACEMENT. Next, actual source/player loss, Stop, logout, denial, origin change and 10-minute timeout remain fail-closed.
- **W158.3:** The shared Start eligibility gate blocks clicks and button highlight for automatic network recovery while leaving Stop available. Explicit Stop cancels auto resume.
- **W158.4:** Recovery copy no longer asserts that retained sound is paused. Active label is the concise `Подмена активна` only after exact current Windows decoder proof and PLAYING; mere version availability is `Версия CELIKOM доступна` in a neutral color. Missing Yandex heartbeat shows waiting instead of completed connection.
- **W158.5:** Focused W15 tests cover true native autorun handshake, saved intent/Stop, recovery button gate, burst coalescing and generation-gated route acknowledgement. W23 tests cover exact owner track `144530503` without kUrl, mapped renderer/lagged host status, PAUSED preservation, reload suppression, rejected-hold reason, and previously existing Next/player-loss/denial/Stop/origin/timeout guards. Both CI workflows checked the committed application source: **Main CI [43769234697](https://github.com/manufact-test/nomusic/actions/runs/43769234697) SUCCESS** and **Windows integration CI [43769234693](https://github.com/manufact-test/nomusic/actions/runs/43769234693) SUCCESS**. Prior first CI attempt stopped at five pre-existing missing final newlines; those were fixed without changing documentation meaning.

**Exactly one W158 owner candidate requested after both CI passed:** `CELIKOM-W158-VPN-AUTORUN-SOURCE-UI-02440-UNSIGNED.exe`, plus `CELIKOM-Windows-0.24.40.zip` containing that exact EXE and `SHA256SUMS.txt`, retained privately as a GitHub Actions W20 artifact. This is not a production signed release, deployment, update-feed change or audible acceptance.

**Owner checks only:** (1) reboot with Yandex initially closed, then manually open Yandex and confirm CELIKOM connects without Stop/Start; also test Yandex already open; (2) switch VPN during unchanged mapped playback and PAUSED, listen for pop/click, and test Next; (3) confirm Start disabled/Stop enabled during automatic recovery; (4) inspect neutral availability vs exact green active source and Stop-before-Yandex/after-VPN behavior. Owner diagnostics were already received; ask for new ones only if a new field failure occurs. Until tested, W158 is engineering-complete, not owner-accepted.

## W159 owner follow-up — 16 November 2026

The owner accepted the W158 VPN audio-continuity behavior in manual listening: the already-playing CELIKOM version continues through VPN route recovery without an audible pop or unnecessary source restart. W54 diagnostics record the same-track source hold/keep and entitlement recovery sequence. The diagnostics do **not** independently prove audible output; see `docs/windows/W159-MAPPED-TRACK-STATUS-20261116.md`.

A remaining presentation regression was found: after VPN recovery the compact popup showed `Версия CELIKOM доступна`, but after Next on another mapped track it reverted to `Источник текущего трека не подтверждён` and `Ожидаем подтверждения`. W159 corrects this copy consistently in compact and main UI. Exact decoder proof remains the only route to `Подмена активна` / accent color. VPN, native playback and Yandex integration are unchanged.
 
W159 owner-review package result (16 November 2026): one successful W20 stage run [43828713363](https://github.com/manufact-test/nomusic/actions/runs/43828713363), artifact `14208040930`, version **0.24.41.0 / native 0.24.31**. The artifact contains the unsigned installer, a ZIP containing that exact same installer, and SHA256 checksums. No production release or deployment.
