# CELIKOM 0.4.52 — upload continues without opening a tab (2026-10-18)

## UX decision and correction
Owner rejected the 0.4.51 approach of redirecting the Upload Version
button to a full browser tab. The accepted UX remains the **original tiny
CELIKOM extension action popup**. No visible new tab/window is opened.

The owner also reported unintended upload cancellation on popup blur,
sometimes after most of the audio had already transferred. This is a genuine
lifecycle problem: Chrome destroys a popup when focus changes. The accepted
solution is a Chrome MV3 **offscreen document** carrying out the HTTP upload
after user selection and explicit Send in the regular popup.

## Implementation
- Original popup HTML/CSS is reused; native Chrome constraint bubbles were
  previously replaced with CELIKOM themed validation. No tab redirection.
- The submitted File is placed in extension-origin IndexedDB temporarily (not
  chrome.storage.local, not a publicly accessible URL). Max file size 30 MiB.
- Popup performs the existing strict duration/track/rights/status checks,
  then asks the service worker to start the offscreen document. The POST runs
  in the offscreen document with the existing server idempotency request ID.
- Browser popup can close due to loss of focus; the offscreen document keeps
  the XHR. New popup instances read bounded, sanitized status from
  chrome.storage.local and show progress, server-wait, success/failure.
- The offscreen document has only runtime messaging access. The service
  worker checks sender origin/URL and persists stripped-down events; no
  audio bytes, filenames, tokens, email, or raw requests are in diagnostics.
  Offscreen worker deletes the local staged file after completion/error.
  Expired staging records are rejected; credentials are never put into IDB.
- Explicit Cancel opens a CELIKOM-branded confirmation, then signals the
  offscreen document. The original action popup never aborts on blur.
- The POST is not automatically retried after an unknown result. Server
  duplicate/idempotency checks are preserved. Server-side diagnostics
  from 0.4.51 require no new backend release.

## Important limitations
- The popup must stay alive during brief local staging / authorization before
  handoff to the offscreen worker; closing it *before the handoff completes*
  may require file reselection. Once handoff succeeds, the document is
  independent of popup lifetime. No server chunk/resume protocol exists.
- Shutting down Chrome/extension or explicitly cancelling can interrupt
  the active request. A full-browser restart cannot resume uploaded bytes.
- No automatic release or update to end users. Package and browser acceptance
  gates must pass before owner installs 0.4.52.
- Do not merge PR #6 or alter existing approved audio, moderation, subscription,
  rewards, DB records or live website. This is a browser-extension-only fix.

## Verification gates
Run extension tests, repository lint, security audit, packaged manifest
validation and configured ZIP build. Dedicated tests must assert no new tab,
offscreen completion with no popup present, explicit cancel and old worker
security guards. Then owner should manually send a harmless new audio version,
click outside the popup at 30%-80%, reopen CELIKOM, confirm background
progress/completion and verify duplicate protection. A static test cannot
substitute for actual Chromium lifecycle testing.
