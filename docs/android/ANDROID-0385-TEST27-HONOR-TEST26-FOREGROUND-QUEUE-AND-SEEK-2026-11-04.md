# CELIKOM Test.27 — foreground audio priority after real HONOR Test.26 diagnostics

Date 2026-11-04. **Test.27 is an experiment, not an accepted audio baseline.** Only owner-selected Test.23 is the immutable rollback. Preserve `backup/android-0385-test23-owner-accepted-20261104` (`251b6facc8739557ff962365da012d502ed3bac8`) and its exact Library APK (`libfile_301d98360e9c8191b8e05594f402d265`, SHA-256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a`). The production `pro.celikom.nativeprobe` / 0.3.85/code86 / Hostinger / stable OTA must never be changed for this task.

## Input and correct diagnostic boundaries

Owner attached `CELIKOM-combined-20261104-164529.txt` (`libfile_a1909a53ca2c8191bc1c70c331cb775f`) and `SVID_20261104_164204_1.mp4` (`libfile_b3e3edfec0848191a9143276b872fccd`). Combined file repeats older Test.24/25 history; **fresh Test.26 run begins at JSONL line 2934**, `2026-11-04T16:42:07+03:00`, and ends roughly at +201s. Do not count older runs again. Environment: owner's HONOR NTH-NX9 / Android 13 / Yandex Music 2026.09.5.

User feedback: first Start is now much faster; several transitions near-instant; others 10–15+ seconds; «Дым» and RASKOL «Нас не понимают вообще» require waiting after finger seeks, with perceived original/replacement cycling and possible pause failures. Video shows Yandex slider jumping far while its playback button remains visible. Video alone cannot prove the exact audio stream or PCM output.

## Evidence: different transport paths, not arbitrary songs

| Observed event | Actual times from fresh Test.26 `elapsed_ms` | Diagnosis |
| --- | --- | --- |
| First Start / 10AGE «Пушка» | cold sparse +224ms; first verified blocks +749ms; first seek ACK +803ms; handover **+1221ms** | Faster startup path is useful; do not revert it. |
| Warm cached song changes | ~284–517ms boundary to joined replacement | Audio-owner handover can work quickly. |
| Track `112217623` | boundary 54780, sparse failure 58607, joined 65924; **11,144ms** | 1.8s sparse deadline falls to complete file, actual download ~6.8s. |
| Track `40371622` | boundary 86832, join 100408; **13,576ms** | Full current file queue wait **7982ms**, network copying only **968ms**. |
| Track `42601865` | boundary 111236, join 133302; **22,066ms** | Full current file queue wait **11,483ms**, actual network transfer 7508ms. |
| «Дым» / `39949113` | boundary 139604, join 156861; **17,257ms** | Full current file queue wait **10,204ms**, transfer 2550ms. |
| RASKOL / `42884423` | boundary 174808, join 176878; **2070ms** | Initial sparse song works. But later seek to 88,837ms at +183364 returned native ACK only +188855, **5510ms callback**, `replacement_stream_seek_data_wait` recorded at +183883. |
| RASKOL second finger seek | +191272 to +191629 native ACK (**392ms**), aligned/joined +191931 | Same song can seek more quickly if required blocks are available; timing is about network/cache availability. |

The single `audioWork` executor served both `downloadLookahead` and `download(current)`. The next-song speculative download occupied the queue for 10–14 seconds, then foreground current full-file fallback **waited behind it**. Separately, 5 out of 8 sparse cold attempts failed after the **hard 1800ms deadline** while 3 optional concurrent Range warmers were still pending. The current decoder's on-demand sparse seek can similarly compete with speculative full-file networking. These are concrete verified transport design defects; no evidence supports changing the accepted seek/ACK/owner algorithm or requesting more Android permissions.

## Test.27 combined changes

1. **Separate foreground and speculative HTTP lanes.** `NativeApi.audioWork` handles current downloads; new `lookaheadAudioWork` handles only speculative next. A queued slow lookahead can no longer block the current transfer.
2. **Cooperative foreground network priority with verified byte retention.** Explicit foreground-demand counter spans cold sparse initialization, current full downloads, and *real missing-block* decoder reads during playback/seek. `AudioTransfer.copy` supports a separate yield flag for lookahead; watchdog closes its socket under foreground demand; partial downloaded bytes remain private, and it resumes with HTTP `Range` + strong `If-Range` ETag. Account/track cancellation is still terminal and deletes partial data, never adopts it as a complete cache file.
3. **Do not equate an optional slow Range with unsupported sparse playback.** After validating block zero and authoritative size/strong ETag, optional metadata-tail/next-prefix/source-position Range warming waits **at most 900ms**, then can finish in the background. An optional slow network response no longer triggers whole-file fallback solely because it missed the startup budget. All decoder reads remain byte-validated; a rejection/changed ETag remains fatal. Initial total sparse deadline 4500ms protects against indefinitely slow authoritative prefix. This is a deliberately conservative change; exact phone startup requires field verification.
4. **Do not alter `ReplacementEngine.seek()/completeSeek()`**, pause arbitrator, AudioOwnership's single decoder and restore-to-original gates, `Media3SourceRouter`, or trusted session. No extra Media3 controller, permissions, OTA, stable app changes.
5. Distinct log events `replacement_stream_cold_warm_pending`, `replacement_stream_decoder_demand_begin/end`, and lookahead `replacement_download_retry.reasonCode=foreground_yield` show whether the priority path actually runs on HONOR.

## Automated verification requirements and limitations

- `TestAudioTransfer` checks that yield retains exact strong-ETag bytes, resumes via valid Range and still cancels stale auth/track transfer promptly.
- `TestBufferedAudio` checks an indefinitely stalled *optional* hint cannot delay publication of validated sparse prefix and cannot prevent a different foreground decoder Range read. Strict ETag, random seeks and full-cache byte equality remain tested.
- Full `tests/run_engine.py`, golden 0.3.85 seek/ACK, pause/Next/source buffer/identity/account/route, `check_audio_architecture.py`, `check_test_app_build_contract.py`, Android API36/D8 signed-build verification in CI. **The host runtime does not include SDK36**; do not claim Android compilation passed until the GitHub CI is green.
- Field metrics: separate `queueWaitMs` current vs lookahead; `replacement_progressive_cold_fallback` count; boundary-to-join for truly completed songs (not abandoned rapid skips); distribution of RASKOL finger seek callback times; pause state after late sparse seek; any source reactivation or loss of replacement. This does **not** assert physical Android audio success before owner tests.

## Exact packaging and rollback

- Experiment branch `feature/android-0385-test27-foreground-priority-20261104` advanced from last Test.26 documented tree, **not the Test.23 backup**. All Test.23 historical source and binary still separately frozen. Test.27 implements follow-up fixes on Test.26 because user observed its faster Start.
- Test package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, version `0.3.85-test.27`, versionCode `86112`, original v3 signing certificate expected `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- **Exact signed-source SHA:** `829a8303095faa54f82959f8e7daecfee40e75dd` (not a later documentation commit). GitHub Actions [run 41843613245](https://github.com/manufact-test/nomusic/actions/runs/41843613245) **SUCCESS**, including Android API36, D8, full native suite, packaging, signing and post-build verification. Original signed artifact `13330660723` is secondary with seven-day retention; ZIP SHA256 `f8c92217c93541870dd6f90d2a0d73fad108797a40f9b1af420eb25d516955ca`.
- **Permanent direct signed APK:** [CELIKOM Test.27 in ChatGPT Library](https://chatgpt.com/library?file_id=libfile_550756e0a96081919ad6408b11dc0d41&account_id=personal), `8800409` bytes, SHA-256 `b31da656b82512502aedaa307f3fa33be2e3387196dd69c9179084286f4f195a`. Verified v3 original signer `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, expected package/code, original assets unmodified, no updater, no `REQUEST_INSTALL_PACKAGES`. Verification JSON and immutable build receipt retained in GitHub Actions artifact and local diagnostics archive.
- **CI is not acoustic proof:** `physical_phone_playback_verified=false`, `acoustic_acceptance=false` in receipt. Owner needs one combined HONOR trial before Test.27 could supersede Test.23. The user has not accepted Test.27 yet; do **not** create or re-point the accepted backup.
- Installation updates only isolated CELIKOM Test (versionCode higher than Test.26). For restoring original owner-selected Test.23, Android does not install older 86108 over newer 86112 normally; uninstall **only test package** or build an explicitly labeled higher-versionCode repackaging of exact frozen Test.23 audio source, original signer, preserving test data. Never mislabel that repackaged build as byte-identical original.
