# W54 — Owner diagnostic analysis: VPN recovery source reload

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Scope: CELIKOM Windows owner diagnostics only. This is an evidence summary, not a claim of audible playback proof.

## Files found

The owner had already uploaded these files to ChatGPT Library. They were omitted from the previous GitHub handoff, which incorrectly said diagnostics had not been supplied.

- `Вставленный текст(20261115-181400).txt` — generated UTC 18:13:51, 48,352 bytes.
- `Вставленный текст(20261115-181616).txt` — generated UTC 18:16:12, 65,778 bytes; contains the VPN route test.
- `Вставленный текст(20261115-181902).txt` — duplicate of the second capture.

Both unique captures identify:
- App version: `0.24.38.0`.
- Native module: `0.24.29`, matches app.
- Code baseline: `W54_GAIN_VARIANT_AND_W53_PERFORMANCE_EXPORT_SAFE`.
- Yandex version: unknown.
- Diagnostic scope: last 15 minutes.

## Summary flags

The second capture reports:
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`.
- `PlayerAudibleEventObserved=false`.
- `NativeDecoderPropertiesObserved=true`.
- `NativeDecoderUrlPropertyObserved=false`.
- `NativeMediaUrlExactMatchObserved=false`.
- Signed URL fields remained intact; no query mismatch was observed.
- No native audio 403, CORS failure, decoder error, Electron event-loop stall, high memory or high CPU was observed.
- The diagnostic explicitly warns that passive `PLAYER_NET_*` events can represent preloading and do not prove decoded or audible playback.

## VPN sequence directly visible in the second capture

### First route interruption — track 106040459

- 18:14:44.144 — `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED`.
- 18:14:44.579 — `NATIVE_ROUTE_RECOVERY_SOURCE_HELD`.
- 18:14:46.231 — `ACTIVE_ENTITLEMENT_RECOVERED`.
- 18:14:47.363 — `NATIVE_CURRENT_SOURCE_REVALIDATE`.
- 18:14:47.364 — `NATIVE_REPLACEMENT_SOURCE_RELOAD`.
- 18:14:48.287 — `NATIVE_REPLACEMENT_SOURCE_RELOAD_OK`.

### Second route interruption — track 144530503

- 18:15:14.643 — `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED`.
- 18:15:15.250 — `NATIVE_ROUTE_RECOVERY_SOURCE_HELD`.
- 18:15:19.745 — `ACTIVE_ENTITLEMENT_RECOVERED`.
- 18:15:20.848 — `NATIVE_CURRENT_SOURCE_REVALIDATE`.
- 18:15:20.850 — `NATIVE_REPLACEMENT_SOURCE_RELOAD`.
- 18:15:20.856 — `NATIVE_REPLACEMENT_SOURCE_RELOAD_OK`.

### Third route interruption — same track 144530503

- 18:15:30.634 — `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED`.
- 18:15:31.029 — `NATIVE_ROUTE_RECOVERY_SOURCE_HELD`.
- 18:15:42.781 — `ACTIVE_ENTITLEMENT_RECOVERED`.
- 18:15:43.103 — `NATIVE_CURRENT_SOURCE_REVALIDATE`.
- 18:15:43.105 — `NATIVE_REPLACEMENT_SOURCE_RELOAD`.
- 18:15:44.028 — `NATIVE_REPLACEMENT_SOURCE_RELOAD_OK`.

## Interpretation and code coverage gap

The companion correctly marks the current source as held during the transient network suspension. On re-enable, however, it performs a current-source revalidation and replacement reload for the same current track. This matches the owner's report of an unnecessary post-VPN source transition.

The current host preservation predicate in `windows-companion/w23/host.cjs` calls `currentDecoderPlayer(...)`. That function requires a player whose `kIsPlaying` is true **and** whose `sourceTrackId` was populated by a matching signed CDP `kUrl`. W54 explicitly reports that the Yandex build does not expose `kUrl`. As a result, `preserveCurrentSource` is not set for this owner configuration, and the renderer takes the revalidation/reload branch. The existing W157 regression tests only cover the `kUrl`-available case.

This means the W157 exact-decoder path is valid for builds that expose the property, but it does **not** close the actual W54 case. Do not report VPN continuity as complete and do not build the final package yet.

## Implementation status after W54 review

A first no-`kUrl` continuity path is now implemented on source commit `23538cab793be9d1381790d4c304db3cd4d4b417`:

- Host captures a short-lived hold containing only the prior current-track ID when same-origin transient network recovery begins and the prior host status was `NATIVE_MAPPING_ACCEPTED` or `NATIVE_SOURCE_VERIFIED`.
- Host does not infer exact source/decoder identity from this hold.
- Renderer independently requires that the actual current Yandex track ID equals the held ID and that `adapter.hasMappedTrack(currentTrackId)` remains true before suppressing current-source revalidation/reload.
- A focused host test passes without emitting a CDP `kUrl` property.
- Main CI `43756267555` and Windows integration CI `43756267579` both pass. W23 native-host is `143/143`; W22/W23/W60 is `360/360`.

This is only a partial fix. It proves the host-side no-`kUrl` hint and the renderer's mapped-track gate in the current test suite, but does not yet establish the complete fail-closed matrix or audible continuity on the owner's PC.

## Remaining narrow work

Continue only the no-`kUrl` VPN recovery task:

- The host may preserve only the previous current track identity and the fact that the track had reached the mapped state; it must not convert this into exact source proof.
- The renderer must independently confirm that the actual current Yandex track ID is still the same and that it was already mapped before the transient suspension.
- Preserve the current source without reloading it while the route is being restored. Keep source status UNKNOWN/neutral unless exact decoder proof exists.
- Track change, selected-player destruction, manual Stop, logout, entitlement denial and API-origin change must not inherit the hold.
- If actual source/player loss is positively detected, retain the existing bounded current-track recovery behavior.
- Add no-`kUrl`-specific tests for Next/current-track change during the outage; manual Stop and selected-player destruction; logout; entitlement denial; API-origin change; invalid/unavailable state; recovery timeout; and bounded recovery when actual current source/player loss is detected. Existing general tests do not replace explicit coverage of this new hold path.
- Confirm a changed current track never inherits the old held ID, and the UI/source status remains UNKNOWN/neutral without exact signed decoder proof.
- If a test exposes a defect, make only that targeted correction. Then rerun both required Windows CI workflows.

## Evidence limits

W54 confirms the internal event sequence of source hold followed by revalidation/reload. It does not prove the audible waveform or the owner's reported pop: the diagnostic explicitly has no replacement-audible proof and no `PLAYER_AUDIO_AUDIBLE` event. The owner's listening observation remains the evidence for the audible symptom.

W54 is a VPN diagnostic, not a separate test of fully closing Yandex Music. The Yandex lifecycle fix remains subject to owner-PC confirmation.

No new installer/package was built from this diagnostic review. The unpublished 0.24.38 Draft must not be published or sent as the W157 fix.
