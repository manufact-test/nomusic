# CELIKOM Android A1 — real owner-uploaded ChromaSync Clone 3.0.1: independent local binary validation

**11 November 2026.** This is a reproducible, read-only check of the actual owner-uploaded `ChromaSync-Clone-3.0.1.apk`, not a summary of competitors' advertisements. Test ran locally in the conversation file container; **NOT** on Android. No binary was copied to the repo, CI, issue comments or external services.

## Precise artifact

- Local source: owner's upload, 102,572,843 bytes (approx. 98 MiB)
- SHA256: `4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`.
- ZIP validation via Python `zipfile.testzip()`: **PASS** outer package (6,587 entries), nested `assets/lspatch/origin.apk` (6,584 entries), nested `assets/lspatch/modules/app.mywave.injector.apk` (41 entries).
- Android DEX structural validation: DEX header magic, exact file-size, SHA1 signature and Adler32 checksum: **PASS** for outer one DEX, nested origin six DEX, module one DEX.
- Parsed three **actual binary** AndroidManifest.xml files from the ZIP bytes, not package descriptions.

## Directly verified architecture, and what it does NOT prove

| Check | Actual observation |
| --- | --- |
| Outer manifest | `package=app.chromasync.yamclone`, `versionCode=24025548`, `versionName=2025.10.4 #120.1rur`, minSdk 28, targetSdk 35; `YMApplication` plus LSPatch `LSPAppComponentFactoryStub` |
| Outer code | 12,020-byte bootstrap `classes.dex`, **not** all original Yandex classes flattened into outer DEX |
| Nested app | `assets/lspatch/origin.apk` independently cloned with package `app.chromasync.yamclone`, versionCode 24025542; six real original-app DEX files, not a publisher-signed `ru.yandex.music` archive |
| Module | Embedded `app.mywave.injector.apk`, version 3.0.1/versionCode 52; LibXposed scope `app.chromasync.yamclone` |
| LSPatch loader | All four supported LSPatch native library ABI folders present; `useManager=false`, `injectDex=false`, **`sigBypassLevel=2`** |
| Signer | X.509 certificate SHA256 **same** across outer, origin and module: `073f86ee2fb80736f7f0a692d98998b8f5b1ac0434a233fa08ea18e7a89697e3` — independent lab signer, **not** proof of publisher-signed native Yandex |
| Remote module updates | Config contains clone-module feed metadata and an Ed25519 public key. Network reachability, actual signature-verification implementation, downloaded code and updates **not verified** |
| Provider collision | Both outer and nested manifests still declare unchanged `com.yandex.preinstallsatellite.appmetrica.provider`. If an installed original Yandex app declares the same ContentProvider authority, Android PackageManager will reject coexistence. No actual two-app install test on device has been performed |
| Security surface | Outer manifest requests `RECORD_AUDIO`, `QUERY_ALL_PACKAGES` and `REQUEST_INSTALL_PACKAGES` among other permissions. Presence in manifest does not establish grants or malicious behavior |

## Head-to-head with CELIKOM A1 experiment

- CELIKOM tested independently signed, 2026 Yandex `#170gpr` clone, LSPatch **level 0** (no signature check bypass). True ARM13 Redroid evidence: independent MAIN starts then constructs a signature-related `IllegalStateException`, enters mode 2 and self-exits. The unchanged original remains alive. Details: [signature trust live NO-GO](ANDROID-A1-20261111-SIGNATURE-TRUST-LIVE-NO-GO.md).
- ChromaSync is a **2025** Yandex clone using different native host version, packaging and signature-compatibility mode. Therefore it is NOT a control that isolates one specific cause. Installing ChromaSync alone might demonstrate its native host launches; running alongside official Yandex might instead fail due to provider authority.
- Config `sigBypassLevel=2` is a verified competitor difference, **not** an authorization to copy its bypass, module, proprietary files or signature logic into CELIKOM. This is outside the approved level-0 test constraints.
- A signed, structurally valid ZIP/Dex/manifest **cannot** establish Android install acceptance, native Activity resume, Passport account login, MyWave, audio replacement, user Play Protect success or Android 13 compatibility. **All those runtime gates remain untested for this exact competitor binary.**

## Why this is not called a live test

The user's exact APK is available **only** as a conversation attachment in the local container. This container has no Android emulator/ADB/Docker/KVM, cannot resolve outbound internet, and GitHub Android13 CI cannot see this local attachment. The public ChromaSync-Mobile GitHub repository contains only `README.md`, publishes no APK under GitHub Releases, and the exact 3.0.1 clone has no verified public download URL. It would be misleading to pretend we launched it in ARM Android13 CI. We did **not** upload the 98MiB third-party binary into the repository or distribute it through artifacts.

**Runtime experiment still required:** on an isolated ARM Android 13 guest, install the exact hash-pinned ChromaSync APK **alone**, record PackageManager result + exact MAIN PID/activity lifecycle; then install original signed Yandex in the guest **only if provider conflicts are managed**, record PackageManager failure type, and inspect native boot without a real user account. Audio/login/Play Protect cannot be declared PASS in guest. Do not ask owner to uninstall stock Yandex or install an unaudited competitor on HONOR 50.

## Product scope and preservation

Owner requires one CELIKOM APK with **actual native Yandex UI and original decoder**, full Yandex features, audio source selection only, no own player, no substitute WebView. This document does not revise that. No changes to frozen A1 integration branch, Test.50, Windows, extension, server, production or owner's phone.
