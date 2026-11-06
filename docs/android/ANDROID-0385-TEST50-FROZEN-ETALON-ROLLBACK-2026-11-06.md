# CELIKOM Android — Test.50 is the owner-accepted acoustic reference with VERIFIED COMPLETE ROLLBACK
Date: 2026-11-06. This document freezes the owner's accepted acoustic reference. DO NOT claim all artifacts vanished. All code restore operations must use exact SHA, not hand-picked cherry-picks.

## Owner HONOR field feedback
User directly reports Test.50 greatly improved vs Test.49, with very few audible dropouts, and requests full durable restore capability. Combined log `CELIKOM-combined-20261106-235245.txt` parsed 5452 lines / 5449 valid JSON lines (zero parse errors). Three runs: Test.48, .49, .50. Test.50 starts at combined line 3665, runs 126294 ms and ends at combined line 5452 with `run_end.reason=user_stop`. Stop did not corrupt the log; one in-flight future prefetch cancelled because of service stop (expected).
- Test.50: 25 successful `replacement_transition_complete`, 21 `replacement_audio_reused`, 2 `replacement_progressive_cold_start`, 25 `replacement_lookahead_prefetch_start`, 23 `replacement_lookahead_prefetch_ready`.
- Crucially `replacement_lookahead_pending_queued` and `replacement_lookahead_pending_started` each occurred once, demonstrating the actual Test.50 fix executed on HONOR.
- 1 `unexpected_commanded_silence`, 90 ms, not acoustic PCM measurement. No `replacement_failure` events. `replacement_recovery.reason=replacement_completed` once (normal track end).
- 21/22 `source_next_readonly_boundary` were predicted+matched+ready, 1 predicted+matched+downloading. Owner's listening is the only genuine hearing-level validation.
- Test.49 had 7 lookahead starts and 15 cold starts; Test.48 had 25 and 5. Different listening scenarios prevent formal percentages.

## IMMUTABLE REFERENCES and independent permanent assets
- **EXACT SOURCE COMMIT FROM SIGNED APK RECEIPT**: `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`
- **EXACT FULL GIT TREE**: `bbdf43d78e04c6dc4562c5b0541049283f9109b0`
- Dedicated untouched recovery branch: `backup/android-test50-exact-source-owner-accepted-20261106` pointing to SOURCE COMMIT.
- Separate doc branch: `backup/android-test50-documentation-20261106` pointing to `30741346292848b85a4bc6a9c7fe4fc87c6e9b60`.
- Full GITHUB repository source archive export run: https://github.com/manufact-test/nomusic/actions/runs/42292749059 (SUCCESS), exported 1392 tracked paths by `git archive` of exact source SHA, independent sha256 `a1e7a2fa10806081e85147fa9b73aabd94b9e47a70d130a8efa1f9d84ad29930`.
- **PERMANENT COMPLETE BACKUP IN CHATGPT LIBRARY**: https://chatgpt.com/library?file_id=libfile_d97af2a45fb48191a40a384db83f6d8e&account_id=personal — `/CELIKOM/Android/Etalon-Test50/CELIKOM-TEST50-ETALON-FULL-RESTORE-2026-11-06.zip`. Exact ZIP SHA-256 `364c13465a942224eb6d798aaeb36805e6e0ca59661733a5e2691996391b40a4`.
- ZIP includes full repo source ZIP, exact signed Test.50 APK, GitHub verification and build receipt, combined diagnostic, SHA256SUMS, complete README and restore shell script. ZIP inner file hashes and signatures verified by actual offline inspection.
- **Same signed APK**: https://chatgpt.com/library?file_id=libfile_c9438555d1d08191831db3f76ecc9443&account_id=personal
- APK version `0.3.85-test.50 / code86135`, package `pro.celikom.nativeprobe.test`. APK SHA256 `aadedff2051cd40e96641cff1be831aa3a6a79c3938c2b849837b3e880b511d1`, byte size 8,829,081, signer cert SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, verified v3 signature. [source CI + signed packaging SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42287196407).

## RESTORE RULES — never cherry-pick partial code by memory
If user requests to return exactly to this version, take the **signed APK from permanent ZIP** (same bytes, same SHA) for device, and full source at exact commit `5d737d...` for coding. Run `git switch --create restore/celikom-test50 5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1` in a clean Git clone and verify `git rev-parse HEAD^{tree}` equals `bbdf43d78e04c6dc4562c5b0541049283f9109b0`. This selects **entire repository snapshot**, not selected files. The standalone ZIP can restore all files even if the GitHub branch disappears. If newer backend/PC must remain, use the bundle's explicitly scoped Android-only script and verify paths; do not accidentally overwrite unrelated areas. Never force-push stable/main automatically.
- Original CI signing secrets are not included in sources by design; **exact APK is preserved, so restoring installed Test.50 does not require these secrets**.
- Stable production Android 0.3.92/code93, PC extension, backend, Hostinger must remain untouched unless user separately authorizes changes.
- Test.33, Test.48, Test.49 and other old references are no longer the **current** audio reference. No destructive removal of historical objects is required for setting the new baseline; keep backups safe. Test.49 is specifically rejected.
- This is an owner-accepted reference, NOT proof that 100% of transitions are acoustically perfect.
