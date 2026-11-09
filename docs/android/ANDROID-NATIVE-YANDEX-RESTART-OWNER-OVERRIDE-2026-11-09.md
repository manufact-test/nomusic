# CELIKOM Android — owner correction / HARD OVERRIDE — 2026-11-09

**Priority P0 / supersedes all conflicting "web", "lab", and alternative-player suggestions.**
**OWNER HAS REJECTED WEBVIEW / EMBEDDED YANDEX WEBSITE as a product direction.**
This decision is final for this handoff. Do not ask owner again to approve web alternative or reinterpret native app as a website.

## 1. Actual product requirement, in owner's words paraphrased faithfully

- User launches/activates CELIKOM (whatever form: companion, module, options app) and then uses the **normal Android Yandex Music application experience**, its player/queue/playlist/radio and native transport controls, logging in **within that Yandex client**. They must **NOT** log into Yandex inside CELIKOM or a web page embedded in CELIKOM.
- CELIKOM silently helps choose already approved *authorized* alternate audio where eligible; same native Yandex player remains authoritative for audio and Play/Pause/Seek/Next/Prev. **One clock per playing song.**
- Can evaluate a compatible transparently modified Yandex **Android** client / in-process module / patcher, as the owner allowed 2026-11-09. Not required to preserve original unmodified APK if user expressly approves eventual controlled installation; **never silently change/uninstall main Yandex**, and never claim a standalone companion can alter stock app media source without permissions/host cooperation.
- Prefer ordinary no-root Android install, Play Protect always ON, no bypass/evasion, no invasive permissions without necessity/consent; signing and distribution must be verifiable. Yandex password/2FA stays in Yandex's own client/login flow, never in a CELIKOM password box.
- A client patched/re-signed by someone else still carries security/privacy risk: audit provenance/signatures/hooks and user account privacy, use a safe test device/emulator first, never blindly import an unknown patcher.
- Users do **not** want a CELIKOM fake separate player or `music.yandex.ru` inside CELIKOM WebView. This is a **product failure even if the APK compiles**.

## 2. What went wrong, with exact preserved branches

Previous assistant ignored the explicit native-client boundary. It first made a pure JVM source-selection policy and local-file demo, then **without asking** built an unrelated Android `WebView` app containing the Yandex Music website and a CELIKOM login form. Offered it to owner as an APK even though no real phone playback, functional parity, Play Protect verdict or in-process native integration was proven. The owner REJECTED this route and asked for a fresh chat.

**Keep these as historical archives only, DO NOT continue or promote:**

1. `experiment/android-one-player-source-gate-20261109`, head at handoff `5964ef8532f7ac5a96edddcbf7b1bc8145935671`: safe `SourceGate` pre-play policy, `SinglePlayerCoordinator` host-generation fencing, pure Java tests, local standalone Android MediaPlayer demo, read-only APK inspection scripts. Useful **only selectively as tests/contracts**, not a working Yandex app.
2. `feature/android-yandex-web-oneclock-20261109`, owner-rejected head before archival annotations `a7c9f80f95322f0a2e2854010c23788e3b1ea0b9`: `android/yandex-web-oneclock/`, actual Android WebView Yandex website, cached alternate in **same web HTMLMediaElement**, separate CELIKOM auth, JavaScript bridge and range-serving source. CI build `42584183770` SUCCESS for source `aad5493303445642451d82f99bedb936c2d46c9e`; **CI only, NOT phone or user product acceptance**. Owner **explicitly rejected** the entire embedded-browser UX. Personal Library preview paths `/CELIKOM/Android/Research/OnePlayer-Web-20261109/` are **REJECTED ARCHIVE, NOT READY FOR INSTALLATION OR DISTRIBUTION**. Never send owner back to install this APK.
3. `research/android-single-player-inprocess-20261109` (this doc branch), original `813514bedb3a2d30a76d720e3e21bf8070aa1361`: correct **native Yandex in-process** architecture feasibility and final Test.76 owner forensic evidence. Make a fresh isolated implementation branch **from this research branch** after reading docs, not from WebView branch.

All source commits remain backed up in GitHub; no production changes are authorized. Owner-accepted Test.50 backup, stable Android, server/DB/catalog, extension, Windows project and official installed Yandex **must not be modified**.

