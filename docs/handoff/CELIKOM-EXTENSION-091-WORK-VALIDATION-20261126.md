# Extension 0.4.91 — Work validation, 26 November 2026

Candidate only; no owner listening acceptance or customer publication.
Read after CELIKOM-EXTENSION-WORK-TRANSFER-20261126.md. The 0.4.90 playback changes remain included.

## Confirmed controller defects and fixes

Three new regression tests failed against 0.4.90 before source changes:

1. During a validated missing-metadata interval, `update()` skipped all native-clock progress updates. A subsequent watchdog tick could restore the original as `master-clock-stalled` despite advancing native playback. Progress is now recorded using the operation's bound track ID during the interval. An actual unchanged clock still fails open; missing/reappearing metadata itself does not reset the clock.
2. The metadata-continuity branch ran before checking enabled/bridge state, so Stop during the interval could leave the replacement running. Global controller controls now take precedence and release the operation before metadata continuity is considered.
3. A user seek while loading from the beginning, to a position within the first five seconds, skipped both intro positioning and mid-song positioning. Such a seek now uses the existing pre-guard decoder alignment. A deferred alignment regression verifies no GUARD_ENGAGE request before positioning completes.

Changed scope: extension controller, three regression tests, extension version metadata and documentation. Android, Windows, server authorization, delivery implementation and CI configuration unchanged.

## Checks actually completed in Work

- Initial 0.4.90 baseline: 437 tests passed.
- 0.4.91: 440 tests passed; full extension ZIP build passed; production manifest validation passed; security build gate passed (67 client files).
- Built API config: https://api.celikom.com. Host permissions remain API + Yandex Music only.
- New candidate ZIP is a local build, not an approved hosted release. The Floki build will have its own receipt/digest; do not substitute the local digest in an approval.

## Browser limitations observed, not playback results

- Work cloud browser rejected navigation to chrome://extensions/ under its protocol/security policy (only HTTP/HTTPS allowed). It explicitly prohibited alternate routes to the blocked operation. No unpacked extension was installed; no Yandex listening test occurred.
- One invocation of the existing synthetic decoder gate was attempted locally with a 90-second outer deadline. It failed before launching Chromium: `/usr/lib/chromium/chromium: not found` (the `/usr/bin/chromium` wrapper exists). No browser/CI repair was attempted. This is not a decoder or playback failure in CELIKOM.
- Handoff run 45864975824 (source 746a43f4) still reported in_progress on its native Chromium step when queried; tests/build had succeeded, spool/security/checksum steps were pending. Do not interpret that stale-looking state as success or claim a verified private release.

## Required next validation/delivery

1. Check the automatic Floki workflow for this source change. Avoid repeated browser infrastructure tuning; retain any actual failure/result.
2. Owner-channel promotion requires the existing verified build/spool receipt and required decoder checks. `.github/release/extension-owner-promotions.json` remains unchanged/empty. No site ZIP or customer baseline was replaced.
3. Once a verified owner ZIP is available, deliver through celikom.com under the existing private owner mechanism; never send an Actions URL. Verify the receipt and protected HTTPS download bytes/hash before giving the URL.
4. Real listening remains required for fresh Start; reload and Play mid-song; fast skips; seek during loading and active playback; Stop during metadata refresh; pause/long pause/resume; VPN changes; displayed song matching actual audio. Passing 440 tests is not listening acceptance.
