# Stage 1 — evidence ledger (2026-10-20)

This is an evidence/uncertainty register, NOT a list of passing tests. DOC and SRC are source-based claims. HYP hypotheses are unverified for live Yandex Music. LIVE / PASS entries are deliberately absent until measured.

| ID | Claim / observed source behavior | Evidence | Confidence | LIVE state | Gate / next measurement |
|---|---|---|---|---|---|
| DOC-01 | DNR supports URL/initiator/resource type conditions and block/allow/redirect/header rules without reading payload content | [Chrome DNR](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest) | High API | 0 | Verify real ad-only network signature and playback safety |
| DOC-02 | Standard MV3 extension cannot rely on webRequestBlocking | [Chrome webRequest](https://developer.chrome.com/docs/extensions/reference/api/webRequest) | High API | 0 | Do not implement classic blocking listeners |
| DOC-03 | Content scripts run in ISOLATED world by default; can change DOM but not share arbitrary page JS globals | [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) | High API | 0 | Test injected selector on actual page |
| DOC-04 | DNR is not a media-stream payload filter; service-worker handled/cached responses may avoid it | [Chrome DNR](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest) | High API | 0 | Classify separate-vs-in-stream audio |
| DOC-05 | Chrome Web Store expects narrow single purpose and functioning utility | [Quality](https://developer.chrome.com/docs/webstore/program-policies/quality-guidelines), [Minimum functionality](https://developer.chrome.com/docs/webstore/program-policies/minimum-functionality) | High policy | 0 | Publication at Stage 6 only |
| DOC-06 | Permissions must be minimum necessary; MV3 code must be inspectable, generally self-contained | [Permissions](https://developer.chrome.com/docs/webstore/program-policies/permissions), [MV3 requirements](https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements) | High policy | 0 | Review manifest and bundled assets |
| DOC-07 | Yandex Music terms constrain service/material/player use; no permission to assume paid entitlement bypass | [Yandex Music terms](https://yandex.ru/legal/music_termsofuse/ru) | High as terms text, legal consequences not adjudicated | 0 | Legal review before distribution |
| SRC-01 | fixYMusic removes selected ad-named DOM components; does not establish audio blocking | [manifest](https://github.com/IyepI/fix-yandex_music/blob/master/manifest.json), [script](https://github.com/IyepI/fix-yandex_music/blob/master/fix.js) | High source / Low efficacy | 0 | Verify current selectors, no code copying |
| SRC-02 | YaBlocker manifest does not match music.yandex.ru and README claims permissions absent from manifest | [manifest](https://github.com/right-git/yablocker/blob/master/manifest.json), [README](https://github.com/right-git/yablocker/blob/master/README.md) | High source | 0 | Do not use as proof of Music coverage |
| SRC-03 | Desktop WebView project uses global fetch/XHR URL interception; MIT file exists | [script](https://github.com/cptn73m0/ya-music-desktop/blob/main/assets/inject.js), [MIT](https://github.com/cptn73m0/ya-music-desktop/blob/main/LICENSE) | High source / Low Chrome compatibility | 0 | Avoid broad hooks and unsafe substring lists |
| SRC-04 | GPL-3.0 filtering projects exist but licence obligations apply | [AdGuard](https://github.com/AdguardTeam/AdguardBrowserExtension), [uBlock](https://github.com/gorhill/uBlock), [filter list licenses](https://github.com/gorhill/uBlock/wiki/Filter-list-licenses) | High license-family | 0 | Recheck at exact pinned revisions; no copying |
| HYP-V1 | Banner/side advertising currently has reliable unique DOM signatures | No live Yandex page capture | Unknown | **NOT OBSERVED** | Free account, layout variants, screenshots/DOM structure redacted |
| HYP-V2 | Marketing popup can be distinguished from login/paywall/service modal | No live Yandex page capture | Unknown | **NOT OBSERVED** | Verify behavior across all modal variants |
| HYP-V3 | Video advertising appears as standalone DOM/media request | Historical class names only | Unknown | **NOT OBSERVED** | Check video AND residual sound/transition |
| HYP-A1 | Audio advertising is fetched as independently blockable request | No live non-Plus network/playback capture | Unknown | **NOT OBSERVED** | Compare precise timestamps, requests and next-track behavior |
| HYP-A2 | Audio advertising is exposed as a reliable player-only ad status | No authorized runtime instrumentation | Unknown | **NOT OBSERVED** | Determine if status is observable without intercepting credentials or player core |
| HYP-A3 | Audio advertising is integrated into music media response | No traffic observation | Unknown | **NOT OBSERVED** | If true, review NO-GO for a safe MV3 implementation |
| HYP-R1 | A single ad-only rule would not block originals, partial content or CELIKOM stream substitution | No Chrome trace/test | Unknown | **NOT TESTED** | Force original playback + seeks + Range before shipping |
| HYP-R2 | Module can be fully disabled/removed with zero parent effects | Existing Stage 0 architecture and tests only | High for no-op shell, unknown after implementation | **NOT TESTED for blocking** | Compare disabled/enabled baseline and folder-only diff |

## Recording a first live event

Use an entry with:
- ID, date and Chrome version; target country/region ONLY in broad terms; subscription yes/no; browser site domain and route.
- Exact class (banner, popup, video, audio); observer note and reproducible user steps; count of independent occurrences.
- Audio transitions: play/next/seek/timestamp, whether music continues, and whether blocking has an effect (only in subsequent controlled sessions).
- Screenshots with user-identifying information redacted, and network request **origin/path pattern only after redacting query params**; never record signed URLs, cookies, bearer tokens, JWTs or account identifiers.
- Result: UNTESTED / OBSERVED / PASS / FAIL / BLOCKED; link to separate local test log or permitted sanitized fixture.

Never infer that an ad class does not exist because it was absent in a short test. Never copy third-party source into the project merely to make a prototype.