## 3. Facts already established

- Last owner HONOR Android 13 / Yandex Music `2026.10.3 #170gpr` Test.76 owner diagnostic: six Media3 SecurityExceptions, external controller first connected at 14.279s, ordinary `Папиросы` 1944599 resolved and played; RASKOL real catalog `42884423` (external alias `548`) replacement found/prepared with matching duration, but remote Media3 remained BUFFERING position 0. Framework witness disabled 91/91 that run. **Don't repeat Test.77 or claim native Yandex stream is broken.**
- Old Android CELIKOM `ProbeService` + own `ReplacementEngine MediaPlayer` causes two clocks and broken seeking on affected tracks; **do not revive**.
- Android sandbox and certificate policy prevent a normal third-party APK injecting into / replacing stock `ru.yandex.music` stream directly. A patched Yandex APK signed with another cert can't silently upgrade the official same-package APK; package/signature/install path must be explicit.
- ChromaSync Mobile README describes a **patched compatible native Yandex Android client** + in-process module; rootless on-device patcher, with some signature/uninstall friction. Its public repository contains README, **not usable public Android module source**. It is an **architecture and UX target**, not validated code.
- YaMusicTabs is source-available in-process Android UI hook but doesn't demonstrate audio replacement or safe rootless distribution. YM Liberty Android is an independent Yandex-style client, GPLv3, **not** the accepted native Yandex app experience.
- Existing approved CELIKOM server resolve/rights/entitlement and audio streaming should be reused; don't change DB or backend during integration discovery.
- Play Protect scan acceptance is NOT identical to Google Play Store admission and can't be promised without a real signed build/device verification.

## 4. Exact next-chat job; DO NOT divert again

**Start:** read `docs/android/NEXT-CHAT.md`, `docs/android/ANDROID-ONE-PLAYER-ARCHITECTURE-FEASIBILITY-2026-11-09.md`, `docs/android/ANDROID-TEST76-FINAL-HONOR-FORENSIC-2026-11-09.md`, and THIS owner override. Start a fresh isolated implementation branch based on `research/android-single-player-inprocess-20261109`. Keep the existing source-gate contracts archived as optional reference.

**Work in a large uninterrupted block, no repeated status or invented pseudo-APKs.**

A. Verify source-auditable, compatible, legitimate **native Android** integration options for Yandex `2026.10.3 #170gpr`: in-process module or transparently modified Yandex client, app signing/installation, update, Android 13 behavior, security, provenance, license and Play Protect safety. Search actual source, not README marketing alone. Identify real catalog ID, edition identity and exact audio source-selection hook that happens before *Yandex's own* player prepares source; do not claim this found until source evidence exists.

B. Implement a **real minimal proof** only if actual compatible source interfaces exist: direct identity and one-source selector, native Play/Pause/Seek/Next stay on same Yandex player; strict fail-open to original and rights/entitlement; original first-play vs prefetch must be described honestly. No browser WebView, Media3 remote state as authoritative, parallel MediaPlayer, audio-session fading or counterfeit integration.

C. Build/test with CI and if possible emulator/isolated environment (never modify owner's phone), document exact source/installer provenance and what verified. Do not ask user for Yandex account credentials, cables, private APK exports, root or disabling Play Protect. If in-process route is not safely achievable with known materials, explicitly mark **NO-GO** with the exact obstacle, then research a suitable native-client route; **do not silently switch to a standalone player or web product**.

D. **Stop and ask only once owner must manually verify an ACTUAL native-Yandex-working installable candidate** or must approve a concrete potentially destructive native-client installation/signature change; do not involve them in generic demos. If a new direction changes user experience or trust model, explicitly get owner's approval FIRST.

## 5. What must be preserved in next handoff

Current research/documentation remains separate; WebView preview remains rejected archive. Do not present CI compilation as real playback proof. Report concisely in Russian: source/branch, implemented native Yandex integration if any, CI and on-device evidence separately, exact next owner action only when indispensable. Never claim resolved before confirmed.

**Owner's request to current assistant:** save everything, update documentation and provide a ready first text message for a new chat; **do not develop another new APK here**.
