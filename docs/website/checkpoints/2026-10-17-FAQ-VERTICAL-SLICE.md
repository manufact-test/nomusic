# CELIKOM website — FAQ v10 server-side vertical slice / 17.10.2026

**Status: TECHNICAL SLICE COMPLETE; owner acceptance and site launch NOT implied.**
This is a self-contained and tested server rendering component within unfinished Stage 3 / planned Stage 7–9 implementation. It does not create an admin GUI, modify MySQL or publish the site.

## Source of truth and files

- Approved visual DOM: `website/app/Templates/site-v10.html`, protected by its v10 content-field manifest.
- Original FAQ content: `website/database/seeds/faq-v10.json`, 28 seed questions across categories `start`, `rewards`, `music`, `help`. The UI has a fifth "all" view, not a fifth data category.
- Server renderer: `website/app/src/FaqV10Renderer.php` (protected PHP, not served as a public path).
- Text/link renderer: `website/app/src/V10Renderer.php`.
- Protected site entry: `website/public/index.php`, validates v10 content and FAQ seed. Public route stays **503/noindex** unless the Stage 9–10 CMS+release gate is actually satisfied.
- CLI-only joint draft preview: `website/tools/render-local-preview.php` (not inside public web-root).
- Sample composed draft: `website/tests/fixtures/preview-v10-faq-overrides.json`.
- Tests: `website/tests/Stage3FaqRendererTest.php`; CI `.github/workflows/celikom-website-checks.yml`.

## What this large block now does

1. **Exact baseline:** compares all 28 seed FAQ IDs, categories, questions, paragraph answers, sort positions and visibility against the original trusted FAQ HTML. With no draft it returns the **identical page bytes** (CSS, icon SVGs, markup, filters and spacing unchanged).
2. **Edit existing items:** approved draft may replace `question` or plaintext `answer`, set `category`, `sort_order` and `is_visible`. It cannot edit the original SVG, CSS or arbitrary markup.
3. **Hide without deletion:** `is_visible=false` removes the item from rendered visitor FAQ; baseline data remains intact. The future CMS can implement unhide/restore through revisions.
4. **Add items:** up to **100** total FAQ entries with unique `faq-question-NN` IDs, typed required fields and approved category keys. New HTML uses the same trusted v10 `details/summary/svg/p` skeleton.
5. **Reorder and move categories:** stable numeric `sort_order` (tie-break by original position) and one of exactly four known `data-category` values. Existing FAQ JS filter and "no questions" state remain unchanged; no new dependency added.
6. **Safe input:** questions/answers are **plain text only**; output HTML-escaped. Invalid UTF-8, dangerous control bytes, unknown IDs/attributes/categories, oversized text, duplicate new IDs, arbitrary HTML/JS fields and malformed draft structure are refused. No arbitrary media or hyperlinks may be inserted by FAQ content.
7. **Composed preview:** CLI accepts both legacy flat content-key overrides and combined `{"content": {...}, "faq": {"updates": {...}, "new_items": [...]}}`. A combined draft changes Hero and FAQ together without changing public state or touching database.
8. **Automated regression:** checks unchanged exact render; mixed edits; category changes; sort; hide; add; escaping of attempted script/img injection; unauthorized edits; and real CLI-generated HTML. GitHub website CI success confirmed for commit `c93d42b23eade6c78b312563597fdccde9deb0e2`, runs [39061066048](https://github.com/manufact-test/nomusic/actions/runs/39061066048) / [39061062241](https://github.com/manufact-test/nomusic/actions/runs/39061062241).

## Local developer example (no production effect)

```bash
php website/tools/render-local-preview.php website/tests/fixtures/preview-v10-faq-overrides.json > /tmp/celikom-faq-preview.html
```

The HTML references local CSS/JS assets; serve them only in a permitted developer preview environment to inspect visually. The CLI does **not** act as a public admin, public API, or publication step. It uses example-only text, not live user edits.

## Frozen product/visual rules

- Approved CELIKOM v10 page and original popup screenshot remain source of truth; do not redesign.
- 3-day trial; planned $2.99/mo (not live); **2%** reward per new approved unique upload, **20%** monthly ceiling, extra credit carries forward; suggestion without upload earns no reward.
- No unverified royalty guarantees or payment activation claims.
- No deploy to Hostinger; no MySQL migration; no app modifications under `extension/`, `server/`, `android/`; PR #6 remains open/unmerged.

## Next-chat boundaries (do not overclaim completion)

- **Completed:** technical FAQ data-to-HTML binding and draft rendering contract with automated tests.
- **Not completed:** browser admin UI, authentication, CSRF/roles/rate-limit, MySQL draft/publish/rollback, real media upload, WOFF2 font license/local loading, full Stage 3 UI-kit sign-off, Stage 4+ per-section owner reviews, final live QA/deploy.
- **Next productive task:** finish and document Stage 3 design-system acceptance checklist (local Manrope metrics, reusable primitives, accessibility states). Then advance stage-by-stage on accepted v10 sections. At Stage 9 wire these renderers to authenticated CMS draft/published atomic snapshots, not earlier and not publicly.
- **Canonical handoff:** `docs/website/NEXT-CHAT.md`; roadmap/master rules still apply.
