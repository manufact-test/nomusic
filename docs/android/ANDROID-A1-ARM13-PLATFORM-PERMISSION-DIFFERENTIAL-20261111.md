# CELIKOM Android A1 — ARM13 public OS permission differential, 11 November 2026

Status: Stage A NO-GO, Stage B locked. Main owner A; GitHub issue #41.

## New, testable hypothesis (NOT an established cause)

Previous ARM13 runs proved clone MAIN EXIT_SELF(0) in all three independently signed layouts and original publisher-signed MAIN survives. The previous log parser looked primarily at MAIN-PID messages. Android OS permission denials can be emitted by system services under other PIDs. Equally importantly, requested permission in a manifest is NOT the same thing as a granted install or runtime permission. Android explicitly documents this difference:
https://android.googlesource.com/platform/frameworks/base/+/android13-release/core/java/android/permission/Permissions.md

We now instrument OS-facing, read-only information without modifying a publisher APK, granting a permission or bypassing Android security.

## Delivered scope

- New android/native-yandex-hooklab/native_arm13_platform_contract.py parser + deterministic unit tests in tests/test_native_arm13_platform_contract.py.
- Existing three-layout ARM13 A/B observes dumpsys package (requested, granted install, User 0 runtime) at each clone install, plus signed original and clone after original install. Only finite counts by Android/Yandex/Google/other permission family, and fixed-category status for the publicly named READ_CREDENTIALS permission leave memory.
- Compares originally granted and independently signed clone missing grants only for permissions requested by BOTH. Separates explicit denied from not listed. This is diagnostic evidence, never a recommendation to grant signature privileges.
- Existing start() now checks system log buffer warnings/errors by trusted system tag and strict exact target-package mention, rejects helper/subpackage lookalikes and ambiguous two-package lines. Raw OS/package text, PIDs, user data, file paths, exceptions and accounts are never printed.
- Existing native ARM13 workflow runs synthetic tests BEFORE guest installation; workflow existing strict native MAIN gate still fails unless clone actually stays alive. A passing unit test is not product success.

## Engineering interpretation and guardrails

A grant difference or a system-service permission denial may identify a narrower class of problems, but does NOT prove the reason for EXIT_SELF(0), demonstrate a publisher signature check, or give permission to defeat one. Lack of a marker is also not absence of a denial. No APK available for owner, no user-device test, no login, no playable audio and no owner acceptance.

This is a SINGLE genuinely new OS/system diagnostic witness, not another default ART overflow capture or 10ms sampled-stack repeat. Retest only once if structural tests pass. If inconclusive, stop this probe rather than generate repeated cloned-layout CI failures.

Verified initial source and exact backup: 76cc47d086d1404eef95dd6bf199d6bce84f83ef;
backup/android-a1-before-platform-permission-differential-20261111.

No writes to Test.50, Windows W61, extension, server, production, owner phone, original Yandex, Play Protect, auth/DRM; no contact with Yandex. Helper B works solely on its audio contract branch; only A may merge a reviewed PR.


## Actual ARM13 execution: measured outcome (CI 43016902789)

Source SHA f8752077bf7f82fb215b9a1491c28a8c1e0726f6; native ARM13 Redroid disposable guest. Structural unit suites: 20+7+8 NEW+17+6+4 = 62 tests PASS, syntax PASS, true ARM guest boot PASS. Product CI overall FAILURE by deliberate strict clone MAIN gate: all three clone layouts still exact MAIN EXIT_SELF(0), original publisher-signed MAIN alive. No playable Yandex clone or owner APK.

PackageManager observations (unmodified original and independently signed clone):
- Every layout requests 34 permissions: Android 25, Yandex 3, Google 3, other 3. Clone before original installation: 16 granted Android install rights, zero granted Yandex; focus READ_CREDENTIALS is requested but NOT_LISTED in install grants.
- After installing the signed original: original 16 Android plus TWO Yandex install grants. Independently signed LSPatch-zero clone has the same 16 Android grants and TWO Yandex explicit denied grants, one the public focus READ_CREDENTIALS. The 34 shared requested names are identical.
- Newly scoped public OS system log shows ZERO exact-package permission/component/AppOps/security denial categories for five-split, merged direct, LSPatch-zero clone and surviving original. Zero markers does not establish absence of all denials.

**CRITICAL causal limitation:** all three clones EXIT_SELF(0) *before original installation* in this A/B run, when their two Yandex permissions are not listed rather than explicitly denied. The subsequent permission mismatch is real OS behavior but is NOT demonstrated to trigger self-exit. Historical signed-manifest static audit ALREADY showed both original custom permission declarations are signature protected and READ_CREDENTIALS does not occur as a literal in six DEX:
docs/android/ANDROID-NATIVE-SIGNATURE-PERMISSION-INSTALL-ONLY-2026-11-09.md.
Do not duplicate this experiment or use it to justify grant spoofing / weakening / app identity bypass.

Next valid path is a genuinely new independently grounded, authorized native integration witness. AOSP visibility cannot force a separately signed app to hold issuer-signature permissions. If no authorized embedding contract exists and the owner forbids publisher contact / architectural change, this is an unresolved external technical and rights dependency, not a fixable CI quality gate.

Privacy: only bounded summary JSON emitted, no raw logcat/dumpsys, PIDs, token, account or publisher binary artifacts. Original device, Play Protect, Test.50, Windows and production untouched.
