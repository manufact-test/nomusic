# W191 — Windows repairs, protected stable promotion and Floki route audit

Date: 27 November 2026

## Repository and branch

- Repository: `manufact-test/nomusic`.
- Main reconciliation base: `117e0772fbecf0bb902127f0a4a5ce704d44d8ec`.
- Main at latest check: `ec68241b3c58d87770267f0d2cde844146086de8` (two later extension-only commits, no W189 path overlap).
- Repair PR: [#73](https://github.com/manufact-test/nomusic/pull/73).
- Repair branch: `work/windows-w189-repairs-from-main-20261127`.
- Current PR HEAD: `cdda5230e6386c3ffaa4ace239310117d0b62e38` (documentation-only handoff update after the code rebase).
- PR diff: 25 files, all W189 Windows runtime/tests/release workflows/docs. No Android, extension runtime or server/admin backend source is included.
- Main's later extension 0.4.96 commits are preserved as base history; the W189 PR does not replace them.

## Implemented repairs

### W169
- Restored Electron main-process protection around CDP detach callbacks and asynchronous native tick handling.
- Added regression coverage for callback/tick exceptions.
- Native host marker is now `0.24.32` because the native host source changed. The 0.24.62.0 app/supervisor release version has not yet been bumped.

### W175 / W178
- Restored initial already-playing-song revalidation and bounded catch-up when a new track becomes current.
- Kept the W188 live media-provider bridge and Yandex Music 5.129.0 provider shape.
- Restored W175/W178 assertions to the blocking Windows regression suite. The old fixture was updated to model the current 5.129 provider chain; tests were not deleted or skipped.
- Resolve diagnostics now distinguish local session missing, invalid origin, refresh failure, changed session, no server grant, rejected grant and valid grant. Only failure causes are incident-classified; tokens, URLs and grant contents are not logged.

### UI state and latency
- BridgeServer title/artist/duration/current ID use the same bounded current-track metadata lease.
- Presence status uses a 15-second cache and shared in-flight read.
- A local proposal/upload mutation immediately sets the pending state and invalidates older GET responses by epoch.
- Old-track async results are rejected before the result panel is rendered.
- The working admin upload and «Предложить песню» contracts remain unchanged.

### Preserved audio baseline
- W174 source files remain byte-identical:
  - `windows-companion/w23/renderer-entry.mjs` Git blob ID: `203b098914d549bc8d21b682b62df6486025cefa`
  - `windows-companion/w22/native-resource-adapter.mjs` Git blob ID: `e3bfdc3ed579709c342c3ae87e2e83510e35826e`
  - `windows-companion/w60/current-source-refresh.mjs` Git blob ID: `a5814bee52a8698ab79f9f4861f1b1451d85ee09`
- W188 `renderer-entry-w188.mjs` / `live-media-provider-hook.mjs` remains the active 5.129 provider bridge.
- No W182/W183/W185 runtime experiments were transplanted.

## CI evidence

Latest completed full checks before the branch was reconciled onto the two newest main commits:
- [Windows integration CI 46070031881](https://github.com/manufact-test/nomusic/actions/runs/46070031881) — SUCCESS. All 22 substantive steps passed, including W174/W175/W178/W188, W21, W24, W15, GUI warnings-as-errors, supervisor, installer and updater safety.
- [Generic CI 46070031935](https://github.com/manufact-test/nomusic/actions/runs/46070031935) — SUCCESS.

The branch was reconciled onto current main; exact-head checks on `cdda5230e6386c3ffaa4ace239310117d0b62e38` passed:
- [Windows integration CI 46071049097](https://github.com/manufact-test/nomusic/actions/runs/46071049097) — SUCCESS.
- [Generic CI 46071049046](https://github.com/manufact-test/nomusic/actions/runs/46071049046) — SUCCESS.

Green CI confirms code/test contracts only. Actual audible replacement on the owner's Windows installation is not yet verified.

## Critical stable OTA finding

The existing Floki root consumer is production-capable:

- `.github/scripts/floki-windows-signed-root-consumer.py` consumes the signed Windows spool.
- Its root timer promotes the local Floki stable pointer and owner download `CELIKOM-Windows-latest.exe`.
- It writes `owner-verified.json` only after both owner HTTPS download routes pass exact size and SHA256 checks.
- Therefore, the Floki spool is not a harmless private test stage. Sending a signed package there can cause automatic stable/owner promotion once the timer is active.

The Hostinger publisher has a different role/path:

- `.github/scripts/windows-stable-publish-hostinger.sh` writes the stable feed under `/home/u235811320/domains/celikom.com/public_html/CELIKOM/Windows/Updates/stable`.
- The Floki root consumer writes `/srv/celikom-releases/windows/stable` and `/srv/celikom-releases/owner-downloads`.
- The public DNS/Nginx mapping and which path the installed updater actually consumes have not yet been confirmed. Do not guess whether Hostinger, Floki or both are required.

### Workflow safeguards now in the PR

- `publish_to_production` defaults to false.
- Production preparation fails closed unless repository variable `CELIKOM_STABLE_PUBLISHER` is one of `floki`, `hostinger`, or `both`.
- Floki and Hostinger publishers are selected independently; each is gated by protected environment `windows-stable-production`.
- The Floki child workflow is `workflow_call` only; direct push and manual dispatch paths were removed.
- The Hostinger job receives a matching stable release artifact.
- No stable publish or server mutation has been performed.

The workflow references `windows-stable-production`, but its required-reviewer settings must still be verified in GitHub repository Settings → Environments. Merely naming an environment does not prove that required reviewers are configured.

### Read-only route audit

The PR adds:
- `.github/deploy/windows-owner-audit-trigger.txt` to trigger the audit after merge.
- Expanded `.github/scripts/floki-windows-owner-readonly-inventory.sh` to inspect:
  - Floki root-consumer timer/service state;
  - pending signed spool files;
  - local stable pointer and manifest version/sequence/hash;
  - owner download and HTTPS verification receipt;
  - public DNS and HTTPS status for the stable feed and owner route;
  - relevant Nginx route mapping.

This audit is read-only and runs through the existing `floki-deploy` environment. It does not publish, clean the spool or alter the server.

## Next actions

1. Mark PR #73 ready and merge it to current main. Do not force-push or reset main.
2. Mark PR #73 ready and merge it to current main. Do not force-push or reset main.
3. Approve/run the read-only Floki route audit and inspect its output. If the spool is non-empty or the timer is active with an unexpected candidate, stop and resolve before any new release.
4. Verify `windows-stable-production` has required reviewers.
5. Determine whether Hostinger and Floki are complementary routes; then set `CELIKOM_STABLE_PUBLISHER` to `hostinger`, `floki` or `both` accordingly.
6. Read the live signed stable version/sequence floor. Only then select the next version (expected app version is 0.24.63.0; sequence must come from the live floor).
7. Build/sign the release from main. Set `publish_to_production=true`, open the exact GitHub Actions run and wait for owner approval in `windows-stable-production`.
8. After approval, verify public manifest/signature/package over HTTPS, then test automatic discovery, download and in-place installation on the already-installed owner copy. Do not ask the owner to manually download an installer as a substitute for OTA verification.
9. Record audible playback separately. Do not claim it works until the owner confirms the actual replacement is heard.

## Hard boundaries

- No Android, browser-extension runtime or server/admin backend changes.
- No W182/W183/W185 experimental player hooks.
- No private spool transfer before protected approval.
- No global stable publication before the route audit, stable floor, trust pin, environment reviewers and rollout scope are verified.
- No claim of audible playback or automatic OTA success based on CI alone.
