# Existing projects & reuse/licensing review (Stage 0 notes)

These are research pointers only; **none of their source code has been copied** into ad-protection/.

| Project | Reference | Observed approach | License observation | Decision |
|---|---|---|---|---|
| fixYMusic | https://github.com/IyepI/fix-yandex_music | MutationObserver, selected DOM banner/modal removal; no verified audio ad suppression | Repository showed no declared license when checked | Study ideas; NO direct code copy without permission |
| YaBlocker | https://github.com/right-git/yablocker | DOM advertising selector scanning; documentation differs from requested manifest permissions | No declared license when checked | Research only |
| AdGuard Browser Extension | https://github.com/AdguardTeam/AdguardBrowserExtension | Mature browser filtering architecture | GPL-3.0 | Study design; don't copy into proprietary source without compliance/legal review |
| YaMusic Desktop Client | https://github.com/cptn73m0/ya-music-desktop | Webview injection: fetch/XHR/window.open URL checks and DOM hiding | MIT when checked | Candidate for carefully adapted ideas/code with preserved notices; do NOT indiscriminately monkey-patch global fetch/XHR |
| YandexMusicBetaMod | https://github.com/Stephanzion/YandexMusicBetaMod | Modifies desktop Yandex Music app; claims ad suppression | No declared license when checked | Different product surface; research only |

Notes:
- Some community add-ons install unpacked; that does NOT mean they passed Chrome Web Store review.
- Repositories and README claims do not demonstrate full audio ad blocking.
- Licensing may change: recheck the exact version before reuse.
- Verify rules using primary Chrome Web Store and Chrome extension docs at Stage 1/6; store acceptance cannot be promised.
- Do not infer permission to bypass paid access or region protections from the existence of a public repo.

Official documentation starting points:
- https://developer.chrome.com/docs/extensions/develop/concepts/declarativeNetRequest
- https://developer.chrome.com/docs/webstore/program-policies/


## Stage 1 verified inspection — 2026-10-20

This appendix supersedes any impression that a project README proves Yandex audio-ad suppression. Existing Stage 0 pointers above were rechecked against source/manifest/license metadata at this date.

| Candidate | Inspected artifact / fixed identity | Validated fact | Reuse / license gate |
|---|---|---|---|
| fixYMusic | https://github.com/IyepI/fix-yandex_music/blob/master/fix.js — blob e2d9da5317926397ebd0cb82f8bec64979503788 | DOM selectors include ad-named banners, video and paywall; also mutates scroll/router, uses MAIN world, no proven audio path | No root license / GitHub license metadata detected. All-rights-reserved by default; **do not copy**. Selectors are research hints only, current functionality untested |
| YaBlocker | https://github.com/right-git/yablocker/blob/master/manifest.json — blob 449462bf695a3b87891022477466d6b82560bc39 | Manifest excludes music.yandex.ru; README permission claims do not match manifest; standard MV3 webRequestBlocking is unavailable | No root license / GitHub metadata detected. **Do not copy**. Not a Music-specific working reference |
| YaMusic Desktop Client | https://github.com/cptn73m0/ya-music-desktop/blob/main/assets/inject.js — blob e24f883d993aa0d91afbbbb19a018429a8f8bfa3 | URL substring based ad handling, modifies global fetch/XHR/window.open in desktop WebView and hides DOM | https://github.com/cptn73m0/ya-music-desktop/blob/main/LICENSE — MIT, blob b8a5ad26340b2a62ed016882455c665201df68e9; permissible adaptation **only with required notice**, but broad patching technique rejected |
| YandexMusicBetaMod | https://github.com/Stephanzion/YandexMusicBetaMod | Desktop mod with Plus-related changes; not Chrome extension | No GitHub license metadata or root LICENSE identified. Exclude: wrong surface/entitlement bypass risk |
| AdGuard extension | https://github.com/AdguardTeam/AdguardBrowserExtension | Mature filtering architecture; current GitHub metadata GPL-3.0 | Reference only; GPL code needs copyleft obligations / legal review before any derivative/proprietary distribution |
| uBlock Origin + uBO Lite | https://github.com/gorhill/uBlock ; https://github.com/gorhill/uBlock/blob/master/platform/mv3/description/en.md | uBO Lite is a declarative MV3 design example | GPL-3.0; source study only |
| uAssets, EasyList, EasyPrivacy | https://github.com/uBlockOrigin/uAssets ; https://github.com/gorhill/uBlock/wiki/Filter-list-licenses | Lists are separate copyright/license assets; EasyList/EasyPrivacy offer GPL/CC terms listed by maintainers, not automatically MIT | No bundling or transforming lists in this phase; check exact list licenses and authors on future pinned revision |

### Vendor authority links
- DNR: https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest
- Standard MV3 webRequest blocking restriction: https://developer.chrome.com/docs/extensions/reference/api/webRequest
- Content script context: https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts
- CWS quality: https://developer.chrome.com/docs/webstore/program-policies/quality-guidelines
- CWS permissions: https://developer.chrome.com/docs/webstore/program-policies/permissions
- CWS MV3 local execution: https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements
- Privacy / Limited Use: https://developer.chrome.com/docs/webstore/program-policies/limited-use
- Yandex Music terms: https://yandex.ru/legal/music_termsofuse/ru

Risk note: absence of a LICENSE file / SPDX metadata is not proof that every artifact in a repository is unlicensed, but grants **no safe permission to copy** the relevant code. Current findings concern code inspection and external documentation, not installed extension performance.
