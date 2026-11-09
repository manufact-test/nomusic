# CELIKOM Android — ARSCLib alternative structural clone gate (09.11.2026)

## Why this gate
The prior exact signed 5-split Apktool 2.12.1 ephemeral trial failed in CI 42662932538. Its diagnostics only reported the heuristic category `APKTOOL_REBUILD_FAILED_ANDROID_FRAMEWORK_MISSING`; the raw aapt2 error was intentionally not surfaced. This does **not** conclusively establish a missing Android framework.

## Independent approach
- REAndroid APKEditor V1.4.9 / ARSCLib (official release pinned to sha256 `a9cd40df818845456be6d696de6110c89edf4b0a0580cb83438ed6b25a366e67`), independent of Apktool's aapt2 resource rebuild.
- Reuse exact pinned publisher-signed #170gpr five-split archive and validation.
- Keep original DEX and native .so byte-identical; change only manifest package/selected authorities/identity declarations; refuse sharedUserId.
- Locally sign ALL five ephemeral outputs with the same throwaway test key; verify metadata, split set, signatures, exact original DEX/native payload hashes.
- No third-party APK artifact, publishing, install, login, credentials, or Play Protect modification. Temporary CI files auto-delete.
- On failure, record stage and truncated sanitized error snippets rather than claim an unverified root cause.

## Hard stop/next gate
Even `ARSC_STRUCTURAL_PASS_NOT_NATIVE_RUNTIME_PROOF` does NOT mean a real parallel Yandex client works: DEX hardcoded package strings, resource package names, auth/deep links, signature checks, Android installer behavior, in-app auth, and decoder integration are NOT validated. Do not ship/install or request owner to remove original. After structural gate assess package-bound/runtime blockers before any owner-side read-only hook test.

New script: `android/native-yandex-hooklab/clone_native_splits_arsclib_ephemeral.py`.
New CI: `.github/workflows/android-native-arsclib-clone-ephemeral.yml`.

Accepted Test.50, installed official Yandex, Windows, extension, server, database and production remain untouched.
