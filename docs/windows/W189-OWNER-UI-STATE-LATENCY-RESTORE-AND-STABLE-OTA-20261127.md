> **Current execution branch (27 November 2026):** `work/windows-w189-repairs-from-main-20261127`, created directly from canonical `main` @ `38b839f7d40a761fb794d4a20680e3cf71b6d65d`. Follow W190 for promotion evidence and execution order. The old recovery branch is now a source reference only; do not make fixes there.

> **Execution order update (27 November 2026):** Follow W190 first. Promote the exact W188 / 0.24.62 baseline to `main` before applying W169/W175/W178 or UI/latency fixes. After baseline CI and source checks pass on `main`, create a fresh Windows repair branch from that `main` and implement the W189 tasks there. Do not repair on the old recovery branch and then attempt a large late transplant.

# W189 — owner UI state, latency, playback recovery and stable auto-update (27 November 2026)

## Purpose and status

This is the active Windows work order after the owner received the W188 / 0.24.62 candidate and reported the latest UI observations. The exact installed version still needs confirmation from diagnostics. It combines:
1. the source-diff audit findings that were missing from the W188 candidate;
2. the newly observed UI state and latency defects;
3. the owner's explicit request to make the next accepted version available through the production/main update path and verify automatic update on his installed copy.

This document records tasks and evidence only. No runtime source, API, production feed, or release workflow was changed by this documentation update.

## Exact project baseline

- Repository: `manufact-test/nomusic`.
- Active working branch: `recovery/windows-w174-02454-known-good-20261126`.
- W188 product/test source: `d0de9824c5e03422a9d6f928f17715de07bb76ba`.
- W188 signed owner-package source/metadata commit: `0364309006bd3451778f01390398fe0f52e5a20c`.
- Last generated owner candidate: CELIKOM Windows **0.24.62.0**, Update Supervisor **0.24.62.0**, native module **0.24.31**, signed sequence **9**.
- Exact Yandex version audited: `5.129.0.r22295238`.
- W174 accepted audio baseline files must remain unchanged unless a narrowly justified, tested integration requires otherwise:
  - `windows-companion/w23/renderer-entry.mjs`: `203b098914d549bc8d21b682b62df6486025cefa`
  - `windows-companion/w22/native-resource-adapter.mjs`: `e3bfdc3ed579709c342c3ae87e2e83510e35826e`
  - `windows-companion/w60/current-source-refresh.mjs`: `a5814bee52a8698ab79f9f4861f1b1451d85ee09`
- W188's Yandex 5.129 provider bridge lives in `live-media-provider-hook.mjs` and `renderer-entry-w188.mjs`; do not replace it with the speculative W182/W183/W185 Sonata/player hook experiments.

## Owner observations — 27 November 2026

### Confirmed working actions

- The owner reports a song was successfully uploaded through the admin interface.
- The owner also successfully used the in-app **«Предложить песню»** flow.
- Do not treat these two successful actions as proof that the current-track UI state is correct or that actual playback replacement is audible. These are separate acceptance checks.
- Do not rewrite the upload/admin backend or change the upload contract without fresh evidence. Preserve the existing working path.

### UI defect A — «Загрузить версию» intermittently disappears

Observed:
- On some tracks, the owner opens the current-song action/tab and does not see **«Загрузить версию»**.
- Instead the UI claims that CELIKOM must connect to Yandex or displays a similar disconnected-state message.
- Yandex/CELIKOM are in fact connected.
- The same song is visible in **«Предложить песню»** and can be proposed/uploaded there.
- Switching to another song and then returning to the first sometimes makes **«Загрузить версию»** appear.

Required investigation/fix:
- Compare the current-track action's state source with the track identity/state used by «Предложить песню».
- Trace selected track ID, current player/queue identity, bridge connection state, and entitlement/loading state across Next/Previous, tab changes, window close/open and return to a previous track.
- Find why a connected session is sometimes represented as disconnected for this action.
- Check for stale per-track cache, late async response, wrong selected/current track identity, or a race between connection state and track metadata. These are hypotheses, not established root causes.
- Refresh or reconcile the current track when it changes; never reuse the previous track's state for the newly selected track.
- Do not show a false «Подключитесь к Яндексу» message while the native bridge is already connected and authenticated.
- Keep the action unavailable only when the actual required state is unavailable; show a neutral loading state while the state is genuinely unresolved.

