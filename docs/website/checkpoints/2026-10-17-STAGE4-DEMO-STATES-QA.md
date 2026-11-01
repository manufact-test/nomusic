# CELIKOM website — Stage 4 demo states and safe first-screen edits

**17 October 2026 · technical blocks complete; NOT a released or
owner-accepted Stage 4.**

## Scope and baseline

Owner-approved visual HTML v10 remains the sole design source. The five
original `website/public/assets/css/v10/00-base..04-v10.css` files,
`sound-demo.js`, `faq.js`, full reference HTML and FAQ 28 seed questions
were NOT edited. Stage 3 remains formally open pending owner acceptance.

## Three coherent technical blocks

1. **Editable visual demo result states.**
   `website/app/src/FirstScreenDraft.php` now supports the original
   `sound.text.07` source result and special controlled preview key
   `sound.result.restored`. Original script v10 hardcodes the restored
   result; the separate
   `website/public/assets/js/v10/demo-editorial-preview.js` is included
   **only** for a local editorial draft which changes one of these keys.
   Two escaped server-generated HTML data attributes store exact labels.
   JS uses `textContent` only, after the approved v10 click handlers,
   preserving `aria-pressed`, `data-mode` and native keyboard buttons.
   With no changes, no attributes or extra script are added: exact v10
   byte-parity is maintained.

2. **Dead-anchor prevention.**
   The first-screen field wrapper refuses a local `#hash` link on an
   editable Header/Hero control unless it refers to a real `id` in the
   immutable approved template. All existing `V10Renderer` safe-URL,
   field scope and HTML-escaping rules continue to apply.

3. **Safety/visual regression.**
   `website/tests/Stage4DemoContractTest.php` checks the canonical
   restored label against original JS, malicious attributes/scripts,
   exact approved HTML recovery after removing only editor-specific
   annotations, UTF-8/emoji, control characters, and length limits.
   `Stage4FirstScreenTest.php` includes dead-link and source-preservation
   tests; `Stage4FirstScreenCliTest.py` checks local fixture output
   and invalid JSON field inputs; `Stage3BrowserAudit.py` verifies
   both edited mode labels, `aria-pressed`, mode changes by keyboard,
   and a keyboard-activated Hero CTA at 320/390/768/1024/1440.

## Evidence

- GitHub revision `53f0925000647b0af1106955e3aad1b380a7ca88`
- [Website CI push SUCCESS 39064380466](https://github.com/manufact-test/nomusic/actions/runs/39064380466)
- [Website CI PR SUCCESS 39064383865](https://github.com/manufact-test/nomusic/actions/runs/39064383865)
- Both jobs in each run: PHP syntax/editor/FAQ/security and local Chromium
  parity/interaction tests. No Hostinger or MySQL deployment.

## Explicit limitations

- The adapter is strictly a developer-preview behavior contract. It is not
  a CMS, does not persist user changes or connect to a live editor, and
  does not change the published state.
- The real owner-supplied popup raster was not uploaded. No personally
  identifiable screenshot or data URI was published to GitHub.
- Payment is still not implemented; public copy must not imply active
  checkout. Product reward policy 2%/approved new unique song,
  20%/month maximum with carry-forward, must be verified separately
  in the application before final launch.
- Stage 9 authorization/CSRF/media/drafts/atomic MySQL revisions and
  Stage 10 QA/owner approval are mandatory for a joint site+CMS release.
- Never touch `extension/`, `server/`, `android/` or merge PR #6
  as part of website implementation.
