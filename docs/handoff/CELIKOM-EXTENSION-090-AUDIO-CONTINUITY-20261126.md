# CELIKOM extension 0.4.90 — startup and mid-song continuity

Updated 2026-11-26. Base: main / extension 0.4.89. Candidate branch:
`fix/extension-0.4.90-audio-continuity-20261126`.

## Owner diagnostics reviewed

### Startup stutter / repeated transitions

The first 0.4.89 diagnostic reported `warmLeadMs: 0` on cold joins and repeated restore/activation cycles (8 restores, 7 activations). The MAIN bridge recorded `guard-lost:master-binding-changed` with `detail.reason: track-unknown`.

The controller could only warm a track descriptor after it had a native media element. Yandex can expose confident MediaSession/catalog metadata before that element is registered, so the selected track was not resolved early. Separately, a temporary `awaiting-track-refresh` metadata state was treated as a lost binding even when the exact native resource was still the same. This tore down a valid replacement and caused another resolve/load cycle.

### Mid-song silence after reload

The second diagnostic proves the replacement was muted too late in its own preparation sequence:
- Native playback began at about 14:14:05.281 with the master at 137.018 s.
- The original guard was engaged at 14:14:05.836.
- The replacement was then positioned at 137.579 s and entered `seeking` / `readyState: 1` at 14:14:06.057.
- The replacement was not confirmed ready again until 14:14:08.446. Its stream completed with HTTP 206 shortly afterwards.

The original was therefore silenced before the replacement decoder had completed the seek to the middle of the file. The successful HTTP 206 and completed stream do not indicate a server outage; the ordering of seek and guard acquisition caused the audible gap.

## 0.4.90 changes

1. **Prewarm a selected track before the native media element exists.** When Yandex has confidently identified the selected track, the controller may resolve its authorized descriptor with a null media binding. It does not create an audio element, play audio, or acquire a guard. A later native media element can consume that descriptor only for the same track and within the existing five-second warm window. Actual resolution still goes through the existing entitled-access path and signed-token checks.
2. **Preserve a valid replacement through a temporary metadata refresh.** MAIN and the isolated controller now tolerate a missing track ID only when the adapter explicitly reports `awaiting-track-refresh` (or non-ambiguous unknown metadata), the same media element and resource revision remain bound, the duration still matches, and no playback mismatch is present. A changed source/revision, a positively identified different track, duration mismatch, or other ambiguity still takes the existing handoff/fail-open path.
3. **Align mid-song joins before muting the original.** After the replacement is loaded, the controller asks its decoder to seek to the projected master position and waits for `seeked/canplay` plus `readyState >= 3`. If an MSE seek is beyond the currently buffered range, the original remains audible while the existing sequential range pump fills the required data. The position is refreshed and rechecked against the moving master clock (80 ms acceptance bound) before guard acquisition.
4. **Bounded failure.** Mid-song alignment has a 10-second deadline. If the decoder cannot become ready/aligned, the replacement is discarded and the original remains the audible source; the existing transient retry path is used. No guard is acquired for an unaligned mid-song replacement.

## Regression coverage added

- Descriptor warm-up while track metadata exists but the native media element is absent; later Play consumes the warm descriptor rather than issuing a late resolve.
- `awaiting-track-refresh` keeps a replacement only while the same resource revision, media element and duration remain bound.
- MAIN guard retains the same native resource through a temporary metadata gap, but still starts a handoff for a different track.
- Mid-song activation does not issue `GUARD_ENGAGE` until the positioning promise completes.
- Replacement decoder seek reaches the mid-song position while remaining muted before handoff.

## Scope and release boundary

Only extension source, extension tests, version metadata and this handoff were changed. No Android, Windows, server/API, account/entitlement, paid-feature, production-host or customer-distribution changes.

Candidate version: **0.4.90**. This document does not claim that real Yandex playback is accepted. The owner must test the new candidate on the same scenarios:
- enable CELIKOM and start playback from a fresh page;
- reload Yandex while a song is around its middle, then press Play;
- skip between tracks and observe metadata refreshes;
- seek, pause/resume, and leave the page in the background.

Do not add 0.4.90 to `.github/release/extension-owner-promotions.json` until the Floki build, checksum, native Chromium gate and private owner-delivery checks have all passed. Do not promote to customers or replace the accepted baseline without owner listening acceptance.
