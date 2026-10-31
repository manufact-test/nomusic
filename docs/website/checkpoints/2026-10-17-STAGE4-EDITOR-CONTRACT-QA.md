# CELIKOM — Stage 4 editor contract and compact-copy QA

**Checkpoint date:** 17.10.2026. **Technical package PASS; owner acceptance NOT implied.**
Branch `feature/api-range`, source of truth is owner-approved sanitized v10.

## Three implemented blocks

1. **Typed CMS editing contract.** Added
   `website/app/src/FirstScreenFieldCatalog.php` with 27 fields
   (19 text, 7 link, 1 dynamic demo state), derived from the original
   `website/app/Config/content-fields-v10.json`.
   Each has a section, type, readable label, safe maximum length and
   original default. `FirstScreenDraft.php` consumes this typed contract,
   preserving XSS escaping, unsafe URL refusal and existing dead-anchor check.
   Test: `website/tests/Stage4FieldCatalogTest.php`.

2. **Long-copy responsive QA and targeted fix.** Created test fixture
   `website/tests/fixtures/preview-stage4-layout-stress.json`.
   Initial Chromium found that a **valid edited** mobile brand and header
   chip could leave the visible 320px viewport while document-wide overflow
   remained hidden. Added `website/public/assets/css/v10/editor-copy-safety.css`
   with natural wrapping, flexible Header sizing and unbroken-word handling.
   This stylesheet is **injected only in a changed, private developer draft**;
   the original v10 styles and the no-edit HTML are unaffected.
   `website/tests/Stage3BrowserAudit.py` now verifies bounding rectangles,
   text containment, demo text switching, expected Header/Hero text at all
   five screen widths: 1440, 1024, 768, 390, 320.

3. **Future CMS field introspection without any public endpoint.**
   `website/tools/list-first-screen-fields.php` emits typed JSON via
   PHP CLI only. Flags declare preview-only and no public admin.
   `website/tests/Stage4CatalogCliTest.py` verifies exact 27 keys,
   valid types, labels, no SEO/media/password exposure and CLI-only usage.

## Verification and preserved boundaries

- `website/tests/Stage4FieldCatalogTest.php`,
  `Stage4CatalogCliTest.py`, first-screen/FAQ/renderer regression and
  Chromium browser checks pass in specialized website CI:
  [push #39065255480](https://github.com/manufact-test/nomusic/actions/runs/39065255480),
  [PR #39065258327](https://github.com/manufact-test/nomusic/actions/runs/39065258327),
  both SUCCESS, code revision `96e844627d44124b295d76179383e6df8fb626fe`.
- Approved reference HTML v10 and its five original CSS and two JS files
  unchanged. Empty `FirstScreenDraft::render(..., [])` is exact source
  bytes. New CSS is draft-only; no replacement or synthetic popup screenshot.
- No authenticated CMS, no MySQL migration, no Hostinger deployment, no
  product backend / browser extension / Android edits and no merge of PR #6.
- Owner must still formally accept Stage 3/4; Stage 9 editor/secured media
  and Stage 10 end-to-end security/legal/real-device QA are mandatory.
- Product copy: trial 3 days, planned $2.99 per month (no active checkout),
  reward 2% per approved unique upload, cap 20% per month with carry-forward,
  promo codes not a widespread permanent promotion.

**Next batch:** continue Stage 4 and prepare Stage 5 sections strictly from
v10. Keep releases blocked until CMS is complete and owner authorizes the
joint site+CMS launch.
