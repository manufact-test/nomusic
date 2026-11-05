# CELIKOM Test.38: stale Media3 controller must fail open

Status 2026-11-05: candidate source and deterministic guard test; physical HONOR acoustic and switching verdict **pending**. Test.37 owner-rejected due to stuck source playback. Keep Test.33 as the only owner-approved rollback.

## Physical evidence

Owner supplied `CELIKOM-combined-20261105-142956.txt` and `SVID_20261105_142918_1.mp4`.

- Current run `0.3.85-test.37`, start 14:29:05 MSK; initial visible Yandex track was **Шёлковая простынь**. During the recorded screen video, Yandex player shows timeline scrub and switches to **Толер** and **Биг сити лайф**, whereas CELIKOM continues playing and reporting **Шёлковая простынь**.
- At 20.652s, 25.366s, 35.645s, 42.984s, Android emitted `OPEN_AUDIO_EFFECT_CONTROL_SESSION` for trusted session 225. These are **unverified-origin** broadcasts, not authority to bind or mute a new track.
- Media3 remained connected and `isPlaying=true` with *alias 255*, reporting monotonically advancing old song positions; no `source_discontinuity`, `source_media_item_transition` or other Media3 `onEvents` were recorded for the current run. First heartbeat at 15.127s showed event age 15.089s; at 45.289s age 45.252s.
- No `audio_effect_session_parked` or `audio_effect_session_reused` was emitted in the current run. The failure involves a stale playback controller, not proven reuse of a parked effect. The Test.37 effect-lifetime experiment is revoked anyway.

## Change relative to Test.33

- AudioOwnership and ReplacementEngine audio paths restored **byte-for-byte to owner-approved Test.33 source**. No parked/reused DSP, no changes to 160ms join, cached seek/ACK, duration safety, audio or account permissions.
- `SourceSessionRecheck` treats a repeated **same trusted session ID** `OPEN_AUDIO_EFFECT_CONTROL_SESSION` as a *revocation/recheck hint only*, and only if replacement is actively audible, Media3 supplied no events for at least 3s, and a 12s cooldown allows it.
- First silence and release the wrong/old decoder, reset and release the source effect via existing AudioOwnership, keep automatic replacement armed; release the stale Media3 binder and make a fresh read-only connection.
- Quarantine the old alias/cursor. A new controller may resume substitution only after it reports **different track ID**, a materially different real cursor (seek), or a corroborated current-controller seek event. If new evidence never arrives, Yandex original remains audible and the old replacement cannot continue indefinitely.
- No notification listener, Accessibility, microphone, account hooks, media transport commands, root or modified Yandex required.

## Validation and safeguards

- `Test38SourceSessionRecheck`: 20 pure assertions; follows the 20.652/25.366/35.645s incident timeline, stale ticker, new alias, seek, duplicate OPEN and cooldown.
- `check_0385_seek_baseline.py` PASS; Test.33 seek source untouched. `check_test_app_build_contract.py` PASS; separate `pro.celikom.nativeprobe.test`, `CELIKOM Test` app, original signing and stable OTA exclusion.
- Full Android compile, all host regressions, signed APK, CI provenance and phone outcome **pending** until GitHub Actions completes.
- Test.33 pinned baseline functional source `53d94d66a32b332b62848e0895285d81dda226e9`, backup `backup/android-0385-test33-owner-accepted-20261105`, library original APK `libfile_0924722c86908191bef31db36cfcf0ed`.
