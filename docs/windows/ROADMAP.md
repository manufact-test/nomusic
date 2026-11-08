# CELIKOM Windows Companion — delivery plan, responsibilities and test gates


> **W13 STOP DECISION (2026-11-08):** [official-client integration feasibility](W13-OFFICIAL-CLIENT-INTEGRATION-DECISION-20261108.md) is **NO-GO/BLOCKED** for the owner's unchanged Yandex Music 5.126.1.0. Previous W0–W12 standalone test success does not grant a production attachment seam. All phases and acceptance items below are **conditional planning only**, not authorized executable work. No W14 laboratory work unless a genuinely new supported integration API or separately approved revised product constraints appear. Keep existing browser extension unchanged; do not ship a second audio player.


Status: **planning only**, 2026-11-08. No app, installer, modified Yandex binary or backend changes exist.

## Priorities and go/no-go gates

| Gate | Required outcome | Allowed writes | Stop condition |
|---|---|---|---|
| W0 — compatibility baseline | User-installed official Yandex Music version/path/OS; clean launch, native seeking, app update behavior; consent/licensing review; current CELIKOM backend audit. | `docs/windows/**` only | No verifiable supported Windows install or legal/technical viability. |
| W1 — isolated source-substitution feasibility | Proof on ONE test track/approved CELIKOM asset with exact ID, initial playback, pause/seek/next, expired URL, original fallback; compare PulseSync SDK vs narrow own bridge. | Experimental branch under `windows-companion/**` only, **after explicit owner go-ahead** | Needs unsafe unsandboxed changes, unknown hashes, Yandex login extraction, fake media controls or no reliable rollback. |
| W2 — native shell/UI | Compact tray app, login/refresh, status, enable/disable, current track, settings; owner design review. | Windows branch only | Source interception not proven yet, cannot call this production-ready. |
| W3 — real account/catalog | Reuse live auth and signed Range API with correct cache/TTL; no backend schema change unless separately agreed. | Windows branch only | Revokes browser/mobile sessions, leaks access URLs or bypasses entitlement. |
| W4 — lifecycle stability | Start/Stop/Original, cancellation, Yandex update/version gate, crash recovery, per-app quit, rollback/uninstall. | Windows branch only | Any failed rollback damages official client. |
| W5 — release readiness | Signed Windows installer, Defender/SmartScreen smoke, Win10/11, update/rollback, threat review, owner real-device acceptance. | Only after release approval | Never silently publish, market or auto-update unknown versions. |

## Phase details

### Phase 0 — read-only reconnaissance (first development chat)
- Confirm exact official Yandex Windows desktop version; setup location may differ from FkCensor's default `%LOCALAPPDATA%/Programs/YandexMusic`.
- Enumerate installed executable, Electron/ASAR presence, package entrypoints, running processes and update mechanism **without writing to installation**.
- Note Yandex terms and likely integrity checks; do not disable security/Defender or bypass app signing as a design default.
- Observe exact Track ID and native player file-info response shape on read-only instrumented copies/approved dev tools, no credentials in artifacts.
- Map current live `/api/v1` auth, resolve and audio contracts. Compare code against latest server branch without modifying it.
- Record which compatibility technique works, which fails and why. **First deliverable = feasibility verdict, not a speculative executable.**

### Phase 1 — source-replacement experiment (no shared edits)
- Build a **single** isolated integration adapter PoC with explicit feature flag OFF by default and test against one known approved mapping.
- Strict states: original on fail; no overlapping own playback; track change cancels old promises; only exact Track ID. Session tokens stay inside Windows companion; no browser/Android session reuse.
- Verify native Play/Pause/Seek/Next, long track, duplicate album variants, no mapping, no entitlement, network loss and signed URL expiry. Include 206 Range and Yandex codec behavior.
- Demonstrate clean uninstall and byte-checked restore from backup if patch strategy chosen. If using PulseSync test install, clearly expose dependency and commercial compatibility unknowns.
- Only if Stage 1 succeeds decide final bridge route; rejected approach remains separate in research notes.

