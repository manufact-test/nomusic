## Infrastructure release addendum — 25 November 2026 (owner downloads)

The CELIKOM infrastructure chat prepared a single trusted Floki bootstrap at `.github/scripts/floki-release-owner-bootstrap.sh` and reused the existing Windows signed-spool root consumer, installer and P-256 pin, without changing audio code. Exact 0.24.56 EXE SHA-256 `2ee81ceaf9488cc80b88e312053af1744c0b801a8f8f6e725c40266e5553c15a` remains privately staged pending live root activation and full owner-auth HTTPS confirmation. The next Windows developer **must not** run a separate per-release root installer or create more ad hoc GitHub download links; use the permanent signed owner producer/consumer after bootstrap.

Owner latest = latest verified signed *test candidate* behind site Basic authentication. Customer stable update feed must remain separately controlled by owner acceptance. The signed 0.24.56 installed-client replacement/audio regression has not yet been accepted; first make the exact 0.24.56 available on celikom.com and test that version before any new Windows audio changes.

Future Windows versions: only main, verified signed manifest with increasing sequence, existing spool workflow; root consumer independently validates and publishes immutable version + owner latest. Do not weaken signature pin or change Hostinger until real old→new OTA has been confirmed. Infrastructure status and blockers: `docs/migration/CELIKOM-RELEASE-PUBLICATION-HANDOFF-2026-11-25.md`.

---

# CURRENT WINDOWS — W176 permanent Floki delivery: signed 0.24.56 staged, owner HTTPS root activation BLOCKED (25 November 2026)

## Exact current position

