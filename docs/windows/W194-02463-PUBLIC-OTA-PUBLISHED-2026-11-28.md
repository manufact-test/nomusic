# W194 — Windows 0.24.63 public stable OTA published (2026-11-28)

> **W196 update (2026-11-28):** W195 restored the exact signed 0.24.62 immutable bootstrap files to the existing public route, but the owner retested and the installed app still reports 0.24.62.0 with `STABLE_UPDATE_CHECK_FAILED` and `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE`. The route repair was not sufficient; the client failure stage remains unknown. Public latest remains 0.24.63 / sequence 10 unchanged. Follow `docs/windows/W196-OWNER-OTA-RETEST-FAILED-2026-11-28.md`; do not ask the owner to repeat the same test.


## Result

**Public stable OTA publication completed successfully.** The owner explicitly approved the existing protected GitHub environment gate. The existing public updater route now serves the exact signed 0.24.63 release.

- App / Update Supervisor version: **0.24.63.0**
- Signed manifest version: **0.24.63**
- Signed sequence: **10**
- Source build commit: `9c6721fdb273fc0850213b79d339b0f47d3e83b0`
- Original signed build: [GitHub Actions 46083334539](https://github.com/manufact-test/nomusic/actions/runs/46083334539) — SUCCESS.
- Protected publication run: [GitHub Actions 46084804919](https://github.com/manufact-test/nomusic/actions/runs/46084804919) — **SUCCESS**.
- Owner approval for `windows-stable-production`: recorded as `approved` in that run.
- Exact installer SHA256: `3315b43e5af8c789f77fe643478b27f466bb4d5c76a591d34ce15143e2b2515f`.
- P-256 public key fingerprint: `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`.
- Exact transfer artifact: ID `15237633233`, archive SHA256 `9d7074fdd0610ebb7f4f00645f882271d595ac13efa05146141c6d2e8cc653b1`.

## What completed

1. Preflight downloaded the original artifact from run 46083334539 and verified its exact identity, pinned P-256 key, signed metadata, sequence 10 and package hash.
2. The protected `windows-stable-production` approval was recorded and passed.
3. The exact signed transfer was staged through the existing Floki spool. No rebuild or re-sign occurred.
4. The existing Floki root consumer independently consumed the signed transfer and promoted local stable to `versions/0.24.63`.
5. A subsequent read-only, approval-bound maintenance check confirmed:
   - `/srv/celikom-releases/windows/stable/current -> versions/0.24.63`;
   - manifest version 0.24.63, sequence 10 and exact installer SHA256;
   - `owner-verified.json` reports `https_verified=True`;
   - the owner latest installer has the same exact package size and SHA256;
   - immutable versions 0.24.55 and 0.24.62 remain present.
6. The existing public customer-stable consumer published the approved manifest/signature and installer through the already-configured public HTTPS route.
7. Final verification in run 46084804919 compared the public `latest.json` and detached signature byte-for-byte with the signed transfer, compared the versioned manifest/signature with the same bytes, downloaded the public 0.24.63 EXE over HTTPS and verified the complete SHA256. Result: `W194_PUBLIC_STABLE_02463_EXACT_SIGNED_HTTPS_VERIFIED`.

The existing public route was already present when checked. A separate route-cutover attempt stopped safely at its duplicate-route guard before changing Nginx. No Nginx configuration was modified.

## Release record and cleanup

- `.github/release/windows-customer-stable.json` records the owner-approved 0.24.63 / sequence 10 / exact package SHA256.
- The one-off release workflow and temporary route-cutover helpers were removed after the successful publication. The GitHub Actions run records remain available at the links above.
- Existing Floki maintenance workflow was restored unchanged.
- No Windows runtime, audio source, Android runtime, browser-extension runtime or server/API code was changed as part of this release operation.

## Owner acceptance — installed-device OTA (failed; see W196)

**Public publication is verified; installed-device auto-update has been attempted and failed.** The owner relaunched the existing 0.24.62 installation after W195. It remained on 0.24.62.0 and logged the two generic updater failures. The old procedure below is historical; do not ask the owner to repeat it. Continue the engineering investigation in W196.

The owner's exact currently installed Windows version remains unknown. The next test must use the existing installed CELIKOM, not a manually downloaded EXE:

1. Fully close CELIKOM and launch it normally again so the installed updater performs its regular check.
2. Allow the in-app update flow to complete if it is offered. Do not manually download or launch the EXE.
3. After restart, verify the displayed app and supervisor version is 0.24.63.0, account/session is retained, and the fresh diagnostic reports the current version.
4. Confirm update discovery, download, signature/hash verification, safe-point handoff and in-place install separately. Do not claim any stage passed based only on the public feed.
5. Audio replacement remains a separate owner acceptance check; this publication does not prove audible playback.

If the installed app does not discover 0.24.63 after a normal restart, capture a fresh diagnostic from that installed copy. Do not rebuild, re-sign, touch the audio baseline, Android or extension.

## Current repository state

- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- Main at the end of release cleanup before this documentation commit: `4d86c904edf13e44fff2c3613ec17ac45fe6023f`.
- No app/runtime changes were needed for the OTA route repair.
