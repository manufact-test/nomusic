# CELIKOM Android 0.3.85-test.67 — isolated HONOR tuning candidate

## Input
Owner diagnosis `CELIKOM-combined-20261108-172101.txt`. The new Test.66 run starts 2026-11-08T17:19:19+03:00. Older Test.64 and Test.65 segments excluded from current-run fault classification. [Evidence and timing](ANDROID-TEST66-HONOR-172101-ANALYSIS-2026-11-08.md).

## Changes in this separate Android-only branch
1. Approved-only NO_MATCH **in the collapsed Android notification while playing**, exact text `Нет одобренной версии · играет оригинал` (39 chars). It must NOT say `на модерации` without server confirmation; the Activity keeps the full approved-only wording. Paused/missing/ambiguous/stale states and suggestion permission rules untouched.
2. Test.66 «Розовое вино» 3067ms: long successor file (246810ms) was promoted while downloading about 2.3s after prefetch start; after 400ms wait it still required verified sparse cold start (stream ready ~1542ms later). Experimental **bounded** 200ms current handoff wait only when progressive is on, duration >=240000ms, phase downloading and speculative prefetch age 1800..2599ms. Older mature downloads retain existing 400ms, short tracks 1200ms, frozen/non-progressive 10000ms. The existing cancellation, fresh resolve authorization, generation and source guards remain intact. No fade/seek/PCM/effect ownership code changes. Numerical real HONOR improvement is **not confirmed**; a speculative transfer may occasionally complete in the 200ms that this experimental fast fallback skips. Test.45 handoff at prefetch age ~1100ms retains its original 400ms wait.
3. Tests for approved-only notice and short/long/frozen waiting boundaries; existing RASKOL and source buffering tests remain. **RASKOL pause/seek and «Дым» BUFFERING still unconfirmed on Test.66, do not declare repaired**.

## Isolation and release
Dedicated branch `feature/android-0385-test66-compact-notification-honor-20261108`, Test.67 package `pro.celikom.nativeprobe.test`, version code 86153. Stable Android 0.3.92, golden Test.50 sound, main, backend, OTA, desktop and other branches untouched. Full CI/Android D8, signing, verifier, Library upload required before any user APK. Physical HONOR confirmation of sound/status/latency required after delivery. No stable promotion.

## Completed CI, signed delivery (2026-11-08)
- Source SHA **afb6124c495fb4f28959fe44f105c099f28621bd** (the validated, signed functional source; subsequent docs-only commits do not change the APK).
- [GitHub Actions #42490751547](https://github.com/manufact-test/nomusic/actions/runs/42490751547) **SUCCESS**, including full host engine regression, Android API36/D8, offline signing, verifier, isolated package and stable/OTA absence.
- Android Test.67 / code 86153, file **CELIKOM-Android-0.3.85-TEST-67-HONOR-TUNING-SIGNED.apk**, SHA256 **d6512571edd8c6623e116bfd7dffe75d91d658708619c16cb41990277ae24ef1**, original signer certificate **67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f** matched; Android **v3 true**, v2 false (same as source APK), non-allowlisted assets unchanged; fresh approved catalogue **158 tracks** injected as the only allowed asset update.
- Library permanent: [signed APK Test.67](https://chatgpt.com/library?file_id=libfile_bb11fa3c37f48191b2ea98e6f5669c4d&account_id=personal) under `/CELIKOM/Android/Test/`. [verification.json](https://chatgpt.com/library?file_id=libfile_d82eeef302748191b4993844fbdbea7c&account_id=personal) and [RECEIPT.json](https://chatgpt.com/library?file_id=libfile_b65c717e982c81918902c68cbeb87668&account_id=personal) uploaded alongside it.
- [GitHub build artifact #13621760878](https://github.com/manufact-test/nomusic/actions/runs/42490751547/artifacts/13621760878) temporary; Library is persistent.
- Physical phone Test.67 evaluation **NOT YET DONE**. Do not promote as stable or claim acoustics/speed fixed based on CI.
