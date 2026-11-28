# W191 — Windows repairs merged to main, protected stable promotion and Floki route audit

 > **W197 UPDATE (2026-11-28):** This is historical implementation evidence. Signed 0.24.63 / sequence 10 is already published and public HTTPS verification passed (W194). The owner-installed 0.24.62 client still fails to discover/install it even after W195 restored its immutable bootstrap files. The controlling failure and next task are in `docs/windows/W196-OWNER-OTA-RETEST-FAILED-2026-11-28.md` and `docs/windows/NEXT-CHAT.md`. Do not repeat W189 release preparation, route cutover, or publication.

Date: 28 November 2026

## Repository and merge status

- Repository: `manufact-test/nomusic`.
- Canonical main at latest check: `bae2553ce410d10cfea6b2eb8f9e569dbdd38538`.
- W189 PR [#73](https://github.com/manufact-test/nomusic/pull/73) is **merged**.
- Merge commit: `23a4b70839abd6fb1b3f014e3ba868f520fe94bc`.
- Merge first parent (main immediately before W189 merge): `bbef018619777c203af60fc56ebc4e524eca2c41`.
- Repair branch: `work/windows-w189-repairs-from-main-20261127`.
- PR head at merge: `a8ea3f292b687c6901980c77732fae7bda371231`.
- Exact pre-merge backup: `backup/main-pre-w189-merge-20261128` @ `bbef018619777c203af60fc56ebc4e524eca2c41`.
- Earlier checkpoint backup: `backup/main-before-w189-merge-20261128` @ `84aa896b0712fd813201e8b300c124cdf966457d`.
- The W189 PR changed 25 files, all Windows runtime/tests/release workflow/docs. No Android runtime, browser-extension runtime, or server/admin backend source was included.
- Concurrent Android A1 operational commits `8d115fb`, `84aa896`, `bbef018`, and `bae2553` remain on main. They are not part of PR #73 and were preserved. Do not modify or roll them back.

## Windows implementation now on main

### W169
- Restored Electron main-process protection around passive CDP event callbacks and asynchronous native relay pulses.
- Added regression coverage for callback/tick exceptions.
- Native host marker is `0.24.32` because native host source changed. App and Update Supervisor remain `0.24.62.0` until the next stable release is prepared.

### W175 / W178
- Restored initial already-playing-song revalidation and bounded catch-up when a new track becomes current.
- Kept the W188 live media-provider bridge and Yandex Music 5.129.0 provider shape.
- W175/W178 assertions are blocking in the Windows regression suite. The fixture models the current 5.129 provider chain; tests were not deleted or skipped.
- Resolve diagnostics distinguish local session missing, invalid origin, refresh failure, changed session, no server grant, rejected grant and valid grant. Tokens, signed URLs and grant contents are not logged.

### UI state and latency
- BridgeServer title/artist/duration/current ID use the same bounded current-track metadata lease.
- Presence status uses a 15-second cache and shared in-flight read.
- A successful proposal/upload mutation immediately sets the pending state and invalidates older GET responses by epoch.
- Old-track async results are rejected before the result panel is rendered.
- The working admin upload and «Предложить песню» contracts remain unchanged.

### Preserved audio baseline
- W174 source files remain byte-identical on main:
  - `windows-companion/w23/renderer-entry.mjs`: `203b098914d549bc8d21b682b62df6486025cefa`
  - `windows-companion/w22/native-resource-adapter.mjs`: `e3bfdc3ed579709c342c3ae87e2e83510e35826e`
  - `windows-companion/w60/current-source-refresh.mjs`: `a5814bee52a8698ab79f9f4861f1b1451d85ee09`
- W188 `renderer-entry-w188.mjs` / `live-media-provider-hook.mjs` remains the active Yandex 5.129 provider bridge.
- No W182/W183/W185 runtime experiments were transplanted.

## CI evidence

Exact PR-head checks on `a8ea3f292b687c6901980c77732fae7bda371231`:
- [Windows integration CI 46073143401](https://github.com/manufact-test/nomusic/actions/runs/46073143401) — SUCCESS; all 22 substantive Windows steps passed.
- [Generic CI 46073143354](https://github.com/manufact-test/nomusic/actions/runs/46073143354) — SUCCESS.

Post-merge runs on merge commit `23a4b70839abd6fb1b3f014e3ba868f520fe94bc`, latest observed:
- [W188 exact Yandex 5.129.0 compatibility 46074224323](https://github.com/manufact-test/nomusic/actions/runs/46074224323) — SUCCESS.
- [Generic CI 46074224262](https://github.com/manufact-test/nomusic/actions/runs/46074224262) — IN PROGRESS.
- [Windows integration CI 46074224334](https://github.com/manufact-test/nomusic/actions/runs/46074224334) — QUEUED.
- [Floki x64 cross-build 46074224315](https://github.com/manufact-test/nomusic/actions/runs/46074224315) — QUEUED.
- [Read-only Windows/Floki route audit 46074224389](https://github.com/manufact-test/nomusic/actions/runs/46074224389) — QUEUED.

CI validates code and contracts, not actual audible playback. The owner has not yet confirmed audible replacement from a build containing W189.

## Critical stable OTA finding

The existing Floki root consumer is production-capable:

- `.github/scripts/floki-windows-signed-root-consumer.py` consumes the signed Windows spool.
- Its root timer promotes the local Floki stable pointer and owner download `CELIKOM-Windows-latest.exe`.
- It writes `owner-verified.json` only after both owner HTTPS download routes pass exact size and SHA256 checks.
- Therefore, the Floki spool is not a harmless private test stage. Sending a signed package there can automatically promote it to the local stable/owner route when the timer is active.

The Hostinger publisher has a different filesystem target:
- `.github/scripts/windows-stable-publish-hostinger.sh` writes under `/home/u235811320/domains/celikom.com/public_html/CELIKOM/Windows/Updates/stable`.
- The Floki root consumer writes under `/srv/celikom-releases/windows/stable` and `/srv/celikom-releases/owner-downloads`.
- The public DNS/Nginx mapping and which path the installed updater actually consumes are not yet confirmed. Do not guess whether Hostinger, Floki or both are required.

### Workflow safeguards now on main

- `publish_to_production` defaults to false.
- Production preparation fails closed unless repository variable `CELIKOM_STABLE_PUBLISHER` is one of `floki`, `hostinger`, or `both`.
- Floki and Hostinger publishers are selected independently; each is gated by protected environment `windows-stable-production`.
- The Floki child workflow is `workflow_call` only; direct push and manual dispatch paths were removed.
- The Hostinger job receives a matching stable release artifact.
- No stable publish or server mutation has been performed.
- Required-reviewer settings for `windows-stable-production` still need explicit verification in GitHub Settings → Environments. Naming the environment alone does not prove that approvals are configured.

### Read-only route audit

The merge changed `.github/deploy/windows-owner-audit-trigger.txt`, which triggered [Windows Floki owner route audit run 46074224389](https://github.com/manufact-test/nomusic/actions/runs/46074224389). It was queued at the last check.

The audit reads:
- Floki root-consumer timer/service state;
- pending signed spool files;
- local stable pointer and manifest version/sequence/hash;
- owner download and HTTPS verification receipt;
- public DNS and HTTPS status for the stable feed and owner route;
- relevant Nginx route mapping.

It runs through the existing `floki-deploy` environment. It is read-only: it does not publish, clean the spool, or alter the server. Inspect its actual output before selecting any publisher target.

## Next actions

1. Finish post-merge generic CI and Windows integration CI on the merge commit; investigate only real failures.
2. Wait for and inspect route audit run 46074224389. If the spool is non-empty or the timer is active with an unexpected candidate, stop and resolve before any new release.
3. Verify that `windows-stable-production` has required reviewers. This configuration has not yet been confirmed.
4. Determine from route audit and live feed evidence whether Hostinger and Floki are complementary targets; do not set `CELIKOM_STABLE_PUBLISHER` by guess.
5. Confirm the owner's currently installed Windows version from a fresh diagnostic. Do not assume 0.24.62 was installed merely because the package was staged.
6. Read the live signed stable manifest and sequence floor. Expected next app/supervisor version is `0.24.63.0`, but choose the sequence only from the verified live floor.
7. Prepare/build/sign the next version from main. Keep `publish_to_production=false` until package, trust pin, target and rollout scope are confirmed.
8. Only after those checks, prepare the exact production run with `publish_to_production=true`. It must pause at `windows-stable-production`; provide the exact Actions/deployment link and wait for the owner's explicit approval.
9. Before publishing, verify whether stable reaches all customers. Do not test one owner device by triggering a global rollout without explicit confirmation or a proven pilot mechanism.
10. After approved publication, verify public manifest/signature/package over HTTPS, then test automatic discovery, download, updater handoff, in-place installation and restart on the owner's existing installation. Confirm no manual installer download/launch was used.
11. Record audible playback separately. Do not claim it works until the owner confirms the actual replacement is heard.

## Hard boundaries

- No Android, browser-extension runtime or server/admin backend changes.
- No W182/W183/W185 experimental player hooks.
- No private spool transfer before protected approval.
- No global stable publication before route audit, stable floor, trust pin, environment reviewers and rollout scope are verified.
- No claim of audible playback or automatic OTA success based on CI alone.
