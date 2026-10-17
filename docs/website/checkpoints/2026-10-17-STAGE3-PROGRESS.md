# CELIKOM website — Stage 3 technical checkpoint / 17 October 2026

**Stage 3 status: IN PROGRESS.** This is a verified implementation checkpoint, **not** acceptance, deployment, or approval to start the next stage without review. Based exclusively on owner-approved v10 handoff.

## What was committed

1. **Original v10 preserved:** \`website/reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html\`; user-provided popup PNG data URI replaced with a controlled CMS media URL and the two embedded identical brand marks changed to approved \`/assets/images/celikom-mark.svg\`. Original ZIP remains with the owner; **do not commit it to GitHub**.
2. **Runtime page wired:** \`website/app/Templates/site-v10.html\` is byte-for-byte equivalent to the sanitized reference **except** for replacement of five \`<style>\` blocks by five linked, unchanged CSS assets and two \`<script>\` blocks by two unchanged JS assets.
3. **UI-kit:** existing \`website/public/assets/css/tokens.css\` and \`components.css\` corrected against real v10 radii, spacing and breakpoints; approved site itself still uses untouched v10 selectors and styles.
4. **PHP front controller:** \`website/public/index.php\` reads the private template and refuses public release until CMS + private release state exist. With a local development preview, it can display the approved template.
5. **Preliminary private PHP architecture:** \`website/app/bootstrap.php\`, \`app/src/Content.php\` (field allowlist and URL validation), \`Security.php\` (session/CSRF primitives), \`Database.php\` (PDO factory). They are NOT a functioning login, owner editor or content publication service yet.
6. **Stage 9 input prepared early:** \`website/database/seeds/faq-v10.json\` contains the exact 28 approved FAQ questions/answers across four actual data categories (plus the "All" UI filter); \`database/migrations/001_website_cms.sql\` specifies an isolated 11-table MySQL/MariaDB CMS schema and atomic pointer-based publication contract. The migration has NOT been executed.
7. **Security boundaries:** existing website deploy workflow made manual-only and guarded; private PHP and SQL deploy outside public_html; release marker not present. Separate website CI checks added. \`extension/\`, \`server/\`, \`android/\` and PR #6 unchanged.

## Verification performed

- **Original file and runtime parity:** compared every extracted stylesheet and script against sanitized v10, reassembled runtime HTML, exact equality of transformed source; passed.
- **Local headless Chromium:** reference vs separated CSS/JS; same 15,141-byte real popup PNG served only from a private local test copy, identical raster images in the local test, external Google Fonts blocked consistently for both. Results at 1440/1024/768/390/320: **zero different screenshot pixels**, no horizontal overflow; FAQ category filter and demo mode switch tested at every width. This is offline regression evidence, **not** proof of live Font/Hosting rendering.
- **FAQ:** all 28 data entries match the original question and answer HTML, in order; seed contains accepted 2%/20% not obsolete 3%.
- **MySQL:** schema *contract* inspected (11 defined tables); no production DB/version/migration execution or backup rehearsal.
- **GitHub Actions:** workflow changes are committed; CI success of remote runs is **not confirmed** from this session. Do not claim deployment or full integration tests passed.

## Open technical work

- Load and license **local Manrope WOFF2** without changing visual metrics, check on actual browsers; no font files have been committed.
- Build a **complete CMS field registry** for all editable texts, links, images, SEO and 28 FAQs without changing the approved HTML geometry.
- Implement protected \`/admin/\` entry and account bootstrap (no default password), real login throttling and CSRF, content editing, media storage with MIME validation, preview, MySQL transactions for publish/rollback, audit log and backup/restore.
- Use a dedicated MySQL database, check real Hostinger PHP/MySQL versions and secure private paths before running migrations.
- Implement section-by-section PHP data binding of v10 preserving typography, interactions, 5 breakpoints. Start with Header/Hero/demo; keep all sections hidden from public until CMS accepted.
- Stage 10: complete responsive visual/browser QA, product fact check, lawful use of real popup screenshot via approved CMS media, owner reviews all texts and FAQ; release site and admin **together**.
- **Separate application task:** verify real reward policy 2% per approved unique upload, cap 20%/month and carry-forward. Do not edit existing product DB or app reward engine from this site task.
- No active checkout: keep $2.99/month as planned and do not depict purchase as possible.

## Transfer rule

Project canonical state: \`docs/website/NEXT-CHAT.md\`; source specification \`docs/website/03-UI-KIT-ARCHITECTURE.md\`; accepted visual basis remains the v10 ZIP. **Stage 3 is not closed.** Next action: finish CMS content registry, then implement site data-rendering contract and guarded preview, before UI-kit acceptance and Stage 4.
