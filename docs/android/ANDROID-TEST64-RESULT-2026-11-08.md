# CELIKOM Android Test.64 — итог проверенного сквозного этапа (2026-11-08)

**Исходная проверенная база:** Test.62, `6cc77df3a9fcc632c36975dc9fb68ffd853c5b36`.
**Экспериментальная ветка:** `feature/android-0385-test64-resolve-priority-media3-evidence-20261108`.
**Точный код подписанной APK:** `e9322f376d57fdb6966d482d2c4c78a20c0bc58a`.
**GitHub Actions:** https://github.com/manufact-test/nomusic/actions/runs/42480130861 — validation + isolated signed APK: SUCCESS.
**APK-artifact:** https://github.com/manufact-test/nomusic/actions/runs/42480130861/artifacts/13617221230 — `CELIKOM-Android-0.3.85-TEST-64-RESOLVE-PRIORITY-SIGNED.apk`. GitHub artifact retention 7 days.
**APK SHA-256:** `d6985bdd0e4e9cb4a4febd96c9ba433119ceaf97a782c162206294215d60d1af`. Signing certificate `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; v3 signature verified (v2 not enabled).
**Stable 0.3.92, Test.50, main, production backend/OTA:** unchanged.

## What actual phone traces prove

Input: owner's HONOR 50 / Android 13 CELIKOM combined 2026-11-08, official Yandex Music 2026.10.3 #170gpr. Session `MediaItem.mediaId` values such as `9`, `69`, `178` are session aliases, NOT Yandex Track IDs. RASKOL 42884423 and «Дым» 39949113 were recovered by Yandex album metadata match, not the official session's explicit ID. The Media3 controller returns an estimate of position and relies on the publisher to supply up-to-date transport events. Some UI actions (notably RASKOL pause/seek) are absent from the external session, and Yandex BUFFERING may remain even though CELIKOM is not itself blocked. Disconnecting a connected session during BUFFERING previously induced SecurityException reconnect loops; Test.62 retains the controller, and Test.64 preserves that.

In the recording the next song may begin resolve/prefetch before the current item has been resolved. In Test.62 `NativeApi.resolve` put both current and next resolve on one serialized `work` executor. This is a concrete blocking path, separate from sound quality.

Approved catalogue automatically fetches from `replacement-catalog`; a later Test.62 run returned HTTP 200 and populated 133 rows. Earlier HTTP 404 was a backend endpoint/caching condition, not a need to embed approved songs in APK. This path is unchanged.

## Implemented code changes

1. `NativeApi.resolve`: **independent current vs speculative lookup network lanes** through new pure-Java `ResolveLaneRouter`. Fresh current resolves never queue behind a speculative lookup already in progress. New speculative requests defer while any current lookup is outstanding. Existing source/account-generation fences still reject stale replies; `access()` synchronizes refresh token rotation across lanes. Speculative `ReplacementEngine.prefetchLookahead` explicitly calls `resolveLookahead`. No bypass of signed URL/entitlement, no cross-account audio reuse.
2. `ProbeService.sample`: current album decision and `replacement.update(current)` now happen ahead of `sampleLookahead`. The similar standalone change in Test.63 was not a proven speed fix; Test.64 combines ordering with an **actual transport scheduling change**.
3. `Media3IdentityInventory`: passive, diagnostics-only snapshot of `MediaItem.mediaId`, `MediaMetadata.extras`, `MediaItem.RequestMetadata.extras/mediaUri scheme`, `MediaItem.localConfiguration` presence/URI scheme, `MediaController.getSessionExtras`, current timeline window and command availability. Bundle keys/types and only explicitly ID-named numeric candidates are logged; never complete URIs, tokens, user extras or unvalidated IDs as ground truth. Current fallback remains strict album/edition matching.
4. Read-only Media3 `onIsPlayingChanged`, `onPlayWhenReadyChanged` and `onPlaybackStateChanged` event journal entries enable testing whether Yandex actually publishes pause/BUFFERING transitions. No new timers, forced Media3 reconnection, root, Accessibility or Notification Listener.
5. Added deterministic `TestResolveLaneRouter` covering current-before-next, independent current lookup during slow prefetch and stale-generation rejection. Included it in the full regression; updated side-by-side Test.64 package and CI validation + signing contract.

## What was reusable from competitors

- **Hazzz895/FckCensor** `src/api/main-api.ts`: first-match priority among track-ID keyed replacement sources. Our server-owned resolve and strict edition policy already implement a safer equivalent; no replacement-source precedence rewrite required.
- **S4YN3X/FkCensor** `assets/inject.js`: flat `trackId -> replacement` registry and scheduled metadata refresh. Our live approved server catalogue already implements the usable refresh principle; don't import its desktop JS player hooks.
- **mrvokintos/YandexMusicMod** `src/mod/features/ym-liberty/ym-liberty.ts`: intercepts internal `getLocalFileDownloadInfo(trackId)`; **not accessible** to an independent Android companion attached to official Yandex Music.
- **gagayhhad-tech/ym-liberty-android** `android_app/assets/www/app.js`: Promise-keyed stream request deduplication, next-track preloading; requires its own browser/WebAudio player. Our existing replacement+version keyed completed-file cache, one lookahead slot, primed decoder and generation leases are compatible principles. New lane separation fixes a specific interference missing from our previous implementation.
- **aeviww/yandex-music-client** `desktop/src/lib/audio.ts`: muted `warmNext` and generation `sourceToken` cancellation; our existing prefetch decoder and owner/generation tokens already provide their acceptable analogue. Do not graft a second output player or change Test.50 audio handoff.

## Evidence, limits, and HONOR acceptance

- Native CI SUCCESS with `PASS: current-before-next resolve, independent lanes, stale candidate fence`; full `run_engine.py`, host tests, Android/D8 compile, packaging contract, original signing certificate check, APK v3 signature verified, distinct test package, no stable OTA.
- **Actual speedup, smooth audio, RASKOL pause/seek, and Dym BUFFERING are NOT confirmed on a device.** No sound fade/decoder or original audio effect adjustments were made; audio glitches cannot be claimed fixed.
- **True Yandex Track ID not proven available** from the public session. Track ID cannot be adopted from a numerical alias alone; inspect new `media3_identity_fields_readonly` on HONOR and corroborate any ID-candidate against authoritative album resolution and multiple song transitions before any production use. Other apps' internal/desktop hooks don't imply public Android access.
- Android `MediaSessionManager.getActiveSessions` outside the permitted controller requires privileged `MEDIA_CONTENT_CONTROL` or Notification Listener; both excluded. Media3 position may extrapolate from the last published session state; an absent source pause/seek event cannot be fabricated reliably by tweaking polls/timers. If the official app doesn't publish it, transparent original-only fallback or explicit user-controlled CELIKOM transport are the realistic noninvasive choices.

**HONOR 50 test:** install alongside stable; leave Test.50 sound baseline installed unchanged if needed. Compare cold first track and 5 rapid Next transitions with Test.62 (same network/VPN setting), then RASKOL 42884423 pause+scrub, «Дым» 39949113 prolonged BUFFERING, approved new song without reinstalling. If any regression in sound, stop Test.64 and use accepted Test.50. Export diagnostics showing `media3_identity_fields_readonly`, `media3_fresh_*callback`, `backend_result` lanes, `source_controller_buffering_retained` and `replacement_lookahead*` after the test. **Phone quality acceptance pending.**

Original full research handoff: https://github.com/manufact-test/nomusic/blob/main/docs/android/ANDROID-RESEARCH-TO-IMPLEMENTATION-HANDOFF-2026-11-08.md
