# CELIKOM website — Stage 3: v10 UI-kit and implementation contract

**Date:** 17.10.2026. **Status:** implementation groundwork in progress; not accepted, not deployed.  
**Sources:** MASTER-TZ.md v1.2, Brand Guide v1.0, FAQ-PRODUCT-FACTS-v10.md, owner-approved handoff ZIP \`CELIKOM_HANDOFF_v10(1).zip\`.  
**Important:** the approved HTML is a *visual implementation reference*, not permission to invent a new design. Do not publish the original handoff HTML: it embeds a user-supplied screenshot from the real extension.

## 1. Verified handoff artifacts

| Artifact | SHA-256 | Result |
|---|---|---|
| \`CELIKOM_SITE_CLEAN_v10.html\` | \`c22de18793ef75bd39de8a98254ed8f628e180a594c8b7a3d235531653b7ae19\` | 11 major HTML sections, including the 12 planned subject areas; full inline CSS cascade and two vanilla JS interactions |
| \`CELIKOM_v10_WORKING_VIEWER.html\` | \`fb1706eab2bb8c0240d314fab09b250309580d95925fe07dfcc4fba7bd82ad97\` | Standalone 1440/1024/768/390/320 comparison viewer |
| \`CELIKOM_SITE_NEXT_CHAT.xlsx\` | \`1e0b1dc5c5f60ddac7e7c1ce5ef6605de5d96849d01107b8d0ba2a2144783973\` | Handoff status, roadmap, history and constraints |

**11 vs. 12:** \`<main>\` contains sections with IDs \`top\`, \`features\`, \`how\`, \`sound\`, \`player\`, \`contribute\`, \`transparency\`, \`faq\`, \`rewards\`, \`install\`, \`closing\`. Header and footer are separate landmarks, and the master plan's 12 topic numbers do not imply a twelfth standalone \`<section>\`. Do not invent a section to make the numbers match.

Two existing scripted behaviors:
- \`#sound-panel\`: \`#mode-service\` / \`#mode-restored\`, \`aria-pressed\`, output \`#sound-result\`. Visual demo only; do not promise playback of a protected recording.
- \`#faq\`: 28 \`details.faq-item\`, horizontal category controls \`button.faq-filter\`, filtering via \`data-category\`, hash-opening of FAQ item. Five controls: \`all\`, \`start\`, \`rewards\`, \`music\`, \`help\`. No FAQ search.

## 2. Accepted geometry — preserve rather than reinterpret

These are from the source HTML CSS and a local headless Chromium inspection of the *unmodified* visual layout (external Google Fonts not loaded by offline browser; measure geometry, not font appearance).

| Token / selector | Actual v10 |
|---|---|
| \`:root\` | \`--ink:#0B1013\`; \`--mint:#66E0BF\`; \`--paper:#F7F8F4\`; \`--secondary:#556368\`; \`--line:#DCE8E3\`; \`--pine:#14594d\`; \`--radius:28px\`; \`--container:1240px\` |
| Font | Manrope 400/500/600/700/800 |
| \`.wrap\` | 1240px max; side gutters **44px desktop**, **30px <=1050px**, **18px <=540px**, **14px <=350px** |
| General vertical rhythm | source \`--section-gap:82px\`, shrinks at breakpoints (64/54/48px) |
| Main Hero H1 | \`clamp(48px,5.3vw,76px)\`, letter spacing \`-.075em\`, line height \`.92\`; on mobile additional v8/v10 overrides |
| Primary/secondary CTA | \`.btn\`: radius **14px**, min-height **58px**, 17/23px padding desktop; mobile min-height **54px**, 15/18px padding |
| Feature card | \`.benefit\`: radius 26px, padding 31/31/34px |
| How-it-works board | \`.process\`: dark, radius 35px, padding 64/60/70px desktop |
| Demo board | \`.demo-board\`: dark, radius 35px, min-height 340px, padding 45/46px |
| FAQ tabs | Full-width pale container, five horizontal categories, mint active; horizontally scrollable controls on narrow screens |
| FAQ cards | two equal columns on desktop, one column <=800px, gap 14px, final radius 23px, 24px side padding |
| Footer | No extra footer disclaimer under links; preserve approved spacing |

Key CSS cascade constraint: the handoff contains **five ordered style elements** (base, v6, v7, v8, v9/v10). Several older declarations are intentionally overridden later. Do not port only the initial rule and accidentally resurrect old sticky FAQ, search, preview-wide animation overrides or old spacing. Migrate exact *effective* selectors and re-test 5 widths before calling a section implemented.

Offline Chromium inspection (font fallback, no horizontal overflow):
- 1440: container 1240px, x=100; Hero CTA 58px, FAQ 2 columns.
- 1024: container 964px, x=30; Hero CTA 58px, FAQ 2 columns.
- 768: container 708px, x=30; FAQ 1 column.
- 390: container 354px, x=18; Hero CTA 54px, FAQ 1 column.
- 320: container 292px, x=14; Hero CTA 54px, FAQ 1 column.

**The previous provisional .ck UI-kit was corrected** to match these v10 choices in \`website/public/assets/css/tokens.css\` and \`components.css\`. They are shared primitives; final section stylesheet will preserve original v10 cascade.

## 3. Real popup / image policy

The handoff HTML contains **2 data-URL SVG uses** for the approved brand mark and **1 base64 PNG** — a real screenshot of the extension popup. The SVG is identical to the approved \`docs/website/assets/celikom-mark.svg\` and can be safely served as a dedicated site asset. The PNG is **not committed or hardcoded** in the repository.

The website must reserve precisely the approved popup's place and dimensions, then load the real screenshot via CMS-managed, verified media after the owner's approval and before joint publication. **No fabricated popup and no substitute third-party Yandex UI.** Do not copy the handoff HTML, viewer or screenshot data URI into public GitHub.

## 4. Site and mini-CMS architecture

\`\`\`text
website/
  public/                   ONLY public document root, media endpoints and assets
    index.php               when section implementation starts
    admin/index.php         CMS login/editor behind server authentication (Stage 9)
    assets/{css,js,fonts,images}/
  app/                      PRIVATE PHP source; stored outside public_html
    bootstrap.php           configuration and app setup, no committed secrets
    Templates/              vetted components; HTML escaped
    Content/                schema registry, validation, published snapshot
    Security/               sessions, CSRF, permissions, rate limits
    Database/               PDO and transactions
  database/                 PRIVATE SQL migrations and seeds (never web accessible)
  tests/                    UI/FAQ/schema/security/deploy checks
  README.md
\`\`\`

Hostinger target:
- public: \`.../domains/lemonchiffon-narwhal-791953.hostingersite.com/public_html/\`
- private: \`.../domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private/\`, outside public_html.
- secrets: protected server-local environment file **outside public_html and not in GitHub**.
- Content: MySQL; deployment never overwrites owner-edited values or uploads.
- URL policy: allow safe relative site routes / anchors and HTTPS links only; no arbitrary javascript/data schemes.
- Editor scope: landing sections, media, FAQs, SEO, contacts, permitted links; **not** product user/song/reward management.
- Publishing: single atomically switched published snapshot with draft, preview authorized by session, revisions and rollback.
- Security: prepared PDO queries, server-side ACL/validation, password_hash/verify, session hardening, CSRF, login throttling, MIME/size checks for uploads, XSS-safe rendering, media isolation.
- Testing: PHP syntax/static checks, URL/HTML sanitization negatives, auth+CSRF, atomic publish/rollback, unauthorized access, path traversal, MySQL persistence, smartphone admin UI.
- Staging noindex and owner-approved final release; no active payment CTA before checkout exists.

## 5. Gates and current status

1. **Stage 3:** translate approved v10 into exact tokens, UI components, content field map, private path contract, and tests. In progress.
2. **Stage 4–8:** migrate the approved HTML by sections, maintaining v10 appearance and tested behaviors. Not complete.
3. **Stage 9:** implement the full small PHP/MySQL admin, image management, drafts/preview/publish/rollback. Not complete.
4. **Stage 10:** finish security, typography, copy, SEO, screenshots and integration QA; owner reviews all page texts and 28 FAQ; release the site **together with CMS**.
5. The old deployment workflow has been made **manual-only**, requires a release approval marker, blocks private-looking files in the web tree, deploys \`website/public/\` and private application separately. It has **not** been run. Its remaining backup/migration/rollback/health checks are a hard Stage 9–10 release gate.

Do not touch \`extension/\`, \`server/\`, \`android/\` or PR #6. Actual reward policy 2%/20% still requires a separate product review; legacy 3% is obsolete and not to be used in site copy. No live checkout; $2.99 is an announced planned price.
