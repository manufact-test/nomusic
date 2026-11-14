> **14 NOV 2026 LATEST OWNER NAV13 DIAGNOSTIC RECEIVED — supersedes earlier WAIT instruction.** The owner supplied `CELIKOM-A1-Diagnostics-1794667528891.txt`. It proves the real Passport result entered the original `qY5.if` path but returned `AFTER_TOKEN_REQUEST NO_USERINFO_RESULT`. No native userInfo success/Main/audio. Read **[ANDROID-A1-NAV14-TOKEN-REQUEST-BOUNDARY-20261114.md](ANDROID-A1-NAV14-TOKEN-REQUEST-BOUNDARY-20261114.md)** before work; token failure versus null remains unknown. A narrow read-only observer and static gates were committed in this SAME branch, with exact pre-change backup `backup/android-a1-nav13-owner-token-boundary-before-readonly-fix-20261114` @ `0f4100c`. Latest source/test head `73f2461`, native CI #43607380238 (paired) and #43607320585 (clone-only) require final verification. **DO NOT ask for another OTP, user installation or GitHub button-click; no new owner APK yet.** Stage A NO-GO, Stage B LOCKED. All older WAIT-FOR-TXT instructions below are historical and superseded by this receipt.

# CELIKOM A1 — NAV13 WAITING FOR OWNER DIAGNOSTIC

**Date:** 14 November 2026  
**Purpose:** exact handoff for the next chat. The next assistant must read the current documents and wait for the owner's diagnostic TXT before doing more work.

## 1. Repository and code state

- Repository: `manufact-test/nomusic`.
- Sole Android A1 working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Android source under latest native validation: `cb6f5b6b00fa35b0c66d499e4e795229d198daae`.
- Documentation/dispatch HEAD before this handoff refresh: `376af367c664759039410b68e331a37ce35dfad2`. New documentation-only commits advance the branch; do not mistake them for source changes.
- Pre-handoff documentation backup: `backup/android-a1-nav13-pre-wait-for-owner-diagnostics-docs-20261114` @ `376af367c664759039410b68e331a37ce35dfad2`.
- Read first:
  1. `docs/android/NEXT-CHAT-ANDROID-A1-LEAD-20261113.md`
  2. `docs/android/ANDROID-A1-NAV13-OWNER-REAL-POSTLOGIN-RECEIPT-20261114.md`
  3. This file.

## 2. Latest verified diagnostic build

- Native workflow #43604192249: **SUCCESS** — https://github.com/manufact-test/nomusic/actions/runs/43604192249
- Final verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- Android 13 ARM: publisher-first install; all 16 original splits verified; original stable for 75s before and after clone installation; clone stable for 75s, 25/25 resumed lifecycle observations.
- Real clone Entry Activity created during no-login smoke. FLOW/PIPELINE, token read/decrypt, Android result delivery and onboarding-writer observers registered. Original master key persisted.
- Persistent owner signer SHA-256: `048D76E1C4447FA4F3AC976C45D5A0F8427C087FA665C4FCA88CE5CAA068F9BF`.
- Diagnostic APK SHA-256: `6e62b17aad4b9d7633a22880cceea02d39029cbe22bb663a7b302b5e9a8bc722`; size 71,446,508 bytes.
- GitHub artifact #14117891265; run #43604192249.
- The APK and instruction are saved in Library:
  - `/CELIKOM/CELIKOM-A1-NAV13-Entry-PostLogin-Diagnostic-20261114.apk`
  - `/CELIKOM/NAV13-Инструкция-реального-входа-CELIKOM-A1-20261114.txt`
- This is diagnostic-only, not a release. CI did not perform real Passport login, prove `Success(userInfo)`, post-login Main navigation or audio playback. Stage A = NO-GO; Stage B = LOCKED.

## 3. STOP POINT — owner diagnostic is the next input

The owner will attach `CELIKOM-A1-Diagnostics-....txt` in the next chat.

Until it arrives:
- Read the documents and wait. If the file is not attached yet, say only that you have read the handoff and are waiting.
- Do not ask the owner to repeat installation, login, OTP, or diagnostic capture.
- Do not launch another Actions run, rebuild/export APK, modify source, or speculate about a fix.
- Do not ask the owner to click `Run workflow` or operate GitHub Actions.

When the TXT arrives:
1. Read the actual file, not just its filename or the owner's summary.
2. Determine which events are actually present and where the flow stops: Passport result delivery; token read/decrypt; original `Success(userInfo)`; onboarding/sync; Entry-to-Main navigation; or process exit.
3. Compare the evidence with the read-only observers and exact original DEX contracts already documented in the receipt.
4. State what the TXT proves and what remains unproven. Do not infer a failure stage from absence unless the relevant observer was registered and the diagnostic explicitly supports that inference.
5. Then continue the implementation autonomously, in one coherent block, preserving architecture and creating an exact backup before substantial source changes. Run the existing CI/native gates and update both handoff documents afterward.

Never request or collect passwords, OTPs, access tokens, account contents, or other credentials. The diagnostic is intended to contain bounded event categories only.

## 4. How to work with the owner

- The assistant is the developer/operator and handles GitHub repository work, commits, exact backups, Actions dispatch, job/artifact retrieval and documentation.
- The owner must not manually trigger workflows, press buttons in GitHub Actions, copy commands, or babysit builds. The previous one-time dispatcher already proved that the assistant can launch the existing protected workflow and self-remove the temporary helper.
- Do not leave permanent helper files or modify product workflow semantics merely to avoid a manual click.
- Work in large coherent blocks; no micro-step instructions, no unnecessary "continue?" pauses, and no long reports. Give only meaningful results/blockers and any genuinely required owner-side phone check.
- Keep this single Android A1 working branch and the existing architecture. Do not create another product/player or treat this as a separate test product.
- Before substantial source changes, create a backup branch at the exact current HEAD and record it.
- Never uninstall or clear data for the ordinary Yandex Music app. Keep Windows, backend, production and accepted Test.50 baseline untouched unless explicitly requested.
- Native idle stability is not login or audio acceptance. Keep Stage A NO-GO / Stage B LOCKED until real owner evidence proves the required flow and playback.

## 5. Rollback points

- Pre-dispatch: `backup/android-a1-pre-one-shot-owner-diagnostic-dispatch-20261114` @ `37fd2f806afc8cd1e1739ef5c17d3f1e5381101b`.
- Post-run/pre-docs: `backup/android-a1-nav13-owner-diagnostic-apk-43604192249-20261114` @ `8ab403e5c9d927af158bf606c17cbe387bcd2b46`.
- Before this wait-handoff documentation refresh: `backup/android-a1-nav13-pre-wait-for-owner-diagnostics-docs-20261114` @ `376af367c664759039410b68e331a37ce35dfad2`.

**Current next action: wait for the owner's diagnostic TXT. Nothing else.**
