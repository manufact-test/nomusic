# CELIKOM Test.30 — conservative verified-cache in-player seeking (2026-11-04)

## Owner context and status

The owner rejected Test.29 on HONOR: RASKOL and «Дым» still lagged, song joins regressed, and audible handoffs persisted. The *fresh* Test.29 session begins at line 4325 of the private `CELIKOM-combined-20261104-185701.txt`; older sessions in that file must not be blended into the conclusion. The paired video is `SVID_20261104_185426_1.mp4`.

Test.29 source/CI may remain for forensic comparison but it is **not owner accepted**. Test.30 is an **unverified experiment**, not a certified acoustic fix. Read `ANDROID-0385-TEST29-OWNER-REJECTED-ARCHITECTURE-POSTMORTEM-2026-11-04.md` first.

## Mechanism

* Test.29's speculative four-block 512 KiB Range batches were removed; Range fetches again stay at 128 KiB. This is a rollback of an unverified change, not a claim that it alone repairs latency.
* `BufferedAudio.hasVerifiedSeekNeighborhood` requires the fully cached file, or a verified byte neighborhood around the target in an incomplete stream. An unverified/network-dependent seek keeps the old original-audible fallback.
* A *verified local seek* after CELIKOM has already become the sole audible owner can call `MediaPlayer.seekTo` in the same decoder without clearing its volume, unmuting Yandex, detaching DSP or restarting a join envelope. It is **not** the historically rejected muted-source timer: no intentional dual silence is inserted for the cached path.
* Only one untagged native seek callback is outstanding; rapid finger scrubs coalesce to the latest target and have at most one local correction. On timeout, retire the decoder and restore the source, rather than interpret a late native callback as belonging to another seek.
* A transient HONOR `!playing` sample **during** a hot cached seek must immediately silence/pause the replacement but retain the decoder until that same seek callback drains. Once drained, stay paused if the source remains paused; if the source resumed, align using the ordinary safe path. This preserves Test.23's pause/resume requirement and fixes the failed first Test.30 host regression (`TestEngine.java:104`).

## Build and scope

* Dedicated experiment branch: `feature/android-0385-test30-cached-seek-owner-20261104`.
* Test-only package: `pro.celikom.nativeprobe.test`; label `CELIKOM Test`.
* Version `0.3.85-test.30`, versionCode `86115`; old original signing identity must be checked in CI.
* No change to stable package `pro.celikom.nativeprobe`, original code86, Hostinger OTA or its release artifacts.
* No Notification Listener, Accessibility, microphone capture or independent second player controller.

## Evidence, limits and validation

* Fresh owner Test.29: «Дым» native seek callbacks around 51–72 ms still caused audible source-to-replacement transfers; first joins had median ~2 s and max ~6.3 s. RASKOL sparse-range seek callback of 1728 ms was **not** a decoder-command latency.
* Local checks: architecture gate, packaging gate and 4,158 standalone buffered-file checks passed on current source path.
* First Test.30 GitHub Action [#41881713158](https://github.com/manufact-test/nomusic/actions/runs/41881713158) **FAILED** at `TestEngine.java:104`: hot seeking retired the decoder during a source pause. Keep this failure in the record; it led to the pause retention change.
* Full end-to-end host / Android SDK 36 / D8 / APK-signature CI **SUCCEEDED** for the exact signed source commit below. Android on-device acoustic validation is separate and **PENDING OWNER REVIEW**; passing CI does not certify sound quality.
* The Media3 source sometimes publishes `isPlaying=true` while the Yandex user interface visibly shows pause, and sometimes does not publish a slider seek in time. A client observing only that Media3 state cannot faithfully respond to an event that is absent from its input. Test.30 does **not** fix this source-observability limit.

## Rollback pins (must remain untouched)

* Owner-accepted Test.23: backup `backup/android-0385-test23-owner-accepted-20261104`, source `251b6facc8739557ff962365da012d502ed3bac8`, original signed Library APK `libfile_301d98360e9c8191b8e05594f402d265`, APK SHA256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.
* Owner-selected interim Test.28: backup `backup/android-0385-test28-owner-selected-20261104`, source `904ba52d5afbb5e77f4ee36e40d321d568896460`, original signed Library APK `libfile_dbc76474748481918f72b91a9eaea383`, APK SHA256 `973ee8565170d333c2ad7a8319f66c099c4afc2388228d3833562ffde7361b12`.
* Android blocks a lower versionCode installed over a higher code; test-only restore can require uninstalling the test package or a newly signed recovery build with a higher code. A recompilation is not the byte-identical original APK.

## Signed artifact record — reproducible Test.30 trial

* **Exact functional/source commit used to build this original APK:** `6a2e8a8028115c9bf45ab9a824f70ce7eeb18ab3`. Documentation-only commits after this do **not** change signed source identity.
* **Successful complete CI:** [GitHub Actions #41886108264](https://github.com/manufact-test/nomusic/actions/runs/41886108264); original CI artifact `13351981041`.
* **Original byte-for-byte signed APK:** [CELIKOM-Android-0.3.85-TEST-30-CACHED-HOT-SEEK-SIGNED.apk in ChatGPT Library](https://chatgpt.com/library?file_id=libfile_a761c255493c8191b2411a066c9bef3a&account_id=personal).
* **APK SHA-256, independently verified against CI:** `c59509312669ba61ac0048496c4848c13f5906ae3c25cb9ac3988ccc0115fb8b` (8,808,601 bytes).
* **Verified APK signing certificate SHA-256:** `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; signature v3 present, original signer match `true`.
* **Package / version / code / label:** `pro.celikom.nativeprobe.test` / `0.3.85-test.30` / `86115` / `CELIKOM Test`.
* Full receipt: the CI-supplied `CELIKOM-Android-0.3.85-TEST-30-CACHED-HOT-SEEK-RECEIPT.json` and `.verification.json` accompanied the GitHub artifact. The APK in Library is the original signed binary from this run, not a locally recompiled approximation.
* **Owner listening review has NOT occurred. Do not designate Test.30 a preferred baseline or create an owner-accepted backup without explicit owner approval.** Preserve frozen Test.23 and Test.28 backup branches and original APKs as documented above. To install a lower-code version, Android may require removing **only** the test package or issuing a separate signed recovery build with a higher versionCode.
