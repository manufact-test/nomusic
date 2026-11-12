# CELIKOM A1 — real 16→1 APK native 75s PASS, original package name retained (12.11.2026)

## Proven, not inferred

**[GitHub Actions 43204916823 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43204916823)** on native ARM64 + ARMv7 Android 13 (disposable Redroid, 25 observation samples across 75 seconds):

- Original XAPK: existing privately uploaded, publisher-signed Yandex Music 2025.10.4 #120.1gpr, **16/16 verified split APKs**. SHA256 archive `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`.
- Real untouched issuer-signed original 16/16 installed and **native 75s baseline PASS** on the guest.
- Original cleanly removed in disposable guest, then the **genuine signed publisher base APK** entered pinned upstream LSPatch v1.2-487 `sigBypassLevel=2` (not already independently re-signed input); 15 remaining splits independently signed by same ephemeral own-key.
- All 16 own-key LSPatch2 parts merged with pinned APKEditor into **ONE independently signed original-name APK** `ru.yandex.music`. Verified preserved nested `assets/lspatch/origin.apk`/config/loader, native/DEX byte-payload parity, signed loader ABI/ELF alignment, original Android version and successful installation of exactly **1 APK**.
- **MAIN native 75s PASS** for this ONE APK, same exact process PID and resumed Activity across 25/25 samples. Results: `one_apk_structural_pass=true`, `output_apk_count=1`, `independent_one_apk_installed=true`, `independent_native_75s=true`, `verdict=2025_SAME_NAME_ONEAPK_NATIVE_MAIN_75S_PASS_NO_AUDIO`.
- No real music, login, MyWave, playback, audio swapping, Play Protect or owner-phone test. No publisher APK or lab APK artifact/key published; private original Draft Release untouched.

**Major causal consequence:** merging **16→ONE APK with LSPatch2 does NOT itself prevent native Yandex MAIN 75s** when the original package name is retained. The previous independently namespaced single-APK CELIKOM `pro.celikom.yandex.nativeclonelab` **installed next to genuine publisher Yandex** yet crashed `JAVA_CRASH / ILLEGAL_STATE` and Activity resumed 1/25 — [43199953381](https://github.com/manufact-test/nomusic/actions/runs/43199953381).

The following additional real A/B tests isolate commonly suspected variables:

- [43202922695](https://github.com/manufact-test/nomusic/actions/runs/43202922695) stock original FIRST 75s PASS, CELIKOM installed SECOND alongside it: clone Java crash. So user-realistic install order does not solve it.
- [43203474672](https://github.com/manufact-test/nomusic/actions/runs/43203474672) clone-only, preserved all original ContentProvider authorities: clone Java crash.
- [43203990462](https://github.com/manufact-test/nomusic/actions/runs/43203990462) clone-only, **only the root manifest `package` changed**; no component/provider/process/permission rewrites: clone Java crash.
- These A/Bs narrow the unresolved failure to independent package identity / package-associated runtime invariants, not signature level alone, not arbitrary provider renames, not one-APK merging alone. Do not claim the exact internal Java check has been identified.

## Engineering next action

Do NOT repeat green signing/merging/manifest experiments. Proceed with **exact first fatal Java process/message/callsite** analysis of independent package `pro.celikom...` using privacy-safe read-only crash classifier, without leaking user credentials or third-party code. A focused experiment `experiment/android-a1-2025-clone-java-rootcause-arm13-20261112` with 27/27 safe unit checks PASS [43204974170](https://github.com/manufact-test/nomusic/actions/runs/43204974170) and real source-controlled ARM13 [43205246130](https://github.com/manufact-test/nomusic/actions/runs/43205246130) is prepared/started. If app init can be repaired without replacing the native player, then hook existing B42 source-before-decoder and verify real audio, pause, seek, Next/MyWave on the owner's one phone.

## Exact branches / invariants

- Real one-APK native PASS source: `experiment/android-a1-2025-original-name-oneapk-arm13-20261112` @ `7361ac133466bb12fdf6840136b963eca1390505`.
- Exact backup: `backup/android-a1-2025-originalname-singleapk-causal-gate-20261112` @ same SHA; independent previous 16-split original-name PASS backup `backup/android-a1-2025-publisher-input-lspatch2-own-main-75s-pass-20261112` @ `93cb95364b4da7655bdc96e12e03dfc321e29da6`.
- Diagnostic experimental branch `experiment/android-a1-2025-clone-java-rootcause-arm13-20261112` @ `215f742a14702ae200158af2dbaff12996f55d76`, exact backup `backup/android-a1-2025-java-rootcause-sanitized-gate-20261112`.
- Accepted Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108` remains untouched. Frozen A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743` remains untouched. No production, owner-installed Yandex, API, Windows or Chrome changes.
- Product **Stage A remains NO-GO** because the successful single APK retains original Yandex package name, cannot independently coexist with installed original, and has **not** produced any tested audible CELIKOM substitution. Stage B remains LOCKED. GitHub issue #41 OPEN.
