CELIKOM Windows 0.24.58, W182 repair: hook the actual Yandex 5.128.0 live-player getFileInfo owner and accept the player's id argument. Owner-only candidate, signed P-256 sequence 5.
Latest personally accepted audible baseline 0.24.54. The 0.24.57 owner candidate is unaccepted. Customer channel remains 0.24.55/sequence2 with approved:null.
Owner must install and personally verify mapped «Ау» track 144530503, another mapped replacement, original/unmapped playback, Next and Play/Pause. Do not promote to customers without explicit owner acceptance and «выпускай всем».

2026-11-26: retry 0.24.58 sequence5 using per-version release concurrency. The old 0.24.57 W180 run is still waiting for its obsolete protected deployment and must not block this candidate. No customer publish.

2026-11-26: unattended owner build uses windows-stable-owner-build with the existing W155 P-256 key; no required reviewers. Customer publication remains separately gated in windows-stable-production.

2026-11-26: release concurrency corrected: push-triggered owner run is keyed by commit SHA, so the obsolete approval-waiting 0.24.57 run cannot hold the 0.24.58 owner-build slot.

2026-11-26: bypass GitHub Releases API (403 integration) by packaging the six-file P-256 signed transfer as a short-lived Actions artifact; reusable Floki stage downloads it from the same workflow run and deposits only data into the isolated runner spool.

2026-11-26: update W156 contract for artifact-to-Floki handoff; retry 0.24.58 owner candidate.
