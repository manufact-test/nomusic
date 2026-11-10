# CELIKOM A1: one APK clone structural/runtime experiment — 11.11.2026

Goal: replace five side-by-side **research** clone splits with one independently signed APK while the publisher-signed original five splits stay intact. This does not create an audio replacement yet and does NOT authorize sideload distribution.

Research branch: feature/android-parallel-clone-single-apk-merge-20261111, based on 80a07d20247c37af64cef98442745fefe0d32685. Safe rollback: backup/android-parallel-clone-main-exit-illegalstate-20261111.

Previous translated Android 11 CI: original app running; 5+5 split original/clone installation PASS; cloned main `EXIT_SELF(0)` before UI; `java.lang.IllegalStateException` in main PID error logs, not proven causal. Approved A1 still requires a *single native player* and original Yandex on owner HONOR unchanged.

New variant uses pinned already downloaded REAndroid APKEditor 1.4.9 merge command to combine ONLY the separate clone's five verified independent-signer split APKs. It performs zipalign, re-signs with SAME throwaway clone research key, checks independent clone package, exact version and no split ID, full original clone DEX/native library byte-by-byte SHA parity, and on isolated Android emulator installs original 5 + merged clone **1**. Native MAIN/Activity/foreground remains a hard FAIL if absent. No credentials, no payment, no Play Protect disable, no fake Yandex signature, no LSPatch signature spoof.

All binaries remain ephemeral in GitHub Actions temporary directory. A successful 5+1 **installation** does not imply native UI, account, audio, single-player source swap or Play Protect ON phone approval. If a real MAIN/UI still fails with merged one-APK, DO NOT repeat guessed packaging fixes or claim release readiness. HONOR 50 read-only preflight exists separately, actual owner install only after independent package, permissions and native UI pass.

Mandatory: once LSPatch sound swap works and owner approves preserved exact backup, proactively remind about independent Stage B injection adapter instead of LSPatch.
