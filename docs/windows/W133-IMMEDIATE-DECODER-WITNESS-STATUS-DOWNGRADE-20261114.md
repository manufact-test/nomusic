# W133 — Immediate downgrade when current decoder proof is invalidated — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Exact pre-W133 backup: `backup/windows-main-pre-w133-immediate-source-witness-downgrade-20261114` @ `2958b9d03fdd803eaab2f20dfad3c9bb4c63d1d9`.
- Runtime implementation commits: `61a3c64fd46fdcd563d9d977354abaeb8c44c237`, `d548ed0af0f3717669c1fbcd903fc4f626428c7e`.
- Regression-test/current code-test HEAD: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`.
- Main CI [43608584535](https://github.com/manufact-test/nomusic/actions/runs/43608584535) — **SUCCESS**.
- Windows integration CI [43608584562](https://github.com/manufact-test/nomusic/actions/runs/43608584562) — **SUCCESS**.

## Change

Previously, after the current Yandex decoder had been verified as a CELIKOM signed source, the host could retain the green `NATIVE_SOURCE_VERIFIED` heartbeat until the regular 2.2-second status sample noticed that the source had left, the decoder paused/destroyed, or CDP detached.

The native host now immediately downgrades that exact current track's heartbeat to neutral `NATIVE_MAPPING_ACCEPTED` when CDP invalidates the current playback proof (source-left, not-playing, player destruction, current decoder error, or observer detach). The same `lastStatus` cache is updated immediately; if the local heartbeat request fails, it is restored so the regular sampler can retry. A later fresh signed-current-decoder proof can promote the status back to `NATIVE_SOURCE_VERIFIED`.

This is status/heartbeat handling only. It does not call Yandex player controls, reload the source, alter the queue, change the media URL, or touch audio.

## Regression coverage

- W133 test first proves the exact current signed URL + `kIsPlaying=true` produces `NATIVE_SOURCE_VERIFIED`.
- It then changes the current decoder URL to Yandex original and verifies that `NATIVE_MAPPING_ACCEPTED` is sent immediately, without waiting for the regular 2.2-second sampler.
- The test then restores the signed current decoder and verifies that the next sample can return to `NATIVE_SOURCE_VERIFIED`; immediate downgrade cannot become a permanently stuck neutral status.
- The test also verifies that signed media URLs never enter heartbeat payloads or diagnostics.
- Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed.

## Acceptance boundary

This closes the stale-green timing window in the native status path. It does **not** prove audible output from speakers, and it does not resolve #52 without owner-PC confirmation that «Ты» (13 карат) is actually playing the alternate source. **Issue #52 remains OPEN.**

No installer was built. Continue from live `main`; keep the one-product, exact-backup, no-intermediate-installer rules.
