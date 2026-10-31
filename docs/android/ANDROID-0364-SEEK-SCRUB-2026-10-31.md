# CELIKOM Android 0.3.64 — HONOR finger-scrub regression checkpoint

Source: owner diagnostic `CELIKOM-combined-20261031-120344.txt`, **latest segment only**, `run_start.version=0.3.63` at 2026-10-31 12:01:49 +03. Earlier 0.3.61 and 0.3.62 segments are historical and must not be mistaken for this session.

## Observed behavior and limits

- There are 26 same-alias explicit source discontinuities (finger seeks) in the 0.3.63 segment. Each was followed by decoder alignment: previously every seek immediately silenced CELIKOM, restored the old Yandex audio, sought the retained secondary decoder, then handed audio back. This creates a perceptible second switch/pitch/volume bump even when the seek succeeded.
- Individual `replacement_seek_complete` reports reach 591ms; one seek beginning at elapsed 5045ms was followed by prolonged native Yandex `BUFFERING`, and the source did not resume until around 8.4s. The journal captures command states, not actual microphone/Bluetooth output. It cannot establish acoustic waveform, or prove that a particular finger movement was ignored by Android.
- No `fade_failed` occurred in the 0.3.63 segment, supporting the 0.3.62 final-ramp-state fix. New-song 40ms overlap is much improved according to the owner, though still detectable on bright intros.

## 0.3.64 change

- Fast explicit same-track user seek from exclusively audible replacement: silence the decoder and `seekTo`, **retain Yandex source attenuation** for a 260ms bounded window. If the decoder seek and verified clock gate succeed within the window, the same CELIKOM decoder becomes audible directly with no return to Yandex. During the window there may be a brief seek gap; no hardware silence guarantee is claimed.
- If seek/stream/clock stalls, restore the original at the 260ms deadline (or safely release the effect if the source is now paused/buffering). Keep the 2s/12s seek budgets, two-correction cap, clock/drift authority, fail-open behavior, and track/account cancellation unchanged.
- Multiple scrubs while a seek is in flight are serialized. A stale callback cannot reauthorize old audio. An unexpired hold stays bounded to the **first** seek and is not reset with each drag.
- After any user scrub within a track, replacement reattachment does not use the 40ms dual-source blend. Fresh new tracks retain the 40ms same-song micro-transition that the owner preferred to the old 160ms wave.
- Added `replacement_scrub_hold` and `replacement_scrub_fallback` diagnostic entries with bounded elapsed policy; the user UI remains unchanged.

## Host gates

`tests/TestHonor063SeekScrub.java`: fast seek retains native gain attenuation; successful seek doesn't re-expose the original later; a slow seek falls back by deadline while keeping the same decoder; rapid superseded seeks serialize; Yandex buffering doesn't strand a muted source; a track boundary cancels delayed gain changes.

`tests/TestUnifiedAudioTransactions.java` and `tests/TestHonor059Journal.java` preserve legacy fail-open checks with the new bounded source-return expectation. All existing actual-engine/Android/Media3 checks and architecture/source-ownership enforcement remain mandatory. The Android SDK 36/D8/signed APK gate is required on GitHub CI. Test release in app via existing **Проверить обновление**, then evaluate manual finger seeks, repeated next, pause/resume, short native buffering, and a fresh automatic song transition on physical HONOR. Do not claim the perceptual bug solved until accepted by owner.
