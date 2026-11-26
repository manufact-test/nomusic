> Extension update26 Nov: **0.4.86 owner candidate** fixes confirmed85 paused/background bridge teardown loops and inappropriate intro mute on mid-song resume.400 local tests + manifest/security pass; actual listening pending.85 stays rollback/test reference, no public promotion. Read `docs/handoff/CELIKOM-EXTENSION-086-BACKGROUND-PAUSE-20261126.md`. No server/Android/Windows changes.

> Latest extension candidate: **0.4.85**, based on the recovered FINAL **0.4.78** (not 73). Starts the authorized selected-track resolve during native loading; guard/player/sync remain at 78. Restores omitted support/upload/My Wave features; retains Floki delivery/access fixes. Local 392 tests, manifest and security gate pass. Owner listening pending; no public promotion. See `docs/handoff/CELIKOM-EXTENSION-085-EARLY-RESOLVE-20261125.md`. 78 Floki control remains rollback. No Android/Windows/server changes.

# 25 November2026 — owner baseline correction:0.4.78

Read [verified78 recovery](CELIKOM-EXTENSION-078-BASELINE-CORRECTION-20261125.md). Earlier73/79 baseline-control instructions below are superseded. Final pre-migration client78 includes the77My Wave fix absent from migration main.73 retest canceled; exact78+Floki-origin control recovered,all packaged runtime bytes match original CI.84 remains held;no customer publication or backend/Android/Windows changes. Main runtime restoration is still pending matched78 owner control.

## 2026-11-25 — Extension 0.4.81 VPN candidate; owner retest pending

Latest: [VPN recovery checkpoint](EXTENSION-0481-VPN-RECOVERY-2026-11-25.md).
Source4cc7814454111f89eb5fe779e5093e6ab584a71d; ZIP2,491,245 bytes;
SHA-2569ddf20fef3c597eb8e91af7c51a4938fde85df792923473c934fe53e258b2380.
381 extension tests/isolated build pass. ZIP delivered privately in the conversation;
website promotion and full CI did not start on GitHub (not passed). Site0.4.80 retained.
No server/DB/paid feature or Android/Windows changes in this candidate.

## 2026-11-25 — Extension 0.4.80 ready for owner retest

Latest: [intro/CORS checkpoint](EXTENSION-0480-OWNER-REPORT-2026-11-25.md).
Source6c1b3491f790e4160464f75af722d64bf8521bc5. Owner ZIP:
https://celikom.com/downloads/extension/celikom-extension-0.4.80.zip
SHA-256 e7304c49db0fdc2c11e5eeb4f1428bda796ddf44aca2729fa2d01520cf1481c0.
368 extension tests/full CI and corrected live rollout PASS. Original fragment during intro addressed with early preparation and a bounded hold; real listening/VPN acceptance pending. Deployment500 incident caused by source mode was repaired and recorded in the checkpoint. No playback architecture or Android/Windows changes.

# CELIKOM extension — FlokiNET acceptance checkpoint, 2026-11-25

## Current owner candidate
- Version **0.4.79**; source commit **0e7d22025ff6f968478b30e61444d168c1c16830** on main.
- ZIP **celikom-extension-0.4.79.zip**, **2,490,404 bytes**.
- SHA-256 **585f996e24040ff0d190d23eb95d8270eecc86909a435946fab24e17ca98d1af**.
- Owner URL https://celikom.com/downloads/extension/celikom-extension-0.4.79.zip ; retain existing whole-site Basic gate. This is an owner acceptance package, not a public release.
- Playback remains from the handed-off current main **0.4.73** (89726d1f5af42f4f97e1597e89499d9ee17e29db), with only its version string changed. CORRECTION:0.4.77/78 were delivered later on their feature branch and MUST be accounted for; the former main-only baseline selection was incomplete. Rejected native-engine experiments remain excluded.
- Keep original 0.4.73 ZIP unchanged, SHA 968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb, for rollback.

