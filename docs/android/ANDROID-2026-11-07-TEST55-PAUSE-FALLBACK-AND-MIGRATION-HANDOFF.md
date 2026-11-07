# CELIKOM Android Test.55 — signed candidate, transfer handoff, 2026-11-07

**State:** owner resumed Android work on the original accepted Test.50 while Hostinger → another platform migration is partly complete. User will finish the migration tomorrow and switch the workflow from GitHub to MCP. Do not automatically deploy or change the new platform. **Test.55 CI completed; phone acceptance not yet performed.**

## Immutable baseline
- **Owner-accepted Test.50 source**: `manufact-test/nomusic` commit `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`, frozen backup branch `backup/android-test50-exact-source-owner-accepted-20261106`. Same etalon source for accepted fade/DSP/cached-seek/lookahead.
- The new candidate branch was created **directly from that SHA**, not Test.51, .52, .53 or the repackaged Test.54:
  `feature/android-0385-test55-audio-pause-fallback-20261107`
- Exact compiled Test.55 source commit `bc359758f1301b9aa2cc638667d733563ae7e1b7`.
- Test.51–53 were **phone-rejected**. Never merge or cherry-pick Test.53's `source_audio_quarantine` (it falsely disabled normally functioning songs).

## Exact evidence / reason for the narrow fix
Combined logs: `CELIKOM-combined-20261107-011335.txt` and `CELIKOM-combined-20261107-152610.txt`; videos `SVID_20261107_011133_1.mp4`, `SVID_20261107_152425_1.mp4`.
- Media3 binder reports `isPlaying=true,playWhenReady=true` throughout visible user UI pauses on RASKOL «Нас не понимают вообще» and «Дым». Pausing original Yandex audio does **not always update this session**. Android's permissionless anonymous `AudioPlaybackCallback` confirms changes from 2 active media players to 1 lasting 1.8–5.8 s on these tracks.
- Across ordinary accepted songs recorded in Test.49–53, equivalent transient changes while the CELIKOM replacement decoder played lasted at most around 0.45 s. Crucially, Test.53 `source_audio_quarantine_started` on healthy «ты» at ~46.216s occurred during a ~0.20s transition and was wrong. These events do **not** establish the identity of a new track.
- Some user seeks are reported late by Yandex. The local cached decoder responds in dozens of milliseconds **after the authoritative position arrives**; do not claim the button-to-position latency has been fixed.
- On RASKOL → «Дым», Media3 may stay in `STATE_BUFFERING=2,playWhenReady=true,isPlaying=false` for ~10s while correctly identifying album `5281614` / track `39949113`. That is **not a pause**. Test.50's `quiet_buffering_snapshot` watchdog forcibly released a still-connected controller after only ~3s, then Yandex rejected reattachments. The Test.55 watchdog no longer releases/reconnects only for quiet buffering, but **does not force Yandex to leave BUFFERING**.
- Independent identity failures come from Yandex album API HTTP `451 REGION_RESTRICTION` or ambiguous album version; never conflate with native audio transport. The identity/catalogue mechanism and the embedded original base APK assets are unchanged from Test.50 in Test.55.

## Exact functional changes in Test.55
1. Added `SourceActivityPauseFallback.java` (no Android permission, no special API). Requires a **previously observed 2→1 media-player change lasting at least 900 ms**, native still saying PLAYING and wanting to play, a currently audible exclusive CELIKOM decoder, stable same track and aged Media3 event. Never interprets a brief player count as new song ID, never disconnects, never commands Yandex.
2. During a confirmed discrepancy it supplies a paused immutable `PlaybackSource` snapshot to existing `ReplacementEngine.pauseSource`; preserves the source position at the onset of audio silence. On the local decoder stopping (media-player count→0) followed by original audio restarting (count→1), supplies a projected resume clock instead of trusting a native clock that continued during the pause. Clears projection on source boundary/seek or native pause/buffering.
3. In `ProbeService.java`, Android's existing `AudioPlaybackCallback` must update internal state even when diagnostic recording is disabled; logging remains gated. Existing source identity, signed-in entitlement, version matching, fade, DSP and seek decoder are preserved.
4. `PlaybackSource.java` gets only a copy constructor for a valid same-key immutable position/playing projection.
5. Removed only the **forced controller release inside the 3s `quiet_buffering_snapshot`** block; retains genuine disconnected-controller reconnect and other original Test.50 behaviors.

## Changed files for tomorrow's migration
`android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/`:
- `SourceActivityPauseFallback.java` (new)
- `ProbeService.java` (existing, narrow integration + buffering retention)
- `PlaybackSource.java` (copy constructor)

Regression/packaging:
- `android/native-companion/addon/TestSourceActivityPauseFallback.java` (new; reproduces HONOR 1.8–5.8s pauses, 0.2–0.45s good-track transition and resuming)
- `android/native-companion/tests/run_engine.py`
- `android/native-companion/tests/run_addon_host.py`
- `android/native-companion/tests/check_test_app_build_contract.py`
- `android/native-companion/build_test_release.py` (only new test class in host suite)
- `android/native-companion/test-app-spec.json`
- `.github/workflows/android-0348-validation.yml`
- `.github/workflows/android-0385-test-app-build.yml`

**Do not cherry-pick Test.51, .52 or .53 logic.** The source branch's exact commit includes these files and can be fetched by GitHub or the next platform's MCP. Need also retain the exact stable test APK signing key / certificate and pinned base input for new-platform build; secrets must **not** be placed in this document.

## Verified result
- CI GitHub Actions run **42408385161 — SUCCESS**, native regression and signed isolated APK build. URL: https://github.com/manufact-test/nomusic/actions/runs/42408385161
- Version `0.3.85-test.55`, versionCode `86141`, package `pro.celikom.nativeprobe.test` (safe forward install over Test.53/54), unchanged stable package `pro.celikom.nativeprobe`.
- Signed APK `CELIKOM-Android-0.3.85-TEST-55-SOURCE-PAUSE-FALLBACK-SIGNED.apk`; SHA-256 **`05f14b7934d77c43f91c53d1c9ca57caf8f7cbd50dd23b07fadf3cbd29ac22b7`**, 8,833,177 bytes. Android APK v3 signature valid; original signing certificate matches. All base assets unchanged; no stable release or OTA.
- **Already saved to ChatGPT Library** under `/CELIKOM/Android/Backups/`:
  - APK: https://chatgpt.com/library?file_id=libfile_146458f63744819191f27ada3e050b03&account_id=personal
  - verification JSON: `libfile_e2d4a83f40f8819182feb0e9fd854cda`
  - build receipt: `libfile_763902b91f0c8191806562237309d863`
- **Not yet confirmed on the user's HONOR 50/Android 13**. CI proves software checks/packaging, not that real user Pause/Seek or «Дым» works. Do not announce full fix.

## Next step
User to test RASKOL Pause and repeated resume, long seeks, RASKOL→«Дым» and normal unrelated tracks. Request one combined diagnostic + short video if failure. Pause fallback must be accepted on device before considering it fixed. If normal songs regress, revert this **one** patch set to frozen Test.50. On completing server migration, verify API origin/auth/entitlement/resolve/stream HTTP Range, TLS, private storage, DB catalogue and signing/build-input availability. No guessed new endpoints or secrets.