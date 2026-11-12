# CELIKOM Android A1 — AppMetrica native ARM13 init-state observer, 2026-11-12

- New branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112` from exact lab-success source `5891ee655061d2049d1e0b9fa7a83927f3b563d2`.
- Immutable pretrial backup: `backup/android-a1-metrica-init-state-observer-pretrial-20261112`.
- Previous pair of green ARM13 runs used one **LAB ONLY** suppressed Android fatal exception, **not** releasable.
- This diagnostic patch uses prior known read-only activation hooks and classifies legacy/modern AppMetrica calls, activation return/throw, context namespace, SDK/context classloader match and execution phase relative to Android Application.onCreate. All outputs finite and MAIN-PID scoped. **No fatal suppression.**
- CI compiles the scoped observer privately on its ARM host and deletes all APK/key/test assets; no binary artifacts uploaded.
- Acceptance unchanged: original real ARM13 native 75s/25, independent ONE-APK clone co-installed side by side native 75s/25 **with no suppression**. Until that passes: Stage A NO-GO / B LOCKED. No real account, audio or playback controls proven.
- Test.50 and frozen main A1 untouched. No raw vendor messages, tokens, secrets, users' accounts, or third-party binaries exposed.
