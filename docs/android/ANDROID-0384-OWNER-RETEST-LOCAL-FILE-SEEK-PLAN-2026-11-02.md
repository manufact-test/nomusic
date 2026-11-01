# CELIKOM Android 0.3.84 — acoustic retest and next experiment (2026-11-02)

## Read first — latest state

**Owner verdict: NO MATERIAL ACOUSTIC IMPROVEMENT** after installing and testing 0.3.84. Scrubbing still has audible unevenness; beginnings and Next handovers remain unreliable and differ across tracks. The owner is exhausted by many unsuccessful trial versions. Stop speculative constant/timer patches and repeated owner testing. Audit evidence and test one falsifiable architecture hypothesis in isolated staging.

**Stable 0.3.84 / versionCode 85 is LIVE; DO NOT overwrite it.**
- Signed release source: release/android-0.3.84-stable, functional SHA 5dcdac3ad0048d4000ede5d44bec36aed772a8f7; docs baseline SHA d434d442aeed7a84f17126da48c6a08b752c825d.
- Publish workflow: https://github.com/manufact-test/nomusic/actions/runs/41350942716 (PASS).
- Live manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json
- Signed immutable APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/85-a64c562989d92749982ec979eb712fa8ba2fa12492c454ff7b1c54e9337f6bc2.apk
- APK SHA256 a64c562989d92749982ec979eb712fa8ba2fa12492c454ff7b1c54e9337f6bc2, size 8,763,465 bytes; original signing certificate unchanged.
- Release PR #34: https://github.com/manufact-test/nomusic/pull/34 (unmerged).
- Initial in-app APK download appeared stuck, but the direct browser URL worked and an in-app retry subsequently downloaded. The full server APK was verified by SHA256. No hotfix to server, APK or updater was made. Do NOT claim the download was fixed by an imaginary code change.

## BACKUPS — preserve exactly

1. **NEW 0.3.84 checkpoint**: backup/android-0384-before-local-seek-experiment-20261102, created from SHA d434d442aeed7a84f17126da48c6a08b752c825d BEFORE this handoff/documentation and before any new audio experiments.
2. **0.3.82 stable listening baseline**: backup/android-0382-stable-listening-baseline-20261101, SHA 2e03aca1dad0f89b3d71f871270e09f8bb9f143f.
3. **Protected original 0.3.78**: backup/android-0378-original-before-cached-join-20261101, SHA bf011dcf1a70c504883a8e5e742e0b038f41d9b0.
4. Keep release/android-0.3.83-stable as previous reference.
5. The branch release/android-0.3.85-ota-download-fix is an EMPTY, unused branch created while diagnosing the intermittent updater. It contains no patch, build, or release; do not confuse it with audio staging.

Do not modify the backup branches. Use a NEW Android-only nonpublishing staging branch based on saved 0.3.84. Leave stable channel at 0.3.84 until owner approval.

## New owner evidence

Attachment filenames in ChatGPT:
- CELIKOM-combined-20261102-005314(1).txt, 3071 lines. Contains runs 0.3.82 / 0.3.83 / 0.3.84.
- SVID_20261102_005154_1(1).mp4, 74.879 seconds, 590x1280 H.264, AAC audio. Five tracks on HONOR Android 13.
- The 0.3.84 portion of combined log begins at line 2443; 629 events over ~71.7 s, partial run without run_end. Track sequence: Толер → Солнца не видно → Биг сити лайф → Он рядом → Крылья.
- Do not commit raw owner log/video into repository.

