# W190 — promote the verified W188 Windows baseline to main before repairs

Date: 27 November 2026

## Owner's sequencing decision

The owner explicitly wants the last prepared and checked Windows candidate to become the canonical Windows version on GitHub `main` first. Only after that exact baseline is present and verified on `main` may the W169/W175/W178 and UI/latency repairs begin.

Do not apply the fixes to the old recovery branch and attempt a large late transplant. The repair branch must be created from the new mainline baseline.

## Exact source baseline

- Repository: `manufact-test/nomusic`.
- Source branch: `recovery/windows-w174-02454-known-good-20261126`.
- Source branch HEAD: `144990bde0848585fadd215a9469f6d496fe580a`.
- Product/test baseline: `d0de9824c5e03422a9d6f928f17715de07bb76ba`.
- Signed package metadata/build commit: `0364309006bd3451778f01390398fe0f52e5a20c`.
- Candidate: CELIKOM Windows **0.24.62.0**, Update Supervisor **0.24.62.0**, native module **0.24.31**, official Yandex **5.129.0.r22295238**, signed sequence **9**.

Verified runs:
- [45965695251](https://github.com/manufact-test/nomusic/actions/runs/45965695251) — official Yandex 5.129.0 compatibility: SUCCESS.
- [45968594874](https://github.com/manufact-test/nomusic/actions/runs/45968594874) — package-commit compatibility validation: SUCCESS.
- [45968594921](https://github.com/manufact-test/nomusic/actions/runs/45968594921) — isolated FlokiNET Windows cross-build: SUCCESS.
- [45968594886](https://github.com/manufact-test/nomusic/actions/runs/45968594886) — P-256 signed private owner package: SUCCESS; production publish SKIPPED.
- [45969140182](https://github.com/manufact-test/nomusic/actions/runs/45969140182) — owner HTTPS receipt: SUCCESS.

These checks establish build, compatibility, signature and private delivery evidence. They do **not** prove audible replacement or automatic production OTA on the owner's installed PC.

## Mainline safety / preservation

- Pre-integration `main` HEAD: `64a1f36a5d3fb6951f327e28864fd5a10440203b`.
- Immutable backup: `backup/main-before-w188-baseline-20261127`.
- Do not reset or force-push `main` to the old recovery tree. The recovery tree is 856 commits behind and lacks 170 files that exist on current main, including newer Android, browser-extension, server and deployment work.
- Promote the Windows product baseline through a clean integration branch/PR based on current `main`. Copy the verified W174/W188 Windows runtime, tests, Yandex 5.129 catalog and relevant Windows docs; preserve current main's unrelated files and newer release/deployment tooling.
- Do not transplant W182/W183/W185 experimental player hooks.
- Do not change Android A1, browser extension runtime, server/admin backend, upload contract or production feed during baseline promotion.

## Promotion result — completed on 27 November 2026

- PR [#72](https://github.com/manufact-test/nomusic/pull/72) merged successfully.
- Canonical main SHA: `38b839f7d40a761fb794d4a20680e3cf71b6d65d`.
- Pre-integration backup: `backup/main-before-w188-baseline-20261127` @ `64a1f36a5d3fb6951f327e28864fd5a10440203b`.
- PR generic CI [46056935295](https://github.com/manufact-test/nomusic/actions/runs/46056935295): SUCCESS.
- PR Windows integration CI [46056935288](https://github.com/manufact-test/nomusic/actions/runs/46056935288): SUCCESS, including W174/W188 regressions, W21, W24, W15, GUI and supervisor builds, installer contracts and updater safety.
- The four W175/W178 current-track catch-up tests remain visibly failing in their explicitly non-blocking baseline step (`W189_BASELINE_GAP`); they were not removed. They must be restored to the blocking suite after W189 repairs.
- The full pre-integration main tree remains present: no files were lost from the 1,856-file backup tree. Android A1, browser extension, server/admin and unrelated repository work were not replaced.
- Post-merge checks launched on exact main SHA `38b839f7d40a761fb794d4a20680e3cf71b6d65d`: Windows integration [46057355291](https://github.com/manufact-test/nomusic/actions/runs/46057355291), W188 Yandex 5.129 audit [46057355369](https://github.com/manufact-test/nomusic/actions/runs/46057355369), generic CI [46057355317](https://github.com/manufact-test/nomusic/actions/runs/46057355317), W181 Yandex 5.128 audit [46057355310](https://github.com/manufact-test/nomusic/actions/runs/46057355310), and FlokiNET x64 build [46057355312](https://github.com/manufact-test/nomusic/actions/runs/46057355312). Recheck these before declaring post-merge validation complete.
- No stable-feed publication, global rollout or new owner installer was triggered. The production guard remains intact.

## Baseline acceptance on main

Before starting W189 repairs:
1. Confirm main contains the exact app/supervisor version 0.24.62 and native marker 0.24.31.
2. Confirm W174 source blobs:
   - `windows-companion/w23/renderer-entry.mjs`: `203b098914d549bc8d21b682b62df6486025cefa`
   - `windows-companion/w22/native-resource-adapter.mjs`: `e3bfdc3ed579709c342c3ae87e2e83510e35826e`
   - `windows-companion/w60/current-source-refresh.mjs`: `a5814bee52a8698ab79f9f4861f1b1451d85ee09`
3. Confirm W188 files:
   - `windows-companion/w23/renderer-entry-w188.mjs`
   - `windows-companion/w23/live-media-provider-hook.mjs`
   - corresponding provider-hook and renderer-relay tests.
4. Confirm the official Yandex 5.129.0 catalog entries and the Windows package builds at 0.24.62.
5. Require generic PR CI, the blocking W174/W188 Windows integration tests, and the W188/5.129.0 compatibility workflow on the integrated source. During this baseline-only promotion, keep the four known W175/W178 catch-up assertions visible in a separate `continue-on-error` step; do not delete or silently skip them. After the W189 repair restores these behaviors, move `initial-current-source.test.mjs` back into the blocking regression command and remove the temporary non-blocking step.
6. Keep the existing main branch head in the backup and confirm Android, extension, server and other non-Windows files remain present.

## Next stage — branch from main and implement W189

After baseline checks pass:
1. Create a fresh branch from the new `main` for W189 repairs.
2. Restore W169 Electron exception protection and tests.
3. Restore W175 initial-current-source revalidation.
4. Restore W178 next-current-track catch-up and privacy-safe resolve diagnostics.
5. Fix stale «Загрузить версию» state, proposal-status flash and measured UI latency.
6. Preserve successful admin upload and «Предложить песню» flows.
7. Verify playback on the owner's Windows PC; CI green is not audible-playback acceptance.
8. Prepare the next version only after checking the live stable version/sequence floor. The expected next version is not to be hardcoded until that check is done.

## Production OTA remains a separate gated stage

- Keep `publish_to_production=false` until the Hostinger/Floki split and production feed target are reconciled.
- Preserve the hard `FLOKI_PRODUCTION_PUBLISH_NOT_YET_APPROVED` guard and protected environment `windows-stable-production`.
- Verify whether the stable feed is global before any publish. Do not use a global customer rollout as a one-owner test.
- After all source/package/feed checks, provide the owner the exact GitHub Actions approval link and wait for explicit approval.
- Test auto-discovery, signed manifest verification, download, install, restart and preserved local session separately on the already-installed owner copy. Do not claim OTA success before those steps complete.
