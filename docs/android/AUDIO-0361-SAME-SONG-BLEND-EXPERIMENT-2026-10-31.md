# CELIKOM Android — same-song blend experiment, 31 October 2026

**Status: isolated experiment; NOT a release or approval for Android 0.3.62.**
Branch: `experiment/android-soft-exclusive-join-20261031`. Stable working branch and
the signed, installed Android 0.3.61/code62 APK remain unchanged.

## User-observed problem

During automatic next-song playback on HONOR, Yandex Music's native recording
plays first. CELIKOM joins roughly half a second later. The listener hears a
brief `pshik`/click where the replacement switches in. The brief `Пауза`
notification is not proof of a stopped audio stream. Logs measure command
timing, not physical Bluetooth/speaker output.

## Rejected prototype (retained in this branch's history, NOT at HEAD)

100ms source attenuation followed by 200ms replacement gain produced a period
when both tracks were too quiet. `TestHonor059Journal.fadeEnergyFloor()` caught
the same rejected HONOR 0.3.59 regression. Do not restore that implementation.

## Current experimental HEAD

- Native Yandex stays at 0dB, replacement decoder silent, throughout network
  retrieval, alignment and the verified advancing-decoder-clock gate.
- **Only a newly attached, verified same-song replacement** can execute a 160ms
  equal-power gain blend; `AudioOwnership.blendSameSong` is the only authority.
  Intermediate gains are `cos(pi*t/2)` for the native source and
  `sin(pi*t/2)` for the replacement (with its allowed descriptor gain).
- Handover is fenced by source identity/epoch, account/edition/version/duration
  command ticket, decoder-running state, seek-in-flight state and effect control.
- Every source boundary, pause, buffering hold, route loss, seek, stop or account
  change cancels stale blend callbacks. A pause commands decoder zero **first**
  and restores native gain; existing retained pause/seek handover remains
  immediate and exclusive (no new overlap window).
- Overlap of two media sessions is authorized **only** inside
  `SAME_SONG_BLEND`, never across different track identities. The sole owner
  keeps controlling the original DSP and the replacement decoder.

## Gates and limits

Host suite `python3 android/native-companion/tests/run_engine.py` covers actual
engine, HONOR 0.3.59/60/61 replays, 300 song boundaries/15 virtual hours,
pause/seek/buffering/route/boundary cancellations, post-clock equal-power
envelope, rejected different-song identity, source energy floor, and the static
single-audio-authority check.

This suite **cannot** certify physical audio continuity. Two aligned-enough
versions may still create phasing, a doubled transient, a momentary loudness
bump, or another hardware-specific click; Android effect commands and
MediaPlayer gains are not sample-accurate on all devices. The original and
replacement may differ in mastering or offset up to the accepted 350ms drift
budget. A real HONOR listening check is therefore release-blocking.

Local SDK 36 is unavailable, so the Android DEX/build gate must run in CI.
No signed APK should be shipped from this branch until CI and real-device
listening, including rapid next, manual pause/resume, seek, native buffering,
Bluetooth interruption and switching CELIKOM off, confirm it helps without
regression. This experiment does **not** reduce the original network readiness
latency (about 0.5s); it aims to conceal the audible seam at takeover.
