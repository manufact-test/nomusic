# CELIKOM Android 0.3.85 — intro/join investigation handoff (2026-11-02)

## Current owner verdict — two issues remain open

The owner has now tested the published **0.3.85 / versionCode 86** on the HONOR phone and reports:

1. **Seeking is accepted as fixed for the tested scenarios.** Ordinary in-song finger seeking is now smooth, including after pressing Next. The owner did not recall a single seek lag during this retest.
2. **Song beginnings / replacement joins are much better, but not finished.** The first seconds still sound wrong or uneven on some songs; the severity varies by track. In some tracks the join is almost imperceptible, in others it remains clearly audible. This is not acceptable as a final result, especially for listening in a car or headphones.
3. **Yandex Music's own crossfade setting is currently OFF.** First make CELIKOM's new-song beginning/join reliable with Yandex crossfade disabled. Only after that is accepted, enable Yandex crossfade and run a separate compatibility test with both transition systems active.

The owner estimates the overall work at roughly **70% complete**. This is the owner's project estimate, not a measured engineering metric. Do not describe CELIKOM audio as finished or 100% accepted.

## Production/release state

- Published Android: **0.3.85**, versionCode **86**.
- Package: `pro.celikom.nativeprobe`.
- The owner installed and listened through the existing in-app update flow.
- Last release receipt: [ANDROID-0385-LOCAL-FILE-OTA-RELEASE-RECEIPT-2026-11-02.md](ANDROID-0385-LOCAL-FILE-OTA-RELEASE-RECEIPT-2026-11-02.md).
- Release CI: [#41358568513](https://github.com/manufact-test/nomusic/actions/runs/41358568513), successful signed Android build and Hostinger publication.
- Published APK SHA-256: `e23c962d969129c5b839ed3676e36d6a337342e2761bde852e2048bbf1bda88a`.
- Original signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Do not change the updater or publish a new stable APK merely because CI is green. No new APK is requested at this checkpoint.

## Owner decision — build a second, side-by-side test app

The owner explicitly approved a **fully separate Android application**, installed alongside stable CELIKOM 0.3.85. The next chat must build one signed installable **CELIKOM Test** APK for the exclusive cold-join candidate. It must not update or replace stable CELIKOM.

Read and follow [ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md](ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md) as the exact build specification. Proposed test package: `pro.celikom.nativeprobe.test`; label `CELIKOM Test`; test version `0.3.85-test` / code `86085`; use the original signing certificate. A distinct package ID provides a separate Android app sandbox and permits both apps to remain installed. Do not globally rename Java class namespaces.

The test app must not instantiate `UpdateCenter`, schedule `UpdateCheckJob`, include `UpdateInstallReceiver`/`REQUEST_INSTALL_PACKAGES`, or fetch the stable manifest. The existing `test_only` workflow is not suitable as-is because it still builds stable package `pro.celikom.nativeprobe`. Use a dedicated test builder/verifier and a manually dispatched, nonpublishing GitHub Actions artifact workflow. Do not upload to Hostinger or alter stable `release-spec.json`, `release_contract.py`, `verify_release.py`, `stable.json`, signing identity, or OTA behavior. Keep PR #37 draft/unmerged.

The owner will stop stable CELIKOM before running CELIKOM Test; never run both audio engines simultaneously against the same Yandex session. Keep Yandex crossfade OFF and request only one short listening check of one or two new-track starts. Do not repeat the accepted seek test.

## Accepted seek baseline — do not disturb

The exact functional source corresponding to the accepted 0.3.85 APK is commit:

`053b7d59beb53db5f30b942feba35e51a1ab256a`

Two backup refs point to that exact commit:

- `backup/android-0385-honor-seek-accepted-20261102`
- `backup/android-0385-honor-seek-accepted-recovery-20261102`

Older checkpoints remain:

- `backup/android-0384-before-local-seek-experiment-20261102` → `d434d442aeed7a84f17126da48c6a08b752c825d`
- `backup/android-0382-stable-listening-baseline-20261101` → `2e03aca1dad0f89b3d71f871270e09f8bb9f143f`
- `backup/android-0378-original-before-cached-join-20261101` → `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`

The current documentation/guard merge is `ee04be8bf239ae52417ece07b2a9a88d5ea028a1` on `feature/android-unified-preparation-seek-gate`. PR [#36](https://github.com/manufact-test/nomusic/pull/36) is merged; post-merge CI [#41406096811](https://github.com/manufact-test/nomusic/actions/runs/41406096811) succeeded. PR #36 changed tests/docs, not the shipped audio implementation. The separate intro investigation branch was created from this exact current HEAD:

`feature/android-0385-intro-join-investigation-20261102`

It now contains one isolated candidate: only prewarmed local full-file cold/new-track joins use an exclusive single-turn handover after the existing clock gate. Same-song seek submission/ACK, Pause/Resume, Next routing, streaming joins, and duration policy remain unchanged. Draft PR [#37](https://github.com/manufact-test/nomusic/pull/37) is open and unmerged. Android CI [#41419113128](https://github.com/manufact-test/nomusic/actions/runs/41419113128) passed, including 32 cold-join experiment checks, the full native host suite, the accepted 0.3.85 seek golden guard, Android API 36 and D8. Publisher and test-candidate jobs were skipped; no signed APK was built and the stable OTA remains 0.3.85/code86. This is the only branch for intro/join experiments. Do not push experiments directly to `feature/android-unified-preparation-seek-gate`: its workflow is the stable publishing path. Do not merge or publish an APK without the owner's explicit approval after listening.

### Important honesty about GitHub backup protection

GitHub currently reports `protected=false` for the backup branches. The backup refs exist and both 0.3.85 refs point to the exact full-repository commit above, but they are **not configured GitHub protected branches**. Do not call them branch-protected or cryptographically immutable. Never force-push, delete, or repoint them. The commit SHA identifies the complete saved repository tree; use that exact SHA for a full-source restore, not selected old Java files copied into a later tree.

## What the 0.3.85 experiment changed

The controlled experiment changed the replacement data path on a cache miss:

- CELIKOM automatically downloads the complete authorized replacement into its private app cache.
- It uses the existing `ReplacementEngine.downloadFull` / `NativeApi.download` path and the existing `MediaPlayer.setDataSource(file.getAbsolutePath())` local-file path.
- The existing player/engine is reused; no second music engine was introduced.
- The transfer has the existing 30 MiB ceiling and an experimental 20-second validity budget.
- The existing join, local decoder prewarm, seek, Pause, Next, Stop, gain/ownership and fade rules were not intentionally retuned by this experiment.
- No manual user download or public music-library file is involved.

The 0.3.85 owner journal (private; raw file must not be committed) showed:

- 30 actual same-item source position jumps.
- 36 ALIGNMENT acknowledgements, median 41 ms, maximum 86 ms, none >=250 ms.
- 41/41 replacement seek acknowledgements used `full_download_file`; zero stream seek-data waits.
- Eight full-file download/join sequences took 1,255–4,592 ms.
- Seven local decoder prewarm-motion observations took 132–219 ms.
- The journal does not contain original-source PCM or measured speaker-output phase. These are transport/decoder/command timings, not proof of the actual waveform from the speaker.

This is consistent with the owner's strong seek improvement. It does **not** establish that the intro/join is solved. Full-file download latency, local decoder preparation, clock readiness, ownership/gain handover, and the interaction of two transition systems remain separate possible contributors.

## Next work — strictly limited scope

The owner has supplied the combined journal `CELIKOM-combined-20261102-105708.txt` and HONOR recording `SVID_20261102_105501_1.mp4`; see [ANDROID-0385-HONOR-INTRO-JOIN-AUDIO-VIDEO-CORRELATION-2026-11-02.md](ANDROID-0385-HONOR-INTRO-JOIN-AUDIO-VIDEO-CORRELATION-2026-11-02.md). The recording shows a near-silent AAC interval around 59.1–60.0 s, before the new CELIKOM join; it begins before CELIKOM's old-decoder cleanup and ends before the new join. The screen appears to show a Next tap, but Media3 cannot confirm the physical button action. Do not claim the interval is conclusively Yandex-originated or a CELIKOM fade defect. The source-vs-speaker PCM is unavailable.

1. The required documentation review and owner evidence correlation are complete. Keep the linked 0.3.85 freeze, controlled experiment, OTA receipt, cache-path/prewarm, Media3 event-correlation and exact rollback documents as the reference set for any further work.
2. The supplied recording contains an AAC audio track and its signal level was measured, but it is not calibrated speaker PCM and does not separate Yandex from CELIKOM output. Keep that limitation explicit.
3. Reconstruct only the problematic new-track boundaries: full download start/end, file validation, local MediaPlayer creation/prepare, prewarm/decoder motion, clock gate, AudioOwnership/gain commands, fade start/end, and transition completion. Correlate the event timeline with the audible recording. Distinguish measured facts from hypotheses.
4. Separate at least these candidate causes: full-file download/readiness delay; local decoder preparation or first-buffer delay; decoder-clock gate; source/replacement ownership and gain handover; content/encoding offset; CELIKOM's own fade; and any interaction with Yandex Music's transition setting.
5. **First phase:** the first falsifiable experiment is implemented: exclusive cold/new-track handover for prewarmed local full-file joins, after the same clock gate. It has passed host/Android CI. The candidate still needs one short HONOR listening test; do not infer acoustic success from CI.
6. **Second phase:** only after the owner accepts the intro with Yandex crossfade OFF, ask the owner to enable Yandex crossfade and test the interaction separately. Determine whether Yandex crossfade and CELIKOM's join overlap, compound, or expose a separate timing issue.
7. Regression tests and Android CI passed in run #41419113128. A successful host/CI test is not acoustic acceptance. Do not issue repeated broad test requests or ask for another seek retest.

## Hard freeze boundaries

Do not change, refactor, or replace these accepted behaviors while investigating intros:

- `ReplacementEngine.seek(...)` accepted finger-seek submission path.
- `ReplacementEngine.completeSeek(...)` asynchronous seek completion/ACK path.
- Full-file local source selection and production default.
- Local-file seek behavior and its cache/read path.
- Pause/Resume, Next, Stop, Bluetooth/audio session behavior, AudioOwnership and gain policy unless the supplied evidence proves a specific intro-only defect and the owner approves a separately isolated change.
- Existing Android OTA/update code, signing configuration, Hostinger publisher, backend, website, browser extension, catalogue, accounts or databases.

The required guard is `android/native-companion/tests/check_0385_seek_baseline.py`. It fingerprints the accepted seek method, async completion method, and full-file source-selection block, and checks the production constructor's local-file default. Keep it enabled. Do not weaken/delete/update its fingerprints merely to make CI pass. It is a focused regression tripwire, not a complete lock on all audio code and not a substitute for owner listening.

## Full rollback procedure if a later APK regresses

The exact saved full-repository source is commit `053b7d59beb53db5f30b942feba35e51a1ab256a`, referenced by both backup branches above. To restore the complete 0.3.85 implementation after a later version has been installed:

1. Start from that exact commit/tree. Do not cherry-pick only `ReplacementEngine.java` or copy a handful of old methods into a later project.
2. Preserve the original signing certificate and all existing build inputs.
3. Because the currently published/installed code is 86 and the OTA publisher refuses a versionCode downgrade, set a **new versionCode greater than 86** (for example 87; choose the version name only when actually preparing the recovery build). Change release metadata only; keep the 0.3.85 product/audio source tree intact.
4. Rebuild and sign using the original certificate, verify package identity/signature/DEX/APK SHA, publish the immutable APK, then atomically update and verify `stable.json`.
5. Install through the normal in-app update button and confirm the restored behavior on HONOR.

This is a full source-tree rollback delivered as a newer Android package, not an attempt to install code 86 over code 87. New experimental work must remain on its isolated branch so the recovery points remain untouched.

## Owner's next action

The owner has approved the side-by-side test build. Build and verify `CELIKOM Test` first, following the dedicated build handoff. After delivery, the owner will install it alongside stable CELIKOM, stop/close stable CELIKOM, and perform one short HONOR listening comparison of one or two representative cold/new-track joins with Yandex crossfade still OFF. Do not repeat the accepted finger-seek test. The near-silent pre-join interval is a separate open question; this experiment is not expected to fix it. Phase two (Yandex crossfade ON) remains deferred until phase one is acoustically accepted.
