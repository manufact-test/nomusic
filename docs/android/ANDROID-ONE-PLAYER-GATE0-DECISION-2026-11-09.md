# CELIKOM Android — Gate 0 decision, 2026-11-09

**Scope:** isolated branch `experiment/android-one-player-source-gate-20261109`, starting from `813514bedb3a2d30a76d720e3e21bf8070aa1361`. No stable, Test.50, server, OTA, original Yandex installation, or database changes.

## Verdict

- **Gate 0 (research): COMPLETE with BLOCKER.** Android 13/ HONOR NTH-NX9, official Yandex Music `2026.10.3 #170gpr` (code 24026531) is the actual baseline according to Test.76. No verified, source-auditable Android host compatible with that exact build and satisfying normal rootless transparent install plus Play Protect acceptance has been established.
- **Gate 1 (real Yandex in-process ID and player source): BLOCKED / NOT PROVEN.** No legitimate read-only internal callback from stock Yandex was obtained. External diagnostic ID `42884423` (RASKOL) is useful as an expected-value test oracle, **not internal evidence**. Edition identifiers in the prototype are synthetic. Neither a fake Media3 player nor a source selector proves integration.
- **Implementation done:** self-contained, no-dependency Java `SourceGate` selects a fully cached approved and entitlement-checked replacement `content://` URI **before playback** only for internally attested numeric catalog ID and exact edition. Otherwise retains original untouched. Twelve deterministic negative/positive cases, host JDK test runner, and CI workflow. No APK created or requested for installation. The code is a policy unit, not the final CELIKOM app.

## Public reference inspection

