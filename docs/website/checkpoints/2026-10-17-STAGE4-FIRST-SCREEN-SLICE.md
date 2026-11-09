# CELIKOM — Stage 4 first-screen editor/preview technical slice

**17 October 2026.** Three preparatory blocks completed; the owner has
approved v10 visual design but has **not** formally accepted Stage 3 or Stage 4.
The new slice is a developer-only technical demonstration, not an online CMS.

## Files
- `website/app/src/FirstScreenDraft.php`: section-scoped typed editor bridge
  for Header, Hero, demo (`header`, `top`, `sound`) into the existing
  verified/escaping `V10Renderer`. It rejects unrelated fields, URLs are
  validated by `V10Renderer`. No HTML/CSS editor is permitted.
- `website/tests/Stage4FirstScreenTest.php`: unchanged v10 HTML parity,
  safe edits, XSS, disallowed scope, script/protocol-relative URL negatives.
- `website/tools/render-first-screen-preview.php`: PHP CLI-only preview,
  no public admin or database storage, fixed known template and manifest.
- `website/tests/fixtures/preview-stage4-first-screen.json` and
  `website/tests/Stage4FirstScreenCliTest.py`: safe fixture plus invalid
  JSON/editor scope cases with no output on rejection.
- `website/tests/Stage3BrowserAudit.py`: localhost `/audit/draft` browser
  regression at 1440/1024/768/390/320 after constructing preview with PHP.
  Source-v10 vs runtime pixel parity remains checked separately.
- `.github/workflows/celikom-website-checks.yml`: PHP and CLI test plus
  pinned PHP 8.3 for browser job.

## Evidence and limitations
- Stage 4 PHP/CLI validation passed on commit `c97a74b2749b9d7663720a70e6163b66db01ae90`.
- Latest successful combined website PR workflow for
  `3ce2596853e10a644b792163792e1c1803cb3571`:
  https://github.com/manufact-test/nomusic/actions/runs/39063617998
- No live database, authentication, content storage, host publication,
  signed-off real popup raster, screenshot transfer or launch. Both
  browsers in the isolated reference/runtime parity tests use matching local
  Manrope, not third-party Google Fonts; draft may legitimately alter text
  and layout within its permitted slots.
- Existing DOM, five approved v10 CSS files and two approved JS scripts
  remain unchanged; draft only replaces registered content text/hrefs.
- The historical old 3% reward policy stays obsolete. No product app changes.

## Next narrow work, not yet done

Work on dynamic demo-state strings and approved editable content behavior
without hardcoding stale strings after CMS edits. Run safe negative cases,
five-width local browser QA and document as a batch after two or three more
technical blocks. Stage 3 owner acceptance, Stage 9 protected CMS and Stage 10
joint owner-approved release remain independent future gates.
