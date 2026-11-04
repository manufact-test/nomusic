# CELIKOM desktop: current accepted reference

**0.4.73 is the MAIN OWNER-ACCEPTED DESKTOP REFERENCE as of 2026-11-04.**

The owner confirmed that approval of a version while listening now produces an audible but orderly transition, with playback continuing normally, and explicitly asked to keep this behavior. Do not chase an inaudible transition or alter this accepted sound without a new request. Opening words were accepted as well.

## Frozen source and deliverable

- Repository: `manufact-test/nomusic`.
- Frozen accepted branch: `archive/desktop-0.4.73-accepted-20261104`. Create once at the acceptance documentation commit; never move it for subsequent work.
- Working branch at acceptance: `feature/desktop-073-complete-file-live-join-20261104`.
- Extension functional source commit: `b081a2fa6c97c8a0373da6598fe08276eb757245`.
- Final verified source/harness commit: `7b9c0656db9a78dd6d37af25c0c470129143c45a`. Later acceptance changes are documentation only.
- ZIP: `celikom-extension-0.4.73.zip`, 2,489,476 bytes.
- SHA-256: `d6689e9d1e7157572e64622864d8c84ec98ec80f286e4aec4cf6fa31bee1a5b8`.
- Persisted ZIP: `libfile_a4ccee7d8e4481919e0d5bac02be72ab`. Do not rebuild/replace this accepted artifact under the same identity/version.
- CI run `41791574411`: 360 regressions and real Chrome, Brave Linux and Brave Windows media tests passed. Owner listening/live-approval acceptance is separate and now confirmed.

## Behavior to preserve

Bounded intro wait prevents the native clock advancing while the opening replacement prepares. Newly available MP3 after an earlier negative lookup is downloaded as a complete signed, bounded native file; original continues playing until a muted decoded position is aligned and ready for handoff. Keep authority, exact-ID/duration/source fences, cancellation, pause/seek and account restrictions. Full details: `LIVE-APPROVAL-073-COMPLETE-FILE-2026-11-04.md`.

## Older versions and scope

- 0.4.71 WITHDRAWN after owner reported the entire Brave window closing. Cause of that closure remains unproven; do not reintroduce its incomplete MediaSource live-join mechanism.
- 0.4.72 is a rollback-only reserve, not owner-accepted and not a replacement for this reference.
- 0.4.70 is an earlier INTRO-only accepted reference; its live approval was rejected.
- 0.4.68 remains preserved as an older accepted fallback.

New desktop experiments must branch from this frozen 0.4.73 reference and leave it intact. This acceptance does not authorize server deployment, moving the backend stable branch, or Android edits. Android is maintained in another chat.

To restore the accepted package: stop playback, replace the files in the existing unpacked extension folder with this exact ZIP, reload the extension, refresh Yandex. No uninstall or account-data clearing.
