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
