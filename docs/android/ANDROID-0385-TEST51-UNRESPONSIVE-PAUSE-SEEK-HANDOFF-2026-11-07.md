# CELIKOM Android — handoff 07.11.2026: unresponsive pause / seek on certain Yandex source items

## OWNER OBSERVATION — CURRENT PRIORITY (NOT AN ACOUSTIC JOIN TASK)

Owner accepted **0.3.85-test.50** as the best Android replacement join / song transition to date (very few dropouts). It is the **golden acoustic version** with verified full restoration; leave it intact.

Different, serious, repeatable **control-response defect**: for certain Yandex Music tracks, notably **«Дым»** and a track by **RASKOL** (in earlier project diagnostics identified as **RASKOL — «Нас не понимают вообще»**, catalogue track ID **42884423**; confirm the album/source identity before assuming the user's new specimen is exactly that edition), CELIKOM replacement **plays**, but when the user drags the Yandex timeline forward the transport can appear unresponsive for ~30 seconds before jumping to the requested time; **Pause** can appear nonfunctional. Owner has found comparable versions of these tracks in another album and roughly a dozen further affected tracks. These are **not just two hard-coded titles** and must not be fixed with per-track exceptions. The owner will describe a separate other problem later; **do not invent it**.

Reproduction constraints:
- Official Yandex Music app (not a modified clone, independent player or website), HONOR 50 NTH-NX9, Android 13, Yandex 2026.09.5 #167.1gpr in the last combined log.
- Distinguish source playback from replacement: source Yandex Media3 published state, progress UI, native CELIKOM player, buffer reads, and exclusive audio ownership may diverge.
- Prior real investigation from Test.31: Yandex UI near ~2:11 while corresponding public Media3 source position remained ~0:50. Native cached seek callbacks observed later were fast; therefore **the time between UI action and public source-position publication was not measured and must not be assumed zero**.
- Test.32 diagnosis: RASKOL «Нас не понимают вообще» had two later cache seek ACKs (62 ms / 51 ms) once the changed public position became visible. This **does not disprove** the user's 30s delay from touching Yandex UI. «Дым» absent in that particular run. Sources: `ANDROID-0385-NEXT-ARCHITECTURE-GITHUB-RESEARCH-2026-11-04.md`, `ANDROID-0385-TEST33-HONOR-LONGBROWSE-SEEK-REJOIN-2026-11-04.md`.
- No current diagnostic of these exact songs in Test.50 is proven. Do not claim specific root cause, and do not retune arbitrary 30/70/160 ms fade thresholds.

## GOLDEN, BITWISE RECOVERABLE — NON-NEGOTIABLE

- Exact golden APK source commit **5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1**, git tree **bbdf43d78e04c6dc4562c5b0541049283f9109b0**. Git backup branch `backup/android-test50-exact-source-owner-accepted-20261106`. It is not enough to call any later branch “Test.50”; restore **all tracked sources at exact SHA**.
- Owner-confirmed signed Test.50 APK: package `pro.celikom.nativeprobe.test`, `0.3.85-test.50/code 86135`, SHA-256 `aadedff2051cd40e96641cff1be831aa3a6a79c3938c2b849837b3e880b511d1`, cert SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Library: https://chatgpt.com/library?file_id=libfile_c9438555d1d08191831db3f76ecc9443&account_id=personal .
- **Independent complete restore kit**: https://chatgpt.com/library?file_id=libfile_d97af2a45fb48191a40a384db83f6d8e&account_id=personal — full source archive (1,392 tracked files), exact signed APK, SHA receipts, tests, diagnostics, restore script. Backup source archive GitHub Actions: https://github.com/manufact-test/nomusic/actions/runs/42292749059 . Read `ANDROID-0385-TEST50-FROZEN-ETALON-ROLLBACK-2026-11-06.md` before touching code.
- Test.50 owner diagnostic `CELIKOM-combined-20261106-235245.txt`: run ends `run_end.reason=user_stop`, 25 joined replacements, 21 cached reuses, only 2 cold starts, 25 lookahead starts, deferred-next mechanism executed; no `replacement_failure` in last run. Log is historical evidence **not** a reproduction of these specific source-track control failures.
- New investigation branch **feature/android-0385-test51-transport-controls-investigation-20261107** derives from Test.50 source and has only documentation changes to start. No experimental APK exists yet. All code changes must remain isolated there.
- Separate stable Android **0.3.92/code93** package `pro.celikom.nativeprobe` owner-confirmed Play Protect install; frozen backup `backup/android-0392-stable-owner-verified-20261106`. PC extension, backend, hosting, stable updater, account code and all existing backups **must remain unchanged**. Signing keys are private; do not copy/expose.
- Google Play Protect runbook `ANDROID-0392-PLAY-PROTECT-RUNBOOK-2026-11-06.md`: only Test app should be iterated, do not change Android installer or invoke bypass, Play Protect warnings should be respected.

## NEXT ENGINEERING TASK — SOLVE CONTROLS WITHOUT DISTURBING AUDIO

1. **Reconstruct symptom and state boundaries** from previous «Дым» / RASKOL diagnostics and current code. Separate: actual UI touch (unobservable directly from standalone app), Yandex MediaSession/Media3 position publication, CELIKOM observation, decoder seek request/ACK, audible paused/playing command. Don't pretend player event callback equates to touch time. Compare CELIKOM OFF / ON if and only if evidence can isolate which side is failing, with **one focused device test** rather than repetitive rounds.
2. Audit source-facing `ProbeService.java` + event/source sampling, `ReplacementEngine.java` (including `sourceBoundary`, `update`, `seek`, `completeSeek`, `bufferSource`, `sourcePaused` if available), `AudioOwnership.java`, `BufferedAudio.java`, and any Yandex MediaSession source controller.
3. Inspect album/edition identity for each affected variant; if same title exists in multiple albums, confirm source alias/album ID/track ID/duration rather than conflating two editions. Check whether source UI hangs independent of CELIKOM, whether source still truly playing while user presses Pause, whether Media3 suppression/buffering hides the control event, and whether CELIKOM's replacement audio continues despite Yandex pausing.
4. Fix a **causally demonstrated state/command issue**, not generic smoothing, timers or short fade tweaks. Priority: Pause must immediately mute/pause our replacement when reliable source Pause is visible; seeking must not keep rendering stale replacement for many seconds. Original remains audible when replacement isn't ready; never stop/pause Yandex from a speculative request. Protect against stale seeks, account/session/track mismatches and overlapping ownership.
5. Add deterministic regression covering these specific stalled paths and tests for normal same-item seek, Pause→Resume, rapid seek, Next/shuffle, audio effect lease retention, Test.50 lookahead/deferred-next, original-fallback, Play Protect test isolation. Keep frozen `tests/check_0385_seek_baseline.py` hashes unless owner explicitly approves a targeted seek API change.
6. One coherent Test candidate, **only after complete host suite and CI**, separate package, signed with original cert and saved to Library; compare on HONOR with **both** RASKOL and «Дым» (including different-album variants) and a few known-good controls. No repeated micro-APKs or enormous millisecond reports. If cause genuinely cannot be demonstrated, report blocker and evidence instead of speculative code churn.

## WHAT NOT TO DO

- **DO NOT change** Test.50 source or backup branch, accepted transition/fade/decoder owner/source session effect/preload, stable Android, PC, Yandex APK, Hostinger, server or release channels.
- Do not delete historical Test.33/Test.48/Test.49 backups or pretend backup branches are GitHub branch-protected; archived refs can remain but are no longer golden.
- Do not ask for root, Accessibility, Notification Listener, patched Yandex APK, LSPosed or new broad permissions.
- Do not promise instant UI response when the standalone app has no UI-touch event API. First establish scope and safe engineering path; don't hide that uncertainty.
- No claim the second as-yet-undescribed user issue is already known.
