# W197 — Windows OTA self-verification size-limit fix and 0.24.64 candidate (28 November 2026)

## Root cause

The installed 0.24.62 and published 0.24.63 packages were valid: their signed manifests, package SHA-256 values, and PE versions verified. The actual installed Companion and UpdateSupervisor executable hashes also matched the signed manifest.

The failure was the local verifier's default size ceiling:

- Companion executable: **144,412,407 bytes**.
- UpdateSupervisor executable: **144,445,634 bytes**.
- `StableUpdatePayloadVerifier.MatchesFile` and `OpenVerifiedReadHandle` defaulted to **125,000,000 bytes**.
- Both executables were therefore rejected despite matching SHA-256. Native host and renderer passed.

This blocked current-install verification and supervisor launch before OTA could proceed. The same defect existed in both 0.24.62 and 0.24.63.

## Fix merged to main

- PR [#75](https://github.com/manufact-test/nomusic/pull/75) merged as `3e5f8ae72d51123dec05e5c5e9196535c9b235c1`.
- Installed-payload and verified-executable defaults raised to **250,000,000 bytes**.
- The signed installer download/package ceiling remains **125,000,000 bytes**.
- Restored the existing local staging filename `CELIKOM-W15-WINDOWS-UNSIGNED`. The protected signed-release workflow continues to override the production output name with `/F CELIKOM-Windows-<version>`; production naming is unchanged.

## Validation

- Generic CI: [46139959353](https://github.com/manufact-test/nomusic/actions/runs/46139959353) — SUCCESS.
- Windows integration CI: [46139959369](https://github.com/manufact-test/nomusic/actions/runs/46139959369) — SUCCESS.
- Live Windows OTA matrix: [46139959359](https://github.com/manufact-test/nomusic/actions/runs/46139959359) — SUCCESS for both public 0.24.62 and 0.24.63.
- Both releases passed all four installed payload hashes, the default `MatchesFile` verifier, the default supervisor launch handle, and fresh LKG bootstrap. The synthetic stale-LKG rejection invariant also passed.
- No owner-device journal was read or inferred. No diagnostics need to be repeated.

## 0.24.64 candidate

Main was bumped to app/Supervisor **0.24.64.0**, stable release **0.24.64**, sequence **11**. The existing owner-build trigger ran:

- Build: [46140222345](https://github.com/manufact-test/nomusic/actions/runs/46140222345) — SUCCESS.
- P-256 public-key fingerprint: `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`.
- Signed manifest and release verification: SUCCESS.
- Package SHA-256: `59f4ea6424041f7aaa6cd88d429a3060fa8340fdd7932ef84de186bdb26c56ef`.
- Stable candidate artifact ID: `15260863373`, SHA-256 `9f1404c6c8a1af0ed86c5b1c3c152d7334bfdd0257591e6c5a34913941d60645`.
- Floki transfer artifact ID: `15261072843`, SHA-256 `0b86069179dbfee01150bf3c01485ea8bcefadb9cfccd57658c4c538ad80af4d`.
- Manifest expiry: **2026-12-05 11:31:05 UTC**. Action artifacts expire **2026-11-29 11:32 UTC**.

The candidate build's production Hostinger and Floki publish jobs were **SKIPPED**. Public `latest.json`, the immutable 0.24.63 manifest and package remain unchanged at sequence 10. **0.24.64 is not published yet.**

## Protected publication workflow repair (28 November 2026)

The first manual 0.24.64 promotion attempt, [Actions 46141150754](https://github.com/manufact-test/nomusic/actions/runs/46141150754), failed closed in `prepare` before signing or publication because repository variable `CELIKOM_STABLE_PUBLISHER` was empty. No protected production approval, server mutation, or public feed change occurred.

The target was then resolved from the actual release path, not guessed:
- W194 promoted 0.24.63 through the existing Floki signed spool and updated `.github/release/windows-customer-stable.json`.
- W195 confirms the public customer feed is served from Floki's `/srv/celikom-releases/public/windows-customer-stable`.
- The Floki customer consumer reads the explicit `windows-customer-stable.json` approval record; staging to the local Floki stable feed alone does not publish the customer feed.

PR [#76](https://github.com/manufact-test/nomusic/pull/76) merged as `c1f59b7fd5789e0a828f5a48ce0b118a2bb6ceba`:
- Manual workflow now has `publish_target`, default **floki**; the unset repository variable is no longer a blocker.
- After the existing `windows-stable-production` approval and signed-spool stage, the Floki job verifies the recorded approval, pinned P-256 key, signed manifest, sequence/version and installer SHA-256, then updates the explicit customer approval record with `owner_accepted=true`.
- The customer approval update is monotonic and idempotent.
- A post-promotion job waits for the customer timer and verifies exact public latest bytes, immutable manifest/signature and full installer SHA-256 at both public installer URLs.

PR CI: generic [46142163668](https://github.com/manufact-test/nomusic/actions/runs/46142163668) and Windows integration [46142163775](https://github.com/manufact-test/nomusic/actions/runs/46142163775) — SUCCESS. Post-merge main generic CI [46142412039](https://github.com/manufact-test/nomusic/actions/runs/46142412039) and Windows integration [46142412032](https://github.com/manufact-test/nomusic/actions/runs/46142412032) — SUCCESS. Publisher static gates [46142412042](https://github.com/manufact-test/nomusic/actions/runs/46142412042) remain in progress without starting a job step; the new workflow contract test already passed in PR generic CI and Windows integration CI.

Current public approval record remains **0.24.63 / sequence 10**. The previous owner candidate artifact from run 46140222345 is not used by the corrected flow; the next manual run rebuilds the exact signed package from current main. **0.24.64 remains unpublished until that run passes its protected gate and public HTTPS verification.**

## 0.24.64 protected promotion and recovery (28 November 2026)

- Manual release run [46143048815](https://github.com/manufact-test/nomusic/actions/runs/46143048815) built and signed **0.24.64 / sequence 11** successfully. Manifest package SHA-256: `5245f2bec09ea4a1c8d732b30dde8ef84da4b6f827a45d9e0629a436abc4a5ff`; EXE size: `85,162,732` bytes. Transfer artifact [15262626691](https://github.com/manufact-test/nomusic/actions/runs/46143048815) and stable package artifact [15262856384](https://github.com/manufact-test/nomusic/actions/runs/46143048815) were uploaded.
- The owner explicitly approved environment `windows-stable-production`; GitHub approvals API confirms `state=approved`.
- Floki staging passed and logged `CELIKOM_WINDOWS_SIGNED_RUNNER_SPOOL_READY 0.24.64 11 d1360531539fa4257d456b8ea035b727caa2da9ae5f1e5dc3989c323a867ba69 85162732 private-staged`.
- The same job then failed because `gh: command not found` in a redundant precheck. The existing Python GitHub API approval verification immediately below that line was already present. The public promotion and `verify_customer_stable` jobs were skipped. **Do not describe the public release as verified yet.**
- PR [#77](https://github.com/manufact-test/nomusic/pull/77) merged as `1950228c8db05a7375820b69902417b8d01d9fd4`. It removes the unavailable GitHub CLI call and retains the authenticated Python API approval check. Regression test added. Generic CI [46146131136](https://github.com/manufact-test/nomusic/actions/runs/46146131136) and Windows integration CI [46146131169](https://github.com/manufact-test/nomusic/actions/runs/46146131169) — SUCCESS.
- The already-approved candidate was not rebuilt. After independently rechecking the recorded environment approval and the successful signed/staging logs, the existing `.github/release/windows-customer-stable.json` approval record was advanced to **0.24.64 / sequence 11**, SHA above, `owner_accepted=true`, in commit `bcc4aade47174a0445e41775bf62397718c426d9`.
- The existing Floki customer consumer timer runs every 120 seconds. It reads the main mirror approval, verifies the signed immutable package, publishes the public latest pair/version files/stable installer, verifies exact HTTPS bytes and full installer SHA-256, then writes `accepted.json`. Public consumer completion still needs independent confirmation; the original release workflow's post-promotion verifier was skipped due to the missing CLI command.
- No new channel, rebuild, Android, extension, Windows audio engine, or customer audio data changes.

## 0.24.64 public customer OTA — verified (28 November 2026)

- Read-only Floki audit [46147714670](https://github.com/manufact-test/nomusic/actions/runs/46147714670) — SUCCESS.
- Local signed stable pointer: `versions/0.24.64`; manifest **0.24.64 / sequence 11**, SHA-256 `5245f2bec09ea4a1c8d732b30dde8ef84da4b6f827a45d9e0629a436abc4a5ff`, EXE size **85,160,055 bytes**. Owner receipt `owner-verified.json` reports `https_verified=True`.
- Customer consumer timer/service is active. Its `accepted.json` now records **0.24.64 / sequence 11**, same SHA and `https_verified=true`.
- Customer consumer log confirms `CELIKOM_CUSTOMER_WINDOWS_HTTPS_200_FULL_SHA256 0.24.64` with the exact package SHA and `CELIKOM_CUSTOMER_WINDOWS_SIGNED_RELEASE_APPROVED 0.24.64 11`.
- Public `latest.json` reports 0.24.64 / sequence 11 and exact SHA. Public versioned manifest returned HTTP 200; versioned EXE and `/downloads/windows/CELIKOM-Windows-stable.exe` both returned HTTP 200 with Content-Length 85,160,055. The consumer's full HTTPS SHA verification passed. **0.24.64 is publicly published and verified.**
- PR [#78](https://github.com/manufact-test/nomusic/pull/78) merged as `e5be65932b5bd2ad8b85ebb60dc909fabf9ad665`; PR [#79](https://github.com/manufact-test/nomusic/pull/79) merged as `6299863395412a50c608ae06e869d79fdcd5c499`. They add only read-only Floki audit coverage.
- Residual mirror issue: `celikom-mirror-sync.service` is failed because its atomic push rejected stale branch tips. The mirror's `refs/heads/main` at commit `0719ed01bc8abd2daa81cacdb299ab38c649cabe` already contained the approved 0.24.64 record, so this release completed. Resolve mirror sync before the next release; do not disturb the current public 0.24.64 feed.

## Owner device — one-time bootstrap completed (28 November 2026)

- The owner explicitly consented to the one-time bootstrap and reports that public stable **0.24.64** appeared, installed successfully, and the application seems to work.
- This was a **manual one-time bootstrap** using the already verified public stable installer. It is not evidence that in-app OTA discovery/download/install works.
- No fresh owner diagnostic or detailed runtime acceptance has been supplied yet. Do not claim the app and Update Supervisor exact versions, account/session retention, or all UI/audio behavior are independently verified.
- The old 0.24.62 installed-payload verifier had a 125 MB ceiling and could not self-update to the 250 MB fix. This bootstrap dependency is now satisfied; do not ask the owner to repeat the installer step.

## Next actions — prepare the first real in-app OTA test

1. Collect the owner's new Windows corrections/bug reports and map each against the existing W189/W191/W192 fixes before changing code. Do not repeat known-good work or request W196 diagnostics again.
2. Work from current `main` on a short-lived Windows-only branch; add/fix regression tests, then merge verified changes through the normal PR process.
3. Before the next release, repair the failed `celikom-mirror-sync.service` atomic push/stale-branch issue. Verify mirror parity without changing the currently published 0.24.64 feed.
4. Do not rebuild/re-sign or republish 0.24.64. Read the live signed stable version/sequence floor and use the next allowed version/sequence only after the new changes are accepted.
5. Use the existing signed release workflow and protected `windows-stable-production` approval. Confirm the stable feed's rollout scope before publication; do not bypass approval or silently expose an unapproved global rollout.
6. Verify public latest, detached signature, immutable manifest and full installer SHA-256 over HTTPS.
7. Test the next update from the owner's already installed 0.24.64: discovery and download in the background while Yandex plays; signature/hash verification; durable pending package after close/reboot; install at the next ordinary CELIKOM launch; app/Supervisor version after restart; account/session and Yandex profile retained. No Stop, forced close, playback interruption or manual EXE download.
8. Record each OTA stage separately. The owner-installed 0.24.64 bootstrap is not a pass for the next in-app OTA test.

## Boundaries

No Android, browser extension, Windows audio engine, customer audio data, or new update channel was changed. Do not repeat W196 diagnostics or ask for the same owner test. Keep the existing single Windows stable feed and protected GitHub publication mechanism.
