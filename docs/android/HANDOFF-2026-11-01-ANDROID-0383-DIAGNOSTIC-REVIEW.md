# CELIKOM Android — handoff to 0.3.83 diagnostic review
Date: 2026-11-01

## 1. What is live now

- Repository: `manufact-test/nomusic`.
- Stable OTA: **0.3.83 / versionCode 84**.
- Full release workflow: [#41347349507](https://github.com/manufact-test/nomusic/actions/runs/41347349507) — SUCCESS.
- Stable manifest: [stable.json](https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json); release workflow fetched it after publication and verified exact expected content with version 0.3.83/code 84.
- Deployed APK SHA-256: `13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425`.
- APK size: **8,763,465 bytes**.
- Original signing certificate SHA-256 retained: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- [Deployed APK](https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/84-13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425.apk).
- Release PR [#33](https://github.com/manufact-test/nomusic/pull/33) remains **open and unmerged**, pending the owner's diagnostic retest.

Important: the earlier test-only artifact from workflow #41346799079 (SHA `08f43a8b39623f2ea574ef86d2c58bbbd8046dc3a8b4554d37145835d79f3e79`) is not the deployed APK. The deployed APK is the separately rebuilt and signed file with SHA `13f68937a268ea21f0f0527b5a1bd41937d3bd43db4c4399143181b9a5163425`.

## 2. Immutable restore points — do not touch

- **0.3.82 / code 83** listening baseline:
  - branch: `backup/android-0382-stable-listening-baseline-20261101`
  - SHA: `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`
- Earlier **0.3.78 / code 79** rollback:
  - branch: `backup/android-0378-original-before-cached-join-20261101`
  - SHA: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`

Never force-push, amend, or repurpose either backup.

## 3. Working branches and release safety

- Diagnostic implementation branch: `feature/android-0382-playback-continuity-fix-20261101`.
- Source implementation commit before this documentation checkpoint: `a084cff5fd9fde500a4fdc36222de7a5c826523f`.
- This handoff/documentation commit is docs-only and does not alter Android code, release identity, APK or stable manifest.
- Release branch: `release/android-0.3.83-stable`; current recorded HEAD at handoff preparation: `8ae548f393702b3e5727ab6dcd08b8bff4bbe12a`.
- Release PR #33 is intentionally left open/unmerged until the owner retests.
- Do not push follow-up changes to `release/android-0.3.83-stable` casually: its PR validation gate is wired to the stable publisher and a PR update can re-run publication. Do investigation and any justified code work in a separate feature branch.
- Do not change the Hostinger updater or stable manifest manually.

## 4. What 0.3.83 actually changes

0.3.83 is **diagnostic-only**, not an audio-quality fix. It adds read-only Media3 event attribution and correlation information:
- timeline changes;
- media-item transitions;
- position discontinuities;
- source-event sequence and source-item generation;
- replacement generation and decoder instance identity;
- source kind (stream / local cache file / full downloaded file);
- seek sequence, type, target and elapsed time;
- owner generation / operation epoch and local prewarm attribution.

It does **not** change:
- audio join algorithm or gain/fade;
- ALIGNMENT or WARM policy/parameters;
- seek handling behavior;
- Next command behavior;
- local prewarm conditions;
- pause/resume or route recovery.

No APK should be built for another speculative parameter change.

## 5. Existing 0.3.82 evidence — historical baseline, not a diagnosis of 0.3.83

The prior combined device log `CELIKOM-combined-20261101-220637.txt` had 2,705 lines and three run segments. The 0.3.82 segment was 95.099 seconds / 1,317 events.

Observed in that 0.3.82 segment:
- 47 `source_discontinuity` events;
- 17 media-item transitions;
- 70 seek requests: 45 ALIGNMENT and 25 WARM;
- ALIGNMENT callback latency: median 51 ms, p90 360 ms, maximum 797 ms;
- two stream seek-data waits: 737 ms and 797 ms;
- local-file decoder prewarm ran only once; that decoder moved 46 ms after 214 ms.

Critical limitations:
- all 47 old `source_discontinuity` events were marked `userSeek: true`, including track changes. This field did not prove finger scrubbing.
- all 17 media-item transition events had `manualNextButtonObserved: false`. The old log could not prove a physical Next tap.
- the first observed start of “Солнца не видно” used the stream path; the local-file prewarm path was exercised once only. This is not enough to compare stream and local-cache starts across songs.
- decoder/transport clocks are not speaker PCM, hardware output or phase measurements. They cannot by themselves prove what was heard.

Do not turn any of these old counts into a root-cause claim for the new 0.3.83 run.

## 6. What the next chat must do first

The owner is moving to a new chat and will attach the new 0.3.83 phone diagnostics and screen recording there. **Those new attachments have not yet been analyzed in this checkpoint.** Do not say they were reviewed until actually opened.

First task, in order:
1. Read this handoff and `ANDROID-0383-MEDIA3-EVENT-CORRELATION-DIAGNOSTICS-2026-11-01.md`.
2. Open every new diagnostic file and the screen recording supplied by the owner. Determine exact run/version boundaries; do not accidentally analyze an older 0.3.82 segment as the 0.3.83 run.
3. Correlate visible moments in the video (track start, Next tap, finger seek, automatic boundary) with log timestamps and event IDs. If clock offset is needed, establish it from shared observable events; do not assume video and log clocks are aligned.
4. For each audible problem, record the track, source kind, source-item generation, replacement generation/decoder instance, seek ticket, Media3 reason/classification and relevant decoder/owner events.
5. Check whether the trace shows a repeatable sequence after manual Next, whether the defect appears on first playback without Next, and whether stream/local-cache paths behave differently. Distinguish observation from inference.
6. Inspect the corresponding current source code and tests, especially `ProbeService.java`, `ReplacementEngine.java`, source/ownership lifecycle and seek single-flight logic. Verify the logging implementation actually emits the fields claimed in the report; do not assume field names imply correct correlation.
7. Produce a technical conclusion with evidence and confidence levels. Identify any diagnostic blind spots before proposing behavior changes.
8. If a concrete bug is established, add a focused regression/replay test first and change one mechanism only. If evidence is insufficient, propose the smallest additional instrumentation. No speculative fade, delay, gain, seek-target or WARM tuning.

## 7. The three owner-visible problems to solve

A. Song beginnings: replacement must attach cleanly without a dip, repeat, skip or audible discontinuity.

B. Finger seeking: scrubbing must not produce audible lag, jumps or desynchronization across songs.

C. Seeking after Next: after the owner presses Next in Yandex Music, subsequent finger seeking must remain stable. This is an observation to investigate, not a proven causal relationship.

The target is stable behavior across different tracks and source types, not merely better log numbers.

## 8. Phone retest that generated the new trace

The intended short sequence was:
1. Start playback and let the replacement attach.
2. Tap Next once and let the next track settle.
3. Perform one finger seek within the track.
4. If convenient, allow one natural end-of-track transition.
5. Export diagnostics and provide the screen recording.

The owner should not be asked to repeat a long checklist unless the new trace has a specific, justified gap. Use the supplied video and logs first.

## 9. Working style / stop conditions

- Do not ask the owner to repeat information already present in the attachments or this handoff.
- Do not provide large lists of manual steps. If a phone test is truly needed, give one concise, specific test and explain what code change it validates.
- Do not create another APK until a concrete, tested fix or a necessary diagnostic change is justified.
- Keep the 0.3.82 and 0.3.78 backups immutable.
- Do not merge PR #33 until the owner has completed the diagnostic retest and the result is documented.
- After the next analysis stage, update current status, diagnostic report and handoff before moving chats again.

## 10. Documents to read

- [Current status](CURRENT-STATUS-2026-11-01-ANDROID-0382.md)
- [0.3.83 Media3 diagnostic release and retest procedure](ANDROID-0383-MEDIA3-EVENT-CORRELATION-DIAGNOSTICS-2026-11-01.md)
- [0.3.82 HONOR log analysis](ANDROID-0382-HONOR-DIAGNOSTICS-2026-11-01.md)
- [0.3.82 local-file prewarm experiment](ANDROID-0382-CACHE-PREWARM-EXPERIMENT-2026-11-01.md)
- [Next-chat starter message](START-NEXT-CHAT-ANDROID-0383-DIAGNOSTIC-REVIEW-2026-11-01.md)
