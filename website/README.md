# CELIKOM website — Stage 3 foundation (17.10.2026)

**Status:** Stage 3 IN PROGRESS; no public launch, no real CMS UI, no database migrations. Site and admin must be completed and released together. Master: `docs/website/MASTER-TZ.md` v1.2; detailed implementation contract: `docs/website/03-UI-KIT-ARCHITECTURE.md`.

## Source of visual truth

`website/reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html` is the vetted visual source from the owner-approved handoff ZIP (11 HTML sections, 28 FAQ, five categories, full v10 CSS and JS, Manrope/brand colors). `website/app/Templates/site-v10.html` is its matching private runtime template. This is **not a redesign**. Reference/template both exclude the uploaded popup PNG, which must be supplied as owner-approved CMS media `/media/celikom-popup-approved.png` only after secure media handling exists.

- All 11 major section IDs and their ordering are preserved.
- `website/public/assets/css/tokens.css` and `components.css` contain v10-derived implementation primitives for progressive migration, **not** a replacement of all v10 CSS.
- `website/public/assets/js/v10-interactions.js` preserves the original two interactions for later extraction from inline scripts.
- `website/public/assets/images/celikom-mark.svg` is the already-approved mark.
- No screenshot or personal user data from the handoff is committed.

## Layout on Hostinger

```text
DOMAIN_ROOT/
  public_html/            <- website/public/ (web-accessible)
    index.php             <- gated PHP entry point
    admin/index.php       <- Stage 9, does NOT exist yet
    assets/               <- public assets
  celikom-private/        <- OUTSIDE document root
    app/                  <- website/app/ (private templates and business logic)
    database/             <- website/database/ (future migrations)
    release-approved.php  <- Stage 10 private release state, NOT present
```

In local PHP built-in server preview only, set `CELIKOM_LOCAL_PREVIEW=1`, use docroot `website/public`, and PHP CLI server. Production `index.php` returns 503/noindex until an authorized release state and CMS entry are installed. Work in `feature/api-range`, do not change `extension/`, `server/`, `android/`, or merge PR #6.

## Work done in Stage 3
1. Parsed the exact v10 ZIP + Excel checkpoint; audited sections, FAQ, image payloads, CSS cascade and breakpoints (1440,1024,768,390,320).
2. Corrected the provisional UI tokens/primitives against actual v10 geometry; no new art direction.
3. Stored screenshot-free v10 reference + private page template.
4. Added private PHP bootstrap, typed content allowlist and output escaping, safe link validation, session/CSRF primitives and PDO factory. **They are foundations, NOT a finished CMS.**
5. Added manual-only deploy with a hard approval gate, plus CI syntax/content/image safeguards. Deployment has **not** run.
6. Added `website/tests/Stage3FoundationTest.php` and `Stage3MarkupTest.py` for future verification.

## Still mandatory
- Stage 3 final component parity check against original v10, real Manrope loaded locally and interaction/browser tests.
- Stage 4–8 section-by-section CMS-aware PHP templates preserving v10, no public site-only release.
- Stage 9 MySQL schema, real owner login + rate limiting, content/FAQ/media CRUD, draft, preview, atomic publish, revision history, restore, protected upload API; ensure no layout editing.
- Stage 10 deploy rehearsal with backup, migrations, health check, rollback; verify admin and private routes cannot be accessed without authentication; upload approved popup via CMS; review all copy/FAQ and rewards with owner; joint launch.
- Test user-visible 2%/20% reward terms against actual production reward policy in a separate CELIKOM app task before public release. Payments are not live.

**Do not add `RELEASE_READY` or `release-approved.php` before Stage 10.**

## Update — original v10 implementation parity

The real v10 page is now split into 5 unchanged CSS assets and 2 unchanged JavaScript assets. `app/Templates/site-v10.html` loads them in the original order, and `tests/Stage3MarkupTest.py` asserts exact source equality after substitution. `database/seeds/faq-v10.json` preserves all 28 FAQ questions and answers; `database/migrations/001_website_cms.sql` is a future, **not-yet-run**, separate database migration. `tests/Stage3SeedContractTest.py` checks both data and schema structure. Pixel-identical local Chromium comparisons passed at 1440, 1024, 768, 390 and 320px with the same fallback fonts; full hosting/font tests are still pending. Stage 3 is **not** owner-accepted. Details: `docs/website/checkpoints/2026-10-17-STAGE3-PROGRESS.md`.

## 17.10.2026 UI-kit verification update

