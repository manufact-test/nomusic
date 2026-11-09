# Stage 1 — technical feasibility and GO / NO-GO review

Date: 2026-10-20 (desk review). Baseline branch head: 5694d6212392616e375f658b46c612e57caf4ff0.
Scope: standalone Chrome MV3 extension for browser-based Yandex Music ONLY.
Status: DESK RESEARCH COMPLETED; LIVE TEST EVIDENCE NOT YET AVAILABLE. This is not a functional ad blocker.

## Executive decision

- **Conditional GO**: continue only with an independent, fail-open research/prototype on observed and precisely classified visual ads. MV3 offers content scripts for DOM changes and declarativeNetRequest (DNR) for known network-request patterns.
- **HOLD**: Stage 1 full-coverage feasibility gate remains open until authorized, reproducible Yandex Music non-Plus ad sessions establish current ad behavior and whether ad audio can be identified without breaking songs.
- **NO-GO for release, completeness claim, or CELIKOM integration now**. No live account, playback, ad-network trace, or browser execution was available in this research pass. We have not confirmed that ANY particular current ad format is blocked.
- Avoid mixing blocking of advertisements with circumventing paywalls, account entitlements, subscription checks, territory restrictions or DRM.

## Evidence levels

- **DOC**: verified vendor documentation, suitable for API/policy capability claims, not proof about Yandex runtime.
- **SRC**: inspected third-party GitHub code/manifest, evidence of that code's design only, not efficacy.
- **HYPOTHESIS**: architecture case needing authorized live validation.
- **LIVE**: observed reproducible Yandex event in a real browser, with date, session, account subscription status, URL/route, source and playback outcome. Current LIVE count = **0**.
- **PASS**: repeated before/after browser outcome with the standalone module on/off. Current PASS count = **0**.

See STAGE1-EVIDENCE-MATRIX.md for individually tracked cases and STAGE1-BROWSER-TEST-PROTOCOL.md for the capture procedure.

## Mechanism evaluation

| Mechanism | What it actually can do | What it cannot establish | Verdict |
|---|---|---|---|
| MV3 DOM content script (ISOLATED world) | Hide/remove narrowly identified HTML elements and restore layout | Does not stop a sound playing outside removed DOM; does not see arbitrary page JS variables by default | Candidate for banners/overlays after LIVE selector verification |
| MutationObserver + CSS | Handle dynamic SPA layout after navigation | Cannot prove an element is an ad from broad class-name guesses; unbounded mutation scans can create CPU churn | Candidate with rate limits, idempotence and detach cleanup |
| DNR block / allow rules | Decide on URL/initiator/resource type/request/response headers; filtering happens in Chrome | Does not inspect arbitrary audio/video **response bodies**, decode a media stream, or classify embedded ad segments | Candidate for EXCLUSIVELY ad requests validated against music traffic |
| Passive chrome.webRequest | Observe some network metadata with permissions | Most public MV3 extensions cannot use webRequestBlocking; passive metadata is not a blocker | Prefer manual DevTools observation in Stage 1 |
| MAIN-world script / API monkey-patch | Can interact with page context | Rewriting global fetch/XHR/player hooks risks service behavior, private data, Chrome review and CELIKOM conflicts | Rejected as default; exception requires separate threat review |
| Muting an audio element or tab | Can suppress audible output | Also mutes music and leaves silence; is not complete ad removal | NOT ACCEPTABLE |
| Blind skip/next on presumed ad | Could change a player state | False positives, queue/skip limits, missing ad termination semantics, possible entitlement bypass | NOT ACCEPTABLE without strong LIVE positive ad signal and explicit scope/legal review |
| Native desktop app modifications / proxy response rewriting | Potentially powerful on different platforms | Outside Chrome extension scope; service/DRM and publication risks | OUT OF SCOPE |

Chrome DNR source: https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest
Chrome webRequest MV3 source: https://developer.chrome.com/docs/extensions/reference/api/webRequest
Chrome content scripts / worlds source: https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts

**Important DNR details:** Declarative rules act on request metadata; DNR has a service-worker/CacheStorage boundary (not every intercepted-looking response traverses DNR). Rules can block, allow, redirect or modify headers, but must never be applied broadly to Yandex API, music CDN, HLS/DASH-like playback, original/replacement tracks or HTTP Range requests. A trusted allowlist alone is not proof against unknown stream endpoints. A future prototype must be able to disable DNR rules immediately and fail open. DNR debug feedback is for unpacked-development testing; it is not a production analytics channel.

## Ad-type decision tree (hypotheses, not current Yandex claims)

### A. Banner / side ad
1. Obtain LIVE DOM sample and a semantic visual classification.
2. Prefer scoped CSS or narrowly targeted removal with layout recovery.
3. Confirm that suppressing the container never removes playlists, messages, subscription controls or the actual player.
4. Verify refresh, SPA navigation, theme/window changes and a disabled-module baseline.

### B. Popup / modal
Distinguish ordinary marketing ads from login, payment, error, consent, subscription entitlement and other user-action dialogs. Only remove a verified promotional ad. Do not hijack a modal tree or unlock normally restricted functionality.

### C. Video
Determine whether video is a standalone ad DOM component, a separately fetched ad media resource or a portion of a legitimate first-party player resource. DOM dismissal may leave soundtrack/audio running. DNR only if a request is proven ad-only, and the player recovers normally with/without the rule.

