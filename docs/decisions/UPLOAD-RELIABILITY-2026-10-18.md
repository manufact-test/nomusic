# CELIKOM 0.4.51 — upload reliability / support evidence (2026-10-18)

## Report and limits
Owner observed MP3 upload stuck at 0% repeatedly, then success without a file change.
0.4.50 diagnostics showed only playback network requests (HTTP 200), not upload.
An apparently successful retry **does not prove** the cause. Do not attribute
the incident to the user, the VPN, or to PHP without correlated evidence.

## 0.4.51 implementation
- The small Chrome action popup only opens a dedicated extension tab at
  `popup/popup.html#upload`. That tab hosts the **same** authenticated
  UI, with the same selected-track and duplicate checks. Losing focus or
  clicking another tab cannot close it or cancel a running upload.
  Closing the full tab/browser still interrupts the request: this is NOT
  server-side resumable/chunked uploading.
- The service-worker message gate allows exactly the old popup URL plus
  the new hash URL, and still refuses untrusted extension/pages/foreign tabs.
- The upload form disables Chrome's native constraint-validation bubbles.
  Required file and rights errors render through CELIKOM dark-theme feedback,
  without native orange system tooltips. Tests cover both cases.
- The upload form has a branded CELIKOM cancellation panel. The user must
  deliberately choose Cancel and then confirm; no native `confirm()` /
  `alert()` is used. Error banners use the current CELIKOM dark palette.
- Attempts record a sanitized journal in local Chrome extension storage:
  25 attempts, seven days, at most 20 events each; initial/preflight,
  connecting, waiting, transferring (coarse milestones), server wait,
  completion, duplicate, failure, explicit cancellation.
  Saved fields are anonymous request UUID, Track ID, file byte count,
  timestamp, upload bytes, percent, HTTP status, bounded error code.
  Never save the file contents/name, credentials, tokens, email or body.
  Diagnostic Copy includes these events even after closing the popup.
- POST uploads send a validated opaque UUID in
  `X-Celikom-Upload-Attempt`. The private PHP error log reports UUID,
  status code and elapsed time, without audio or user credentials.
  This requires server deployment; the extension-only update cannot
  retroactively recover logs for the owner's 2026-10-18 incident.
- After 15 seconds without a first transfer, the UI explains it is
  waiting. At 45 seconds of no bytes it aborts locally as stalled.
  The total POST timeout remains 120 seconds. A completed body transfer
  is shown as **waiting for server confirmation**, not as a guaranteed
  successful submission.
- The server re-checks idempotency and duplicate status before a
  user-initiated retry. Never silently retry a POST whose outcome might
  already be committed.

## Guardrails
No audio library content, mapping, gain, entitlement, payments, trial,
moderation or Android behavior changes. No database migration. No
forced merge of PR #6. Do not automatically deploy to Hostinger before
CI and owner acceptance. Extension bundle must use configured live API,
version 0.4.51 and matching manifests/lock file. Test network stalls,
explicit cancel, error display, auth sender restrictions, upload-success
and duplicate flow. Observe actual-browser acceptance separately.

## Further phase
For uploads that must continue **after closing the entire upload tab**,
build an offscreen/background upload queue with durable file storage and
an explicit consent/retention policy, or a server-supported resumable
chunk protocol. Neither is claimed here; the goal fixed by this change
is accidental focus loss of the small browser-action popup.
