# CELIKOM website — controlled media, accessibility and typography contract

**17.10.2026 · Stage 3 technical policy · no public deployment.**
This contract applies to the small CELIKOM website CMS only. It does not alter
`extension/`, `server/`, `android/` or the open PR #6.

## 1. Design authority and typography

- Accepted v10 is the single visual baseline. Keep the five original CSS
  cascade files unchanged. Additive files may fix delivery/accessibility only;
  they must not alter the unfocused/default appearance or approved page geometry.
- Runtime self-hosts the original `Manrope` family at weights 200–800,
  serving version 5.3.0 Fontsource variable WOFF2 subsets for Latin, Latin-ext,
  Cyrillic and Cyrillic-ext from `website/public/assets/fonts/`.
- Manrope is licensed under SIL OFL 1.1. Include
  `website/public/assets/fonts/OFL-Manrope.txt` in the deployed public assets.
  Do not add font files to user-facing handoff archives unless redistribution
  includes the license. Browser test must load Cyrillic and Latin without
  `fonts.googleapis.com`/`fonts.gstatic.com` calls.
- `manrope-local.css` precedes the five original v10 CSS files.
  `focus-visible.css` is a separate focused-state-only override.
- Verify 1440, 1024, 768, 390 and 320 px, container widths, document overflow,
  keyboard navigation, focus indicators, FAQ filters, demo mode, and reduced
  motion. Reference/runtime screenshots may use **the same local font** for a
  fair pixel-drift comparison.
- Final Stage 10 screenshot verification must use the actual owner-approved
  popup raster, **not** a fabricated or synthetic image. Offline tests without
  that private raster do not certify its real appearance.

## 2. Immutable brand assets vs editable media

| Slot | Allowed treatment |
|---|---|
| Brand mark | Approved SVG shipped as `/assets/images/celikom-mark.svg`; not editable HTML |
| Approved popup screenshot | Controlled CMS-managed media slot `celikom.popup.approved` at `/media/celikom-popup-approved.png`; owner consent required |
| Other editorial photos | Stage 9 CMS-controlled file ID; never raw arbitrary `src` supplied as HTML |
| Icons/decorative SVG | Only trusted, reviewed in-repository SVG; disallow arbitrary uploaded SVG/XML/HTML |
| FAQ | Plain-text editor, no arbitrary HTML/image embedding in FAQ answers |

The sanitized reference and runtime template intentionally do **not** contain
the original popup's base64 PNG. The missing media slot in offline Stage 3 tests
is expected; the screenshot must not be committed or redistributed via GitHub.

## 3. Stage 9 media implementation requirements (NOT implemented yet)

- Upload endpoints require authenticated administrator, CSRF verification,
  rate limits and server-side authorization. Do not trust browser MIME,
  extension, filename, request metadata or dimensions.
- Initial allowlist: PNG, JPEG, WebP; sniff content using PHP `finfo` and
  decode/inspect server-side; reject SVG, scripts, polyglot/invalid files.
  Define and test bounded upload size (initial 5 MiB maximum), pixel count
  (initial maximum 20 million) and dimensions. Strip EXIF/metadata where
  possible, encode approved outputs and cap storage usage.
- Store raw upload bytes outside `public_html`; use random server-assigned
  filenames and immutable media IDs, unique revision references and checksum.
  Serve only approved media IDs via a controlled public resource handler,
  or publish sanitized approved derivatives to a dedicated non-executable
  directory. Send correct Content-Type, nosniff and restrictive caching.
- Never directly make arbitrary private uploads web-visible; disable PHP/script
  execution in media directory. Prevent `../`, null bytes, symlink traversal,
  arbitrary local-file access, remote SSRF and URL-scheme injection.
- Preserve existing published images and rollback references when deploying
  code; no source deployment must overwrite owner content.
- Hold the real screenshot for owner consent/redaction review; exclude account
  identifiers and personal data before approval. Keep originals private.
- Publishing switches page content and its media revision **atomically**.
  Draft preview requires authentication. Audit who approved/published an image.

## 4. Accessibility release rules

- Maintain one `h1`, meaningful `h2` section hierarchy, meaningful anchors,
  language `ru`, accessible labels for the demo, FAQ buttons with
  `aria-pressed`, keyboard-expandable native FAQ `details/summary`.
- Contrast target WCAG AA: normal text 4.5:1, large text/UI indicators 3:1,
  including hover/active/focus/disabled states where appropriate.
- Focus indicators must be visible at a minimum in links, buttons and
  `summary`; do not remove browser outline without a stronger replacement.
- Respect `prefers-reduced-motion` and avoid keyboard traps. Scrollable FAQ
  category pills must still be accessible by keyboard.
- Real mobile touch QA, zoom/200%, VoiceOver/TalkBack/NVDA, Safari/Firefox,
  owner screenshot and production font/hosting performance remain Stage 10
  acceptance tasks; GitHub Chromium checks alone cannot certify them.

## 5. Explicit release boundary

A PHP template and CLI preview are **not a CMS**. Stage 9 must deliver login,
roles, CSRF, MySQL draft/publish/rollback, revisions, backups, safe upload
and private/public path isolation. Production stays 503/noindex until site
**and** CMS pass Stage 10 together and the owner authorizes the joint launch.
No MySQL migrations, Hostinger deploy, reward-engine changes or PR #6 merge
are authorized by this contract.
