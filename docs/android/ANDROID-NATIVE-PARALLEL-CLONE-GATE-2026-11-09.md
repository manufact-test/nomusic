# CELIKOM Android — parallel test clone without uninstalling Yandex (2026-11-09)

OWNER DECISION: On the primary HONOR 50, never uninstall, update, modify, clear data or downloads of official Yandex Music. No Play Protect disable, root or spoofing.

## Feasibility gate (NOT an installable APK yet)

- The currently installed official app uses package ru.yandex.music and the original publisher signature. An LSPatch-signed same-package bundle conflicts with it. Different Android user/work profile alone does not change the package signing identity.
- A possible parallel lab client needs a **different** Android package ID, for example pro.celikom.lab.yandexclone, and a visible test label. This is a research hypothesis, not a proven way to run Yandex. Merely changing the icon/label is insufficient.
- Offline preflight must check all five split APKs have the new package ID, compatible split metadata and one lab signing cert. Inspect AndroidManifest provider authorities, explicit intents, app-links, permissions, DEX self-package references, and login flow. Repackaging may break OAuth, vendor integrity checks or Play Protect; do not bypass them.
- Existing libxposed module is scope- and version-locked to ru.yandex.music (HookSpec, NativeHookEntry process gate, META-INF/xposed/scope.list). A clone requires a separate explicitly clone-scoped experimental variant; never activate it inside the real official app.
- No compiled clone, no direct device run, no native FileInfo runtime proof, and no audio source replacement exists yet. Do not offer the current same-package APK to the owner.
- Never stage/provide proprietary repackaged Yandex as public releases or CI artifacts. Phone remains untouched until a verified non-overwriting test path is established.

## Plan

1. Study manifest, provider authorities and hardcoded package/self-identity dependencies in exact publisher-verified #170gpr; classify which are safe to adapt to a different package and which prevent login.
2. If feasible, build an isolated **static-only** clone package audit and exact clone-only module configuration, with synthetic tests proving no scope for ru.yandex.music.
3. Only if offline inspection passes and owner agrees to install a parallel application: check signed lab bundle identities and Android installer behaviour without any uninstall/replace commands.
4. If clone is incompatible with Yandex authentication or security, stop. Use a separate, CELIKOM-owned host APK to investigate LSPatch native ARM loader as a partial diagnosis, without modifying official Yandex.

Gate status: NO-GO pending isolated package-ID compatibility proof. The original app stays installed and usable.
