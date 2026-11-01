> **Follow-up 2026-11-01:** This file records the 0.3.75 diagnostic baseline. The signed 0.3.76 / code77 release is now published to Hostinger stable. Open CELIKOM and use its existing `Проверить обновление` control; install over the current app without uninstalling, run the affected-track listening test and export diagnostics. Production CI/publication [41299061730](https://github.com/manufact-test/nomusic/actions/runs/41299061730) passed; the live manifest reports `0.3.76 / 77`. Published APK SHA-256: `76e1086dc6a38d5b5c5186475babbfd16c959c06a573775e3c264b3b63cdcf40`. This is not an audio-fix claim. Its next-step plan has been refined by [ANDROID-0376](../android/ANDROID-0376-OUTPUT-CLOCK-AND-UPDATE-STATE-2026-11-01.md) and the [follow-up handoff](2026-11-01-audio-output-clock-and-update-state-followup.md). The key correction is that `rawResidualMs` includes source advance during asynchronous seek; it is not by itself decoder landing error or acoustic output evidence. No audible fix is claimed.

---

# CELIKOM — handoff: 2026-11-01 diagnostic 0.3.75 and update-state UX

## Purpose

This handoff is for the next Android/audio developer. Do not restart the project and do not repeat the previous seek-clock tuning blindly. The user reports that playback still sounds wrong overall: some tracks seem slightly better, others worse. Treat the current result as **not solved**.

Repository: https://github.com/manufact-test/nomusic  
Source branch at handoff: `feature/android-unified-preparation-seek-gate`  
Handoff branch: `handoff/diagnostic-audio-output-evidence-20261101`  
Device: HONOR NTH-NX9, Android 13 / API 33  
Yandex Music: 2026.09.5 #167.1gpr  
Diagnostic uploaded: `CELIKOM-combined-20261101-125049.txt`  
Diagnostic format: CELIKOM COMBINED 0.3.75; includes runs 0.3.73, 0.3.74 and 0.3.75.

## 1. User-facing result

The user says the sound remains unsatisfactory and inconsistent between songs. In one song it seems a little better; in another it seems worse. The user's overall assessment is that it is still bad / effectively not fixed. Do not reinterpret this as a successful fix because internal timing counters look better.

The main objective remains a seamless, inaudible handover between original Yandex audio and the replacement audio:
- no click/pop at the beginning;
- no full fade-out followed by a separate reappearance;
- no audible jump, doubled transient, missing fragment, or timing shift;
- manual seeking must remain usable and must not break pause/play or next-track behavior.

## 2. What the new diagnostic actually contains

The file has three runs:

| Run | Events | Interpretation |
|---|---:|---|
| 0.3.73 | 38 | Very short, manually stopped after about 5.2 s; not a meaningful audio evaluation |
| 0.3.74 | 962 | Main run; 9 replacement preparations, 61 seek acknowledgements, 24 WARM alignments |
| 0.3.75 | 1073 | Main run; 8 replacement preparations, 67 seek acknowledgements, 20 WARM alignments; file ends during playback_health rather than a run_end event |

0.3.75 contains these prepared tracks and source-vs-replacement duration differences:

| Track | Track ID | Replacement duration minus source |
|---|---:|---:|
| Толер | 114377621 | +50 ms |
| Солнца не видно | 48591644 | -1 ms |
| Биг сити лайф | 40371622 | -1354 ms |
| Он рядом | 89285816 | +29 ms |
| Крылья | 50163052 | -582 ms |
| Монпасье | 1944605 | +83 ms |
| Не стесняйся | 48592143 | +156 ms |
| Метамир | 42601865 | -663 ms |

The bounded-tail policy accepts some replacements whose measured duration is shorter than the Yandex source. That may be intentional for tail tolerance, but it must be evaluated against the user's audible symptom; it does not establish that the replacement waveform is the same edition or that the join is inaudible. Track identity is still metadata-level: album ID + strict title/artist + duration. The log explicitly says `automaticSourceIdVerified:false`.

### Critical correction to the previous interpretation

Do **not** say that the whole seek path is now accurate merely because WARM seek timing improved.

Measured `replacement_seek_ack` values:

| Run | Kind | Count | Raw residual range | Acks with |residual| > 100 ms |
|---|---|---:|---:|---:|
| 0.3.74 | WARM | 24 | -177…+6 ms | 5 |
| 0.3.74 | ALIGNMENT | 37 | -9…+403 ms | 8 |
| 0.3.75 | WARM | 20 | -52…+91 ms | 0 |
| 0.3.75 | ALIGNMENT | 47 | -16…+772 ms | 11 |

0.3.75 WARM alignment is materially better in these counters. However, 0.3.75 ALIGNMENT remains highly variable and has 11 acknowledgements over 100 ms, including:
- +223 ms, callback 223 ms;
- +285 ms, callback 342 ms;
- +431 ms, callback 469 ms, `rangeWaitObserved:true`;
- +310 ms, callback 358 ms;
- +201 ms, callback 254 ms;
- +327 ms, callback 377 ms;
- +239 ms, callback 290 ms;
- +259 ms, callback 301 ms;
- +293 ms, callback 291 ms;
- +772 ms, callback 816 ms, `rangeWaitObserved:true`;
- +350 ms, callback 403 ms.

These are important because they occur on ALIGNMENT, including the path after user seeks. The 0.3.75 WARM counters do not cancel out these larger ALIGNMENT discrepancies.

In 0.3.74 there were also 9 `audio_command_anomaly` events, and in 0.3.75 there were 8. Their `kind` is `overlap_commands`, cause `handover`, with source and decoder both playing while the replacement volume command is rising. These events may be expected by the current blend implementation, but the developer must inspect the exact code path and confirm whether command ordering and actual output overlap are safe. The event is not proof of audible overlap because hardware output is not measured.

0.3.75 also records:
- 43 source discontinuities in the full run (36 same-item seeks, 7 item transitions);
- 35 source-buffer events;
- 8 `replacement_join_transport_summary` records;
- 43 `replacement_join_guard_verified` records;
- `sourcePcmMeasured:false` and `phaseVerified:false` throughout join summaries and guard events;
- `hardwareOutputMeasured:false` throughout audio ownership transitions.

## 3. The central diagnostic limitation

The current diagnostic primarily measures **commanded/player/decoder timeline positions**, not the audio waveform that actually reaches the speaker/headphones.

Important fields repeatedly show:
- `sourcePcmMeasured:false`;
- `phaseVerified:false`;
- `hardwareOutputMeasured:false`;
- `transportOnly:true`.

Therefore:
- `replacement_join_guard_verified` means the software's position estimate passed a threshold; it does not mean the two audible waveforms are phase-aligned or perceptually continuous.
- `replacement_join_transport_summary` is a transport-clock summary, not an acoustic measurement.
- A 160 ms commanded complementary-linear gain ramp does not prove a click-free crossfade.
- `sourceMutedCommand:true` / `replacementVolume:1` are commands/state, not proof of the exact samples emitted by the audio mixer.
- A user can hear a problem even while the internal drift is inside 100 ms.

This is likely why we have repeatedly celebrated improvements in counters without achieving the desired listening result. The diagnostic has been useful for transport debugging, but it is not yet a sufficient instrument for diagnosing the audible defect.

## 4. Required investigation — do this before changing the audio algorithm

### A. Audit the diagnostic semantics

Inspect the code that emits:
- `replacement_seek_request`
- `replacement_seek_ack`
- `replacement_seek_complete`
- `replacement_warm_alignment`
- `replacement_join_guard_verified`
- `replacement_join_transport_summary`
- `audio_command_anomaly`
- `replacement_original_muted`
- `audio_owner_state`

For every reported residual, write down exactly:
1. which clock produced each timestamp;
2. whether it is a requested position, projected player position, decoder media position, callback time, or estimated presentation time;
3. whether values are sampled at the same instant;
4. whether callback delay is incorrectly mixed into the media-position residual;
5. whether the source player position is extrapolated while the decoder is paused/seeking;
6. whether a seek callback means the requested media position was reached, or only that the seek operation completed;
7. whether the 100 ms threshold has any physical/acoustic basis.

In particular, investigate why ALIGNMENT acknowledgements can return +200…+772 ms while the player later resumes and the join guard reports a small drift. Do not hide this by changing thresholds or relabelling fields. Determine if this is stale sampling, a mismatched clock, delayed callback, range wait, source projection error, or an actual decoder positioning error.

### B. Build an actual audio-output evidence path

First investigate what Android exposes without privileged/root access on this device and API level:
- `AudioTimestamp` / `AudioTrack.getTimestamp()` for the replacement output's frame position and monotonic timestamp;
- audio output latency / frame accounting where available;
- AudioEffect session semantics and whether the current effect attachment is on the actual Yandex source session or only a separate replacement session;
- Media3/ExoPlayer position and seek semantics, distinguishing timeline position from output presentation time.

Important: do not claim that Android gives CELIKOM direct access to another app's PCM output. It generally does not provide arbitrary raw capture of another app's audio without a supported capture path and user authorization. Check Android's Audio Playback Capture restrictions and HONOR behavior before proposing capture. Do not add Accessibility, notification listener, microphone recording, root requirements, or privacy-invasive permissions as a casual workaround.

If direct source PCM cannot be captured, design an honest measurement strategy:
- record replacement AudioTrack presentation timestamps;
- record all available source player clock/timeline signals with explicit uncertainty;
- optionally create a user-authorized external loopback test procedure (another recording device/PC line-in) to compare actual audible output;
- keep command-level and acoustic-level evidence separate in the report.

If actual waveform measurement is possible through an explicit user-authorized route, compare source and replacement around handover using waveform correlation, onset/transient alignment, RMS/envelope and discontinuity detection. Do not assume phase matching is necessary for two independently mastered copies; first verify edition identity and perceptual timing.

### C. Inspect track identity and file integrity

The prepared replacements show duration deltas up to -1354 ms for `Биг сити лайф`, -663 ms for `Метамир`, and -582 ms for `Крылья`. Determine:
- whether these are intentionally different endings / encodings / edits;
- whether the backend's `durationMs` metadata, measured file duration, and source duration are being compared consistently;
- whether accepting a bounded tail can hide a wrong or incomplete recording;
- whether the user noticed the worse result on one of these tracks.

Do not use duration tolerance as proof of track identity. Album metadata is useful evidence but is not source-track-ID verification.

### D. Inspect the join and state machine

Review the full flow from source observation through resolve, stream buffering, decoder preparation, alignment, warm correction, join guard, gain ramp, exclusive handover, seek recovery, and cleanup.

Specific questions:
- Why does the normal seek path (ALIGNMENT) still have high callback/residual outliers?
- Why are warm corrections sometimes one pass and sometimes two?
- Why does the code start a complementary-linear join and later emit `overlap_commands` during handover?
- Does `audio_command_anomaly` describe an expected transient in the state machine or a genuine command race?
- Is the source audio actually muted before the replacement becomes audible, or are both commands asynchronous?
- Does the 360 ms source mute ramp overlap the 160 ms join ramp in a way that creates a dip/peak?
- Are gains linear in amplitude or perceived loudness? Does the crossfade law fit the actual audio path?
- Is the original source restored on every failed/late seek and every lifecycle transition?
- Are buffering/resume and end-of-track paths changing the join behavior?

Do not merge seek and next-track paths into one new mechanism without proving the state-machine boundaries. Past work has shown that combining the paths can create regressions.

### E. Compare against prior documented experiments

Before proposing a new approach, read the relevant existing docs, especially:
- `docs/project-status.md`
- `docs/android/`
- `docs/architecture/`
- `docs/adr/`
- `docs/test-plans/`
- `docs/handoff/`
- `android/native-companion/tests/TestHonor074StrictJoin.java`
- `android/native-companion/tests/TestHonor075WarmLatency.java`
- `android/native-companion/tests/TestHonor066JoinLab.java`
- `android/native-companion/tests/TestHonor066SeekBufferReplay.java`
- `android/native-companion/tests/TestHonor067SlowStreamSeek.java`
- `android/native-companion/tests/TestUnifiedAudioTransactions.java`

Read the complete relevant tests and implementation, not just test names. Determine which previous hypotheses were already tried and rejected. Do not re-run the same change with a different name.

## 5. Rules for the next developer — avoid repeating past mistakes

1. Do not change production audio behavior before producing a written root-cause hypothesis supported by evidence.
2. Do not treat simulated/fallback scenarios as real runtime observations.
3. Do not treat player position, decoder position, or callback completion as proof of acoustic alignment.
4. Do not claim success based only on reduced drift counters.
5. Do not change multiple variables at once. One isolated hypothesis per experiment.
6. Preserve a known-good build/branch before changes. Keep a clean rollback point.
7. Do not regress pause/resume, manual Next, manual seek, automatic next, recovery, or source restoration while fixing the join.
8. Run the existing host tests and Android compile gates before delivery. In particular inspect `android/native-companion/tests/run_addon_host.py`; it compiles all addon source and test classes and runs the designated native test suite in CI with Android SDK 36.
9. Include a before/after table and a clear statement of what was actually measured.
10. If no reliable measurement can prove the proposed fix, say so and build the measurement first rather than claiming a fix.

## 6. Update UX request — accepted product behavior, not yet implemented

The user explicitly approved making the in-app update state match the notification. Current code inspection found why the UI can be stale:

- `UpdateCheckJob.onStartJob()` calls `UpdateCenter.fetch()` and, when a release is found, calls only `UpdateCenter.notifyAvailable()`.
- It does not persist the discovered release/version for the activity.
- `UpdateCenter.check(false)` can return early for six hours when `checked` is recent and `verifiedInstalledCode` matches the installed app.
- `UpdateCenter` currently stores only `verifiedInstalledCode` and `verifiedLatest` from the foreground check. It does not restore a pending release candidate on activity creation.
- The foreground check's `candidate` is an in-memory field. A notification tap launches `RecorderActivity`, but the activity cannot necessarily reconstruct the release candidate from persisted state.

Required behavior:
- Use one persisted update-state source for background JobService, foreground activity, and notification tap.
- Persist only validated manifest data for a newer version (versionCode, versionName, notes, canonical APK URL, SHA-256, size, schema/channel as needed). Validate it with the existing strict host/package/signer checks before display or download.
- When a background check finds a release, persist the candidate **before** posting the notification.
- When CELIKOM opens, render the persisted pending update immediately; do not display “latest version” while a newer verified candidate is stored.
- UI when no update: “У вас последняя версия” + “Проверить обновление”.
- UI when update exists: “Доступна новая версия X” + “Скачать обновление” + “Проверить обновление” + “Позже”.
- “Позже” should hide/defer the prompt, not delete the update candidate or falsely mark the app as current. On next app open, it can remain available in a quiet state or reappear according to a documented reminder policy.
- Download must always use the verified persisted candidate and revalidate APK hash, package, version and signer as it does now.
- On successful install, after confirming installed versionCode, clear obsolete candidate/notification state. Do not clear a newer candidate if the install callback is for an older code.
- If the manifest check fails, preserve a previously verified pending candidate rather than overwriting it with “latest” or losing it. Show a neutral error only when no verified candidate exists.
- Handle notification permission denied, offline startup, stale candidate, rollback/disabled manifest, version already installed, and app upgraded while it was not running.
- Do not add more buttons to the main player UI; keep these controls in the existing update section.
- Keep updater isolated from audio state and playback lifecycle.

Files to inspect:
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/UpdateCenter.java`
- `UpdateCheckJob.java`
- `UpdateInstallReceiver.java`
- `RecorderActivity.java`
- update-related tests under `android/native-companion/addon/` (the host runner runs `TestNotifications` and `TestAppPresentation`; add/update focused update-state tests).

## 7. Suggested order of work

1. Confirm branch/HEAD and read project docs + relevant tests.
2. Reproduce and audit the 0.3.75 diagnostic calculations, especially ALIGNMENT residuals and callback semantics.
3. Audit Android output clock/latency options and the actual session topology on Android 13/HONOR.
4. Produce a written measurement plan and root-cause ranking before touching production audio code.
5. Implement the updater persisted-state/UI behavior as an isolated change, with tests; do not mix it with audio changes.
6. Only then run one controlled audio experiment based on the strongest measured cause.
7. Deliver a build only after tests, regression gates and a transparent evidence report.

## 8. Official Android references to verify during investigation

- Media3 Player API and seek/discontinuity semantics: https://developer.android.com/reference/androidx/media3/common/Player
- Android AudioTimestamp: https://developer.android.com/reference/android/media/AudioTimestamp
- Android AudioTrack: https://developer.android.com/reference/android/media/AudioTrack
- Audio playback capture policy and limitations: https://developer.android.com/media/platform/av-capture
- Android AudioEffect: https://developer.android.com/reference/android/media/audiofx/AudioEffect

The next developer must check current documentation and API/device behavior rather than assume all signals are available on API 33.

## 9. User communication

The user is tired of repeated experiments and contradictory “it is fixed” conclusions. Be direct. Explain what is measured versus inferred. Do not ask the user to repeat information already in this handoff. Do not make them perform a large diagnostic ritual unless the next test isolates a specific hypothesis and is likely to change the diagnosis.

Current user conclusion: audio still sounds wrong overall. Treat this as an unresolved defect.


### Verified notes from current Android documentation (checked 2026-11-01)

- Media3's `Player` contract says the visible player state is updated immediately after method calls even if the actual change is handled asynchronously. It also distinguishes normal playback progression from position-discontinuity callbacks, and documents `DISCONTINUITY_REASON_SEEK_ADJUSTMENT`. Do not assume a seek request or callback is a presentation timestamp: https://developer.android.com/reference/androidx/media3/common/Player
- Android `AudioTimestamp.nanoTime` from `AudioTrack.getTimestamp()` estimates when a frame was presented or committed to presentation, using the monotonic timebase. This is a more relevant output-clock signal for the replacement track than just decoder media position, though it still does not expose the source Yandex PCM: https://developer.android.com/reference/android/media/AudioTimestamp
- Capturing another app's playback through `AudioPlaybackCapture` requires `RECORD_AUDIO`, a user-approved `MediaProjection` token, same user profile, compatible usage and capture policy. Yandex may disallow capture, so this is a conditional test option, not an assumed capability: https://developer.android.com/media/platform/av-capture and https://developer.android.com/reference/android/media/AudioPlaybackCaptureConfiguration
