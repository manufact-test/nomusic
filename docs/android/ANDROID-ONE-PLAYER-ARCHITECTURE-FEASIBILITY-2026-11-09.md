> **2026-11-09 —実験ный Android lab:** independent Gradle APK built, [CI #42532598788 PASS](https://github.com/manufact-test/nomusic/actions/runs/42532598788), pure-Java 12 source-gate cases pass. This is not Yandex in-process access and not a Play Protect result. See [Gate 0 decision](ANDROID-ONE-PLAYER-GATE0-DECISION-2026-11-09.md).

> **2026-11-09 · новый независимый эксперимент:** `experiment/android-one-player-source-gate-20261109`. Gate 0 исследован, Gate 1 реальной интеграции с Яндексом пока **BLOCKED**: отсутствует аудируемый совместимый in-process host. Создан автономный `android/one-player-prototype/` с безопасным выбором альтернативы до запуска одного плеера и 12 unit scenarios; этот код не является модификацией Яндекса или APK. Подробности: [ANDROID-ONE-PLAYER-GATE0-DECISION-2026-11-09.md](ANDROID-ONE-PLAYER-GATE0-DECISION-2026-11-09.md). Основу, Test.50, сервер и официальный Яндекс не менять. CI результат проверять отдельно.

# CELIKOM Android — single-player architecture / implementation contract

**2026-11-09 · owner-approved NEW direction · DOC/RESEARCH ONLY.** Repository `manufact-test/nomusic`; working docs branch `research/android-single-player-inprocess-20261109`. This is NOT a signed implementation nor proof of Play Protect acceptance.

## 0. Product contract — what the owner actually wants

User experience: **start/enable CELIKOM → open the familiar Yandex Music UI → play as usual → get an approved alternate audio version**, with authentic native Play/Pause/Next/Previous/seek, ordinary playlists and radio, reliable first track and next track. Whether CELIKOM is called an equalizer, separate settings app, module or helper is NOT a product requirement. Underlying module distribution must be transparent, non-malicious, ordinary install **with Play Protect ENABLED**, and ideally no root. Owner accepts researching a *compatible modified Yandex Music client*, provided it remains safe and genuinely convenient. Do not repeat the old assumption that the official Yandex APK must never be changed: this preference was explicitly superseded on 2026-11-09.

Nonnegotiable: **one authoritative player clock for each active song**, not CELIKOM's separate MediaPlayer slaved to external Yandex Media3. Current architecture `ProbeService.java` observes Yandex via external Media3; `ReplacementEngine.java` decodes an approved replacement in its **own** `android.media.MediaPlayer`, uses `DynamicsProcessing` attached to Yandex's audio session to fade out the original. This causes two independent clocks and depends on the Yandex remote service accurately reporting seek/pause/current item. On HONOR those callbacks lag or remain stuck; see Test.74, Test.75 and final Test.76 evidence. Do NOT build a new Test.77 from this same fundamental coupling.

## 1. Reality checks — avoid promising impossible Android behavior

* A normal, unprivileged companion APK cannot arbitrary inject code into or replace an audio stream inside a **stock installed** `ru.yandex.music` app. Android applications are sandboxed. Normal equalizer `AudioEffect` modifies audio session signal, **does not give an API for choosing the app's audio data source**.
* The credible in-app model needs a **compatibly modified client / runtime module / officially supported extension**. No Android equivalent of PC PulseSync with identical guarantees has been established in this repo. PC PulseSync/ASAR script injection in Electron is not transferable as-is to Android.
* A Yandex APK repackaged and re-signed under our own certificate **cannot update the stock Yandex package signed by a different certificate**. For same package name, installation generally requires removing original first (risk to login/downloads); with new package name, compatibility/account/OAuth/notification handling require independent verification. Never advise owner to uninstall the everyday official app without deliberate approval and backup.
* **Google Play Protect scan acceptance ≠ publication on Google Play Store**, and neither can be guaranteed from static code or an untested APK. There are genuine policy, privacy, trademark, terms-of-service, copyrighted audio and install-signing questions. Never disable Play Protect, bypass app integrity, hide code/functions, suppress scanning, use root/LSPosed as a mass-user requirement, collect passwords/OAuth tokens, or ask owner to test on daily account first. Legitimate transparency and minimum permissions only.
* In-app source identification may expose the **real Yandex catalog track ID** and perhaps album/edition, unlike external Media3 aliases `548`, `578` etc. It is a **hypothesis until demonstrated** with live known IDs and duplicate-edition negatives. No static assumption that every internal `mediaId` is a catalog ID.
* Single authoritative player means eliminating **same-song** independent source/replacement clocks. Crossfading two *consecutive* songs inside one controlled client's queue is a separate feature and should not be confused with two independent apps duplicating the same song. Never use an arbitrary second audio session to replace a playing same song.

## 2. Compared real-world implementations

| Source | Actual evidence | Reuse and limits |
| --- | --- | --- |
| **ChromaSync Mobile** https://github.com/Desai0/ChromaSync-Mobile | README describes an Android module running **inside a compatible modified Yandex client**; rootless installer via on-device patcher + separately installed module; rooted option LSPosed. Caches the replacement, original may play on first uncached pass. **The GitHub repo root contains only README.md as of this audit**, no buildable Android source/license file. | Closest *product/architecture analogy*, not available source to copy. Does not establish Play Protect pass, exact phone compatibility or performance on RASKOL. Never install unknown patcher blindly. |
| **YM Liberty Android** https://github.com/gagayhhad-tech/ym-liberty-android | Open independent Android client. `android_app/assets/www/yandex.js` has `getStreamUrl(trackId,token,...)` and chooses DB replacement before play; `app.js` uses HTMLAudioElement and can crossfade between successive tracks. | Useful reference for **direct catalog ID** and replace-before-play policy, **NOT** a modifier of installed Yandex. Code GPLv3: do not copy into proprietary CELIKOM without license review; don't copy OAuth handling/security assumptions. |
| **YaMusicTabs** https://github.com/daanqq/YaMusicTabs | Public Xposed/Vector in-process Android Yandex module, hooks navigation list; notes version-specific internals (`2026.03.4`) and breakage risk. | Shows hooks are technically possible, **does NOT replace audio** or demonstrate rootless installation/Play Protect. |
| **YaMusicLsposed** https://github.com/windyx0/YaMusicLsposed | LSPosed project for in-app metadata/track operations; requires root/LSPosed for its published installation. | In-process research only, **not** normal-user install solution. |
| **FckCensor / FkCensor PC** https://github.com/Hazzz895/FckCensor and https://github.com/S4YN3X/FkCensor | Desktop Yandex music mods; FkCensor inserts JS inside Yandex desktop Electron app, FckCensor via PulseSync. | Desktop proof of concept only, **not** an Android API or drop-in patch. |
| **Existing CELIKOM Android** `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/` | `ProbeService` external Media3 and `YandexSessionWitnessService` optional framework observer; `ReplacementEngine` own decoder; server already has approved track resolve/stream and subscription gates. | Reuse **server/data/business logic**, **not** current two-player output engine. |
| **Earlier research** `docs/android/ANDROID-0385-NEXT-ARCHITECTURE-GITHUB-RESEARCH-2026-11-04.md` | Additional source comparisons, Ynison limitations, detailed cold-start lessons; was constrained by old owner "no modified Yandex client" rule. | Research remains relevant; its restriction on considering a compatible patched Yandex APK was **superseded by owner**. |

Authoritative Android sources:
- Apps sandboxed: https://developer.android.com/guide/components/fundamentals
- Audio effects only modify an audio session: https://developer.android.com/reference/android/media/audiofx/AudioEffect
- Signatures on updates: https://developer.android.com/studio/publish/app-signing
- Play Protect scanning/warning types: https://developers.google.com/android/play-protect/warning-dev-guidance
- Transparency/minimum permission/privacy policy: https://developers.google.com/android/play-protect/mobile-unwanted-software

## 3. Preferred architecture A: in-process **one Yandex player** + CELIKOM broker

Diagram (conceptual, not existing code):

```
[CELIKOM control / user settings / entitlement]
             |
  explicit authenticated app-to-app IPC (scoped, least privilege)
             |
[compatible instrumented Yandex client]
      [current real Track ID + edition identity]
             |
      [source selection before playback]
        /                         \
 [original Yandex source]    [CELIKOM approved replacement]
        \                         /
       [ONE active Yandex player + ONE seek/pause/next clock]
```

**Mandatory audio-source contract** for a controlled, authorized test environment:
1. At track-source selection (BEFORE playback starts), observe real track ID, catalog edition/album ID, item generation and normal source details. Prove those identifiers across two songs with same title/artist but different versions; no guessing by menu alias or UI text.
2. Resolve an approved version against CELIKOM's existing backend, respecting authentication, entitlement, moderation and rights-confirmation policies; server remains the sole authority. Do not supply raw user credentials to a third-party-modified client or log account tokens. A CELIKOM-signed companion broker may expose **one narrowly scoped, authenticated local transport** (e.g. expiring URI permission or explicit IPC). If identity/signature validation cannot be designed securely, **STOP**.
3. Before selecting that track's playable source, choose either **one verified CELIKOM replacement** or unmodified Yandex original. Replacement must have proven playable URL/file, metadata/duration/codec compatibility, range behavior/caching and rights; no DRM circumvention. **Never** start original audibly and crossfade to a *second same-song player* to "fix" latency.
4. Playback controls stay inside the single authoritative player. In a modified compatible client, track order, UI and MediaSession must remain correct. Next/Prev/seek/pause must operate on chosen source without external re-synchronization.
5. If offline/timeout/denied/not cached, stay on original for **that occurrence** and optionally prefetch for next occurrence. No mid-song original→alternate flicker, no wrong edition from title-only fallback, no silent data mutation. Define measurable first-play offline/online behavior with user approval; cannot promise instant uncached network download.
6. Keep original Yandex integration and owner's stable CELIKOM intact. Reuse existing catalog of **1426 approved replacement rows observed in last logs**; do not move/re-upload sources or modify backend during discovery. No delivery of modified proprietary Yandex APKs in public GitHub without legal/distribution review.

### Feasibility gates: NO scope creep

**Gate 0 — static inventory and risk assessment (start now, no phone):**
- Pin HONOR Android 13, Yandex build `2026.10.3 #170gpr` and owner current official package; determine exact compatible client build and its public provenance, version lock, package/signature layout, update method, supported architecture.
- Inspect **source-available** patch/module examples, verify licenses/signers/dependencies, identify where catalog `trackId` is read and media source is selected. ChromaSync public README alone is *not* source.
- Formalize account/auth/Play Protect risk and test in **spare/emulator/isolated install**; do not delete or patch owner's installed original.
- Write concise `GO/NO-GO` with exact show-stoppers, before building anything large.

**Gate 1 — read-only proof in test environment:**
- Produce a verifiable **non-production** prototype able to observe a real catalog track ID and the one active player's media source choice in a *compatible independently testable client*; capture one-song native pause/seek and one Next.
- Compare exact known catalog IDs for ordinary song, RASKOL and «Дым» against backend; report ambiguous editions. No playback hijack, other-app token capture or protection evasion.
- If no viable read-only in-process mechanism can be delivered under Android permission/signature/security constraints, **STOP A** and evaluate B (below), do not go back to 2-players.
  
**Gate 2 — minimal actual single-player replacement:**
- Only after Gate 1, replace ONE owner-authorized test audio source selected **before native player load**; pause/seek and Next must still work in the same native player, no secondary MediaPlayer, no AudioEffect ducking; original fallback reliable when file unavailable.
- Test sample tracks (RASKOL «Нас не понимают вообще», Лёша Свик «Дым», normal control) plus radio/random Next, cached vs uncached. Avoid user main account/DRM bypass and unauthorized files.

**Gate 3 — distribution/install and hygiene:**
- Reproducible signed builds, hash/signature/provenance, dependency audit, package IDs/updates and rollback plan, no dangerous/sensitive permission demands, no unwanted background injection, clear user consent and transparency.
- **Play Protect must remain ON** for installation and actual playback test. If it warns or blocks, document exact message and stop; do not advise disabling it or disguising the app. Check client login, restoration of official Yandex, auto-update/version-lock strategy, privacy and ToS. Note **Play Store approval is distinct**.
- Owner field assessment is required to say it works. CI cannot prove phone sound or Play Protect verdict.

**Gate 4 — only after validated prototype:** integrate CELIKOM existing UI/accounts/catalogue/subscriptions/updates and release engineering, while keeping PC/browser/server stable.

### Architecture B — independent compatible client, only if A fails

Build a **standalone licensed, transparent CELIKOM client** with one owned playback clock using permitted Yandex access (account consent/API where lawful/available) and our approved replacement library. **YM Liberty Android** is a useful technical reference but not a source to paste because GPLv3 and independent API/auth tradeoffs. Evaluate whether «Моя волна», favorites, library, offline, cast, subscriptions, lyrics, queue and session persistence can genuinely match ordinary Yandex; **it will not literally open the stock Yandex app**. If the user experience/rights/credentials cannot be made safe, explicitly report that limitation, not silently substitute a crippled player.

### Architecture C — old two-player DSP companion

**Parked, not a migration target.** Test.50 retained as best owner-accepted older checkpoint; Test.76 available for audit only. Do not initiate Test.77/78 without owner changing the strategy.

## 4. Objective acceptance criteria (no invented success)
- **Exactly one active same-song player**; internal Yandex native Play/Pause, Next/Prev and seek accurately control the chosen replacement. No Media3 external controller as timing master; no CELIKOM `MediaPlayer` following an already-playing original for the same song.
- No wrong replacement when editions collide; real Track ID and edition provenance documented by a read-only trace. Server approved-only enforcement remains unchanged.
- No startup stall from repeated external Media3 `SecurityException`; player emits normal source or explicit original fallback. This is a property to *verify* on a phone, not assumed.
- Local/cache version starts from appropriate chosen position, no audible original→replacement→original oscillation, no first-second burst, pause remains pause, seeks respond and play/pause icon remains consistent.
- Ordinary Yandex features actually work: playlist, «Моя волна», Next, background, phone screen off, Bluetooth, VPN on/off, network intermittent, account restored.
- Play Protect ON: unmodified official baseline continues intact, installs without harmful-app warnings that require bypass; if warning appears, record verbatim and STOP. No root requirement for target user, no broad Notification Access/Accessibility, no credential theft, clean signed reproducible OTA.
- Preserve immutable Test.50, current stable main application, browser/desktop, server, admin, approval database, already-uploaded files. Any upgrade requires owner testing and explicit deployment approval.

## 5. First chat execution order / deliverables

1. Read THIS file and [ANDROID-TEST76-FINAL-HONOR-FORENSIC-2026-11-09.md](ANDROID-TEST76-FINAL-HONOR-FORENSIC-2026-11-09.md); read prior 2026-11-04 GitHub research. Inspect GitHub examples and legitimate Android install constraints yourself.
2. Create a **new isolated experiment branch**, no Android stable/OTA changes, no irreversible phone instructions; begin Gate 0 followed by Gate 1 when technically justified. Pin sources, licenses, Yandex build, package names and required permissions in a small decision document.
3. Deliver usable artifacts and tests **in the same work session** whenever feasible: read-only catalog-ID observation and source-selection prototype (not only generic recommendations), a reproducible proof/build or a concrete NO-GO with evidence.
4. If blocked by lack of Yandex compatible APK or real handset, complete everything possible off-device and ask the owner **only for one necessary action** (never request passwords, sensitive tokens or Play Protect bypass). Avoid serial 2-minute updates and repetitive tiny experiments.
5. Update this document, exact commit+CI/build artifacts, current short handoff in `docs/android/NEXT-CHAT.md`. User prefers a final short factual report.

**No APK or source-code changes authorized by this documentation task.** Current execution is a research-to-handoff, NOT a finished integration.
