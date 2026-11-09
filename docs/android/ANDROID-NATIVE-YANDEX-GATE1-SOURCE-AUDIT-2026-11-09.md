# CELIKOM Android — NATIVE Yandex Gate 1 evidence & NO-GO (2026-11-09)

**Scope:** new isolated branch `experiment/android-native-yandex-gate1-20261109`, based on research HEAD `f2d2ed11deea8c70048694276033498bafa9e800`. **Do not install or build a user-facing APK from this audit.**

## Owner's exact immutable product contract
CELIKOM runs with the **native Android Yandex Music experience**, login in Yandex, same native source owner and transport controls (Play/Pause/Seek/Next, playlists/radio). No WebView, no independent player, no external Media3 as master, no second same-song MediaPlayer, no credential capture, no root/disabled Play Protect requirement for ordinary users. No change to stable CELIKOM, accepted Test.50, Yandex installed on owner's HONOR, server, catalogue or desktop/Chrome.

**Device baseline (owner's last real log):** HONOR NTH-NX9 Android 13, Yandex Music `2026.10.3 #170gpr` code `24026531`. RASKOL «Нас не понимают вообще» catalog ID `42884423` from external resolver, replacement prepared, but remote Media3 stalled at BUFFERING/0. This is **not** a Yandex-native in-process trace. Framework witness off in final Test.76. See `ANDROID-TEST76-FINAL-HONOR-FORENSIC-2026-11-09.md`.

## 1. Direct public source inventory (not README-only assumptions)

| Candidate | Exact inspected source/evidence | Native source replacement verified? | Rootless & safe install verified? |
| --- | --- | --- | --- |
| [Desai0/ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) | Git tree `48be24d69327d040276992b16ec6cb1432f92437`: **only README.md**; no module/patcher source, no license file. README says compatible patched native Yandex, in-process alternate audio, first uncached play may remain original. | **No** public source or identifiable hook. Product-level analogy only. | **No.** README warns same-package signature difference may require uninstalling official Yandex. No proven compatibility with `#170gpr` or Play Protect verdict. |
| [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) | Tree `0f5d07bfc391dc4f4f9f511657dde979b42b913d`; `ModuleMain.java` hooks obfuscated `tz6`/bottom navigation only; project targets Yandex `2026.03.4`, Android 16, modern libxposed, Apache-2.0. | **No** audio stream hook or exact in-player catalog edition. | **No** rootless signed host proof; public instructions assume Vector/LSPosed. |
| [windyx0/YaMusicLsposed](https://github.com/windyx0/YaMusicLsposed) | Tree `c7bf85898cd590b5c4cc09cfce0ed77e9dbce6af`; `MainHook.kt` hooks `MediaSession.setMetadata` (post-selection information), then resolves approximate IDs from cover/album and title/duration search. | **No** verified pre-prepare data-source selection; media ID isn't authenticated exact catalog identity. | **No**, installation explicitly requires root + LSPosed. **Privacy red flag:** `hookNetworkForToken` captures the app's `Authorization: OAuth` header; `findToken` reads app shared prefs; metadata/network URLs are logged to `/sdcard/Download/YaMusicLsposed_Meta.txt`. Do NOT import or run as-is on any real Yandex account. |
| [errorman-awful/YMDownloaderXposed](https://github.com/errorman-awful/YMDownloaderXposed) | Tree `ac5a9e35ffefc4e14505822daeb7e7c460a5bbe3`: only README/license and metadata; no buildable module source visible. | **No.** Downloader description is not source substitution. | **No.** |
| [JingMatrix/LSPatch](https://github.com/JingMatrix/LSPatch) and [konglongbt/LSPatch-A15](https://github.com/konglongbt/LSPatch-A15) | Source-available rootless *patcher substrate* (trees `4d573639e4192c33afb3f1b76b16fc248dbeb830`, `0dc50f42503711b14f5e2bb217c2bdd6321ce5be`); GPL-3.0, can embed hook runtime in one patched APK on Android 9+. No root inherently required; optional Shizuku mentioned. | **No:** framework alone does not discover Yandex's `#170gpr` internal player source methods or identify an edition. | **Unproven:** re-signing can cause official package collision; no pinned, audited signed Yandex+CELIKOM build or Play Protect scan. Don't install unknown forks as a trust shortcut. |
| [YM Liberty Android](https://github.com/gagayhhad-tech/ym-liberty-android) | Independent Yandex-style player, GPL-3.0, not native Yandex APK integration. | **Not applicable to owner UX.** | Not a candidate without explicit owner concept approval. |

Confirmed Android platform prerequisite: [Android update rules](https://developer.android.com/google/play/app-updates) demand same package ID **and** same signer / valid rotation to update in place. A CELIKOM-signed `ru.yandex.music` **cannot silently update** the Google Play-signed installed app. Removing stock app loses app data; a differently packaged build does not prove Yandex OAuth/account flows. Play Protect acceptance must be measured **on actual device/install**, cannot be inferred from open-source or a passing CI.

## 2. Concrete verdict

**Gate 0 ecosystem scan: completed. Gate 1 on actual owner-compatible native Yandex: NO-GO / not yet testable.**

A rootless hooking *framework* does exist with inspectable source (JingMatrix LSPatch); thus the blocker is **not** an absence of any patcher. **Exact blockers**:
1. No source-verified real `2026.10.3 #170gpr` Yandex **internal pre-prepare audio source-selection hook** with authoritative numeric catalog **track ID + album/edition** and original fallback. Public modules only prove UI/metadata/download callbacks, not this integration.
2. No audited legitimate target package and proven safe signer/install/update path preserving account privacy and owner original Yandex, with Play Protect ON. Patched same-ID installation can require replacing the official app; no permission from owner to do this, and no working candidate to justify it.
3. No independently reproducible native-Yandex playback test environment / verified host APK and therefore no native Pause/Seek/Next/radio evidence. External Media3 and pure fake-host source-gate tests do not satisfy Gate 1.

**Therefore deliberately no new APK, no code injection, no compilation/CI, no Play Protect assertions, no request to disturb owner's phone.** This is a precise missing-interface dependency, not proof that native integration is fundamentally impossible. Owner's Test.50 and stable are preserved.

## 3. Required verifiable evidence before implementation resumes

- Obtain **legitimate, audit-permitted, exact-compatible native Yandex host** and its version/source-symbol evidence **without collecting owner's private app data, credentials, paid content or proprietary APK into public GitHub**. Alternatively establish a vendor-supported extension API.
- In a separate emulator/spare phone, validate the Yandex-host class/method where **real catalog ID + edition** reaches source selection *before the player's prepare*. Log only test catalog IDs and selected source type, never tokens or paths containing secrets. Compare duplicate editions; require a pinned signature/build fingerprint and default original/fail-open.
- Only after this proof, construct a narrowly scoped CELIKOM broker and choose pre-cached, rights-authorized alternate **inside the same native playback pipeline**, with no stream hijack / second player. Test native pause, immediate seek, Next, random radio, cached/uncached fallback and security/privacy.
- Before any installation requiring uninstall/signature/package change, present the exact user-facing trust/backup/update consequences to owner for **explicit approval**. Keep Play Protect enabled; do not disguise a modified APK or guarantee Google Play Store review.
- Mark any independent player or WebView alternative as **out of scope** unless owner explicitly changes direction.

**Handoff:** retain `experiment/android-one-player-source-gate-20261109` as isolated policy tests; retain `feature/android-yandex-web-oneclock-20261109` as **rejected archive**, not an APK candidate. The existing Yandex original cannot be accessed through a normal unprivileged CELIKOM companion for in-process stream replacement. Next work needs **real audited host evidence**, not another demo.