## Confirmed migration issues fixed
- Unconfigured extension builds previously had an empty API target. Default/empty build configuration now selects https://api.celikom.com; explicit hostingersite.com targets are rejected. Explicit loopback/HTTPS fixtures remain supported.
- Extension artifact workflow now uses the new API for supported refs, validates manifest/security, and independently checks main origin and exact host permissions before private spooling.
- Old hostinger-extension-private workflow is retired to an explicit failing notice; it cannot produce another legacy-target package from current main.
- Start used to collapse entitlement/session/transport errors into a generic “no connection”. A bounded public-code allowlist now distinguishes sign-in, account/access denial and transport failure. Unknown details never reach UI. This changes messages, not authentication authority, retry policy or playback.

## Evidence
- Baseline rebuilt locally from exact main files: 360/360 extension tests; original 0.4.73 ZIP byte-identical to handed-off digest.
- Candidate locally and isolated Floki runner: **363/363 extension tests**, manifest/security PASS; **4/4 spool tests**. Independent builds produced identical ZIP SHA/size.
- Extension artifact run https://github.com/manufact-test/nomusic/actions/runs/45612204613 SUCCESS; private receipt sha/run/attempt matched the source commit.
- Full CI https://github.com/manufact-test/nomusic/actions/runs/45612205528 SUCCESS, including real PHP/MySQL HTTP checks and native Chromium HTMLAudioElement decoding, seeking and playing signed Range audio. These synthetic checks do not prove the owner’s real Yandex playback session.
- Protected live read-only audit https://github.com/manufact-test/nomusic/actions/runs/45610927530 SUCCESS: health/config200, anonymous auth/me and entitlement401, API config/manifest in existing 0.4.73 correct.
- Live authorized API probe https://github.com/manufact-test/nomusic/actions/runs/45611263231 SUCCESS: auth/me, entitlement, Start, resolve and same-origin signed audio206 at two offsets; pre-existing owner trial unchanged. One separate five-minute probe session was created then removed; its signed URL was subsequently denied. No existing sessions, account, promos, songs, payments or feature flags changed.
- Owner’s previously installed ZIP/origin and exact error cause remain **unconfirmed**. Do not assert Hostinger was the cause without installed diagnostics.

## Release boundary and updating
- Runner spool /srv/celikom/ci-runner/runner/celikom-build-spool/ is untrusted data, never executed as root or served by nginx.
- Root promotion validates exact known SHA/size/source receipt, bounded regular files without symlinks, safe ZIP entries, API origin and permissions. Immutable root-owned private and owner-download copies; add exact nginx route under the existing Basic gate. Keep 0.4.73 route.
- No production application/DB/config changes, no paid features, no Android/Windows changes. Hostinger remains frozen and retained for rollback. Forgejo is a one-way mirror only.
- ZIP/unpacked updating is manual: replace contents of the same extension directory; reload CELIKOM on chrome://extensions or brave://extensions, then reload Yandex Music. Do not remove the extension merely to update. Reauthenticate the existing account if its old session is rejected.
- Chrome Reload does not download ZIP updates. Store/enterprise distribution and stable extension identity require a separate agreed release process; no fake update_url added. Official documentation: https://developer.chrome.com/docs/extensions/how-to/distribute .
- Next: owner installs this candidate and checks Start, pause/seek, track switches and approval of a currently playing song. Analyze support JSON if any failure. Do not call actual Yandex playback accepted before owner confirmation.

## Protected promotion completed
- https://github.com/manufact-test/nomusic/actions/runs/45613004378 SUCCESS: independently validated spool, immutable private and owner copies, root-owned nginx route with existing Basic protection and method restrictions, nginx -t and reload PASS. Anonymous old/new download URLs401; API health/config200 after reload. Old download preserved. Owner-authenticated browser download and actual Yandex playback still await manual acceptance.
- Earlier promotion attempt 45612835407 safely stopped before nginx modification because a simple location regex did not handle nested method restrictions. Corrected with balanced block extraction; reused byte-identical immutable copies. No relaxation of gates.
- Administrative request reset to inert no-op after completion; persistent authorized maintenance access remains unchanged.
