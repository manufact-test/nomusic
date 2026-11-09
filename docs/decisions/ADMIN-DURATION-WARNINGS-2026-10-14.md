# Admin duration mismatch warnings — 2026-10-14

Owner requested a scalable warning for uploaded versions whose duration prevents extension playback. Implemented and deployed backend release `0.4.37-b05ddfc858940c0c86979e3af2056f3cafa7dada`; extension update is unnecessary.

Upload cards and the approval confirmation display an amber warning when the stored audio duration differs from the original by more than 1500 ms, in either direction. The warning gives the exact difference in seconds and states that approval does not fix compatibility. Card durations now retain milliseconds instead of rounding away the discrepancy.

The upload queue includes a catalog-wide mismatch count, a direct link to problem versions, and a duration filter (all / mismatch / within tolerance). Status and duration filters compose safely, and pagination preserves the duration filter. MySQL durations are cast to signed before subtraction so shorter audio cannot raise an unsigned subtraction error. Existing approval actions remain available; this is a warning-only change requested by the owner. No auto-crop/pad or audio mutation occurs. Total duration alone cannot establish whether extra audio is silence or whether the music is aligned.

Validation:
- Full PHP/MySQL/extension/browser CI PASS: https://github.com/manufact-test/nomusic/actions/runs/38550755708
- Gated build, predeploy snapshot and HTTPS deployment PASS: https://github.com/manufact-test/nomusic/actions/runs/38550780852 — its final audit refused a stale revision after the follow-up verification commit, so the overall run is marked failed. This was completed separately below.
- Read-only live render/filter and exact tolerance checks PASS: https://github.com/manufact-test/nomusic/actions/runs/38551127528
- Postdeploy data preservation, private snapshot and isolated MySQL restore PASS: https://github.com/manufact-test/nomusic/actions/runs/38551458096

The regression exercises 1500/1501 ms in both directions, selected filter persistence, pagination, malformed query normalization and combined status filtering. Live verification confirmed the new release and unchanged repaired mappings #18/#21, version 3. On 2026-10-14 at 13:27 Moscow the owner accepted playback of both previously repaired tracks: Холодно (50163040) and Моя игра (48591588).

No schema changes, new grants, account resets or audio/catalog changes were introduced by this admin update. PR #6 stays open/unmerged; Issue #7 stays open. Future repair requests can identify a track by Track ID; the private file can be inspected through the existing Hostinger Actions channel without asking the owner to reattach it.