### UI defect B — stale state flashes when reopening a proposal window

Observed:
1. Owner proposes a song.
2. The UI confirms **«На рассмотрении»**.
3. Owner closes and reopens the song window.
4. The old **«Загрузить версию»** action is shown briefly.
5. Roughly half a second later, the correct green **«На рассмотрении»** state replaces it.

Required investigation/fix:
- Trace the successful proposal response, local state/cache update, persisted server state and the fetch performed on window open.
- After the server confirms the proposal, update the local song state immediately from that confirmed response.
- On reopening, resolve the cached/current state before rendering an obsolete action. If server refresh is required, use a loading/skeleton/neutral state rather than flashing the stale button.
- Ensure close/reopen does not create duplicate requests or revert a newer state with an older response.
- Test repeated open/close, fast reopen, Next/Previous, and proposal submission followed immediately by reopening.
- The server's confirmed state remains authoritative; do not fake a green status before a successful server response.

### UI defect C — general interface latency

The owner reports that different interface operations sometimes feel slow, not only the two song states above.

Required investigation/fix:
- Measure the slow paths: opening/closing windows, switching tracks, opening song actions, refreshing proposal status, and rendering the current-track state.
- Inspect UI-thread blocking, synchronous file/network work, redundant polling, duplicate concurrent requests, repeated parsing/rendering, and late responses overwriting newer state.
- Reuse already-valid state where safe; avoid waiting for a full network refresh when a valid confirmed state is already available.
- Add only bounded, privacy-safe timing diagnostics where needed; no signed URLs, credentials, tokens, full response bodies or personal data.
- Fix the demonstrated bottleneck(s), not by globally increasing polling frequency or adding arbitrary delays.
- Keep the interface responsive while requests are pending, with explicit loading/empty/error states.

## Playback/source recovery items from the previous audit

The previous source audit found these specific W169/W175/W178 changes missing from the W188 candidate. Re-check the live branch HEAD first, then port/adapt them narrowly around the W188 provider bridge and W174 audio baseline.

### W169 — guard Electron main-process callbacks

- Restore the guarded scheduler for asynchronous native relay pulses: rejected `tick(view)` promises must be caught and recorded as `NATIVE_RELAY_TICK_EXCEPTION`, not bubble into Electron's main process.
- Restore exception protection around passive CDP event callbacks; on unexpected payload, fail closed for the passive decoder witness and record `NATIVE_CDP_EVENT_EXCEPTION`.
- Restore the W169 regression test proving all pulse entry points use the guarded scheduler and CDP callbacks cannot throw out of Electron.
- Do not blindly change the native module version marker. Preserve W174's accepted module/source baseline where possible; determine whether any version bump is required by the actual binary contract.

### W175 — catch up the already-playing song after initial attach

- Restore the delayed initial-current-source revalidation (original W175 waits for the player to settle, about 3.5 seconds).
- It must inspect only the exact current PLAYING/PAUSED track and make at most one bounded attempt for that attach/state generation.
- It must require an approved grant and use the existing version-pinned source-only QUALITY_CHANGE path.
- Preserve queue, position and pause state; never autoplay, seek, change track, or reload an unknown/unapproved source.
- Restore/adapt the W175 tests for cached current source, exact track identity, one attempt, approved grant, and Stop/disable cancellation.

### W178 — catch up a newly selected current song and improve resolve diagnostics

