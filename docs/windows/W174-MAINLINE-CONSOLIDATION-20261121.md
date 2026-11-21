# W174 — make the latest working Windows build canonical on main

Date: 21 November 2026

## Owner request

The owner wants one clear canonical CELIKOM Windows production line. The latest working version should be in GitHub `main`; older competing Windows snapshots and obsolete experiment/PR clutter should be cleaned up afterward so it is obvious which version is current.

Target candidate: **W173 / CELIKOM Windows 0.24.54.0**, Update Supervisor **0.24.54.0**, Native **0.24.32**, official Yandex Music **5.128.0**.

The owner says the latest version appears to work and is suitable to become primary. The conversation explicitly confirms Yandex 5.128.0 works and real songs reached moderation. The 0.24.54 W173 package was built to remove the extra red “Yandex updated” prompt and preserve the existing Start click. If the exact 0.24.54 installation is not clearly confirmed in the next chat, verify only that point before final acceptance; do not restart broad tests or rebuild without a concrete issue.

## Repository snapshot

- Repository: `manufact-test/nomusic`.
- Default branch: `main`.
- `main` at snapshot: `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- Main Windows app and Update Supervisor still declare **0.24.48**.
- W173 source/package checkpoint: `0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`.
- W173 branch: `experiment/windows-w172-yandex-51280-compat-20261121`.
- W173 branch was 84 commits ahead of main, merge base exactly main snapshot above.
- Latest W173 package is internal/unsigned, not a signed public release.
- Main pre-W170 backup exists: `backup/windows-main-pre-upload-cleanup-20261121` @ `affb7b225d2e7eb2835f53294e975a1e60bb758b`. Create a fresh backup immediately before mainline consolidation anyway.

## W173 scope

W173 carries:
- W170 Windows MP3 upload compatibility and strict HTTP 202/pending/replacement_id confirmation.
- W172 exact official Yandex 5.128.0 compatibility pin and safe reversible native integration refresh.
- W173 stable Start UX: keep the normal “Подождите, идёт подключение к Яндекс Музыке” message; no separate red “Yandex updated” message; preserve an in-flight Start when the exact verified vendor update is detected.
- Unknown/modified Yandex files remain fail-closed.

No changes to server source/deployment, Android source, browser extension, playback pipeline, gain, VPN, routing, auth/access or native host version.

## Verification evidence

- W172 Yandex 5.128.0 candidate run [44894403337](https://github.com/manufact-test/nomusic/actions/runs/44894403337) — SUCCESS.
- W20 safe internal installer stage [44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351) — SUCCESS.
- W15: 469 tests; W21: 41; W24: 20; warnings-as-errors build and disposable install/upgrade/uninstall/package checks passed.
- Owner package artifact ID `14703029534`, run `44894407351`, expires 1 December 2026 10:30 UTC.
- EXE SHA256: `da5877bb01dca6048ce85cb07881f663c3a16cb81ec1f3b16074837bf9b60f33`.
- ZIP SHA256: `d719af9688d74230440887707b9a6cd1c8e2b08af6026cd406c909fd4d3fb4b3`.

## Upload cleanup — final product decision

Shared server cleanup 0.4.78 is already deployed. The post-activation read-only audit [44895271863](https://github.com/manufact-test/nomusic/actions/runs/44895271863) checked all 13 replacements: 13/13 stored hash, size, duration, canonical-normalizer and full-decode checks passed; 9 approved, 4 pending, 0 failures.

The audit inspected canonical files after cleanup. It cannot retrospectively tell which original uploads had removable metadata. Do not claim otherwise.

**Owner explicitly decided against a per-song cleanup journal, removed-tag counters, extra telemetry, or raw MP3 retention.** The requirement is simple: valid songs are cleaned, fully decoded and stored correctly; damaged songs are rejected. No need to record what was removed. Do not add a logging feature.

## Current PR/branch state to reconcile

- PR #65 is open as draft, but points to the older W170 branch `experiment/windows-w170-mainline-20261121` @ `6ce4cc21352912ab31578190007042397e083f64`, not W173. Do not merge PR #65 as-is.
- PR #64 is a closed duplicate W170 attempt.
- PR #62 is separate server upload-cleanup review work (backend is already deployed); do not include in Windows consolidation.
- PR #66 is separate admin rejected/disabled cleanup; do not include in Windows consolidation.
- Preserve `backup/*`, Android A1 branches, server/extension branches and unrelated work. Do not delete them as “old versions”.

## Execution plan for the next chat

1. Read `docs/windows/NEXT-CHAT.md` and this document. Inspect the current refs again; do not rely blindly on this snapshot if main or W173 moved.
2. Inspect full commit graph and complete file diff from current main to W173. Verify that only intended Windows code/docs/workflow changes are included. Confirm no server, Android, browser-extension, access or unrelated admin changes are accidentally entering main.
3. Confirm the exact owner-accepted build is 0.24.54.0. If there is ambiguity about whether the W173 installer was installed and tested, ask one concise question; do not claim owner acceptance based only on CI.
4. Create a new immutable backup branch from current main.
5. Create a fresh PR from W173 to main. PR #65 cannot represent W173 because its head is an older branch. Put the exact target versions and CI evidence in the new PR description.
6. Run full main CI, Windows integration CI, W20 safe installer validation and all applicable gates against the exact PR head. Fix only real failures.
7. Merge the W173 PR to main after checks pass and owner acceptance is clear. Verify app, supervisor and installer identities on main are all 0.24.54.0; verify Yandex 5.128.0 compatibility and W173 Start behavior are present.
8. Close PR #65 as superseded by the W173 PR. Do not touch PR #62 or #66.
9. After main is verified, review obsolete Windows-only experiment branches. Remove only clearly superseded, unprotected Windows work branches and duplicate Windows PR clutter. Preserve every `backup/*` ref and all Android/server/extension branches. Never bulk-delete by prefix.
10. Update `docs/windows/NEXT-CHAT.md` with final main SHA, merged PR, CI runs, backup branch and exact refs removed.

## Hard constraints

- One canonical Windows production line: `main`.
- No reset or force-push of main.
- No deletion of backups.
- No unrelated platform or server changes.
- No redeployment of server 0.4.78.
- No cleanup journal or per-song telemetry.
- No new owner installer unless a real code change requires it.
- Keep work in one complete block; avoid frequent progress reports.
