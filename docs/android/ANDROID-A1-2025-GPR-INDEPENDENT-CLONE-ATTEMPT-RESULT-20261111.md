# 2025 GPR original versus independently signed lab clone — observed result (11 Nov 2026)

The owner-supplied pristine 2025 GPR 16-split original is **verified**: [real signature CI 43090872523](https://github.com/manufact-test/nomusic/actions/runs/43090872523), [real native ARM13 original MAIN 75s CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430), 25/25 same MAIN PID and 25/25 Activity resumed. This is genuine original Yandex.Music ru.yandex.music, NOT CELIKOM's independent app.

## Separate controlled build attempt

Goal: without modifying original DEX/native code, create 16 independent-lab-signature, distinct-package ephemeral APK splits **only for native clone feasibility**, no distribution and no publisher signature/DRM bypass.

- Research branch experiment/android-a1-genuine2025-original-vs-own-clone-20261111. Exact prior preserved original success backup: backup/android-a1-owner-gpr-2025-16issuer-native75-pass-20261111.
- [Native clone CI 43092662299](https://github.com/manufact-test/nomusic/actions/runs/43092662299): FAIL at rebuild with Apktool RESOURCE_DECODE_FAILURE; clean ARM13 guest booted successfully but no lab clone was installed/launched.
- [Native clone CI 43092999958](https://github.com/manufact-test/nomusic/actions/runs/43092999958): tried existing pinned ARSCLib/APKEditor resource path (used elsewhere in this project); full lab signature validation was **NOT verified**, fixed category OWN_CLONE_SIGNATURE_NOT_VERIFIED. No clone installed or launched.
- [Native clone CI 43093361498](https://github.com/manufact-test/nomusic/actions/runs/43093361498): additional ordinary v1/v2/v3 lab signing compatibility trial resulted in the SAME OWN_CLONE_SIGNATURE_NOT_VERIFIED. No clone installed or launched.
- The failed lab APKs, original XAPK and build keys were disposed within each Actions runner. GitHub release stays unpublished. Owner's HONOR 50, accepted Android Test.50, Windows, extension, backend, official installed Yandex, main A1 branch were untouched.

**Do not misread signed ORIGINAL success as independently signed CLONE success.** The experimental clone reached no live PackageManager or MAIN stage. Build/signing incompatibility remains a distinct earlier blocker from the previously established 2026 clone MAIN EXIT_SELF(0); do not conflate them. No signature/DRM bypass was used, authorized, or verified.

**A1 Stage A remains NO-GO; Stage B locked.** Do not rerun the same three clone packaging attempts blindly, weaken signature requirements, claim audio/GUI proof, publish a binary, or contact Yandex without owner direction. New work requires an independently justified, permitted technical approach, or an explicit user-approved architecture/rights decision.
