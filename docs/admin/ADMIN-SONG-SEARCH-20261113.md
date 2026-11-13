# Admin song search — 2026-11-13

User request: find songs among approximately 1,500 uploads without scanning every page.

## Scope and behavior

- Search field `q` in Uploaded versions and Song proposals, alongside existing filters.
- Matches partial title, artist or Yandex Track ID over the entire filtered catalog before pagination.
- Case-insensitive Unicode comparison using the existing utf8mb4_unicode_ci collation. Multiple words may appear in either title/artist order.
- Retains q, status, duration and page size in pagination. Submitting filters starts at page one; clear-search link retains other filters.
- Empty results are explicit. Bounded UTF-8 query, parameterized SQL, literal `%`, `_`, `!`, escaped HTML. No schema/index migration for this catalog size.
- Playback, client packages, audio files, auth, entitlement, billing and moderation actions are unchanged.

## Exact live deployment, not a historical server overwrite

Branch: `feature/admin-song-search-20261113`, based on support branch at `239ef790e2224fa9ab678a16094b5b2fb096187c`.

A read-only SSH inspection run **43431021469** found active release `browser-support-076-b807cd691074` with additional bulk-moderation code absent from the historical branch. That code MUST be preserved; do not deploy the branch's entire AdminPanel or server directory.

Only `src/Admin/AdminPanel.php` in a fresh clone of the current immutable release is patched with checked exact anchors:

- Before SHA-256: `15aa4414bf3257730693a6a25d9d39578e15f27fe08a4e1d1f7557284022d69a`
- After SHA-256: `7c5d63e5dbb6182daa55a4c8b31f2a98f070844fd34e995ec5f8e596d7160d25`
- Payload: `.github/scripts/admin-search/manifest.json` and `patch.php`.
- Deployment entry: `.github/scripts/admin-search/deploy.sh`.
- Workflow: `.github/workflows/admin-song-search-20261113.yml`, specific branch and path triggers, concurrency group `celikom-hostinger-private-test`.

A mismatch aborts without switching production. The deployment copies current release, backs up its AdminPanel and public launcher, checks that only AdminPanel changed, performs candidate checks against real catalog, switches current atomically, then checks authenticated HTTPS search and public config. A failure after switch automatically restores the previous symlink.

Release intended by deployment commit `4bf2ac5111423b4d5d5ee5adf9c0cd7642942fd7`: `admin-song-search-4bf2ac511142`.
Backups under `$CELIKOM_ROOT/backups/admin-song-search-4bf2ac511142/` include `previous-release`, `AdminPanel.php`, `public-index.php`.

## Validation

- **43431543825: PASS** on MySQL 8 / PHP 8.3. Dedicated transactional fixtures cover cross-page search, title/artist/ID, Cyrillic case, multiple words, filters, literal wildcards, invalid UTF-8 and array input, XSS and SQL payloads, proposal queue and its paging.
- Existing `server/tests/admin.php` suite passes, including moderation, rights, CSRF, protected Range preview, concurrent approvals, grouping, gain and trial resolution checks.
- Candidate and live smoke use real existing catalog rows with read-only queries. Temporary five-minute session for an existing owner is removed in finally; no new admin, catalog writes, uploads, moderation, emails or trials.
- **43431822607: PASS** (verify job `131906937397`, deploy job `131907250969`). Exact patch, single-file delta, candidate real-catalog checks and authenticated HTTPS live search all passed. Active release is `admin-song-search-4bf2ac511142`; other components and catalog counts were preserved.

## Operational note

Future server deployments must carry this search delta forward along with the previously deployed bulk-moderation and shared support changes. Do not roll production back to the older branch's whole server snapshot. Docs-only updates use `[skip ci]`; do not retrigger the fixed-before-hash deployment after another release changes AdminPanel.
