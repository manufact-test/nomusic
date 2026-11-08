# CELIKOM Windows Companion — NEXT CHAT (planning checkpoint, 2026-11-08)

## This is a NEW Windows native companion, not the Chrome/Brave extension

The user will install the **official** Yandex Music Windows app from https://music.yandex.ru/download/. Our app should connect to this installed original and replace audio URLs at the **source-selection layer**, so original Yandex playback controls, queue and session remain authoritative. This is a proposal, **not yet validated** on the user's Windows app.

## GitHub and responsibilities

- Project: https://github.com/manufact-test/nomusic
- Planning/documentation branch: `planning/windows-companion-v1-20261108`.
- Experimental implementation branch: `experiment/windows-companion-integration-20261108`.
- Both start from owner-accepted browser desktop archive `archive/desktop-0.4.73-accepted-20261104` (snapshot SHA `63d8cd891e1db82e0245122391fd4ab5cdd323be`). This is **frozen** and must not be modified.
- Existing browser branch `experiment/desktop-native-source-20261108` is **a DIFFERENT chat's work**, not ours.
- Android, blurred-song database, browser extension, shared server and website are maintained concurrently by other chats. No writes to their files, branches, deployed systems or accepted artifacts.
- This handoff covers **preparation/design only**. No actual Windows app, install test, ASAR patch, official Yandex edit or live API change has been performed.

## Read in order

1. `docs/windows/README.md`: mission, scope, branch ownership.
2. `docs/windows/ARCHITECTURE.md`: SDK vs reversible own adapter, exact-ID and private Range API, session/privacy/rollback.
3. `docs/windows/PRODUCT-DESIGN.md`: all screens, states, UI, wording, compact tray app and brand.
4. `docs/windows/mockup.html`: offline interactive UI visual reference only.
5. `docs/windows/ROADMAP.md`: W0–W5 test and release gates.
6. Frozen `docs/desktop/README.md`, `docs/desktop/LIVE-APPROVAL-073-COMPLETE-FILE-2026-11-04.md`, `docs/adr/0005-private-api-range-and-catalog.md`, `docs/website/BRAND-GUIDE-v1.0.md`.

## Agreed direction / open decisions

- Primary target Windows 10/11 x64; official Yandex Music must be installed. Do not build a competing music player.
- Preferred end state = independent branded CELIKOM tray companion, reusing existing accounts, access, subscription, rewards, approved song catalog, signed HTTPS/Range audio.
- Feasibility route A: PulseSync add-on `setTrackReplacements`; quick integration but third-party dependency/licensing/commercial risk.
- Feasibility route B: version-pinned, reversible own source hook into official Electron client, inspired by FkCensor `getFileInfo/getFileInfoBatch`; more independent but brittle across Yandex updates and may conflict with licence/terms.
- GSMTC can observe player state but cannot provide source substitution. No second audio player fallback without a **new explicit decision**.
- No proof yet either A or B works with our private signed URL expiry and the user's current Yandex build.
- Proposed Tauri 2 + TypeScript UI / Rust shell **not frozen**; evaluate after W0/W1.
- Security/legal/rights review and owner approval are gating requirements, not post-release TODOs.

## What to do next when the owner resumes Windows development

**W0 read-only baseline first.** Verify official Yandex Music version, install path, Yandex account working, package layout/update behavior, native source loading and possible integration path. Do not require the owner to install competitor mods, supply passwords or disable Windows Defender. Compare current server auth/entitlement/resolve/Range contracts read-only; report any dependencies that must be approved by backend owner.

Then present **one small, safely reversible W1 PoC proposal** and obtain explicit go-ahead BEFORE modifying the installed Yandex app or implementing integration. All future code goes only to `windows-companion/**` on the experimental branch; keep stable browser/Android untouched. Need real measured Play/Pause/Seek/Next, original fallback, signed URL expiry, updates and rollback.

Owner review pending: visual design and A/B choice. Avoid promising a working app until real Windows evidence exists.

## Reporting format

Short user-facing outcome: what was found, what actually works on real Windows, what remains unverified, which specific input/approval is needed, next gate. No endless fine-grained timing reports, no fake fixes, no spontaneous promotion to stable.