- Restore/adapt the separate W178 behavior for a song that becomes the current track after Next/Previous but whose original source was already cached by Yandex.
- This is not the same as W77 deferred prefetch recovery. W77 handles a deferred prefetched request; W178 revalidates the exact newly current PLAYING/PAUSED track.
- Only a confirmed grant may trigger the existing source-only reload. No grant means preserve Yandex original; no reload loops or duplicate QUALITY_CHANGE.
- Restore privacy-safe diagnostic distinctions:
  - `RESOLVE_LOCAL_SESSION_MISSING`
  - `RESOLVE_LOCAL_ORIGIN_INVALID`
  - `RESOLVE_SESSION_REFRESH_FAILED`
  - `RESOLVE_SESSION_CHANGED`
  - `RESOLVE_SERVER_NO_GRANT`
  - `RESOLVE_GRANT_REJECTED`
  - `RESOLVE_GRANT_VALID`
  - `RESOLVE_QUEUED`, `RESOLVE_DEQUEUED`, `RESOLVE_REPLY_RECEIVED`
  - the bounded `NATIVE_CURRENT_CATCHUP_*` / initial-source outcomes used by the W175/W178 implementation.
- Do not log signed audio URLs, access/refresh tokens, credentials, response bodies, or grant contents.

### Preserve existing behavior

- Keep W77 deferred-prefetch recovery and Stop cancellation.
- Preserve the previously verified W160–W173 fixes, W174 accepted source baseline, W188 5.129.0 provider bridge, upload contract, and native restore safety.
- No speculative player architecture and no transplant of W182/W183/W185's unproven SonataProvider hook.
- Do not equate RESOURCE_HOOK_ATTACHED, a grant, HTTP 206, or a successful CI run with audible playback. Final playback acceptance requires the owner to hear the actual replacement.

## Required regression and owner acceptance plan

### UI tests

1. Connected Yandex + track eligible for «Загрузить версию»: action appears immediately.
2. Same track through «Предложить песню»: both views use the same correct track identity and compatible state.
3. Next to another song and back: action remains correct without requiring a manual tab/window cycle.
4. Open/close/reopen song window repeatedly: no stale «Загрузить версию» flash after the server has confirmed «На рассмотрении».
5. Submit proposal, close immediately, reopen immediately: confirmed status wins over any older in-flight response.
6. Simulate slow/error network responses: UI stays responsive and never falsely reports Yandex disconnected.
7. Test a genuinely disconnected bridge separately to ensure the correct disconnected message still appears.

### Playback tests

- Test known mapped song «Ау» (track ID `144530503`) and at least one other mapped song.
- Test an unmapped/original song; it must remain the original.
- Test initial attach while a song is already playing, Next to a new current track, Play/Pause/resume, Stop, and a delayed/failed resolve.
- Verify no duplicate reload, no queue/position/pause corruption, and no retry storm.
- Inspect fresh diagnostics from the exact candidate build; do not reuse diagnostics from 0.24.61/0.24.62 as proof for a later candidate.

## Next release: owner explicitly requests main / production auto-update test

The owner does not want the next candidate merely uploaded to the test/private channel. After the fixes and acceptance gates, the requested path is to put the next version on GitHub `main`, then use the production stable update path and verify that the owner's existing installation discovers and installs it automatically.

Important distinction:
- Merging source to GitHub `main` is a code integration step.
- Publishing the signed `stable` feed is a separate production deployment that can affect every installation following that feed.
- The private Floki spool/owner download used for 0.24.62 is not itself the public stable update feed and does not prove in-app auto-update works.

### Current release-path blockers discovered on 27 November

