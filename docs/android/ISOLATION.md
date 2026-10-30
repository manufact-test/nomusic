> **АКТУАЛЬНЫЙ SCOPE (30.10.2026):** только Android `feature/android-unified-preparation-seek-gate` и документы `docs/android/**`; текущая передача [HANDOFF-2026-10-30-UNIFIED-AUDIO.md](HANDOFF-2026-10-30-UNIFIED-AUDIO.md). Signed Android 0.3.54 AUDIOFIX с оригинальным ключом существует; old claims "missing signing key" ниже исторические. Desktop `feature/api-range`/0.4.65, backend, catalogue, CMS and Ad Protection не менять. Ветка `feature/android-0348-audio-ownership-stabilization` — green baseline `8128307d0daf95f3386b85791db5347e3ec56357` (PR #22 draft), не мержить её целиком в desktop.

---

> **СУПЕРСЕДЕД: ЗА ТЕКУЩИМ СТАТУСОМ СМОТРИ** [HANDOFF-2026-10-29-ANDROID-0352.md](HANDOFF-2026-10-29-ANDROID-0352.md). Новое: только Android, desktop 0.4.65 не менять, CI 40942060340 PASS, версия 0.3.52 готова только как НЕПОДПИСАННЫЙ structural smoke, оригинальный приватный ключ подписи отсутствует.

---

> **Обновление 29.10.2026.** Нижеследующее описание desktop 0.4.61 и ранней ветки `feature/android-isolated` историческое; актуальное разделение: desktop **0.4.65** на `feature/api-range` — НЕ МЕНЯТЬ; Android на `feature/android-0348-audio-ownership-stabilization`, PR #22 (DRAFT), issue #20 (OPEN). Сначала читать [ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md](ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md). Сохранённые архивные ветки: `backup/android-0351-last-signed-20261029` (последняя подписанная 0.3.51) и `backup/android-pre-architecture-refactor-20261029` (промежуточный код до переделки). Все будущие изменения только Android+docs/android (и утверждённый Android CI); не изменять/деплоить сервер, desktop, сайт, CMS, общие credentials или продуктивные workflows. Резервные ветки не обновлять.

---

# Android isolation checkpoint — 2026-10-21

Desktop working release: **0.4.61**, commit `3a037e5fd5c1d09cd811dbf12dc80c7a12ed5e2e` on `feature/api-range`. The owner confirmed playback works after the startup timeout correction. The earlier 0.4.60 checkpoint remains historical, not the current working release.

Android work branch: `feature/android-isolated`. This branch deliberately removes every inherited GitHub Actions workflow, including production deployment, catalog SSH, desktop packaging and historical repair jobs. Only the isolation guard is reintroduced. The original desktop branch and its workflows remain unchanged.

The pinned guard permits subsequent changes only under `android/**` and `docs/android/**`. It checks the complete diff, including deletions and both sides of renames. The only permitted workflow must exactly match the definition in the pinned bootstrap commit. It executes its own script from that commit, so editing the working-copy guard does not bypass the check. Guard cases include protected source, root configuration, deployment scripts, deletions, renames and altered workflows.

This is a CI check, not an enforced GitHub branch protection rule or a separate secret store. Do not merge this Android workspace branch wholesale into the desktop branch. Production credentials still exist at repository level; no Android workflow references or uses them. This branch does not build an APK or access the production API.

## Current native source and accepted scope

Exact Android 0.3.22 source has been recovered from the installed APK's embedded ZIP and committed at `a40a27cb29c539f7a795a13fbdf565d810d44494` under `android/native-companion/`. Recompilation gave a byte-identical classes2.dex. Hashes are recorded in `android/native-companion/RECOVERED-0.3.22.json`. Private signing material remains outside Git.

The owner explicitly accepted continuing client-only Android fixes without staging setup, new hosting, migration or repeated manual tests. Do not require a staging environment for these client fixes. Do not modify/deploy shared API, session policy, catalogue, database, storage, desktop or website in this work. Builds and automated tests do not contact production. The installed Android app retains the existing API origin and its independent installation/session; separate folders and branches are code isolation, not a claim that an installed client has no shared service dependency.

Current candidate changes and offline build instructions are in `android/native-companion/README.md`. The design stage is still pending. Calls remain deferred. Deliver one candidate APK after automated checks and ask for one combined physical playback check, rather than another installation for every minor issue.
