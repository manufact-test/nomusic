# CELIKOM Stage 3 — live playback gate

Version: `0.3.1`. Status: pending owner run after fixing the reported 0.3.0 startup crash. Stage 2 acceptance does not cover this new audio-changing implementation.

## Setup

1. Disable the old PoC and any second CELIKOM copy.
2. Replace the loaded extension with the `0.3.1` unpacked build; reload it in `chrome://extensions`.
3. Refresh Yandex Music once. This replaces the previous page-world globals; do not mix old and new scripts.
4. Press `Старт`, play a track, open `Для разработчика` and press `Тестировать текущий трек`. Start at a low comfortable volume: the replacement is a synthetic signal, not a song.
5. Expected: `REPLACEMENT_ACTIVE`, exact configured/current Track ID equality, `guardActive: true`, one replacement audio, no original music mixed with the test signal. Copy diagnostics from the developer section.

## Scenarios

| Action | Expected |
| --- | --- |
| Unconfigured track A → configured B → unconfigured C | Original → signal → original; no wrong-track replacement |
| Pause for at least 10 seconds; resume | Silence on pause; signal resumes at matching position, not stale-clock error |
| Seek forward and backward; seek then immediately pause | Replacement follows seek and stays silent when paused |
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

Send diagnostics while active, after Return Original and after Stop, plus a short report of pause/resume, seek, next/previous, volume/mute and extension-disable restoration. Automated VM tests do not substitute for this run. Any double audio, wrong track, persistent mute, failed bypass or queue disturbance blocks Stage 4. After this gate, implement API/MySQL/Range (Stage 4), then connect Hostinger and authorized real audio files (Stage 5).