- **Business rule from owner:** every new Windows version becomes the main, directly downloadable EXE on `https://celikom.com`; keep the previous exact EXE and signed release for rollback. Owner handles only install/listen/acceptance, not terminal/GitHub draft download.
- Last owner installed: **0.24.55.0**, connected but owner reported NO replacement audio. **0.24.56** W175 narrow already-loaded current-track revalidation correction is compiled/signed but NOT owner-tested.
- Signed Windows release [run 45653125688](https://github.com/manufact-test/nomusic/actions/runs/45653125688) SUCCESS, source `3c743332d134618fd4bba39ee826e833f39aa54c`, owner EXE SHA-256 `2ee81ceaf9488cc80b88e312053af1744c0b801a8f8f6e725c40266e5553c15a`, size **85,149,440**, schema2 P-256 signed sequence **3**, unpublished private drafts 458351822 and 458351971. No public feed.
- Existing site route confirmed in previous successful owner acceptance: `/downloads/windows/CELIKOM-Windows-0.24.55.exe` Basic-auth protected. Last independently confirmed root `/srv/celikom-releases/windows/stable/current` -> `versions/0.24.55`, sequence 2. **0.24.56 is NOT yet live on website; do not give a made-up URL or the old 55 link.**
- **Permanent data-only Floki transfer is FIXED and ACTUALLY VERIFIED:** [run 45659773351](https://github.com/manufact-test/nomusic/actions/runs/45659773351) SUCCESS on native `celikom-ci-smoke-only` / `celikom-floki-ci01`. Exact signed 0.24.56 ZIP (85,152,111 bytes) SHA256 `736f4580e2d4580e84457e79849bb70dc82fab7f39621bdda367044c3de7f1bf` persisted atomically as `/home/runner/celikom-windows-signed-spool/windows-0.24.56-3-736f4580e2d4580e84457e79849bb70dc82fab7f39621bdda367044c3de7f1bf.zip` inside runner, corresponding host bind mount `/srv/celikom/ci-runner/runner/celikom-windows-signed-spool`. Actual signed installer SHA verified inside ZIP by P-256 before staging. NO SSH / root keys in runner. `gh` CLI not needed; Python token-scoped GitHub REST downloader with strict authenticated API→unauthenticated GitHub asset CDN redirect.
- **Root activation is NOT DONE:** secure admin run [45662358922](https://github.com/manufact-test/nomusic/actions/runs/45662358922) FAILED before obtaining a GitHub-hosted `ubuntu-22.04` runner (runner_id=0, no steps). Windows+Linux GitHub-hosted jobs have been failing similarly; this is NOT a root-service failure. The isolated runner deliberately cannot SSH to VPS port22 (proved `Connection refused` in [45658731022](https://github.com/manufact-test/nomusic/actions/runs/45658731022)). Never change Docker isolation or mount host root/SSH for convenience.
- Checked-in root-only one-time deployment is **prepared, reviewed by exact Git blob pin**, but not run. The scripts do NOT execute untrusted spool payload:
  - `.github/scripts/floki-windows-signed-root-consumer.py` — pinned to root P-256 DER, validates untrusted spool path/mode/UID/inode/hash, independent installed root importer signature and monotonic version, atomically promotes to root-owned `stable/current`, copies exact checked EXE to root:www-data owner directory, updates permanent `CELIKOM-Windows-latest.exe` as hardlink, verifies BOTH versioned and latest HTTP200 with owner Basic credentials and complete SHA-256.
  - `.github/scripts/floki-windows-owner-download-bootstrap.sh` — one-time safe Nginx exact Windows-version + latest allowlist, site-level Basic Auth inherited, nginx test/reload, rollback on failure, other Nginx routes unaffected. Existing 55 route remains.
  - `.github/scripts/floki-windows-root-consumer-install.sh` — one-time root hash-pinned installer and systemd 1-minute timer `celikom-windows-signed-owner.timer`, verifies initial 0.24.55 floor, runs first import before activating recurring timer.
  - `.github/workflows/windows-root-spool-bootstrap.yml` — existing approved `floki-deploy` environment SSH through GitHub-hosted runner, hash-pinned only; trigger file `.github/deploy/windows-root-bootstrap.trigger` created, first run failed at runner allocation. If GitHub-hosted executor is restored, retry THAT exact job; otherwise use another separately approved remote administration channel, NEVER let selfhosted CI run root commands.
  - `.github/scripts/tests/floki-windows-signed-root-consumer.test.py` — isolated spool safety, signed parser, static Nginx syntax and exact source Git blob pin tests. Initial run [45662134715](https://github.com/manufact-test/nomusic/actions/runs/45662134715) had a **test harness** bug (runpy globals shadow). Fixed in `abef20d07c3ea287be21e0e68b3c901dcb52874a5`, subsequent [run 45662617113](https://github.com/manufact-test/nomusic/actions/runs/45662617113) requested. Check current result and fix test failures before any root activation.
- New Windows stable signer workflow now automatically calls `.github/workflows/windows-stable-floki-private-stage.yml` after successful approved signed mainline build. The latter uses existing selfhosted Floki runner ONLY to store verified DATA into isolated private spool; a separately pinned root service, when installed, does independently verified atomic deployment. No GitHub-hosted Linux transfer, no need to install GitHub CLI, no CI root permissions.
- DO NOT declare 0.24.56 delivered to user until root activation succeeds AND real owner-credential HTTPS download is HTTP200 and SHA256 exactly `2ee81ceaf9488cc80b88e312053af1744c0b801a8f8f6e725c40266e5553c15a`. Then give `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.56.exe`, and permanent `https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe`. Until proven live do NOT paste either as working link.
- Keep 0.24.55 immutable in `versions/0.24.55` and original owner download as the rollback. Preserve exact repo backup `backup/windows-02456-delivery-floki-runner-20261125`. Main is shared with Android/extension concurrent developers: always re-read live main before edits; Windows only, no new branch or audio architecture/UI modifications. No public auto-update manifest, no paid features, no Hostinger deletion. After owner playback accepts 56, separately complete signed auto-update HTTPS feed and prove transition to 57.

## Immediate action

Get approved protected admin bootstrap to execute ONCE (GitHub-hosted runner allocation must resume OR invoke Work/cloud SSH using approved owner credentials, no user's terminal), independently verify installed root importer, `stable/current`=56, Nginx and full private HTTP200+SHA256, and only then send one website EXE link. If the existing hosted job still fails before first step, do not claim server publication; document exact failure and preserve signed spool with queued root activation.

---

# CURRENT WINDOWS — W175 0.24.56 owner regression, FlokiNET transport pending (25 November 2026)

## Owner report and direct evidence

The owner installed CELIKOM **0.24.55.0** on Windows over the accepted 0.24.54 baseline and reported **no music replacement** while Yandex Music 5.128.0 visibly played the real "Ау" track. GUI showed a teal connected state, "Версия CELIKOM доступна" and signed-in account; this is *availability*, not audible replacement. W54 diagnostic at 2026-11-25T16:07:10Z had NativeIntegration ACTIVE, BridgeStarted/Enabled/SignedIn=true, host+renderer handshake and current native observer attached, but **no new RESOLVE_REQUEST/NATIVE_FILEINFO_REQUEST/GRANT_FOUND/SOURCE_ACTIVE_REPLACEMENT or player-network events** for that session. `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE` and `STABLE_UPDATE_CHECK_FAILED` are expected while owner-protected signed feed returns 401; do not confuse them with source injection failure.

Protected root read-only live API check [45651443471](https://github.com/manufact-test/nomusic/actions/runs/45651443471) SUCCESS: exact Windows `GET /api/v1/resolve?service=yandex&track_id=144530503&audio_formats=mp3,m4a&audio_profile=windows_gain_v1` returned authorized `found:true` with `gain_applied:false` and an exact .NET GrantValidator-compatible signed `audio/mpeg` URL for each of two entitled accounts; both signed 1024-byte Range reads returned HTTP206. Ephemeral test sessions were deleted. This proves the migrated API/song exists and issues working signed bytes; no conclusion about the owner's own DPAPI token or actual browser/CORS decoder is justified.

## W175 narrow code fix and tests

- Fresh immutable backup made before the change: `backup/windows-02455-pre-current-track-recovery-20261125` at `afcafbbccf183ddbe1602e27d2e0478d3e7f98da`.
- `windows-companion/w23/renderer-entry.mjs` patch at `9a18b544656e613a1747ca056e5f3bdc9932938c`: initially enabled native bridge now performs **one** delayed (3.5s settling) exact-current-track authenticated grant revalidation if Yandex already loaded an original media source before hook attach. Only a current PLAYING/PAUSED valid ID and positive `adapter.prime()` grant can request the existing `playerSourceRefresh.request(id)` → Yandex `reloadEntity("QUALITY_CHANGE")`. No alternate player, track queue, seek, pause, VPN/gain or server behavior changed. All Stop/origin-change/generation conditions suppress stale work. Diagnostic markers `NATIVE_INITIAL_SOURCE_REVALIDATE`, `NATIVE_INITIAL_SOURCE_RELOAD[_OK/_DEFERRED]`.
- New regression file `windows-companion/w23/initial-current-source.test.mjs`, wired into `.github/workflows/windows-w98-integration-ci.yml`. [Windows integration #45652096445](https://github.com/manufact-test/nomusic/actions/runs/45652096445) **SUCCESS**, including the W22/W23/W60 original-source, VPN, 403, audio regressions and new cold-start contracts. [General CI #45652096441](https://github.com/manufact-test/nomusic/actions/runs/45652096441) **SUCCESS** at test-wiring checkpoint.
- No claim the fix is user-accepted or audible yet; actual source acceptance is owner's next test.

## Private 0.24.56 package ready; Floki transfer blocked by hosted runner

- Companion, Update Supervisor and Inno installer metadata incremented from 0.24.55 to **0.24.56**; protected signing sequence from **2→3**; original signed stable publisher remains fail-closed to public release. A historical fixed-2 contract assertion was changed to validate the current monotonic pinned workflow sequence, not bypass signature checks.
- Windows-hosted protected signed release **[45653125688](https://github.com/manufact-test/nomusic/actions/runs/45653125688) SUCCESS**: exact source commit `3c743332d134618fd4bba39ee826e833f39aa54c`, 0.24.56, P-256 schema2 detached manifest, immutable package, signed sequence **3**, trusted public DER SHA256 `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`. The EXE itself is not Authenticode signed. No public release.
- **Direct private owner EXE** (requires GitHub repository access): `https://github.com/manufact-test/nomusic/releases/download/untagged-fd58dae6558d32121d80/CELIKOM-Windows-0.24.56.exe`. Draft ID `458351822`, EXE asset `792244646`, 85,149,440 bytes, SHA256 `2ee81ceaf9488cc80b88e312053af1744c0b801a8f8f6e725c40266e5553c15a`. ZIP and SHA256SUMS included separately in draft for immutable provenance. P-256 feed metadata in separate draft ID `458351971`, tag `celikom-windows-v0.24.56-floki-feed-candidate`, source commit and file checks all match. **Do not publish either draft**.
- Updated protected `.github/workflows/windows-stable-floki-private-stage.yml` defaults to this exact 0.24.56/3/source commit. Explicit staged transport trigger `ab8a27a4122cab2edad299cd7d8c9e64c67cc885` initiated [run #45654110452](https://github.com/manufact-test/nomusic/actions/runs/45654110452); **failure twice before a hosted `ubuntu-latest` runner was assigned (runner_id=0, 0 steps)**. No EXE transfer or independent root import occurred. Do not claim `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.56.exe` works or exists. Do not weaken the isolated FlokiNET runner/SSH secrets isolation to bypass unavailable GitHub-hosted jobs; rerun verified transport when appropriate.
- **Old 0.24.55 owner EXE stays unchanged** at `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.55.exe`, and Floki root-owned stable/current still targets `versions/0.24.55`, signed sequence2. No public automatic feed, payments or Android changes.
- Some later general CI jobs failed with runner_id=0 and empty steps (hosted runner allocation), not product test failures. Earlier v56 release initial run failed due the now-fixed historical test assertion, followed by #45653125688 SUCCESS. Avoid conflating infrastructure failure with code regression.

## Immediate next actions

1. Owner can manually install the exact verified **private 0.24.56 EXE** from GitHub over 0.24.55, preserving settings, then play original Yandex "Ау" and confirm actual replacement, correct UI status, pause/Next and VPN. Collect a new W54 diagnostic only if replacement still fails.
2. Retry approved protected draft-to-Floki data-only intake and independent root verification if GitHub-hosted jobs are available; publish **owner-only** direct 0.24.56 EXE under `/downloads/windows/` with existing Basic auth. Never expose private feed or change `stable/current` before owner acceptance.
3. After owner-confirmed playback, finish fixed HTTPS signed update channel, replace disabled Hostinger publisher with a separately reviewed Floki release pipeline, and verify real newer-version update with fresh P-256 signature and safe-point rollback. No public/paid enablement before owner approval.
4. Preserve all backups and freeze at exactly two legacy CELIKOM Hostinger sources. Do not modify Android, extension, server, audio routing/gain or VPN based on speculation; concurrent non-Windows development on `main` may advance HEAD and stale-main protected jobs must be retried rather than bypassed.

---

# CURRENT WINDOWS — FlokiNET owner acceptance, CELIKOM 0.24.55 (25 November 2026)

## Production baseline and scope

- GitHub private primary: `manufact-test/nomusic`, Windows works only in `main`; Forgejo `celadmin/nomusic` is one-way GitHub → Forgejo backup.
- **0.24.54.0 remains the last personally accepted Windows runtime baseline.** W173 audio/Start/VPN/gain/UI must be preserved.
- **0.24.55** is the current prepared Windows owner candidate: Companion, Update Supervisor and Inno installer all declare 0.24.55.
- Owner-only direct EXE: `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.55.exe`, protected by the existing website Basic credentials (anonymous HTTP 401). This is one installer for normal in-place upgrade, not a public release.
- Native/Yandex playback architecture was not changed for the API migration; official Yandex 5.128.0 support remains from W173.
- New production API: `https://api.celikom.com`. Runtime API app: `/srv/celikom/app/staging-20261122`, DB: `celikom_cutover_20261124`. Do not redeploy server or unfreeze Hostinger source to test Windows.
- The DPAPI SessionStore stores existing user tokens and installation identity. `CelikomApi.MigrateProductionOrigin` migrates **only** the exact legacy Hostinger API origin to `https://api.celikom.com`, and persists it atomically; other origins are not rewritten. Initial 0.24.54 → 0.24.55 upgrade must be manual, because the old 0.24.54 package did not have the new feed public trust pin embedded.

## Independent live FlokiNET acceptance evidence (25 November 2026)

- GitHub-hosted privileged *read-only* remote check: [45611425032](https://github.com/manufact-test/nomusic/actions/runs/45611425032) — **SUCCESS**, using the existing owner-approved secured FlokiNET SSH environment. No server files or database changed.
- Root-owned `/srv/celikom-releases/windows/stable/current` points to `versions/0.24.55`; exact `CELIKOM-Windows-0.24.55.exe` is 85,145,078 bytes, SHA-256 `f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487`, and has a PE/MZ header.
- P-256 DER signature on the immutable 0.24.55 manifest was independently checked by OpenSSL against root-pinned public DER fingerprint `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`. Manifest schema2, version 0.24.55, sequence **2**, package URL/size/hash matched. The manifest expires **2026-12-01 17:14:29.349 UTC**. Check expiry before any later publishing.
- **Signing terminology:** the P-256 *manifest* and exact installer SHA-256 are verified. The EXE itself is **not Authenticode-signed**; the signed-release workflow explicitly builds without Authenticode/PFX. Do not claim a Windows publisher certificate, or a certificate expiration date, exists.
- Actual HTTPS checks: `GET /api/v1/health` and `/api/v1/config` 200; unauthenticated `auth/me`, `entitlement` and `resolve` 401; Nginx config syntax passes.
- Owner download and `/CELIKOM/Windows/Updates/stable/latest.json`, detached `.sig`, immutable 0.24.55 manifest routes all return HTTP 401 anonymously. This is **intentional pre-acceptance protection**: the Windows updater does not carry the owner's Basic password; auto-update remains *blocked* until a reviewed signed feed route is approved.
- Separate shared-backend authenticated test [45611263231](https://github.com/manufact-test/nomusic/actions/runs/45611263231) — SUCCESS: authenticated me, entitlement, Start/activate, same-origin replacement resolve, two signed Range 206 audio reads, trial unchanged; temporary session removed and subsequent access denied. This proves the new API path for a controlled session, **not** the owner's saved DPAPI session or audible replacement in CELIKOM Windows.
- The one-off remote audit request `.github/deploy/floki-maintenance-request.sh` was returned to an inert no-op via commit `955f88593eb261a302468ecd1ca976df1f62ebd9`, and [45611603357](https://github.com/manufact-test/nomusic/actions/runs/45611603357) succeeded. Backup before audit: `backup/windows-floki-pre-acceptance-audit-20261125`.
- No Windows EXE rebuild, server deployment, public feed publication, paid feature enablement, Android change, browser extension change, or Hostinger shutdown in this task.

## Remaining work, in order

1. Owner downloads the **existing exact 0.24.55 EXE** with Basic authentication and installs it over the existing Windows package; check preserved login, new API, replacement audio (including real mapped song), status colors/Start, upload, and behavior during VPN switches. Collect CELIKOM diagnostic only for a real failure.
2. **Only after owner acceptance**, review and enable the exact fixed HTTPS signed feed routes from the root-owned FlokiNET store, public GET only for signed latest/immutable manifest/signatures and version-matched installer; never expose private storage, secrets, CMS, admin or paid endpoints. Current Basic 401 must not be bypassed early.
3. Current `.github/workflows/windows-stable-signed-release.yml` has an **obsolete, currently blocked** `publish_to_production` path to `.github/scripts/windows-stable-publish-hostinger.sh`. Replace it with a reviewed FlokiNET production path, **not** by simply unblocking the old Hostinger job. Preserve the existing Windows-hosted build/signing and the FlokiNET private staging trust boundary.
4. To prove real automatic upgrade, prepare the next strictly increasing version (greater than 0.24.55) and signed sequence (greater than 2), with a fresh valid expiry, verify hash/DER pin, publish atomically through the reviewed FlokiNET path and run a real owner safe-point update without playback interruption. Verify rollback, login retention and no downgrade. Do not manufacture an extra installer or update just for an unaccepted migration.
5. Keep the exact legacy Hostinger string only in the deliberate one-time DPAPI session-origin migration and any known old-client compatibility bridge until corresponding clients are accepted. Keep old Hostinger applications frozen, not deleted; paid features off. No unrelated work or branch cleanup.

---

# CURRENT WINDOWS — canonical CELIKOM 0.24.54.0 on main (21 November 2026)

Read these documents first:

1. `docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md` — completed promotion record, final main SHA, CI and backup.
2. `docs/windows/W173-START-UX-AND-OWNER-UPLOAD-AUDIT-20261121.md` — owner-accepted W173 implementation, Yandex 5.128.0 compatibility, Start UX and upload audit.
3. `docs/windows/W170-WINDOWS-UPLOAD-AUTO-CLEANUP-20261121.md` — original Windows upload compatibility contract.

## Canonical production state

- Repository: `manufact-test/nomusic`.
- The only canonical Windows production line is GitHub `main`.
- W173 code-promotion squash-merge commit: `aa713b99824f20abbe7c239bf06e356cf3f7f367`. Handoff documentation was committed afterward; resolve the live `main` ref before any future ref operation.
- Promoted implementation: W173 / CELIKOM Windows **0.24.54.0**.
- App: **0.24.54**; Update Supervisor: **0.24.54.0**; installer: **0.24.54.0**.
- Official Yandex Music **5.128.0** compatibility pin is present.
- The exact W173 0.24.54.0 package was installed and accepted by the owner before promotion. Do not ask the owner to repeat that test or rebuild without a concrete failure.
- PR [#67](https://github.com/manufact-test/nomusic/pull/67) was squash-merged successfully. Merge commit: `aa713b99824f20abbe7c239bf06e356cf3f7f367`.

## Verified backup

- Pre-promotion `main` HEAD: `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- Immutable backup: `backup/windows-main-pre-w173-consolidation-20261121`.
- Verified backup ref still points exactly to the pre-promotion SHA above.
- Preserve this backup.

## CI and installer verification

All checks below completed successfully:

- PR #67 general CI: [44898409654](https://github.com/manufact-test/nomusic/actions/runs/44898409654).
- PR #67 Windows integration CI: [44898409698](https://github.com/manufact-test/nomusic/actions/runs/44898409698).
- Main push general CI: [44898706705](https://github.com/manufact-test/nomusic/actions/runs/44898706705).
- Main push Windows integration CI: [44898706600](https://github.com/manufact-test/nomusic/actions/runs/44898706600).
- Main push W20 safe installer stage: [44898706605](https://github.com/manufact-test/nomusic/actions/runs/44898706605).
- W20 artifact: [14705515606 — CELIKOM-Windows-internal-stage-aa713b99824f20abbe7c239bf06e356cf3f7f367](https://github.com/manufact-test/nomusic/actions/runs/44898706605/artifacts/14705515606). Internal unsigned staging artifact; expires 1 December 2026, 11:24 UTC.
- W20 compiled the installer, verified app/supervisor/PE versions and updater ZIP anti-downgrade, and passed disposable per-user install/uninstall smoke.
- Existing official Yandex 5.128.0 candidate verification: [44894403337](https://github.com/manufact-test/nomusic/actions/runs/44894403337) — SUCCESS.
- Existing W173 owner package stage: [44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351) — SUCCESS.

## Scope and owner decisions

- W170 upload compatibility, W172 Yandex 5.128.0 support and W173 Start UX are now part of `main`.
- No Android, server, browser-extension, access, billing, playback, gain, VPN or audio-routing changes were included in the promotion.
- Shared server cleanup 0.4.78 is already deployed. Do not redeploy it as part of Windows work.
- Do not add a per-song cleanup journal, removed-tag counters, extra telemetry or raw MP3 retention.
- The owner explicitly asked to postpone old-branch/PR cleanup. **Do not delete branches, close old PRs or perform repository housekeeping now.** Revisit only after the planned move to the owner's separate server, if the owner wants it then.
- PR #65 (older W170), PR #62 (server upload cleanup) and PR #66 (admin cleanup) were left untouched. All backup, Android, server and extension refs remain untouched.

## Next-chat operating rules

- Start from current `main`, not an old Windows experiment branch.
- Treat 0.24.54.0 as the current owner-accepted Windows baseline.
- Do not redo mainline consolidation; it is complete.
- Do not clean up branches or PRs until the owner explicitly reopens that task after the server migration.
- Continue only with the next concrete CELIKOM task. Keep work focused and avoid unnecessary status reports.

---

# PREVIOUS WINDOWS W170 — owner upload runtime testing (21 November 2026)


This section is historical context for the original W170 upload change. The active handoff is the W173 section at the top of this file.

## Repository state

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/windows-w170-mainline-20261121`
- PR: [#65 — W170 Windows upload compatibility](https://github.com/manufact-test/nomusic/pull/65) — still open as a draft on the older W170 branch; it is superseded by the W173 candidate and must not be merged as-is.
- Product: CELIKOM Windows only.
- Owner-accepted source baseline: app **0.24.51.0**, native **0.24.32**.
- W170 internal build: app **0.24.52.0**, update supervisor **0.24.52.0**, native host/module unchanged.
- Main pre-work backup: `backup/windows-main-pre-upload-cleanup-20261121` @ `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- At the W173 handoff, `main` still contains Windows 0.24.48. The owner has requested W173 0.24.54.0 become canonical on main; follow the W173 mainline-consolidation plan at the top of this file.

## What W170 changed

- Windows already used the shared authenticated `POST /api/v1/uploads`; the endpoint was not replaced.
- MP3 local duration preflight now recognizes the bounded leading ID3v2 / Info-Xing / APEv2 / ID3v1 metadata variants accepted by the extension/server cleanup.
- Local inspection is read-only: no cleanup, rewrite or transcoding in Windows. The original selected bytes go to the server unchanged.
- Upload success requires HTTP **202**, `status=pending`, and a positive `replacement_id`; generic 2xx or malformed bodies are not success.
- Clear errors are shown for `invalid_mp3`, `invalid_m4a`, `upload_too_large`, and missing server confirmation.
- Existing 30 MiB limit, 1.5-second duration tolerance, rights declaration, request ID/deduplication and in-flight duplicate-submit guard remain.
- The deployed server remains authoritative for metadata cleanup, duration measurement and full audio decode. **Do not redeploy server code.**

## Verification and delivered package

All checks for the built source passed on 21 November:

- Main CI [44887076540](https://github.com/manufact-test/nomusic/actions/runs/44887076540) — SUCCESS.
- Windows integration CI [44887076485](https://github.com/manufact-test/nomusic/actions/runs/44887076485) — SUCCESS.
- W20 safe internal installer staging [44887071981](https://github.com/manufact-test/nomusic/actions/runs/44887071981) — SUCCESS.
- W15 native contract: **467 passed**.
- W23 native tests: **156 passed**; W24 image-builder: **20 passed**; W21 recovery contract: **41 passed**.
- GUI and supervisor warning-as-error builds, PE/version/anti-downgrade validation, disposable per-user install/uninstall, package and checksum checks all passed.

The owner was already given these files in the previous chat:

- `CELIKOM-W170-WINDOWS-UPLOAD-CLEANUP-02452-UNSIGNED.exe`
- `CELIKOM-Windows-0.24.52.zip` (contains exactly one root EXE, byte-identical to the standalone installer).
- Installer SHA256: `4a5c75bc70a936acfbc6af0c1c9d03281921203afce75b5fed55473a7ef59dc7`
- ZIP SHA256: `edd505333e400f0ef5da3d0c0aff3983b14255979cb5eb0f4d6fb7c7f5e67a4c`
- GitHub Actions artifact ID `14700675953`, run `44887071981`; expires **1 December 2026, 08:58:05 UTC**.

This is one internal unsigned owner-review build, not a production release. No signing, public feed or server deployment.

## Owner runtime follow-up — superseded by W173

The original W170 handoff was waiting for real-file testing on 0.24.52. Subsequent owner testing moved to W172/W173 and official Yandex 5.128.0.

- The owner confirmed Yandex 5.128.0 works and several real songs reached the moderation queue.
- Five new submissions were inspected at the stored/canonical-file level; later widened read-only audit covered all **13** post-activation uploads.
- Run [44895271863](https://github.com/manufact-test/nomusic/actions/runs/44895271863) verified **13/13** stored hash, size, duration, canonical-normalizer and full-decode checks; 9 approved, 4 pending, 0 failures.
- This does not identify which original files contained removable metadata because the audit reads files after server cleanup.
- Owner explicitly declined a per-song cleanup journal, removed-tag counters, extra telemetry and raw-file retention. Do not add these.
- Continue from the W173 current handoff; do not reopen the W170 work as a separate new task.

## Hard boundaries

Do not change playback, volume, Next/Previous, radio, VPN, audio routing, native Yandex host, Android, browser extension, auth/access, billing, moderation, or the already-deployed server. No speculative refactors or broad audits. Preserve the main backup and the current owner-accepted Windows line.


---

# CURRENT WINDOWS W169 (17 November 2026)

Read **`docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md`** before any other Windows history. Active source: UI `1ac135ba5312473cc6c7feca8d1f5f57726f5342`, native exception guards `b2f9131132e26020fd861dcb71d3c33b8ff9a0c1`. App **0.24.51.0**, native **0.24.32**, backup `backup/windows-w169-pre-track-handoff-crash-investigation-20261117` @ `92e0d9e63f5fd7dc7f243d7c2a2202cf5ad8b2de`. Owner says green status in 0.24.50 works; preserve it. No VPN modifications. **Actual Yandex restart mechanism not proven by old diagnostics; guards eliminate unsafe unhandled Node rejection/callback failure but runtime owner must confirm.**

---

# CELIKOM Windows — active W168 handoff (17 November 2026)

**W168 delivered for owner review:** W20 run `44051448677` SUCCESS; 0.24.50.0 owner installer/ZIP/SHA256 independently checked and verified in personal Library `/CELIKOM/W168/`. The Yandex spontaneous restart is STILL UNRESOLVED; see dedicated W168 incident doc. No audio/VPN/native module changes.

**CURRENT OWNER BUGS, not W167 stale instructions:** Read `docs/windows/W168-OWNER-THREE-ISSUES-20261117.md` FIRST. Owner has 0.24.49.0 and supplied two W54 diagnostics. W168 UI fixes committed at `2c352479b267266cd62fab7d8221bab97051c539` for (1) idle prompt after Start, (2) green available/paused labels without false audible claim. Proposed 0.24.50.0, native still 0.24.31. W168 backup: `backup/windows-w168-before-owner-three-fixes-20261117` @ `31e364bfba8795f84502f050d6716b2b6639f5cf`. **Third issue (actual Yandex main-process restart 08:13:54Z) diagnosed but root cause NOT proven; do not call it repaired or touch VPN/audio/host speculatively.** W167 documentation below is historical.

---

# CELIKOM Windows — active handoff W167 (16 November 2026)

**Status:** W167 UI fixes are committed on the W165-based branch. The single internal W20 owner-review package is being prepared; CI and owner runtime acceptance are still pending. W166 / 0.24.48.0 remains rejected and was not used as the implementation base.

## Exact repository state

- Repository: `manufact-test/nomusic`
- Product: **CELIKOM Windows only**
- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`
- W167 source checkpoint: `e88280740457bf539ec8e661416a26d9de1e1102`
- CI validation checkpoint: `8964ec124025cf2f480c0f913f5b7b2d69a90f00` (Main CI and Windows integration CI both succeeded).
- App version: **0.24.49.0**
- Native module: **0.24.31**
- Rollback branch before W167 fixes: `backup/windows-w167-pre-ui-fixes-20261116` @ `ea788eaed198b71db787215b9ba85829766d6062`
- W165 code baseline: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`
- Original pre-W166 backup: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`
- Main/W166 was not reset, force-pushed or modified by W167.

## W167 implementation

1. **Start / module refresh:** `StartAction` no longer clears `_compactStarting` before `ConnectYandexAsync`. The green Yandex connection banner remains visible through the existing module validation and upgrade. Startup completion is blocked while native integration is busy or the installed module still mismatches. If the initial consent prompt is declined, the banner is cleared. The real version check, upgrade, entitlement checks and fail-closed behavior remain intact.
2. **Transient waiting copy:** the fresh-heartbeat + `UNKNOWN` fallback now returns an empty track row. The same old waiting copy was removed from the legacy `_switchHint`, `_song` and service-status fallbacks. W164's 2.5-second previous-title/artist handoff, raw Track-ID suppression and pending-presence suppression are unchanged.
3. **Pause:** `Пауза` is neutral in both compact and legacy UI. The header connection dot/label still follow the independent fresh native-service heartbeat and may remain green.
4. **Active replacement:** the green predicate is centralized and remains strict: enabled bridge, fresh heartbeat, `ACTIVE_REPLACEMENT`, current `PLAYING`, `NATIVE_SOURCE_VERIFIED`, and approved presence. Mapping, HTTP 206, prefetch, entitlement or generic PLAYING cannot turn the label green. No W166 DOM observer was copied; no current W55 diagnostic was supplied to justify it.
5. **Spacing:** idle/disabled placeholder remains 18 px. Active status uses a 28 px row and 2 px lower gap before Account. No global window, title, artist or idle spacing changes.
6. **Scope:** no W23 native host/renderer, audio, VPN, source routing, server, auth, Android or browser-extension code changed.

## Verification and package — all CI passed

- Main CI: [run 43903409504](https://github.com/manufact-test/nomusic/actions/runs/43903409504) — **SUCCESS**.
- Windows integration CI: [run 43903409454](https://github.com/manufact-test/nomusic/actions/runs/43903409454) — **SUCCESS**.
- W20 safe installer staging: [run 43903271312](https://github.com/manufact-test/nomusic/actions/runs/43903271312) — **SUCCESS**.
- W20 source commit: `025a51d7478b3c7591f893a5dc55fd8ecfee7bdc`; it contains the full W167 source checkpoint above. Latest branch HEAD differs only by branch-scoped CI trigger configuration and this documentation update.
- W15 contract tests: `W15_NATIVE_CONTRACT_PASS 436`; W23 native tests and W24 native image-builder tests passed.
- W20 passed warnings-as-errors compilation, stage-only policy, PE file-version/identity and anti-downgrade validation, disposable install, same-AppId in-place upgrade, uninstall without touching Yandex, and one-installer ZIP/SHA256 checks.
- One internal unsigned owner-review package only:
  - Installer: `CELIKOM-W167-OWNER-UI-REGRESSIONS-02449-UNSIGNED.exe`
  - ZIP: `CELIKOM-Windows-0.24.49.zip`
  - SHA256 manifest: `SHA256SUMS.txt`
  - EXE SHA256: `f363a23b90a58268d31f2c5a34313f35510645ab34bcf2c9acfcc3521b14a852`
  - ZIP SHA256: `abd7ab026a6dcfa7532f4aa833c7db2c4bf93c81e76c17afa001b941dfa15f0e`
  - GitHub Actions artifact ID: `14242836055`; expires **26 November 2026, 16:06:19 UTC**.
- ZIP contains exactly one root installer, byte-identical to the standalone EXE. Both hashes were independently recalculated after download and matched the manifest.
- Verified Library files: `/CELIKOM/W167/` (installer, ZIP and SHA256 manifest). Use the Library copies for download, not a sandbox or direct Actions artifact link.
- Package is internal and unsigned; no production signing, public feed, deployment or owner acceptance is claimed.

## Owner manual check

1. Press Start with the module requiring refresh: green Yandex connection text appears immediately; no disabled-state copy or idle module-update hint appears during the operation.
2. Let Yandex open and press Next: no `Ожидаем воспроизведения в Яндекс Музыке…` flash; previous title/artist handoff remains stable and no raw Track ID or pending-presence copy appears.
3. When the current replacement is genuinely active, `Играет версия CELIKOM` is green only if exact current-source proof is present. If the owner hears the replacement but the label remains neutral, collect a fresh W54/W55 diagnostic from 0.24.49.0; do not weaken the proof gate.
4. Pause is neutral while the header connection indicator may stay green.
5. Active status-to-Account spacing is compact; disabled/placeholder breathing room remains.
6. No broad VPN/audio retest is required; those paths were accepted in W164 and remain untouched.

## Hard boundaries

Do not start from W166. Do not reset or force-push main. Do not alter audio, VPN, source routing, server, entitlement authority, updater architecture, Yandex files, Android or browser extension. No broad audits, speculative hooks or intermediate packages.
