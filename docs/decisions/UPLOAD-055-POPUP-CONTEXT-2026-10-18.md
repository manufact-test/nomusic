# CELIKOM 0.4.55 — popup lifecycle, single-button cancel and invalidated context (2026-10-18)

## Reproduced complaints

Owner's 0.4.54 screenshot confirmed a successful MP3 upload, but:
- Clicking "Загрузить версию" to collapse the panel made it momentarily
  close and immediately expand again.
- A completed upload could be replaced by a fresh upload form for the same
  track, instead of retaining moderation/duplicate status.
- A tiny cancel control sat alongside a tiny progress bar in a permanent
  82px empty slot after completion.
- Chrome extension errors showed "Extension context invalidated" and
  "Cannot read properties of undefined (reading 'local')" inside the
  old content controller wake() after extension reload.

## 0.4.55 fix

- The existing wide mint Submit button becomes a wide red "Отменить
  загрузку" action during transfer; confirmation is the same in-brand
  CELIKOM dialog. It returns to the green disabled "Отправлено на проверку"
  on completion, or a green Retry/Submit action after an error or cancel.
- The slim full-width progress line appears only during an actual active
  transfer/server wait; no permanently reserved empty slot, no little
  cancel button off to the side, no extra browser tab.
- Explicit panel collapse records user intent. Polling updates cannot
  resurrect a closed panel. An in-progress offscreen transfer keeps going.
  Reopening while active restores the same request/progress without
  resetting the file. On completed uploads, server presence verification
  provides the pending moderation/approved result rather than a blank form.
- Existing one-click new-track handling and retry after status errors remain
  intact. Song changes clean up old form selection and request IDs.
- Content controller guards absent/revoked chrome.storage before wake(),
  catches synchronous and asynchronous invalidated-context errors, and
  destroys old controller/watchers rather than throwing. The browser tab
  should still be reloaded once after manually updating the extension.
  Historical errors in chrome://extensions are not automatically cleared.
- No changes to Hostinger, audio library, moderation, entitlements,
  account identity, website or pending PR #6. Client-only version 0.4.55.

## Evidence and acceptance

CI run `39162212729` passed the full extension, backend MySQL and security
test suite with a 0.4.55 Chrome ZIP. Regression tests cover the direct
primary-button cancellation and confirmation, closed panel surviving
repeated status polls, background progress restoration, finished uploads
not offering a new form, and synchronous/asynchronous invalidated contexts.

Manual owner acceptance: install the updated package in the SAME extension
directory without changing its ID, reload the Yandex Music tab, clear the
old extension error history, then verify no new errors; collapse/reopen
the panel both while transferring and after completion. Any previously
uploaded song that is already pending moderation should not be resubmitted.