- `.github/workflows/windows-stable-signed-release.yml` is main-only for its release jobs.
- `prepare` builds/signs the P-256 package; `private_stage` stages a data-only transfer to the Floki spool.
- The `publish` job requires `inputs.publish_to_production == true` and the protected GitHub environment `windows-stable-production`.
- However, the current `prepare` step explicitly throws `FLOKI_PRODUCTION_PUBLISH_NOT_YET_APPROVED` whenever `publish_to_production=true`; the input description also says production publishing is disabled during migration. Therefore the production approval job cannot currently be reached by simply selecting the input.
- The production publisher script is still `.github/scripts/windows-stable-publish-hostinger.sh`, uses the `HOSTINGER_SSH_KEY`, and targets the Hostinger filesystem path for `celikom.com/CELIKOM/Windows/Updates/stable`. The private owner staging path is FlokiNET. Reconcile this split against the actual live production feed/hosting before enabling any publish. Do not assume a Floki private-stage success means the stable feed has been updated.
- `StableUpdateTrustConfiguration.cs` contains empty source constants by design; the signed release workflow embeds the public production origin/key during build. Verify the generated executable contains the exact expected production trust pin; do not add a private key or hand-edit a secret into source.
- The production publisher verifies the current signed `latest.json` pair, enforces a strictly increasing sequence, stages immutable files before promoting `latest.json`, and compares the published HTTPS bytes. Preserve these safety checks.

### Required release execution

1. Finish W189 code fixes and tests on the recovery branch; do not merge an untested candidate.
2. Verify the owner's current installed version from fresh diagnostics. The last generated private candidate is 0.24.62 / sequence 9; choose the next version and sequence only after checking the live signed feed and monotonic floor.
3. Review the complete recovery-branch diff against current `main`; only intended Windows runtime, tests, release metadata and docs may be included. Do not merge unrelated Android, extension, server or admin changes.
4. Create a fresh immutable backup of `main`, open/review the correct PR or merge path, and integrate the accepted Windows code into `main`. Do not force-push or reset main.
5. Reconcile and repair the production workflow blocker and Hostinger/Floki deployment split with tests. Keep `publish_to_production=false` until the exact signed package, trust pin, production target and auto-update behavior are ready.
6. Build/sign the exact new version from `main`; verify the package, P-256 manifest/signatures, sequence, installer contents, updater trust pin and official HTTPS feed paths.
7. Only then make the production publish job eligible. It must pause at protected environment `windows-stable-production`; send the owner the exact GitHub Actions run/deployment link and wait for his explicit approval. Do not bypass required reviewers, environment protection, branch protections or signing checks.
8. Before publishing, explicitly verify whether the stable feed is consumed by all customer installations. If it is a global feed, do not release to all users merely to test one owner's PC; establish an owner-only/pilot targeting mechanism or obtain explicit confirmation that global rollout is intended.
9. After approved publication, test end-to-end from the owner's already-installed previous version: the app checks the correct stable feed, discovers the new signed manifest, verifies P-256 signature and package hash, downloads, invokes the updater/supervisor, installs in place, preserves CELIKOM login/DPAPI and Yandex profile, and reports the new version after restart. Confirm the owner did not manually download or launch the installer.
10. Verify the exact production `latest.json`, signature and package over HTTPS after publish. Record whether automatic discovery, download, install and restart each succeeded; these are separate acceptance results.

### Hard boundaries

- No Android A1 or browser-extension runtime changes.
- No server/admin backend or upload-contract changes unless fresh evidence proves they are required.
- No Yandex executable/profile replacement outside the existing verified compatibility snapshot/restore pipeline.
- No public stable promotion or mass OTA before the owner's explicit approval at the protected environment gate and confirmation of rollout scope.
- Do not disable security, bypass Defender/SmartScreen, or tell the owner to ignore warnings.
- No claim that playback or auto-update is fixed until each has been tested on the owner's actual Windows installation.

## First actions for the next chat

1. Read this W189 work order, then the W188 handoff and W188 investigation; fetch the live recovery branch HEAD and verify current installed candidate version from the owner's next diagnostic if available.
2. Inspect the exact W188 UI state/data flow for the two observed defects before editing. Reproduce with tests; do not change upload/admin backend.
3. Restore/adapt W169, W175 and W178 as narrowly described, preserving W174 and W188 source hooks.
4. Profile and fix the real UI latency source.
5. Run all relevant Node/W15/W20/W21/W24/Windows build and install/upgrade regression checks.
6. Only after owner runtime acceptance, execute the main/stable release and auto-update plan above. The user expects a protected approval step and must be invited to approve; do not stop at another test/private package.

