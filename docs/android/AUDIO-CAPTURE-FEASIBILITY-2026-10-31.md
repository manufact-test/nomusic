# CELIKOM Android: feasibility of measuring Yandex audio for a coherent cold join

**2026-10-31 — research checkpoint, not a release or acoustically accepted fix.**
Scope is exclusively the existing HONOR/Yandex Android audio transition. No CELIKOM permission, manifest, user UI, backend, desktop code, signed APK, or stable-branch state was changed by this investigation.

Read after `AUDIT-2026-10-31-0365-CONTINUITY-STAGING.md`. The experimental seek fix is separate; the 0.3.65 exclusive 250ms+250ms cold-entry dip still exists and fails the listening acceptance gate.

## The missing variable is physical audio phase, not another fade duration

The `ProbeService` event source/Media3 arbitration identifies a *track and transport timeline*. `ReplacementEngine` observes `MediaPlayer.getCurrentPosition()` and waits for an advancing decoder clock before `fade(true)`. `AudioOwnership` grants the replacement session only after the verified Yandex audio-session effect is permitted to mute the original. None of these readings reveal the relative sample phase, capture-to-speaker latency, per-output DSP buffering, or Bluetooth route delay.

For two equal-level, equal-frequency correlated components mixed with gains `a` and `b`, relative phase `phi`, the amplitude is:

`A = sqrt(a*a + b*b + 2*a*b*cos(phi))`.

Consequences reproduced by the standalone *synthetic* Python tests `android/native-companion/tests/test_handover_signal_feasibility.py`:

1. The current exclusive two-half envelope necessarily contains `a=b=0` at its midpoint. Removing overlap by progressively fading out one output before fading in the other creates an actual commanded energy valley; this is not a Media3 timeout issue.
2. At the midpoint of an equal-power overlap, identical aligned audio sums to amplitude `sqrt(2)` (**+3.01 dB**), not unity. If one component is inverted, the same gains produce **complete cancellation**. A gain envelope alone does not guarantee acoustic power for correlated tracks.
3. For a 500Hz tone, a 1ms relative time offset produces `phi=pi` and cancels the midpoint of a linear 50/50 blend. Media3 position estimates that agree to tens of milliseconds cannot establish the necessary phase alignment.
4. A discontinuous source-to-replacement switch can preserve the commanded envelope but can also jump between unrelated instantaneous waveform samples. Without source PCM and an output clock reference, a genuinely click-free switch cannot be guaranteed.

All signal examples use generated sine waves. **No Yandex audio or speaker output was captured, copied, uploaded or inferred from these tests.** Real full-band songs, different masters, censored/uncensored sections and codec/DSP differences make correspondence harder still. The results disprove blanket guarantees, not every possible perceptually acceptable compromise.

## Android capability audit

| Method | Possible measurement | Prerequisites / limits | Cold-join verdict |
| --- | --- | --- | --- |
| Existing `PlaybackSource`, Media3 callbacks, native `MediaPlayer`, `DynamicsProcessing` | Track identity, nominal transport position, own decoder readiness and commanded attenuation | Already present; `trustedSession` comes from the verified Yandex audio-effect panel. Timing **does not expose output PCM**. | Adequate for seek ownership, insufficient for sample-coherent overlap. |
| `android.media.audiofx.Visualizer(trustedSession)` | Partial 8-bit unsigned mono waveform, 8-bit magnitude FFT, approximate peak/RMS | Requires `android.permission.RECORD_AUDIO` despite the audio already playing; effect availability is device/session-dependent. Callbacks have configurable frequency but no documented per-sample *physical output timestamp*. Session 0 captures mix and additionally needs `MODIFY_AUDIO_SETTINGS` (already present). | Could test whether a coarse Yandex envelope is available on HONOR. **Not an assured sample-level synchronization source**. Cannot certify Bluetooth speaker phase. |
| `AudioPlaybackCaptureConfiguration` + `MediaProjection` + `AudioRecord` | PCM of playback that the source app allows to be captured, optionally restricted to Yandex UID | User must explicitly approve a projection session; `RECORD_AUDIO`; source must use an eligible audio usage and effective capture policy `ALLOW_CAPTURE_BY_ALL`, with matching user profile. Its actual Yandex policy is **unknown**. Target SDK 36 implies additional foreground `mediaProjection` service declarations and per-session user approval. | Only candidate for quantitative PCM correlation, if permission and source capture policy allow. Capture timestamps are not a cross-app speaker/Bluetooth clock; measuring/joining introduces buffer latency. Background transparent handover cannot silently start a projection. |
| `AudioTrack` / `AudioRecord` timestamps, `AudioRecordingConfiguration`, playback configuration callbacks | Timestamp for the *owned* track/capture stream or metadata about active streams | No public API here grants the PCM and output hardware clock of an independent Yandex `AudioTrack` solely from its audio session ID. `AudioRecord.getTimestamp()` refers to an early capture-pipeline frame. | Helpful diagnostics on owned output; cannot substitute for Yandex waveform acquisition. |
| External speaker/BT capture or user-approved Android screen recording | What was actually audible, including the cold dip, timbre/beat and route-dependent delay | Requires the real HONOR, explicit device operation/consent and a suitable recording path. Internal recording may omit apps that refuse capture. A microphone recording is a physical observation, not direct clean PCM of Yandex. | Needed for an **acoustic** accept/reject decision; avoids changing CELIKOM manifest, but not a direct cross-app phase clock. |