Measurements for 0.3.84:
- source_discontinuity userSeek=true: 22, but only 18 change position >1s; others are zero-to-zero transitions.
- replacement_seek_ack: 34 total, 25 ALIGNMENT + 9 WARM. 6/25 ALIGNMENT took >=250ms; max 751ms. WARM max 64ms in this sample.
- Two real replacement_stream_seek_data_wait events. Corresponding ALIGNMENT callbacks: 751ms (seekSeq 10 near 197.4s, event time ~21.54s) and 442ms (seekSeq 27 near 161.76s, ~58.16s). Four other slow ALIGNMENT ACKs lack explicit stream wait and need separate investigation.
- In data-wait events sourceEffectRetained=true and replacementSilent=true: original stays audible while replacement waits.
- staleOperation=true: zero in this run. The 0.3.84 superseded-in-flight-seek fix was not exercised in this user test. It cannot be considered a solution for usual lag.
- Five replacement_unified_join_start events all show audioSourceKind=stream and localPrewarmAttempted=false. This sample did NOT play from local cached files.
- New-track boundary to replacement_transition_complete was approximately 0.99s, 1.46s, 1.11s, 2.05s; initial song takeover ~1.82s after arming. These are command timing intervals, not measured speaker silence durations.
- sourcePcmMeasured=false, phaseVerified=false, hardwareOutputMeasured=false; replacement MediaPlayer.getTimestamp is available but source output timestamp unavailable. Transport/decoder cursor agreement does NOT prove clean acoustic handover.
- For context only: 0.3.82 run had 62 seek ACKs/max 2887ms across 8 tracks; 0.3.83 had 77/max 1173ms across 11 tracks. Do not infer quantitative improvement from maximum values across unequal tests.

Why recent releases did not fix it:
- 0.3.84 specifically fixes superseded ALIGNMENT ownership when a second Media3 seek arrives before an untagged native callback, with one seek in flight. See ANDROID-0384-SUPERSEDED-ALIGNMENT-SEEK-2026-11-01.md and TestHonor068SupersededAlignmentSeek.java.
- It does NOT speed HTTP Range or native MediaPlayer.seekTo, does not alter initial attachment timing, the source/decoder output relationship, or cache policy. Host fake tests cannot reproduce real HONOR streaming network/acoustics.
- Previous caching/prewarm experiments regressed Pause/other functions; review their precise evidence and protected backups before reusing anything. Do not blindly re-enable previous experimental implementation.
- Android official MediaPlayer API documents that asynchronous seekTo can take substantial time when streaming; verify official MediaPlayer, MediaDataSource, buffering, and timestamp behavior rather than treating transport positions as audible proof.

## Next technical plan — NO stable publication yet

1. Independently audit replacement code and real log timelines. Read android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/{ReplacementEngine,BufferedAudio,StreamingAudio,NativeApi,AudioOwnership,ClockSupervisor,SourceEventArbiter}.java and earlier caching regression reports. Reconstruct the true sequence around ~20.77–21.88s and ~57.70–58.31s of 0.3.84 plus 1–2s Next joins. Independently challenge the hypothesis and review official Android documentation.
2. Controlled A/B on isolated nonpublishing staging: **streaming replacement vs bounded local fully downloaded replacement**. Existing ReplacementEngine.downloadFull and MediaPlayer.setDataSource(file.getAbsolutePath()) can be reused. Only one targeted audio-data-path variable. Use automatic temporary private cache (NOT manual owner song downloads) and verify storage limits, cleanup, permissions, auth lease, file identity and release.
3. Measure user source seek → HTTP readAt/range wait → native seek request/ACK → output timestamp → gain/transition commands, and correlate with recorded audio carefully. Distinguish command-time proofs from actual acoustic output. Do not pretend speaker PCM is measured when it is not.
4. Criteria: once replacement is locally available, no hundreds-of-ms network wait on local seeks, latest finger position followed, no audible original fragments/dips, no worse intro/Next, Pause/Stop/Bluetooth unaffected, no security/storage regression. Host tests, Android API36/D8, signed APK provenance and CI before ANY owner test.
5. If full file removes seek lag but worsens startup, study **hybrid**: streaming starts immediately, concurrently materialize authorized replacement for subsequent local seeks; separately measure and constrain network, storage and readiness. Do NOT claim full download can make the first note instant.
6. ONE owner HONOR retest only after staging candidate convincingly passes. Stable publishing requires explicit owner approval after evidence. Do not touch accepted OTA implementation, website, backend, catalogue or accounts.

**Handoff instruction:** Stop the release treadmill. Prove or disprove whether network-backed MediaDataSource is the dominant seek bottleneck with one isolated A/B. Separately investigate slow new-track ownership/joins and genuine audible output. Do not patch random timing constants.
