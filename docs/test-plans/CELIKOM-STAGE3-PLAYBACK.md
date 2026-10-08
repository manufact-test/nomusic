# CELIKOM Stage 3 — live playback gate

Version: `0.3.2`. Status: pending stability run. The owner's 0.3.1 JSON confirms healthy startup, the exact configured Track ID and an active guard with −1 ms drift, but repeated same-track restores (generation 49) block acceptance. Two reproducible defects are fixed: utility media stealing a paused master, and an active operation aborting during metadata-only seek. This does not prove every reported restart had either cause; the new diagnostics must establish live continuity.

## Setup

1. Disable the old PoC and any second CELIKOM copy.
2. Replace the loaded extension with the `0.3.2` unpacked build; reload it in `chrome://extensions`.
3. Refresh Yandex Music once. This replaces the previous page-world globals; do not mix old and new scripts.
4. Press `Старт`, play a track, open `Для разработчика` and press `Тестировать текущий трек`. Start at a low comfortable volume: the replacement is a synthetic signal, not a song.
5. Expected: `REPLACEMENT_ACTIVE`, exact configured/current Track ID equality, `guardActive: true`, one replacement audio, no original music mixed with the test signal. Copy diagnostics from the developer section.

## Scenarios

| Action | Expected |
| --- | --- |
| Keep the configured track playing for 2–3 minutes without changing the queue or settings | Same active generation; activation/restore counts unchanged; no repeated PREPARING/RESTORING loop |
| Unconfigured track A → configured B → unconfigured C | Original → signal → original; no wrong-track replacement |
| Pause for at least 10 seconds; resume | Silence on pause; signal resumes at matching position with the same generation and no restore |
| Seek forward and backward; seek then immediately pause | Replacement follows seek and stays silent when paused; metadata-only buffering pauses it without recreating the guard |
| Rapid next → next → previous within one second | No previous load/error changes the new track; at most one replacement |
| Next while replacement prepares | Old preparation cancels without muting the new original |
| Change volume; mute; unmute in Yandex | Signal mirrors settings; original stays physically guarded |
| Return original; wait at least 10 seconds; reopen popup | Original stays restored for the same Track ID; no automatic rearm |
| Explicit Start after manual original | Test replacement may rearm for configured exact ID |
| Stop during playback; reopen popup; refresh page | Original restored; STOPPED persists until Start |
| Disable extension while active, visible page | Signal stops and original returns within 12 seconds plus watchdog scheduling; report actual delay |
| Refresh / navigate SPA while active | No duplicate sound, stuck guard, stale ID or permanently connecting state |
| Tab through four main controls | Visible focus, Enter/Space work; Add Track is explanatory only |
| Clear test binding | Immediate original-only mode; no synthetic signal on later tracks |

For a missing/blocked demo file, production code must remain original-only, log `replacementError`, and avoid a retry loop. Automated tests inject load/play/guard/restore failures; browser fault injection is optional and must not change extension site permissions as a workaround.

## Evidence and acceptance

Send diagnostics at the start of active playback and after the continuity/pause/seek run, then after Return Original and Stop, plus a short report of next/previous, volume/mute and extension-disable restoration. `playback.activationCount` counts successful activations; `restoreCount` counts disposals of active/preparing operations, including intentional controls. Compare them within a single tab session: manual original, Stop and track changes legitimately increase restores. `lastRestore` records binding IDs, readiness, seeking and a safe MAIN reason where available; signed stream URLs are never logged. A native source change restores immediately and requires a new exact Track ID or explicit Start before retrying the stale binding.

Automated VM tests do not substitute for this run. Any double audio, wrong track, unexplained same-track restore loop, persistent mute, failed bypass or queue disturbance blocks Stage 4. After this gate, implement API/MySQL/Range (Stage 4), then connect Hostinger and authorized real audio files (Stage 5).
