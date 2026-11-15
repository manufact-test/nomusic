# W54 — Owner diagnostic analysis: VPN recovery source reload

> **Outcome:** W54 diagnostics were received and analyzed; W157 no-kUrl continuity is now implemented and CI-verified. The single final owner-stage package `0.24.39.0` is built (artifact `14180750696`). This document remains the evidence analysis; it does not claim owner-PC audible acceptance.

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

Before the partial correction in commit `23538cab793be9d1381790d4c304db3cd4d4b417`, the host preservation predicate in `windows-companion/w23/host.cjs` called `currentDecoderPlayer(...)`. That required a player whose `kIsPlaying` was true **and** whose `sourceTrackId` came from a matching signed CDP `kUrl`. W54 reports that the owner's Yandex build does not expose `kUrl`, so the original W157 code could not set `preserveCurrentSource`; the renderer took the revalidation/reload branch. The no-`kUrl` host regression has since been added, but its fail-closed matrix remains to be completed.

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


## Дополнение W157 — результат реализации 15.11.2026

Диагностика владельца подтверждала отсутствие CDP `kUrl`; повторная диагностика не требуется. No-kUrl hold оставлен исключительно как continuity hint по ID ранее сопоставленного трека.

Реализация завершена на checkpoint `2948c38343cc8fba0027fe2c1a38b104b38a80ca`:
- Host повторно проверяет текущий Yandex ID и PLAYING/PAUSED при восстановлении.
- Renderer независимо сверяет тот же ID, playback state и наличие прежнего mapping.
- Next, Manual Stop, уничтожение декодера, logout, entitlement denial, смена/некорректность origin, unavailable state и 10-minute timeout закрывают hold.
- Hold не возобновляется после потери источника до свежего mapping текущего трека.
- Источник не маркируется подтверждённым: heartbeat `UNKNOWN`, ложного зелёного статуса нет.

Main CI `43760597485` и Windows Integration CI `43760597507` — SUCCESS. W22/W23/W60 — 151/151; адресные W157-тесты прошли. Итоговая версия для owner-stage пакета: app `0.24.39.0`, native module `0.24.30`. Старый Draft `0.24.38` не публиковать.


## W157 final package — 15.11.2026

Кодовый checkpoint `2948c38343cc8fba0027fe2c1a38b104b38a80ca` и package source commit `58eb6e6ab1c303ae6ebf0cdcff96eb3bf0dc3191` сохранены в точных backup branches.

- Main CI `43760955385` attempt 2 — SUCCESS.
- Windows Integration CI `43760955380` — SUCCESS; W22/W23/W60 151/151, все W157 no-kUrl проверки прошли.
- W20 safe installer stage `43760955394` — SUCCESS.
- App `0.24.39.0`, native module `0.24.30`.
- Artifact `14180750696`: один EXE `CELIKOM-W157-VPN-NOKURL-CONTINUITY-02439-UNSIGNED.exe`, один ZIP `CELIKOM-Windows-0.24.39.zip`, `SHA256SUMS.txt`.
- Artifact SHA-256: `b4a76570ded9cbe5640167e2f2258da9ca6a7d0f6f581ba5abbc1c90b5edf695`.
- Ссылка: https://github.com/manufact-test/nomusic/actions/runs/43760955394/artifacts/14180750696

Сборка внутренняя и unsigned; публикации или production feed нет. Старый Draft `0.24.38` запрещён к использованию. Осталась только ручная проверка владельца.


## W54 follow-up capture — 16.11.2026, app 0.24.39.0

A second owner diagnostic was supplied as Вставленный текст(20261115-213827).txt (generated 21:38:19 UTC). It identifies app 0.24.39.0, native module 0.24.30, and the same absence of decoder kUrl / exact native media URL proof.

The 15-minute window records 25 route-change events, 5 entitlement network errors/suspensions, 5 recoveries, 19 native recovery pause/resume pairs, 5 SOURCE_HELD events and 4 SOURCE_KEPT events. Crucially, it still contains one same-track failure: track 144530503 is marked NATIVE_ROUTE_RECOVERY_SOURCE_HELD at 21:35:29.013, but after recovery the renderer emits NATIVE_CURRENT_SOURCE_REVALIDATE at 21:35:31.735, NATIVE_REPLACEMENT_SOURCE_RELOAD at 21:35:31.737 and NATIVE_REPLACEMENT_SOURCE_RELOAD_OK at 21:35:32.648. A second route-change event occurred between hold and recovery.

This proves the W157 no-kUrl path is not yet fully field-accepted. The capture does not identify whether preserveCurrentSource / preserveCurrentTrackId was false, the host current-track witness failed, or renderer currentWasMapped was false. The next implementation must instrument the exact rejection reason with privacy-safe fixed codes and correct only the failed guard. Do not assume that a SOURCE_HELD event proves SOURCE_KEPT.

The same capture reports ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING, PlayerAudibleEventObserved=false, NativeDecoderUrlPropertyObserved=false and NativeMediaUrlExactMatchObserved=false. It shows no observed CORS failure, native audio 403, decoder error, CPU/memory spike or event-loop stall. Passive PLAYER_NET_* events remain non-proof of audible playback.

A separate autorun capture, Вставленный текст(20261115-212832).txt, shows WIN_AUTORUN_CONNECTED_IN_TRAY before HOST_LOADED / PLAYER_CDP_READY; the native host becomes visible only after the owner manually presses Stop and Start. Full owner field findings and ordered work are recorded in W158.