Self-hosted Manrope WOFF2 with OFL license and a keyboard-only FAQ focus ring
are now present; original five v10 CSS and two JS remain untouched.
Offline browser audit: `python website/tests/Stage3BrowserAudit.py`
(after installing pinned Playwright Chromium). CI now runs this along
with PHP/security/rendering tests. Five sizes (1440/1024/768/390/320)
passed in [push run 39062848524](https://github.com/manufact-test/nomusic/actions/runs/39062848524)
and [PR run 39062851976](https://github.com/manufact-test/nomusic/actions/runs/39062851976).
See `docs/website/checkpoints/2026-10-17-STAGE3-UIKIT-QA.md` and
`docs/website/04-MEDIA-AND-ACCESSIBILITY-POLICY.md`.
Older sections describing font work as outstanding are historical.
**Technical QA complete != Stage 3 owner acceptance; no deploy or CMS.**

## Stage 4 first-screen editing safety — update 17.10.2026

Private `FirstScreenDraft.php` supports controlled Header/Hero/demo edits only.
In a **local CLI preview** the two demo state labels may be changed through
`sound.text.07` and `sound.result.restored`. The trusted additive
`public/assets/js/v10/demo-editorial-preview.js` reads escaped
`data-editorial-*` attributes and only writes `textContent`; it cannot
be configured to execute HTML/JavaScript from the editor. The original v10
demo script, FAQ script and all five CSS cascades are unchanged, and untouched
previews still match the approved HTML byte for byte.

Bad local `#hash` targets in Header/Hero are rejected. Tests cover script
injection, URL validation, Unicode/control bytes, five Chromium breakpoints,
mouse/keyboard switching and CTA navigation. Verified specialized CI:
[push 39064380466](https://github.com/manufact-test/nomusic/actions/runs/39064380466),
[PR 39064383865](https://github.com/manufact-test/nomusic/actions/runs/39064383865).
See `docs/website/checkpoints/2026-10-17-STAGE4-DEMO-STATES-QA.md`.
**No public CMS, publication or Stage 3/4 formal acceptance yet.**

## Stage 4 content contracts / 17 October 2026 (v3.7)

The private `FirstScreenFieldCatalog` exposes 27 typed slots (19 text,
7 approved links, 1 demo state) tied to the authoritative v10 manifest.
`FirstScreenDraft` enforces section-specific length limits. The
CLI-only `tools/list-first-screen-fields.php` exports this read-only contract
for a **future**, authenticated Stage 9 editor; it is not an admin route.

Browser QA with valid, longer strings exposed an edited header chip outside
the 320px viewport. `assets/css/v10/editor-copy-safety.css` now prevents
clipped mobile Header and Hero labels **only in a nonempty developer draft**.
The five original v10 CSS and two JS files and the no-edit v10 HTML stay
unchanged. Tests cover 1440/1024/768/390/320 and font/editor security.
CI verified push [39065255480](https://github.com/manufact-test/nomusic/actions/runs/39065255480)
and PR [39065258327](https://github.com/manufact-test/nomusic/actions/runs/39065258327)
on commit `96e844627d44124b295d76179383e6df8fb626fe`.
Stage 3 owner sign-off, real CMS and approved site+CMS release are still pending.

## Stage 5: benefits, three steps and familiar player (v3.8)

A new Stage 5 technical editorial slice reuses approved v10 structure:
`PrincipleFieldCatalog.php` provides exactly 22 scoped text fields,
`PrincipleDraft.php` validates and renders only these fields, with step
numbers `01/02/03` non-editable. This is **not an authenticated CMS**.
`tools/render-principle-preview.php` provides CLI-only preview from
`tests/fixtures/preview-stage5-principle.json` with no writes.
The fixture is intentionally non-public draft copy, not a change to the
approved website. `Stage5PrincipleTest.php` and
`Stage5PrincipleCliTest.py` check exact default HTML parity,
injection protection and blocked unrelated fields. The browser audit
checks principle text, 3 benefit cards, 3 steps and 4 controls on
1440/1024/768/390/320 while original CSS, JS and FAQ remain unchanged.
CI: [push 39066168991](https://github.com/manufact-test/nomusic/actions/runs/39066168991)
and [PR 39066172269](https://github.com/manufact-test/nomusic/actions/runs/39066172269),
both PASS at `4f1017fe3d6033b28614a44c23a98ed1b960b9d6`.
Checkpoint: `docs/website/checkpoints/2026-10-17-STAGE5-PRINCIPLE-SLICE.md`.
No live editor, database migration, deployment or formal owner signoff.
