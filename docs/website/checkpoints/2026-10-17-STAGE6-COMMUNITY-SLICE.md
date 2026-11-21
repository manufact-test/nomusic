# CELIKOM website — Stage 6 participation and rewards technical slice

**Date:** 17 October 2026. **Checkpoint:** v3.9. **Working branch:** `feature/api-range`.
**Status:** technical QA passed; **NOT owner acceptance or public release**.

## Package summary

One substantial package comprising three tightly related engineering chunks:

1. **Scoped community and reward headings.** Added
   `website/app/src/CommunityFieldCatalog.php` + `CommunityDraft.php`:
   strict manifest-checked safe editing of 8 `contribute.text.*` fields
   plus 2 reward heading fields. The financial content fields
   `rewards.text.03` and `rewards.text.04` intentionally remain immutable
   in this local Stage6 preview: approved unique upload **2%**, monthly
   **20% / 10 versions cap**, **carry forward surplus**, and the statement
   **payment is not yet live** remain correct. Stage 9 CMS may later
   authorize audited policy changes, but cannot publish mismatched promises.

2. **Rights and moderation safeguards.** Edited
   `contribute.text.08` must retain both necessary rights/permissions
   and the need for moderation/review. Users cannot be told that any track
   may be uploaded without permission. `tools/render-community-preview.php`
   is CLI-only, size-limited JSON-object input, with no HTTP API, no writes,
   no payment, and no interaction with the CELIKOM application.
   `website/tests/fixtures/preview-stage6-community.json` is a harmless
   editorial test fixture, **not** approved public copy.
   Tests `Stage6CommunityTest.php`, `Stage6CommunityCliTest.py`
   cover XSS escaping, rights, category isolation, empty/list JSON, URL
   and policy editing rejection. Stage6 does not implement the upload or
   song-request action; those remain product extension functions.

3. **Chromium browser QA.** The offline `Stage3BrowserAudit.py` added
   `/audit/community` route only in the localhost test HTTP server.
   It validates the 2 participation cards and reward section,
   existing 2%/20%/10-song/carry-over copy, no payment CTA or form,
   original 28 FAQ, no inline scripts and no text overflow at **320,
   390, 768, 1024 and 1440 px**. Original source v10 reference HTML,
   five original CSS, two original JS and approved geometry untouched.

## Evidence and boundaries

- Code SHA: `65018dceaf53f19bf8b3e82940f2e3e2bb91583a`
- [GitHub Actions push 39067165645 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/39067165645)
- [GitHub Actions PR 39067169564 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/39067169564)
- Only `website/**` and website CI workflow changed during this batch.
  PR #6 remains open, unmerged. `extension/`, `server/`, `android/`
  have not been edited. No MySQL migration or Hostinger deployment.
- Stage 3 awaits formal owner signoff. Stage 4/5/6 technically prepared,
  **not signed off**. Stage9 protected CMS and Stage10 joint site+CMS QA,
  legal review and owner-approved release are still mandatory.
- The real approved popup/screenshot must not be committed to GitHub.
- Three-day trial and planned $2.99/month are NOT a current payment flow.

## Protocol change requested by owner (17.10.2026)

**Do not continually update checkpoint documents.** Save NEXT-CHAT,
ROADMAP and checkpoint **only** when the owner explicitly asks, when
handing off to a new chat, or after a genuinely major implementation batch
or many accumulated smaller tasks presenting risk of lost context.
Routine source commits/test fixes remain normal; documentation churn is
not. This supersedes prior every-2/3-tasks guidance.

## Next chat

Read `docs/website/NEXT-CHAT.md` v3.9, Master-TZ v1.2, ROADMAP,
this checkpoint, and code at live branch HEAD. Continue Stage6 cleanup
if needed and Stage7 trust/FAQ according to v10. Do not silently change
financial policy, FAQ content, approved appearance or existing app
code. Do not deploy site before secured CMS and owner approval.
