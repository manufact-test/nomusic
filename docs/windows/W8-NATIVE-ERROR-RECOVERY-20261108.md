# W8 — one native decoder, automatic original recovery on media error

**2026-11-08. Isolated engineering fixture, NOT an installed Windows Yandex integration.**

## Verified prerequisites

- Owner W3: official Yandex 5.126.1.0 Windows x64 ASAR identity
  `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- W4 source resource adaptation: strict exact-ID / generation fence.
- W5: genuine **public web Yandex** resource/source class use in
  isolated Electron, 35/35 runtime assertions.
- W6: 15/15 synthetic original-file recovery tests. Does not patch Yandex.
- W7: an external Node sidecar genuinely attached to a separate disposable
  Electron renderer over a nonce-gated temporary DevTools port, imported W4
  dynamically and passed **28/28** native source/playback assertions in
  [CI 42514425074](https://github.com/manufact-test/nomusic/actions/runs/42514425074).
  **DevTools is not a safe production plugin transport** and must not be
  enabled on the user's authenticated official Yandex session.

## W8 delivered behavior

`windows-companion/w8/native-original-recovery.mjs` implements
**one-shot**, exact-track native media decoder recovery. It does not create
an audio player, fetch unapproved assets, or touch the installed Yandex
app. The future official native integration (not yet built) would supply
the actual engine's original-source reacquisition and same-decoder setter.

- `setTrack(ID)` owns an exact current ID and invalidates old attempts.
- On an observed **decoder error** (not a mere network stall), the
  contract first blocks further replacements via W4 `original()`,
  then re-acquires the actual original file-info for the SAME track.
- It verifies returned track identity; wrong or missing original is a
  hard stop rather than silently playing an unrelated song.
- It passes the previously captured position and play/pause state to
  the **same media element**, using a freshness callback immediately
  before any native source assignment.
- Additional errors for that track cannot recurse or endlessly retry.
- Rapid Next, Stop or Dispose cancels late callbacks; stale source
  is never eligible to overwrite the new track.
- Logs/diagnostics contain counts/status only: no URLs, track IDs,
  user profile, credentials, cookies or audio data.
- A failure to restore is reported as RESTORE_FAILED, not disguised
  as successful fallback.

## Automated tests

`windows-companion/w8/native-original-recovery.test.mjs` tests the
one-shot recovery contract under synthetic source success/failure,
duplicate notifications, invalid position, wrong ID, Next in flight,
Stop/Dispose in flight, and decoder-assignment faults.

The separate W7 **genuine Electron runtime fixture** now activates W8
after the external CDP attach. After Play/Pause/Seek on a known synthetic
alternate track, it deliberately feeds invalid synthetic MP3 bytes to
the **same** native Chromium media element. The test must observe
the **actual** media error, automatically select the synthetic
original via the real Yandex public source class, restore position
and play state, and prove a second error does not start a recovery loop.
Then it checks Next, long seek, stale request and manual Original/Stop.

These tests do not use real customers' signed URLs or Yandex accounts.
They are valid only for the selected pinned **public** Yandex web build
inside a private offline Electron fixture, NOT for the owner's official
Yandex Music 5.126.1.0 session.

## Remaining integration gap

We still have no documented, authenticated, permission-limited external
source-selection API in the owner's official Windows app. No code
modification, integrity bypass, debugging port or DevTools session will
be applied to the user's official Yandex without explicit agreement and
validated byte-level rollback. Whether its actual decoder/queue
will accept this recovery controller is **not proven**.

Proceed only after verified safe native hook point/official plugin support,
accurate runtime version-gating and a user-approved test.

## Verified W8 automatic original recovery — Windows CI

- Source commit `8e85da515b20f9c9b825d048aef6eaec5dfe106f`.
- [GitHub Actions run 42514969269](https://github.com/manufact-test/nomusic/actions/runs/42514969269):
  **SUCCESS** on Windows with Node 22 + Electron 44.
- **12/12** W8 controller contract tests passed (wrong ID, stale Next,
  Stop/Dispose, duplicate error, original failure, invalid original,
  position/state preservation and diagnostics).
- **33/33** integrated W7+W8 Electron assertions passed: external Node
  CDP attachment → W4 installed into pinned actual public Yandex
  resource classes → synthetic MP3 decodes → native play/pause/seek
  → intentionally corrupted MP3 causes **real HTMLMediaElement error**
  → W8 automatically reacquires synthetic original with same decoder,
  restores position and play state → no retry loop → Next, late seek,
  manual Original/Stop remain functional.
- W6 synthetic rollback, W4 source-gate, W5 original 35/35 regression,
  legacy .NET probe build/safety checks also passed in the same workflow.
- **All media and accounts in these tests are artificial**. The actual
  installed Yandex Music `5.126.1.0` has still NEVER been modified,
  attached to, or proven capable of using W8 in live playback.
- No owner-side test ZIP required. Next engineering gate is a
  permission-limited, authorized and reversible **official-client**
  runtime entry point; our current CDP approach is not production safe.
