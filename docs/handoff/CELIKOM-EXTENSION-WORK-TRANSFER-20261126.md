# CELIKOM Extension — handoff to ChatGPT Work / Chrome
**Date:** 2026-11-26  
**Status:** development paused at owner's request; resume inside ChatGPT Work with a real Chrome-capable environment.  
**Repository:** `manufact-test/nomusic`, branch `main`; **candidate extension version: `0.4.90`**. Do not rely on an old hardcoded HEAD: other Android and Windows chats also write to `main`.

## Read first
1. This file (`docs/handoff/CELIKOM-EXTENSION-WORK-TRANSFER-20261126.md`).
2. `docs/handoff/CELIKOM-EXTENSION-090-AUDIO-CONTINUITY-20261126.md`.
3. `docs/handoff/CELIKOM-EXTENSION-STORE-AND-FLOKI-PUBLICATION-20261125.md`.
4. `extension/README.md`, `extension/package.json`, `extension/src/player/{replacement-controller,replacement-player,main-world-entry}.ts`.
5. Relevant regression tests in `extension/tests/` and `scripts/test-audio-gain-browser.mjs`.

## Owner-visible defects to fix together
All issues were reported during actual listening on Yandex Music; avoid single-issue releases:
- **At fresh Start / extension activation:** repeated audible stutters, harsh transition, and delayed connection; previously there was a smooth handoff. Diagnostics of 0.4.89 included `warmLeadMs:0`, repeated activate/restore cycles, and `guard-lost:master-binding-changed` with `track-unknown`.
- **Reload Yandex mid-song and press Play:** original plays briefly, then disappears for ~2 seconds, then replacement continues. Diagnostics: original guard engaged before the replacement decoder's middle-of-track seek finished; its MSE seek was still buffering.
- **Previously observed 0.4.87/0.4.88:** several-second late connection, audible catch-up/freeze, resume/VPN/pause instability, and severe metadata/audio mismatch (one song displayed while another original played). `0.4.88` was not accepted because it only detected and offered recovery for the mismatch rather than fixing all accumulated defects.
- Test fast track skips, temporary metadata gaps, seeking, pause/resume, refresh, long pauses, VPN changes. Do not mask an actual track change as an innocent metadata gap.

## Code already implemented in 0.4.90
Changes are in `main`, from the extension fix PR #68 and subsequent CI-only adjustments:
1. Prewarm an authorized selected-track descriptor before Yandex creates the native audio element (without taking over audio).
2. Keep the existing replacement through `awaiting-track-refresh` only with matching media element, resource revision, duration and any still-present title/artist; a genuine track change still releases the guard.
3. Before acquiring the original-audio guard for mid-song starts, seek and decode the replacement to the live master position. Retain the original audible until alignment; abort boundedly/fail open if decoder cannot join.
4. Regression tests cover descriptor prewarm, refresh identity, late-start alignment, and guarded handoff.

**These fixes have not been accepted by owner listening tests.** Do not claim real playback is fixed based on passing unit tests.

## State of CI / Floki experiment
- Extension unit/integration suite previously reported **437 passing tests** and build/manifest validation on 0.4.90. This does not prove a real audio handoff.
- FlokiNET `Extension artifact` workflow uses a self-hosted `celikom-ci-smoke-only` runner. The early failures were due to a stripped-down Ubuntu 24.04 image: Chrome and many shared libraries missing. The CI was updated to download official Chrome for Testing, FFmpeg and user-space libraries without sudo. Chrome 158.0.8127.88 now starts and reaches the synthetic media fixture.
- The next gate failure was a **headless M4A playback test**: `paused:false`, `readyState:4`, `networkState:1`, but `currentTime:0` even after waiting. This is an unresolved headless test/environment/audio-clock issue; do **not** declare the extension's real M4A playback broken solely from this.
- An additional silent audio sink/CI tuning commit exists in main. **Most recent workflow seen during handoff:** `Extension artifact` run `45864975824` at commit `746a43f4e8462dd463238fcc82af60a7ccec5c16`, running during handoff; check its actual final result instead of assuming success or failure.
- CI files touched: `.github/workflows/extension-build.yml`, `scripts/test-audio-gain-browser.mjs`; browser isolation/dep preparation is for tests only. Do not keep changing playback source merely to satisfy unreliable headless timing.

