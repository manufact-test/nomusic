# CELIKOM website — Stage 5 principle / benefits / player technical slice

**2026-10-17 · checkpoint v3.8**. Working branch `feature/api-range`, GitHub `manufact-test/nomusic`.

## Scope

Next in `docs/website/ROADMAP.md`: section group (04) three installation/replacement steps,
(05) three benefits, (06) preservation of playlists/player actions and ability
to return to original audio. These sections already exist in accepted HTML v10;
this change makes editorial copy safely previewable **without touching**
owner-approved design, its five original CSS files and two JS scripts.

## Three completed engineering pieces

1. `app/src/PrincipleFieldCatalog.php` — typed schema with 22 scoped text fields
   (6 `features`, 8 `how`, 8 `player`), mapped to verified immutable
   `content-fields-v10.json`. Counters `01/02/03` are checked against
   the approved registry and strictly excluded from editor input. String
   length, UTF-8, control bytes and default values are validated.
   `app/src/PrincipleDraft.php` uses original
   `V10Renderer::render()` for safe HTML escaping and blob-SHA verification.
   Unedited HTML is byte-for-byte equal to owner-approved v10.
2. `tools/render-principle-preview.php` — CLI-only 32KB JSON preview without
   network, MySQL, filesystem writes or public URL. Test fixture
   `tests/fixtures/preview-stage5-principle.json` exercises all three
   existing v10 groups with realistic longer copy. PHP unit/regression
   test `Stage5PrincipleTest.php`, Python CLI security check
   `Stage5PrincipleCliTest.py` verify XSS rejection/escaping, scope,
   immutable 3 counters and exact 28 FAQ.
3. Local Chromium browser regression extended with `/audit/principle`
   temporary test route (not in production) to audit **five widths**
   320/390/768/1024/1440. Assert 3 cards, 3 steps, 4 player actions,
   no elements beyond viewport, long-copy placement, FAQ integrity,
   canonical v10 screenshot pixel parity (on the untouched reference/runtime)
   and no inline script injection.

## Evidence

- Code commit `4f1017fe3d6033b28614a44c23a98ed1b960b9d6`
- [GitHub Actions push SUCCESS, run 39066168991](https://github.com/manufact-test/nomusic/actions/runs/39066168991)
- [GitHub Actions PR SUCCESS, run 39066172269](https://github.com/manufact-test/nomusic/actions/runs/39066172269)
- Tests: PHP syntax, Stage3 original/FAQ regressions, Stage4 editing guards,
  new Stage5 PHP and CLI safeguards; separate Chromium UI-kit job.

## Approval and launch boundaries

**This is a completed technical three-piece batch, NOT formal owner
acceptance of Stage 5.** Stage 3/4 signoff remains pending. No genuine
website CMS/authentication/media dashboard; no MySQL migration and no
site/Hostinger deployment. The real owner-supplied popup image must stay
out of GitHub. Product integrations are untouched: `extension/`,
`server/`, `android/`, PR #6 unchanged/unmerged.

### Follow-up

Continue Stage 5 qualitative/content/accessibility review, then Stage 6
community and rewards as read-only scoped content previews on the approved
v10. Don't claim public install/payment availability. Preserve 3-day trial,
$2.99 planned monthly cost (no live checkout), **2% for each approved
unique upload** with **20% monthly cap and carry-forward**.
Prepare a genuine authenticated Stage9 CMS and a user-approved joint
site/CMS Stage10 release before any public deployment.