Android platform references (official):

- `Visualizer`: https://developer.android.com/reference/android/media/audiofx/Visualizer
- Playback capture and source capture policies: https://developer.android.com/media/platform/av-capture
- `AudioPlaybackCaptureConfiguration`: https://developer.android.com/reference/android/media/AudioPlaybackCaptureConfiguration
- Android media projection approval/foreground service: https://developer.android.com/media/grow/media-projection
- `AudioRecord.getTimestamp`: https://developer.android.com/reference/android/media/AudioRecord

## Why capture is not an automatic product fix

The current `android/native-companion/decoded/AndroidManifest.xml` declares `MODIFY_AUDIO_SETTINGS` but **not** `RECORD_AUDIO`, a projection foreground-service type, or a projection permission. `android/native-companion/verify_release.py` expressly forbids `RECORD_AUDIO` in shipping manifests. Adding it to the product to make a speculative algorithm work would both expand permissions and violate an existing release invariant. We have **not** done that.

Even a successful Visualizer constructor does not prove correct waveform phase, and successful projection capture does not prove zero-latency access to the sound actually reaching a Bluetooth speaker. Yandex's effective audio capture policy cannot be inferred from our `trustedSession`, its package name, target-SDK defaults alone or a normal Media3 event. It requires a real device-side permission-respecting test. If the source refuses capture, CELIKOM must honor the denial; it must not attempt to bypass it.

## Next experiment, in a separate on-device research environment only

**Gate 0 — permission and deployment boundary:** keep Android 0.3.65 installed and no new product APK. Any future diagnostic that declares `RECORD_AUDIO` or requests `MediaProjection` must be an explicitly approved, user-visible experiment, distinct from CELIKOM's existing manifest/release path. Never collect or upload full songs; retain only derived alignment/envelope measurements if consented.

**Gate 1 — source acquisition:** on HONOR with Yandex playing and its verified audio session, test whether a consented `Visualizer(trustedSession)` can initialize and report a nonzero (non-normalized) waveform/peak/RMS. Record *only* success/failure, selected session, sample rate, capture size, callback jitter, RMS/peak and the audio route. Check whether session changes on Next invalidate the effect. No user audio content should be logged. If Visualizer fails or produces unstable data, mark this route unavailable.

**Gate 2 — optional full PCM capture:** *only after separate approval*, determine whether user-authorized `MediaProjection`/`AudioPlaybackCaptureConfiguration` produces non-silent Yandex PCM. Distinguish projection granted-but-silent from source actually capturable. No assumptions about Yandex's runtime capture policy. Compare `AudioRecord` timestamps and actual microphone/speaker output under phone speaker, wired if available and Bluetooth; never assume they share a phase clock.

**Gate 3 — correlation and audibility:** use a licensed/test-owned reference track to measure time-varying source/alternate PCM alignment, correlation peak stability, worst-case 1ms / phase drift, loudness and click transients across the complete timeline: natural song -> manual Yandex Next -> several seeks -> natural successor -> several seeks. Repeat paused/resumed and route-loss paths. Only then consider a phase-aware overlap or another controlled seam. The original still must be restored safely on denial, buffering, effect loss, unrecognized track or app Stop.

**Go / no-go:** An implementation that only reduces the dip in fake-engine command telemetry without speaker/BT capture and acceptable audio evidence is **NO-GO**. A permission-free, always-background seamless waveform match is **not established** by current Android APIs. Do not replace `fade(true)` with a 40/100/160ms blend or another unmeasured timer. Preserve the completed seek regression and do not publish one signed release until both reported audio problems and the complete Android regression gates pass on HONOR.