### Phase 2 — packaged companion UI
- Implement approved [PRODUCT-DESIGN.md](PRODUCT-DESIGN.md) and [mockup.html](mockup.html) as a Tauri 2 / TypeScript prototype (or alternative framework after written decision).
- Wire tray, localized status + settings, login/session and exact track identity; Yandex UI/transport stays untouched.
- UX tests must compare text, actions, key navigation, accessibility and DPI; avoid unneeded graphic changes.

### Phase 3 — full service flows and resiliency
- Account, trial/entitlement, server catalog, upload/request/status, update; rewards shown from server only.
- Crash/stop/OS sleep/resume/VPN flip/Wi-Fi restart/Yandex restart/update; no repeated activation or duplicate file downloads.
- Security/telemetry redaction, keychain credential handling, one-session logout. No surprise server migrations.
- Prefer a single end-to-end QA path to endless timing tweaks.

### Phase 4 — release and ownership
- Installer provenance and signing, release notes and consent screens, update distribution, official-app compatibility table, rollback playbook, support diagnostics.
- Real Windows desktop owner acceptance on clean and previously installed Yandex clients.
- User-facing claim `Windows supported` only after all acceptance gates and explicit approval.

## Acceptance checklist (mandatory real Windows)

- [ ] Clean official Windows Yandex opens and plays before CELIKOM installed.
- [ ] CELIKOM detects install/version, uninstalled/running/stopped/updated states.
- [ ] One exact approved track plays alternate **through original Yandex decoder**, with Play/Pause/Seek/Next unchanged.
- [ ] Unmapped track continues original without stalling; no lookup by title alone.
- [ ] Expired signed URL, 401/403, 404, 206/416, 500, offline, VPN loss -> original, no infinite retry.
- [ ] Stop and Original yield native original immediately or a documented safe next-track boundary (never claim impossible seamlessness).
- [ ] Yandex upgrade invalidates incompatible integration safely and never corrupts installed app.
- [ ] Installer and uninstall restore original bytes / settings; backup hashes recorded and checked.
- [ ] Windows lock/sleep/resume, tray close/exit, system media keys and volume behave normally.
- [ ] Browser approved 0.4.73 baseline, Android stable and live backend remain unchanged.
- [ ] No accidental production deployment, no token/URL leak in diagnostics, no account cross-logouts.
- [ ] Owner hears and approves real sound on Windows, not only mock/test fixtures.

## Shared-team workflow and version control

- `planning/windows-companion-v1-20261108`: **source of planning truth** and owner review. Change docs here deliberately; do not add shipping code.
- `experiment/windows-companion-integration-20261108`: isolated engineering PoC (create from approved planning snapshot); freeze each tested build by commit hash. No pushes to concurrent desktop/mobile/song branches.
- Existing `experiment/desktop-native-source-20261108`: **browser extension experiment owned by another chat**, not a base to rebase or merge blindly.
- `archive/desktop-0.4.73-accepted-20261104`: read-only accepted browser extension. Do not move its SHA.
- Any common API feature request must be written as a separate proposal and explicitly coordinated with server/Android/extension owners; never change shared files behind their backs.
- Keep one `docs/windows/NEXT-CHAT.md` handoff for future chats once first real PoC starts. Before that, this README is the handoff.

## Current practical instruction for owner (W13 supersedes W0)

**Nothing to install or rerun.** The owner has already supplied the official Windows W10 identity and integrity report. Keep normal Yandex Music unchanged. CELIKOM Windows-native audio source substitution is blocked while no permitted, supported native source-provider interface is evidenced.

Only after a documented technical opening and an independent safety plan would the owner be asked for a narrowly scoped consent. The prior W0 instruction to install/report the app is **obsolete**.

**No release timing is promised.**
