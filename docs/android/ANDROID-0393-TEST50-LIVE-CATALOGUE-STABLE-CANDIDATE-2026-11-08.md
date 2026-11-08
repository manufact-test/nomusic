# CELIKOM Android 0.3.93 — Test.50 sound + automatic approved catalogue (STAGING, NOT PUBLISHED)

Date: 2026-11-08. Owner requested the original/stable Android app to gain **both** accepted Test.50 playback and automatic catalogue syncing, keeping RASKOL/«Дым» playback-control fixes in Test channel only.

## Verified facts and exact refs
- Current owner-verified stable source reference: `backup/android-0392-stable-owner-verified-20261106`, commit `8a215d59432d9b6d11ab1971af6189cd230b52f3`. Stable source spec: `0.3.92 / code93`, package `pro.celikom.nativeprobe`. This is distinct from Test.50; do NOT assume Test.50 was already published.
- Frozen Test.50 **remains untouched**: `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`, tree `bbdf43d78e04c6dc4562c5b0541049283f9109b0`, branch `backup/android-test50-exact-source-owner-accepted-20261106`.
- Auto-catalogue Test.60 source: `6951504b3eb04e0f77338295a4258e0a9cdf5e79`, branch `feature/android-auto-catalogue-sync-20261108`. Tests/signed isolated APK were green in CI [42463932575](https://github.com/manufact-test/nomusic/actions/runs/42463932575); that run did **not** compile or sign the stable package.
- **Real HONOR 50 Test.60 diagnostic** `CELIKOM-combined-20261108-122422.txt`, segment at 12:22:17 +03:00: `replacement-catalog` returned HTTP **404** twice (elapsed_ms=238 and 120577), with `own_catalogue_auto_refresh: unavailable_keep_previous`. Thus auto-sync is NOT working with the live server yet, regardless of apparently normal song playback. Must not label as end-to-end accepted.
- RASKOL/«Дым» Pause/Seek and buffering remain unresolved, not part of 0.3.93. Do not port failed Test.51-59 transport mitigations.

## Work performed on isolated candidate
- Dedicated candidate branch `feature/android-0393-test50-live-catalogue-stable-candidate-20261108` starts **strictly at 0.3.92 source**; do not modify 0.3.92 backup, Test.50 exact backup, stable OTA or Hostinger.
- Selectively ported Test.50 audio modules (AudioOwnership, ReplacementEngine, corresponding ProbeService) **from Test.60 whose playback is based on accepted Test.50**, plus automatic catalogue Android changes (AlbumProbe, NativeApi, LiveCatalogueStore), and host regression files (Test48SourceEffectLease, TestLookaheadPrefetchHandoff, TestHybrid, TestLiveCatalogueStore, runners).
- Preserved stable-specific updater code `UpdateCenter` / `UpdateCheckJob` and main package; test-only APK metadata/build tooling are NOT ported. Bumped `release-spec.json` and `AppVersion.java` to **0.3.93 / code94** in this branch only; added catalogue test to stable release builder. Added branch to Android validation CI push filter.
- Included the authorized metadata-only API route and `ReplacementCatalogueService` / backend test in the candidate branch, **not deployed anywhere**.
- A source-level port is NOT yet accepted as a signed or phone-tested stable APK. Validation/build/signing results must be checked before deployment. No public release link must be claimed at this stage.

## Mandatory release gates, in order
1. Finish provider migration and choose the real production origin. Deploy server route `GET /api/v1/replacement-catalog` safely on that origin, without modifying existing audio/auth APIs. Run backend test, verify 401 without bearer, 200 with bearer, approved song appears and revoked/pending do not. Test endpoint with actual production DB schema; don't rely on synthetic SQLite alone.
2. Ensure Android `ApiContract.ORIGIN` points to **same** production host that offers this endpoint. Do not blindly carry over temporary Hostinger credentials or domains during migration.
3. Run native host regression/Android source compile, build **stable package** `pro.celikom.nativeprobe`, `0.3.93/code94`, with pinned ORIGINAL signing certificate `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; verify exact APK contents, updater contract, manifest/permissions, and Test.50 playback code provenance. Signed isolated Test.60 does NOT count.
4. Before OTA publication, verify currently published `stable.json` versionCode and cert, channel and immutable backup. Legacy release workflow presently depends on Hostinger SSH build inputs and publishes to Hostinger: MUST be migrated/verified before triggering. Do NOT publish via workflow_dispatch blindly.
5. Test 1 end-to-end on user's HONOR 50: approve new track -> authenticated API returns it -> Android refreshes without APK reinstall -> proper replacement, with normal playback and regression against Test.50. Keep RASKOL/«Дым» as known issues.
6. Only then publish atomically with verified stable manifest and rollback instructions; update this doc and NEXT-CHAT with **real** build SHA, CI run, SHA256, OTA proof and install result.

## Recovery
- Stable pre-change frozen source: `8a215d59432d9b6d11ab1971af6189cd230b52f3`. Test.50 exact frozen source: `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`. Keep both independently.
- Never overwrite published APK in-place or downgrade versionCode to roll back; use an emergency incremented signed release if rollback necessary.
