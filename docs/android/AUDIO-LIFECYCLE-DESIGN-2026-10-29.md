# CELIKOM Android — audio architecture contract (29 October 2026)

## Evidence and scope
New work follows the 0.3.51 HONOR combined diagnostics, run 19:14:27 +03:00. Source alias 106 had 1156–1166 ms commanded-clock discrepancy for more than 80 seconds. Alias 108 had source duration 221930 ms versus replacement 223399 ms: 1469 ms mismatch. No outgoing-reset log was present. This does not prove the actual speaker/Bluetooth sound waveform. The original combined journal and all signing assets remain private.

## Event ownership
ProbeService delivers Media3 snapshots and confirmed boundaries on its serialized main handler. NativeApi posts asynchronous responses to that same handler. ReplacementEngine retains file/decoder/seek/buffer transport, but AudioOwnership now holds the exclusive audible-output permission, track generation, delayed-pause lease and user-visible lifecycle state.

The permitted path is SOURCE_ONLY -> PREPARING -> ALIGNING -> REPLACEMENT. Pause or seek withdraws the audible permission; only an aligned, verified current decoder may request it again. Any failure moves through RECOVERING (secondary silent before restoring source), a wrong file becomes TRACK_UNSUPPORTED for that song only, and explicit Stop enters STOPPED. An incidental metadata observation cannot rearm a stopped system. Reactivation requires a user Arm event.

The authority checks the current track generation for decoder prepare, error, completion, seek-timeout, pause and handover callbacks. Track boundaries are committed after the outgoing decoder is silenced and native attenuation is released. A callback from an earlier generation may observe but never start a decoder or change an audio effect for a newer track.

A positive MediaPlayer volume is rejected unless (a) the authority is REPLACEMENT, (b) the verified source DynamicsProcessing is enabled and under control, (c) the original has first received a -100 dB input-gain command. No automatic crossfade of two audible sessions is allowed. A failed mute/pause forcibly releases the secondary decoder before native gain is restored.

## Contract for endings and drift
A secondary completion with over 750 ms remaining in the active source is **not** a Media3 track boundary. Restore native, mark TRACK_UNSUPPORTED with a user-readable reason, and continue automatic matching at the next confirmed source identity. Preserve the 500 ms duration equality guard, pause prealignment and seek optimizations. Sustained commanded-clock drift above 700 ms for 1500 ms fails open for the current track, rather than repeatedly seeking/fading. Distinguish this clock measurement from hardware output latency.

## Gates and release policy
Mandatory host suite includes TestEngine, TestAudioOwnershipRegression, TestRealFailures, TestAudioLifecycle, TestResumeClock, TestStreamingEngine, TestCarRecovery, TestHandoverClock, TestLongRun and the independent addon tests. Android API36 compilation and D8, Android-only isolation, and a physical HONOR playback/BT audit are separate requirements.

This is an architecture integration checkpoint, **not** a claim the entire lifecycle/event reducer or hardware isolation has been proven. Continue removing parallel state transitions and validate the full end-to-end stream and Media3 callback sequence before producing any APK. Never deploy or merge desktop/server/CMS assets.

Backup before work: backup/android-architecture-reset-head-20261029 at b9c3e383f10630d5d55f8525e7cd300addc1e498. PR #22 remains draft, issue #20 remains open.
