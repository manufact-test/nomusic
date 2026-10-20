# CELIKOM Android native companion — 0.3.23 candidate

This directory owns the current native application addon. The exact 0.3.22 Java source was recovered from its embedded source ZIP. Recompiling it produced a byte-identical `classes2.dex`: SHA-256 `650e8af017f98a9a016fb9b71386bb4774498eb6ca4a49606f16c8000ca57280`. `RECOVERED-0.3.22.json` preserves all recovered source hashes and the APK hash. The older `android/companion-probe` project is not the current installed application source.

0.3.23 changes only Android playback and build/recovery tooling:

- Reuse an already aligned paused decoder on headphone/ordinary resume, avoiding an unnecessary seek.
- If a required seek completes with a moderate measured error, make at most one predicted correction before replacement playback becomes audible. Keep existing timeouts, track/generation fences and original restoration.
- Remove the proactive last-150ms cutoff. Let actual file completion or the native source's track change govern the end.
- Add native discontinuity reason and both playback positions at source track changes to the same combined TXT. A native early transition must still release the previous replacement immediately; do not continue an old song over the new one. The owner's several-second early transition is not claimed fixed by removing 150ms.

The 12-minute diagnostic run and existing UI are retained for this candidate. Design work follows the physical playback check. Calls remain a deferred owner test.

## Isolated work

Work only in `feature/android-isolated`, under `android/**` and `docs/android/**`. Its pinned workflow rejects changes to desktop, backend, website, root configuration and workflow definitions. Do not merge this workspace branch wholesale into the desktop branch. Desktop 0.4.61 is commit `3a037e5fd5c1d09cd811dbf12dc80c7a12ed5e2e`; Android work does not change that ref.

The owner's accepted scope requires no staging setup for these client-only fixes. Builds/tests do not contact production. The installed APK uses the existing API and independent Android installation/session as before; no API/auth/session/catalogue deployment is included in this work.

## Build and verify

Use JDK17, Android SDK API36, compatible Android build-tools, Apktool2.11.1, the exact original 0.3.22 APK and external signing backup. Dependency hashes and official coordinates are pinned in `build-inputs.json`. Put the pinned JARs in `deps/` (ignored). Keep signing files outside the source directory. No network fetch or server snapshot is part of the build.

```sh
python3 build_release.py \
  --sdk /absolute/android-sdk \
  --build-tools /absolute/android-sdk/build-tools/version \
  --apktool /absolute/apktool.jar \
  --base-apk /absolute/CELIKOM-0.3.22-install.apk \
  --signing-dir /absolute/private-signing-directory \
  --output /absolute/CELIKOM-0.3.23-install.apk
```

The script compiles actual Android source, executes deterministic engine/phone replay/parser/API tests, creates addon DEX, packages an exact source snapshot, signs with the existing key, and verifies package/signature/version/permissions/assets/embedded source. Host audio adapters are test code only and are never sent to D8. Build output includes a verification JSON with `physical_phone_playback_verified: false`; it cannot certify headphone hardware behavior.

A physical check needs one update installation, normal playback with a headphone disconnect/resume, and one natural track ending. Keep other observations in one report rather than creating a new build for each minor issue. Do not uninstall the installed app first: the matching signer/package/versionCode are intended to preserve account and settings during an update.
