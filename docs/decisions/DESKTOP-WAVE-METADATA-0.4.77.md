# Desktop 0.4.77 — bounded MediaSession clear on My Wave

2026-11-18. Browser extension only. No server, Android, Windows or production deployments.

Owner diagnostics: `Вставленный текст(20261118-163301).txt` and `Вставленный текст(20261118-163409).txt`, both version 0.4.76. Multiple active tracks repeatedly enter `guard-lost:master-binding-changed` with `track-unknown` immediately after `media-session-metadata`. The same ID returns 8–13 ms later on the same ready media element. API responses are successful. Example: track 136487137 activates at 16:33:56.799Z, restores at 16:33:57.034Z and activates again at 16:33:57.198Z.

## Change

Only playback behavior delta is in `extension/src/adapters/yandex-music-adapter.ts`. A null MediaSession assignment may retain the immediately preceding object for at most 40 ms internally, on the exact same master element, assigned source, current source, duration and usable readiness. Native MediaSession remains untouched. Actual non-null metadata is observed immediately, cancels the grace and still reports genuine new-track identity synchronously. A repeated null cannot renew the deadline. A one-shot timer flushes persistent absence, and unmount cancels it.

Both metadata matching and source-freshness comparison use the same effective object; polling and media events during the small gap therefore cannot invalidate an otherwise unchanged binding. Source changes, emptied media, ended state and duration changes cannot use the grace. Original guard/controller, admission fence, streaming, gain, seek, audio player, approval handoff and permissions are unchanged. No MediaSource live-join or rejected native-engine experiment is reintroduced.

## Checkpoints and verification

- Base: accepted support build 0.4.76, `da837585379373e356be0b93bb956a1e97f9ada3`.
- Explicit immutable recovery branch: `backup/desktop-0476-before-wave-fix-20261118`.
- Work branch: `fix/desktop-wave-metadata-20261118`.
- Code: `b6eff7efef5c29ffa52c23e1ef40278d159b3fe8`.
- CI **44351282060**, job **134967279348**: SUCCESS.
- 369/369 extension tests, manifest validation and security gate PASS.
- New controller regression: six null/restore cycles with intervening polls/timeupdate do not recreate the replacement (activationCount 1, restoreCount 0); pause/resume still apply.
- Bounds, no renewal, genuine new-track metadata, resource/readiness/duration changes and timer cleanup checked.
- Actual headless Chrome with native MediaMetadata setter and HTMLAudioElement on a local synthetic WAV fixture: baseline 0.4.76 fails with `Identity lost during same-song refresh`; 0.4.77 passes eight 9 ms refreshes, actual source change and persistent clear.
- Local Chrome could not start because socket creation is denied by the execution environment; the real-browser test ran successfully in GitHub Actions instead. No owner Yandex session was accessed and no live My Wave listening test is claimed.

## Package

`celikom-extension-0.4.77.zip`: 2,490,658 bytes.
SHA-256: `9975ac20cee5a7e50dcd2213905a0e89187961448d62df85b52c9867802827d5`.
Local package and CI package hashes match. API origin is preserved from 0.4.76; no secrets bundled.

Owner acceptance remains pending: replace unpacked extension files, click Reload in Brave extensions and refresh Yandex Music. Compare affected My Wave starts/repeated seeks, native Next and album playback. If undesired behavior appears, restore 0.4.76 from preserved backup; 0.4.73 reference is untouched.
