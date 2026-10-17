# CELIKOM website — implementation workspace

**Status 2026-10-17:** Stage 3 foundation only. **NOT deployable.** The accepted visual source is the independent HTML v10 viewer, which must be supplied/verified before detailed section implementation. Do not redraw the accepted design.

## Boundaries
- All site work is isolated under `website/` and `docs/website/`.
- Do not change `extension/`, `server/`, `android/` or merge PR #6.
- Website and small protected PHP/MySQL content CMS are one release. There is no public site until both are accepted.
- Main requirements: `docs/website/MASTER-TZ.md` v1.2; latest transfer `docs/website/NEXT-CHAT.md`.

## Planned structure
```
website/
  public/
    index.php                 # Stage 4+, not created yet
    admin/index.php           # Stage 9, authenticated PHP entry point
    assets/css/tokens.css     # Stage 3
    assets/css/components.css # Stage 3
    assets/                   # approved fonts, safe SVG, images, JS
  app/
    bootstrap.php             # Stage 9, server-only code (outside document root)
    templates/                # controlled PHP sections
    auth/                     # session, roles, CSRF, rate limits
    content/                  # rendering, revisions, publishing
  database/
    migrations/               # Stage 9; NEVER public
  tests/
    ...                       # checks for UI, security, deployment
  RELEASE_READY               # NOT present until owner-approved Stage 10
```

## Deployment boundary
`.github/workflows/deploy-celikom-website.yml` is manual-only and gated. It deploys ONLY `website/public/.` to the Hostinger domain's `public_html/`; `website/app/.` and `website/database/.` go to sibling `celikom-private/` outside the web root. Missing PHP/CMS and `RELEASE_READY` block every deploy. It has NOT run. Before final release, test PHP private-path resolution, backups, migrations, rollback, production file permissions, and Hostinger constraints. Never commit credentials or user screenshot/real popup image from the v10 archive.

## Content model
The CMS edits allowlisted content keys (`hero.title`, `hero.cta.label`, etc.), media refs, FAQ items/categories and SEO; it does not permit arbitrary HTML/CSS/JS or page layout changes. Public reads use a single atomically published version; draft previews require an admin session. Content survives code deployments.

## Working rules
1. Compare each implemented section visually to **v10** on 320/390/768/1024/1440 px before calling it done.
2. UI tokens in `tokens.css` are initial technical values; refine measurements against the approved v10 HTML, not a new design.
3. Keep FAQ at 28 approved questions in five horizontal categories; desktop two columns / mobile one. Payment is NOT active. Reward rate is **2%** per approved unique uploaded version, **20%** monthly cap with carry-forward.
4. Final owner copy review is a last-stage gate, followed by site + CMS QA and joint publication.
