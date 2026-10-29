# CELIKOM Android 0.3.52 — structural packaging smoke / NOT SIGNED

Date: 29 October 2026. Repo: `manufact-test/nomusic`, branch `feature/android-0348-audio-ownership-stabilization`. Latest code checkpoint before docs: `04a583a5d32a29aa96f5a61aebd8bbbe892b92c9`; GitHub CI https://github.com/manufact-test/nomusic/actions/runs/40937933292 is **SUCCESS**. PR #22 remains draft; issue #20 remains open.

## Input authenticity

- Recovered local original toolchain from private Library archive `CELIKOM-Android-Build-Environment-20261029.tar.gz`, archive SHA-256 `ac9710ba416af3895350b94c83b09ad48a67da212d2fafbf5e65736a4018aa6e`.
- Proven baseline `CELIKOM-0.3.22-install.apk` SHA-256 `170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9`.
- Exactly pinned `annotation.jar`, `common.jar`, `guava.jar`, `json.jar` and `session.jar`: SHA-256 matched `android/native-companion/build-inputs.json`. Android platform API 36.
- Actual Apktool 2.11.1 JAR SHA-256 `56d59c524fc764263ba8d345754d8daf55b1887818b15cd3b594f555d249e2db`. The release build now refuses any other Apktool binary and requires JDK17 and Android API36.
- SHA-verified original 0.3.22 and last signed 0.3.51 both passed `apksigner verify` v3 and had matching signer SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. This proves certificate identity of historical packages, **not** access to the private signing key.

## Actual structural packaging test

1. GitHub Actions compiled all actual addon source against API36 with JDK17, ran main host test suite, 16 native addon checks, pinned JAR hash checks, and D8. GitHub offline-kit artifact came from commit `d0c1ad961e95d6d0d644afed785bb2cbb2cf2e43` (there are no later changes to Android .java files through `04a583a5`).
2. On local Linux, a **temporary unsigned-only inspection copy** of the official build script decoded the SHA-pinned real 0.3.22 APK, applied 0.3.52/versionCode 53 plus the existing approved manifest modifications, ran the source/audio regressions and Java/Android checks, and completed `apktool b`. First attempt discovered the real indented Apktool `versionInfo:` format; the patch and matching negative tests were committed as `c9723867`. The packaging then completed successfully.
3. The local Java runtime was JDK21, so its DEX differed from CI JDK17. For the final structural package, `classes2.dex` was replaced with the **byte-identical CI JDK17 DEX** from GitHub Actions; its SHA-256 is `8683a9f50fc2d1171206e0a803fe9f730c8e67f709909dcacecd67fa916ade98`. No production source was altered.
4. The aligned structural package was checked: APK version `0.3.52`, `versionCode 53`, minSDK28, targetSDK36, `zipalign -c 4` PASS, exactly `classes.dex` and `classes2.dex`, no duplicate ZIP members, all baseline catalogue assets byte-identical, recovery-source ZIP and signing/development files absent, and expected code markers including `AudioOwnership`, `ClockSupervisor`, `SourceEventArbiter` and `retireDecoder` present.
5. Local unsigned smoke file SHA-256 `fa8f4ee6a9390fa49cda4abd8b96fccde6d638160198a8881e36cd14165a0c49`, size 8,669,686 bytes. It is **NOT INSTALLABLE/RELEASED**, not included in Git, and must not be offered as the signed next APK. The actual `verify_release.py` was executed on an unsigned variant and **failed closed** at `apksigner verify`, which is the intended negative result.

## Remaining blockers

There is **no available original `celikom-native-probe.p12` and `signing.json`** in this runtime. The recovered toolchain archive explicitly excludes signing credentials. Do NOT create a new signer; that would break same-app updates and violate the pinned certificate contract. A real 0.3.52 release must be compiled on JDK17 using `build_release.py` with the original private signing material supplied only to the isolated offline signing directory. Run complete `verify_release.py` on the **signed APK**, compare signer to both historical app and pinned SHA, recheck asset/manifest/version/DEX and keep sensitive files out of Git or shared archives. Only then is it meaningful to request one physical listening test on HONOR/Bluetooth. Nothing here proves acoustic zero-overlap or user acceptance.

Backup before work: `backup/android-before-0352-release-pipeline-20261029` (`351d9cac`). Green code snapshot: `backup/android-0352-release-contract-green-20261029` (`04a583a5`). Historical protected backups remain intact.

