# Test.50 — remember NEXT during current prepare (2026-11-06)

Baseline: Test.48 (not rejected Test.49). Input CELIKOM-combined-20261106-230322.txt, last run Test.49: 7 prefetch starts, 15 cold starts, 19 completed transitions; previous Test.48: 25 prefetch starts, 5 cold starts, 30 completed transitions. Distinct usage scenarios, not measured acoustic PCM.

Regression mechanism: on Test.49 after 60s, source_next_identity_resolution knows next track and source_next_readonly_boundary reports authorizedForPrefetch=true but prefetchStarted=false. prefetchLookahead discards a known next ID during current preparation; no replay arrives from source. New code queues candidate metadata (not audio) while foreground preparing and launches original prefetch only after exclusive current join; validates source key, next candidate, account, authentication; discards on boundary. No audio DSP, seek, timing, crossfade, source effect, permissions modified. Test.49 promoted lease guard is not carried forward.

New tests cover deferred next and stale next on source change. Keep stable 0.3.92, Test.48 and Test.33 unchanged; PC, Hostinger, backend untouched. CI APK still separate from stable OTA. Need signed CI and real HONOR listening for Next and shuffle before acceptance.

## Подтверждение подписанной Test.50
Source commit (code, not docs): `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`. CI run `42287196407`: native host regressions, Android API 36, D8, packaging/signature verification — PASS.
Test package: `pro.celikom.nativeprobe.test`, version `0.3.85-test.50`, code `86135`. Подпись APK v3 — verified, cert matches original. `stable_published=false`, `stable_ota_touched=false`.
Verified SHA256 APK: `aadedff2051cd40e96641cff1be831aa3a6a79c3938c2b849837b3e880b511d1` (8,829,081 bytes).
Library artifact: https://chatgpt.com/library?file_id=libfile_c9438555d1d08191831db3f76ecc9443&account_id=personal
CI: https://github.com/manufact-test/nomusic/actions/runs/42287196407
Caveat: GitHub artifact **folder** retained stale label Test.48 from workflow; the APK filename, cryptographic hash, metadata and signing report all verify Test.50. Do not confuse folder label with actual APK.
Physical HONOR audio acceptance: **not yet tested**. Test.49 is rejected as worse than Test.48. Do not promote Test.50 to stable until phone listening in manual Next/shuffle.
