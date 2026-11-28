# W195 — Repair 0.24.62 installed-client bootstrap route (2026-11-28)

## Result

The owner PC was still running **CELIKOM 0.24.62.0**. Its diagnostic (W54, generated 2026-11-28 09:48:27 UTC) showed:

- `STABLE_UPDATE_CHECK_FAILED` immediately after startup.
- `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE` immediately before it.
- The same updater failures had already appeared on 25–27 November.
- The installed app otherwise initialized the bridge and player observer normally.

## Root cause

The signed customer stable feed already served **0.24.63 / sequence 10**, but the currently installed **0.24.62** client first authenticates its own immutable installed-version manifest and seeds its exact last-known-good installer before it can safely evaluate/install a newer release.

The public customer version store contained the accepted baseline 0.24.55 and the newly approved 0.24.63, but was missing the immutable **0.24.62** manifest, detached signature and installer. The exact 0.24.62 release still existed in Floki's private signed immutable release store. Because the client's first bootstrap request for its installed version could not be satisfied, the coordinator failed before reaching the already-published 0.24.63 latest manifest.

This was **not** a missing P-256 trust pin. The checked-in source defaults are intentionally empty; the protected release workflow derives the public key from the private Environment secret and embeds the fixed production origin and public P-256 pin into the actual release binaries via `.github/scripts/windows-stable-trust-embed.mjs`. The 0.24.62 diagnostic proves the updater path was active.

## Repair performed

Through the existing protected Floki maintenance path, copied only the exact signed 0.24.62 immutable bootstrap/rollback files from:

`/srv/celikom-releases/windows/stable/versions/0.24.62`

to the existing public customer version directory:

`/srv/celikom-releases/public/windows-customer-stable/versions/0.24.62`

Pre-copy checks verified:
- P-256 public key fingerprint: `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`.
- 0.24.62 manifest version/sequence: `0.24.62 / 9`.
- Installer size: `85,156,133` bytes.
- Installer SHA256: `5daad26eefeacca7b3f1a08c7d6fe0c07bc50e73ae9d601b5a7d71f4be1f37a9`.
- Detached signature verified with the pinned P-256 key.

Public HTTPS verification passed for the exact 0.24.62 manifest, signature and full installer download/hash.

**No change** was made to:
- `latest.json` or `latest.json.sig`;
- customer accepted record;
- current stable version or the 0.24.63 sequence;
- Nginx configuration, owner downloads, API, audio runtime, Android or browser extension.

The already-approved public latest feed remained byte-identical at **0.24.63 / sequence 10**, with its existing acceptance record unchanged.

- Successful Floki maintenance workflow: [46132668967](https://github.com/manufact-test/nomusic/actions/runs/46132668967).
- Final output: `W195_PUBLIC_02462_BOOTSTRAP_AND_ROLLBACK_HTTPS_VERIFIED_LATEST_02463_UNCHANGED`.
- One-time maintenance request was cleared after success.

## Owner retest — FAILED after server repair

The owner relaunched 0.24.62 after the public route repair. Fresh W54 diagnostic generated at 2026-11-28 10:13:32 UTC still reports:
- `AppVersion=0.24.62.0`
- `STABLE_UPDATE_CHECK_FAILED` at 10:12:25.392Z
- `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE` at 10:12:35.643Z
- no verified download/waiting-for-safe-point or installer-start event.

The two new uploaded diagnostics are duplicate copies of the same snapshot; there is no distinct after-Stop snapshot. The route repair itself remains verified, but it was not sufficient to make this client update. The earlier conclusion that missing public 0.24.62 files were the sole cause was premature. See `docs/windows/W196-OWNER-OTA-RETEST-FAILED-2026-11-28.md` for the source analysis and next engineering task.

## Remaining owner acceptance

The currently open 0.24.62 app must perform a fresh startup check against the now-complete public chain:

1. Fully close and relaunch the existing CELIKOM 0.24.62 normally. Do not download or run an installer manually.
2. Let CELIKOM perform its background check. It is not expected to show a manual “download update” prompt; the updater is automatic and waits for a safe point.
3. If Yandex is playing, the verified 0.24.63 package may download in the background but installation waits until playback/integration is stopped safely. Do not force-close Yandex or CELIKOM during an install.
4. Send a fresh diagnostic after relaunch. Confirm that the bootstrap/check failure events are gone and that the update has been discovered/downloaded.
5. Confirm the app and Update Supervisor reach **0.24.63.0**, account/session remains connected, and the app reopens normally. Audio replacement remains a separate audible acceptance check.

Do not rebuild or re-sign 0.24.63. Do not touch Android, extension, W174 audio baseline, Yandex profile or server/API backend.
