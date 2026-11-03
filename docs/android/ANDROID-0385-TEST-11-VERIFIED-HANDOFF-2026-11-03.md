# CELIKOM Android — final Test.11 handoff before owner's diagnostic (2026-11-03)

## Exact working state

- Repository: https://github.com/manufact-test/nomusic
- Experiment branch: `feature/android-0385-intro-join-investigation-20261102`
- **Last validated functional commit:** `7cb3cc190d614dd23646fa9b64a233e5f91162d4`. Subsequent documentation-only commits, if any, do not change executable source. Preserve this exact functional checkpoint and its parent lineage.
- **Last full CI:** https://github.com/manufact-test/nomusic/actions/runs/41638455540 — **SUCCESS** (Android host regression, golden HONOR seek source hash, API36 compile/D8, separate side-by-side signed APK verification).
- **One-click GitHub ZIP download:** https://github.com/manufact-test/nomusic/actions/runs/41638455540/artifacts/13231786977 . Artifact name `CELIKOM-Test-0.3.85-test.11-code-86096`; APK inside `CELIKOM-Android-0.3.85-TEST-COMBINED-SEEK-INTRO-SIGNED.apk`. Signed APK SHA-256 **`dc3d1026948d4b8e5978a5d116d09ceb2b57ff2d7ca2b1c347d1e60e25a52089`**, size 8,788,121 bytes. Signature v3 verified; original certificate SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Test package: `pro.celikom.nativeprobe.test`, label **CELIKOM Test**, version `0.3.85-test.11`, code **86096**. OTA updater absent, distinct Android sandbox, no Hostinger write. Test.11 supersedes Test.10; **do not ask the owner to test both**.
- **Stable original remains published and untouched**: CELIKOM `0.3.85/code86`, package `pro.celikom.nativeprobe`, accepted baseline SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`. Hostinger stable.json/OTA, backup branches, historical accepted seek methods, Pause/Resume and PR#37 **not merged/not touched**. CI stable publishing job skipped.
- **Owner field verdict on Test.11: PENDING.** CI SUCCESS is not acoustic proof. No report or diagnostic from Test.11 has been received in this chat yet; the owner will bring it to the next chat.

## Why Test.11, and exactly what is in it

The owner specifically demanded **all viable changes in one APK**, with one listening pass and one combined diagnostic. Test.10 was an incomplete intermediate build. Do not issue another single-minor-fix APK unless a genuine blocker forces it.

**Confirmed Test.9 owner evidence:** private `CELIKOM-combined-20261103-150348.txt` + `SVID_20261103_150238_1.mp4` (earlier Test.7/Test.8 sessions are included in the same combined file; only the Test.9 session starting log line 3557 is fresh). On “Дым” by Лёша Свик (alias77), the on-screen Yandex slider visibly seeks toward ~3:16/3:39 but direct Media3 controller observations remain near 10 seconds. No Media3 `SAME_ITEM_SEEK` or CELIKOM seek request appears during that song. Other songs emit the normal source discontinuity and native seek ACK. This is a **missing/stale source position signal**, not a proven failure in the frozen `ReplacementEngine.seek()`/ACK methods. User says Test.9 felt slightly worse than Test.8, especially in some starts.

**Additional intro evidence:** for the same song, initial alignment ACK elapsed 23969ms, next effect attach 24237ms: an extra ~268ms near the old 250ms source observation period, followed by an unnecessary WARM correction. Other ready primes attached much faster. Test.9 had 8 primed decoders adopted and **zero** actual invocations of its 150ms promoted-prime wait. There is also one first-song `replacement_drift_unstable` at 19314ms, source-vs-decoder offset ~1087ms, which correctly restored original. Its cause is unproven; do not blind-rewrite clock supervision.

**Combined changes in Test.11** (source details in [ANDROID-0385-TEST-11-COMBINED-INTRO-SEEK-2026-11-03.md](ANDROID-0385-TEST-11-COMBINED-INTRO-SEEK-2026-11-03.md)):
1. Carries Test.10's optional **passive platform MediaBrowser/MediaController** source position: tries reading the same Yandex session independently of Media3. Only a matching title/artist/duration, fresh platform state, two observations over >=250ms and >=4-second disagreement may substitute a source position. Android APIs are read-only, no Accessibility/notification permission, no play/pause/seek command to Yandex. If the legacy browser is unavailable, original logic remains; if source confidence is lost **after** recovery, restore original.
2. Fixes a paused-state edge after a recovered platform seek: matching paused states can retain the verified original position for up to 5 minutes; beyond that, fail-closed rather than jump back.
3. **Bounded post-preparation fast source sampling**: initial check after 35ms and every 60ms for up to 1200ms **only** while current track, verified decoder ready, user arm/trusted session, playing, source identity matching, and source effect not yet attached. Ends immediately on grant, pause, track change, deadline or disarm. Normal 250ms service tick remains. This is an evidence-based attempt to reduce the 268ms wait at first-note joins. It makes no modification to native seek/ACK logic or audio gain/ownership/crossfade policy.
4. Added host tests for new fast sampling negative gates, independent position policy, and pause hold; verified against frozen seek hash, native host audio suite and Android API36/D8. Host fake generator updated; Test.11 CI passed.

## Owner constraints and priorities

- Communicate to owner **very briefly**, outcome first: *what found / what fixed / direct ZIP / what is needed*. No timing tables or speculative long explanations unless asked.
- Continue independently; do not stop after an investigative report if safe implementation and testing are still possible. **Batch all credible, interrelated fixes before asking for one test**. Sound takes priority over UI cosmetics.
- One mode, one side-by-side Test app, no A/B test modes. Do not touch stable `0.3.85/code86` or Hostinger/OTA; do not merge PR#37. Preserve working seek, Pause/Resume, Bluetooth/session safety and original restoration.
- HONOR NTH-NX9 Android13, Yandex Music 2026.09.5; Yandex setting `Плавный переход` is OFF for current comparison. Never treat mere Media3 transport-clock alignment as verified PCM/acoustic phase, or a green CI as successful listening.
- Never confuse a Yandex UI seek with an actual CELIKOM seek event without evidence; compare **fresh `run_start`** segments, not the concatenated historical events.
- If another Test APK is truly needed, retain test package `pro.celikom.nativeprobe.test` label `CELIKOM Test`, increment code >86096, sign with the original key via the existing validated GitHub Actions workflow, and provide a **direct single-click ZIP artifact URL**, not navigation instructions.

## Next chat — immediate task

1. Owner will provide **Test.11 combined diagnostic, possibly video, and short subjective verdict**. **Do not request reupload of previous Test.9 files unless genuinely necessary**.
2. Identify the latest `run_start` with `version=0.3.85-test.11` and compare within that run: `legacy_position_source_connected` vs `legacy_position_source_unavailable`; `source_seek_platform_disagreement` / `source_seek_platform_recovered` / `source_seek_platform_fail_closed`; `replacement_fast_join_poll_started`; `replacement_seek_request/ack`; source boundary → prewarm ACK → effect → handover; `replacement_drift_unstable` and source refresh. Correlate **actual video scrubbing** with Media3 and platform data. If the platform browser does not connect, this fallback could not have fixed the rare seek; report it directly.
3. Prioritize remaining acoustic first-note seam and abrupt/late handovers, occasional media-session fallback and any real new seek regression. Avoid theoretical changes unsupported by the new trace, but combine all safe fixes before another candidate.
4. Update documentation and direct GitHub ZIP only after a coherent, tested batch; never report a test app as accepted until the owner has listened on HONOR.

Reference: [NEXT-CHAT.md](NEXT-CHAT.md), [ANDROID-0385-HONOR-SEEK-ACCEPTED-FREEZE-2026-11-02.md](ANDROID-0385-HONOR-SEEK-ACCEPTED-FREEZE-2026-11-02.md), [ANDROID-0385-INTRO-JOIN-INVESTIGATION-HANDOFF-2026-11-02.md](ANDROID-0385-INTRO-JOIN-INVESTIGATION-HANDOFF-2026-11-02.md), [ANDROID-0385-TEST-10-LEGACY-POSITION-RECOVERY-2026-11-03.md](ANDROID-0385-TEST-10-LEGACY-POSITION-RECOVERY-2026-11-03.md).
