# CELIKOM website — Stage 3 UI-kit technical QA / 17.10.2026

**Result: STAGE 3 TECHNICAL UI-KIT QA COMPLETED in isolated Chromium; owner
acceptance and release are NOT implied.** This report follows the v3.3
handoff and supersedes only its open technical typography/keyboard QA items.
All remaining host, private media, CMS and Stage 10 gates stay in force.

## Baseline and changes

- The owner-approved v10 `website/reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html`
  remains intact. All five original v10 CSS cascades and both original JS
  scripts remain byte-for-byte unchanged.
- Runtime `app/Templates/site-v10.html` switches only from external
  Google Fonts Manrope to self-hosted licensed WOFF2 via
  `public/assets/css/v10/manrope-local.css`. Four subsets: Latin,
  Latin-ext, Cyrillic, Cyrillic-ext; variable weight 200–800.
- `public/assets/fonts/OFL-Manrope.txt` retains the redistributable
  SIL Open Font License 1.1 from the Fontsource Manrope package.
  Origin: https://github.com/fontsource/font-files/tree/main/fonts/variable/manrope
- A separate `public/assets/css/v10/focus-visible.css` provides a 3px
  keyboard-only indicator for native FAQ `summary` elements. Original
  unfocused/default UI and all five approved CSS assets remain intact.
- The exact CMS text/link schema SHA was updated to the reviewed runtime
  template revision; 91 text, 13 link and 2 metadata fields remain.
- No API, backend product, MySQL schema execution, Hostinger deployment,
  PR #6 merge or public release was performed.

## Automated evidence — GitHub Actions

- Workflow: `.github/workflows/celikom-website-checks.yml`, two jobs:
  PHP/content/security/frozen reference; offline Playwright Chromium audit.
- Latest pass on code revision `f102c1af2e3dda87b0f7fd48834371660207f9eb`:
  push run https://github.com/manufact-test/nomusic/actions/runs/39062848524
  and PR run https://github.com/manufact-test/nomusic/actions/runs/39062851976
- Both jobs completed successfully for each of these two runs. No claim
  about the broad product CI or public hosting is made.

### Chromium with actual local Manrope

| Viewport | Expected header container | Verified | Horizontal overflow | Reference/runtime raster |
|---|---:|---:|---|---|
| 1440 | 1240px | 1240px | None | identical |
| 1024 | 964px | 964px | None | identical |
| 768 | 708px | 708px | None | identical |
| 390 | 354px | 354px | None | identical |
| 320 | 292px | 292px | None | identical |

For every viewport Chromium loaded local Cyrillic and Latin Manrope
(`document.fonts` family `Manrope`, loaded faces and check true);
reference and runtime used **the same** local font CSS, so screenshot
equivalence isolates CSS/JS extraction and the additive focus styling,
not a comparison with unavailable live Google Fonts.
All 11 major sections, 28 FAQ details, five filter controls,
internal anchors, demo mode with correct `aria-pressed`, FAQ
category filters and Enter-key native summary toggling passed.
Keyboard-focused summaries are now asserted to have an indicator
at least 1.5px; shipped ring is 3px.

### Token-color contrast sampling

Computed contrast of representative approved color pairs (WCAG ratios):

| Foreground/background | Ratio | Typical purpose |
|---|---:|---|
| `#0B1013` on `#F7F8F4` | 17.93:1 | body/heading |
| `#556368` on `#F7F8F4` | 5.84:1 | supporting text |
| `#14594D` on `#F7F8F4` | 7.67:1 | links/focus accents |
| `#0B1013` on `#66E0BF` | 11.82:1 | mint CTA label |
| `#33534A` on `#E8F1EC` | 7.36:1 | inactive FAQ tabs |
| `#33534A` on `#66E0BF` | 5.24:1 | alternate mint state |

These token samples meet normal-text 4.5:1 AA, but are NOT an exhaustive
element-by-element contrast or assistive-technology audit.
Original v10 styles include `prefers-reduced-motion` declarations;
the offline browser parity checks also use reduced motion to suppress
timing-related screenshot differences.

## Still pending (correct boundary)

1. **Owner Stage 3 acceptance** of delivered UI-kit and behavior; do not
   silently mark Stage 4 officially started/accepted without stage gate.
2. The original real popup image was intentionally **not in GitHub or
   test assets**. Offline browser tests use a missing media slot in both
   reference and runtime; real screenshot dimensions/content remain a
   separate owner-authorized media integration and visual check.
3. Stage 9: authenticated CMS on dedicated MySQL, draft/preview/publish,
   safe media upload, rollback, access controls, backups and migrations
   after backup rehearsal. There is no functioning CMS today.
4. Stage 10: mobile real-device Safari/Firefox/Chrome and AT/200% zoom,
   privacy review of approved screenshot, full copy/FAQ owner proofread,
   reward-policy verification in the separate CELIKOM product app,
   payment truthfulness and joint site+CMS release authorization.

**Media and accessibility contract:**
[04-MEDIA-AND-ACCESSIBILITY-POLICY.md](../04-MEDIA-AND-ACCESSIBILITY-POLICY.md)

**Next stage once owner accepts Stage 3:** Stage 4 Header + Hero +
non-audio demonstration, preserving approved v10 and the server-safe
content contract. Do not implement fake product playback, rewrite design,
or expose the site before CMS and the explicit joint release gate.
