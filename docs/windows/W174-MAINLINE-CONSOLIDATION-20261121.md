# W174 — CELIKOM Windows 0.24.54.0 promoted to canonical mainline

Date: 21 November 2026

## Outcome

The owner asked to make the latest personally installed and verified CELIKOM Windows build the single canonical production version. The owner explicitly confirmed that the exact W173 **0.24.54.0** package had been installed and works.

**Completed:** W173 was promoted to GitHub `main` through PR [#67](https://github.com/manufact-test/nomusic/pull/67), using a squash merge.

- Repository: `manufact-test/nomusic`
- Canonical branch: `main`
- Merge commit / current main SHA: `aa713b99824f20abbe7c239bf06e356cf3f7f367`
- PR head before merge: `02b3b904bba78ffe490cf8a9ecaac0c20385543a`
- Source/package checkpoint: `0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`
- CELIKOM app: **0.24.54**
- Update Supervisor: **0.24.54.0**
- Installer: **0.24.54.0**
- Official Yandex Music compatibility: **5.128.0**

## Backup

A fresh immutable backup was created before changing `main`:

- Branch: `backup/windows-main-pre-w173-consolidation-20261121`
- Exact preserved pre-merge SHA: `affb7b225d2e7eb2835f53294e975a1e60bb758b`

The backup ref was read back from GitHub and confirmed to point to that exact SHA. Preserve it.

## Scope reviewed

The W173 PR contained 29 changed files, all within Windows source, Windows CI/installer workflows and Windows documentation.

Included:
- W170 Windows MP3 upload preflight and strict upload confirmation.
- W172 exact official Yandex 5.128.0 compatibility and safe reversible native integration refresh.
- W173 Start UX correction: preserve the normal connection message and in-flight Start; suppress the redundant red vendor-update prompt for the exact verified Yandex build.
- Relevant Windows tests, CI workflows and handoff documentation.

Not included or changed:
- Android.
- Shared server source/deployment.
- Browser extension.
- Auth/access, billing, playback, gain, VPN or audio routing.
- Unrelated admin moderation work.

## Verification

All checks succeeded.

### Pull request checks

- General CI: [44898409654](https://github.com/manufact-test/nomusic/actions/runs/44898409654) — SUCCESS.
- Windows integration CI: [44898409698](https://github.com/manufact-test/nomusic/actions/runs/44898409698) — SUCCESS.

### Main after merge

- General CI: [44898706705](https://github.com/manufact-test/nomusic/actions/runs/44898706705) — SUCCESS.
- Windows integration CI: [44898706600](https://github.com/manufact-test/nomusic/actions/runs/44898706600) — SUCCESS.
- W20 safe installer staging: [44898706605](https://github.com/manufact-test/nomusic/actions/runs/44898706605) — SUCCESS.

The main W20 run compiled the application and installer with warnings as errors, ran native bridge and host preflight tests, tested native image construction and crash recovery, validated updater ZIP selection/PE version/anti-downgrade, passed disposable per-user install/uninstall smoke, and packaged one internal installer ZIP with checksums.

Main W20 artifact:
- [14705515606 — CELIKOM-Windows-internal-stage-aa713b99824f20abbe7c239bf06e356cf3f7f367](https://github.com/manufact-test/nomusic/actions/runs/44898706605/artifacts/14705515606)
- Internal unsigned staging artifact, not a signed public release.
- Expires 1 December 2026, 11:24 UTC.

Earlier W173 evidence retained:
- Official Yandex 5.128.0 candidate and reversible vendor sandbox: [44894403337](https://github.com/manufact-test/nomusic/actions/runs/44894403337) — SUCCESS.
- Owner package stage: [44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351) — SUCCESS.
- W15: 469 tests; W21: 41; W24: 20; warnings-as-errors builds and disposable installer checks passed.

## Repository cleanup explicitly deferred

The owner clarified that old Windows branches, historical versions and PR clutter should **not** be deleted now. The project is expected to move from GitHub to a separate owner-controlled server later; repository cleanup can be considered then.

Therefore:
- No branches were deleted.
- No historical PRs were closed as part of this task.
- PR #65 (older W170) remains untouched.
- PR #62 (server upload cleanup) remains untouched.
- PR #66 (admin cleanup) remains untouched.
- All `backup/*`, Android, server and extension refs remain untouched.

Do not resume cleanup unless the owner explicitly asks after the server migration.

## Final operating rule

`main` is now the one canonical Windows production line. All future Windows development starts from current `main`. Do not reset or force-push `main`; preserve the verified backup. No new installer is needed unless a concrete code change requires one.
