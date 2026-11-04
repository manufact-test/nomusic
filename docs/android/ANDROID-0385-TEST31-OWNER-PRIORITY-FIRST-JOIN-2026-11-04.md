# CELIKOM Test.31 — owner-priority first-song crossfade and CI/production parity (2026-11-04)

## Owner correction and root cause

The owner explicitly rejected spending another cycle on already-improved initial **load time** or exclusively on RASKOL/«Дым» seeks. The top priority is the audible **«пшик»/volume break on the FIRST original→replacement connection on arbitrary songs**. Test.30's technical improvements did not fix that acoustic issue. Do not mislabel first-join **audio continuity** as first-join **latency**.

Code inspection exposed a deterministic discrepancy: the production `ReplacementEngine` constructor had `coldJoinExclusiveExperiment=true`, whereas the host `TestEngine.reset()` **unconditionally forced `coldJoinExclusiveExperiment=false`**. This meant the main suite exercised the 160ms complementary crossfade (`original=1-mix`, `replacement=mix`) while the real Android Test.30 selected an exclusive 32ms original duck followed by a 48ms decoder rise, with an intentional near-silent notch. CI green was therefore not validation of the production first-join envelope. This is an application/test design error, not a Yandex attribution.

## Exact scope of Test.31

1. The actual Test APK now defaults to the original, single-timed **160ms complementary linear crossfade**. At mathematical midpoint both source and replacement are commanded at 50% scalar (subject to destination gain cap). No intentionally non-overlapping source-duck/decoder-rise valley remains in default first joins, whether local cached file or sparse/streaming.
2. Remove the host-only assignment that overrode the production constructor. The default host path must be the same as the installed APK. A new regression exercises the **unconfigured** default full-file cold path and asserts both `replacement_unified_join_start` and `replacement_join_transport_summary`, and the absence of `replacement_exclusive_soft_join_start`. A static architecture gate rejects future silent constructor/host divergence.
3. The 32/48ms experimental function remains **explicit opt-in in a named host comparison** only; no user setting, second controller, new permission or playback branch selector. This experiment is NOT enabled in the APK.
4. Keep Test.30's locally cached hot-seek safety, transport/session gating, existing preparation/lookahead and initial loading pipeline **unchanged**. Preserve pause/seek source-fallback when Media3 lacks the event; do not claim RASKOL/«Дым» fixed.
5. `0.3.85-test.31`, `versionCode=86116`, isolated package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, original signer, separate branch `feature/android-0385-test31-first-join-complementary-20261104`, SDK36/D8/host full CI and byte-identical signed APK Library delivery required. No stable package, code86, Hostinger OTA or signed original backups touched.

**Limit:** linear complementary gains *remove the commanded audio valley* but do **not guarantee** artifact-free acoustic joins between independently clocked/mixed recordings. With unmeasured PCM phase, 50/50 can attenuate or reinforce correlated sounds; the synthetic signal-level regression demonstrates counterexamples. Therefore Test.31 is **not owner-accepted** until one real phone listen test. No more claims that green CI proves a seamless song transition.

## Immutable rollback pins

* Test.23 owner-accepted branch `backup/android-0385-test23-owner-accepted-20261104`, source `251b6facc8739557ff962365da012d502ed3bac8`, original signed APK `libfile_301d98360e9c8191b8e05594f402d265`, SHA256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`.
* Test.28 interim owner-selected branch `backup/android-0385-test28-owner-selected-20261104`, source `904ba52d5afbb5e77f4ee36e40d321d568896460`, original signed APK `libfile_dbc76474748481918f72b91a9eaea383`, SHA256 `973ee8565170d333c2ad7a8319f66c099c4afc2388228d3833562ffde7361b12`.
* Test.30 unverified functional SHA `6a2e8a8028115c9bf45ab9a824f70ce7eeb18ab3`, original signed APK `libfile_a761c255493c8191b2411a066c9bef3a`, SHA256 `c59509312669ba61ac0048496c4848c13f5906ae3c25cb9ac3988ccc0115fb8b`. Test.30 is **not** owner-accepted; no backup branch created.

Android lower-versionCode reinstalls may require removing only the test package, or a new signed higher-code recovery APK. Source commit alone is not a full rollback; original signed binary matters.

## CI and signed artifact — complete, awaiting owner acoustic verdict

* **Exact source commit used in original signed APK:** `8f3bce6bb049d66ae1e30316ab4365bbd7c9f66b` on `feature/android-0385-test31-first-join-complementary-20261104`. Later documentation commits do not change the signed-source commit.
* **[Full GitHub Actions #41891216645 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41891216645)**, `native-android` and `build-celikom-test / build-test-app` both successful. Stable OTA jobs skipped.
* **Original CI artifact:** `13354631240`, archive `CELIKOM-Test-0.3.85-test.31-code-86116`.
* **[Direct original signed APK in ChatGPT Library](https://chatgpt.com/library?file_id=libfile_a4aa619bae1c819187d651fb9900ad05&account_id=personal)**, filename `CELIKOM-Android-0.3.85-TEST-31-FIRST-JOIN-CROSSFADE-SIGNED.apk`.
* **Independently checked APK SHA-256:** `124f45abad77cd70664f557161736fa76ac997b9c3f118f350665a9a2f326522`; size `8,808,601` bytes. This file was extracted unchanged from the CI ZIP and saved to Library byte-for-byte, **not recompiled**.
* **Original signer SHA-256:** `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` matches reference; APK signature v3 verified. Test-only package `pro.celikom.nativeprobe.test`, `0.3.85-test.31`, versionCode `86116`, label `CELIKOM Test`.
* The original CI receipt and APK verification JSON are bundled in the GitHub Actions artifact. `stable_published=false`, `stable_ota_touched=false`, `hostinger_write_performed=false`, `physical_phone_playback_verified=false`.
* **Owner phone audio verdict still PENDING.** Do not create any new owner-approved backup branch or present Test.31 as a verified seamless first join without listening evidence.