### D. Audio between tracks (PRIMARY BLOCKER)
Three mutually different architectures require different tests:
- **D1: separate ad URL/host/playlist resource.** Potential narrowly scoped DNR rule IF the URL is ad-only and playback successfully transitions to actual music when blocked. Unverified.
- **D2: a player-managed ad item/status represented in application state.** Could in theory be identified by robust exposed markers, but modifying player state risks playback integrity and product-boundary violations. No safe signal identified yet.
- **D3: ad audio inserted into the same media stream/CDN request as licensed music.** DNR cannot selectively remove in-stream segments; a browser content script cannot decode/transcode arbitrary protected audio safely. This is a potential fundamental NO-GO under current scope.
Do not assume which of D1/D2/D3 Yandex currently uses. If none can be handled without breaking lawful music playback, stop and report NO-GO for full ad protection.

## Third-party implementation findings (source inspection 2026-10-20)

- **IyepI/fix-yandex_music** manifest SHA 05f5c7999d07ba7e6312ca9112960b8a6c6632be; fix.js SHA e2d9da5317926397ebd0cb82f8bec64979503788. MV3 content script in MAIN world; uses selectors named TopAdvertBanner, SideAdvertBanner, PaywallModal and VideoAd and a MutationObserver; also alters collection routing and wheel handling. It contains **no demonstrated audio-blocking mechanism**. Current selectors unverified; no repository license detected.
- **right-git/yablocker** manifest SHA 449462bf695a3b87891022477466d6b82560bc39. Its match set covers yandex.ru / ya.ru / shedevrum.ai / dzen.ru, **not music.yandex.ru**. README discusses webRequestBlocking and all_urls but manifest requests only activeTab; these claims are inconsistent and MV3 webRequestBlocking is not available to ordinary store extensions. No repository license detected.
- **cptn73m0/ya-music-desktop** assets/inject.js SHA e24f883d993aa0d91afbbbb19a018429a8f8bfa3; license file SHA b8a5ad26340b2a62ed016882455c665201df68e9 (MIT). It uses broad URL substrings and global fetch/XHR/window.open interception in a desktop WebView and CSS/DOM hiding; this is NOT validated in a Chrome MV3 context, and might interfere with first-party endpoints. Do not transplant this technique.
- **Stephanzion/YandexMusicBetaMod** is a mod of a separate desktop product and advertises Plus-related modifications. No license found in repository metadata/root at check time. Reject as out-of-scope, both for platform and product goals.
- **AdGuard Browser Extension** and **uBlock Origin / uBO Lite** prove that MV3-oriented filtering architectures exist, but their stated general blocking capability does not prove Yandex audio-ad suppression. Their source and uAssets are GPL-3.0; inspect filter-list licenses independently.

Source inventory, exact links and reuse rules: RESEARCH-SOURCES.md.

## Initial minimum-permission approach — proposed, NOT installed

- Limit static content script match patterns to verified Yandex Music domains, starting with https://music.yandex.ru/*; add other actual service hosts only with evidence.
- Run DOM code in ISOLATED world. No access to cookies/local tokens, no telemetry servers, no cross-origin requests.
- Introduce DNR only after an ad-only request signature exists. Evaluate declarativeNetRequest vs declarativeNetRequestWithHostAccess precisely for rule type, permission prompts and host scope; never request all_urls for convenience.
- Package all executable logic locally; externally sourced ad filters can be data only, never remotely executed scripts or complex command languages.
- Independent toggle + kill switch; DNR rules OFF by default during discovery. No touch of audio/Range/CDN without test evidence.
- Build / compile time isolation for eventual Stage 7: no importing from CELIKOM core; removal means deletion of this folder leaves parent untouched.

## Web Store & service conditions

Chrome Web Store policy requires narrow, clear single purpose, minimum needed permissions, honest store listing, adequate functionality, user data disclosure/privacy, and inspectable self-contained MV3 extension logic. An inert research shell is not suitable for publication. Approval cannot be promised. Existing single-purpose guidance could require fresh review of a later combined CELIKOM/ads extension. No obfuscation to bypass reviewer understanding, no dynamic remote JavaScript.

Chrome policy references:
- https://developer.chrome.com/docs/webstore/program-policies/quality-guidelines
- https://developer.chrome.com/docs/webstore/program-policies/minimum-functionality
- https://developer.chrome.com/docs/webstore/program-policies/permissions
- https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements
- https://developer.chrome.com/docs/webstore/program-policies/limited-use

The Yandex Music public terms govern access and constrain usage of the service/player/materials. The examined terms mention service restrictions and personal/noncommercial use (see Russian terms, sections 2.6-2.8 in applicable variants); they do **not** grant permission to manipulate licensed content or paid entitlements. This research does not establish whether a particular browser ad filter is contractually authorized or lawful in each jurisdiction. Legal review is required before commercial distribution. No claim that the public terms explicitly ban all ad blockers was verified here.
Source: https://yandex.ru/legal/music_termsofuse/ru

## Stage 1 exit criteria and next action

1. Obtain authorized LIVE evidence on a non-Plus browser session for each advertisement observed, plus a Plus comparison where lawful and available.
2. Inspect the boundary between separate ads and original music; classify audio as D1/D2/D3 or UNKNOWN, using only redacted metadata.
3. Test a narrowly instrumented standalone MV3 observer **without blocking** first, then an isolated candidate only if the precise media safety boundary is proven.
4. Require repeatable positive and negative controls, and regression cases from TEST-MATRIX.md and STAGE1-BROWSER-TEST-PROTOCOL.md.
5. Update Stage 1 GO/NO-GO. DO NOT advance to production, promise completeness or authorize Stage 7 on the strength of this paper.

**Result today:** strong desk evidence for the Chrome API decision, but no live Yandex functionality evidence. Stage 1 remains IN PROGRESS; scope-limited observation/prototyping may be planned, not accepted as complete.
