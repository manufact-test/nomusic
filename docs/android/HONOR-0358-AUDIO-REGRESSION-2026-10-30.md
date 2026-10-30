# CELIKOM 0.3.58 HONOR audio regression — 2026-10-30

**Source:** user's real HONOR NTH-NX9 Android 13 combined diagnostic file `CELIKOM-combined-20261030-192016.txt`. It contains 3 runs: 0.3.54 (508 events), 0.3.54 (848 events), **0.3.58 (445 events)**. Do not mix old-run and new-run events.

## User-reported subjective observations (0.3.58)
- Track overlaps / dueling two songs appear resolved so far — preserve the Gate A–G ownership fixes.
- Audible small gap on every manual seek.
- Audible pause/resume gap, stronger from second song.
- New track starts acceptably, then an audible dip/cut shortly after start before continuing normally.

## Evidence specific to 0.3.58
- 16 `source_discontinuity`; 14 `replacement_seek_complete`; 12 `replacement_source_buffer` and 11 `replacement_source_buffer_resumed` events.
- 7 diagnostic `audio_command_anomaly` (commanded_silence). These are **command-state inference, not measured hardware output**. Durations observed include 41, 44, 45, 47, 50, 53, 209ms.
- Example repeated seek/short buffering and subsequent fade: at elapsed 6654ms seek, 6673ms buffer, 6705ms resume, 7096ms replacement transition completes after ~295ms ramp; at 7976ms seek, 7990ms buffer, 8021ms resume, 8437ms next transition completes (~306ms ramp).
- At 35969ms manual seek, `replacement_seek_complete` at 36176ms reports 203ms residual 204ms; follow-up seek correction then completes, transition at 36646ms. Audibly perceptible interruption plausible.
- On next tracks, replacement arrives only after original begins: at 29180ms source boundary, 29898ms original muted, 30399ms transition complete; similar 36972 -> 37516 -> 37994ms. The release design deliberately has `preparedBeforeArm:false`; do not accidentally add a conflicting next-track preloader.
- `ReplacementEngine.java` already has `FADE_MS=360`, `PAUSE_RESUME_FADE_MS=180`, `RETAINED_SEEK_JOIN_MS=180`, `NEW_TRACK_JOIN_MS=200`, `SOURCE_FADE_OUT_MS=100`; `AudioOwnership` is single owner and must remain so. Repeated ramp after a seek or a transient buffering is a candidate cause.
- No demonstrable simultaneous ownership of old/new replacement in reviewed diagnostic; logging is not a direct microphone-level confirmation.

## Next engineering work
1. Preserve a backup of the signed 0.3.58 and current branch checkpoint; tests before changing audio. No revert to dual flags or independent seek preparation.
2. Model seeks, transient buffering, pause/resume and beginning-of-track handover as separate **events governed by a single AudioOwnership state machine**, preserving old-generation/old-track cancellation and no-overlap invariants.
3. Identify whether short source buffering during a user seek should avoid restarting an entire source-to-replacement ramp, while preventing silent/overlap intervals. Measure explicit timeline for 0.3.58 under deterministic tests and compare next candidate.
4. Distinguish user pause from decoder buffering; avoid unnecessary decoder seeks on normal resume if drift is within tolerance, without stale decoder grants.
5. Keep source audio safely audible while replacement not yet granted and fade to replacement only after validated clock/decoded output.
6. Add focused regression tests for repeated seeks, seek while BUFFERING, pause/resume on second song, natural source boundary, and stale asynchronous callbacks. Do not declare seamless audio based on CI alone: repeat physical HONOR test and compare diagnostics.

No audio code changed as part of this diagnostic checkpoint.
