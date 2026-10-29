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

## 2026-10-29 architecture integration checkpoint

The refactor is implemented on `feature/android-0348-audio-ownership-stabilization` without touching desktop, server, catalogue, website or CMS. The current code is deliberately **not** an APK or a hardware-verified release. Never regenerate a signed APK until every gate is green and this branch has received a complete architecture audit.

**Single command path.** `AudioOwnership` now owns all positive and zero secondary volume commands, `MediaPlayer.start()`, `pause()`, `seekTo()` and verified native-effect restoration. Calls are serialized by `ProbeService.handler`. A decoder may start in PREPARING only with a verified native audio session and zero replacement volume; seeking requires ALIGNING or PAUSED and is always muted. Replacement non-zero output requires the exclusive granted effect. Emergency pause and decoder release are always allowed. State, identity and generation invalidate queued work.

**Single source-event classifier.** `SourceEventArbiter` handles Media3 media item transitions, event aliases, live controller aliases, discontinuities, index changes, repeats and source seeks before dispatching any callback to `ReplacementEngine`. The recorded 0.3.51 HONOR discontinuities presented a user-SEEK reason with changing indices on 104→105, 105→106, 106→107, 107→108 and 108→109. The first was stale because 105 was already active. Tests verify that a stale boundary cannot destroy a new decoder, that a genuine boundary still releases the old, and that stale 3648→61334 ms seeks cannot override the live 101197 ms position.

**Single drift decision.** `ClockSupervisor` replaces separate `SyncPolicy` and `DriftGuard` decisions in the live engine. Small commanded-clock offsets (240, 550 ms) do not cause repeated seeks. Persistent differences over 700 ms for 1500 ms fail open to original-only with TRACK_UNSUPPORTED, rather than reattaching the effect. An extreme stall can receive one bounded muted correction before fallback. Both older policy classes may remain for historical tests but do not own live audio. The sanitized fixture `android/native-companion/tests/honor-0.3.51-clock-replay.tsv` contains only abstract segment labels, timestamps, positions, drift and event types from 0.3.51. The original full report stays private.

**Lifecycle regressions.** A file ending more than 750 ms before the confirmed original is a track-specific unsupported failure, not a premature native boundary. The recorded 1469 ms metadata mismatch remains rejected by the 500 ms duration policy. Stop→Start of the same source identity now explicitly reacquires a new authority lease without bringing back a retired callback, and all automatic source transitions retain the user's enabled mode.

**Automated validation.** The workflow now includes `TestAudioCommandGateway`, `TestSourceEventArbiter`, `TestHonor051Journal`, `TestClockSupervisor`, `TestAudioLifecycle`, every previous real-engine host replay and the 16 runnable native addon tests. It checks pinned dependencies, compiles against API 36 and runs D8. Some addon test classes are fixture-only and require arguments, so the CI executable list follows the verified packaging contract rather than invoking every Test*.java blindly.

**Existing protection branches.** `backup/android-0351-last-signed-20261029`, `backup/android-pre-architecture-refactor-20261029`, `backup/android-handoff-docs-20261029` are immutable. Additional backups created in this work are `backup/android-architecture-reset-head-20261029`, `backup/android-phase1-audio-lifecycle-20261029`, `backup/android-before-transport-command-gateway-20261029`. No signing keys, full diagnostics or user secrets are committed.

**Remaining release blockers.** Hardware acoustic output cannot be measured by these host tests, because DynamicsProcessing acts on a separate original audio session. Real HONOR + Bluetooth playback, background reconnection, varied track endings and stop/start should be tested only after integration review; no claim of audible zero-overlap can be made from software command logs. PR #22 stays draft; issue #20 stays open.

## Final code checkpoint / blocking static guard

At code commit `04588acf3495cff41603c2a9ea12ed3cabdddf83` (GitHub Actions run `40926420266` PASS), `AudioOwnership.prepareSourceEffect()` also owns enabling the fresh session DynamicsProcessing instance. The controller validates that the effect is the one attached to its current identity before allowing a decoder to start or volume to rise. The release-blocking `check_audio_architecture.py` prevents future direct MediaPlayer start/pause/seek and effect-gain mutation from leaking back into `ReplacementEngine`. `TestAudioLifecycle` validates restoration ordering: the secondary decoder must already be silent before native gain can be reset. This does not establish acoustic hardware output timing. No signed APK or version bump exists from this work.

## 2026-10-29 static concurrency and release-readiness addendum

Verified regression commits: `25caa102` (stable DSP/volume command coalescing and stale Media3 seek-identity fence), `26e71ce` (explicit same-song decoder-lease retirement), `ce52b178` (actual-engine retry and long-pause callback regressions). Full CI **success**: https://github.com/manufact-test/nomusic/actions/runs/40931276362.

The source/audio-effect authority now distinguishes a retained decoder with a temporarily released source effect (e.g., long pause) from a *retired* MediaPlayer whose old callback must be fenced off even if the source song identity has not changed. `release()` retires the ownership epoch after audio silence and source restoration. A same-song new decoder receives a new epoch; a long paused retained decoder keeps its epoch. The Media3 SEEK classifier requires a match among previous, live, and event aliases and rejects mixed old/new position aliases even when timestamps are identical. During stable audio output, valid repeat grants still revalidate effect identity/control/enablement, but do not repeatedly send the same DSP attenuation; verified unchanged positive decoder gains are coalesced while emergency zero-gain commands are never coalesced.

**Static audit outcome:** source scope limited to Android and these documents, tests green, no APK generated, no physical waveform measurement. `build_release.py`, `verify_release.py`, and `AppVersion.java` still describe the rejected `0.3.51` with versionCode 52; a genuinely new candidate requires coordinated next-version identifiers (>52), pinned inputs, original signing identity, complete signed-DEX/asset/manifest checks, and finally HONOR/Bluetooth listening. Do not describe this static review as hardware acceptance.

