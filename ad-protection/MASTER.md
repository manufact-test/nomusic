# CELIKOM Ad Protection — Master specification v1.0

Status: Stage 0 prepared on 2026-10-19. This is a **standalone research project** inside the existing CELIKOM repository, not an approved production feature.

## Product outcome / release bar

An optional module that, *within explicitly tested environments*, removes **all user-visible advertisement categories** encountered while listening to Yandex Music:

- Visual advertising (banners, sidebar ads and ad overlays).
- Promotional full-screen popups/video ads.
- Audio advertisement between tracks.

The user must not be misled: banner-only blocking is an incomplete outcome and is NOT a releaseable "full ad protection" feature. A solution is acceptable only after an evidence-backed test matrix demonstrates all observed categories and no music breakage. Unknown formats, service changes, regions and devices make unconditional 100% promises inappropriate.

Do not implement general paid-feature or subscription entitlements bypass; the research target is advertising, not unlocking paid playback or protected content.

## Independent implementation

- Folder at repo root: ad-protection/.
- Existing branch: feature/api-range. Do not create a second repository just for this feature.
- Stage 0–6 changes stay exclusively within this folder.
- Build as **separate unpacked MV3 Chrome extension** for experiments; no import/registration in existing CELIKOM extension.
- No production changes to music stream substitution, device binding, authentication, server, CMS/site, Android PoC or extension manifests.
- Avoid global monkey-patching (window.fetch, XHR, player core) unless separately justified and verified safe; favor scoped declarative rules and DOM selectors.
- Independent kill switch for failures in standalone module; later integration must also have a build-time EXCLUDE capability, including related permissions, scripts and rules.
- Failure mode: fail-open. Failed ad detection must not interrupt musical playback.

## Privacy, legal and publication

- Verify current Chrome Web Store rules, requested permissions and single-purpose / disclosure requirements at Stage 1 and Stage 6; store approval cannot be guaranteed.
- Verify relevant Yandex terms and copyright/access requirements. Chrome approval is not permission from Yandex.
- Use explicit, minimal host permissions. No broad all_urls unless justified and approved.
- Do not collect or upload account tokens/cookies or browsing histories.
- No evasive, hidden features to defeat platform reviews.
- Research other implementations, but inspect and document licenses before copying code.

## Scope & sequencing

Chrome + Yandex Music first. Android application and other streaming platforms are out of scope for this module's MVP and may be reconsidered separately; never label a Chrome-only prototype "all devices".

Work through ROADMAP.md stages sequentially. There are hard gates before implementation (Stage 1), before claiming complete coverage (Stage 4), and before packaging for the Chrome Web Store (Stage 6). Stage 7 integration requires explicit owner authorization.

## Evidence/acceptance

- Reproducible test conditions (date, account with/without Plus, region when relevant, browser build, ad type).
- Audio/visual cases observed in live tests or captured permitted test fixtures; cannot claim absent ad types are blocked.
- Playback remains correct for original Yandex tracks AND CELIKOM replacements when later integrated.
- Long-run stress, playlists, seek, ads, timeouts, page navigation, multiple tabs and recovery covered.
- Clean-removal proof: deleting ad-protection/ and all its integration references must restore prior build behavior without residual permissions or hooks.

## Document policy

Stage 0 creates these documents. Starting at Stage 1, update **ad-protection/** research and checkpoints after meaningful chunks or when the user requests handoff. Do not update unrelated CELIKOM documentation during this isolated effort.

## Research implementation status — 2026-10-20

The Stage 1 evidence collection instruments (`observer/`, `analysis/`, `visual-lab/`) now exist and are **read-only or synthetic fixture-only**. They do not implement nor authorize an ad blocker, nor complete Stage 2's full prototype acceptance bar. Observer permits only manual ad/normal labels and passive native media/CSS candidate counts; local HAR analyzers do not block and issue a conservative HOLD. New cap: 20 manual markers, 80 recent events; observer overload increments dropped-root count. Popups export a strict whitelist only.

**Hard gate unchanged:** need evidence from authorized real Yandex Music non-Plus sessions, including audible inserts and negative controls, before audio architecture D1/D2/D3 can be classified. Stage 7 integration and any changes to parent apps remain forbidden without separate approval. See the operational checkpoint, live-browser handbook and NEXT-CHAT.
