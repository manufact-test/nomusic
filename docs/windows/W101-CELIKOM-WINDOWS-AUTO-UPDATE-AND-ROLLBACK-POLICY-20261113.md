# W101 — CELIKOM Windows: единая политика обновлений и отката (2026-11-13)

> **Latest owner decisions are in W102.** W102 supersedes earlier branch/release workflow assumptions and defines the single-production-line rule, 15-minute Yandex monitoring, full task ledger and ordered handoff. Keep the technical updater security and rollback requirements below.

## Зачем этот документ

Владелец зафиксировал обязательное продуктовое требование: пользователь CELIKOM Windows не должен самостоятельно следить за релизами, заходить на сайт и вручную скачивать каждый новый EXE/ZIP. Обновление самого CELIKOM должно доставляться приложением автоматически, безопасно и без прерывания музыки.

Это политика для существующего продукта CELIKOM Windows. Не создавать второй клиент, отдельный параллельный плеер или отдельную «тестовую программу». Новая версия — следующая версия того же приложения, устанавливаемая поверх текущей.

## Точное состояние разработки на момент передачи

- Repository: `manufact-test/nomusic`.
- Active work branch: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
- Branch HEAD после W100 handoff: `39b763d6b94ce4ffb8660765da4eabeb3eeb9b48`.
- Code SHA, на котором собран W100: `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- Exact pre-documentation backup: `backup/windows-w100-handoff-pre-docs-20261113` @ `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- New exact backup before this policy document: `backup/windows-w101-pre-update-policy-20261113` @ `39b763d6b94ce4ffb8660765da4eabeb3eeb9b48`.
- Current GUI version in W100: `0.24.36`; native bridge `0.24.29`; W23 package `0.24.10`.
- Windows CI run `43500415302`: SUCCESS on `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- Hostinger/final-package run `43500415358`: FAILURE. Deploy job stopped at isolated MySQL restore/audit step; gain staging, final installer build and publish were skipped. Do not describe 0.24.36 as delivered. Do not launch a duplicate deploy or mutate the one-shot request until the failure is understood.
- No installation was performed on the owner's PC.
- This documentation change does not change application code, server data, deployment state or release version.

## Что реально реализовано в приложении сейчас

### CELIKOM application updater

Current source: `windows-companion/w15/Celikom.Companion/AppUpdateManager.cs` and `MainWindow.cs`.

Implemented:
- validates a locally selected EXE/ZIP;
- accepts a ZIP containing exactly one root-level CELIKOM installer;
- checks PE ProductName, CompanyName and version;
- rejects same/older versions;
- stages the installer under the user's LocalAppData;
- invokes the existing Inno Setup installer using the same application installation path/AppId, without a manual uninstall;
- uses a one-use, time-limited completion ticket;
- after the new app starts, can refresh the managed Yandex integration if required.

Important limitation:
- This is **not an automatic updater**.
- Current path requires a local EXE/ZIP selected by a person.
- In current MainWindow it is invoked through the staff/diagnostics-only Ctrl+Shift+U shortcut, not exposed as a normal end-user update experience.
- Current internal packages are UNSIGNED. PE metadata and SHA256 alone do not prove publisher authenticity.
- Automatic download, public stable feed, background verification, automatic installation scheduling, and automatic rollback are not yet implemented as a complete user-facing flow.

Do not tell the owner or users that automatic CELIKOM application updates already work.

### Yandex vendor updates — separate mechanism

This is a different system and must remain separate from CELIKOM application releases.

Already implemented:
- hourly official Windows Yandex release discovery via `.github/workflows/windows-yandex-hourly-release-watch.yml`;
- reviewed, data-only compatibility catalog;
- exact Yandex EXE + ASAR version/hash checks and Authenticode publisher validation;
- new unknown vendor versions are reported for review and are not blindly accepted;
- after a build is proven and added to the reviewed catalog, CELIKOM can recognize that exact official Yandex build and reconnect on the user's next Start without requiring a CELIKOM installer update.

Never automatically trust an unknown Yandex version merely because the official updater installed it. Vendor signature/hash identity is necessary but still not sufficient proof of audio behavior.

### Browser extension updates

The browser extension continues to use its own store/distribution update mechanism. Do not merge its updater with the Windows application updater.

## Required product behavior: automatic CELIKOM Windows updates

Implement this inside the existing CELIKOM Windows application and its existing AppId/installation. Do not create a parallel app.

### 1. One official stable update feed

Recommended stable endpoint on the existing official CELIKOM HTTPS origin:

- Manifest: `/CELIKOM/Windows/Updates/stable/latest.json`
- Immutable versioned packages: `/CELIKOM/Windows/Updates/stable/<version>/...`
- The exact host/origin must be confirmed from the existing deployment configuration before implementation; do not invent a second domain.

The stable manifest is data only. It must not contain executable scripts, shell commands, arbitrary DLL paths or code to execute.

Manifest contract should include at least:
- schema/version;
- channel (`stable`);
- semantic application version and monotonic release sequence;
- publication timestamp;
- package URL, exact byte size and SHA256;
- expected Authenticode publisher identity;
- minimum supported application version, if applicable;
- concise release notes;
- optional/mandatory update policy;
- explicit rollback directive, if a rollback is being authorized.

Never overwrite an already published version package. Publish immutable versioned artifacts and update only the signed latest manifest.

### 2. Trust and integrity — release blocker

Before enabling unattended installation for customers:
- sign the Windows installer with a trusted CELIKOM Authenticode code-signing certificate;
- sign the update manifest with a separate release-signing key whose public key is pinned in the application;
- protect private signing keys in a restricted signing environment; never put a private signing key in the repository or ordinary build logs;
- verify manifest signature, HTTPS origin, package size, SHA256, Authenticode chain, publisher identity, ProductName, CompanyName, architecture and version before staging or executing;
- reject unsigned, expired, malformed, replayed, wrong-channel, wrong-publisher, modified or older packages;
- do not treat TLS or a SHA256 value from an unsigned manifest as sufficient authenticity.

Until signing is available and independently verified, automatic installation must remain disabled. Do not silently install today's unsigned internal artifacts.

### 3. Client check and download behavior

Default channel for ordinary users: `stable` only.

The client should:
- check the stable manifest once after startup/network initialization and then periodically (suggested interval: every 6 hours, configurable centrally);
- perform checks/downloads in the background with bounded timeouts and backoff;
- fail quietly while offline and retry later;
- keep update discovery independent of login, account email and paid entitlement, so a user can repair/update the app even while signed out or with an expired subscription;
- never ask users to create accounts, add GitHub secrets, provide emails or visit GitHub Actions;
- download only a newer verified stable release;
- display a small non-blocking notice that an update is ready, with “Установить сейчас” and “Позже”; the user must not need to visit the website;
- install at a safe point: do not stop Yandex or interrupt an active track. If playback is active, defer installation until playback is idle or the next normal application exit/restart;
- allow the user to defer a normal update, but retry the prompt later;
- for a mandatory security/compatibility update, explain the deadline and apply only at a safe stop point, never by abruptly cutting audio.

The app may download while music is playing; it must not replace active binaries, restart Yandex, reset the bridge or touch audio sources during playback.

### 4. In-place upgrade invariants

Every CELIKOM update must remain an upgrade of the same installed application:
- same Inno Setup AppId and install directory;
- no uninstall/reinstall journey for the user;
- no second parallel CELIKOM installation;
- preserve DPAPI-protected login/session data;
- preserve user preferences, autostart choice, diagnostics and local state;
- preserve Yandex original files and vendor installation;
- preserve browser extension files and behavior;
- preserve entitlement checks; updater must never bypass subscription validation for playback;
- do not restart Yandex or resume playback automatically just because CELIKOM updated.

Local data/schema changes must be backward-compatible or explicitly versioned with a proven rollback path.

### 5. Health check and automatic rollback

A successful installer exit is not sufficient.

Before replacing the current version:
- keep the last known-good signed installer/package locally;
- record the exact current version and update transaction;
- verify sufficient disk space and close/stop only CELIKOM-owned processes at the safe point.

After installation:
- start the new CELIKOM version;
- run a bounded health check for process startup, settings/session readability, native bridge startup and update completion;
- mark the new version healthy only after the required checks pass.

If the new version fails to start or fails its health check:
- an updater/helper process independent of the main app must restore the last known-good version;
- preserve DPAPI/session data and all Yandex originals;
- record a concise diagnostic reason;
- do not enter an endless update/rollback loop.

For a remotely discovered bad release:
- stop offering that release in the stable manifest immediately;
- publish a newly signed rollback directive targeting one exact known-good version;
- rollback authorization must explicitly name the bad source version and allowed target version; never permit arbitrary downgrade;
- use a monotonic release sequence so a signed rollback cannot be replayed indefinitely;
- users should receive and apply this rollback through the same updater, without visiting the site.

Keep at least the current and previous known-good signed packages available on the official server. Keep at least one previous package cached locally until the new version is marked healthy.

### 6. Release process and rollout

The owner does not want endless user-facing “TEST versions”. Internal CI/QA is an engineering gate, not a separate customer product.

Release process:
1. Work on the existing CELIKOM codebase and preserve the exact rollback branch.
2. Finish and verify the requested fixes in the current workstream.
3. Build one coherent next version of the same CELIKOM application.
4. Run exact-commit Windows CI, installer/in-place upgrade tests, updater signature tests, failure/rollback tests and audio regressions.
5. The owner checks the delivered next version on his PC before it is exposed to all users.
6. Only after acceptance, publish it as a normal `stable` release and update the signed manifest.
7. All users then discover/download it inside CELIKOM. No manual website download for every release.

A one-time manual bootstrap may be needed to move users from a legacy installed binary that has no automatic updater into the first version containing the updater. Explain this honestly. After that bootstrap, subsequent updates must be automatic. Do not make users repeat the bootstrap for every release.

Do not expose GitHub Actions artifacts, experimental branches, internal QA labels or unsigned packages through the public stable feed.

## Work order for the next lead — do not derail the current Windows fixes

1. Read this document first, then `W100-0.24.36-FINAL-TEST-RELEASE-HANDOFF-20261113.md` and `NEXT-CHAT.md`.
2. Re-fetch the current branch HEAD and run `43500415358`; it is currently recorded as failed at isolated MySQL restore/audit. Inspect exact failing log and actual remote state before retrying. Do not ask the owner for more credentials or secrets.
3. Resume the existing Windows fixes and deliver one coherent next version of the same application. Do not create a second app, do not send interim installers, and do not install anything on the owner's PC.
4. Keep #54 mid-track volume drop, #56 admin gain and #57 403 hiss as separate diagnoses.
5. After the owner has a coherent working version, implement the automatic CELIKOM app updater described above as a dedicated, bounded work block. It is a release requirement before general customer rollout, but do not use it as an excuse to postpone the currently requested audio fixes.
6. Before any automatic updater reaches users, code signing, signed manifest verification, in-place upgrade, failure rollback and no-playback-interruption gates must all pass.

## Owner's explicit operating rules

- The product is the existing original CELIKOM Windows application. Every new release upgrades that same installation.
- A backup branch is a rollback point, not a second product.
- No user should have to watch a website or manually fetch each new version.
- No new account/email/secret should be requested for application updates.
- No arbitrary architecture rewrite, no unnecessary branches and no claims of completion based only on CI.
- Keep the owner-facing status concise: what was fixed, what is verified, what remains unverified, and the single current blocker.
