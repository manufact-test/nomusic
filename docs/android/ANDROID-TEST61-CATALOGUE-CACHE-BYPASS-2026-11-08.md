# 2026-11-08 — CELIKOM Android Test.61: catalogue CDN 404 fixed (owner phone acceptance PENDING)

**Goal:** fix automatic list of approved songs in isolated Android Test, do not release to stable until user verifies.

## Verified live server
- Actual public API: `https://darkred-camel-588676.hostingersite.com`; old no-query `GET /api/v1/replacement-catalog` returned 404 due to CDN negative caching.
- Found active atomic release layout under `/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/current` (symlink to `releases/`). Safely cloned immutable release `0.4.57-78a1072c212fa3c8f1256b3524c353a5883eabcc` into `0.4.57-78a1072c212fa3c8f1256b3524c353a5883eabcc-test60catalog-42472318311`; installed only authenticated metadata-only route + ReplacementCatalogueService; switched current symlink. Old release unchanged and preserved. [deployment run](https://github.com/manufact-test/nomusic/actions/runs/42472318311) code deploy succeeded, but its plain-URL check failed because CDN still cached 404.
- [Read-only live smoke](https://github.com/manufact-test/nomusic/actions/runs/42472780808) **PASS**: active source contains route; real production DB returned **126 approved songs**, complete; public `/api/v1/health` 200; catalogue `?test60=<unique>` 401 without Bearer (as expected). Authenticated HTTP 200 and phone E2E remain to be confirmed. Don't claim user acceptance yet.
- Production rollback: private home folder `~/celikom-private-backups/test60-catalog-42472318311` contains prior/new release pointer. Restore prior release by *atomic symlink* only with an explicit owner-approved rollback; never delete signed APKs or overwrite immutable release.

## Android Test.61
- Android source branch `feature/android-auto-catalogue-sync-20261108`, signed build source SHA `1b949adb8b0246ea3116aff124bd3980e1ab512a`.
- `NativeApi.fetchApprovedCatalogue` now requests `replacement-catalog?refresh=<epochMs>` to bypass CDN stale 404; `Cache-Control: no-store, no-cache, max-age=0` and `Pragma: no-cache`; preserves full 2 MB catalogue JSON safety limit, auth and account-change fencing.
- `0.3.85-test.61 / code86147`, package `pro.celikom.nativeprobe.test`; user-approved Test.50 backup remains immutable; no transport engine modifications in Test.61; RASKOL/«Дым» uncorrected.
- [CI signed APK](https://github.com/manufact-test/nomusic/actions/runs/42472638742): full native PASS + signed isolated test-app PASS, original signing identity retained. Artifact `CELIKOM-Test-0.3.85-test.61-code-86147`. Exact signed APK filename `CELIKOM-Android-0.3.85-TEST-61-CATALOGUE-CACHE-BYPASS-SIGNED.apk`, SHA256 `a5a0fa97140846ffbacd8a74b3d922e4145a700eb7a6f994e8f417055380ebea`, size 8,841,369 bytes. Bundled fallback catalogue was refreshed to **126** approved rows. Note signed APK has v3 matching pinned original and separate Test package, no updater/stable OTA.
- Test signed ZIP uploaded into user's Library as `libfile_edcecf78927881918d306c0485247e2f`; extracted APK in conversation sandbox separately.
- Owner to test on HONOR: install Test.61 over Test.60, sign in, play approved song; ensure diagnostics say `own_catalogue_auto_refresh status=success rows=126` (or newer count), **no 404**; after approving an additional song, after active refresh ~15 min or app reopen, confirm catalogue and replacement without reinstall. Only after this start stable Android 0.3.93 promotion. Do not conflate signed CI success with actual device acceptance.

## Stable release remains untouched
- Owner-verified stable `0.3.92/code93` package `pro.celikom.nativeprobe` unchanged and OTA not published.
- Staging `feature/android-0393-test50-live-catalogue-stable-candidate-20261108` is NOT ready for release; requires verified Test.61 acceptance then selective and guarded promotion.
- Exact immutable owner-approved Test.50 source `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1` remains unchanged.