## Next-chat priority: use ChatGPT Work and a real Chrome session
1. Confirm real access to the repository and a Chrome installation that supports **unpacked extensions** and interacting with Yandex Music. Work's cloud browser should be inspected first: having a Chromium browser does *not* guarantee it permits `chrome://extensions` or loading an unpacked MV3 extension. If restricted, report the limitation precisely and use an available supported full Chrome environment rather than pretending a browser check was performed.
2. Fetch the latest `main` (other chats share it), verify `extension/package.json` version `0.4.90`, and read the files above. Run `npm ci`, `npm run test:extension`, `npm run build:extension`, `npm --prefix extension run validate` where allowed.
3. Inspect the built unpacked files at `extension/dist/unpacked/` (manifest + API base URL `https://api.celikom.com`). Only test against real accounts/approved access; never invent owner credentials or bypass subscription/auth checks.
4. **Listen/test visibly in Chrome**: fresh Start and smooth fade, reload mid-song around ~2 min then Play (no two-second silence), track skips, pause/resume, seek, tab reload, and changing VPN/network. Confirm audio matches displayed metadata and replacements; capture diagnostics on any failures. If Work cannot authenticate or play audio, distinguish blocked testing from an observed defect.
5. Fix any confirmed remaining issues together, update regression tests, then run full checks. Minimize new CI loops in an unreliable Floki headless environment.
6. Only after a checked owner candidate exists, stage it via the established **Floki private owner-delivery** pipeline. **Never send a GitHub Actions artifact or call it a customer auto-update**. See release docs: CI staging into private spool, exact approved metadata, trusted `celikom-extension-owner.timer`, protected `https://celikom.com/downloads/extension/celikom-extension-latest.zip` and versioned URLs; verify receipt, HTTPS anonymous 401 / authorized 200, bytes + SHA256. Ask owner to listen before store/customer promotion. Do not change `.github/release/extension-owner-promotions.json` on unverified builds.

## Boundaries and collaboration
- Owner has **explicitly stopped work in the old chat** and moved continuation to Work. This handoff is documentary; no release/promotion action is authorized by the handoff itself.
- Windows, Android, server, API, subscription, payment, VPN credentials, and Floki deployment pipelines belong to other streams. Keep changes strictly scoped to extension and necessary extension test/release code.
- **Do not force-push or overwrite `main`**; compare HEAD immediately before commits. Other project chats work concurrently.
- Give the owner a usable, tested candidate through the existing CELIKOM site release channel only after safety checks. State honestly what was verified, what still fails, and exactly how to reproduce it.

## Work continuation — 0.4.91 candidate, 26 November 2026

Work's cloud browser blocked chrome://extensions under its security policy. No unpacked installation or Yandex listening test was completed. The local synthetic decoder check also could not launch because the Chromium binary is absent; browser setup was not pursued.

Three controller regressions were reproduced and fixed: false stalled-clock resets during missing metadata, Stop ignored during that interval, and first-five-seconds user seeks skipping pre-guard alignment. Candidate **0.4.91** passes **440 tests**, ZIP build, manifest validation and security gate. Owner promotion remains unmodified. Read `CELIKOM-EXTENSION-091-WORK-VALIDATION-20261126.md` for precise evidence and remaining validation/delivery steps.

## Latest continuation — 0.4.92 private owner candidate, 27 November 2026

0.4.91 owner upload failures were separately repaired by restoring migrated validator/lock permissions; ordinary HTTPS upload and proposal flow passed, and the owner confirmed successful real uploads. Playback diagnostics from 27 November then proved transport failures tearing down MP3 playback and a failed 206 body becoming a non-retryable generic error. 0.4.92 retries the exact signed range while retaining the decoder/buffer; 449 tests, build, manifest, security and exact private package verification passed. Versioned/latest owner HTTPS downloads were independently verified with matching bytes/hash. Read `CELIKOM-EXTENSION-092-STREAM-RECOVERY-20261127.md` for authoritative source/run/delivery evidence, the owner's mid-song audible-dip report, and remaining listening limits. Expanded general diagnostics remain deferred; no customer publication.