- [ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) currently exposes README only, no licensed source, no reproducible patcher/host source. README says rootless mode patches a compatible Yandex APK, may require removal of official package due to different signature, and is version-locked. No proof of Play Protect or stock `#170gpr` compatibility.
- [YM Liberty Android](https://github.com/gagayhhad-tech/ym-liberty-android) has source and **GPLv3**; its `android_app/assets/www/yandex.js` uses catalog track IDs for independent client playback. It is not a stock client integration and cannot be pasted into a proprietary project without a license plan.
- [YaMusicTabs](https://github.com/daanqq/YaMusicTabs): Apache 2.0, source includes Android build and version-dependent in-process UI tweaks, but not an authenticated audio-source hook or rootless distribution proof.
- [Android Media3 source factory](https://developer.android.com/media/media3/exoplayer/media-sources): source selection before `prepare` is a supported mechanism **inside a player we own**. It cannot replace the stream in an unrelated sandboxed stock process.
- Signing: a modified APK signed by CELIKOM cannot update stock `ru.yandex.music` in place under a different certificate. Repackaging may require removal, which is unacceptable on owner's primary phone. An alternate package can coexist only after explicit verification of manifest, package-name assumptions, auth and legal suitability. Play Protect compatibility can only be verified with an actual signed install while protection stays enabled; never attempt evasion.

## Concrete stop conditions / next executable gate

1. Obtain a source-auditable, legally distributable Android host with authorized **in-process** catalog ID + edition callback and pre-load media-source API, pinned version and signing chain; or secure explicit support from the client vendor. Audit permissions, privacy and license before loading account data.
2. In **emulator/spare device only**, prove two different tracks/editions have catalog IDs from that host and an unchanged source decision route. Do not request credentials or extract tokens.
3. Only then integrate this SourceGate into that host, test one rights-cleared local file through its **one** player, and check native pause/seek/next, Play Protect **ON**, normal installer, and rollback. Without (1), **NO-GO for architecture A as a deliverable**, not a claim that all in-process modifications are impossible.
4. If (1) cannot be sourced, investigate a first-party independent client under explicit user approval. It cannot promise to retain the installed stock Yandex interface.

**Verified CI:** [run #42532088126 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42532088126), host JDK compile + 12 source-gate scenarios + legacy-dependency scan passed. No signed APK, live HONOR ID trace or Play Protect verdict is available. CI checks only source decision behavior.

## 2026-11-09 — completed Android lab APK build

- **CI PASS:** [Android single-player lab build #42532598788](https://github.com/manufact-test/nomusic/actions/runs/42532598788) at code SHA `a17da94a3ef61886f7e8b1df1e39ee8eb5755ea0`. JDK source-gate tests passed, Android SDK 35 Gradle assembled the debug APK, manifest sensitive-permission grep passed, SHA256 recorded, artifact upload passed.
- [GitHub Actions artifact (debug APK)](https://github.com/manufact-test/nomusic/actions/runs/42532598788/artifacts/13637703961), artifact ZIP SHA256 per GitHub digest `46bb56b3f389945fbf373e9f42d441a5dd0868244039d28d37bea0714f745bcc` (ZIP digest, **not APK hash**). Retention through 2026-11-15 UTC. This is a *debug signed* standalone laboratory APK despite workflow artifact name saying 'unsigned-for-research'; it is **not a release signature** and cannot replace official Yandex Music.
- The lab is a single-MediaPlayer Android Activity that lets a tester pick two user-owned audio files via the system picker, simulate catalog+edition IDs, choose a verified cached source before start, pause, seek, and release old playback on Next. Metadata duration comes from `MediaMetadataRetriever` (not a second player).
- **No Yandex interface integration / no real in-process ID evidence / no Play Protect on-device verdict**. Gate 1 for modified Yandex still blocked. The lab is ready for *optional separate-device* hands-on evaluation; never tell owner to uninstall or alter official Yandex for this.

## Follow-on implementation: host queue coordination

Added `SinglePlayerCoordinator` with an explicit **authorized host API** (`HostPlayer`, `CatalogueResolver`, `Telemetry`): a track from the same host queue triggers replacement eligibility before `prepare`; a generation fence excludes stale play/pause/seek from the prior track; a track switch always stops the old source first. No external Media3 controller or audio-session hijack. Fake-host tests exercise replacement selection, exact-original fallback, host native commands, Next generation increase, stale-event rejection and stop safety.

The real Yandex app has **not** provided these host interfaces. Connecting `SinglePlayerCoordinator` to stock `ru.yandex.music` is still blocked by sandbox, proprietary implementation and lack of compatible, auditable extension source. The standalone Lab Activity remains only a local-files harness.

An APK built by this branch has its **own** package `pro.celikom.oneplayerlab`; signature does not alter Yandex, and a successful GitHub debug build does not imply Play Protect approval. No primary-phone test is requested.

## Research update 2026-11-09 — safe rootless feasibility and exact-client dependency

- [Original LSPosed/LSPatch](https://github.com/LSPosed/LSPatch): rootless APK-specific DEX/SO injection, **GPLv3**, repository archived on 2023-12-13. It is a reproducible historical reference, not evidence of compatibility with Yandex 2026.10.3, normal signature preservation, or Play Protect acceptance. Newer forks exist but must each be audited independently. As patched APK is re-signed, it cannot silently update the official Yandex package.
- ChromaSync's public README confirms a patched, version-specific rootless host and possibly removal of stock Yandex for same-package signature conflict; the actual Android patch/module implementation remains nonpublic. No authorized source/compatibility proof for owner build.
- Added local-only `tools/inspect_apk.py`: verifies ZIP, SHA256, split DEX/native ABIs, optional installed Android SDK signer/package info, and non-authoritative player class markers; Python unit tests with synthetic fixtures. **No APK is collected or modified by CI.** If a safe private snapshot becomes available it can be inspected offline; no Yandex tokens/database/music cache are involved.
- Prepared `tools/export-yandex-apks-readonly.ps1` for a later owner's **explicit** Windows/ADB read-only extraction of their installed `ru.yandex.music` APK parts. Does not uninstall/install Yandex, access app data or change phone settings itself. No such owner's snapshot has yet been provided. Do not publish proprietary snapshot in GitHub.
- Added `SinglePlayerCoordinator` fake-host contract: native Play/Pause/Seek/Next generation fence; source decision before prepare, no secondary player. Its fake-host tests **do not prove** it can be attached to Yandex.

**Latest verified code CI:** [single-player source gate run #42579938038 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42579938038), [standalone Android lab APK run #42579938010 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42579938010), both after `db212f63671eb89304cfc1f9ac9959f7a0a2a263`. Need a separate private exact-Yandex-APK inventory and legal/compatibility audit before any in-process Gate 1 claim. **No installable Yandex replacement / Play Protect verdict yet.**
