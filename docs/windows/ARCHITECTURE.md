# CELIKOM Windows — architecture v1 (proposal)

> **LATEST 2026-11-09 OWNER PRODUCT CORRECTION:** [Current NEXT-CHAT](NEXT-CHAT.md) and [W19 owner correction](W19-OWNER-PRODUCT-CORRECTION-20261109.md) supersede all old stop/go instructions below. Native consumer CELIKOM + Yandex single playback pipeline, one normal Windows installer, no customer Sandbox/VM/manual mod setup, no disabling Defender/SmartScreen. W15.2 UI/addon built; W18 mod install+addon import real; original Yandex EXE signature invalidated by PulseSync mod; native audio not proven. All phases below are historical planning until confirmed new architecture. Do not fabricate "clean" security compatibility.

> **W14 NEW APPROVED DIRECTION (2026-11-08):** Modifications to the client may be **considered**, not secretly installed; preserve Yandex's native decoder and transport, normal Windows protection and transparent user consent. [W14 architecture and safety plan](W14-MODIFIED-CLIENT-PATH-20261108.md). W13 NO-GO applies to *unchanged* official binaries only. A proposed PulseSync SDK addon requires real-version verification plus a separate commercial rights review; SDK host EULA != mod MIT license.



> **W13 architecture verdict (2026-11-08): BLOCKED / NO-GO under present rules.** Read [W13 decision](W13-OFFICIAL-CLIENT-INTEGRATION-DECISION-20261108.md). The actual official Yandex 5.126.1.0 has enforced ASAR validation and ASAR-only loading (owner W10). **Candidate B's packaged integration/ASAR-patch route is now prohibited**, not an independently viable preferred implementation. PulseSync's third-party SDK requires its modified client runtime and is not an official unmodified Windows integration. There is no demonstrated permission-limited source-provider interface in the installed official player. This entire proposal, including companion UI and backend integration flows, is **frozen** until a genuinely supported attach seam or a separately approved change of requirements is demonstrated. Do not infer Windows compatibility from isolated W5–W12 Electron fixtures.


Status: **design hypothesis / read-only study**, 2026-11-08. Runtime compatibility with the owner's installed Yandex Music has not yet been measured.

## Scope and invariant

**Use the official Windows Yandex Music app**, not an embedded website, forked music service, browser tab, external Spotify client, replacement MediaPlayer or a standalone alternative music application. CELIKOM Companion is a tray/window management and entitlement client plus an optional, reversible integration bridge. The Yandex app remains the sole playback owner: play, pause, seek, next, volume, queue and media keys remain native.

```text
                   CELIKOM account / Hostinger existing backend
                         PHP 8.3 + MySQL + HTTPS
                 auth, entitlement, catalog, resolve, signed Range
                                     ^
                                     | official, restricted HTTPS API
                                     v
 Official Yandex Music Windows app <-- bridge --> CELIKOM Companion
   player + UI + media session         |             small tray app
          ^                           |                |
          |   source-only substitution|                |
          +---------------------------+        account / status / upload
```

**Desired playback:** identify exact Yandex track ID -> query approved CELIKOM mapping -> get authorized, short-lived **same-origin** audio URL -> replace Yandex file-info response before decoder starts -> let Yandex control the replacement. When no approved mapping, authorization or compatibility, preserve **untouched Yandex audio**. No global OS sound interception or cross-process muting.

## Candidates / feasibility ranking

**A. Supported SDK bridge (low integration risk, high dependency risk).** Study FckCensor on PulseSync and `api.client.setTrackReplacements(replacements)`; investigate whether a Windows CELIKOM addon can use this interface with our own catalog/access control. This requires the user to install PulseSync, creates an external runtime and may be unsuitable for a polished paid product. Verify SDK license, API access, commercial terms, account permissions and stale signed URL refresh. A serves as feasibility baseline, not an automatic product choice.

**B. CELIKOM-managed reversible local integration (preferred independence if proven).** Inspect how FkCensor modifies installed Electron `app.asar` and intercepts `getFileInfo` / `getFileInfoBatch`. Implement a **new** narrow source-substitution bridge if compatibility and maintenance costs justify it. Restrict to a known, hash-validated version of the official app. Preserve original package / fail-safe restore; protect against updates during installation and playback; show supported-version status. Never silently disable integrity checks, replace unknown executables, edit Windows binaries without informed user consent or ship someone else's mod as CELIKOM. Third-party techniques are references, not drop-in code.

**C. Observe-only OS media session (safe but insufficient).** Windows GSMTC can help observe/control media state if exposed; does **not** substitute audio. Useful as telemetry/recovery signal only. It is not a replacement playback architecture.

**Fallback:** on unsupported or updated Yandex desktop client, disable substitution clearly and leave Yandex playing original. Do NOT automatically switch to independent audio overlay: user expects native transport and we already have evidence of sync trouble on other platforms.

**Gate requirement:** choice of A vs B only after owner installation, compatibility matrix, independent lawful/licensing review and a rollback demo. Prefer a **supported interface** over private hooks when equivalent.

## Shared backend: reuse, do not fork

Read existing implementation; no new backend or parallel song database.

- `POST /api/v1/auth/login`, refresh/logout/me/sessions: native Windows client should use its **own device/session tokens**; never extract Yandex session/cookies or the browser extension token.
- `GET /api/v1/config`, `GET /api/v1/resolve?audio_formats=mp3,m4a&service=yandex&track_id=...`: **actual endpoint/format to verify at integration** against the latest server branch. Exact service track ID, approval and entitlement check take precedence.
- Resolve emits `audio_url`, `replacement_id`, `expires_at`, version/cache TTL as defined by live backend. Validate allowed HTTPS origin, route, expiry, format, byte ranges and duration before use.
- `GET /api/v1/audio/{replacement}?token=...&expires=...` returns authorized Range 206 for streaming; short-lived URL is a bearer capability. No logged URLs, tokens, referrers or unrestricted forwarding to third parties. Streaming context in Electron must be tested for CORS, 206, Content-Type, caching, URL expiry, repeated seek and signed 401/403 behavior.
- Existing user trial, subscription, rewards, song requests/uploads and moderator approval remain authoritative server-side. No local bypasses.
- New Windows `client_platform` should reuse existing telemetry schema **only after checking allowlists**; no server schema changes in this planning phase.
- Do not assume existing audio URL works with arbitrary private Yandex decoder APIs; validate without exposing secrets.

## Internal modules (proposed, future code `windows-companion/**` only)

```text
windows-companion/
  ui/                   Tauri 2 + TypeScript/HTML/CSS design implementation
  src-tauri/            Rust shell: tray, lifecycle, secure local session storage
  bridge/               separately versioned official-client adapter / experiments
  contracts/            typed API and IPC messages; no server fork
  diagnostics/          redacted logs and local export with consent
  tests/                contract, cancellation, rollback, Windows integration
  README.md
```

**Technology is not frozen.** Tauri 2 + TypeScript/HTML is the initial recommendation for compact web-style UX and Windows installer; Go + WebView2 is a valid alternative if the patched-client adapter is better in Go. Do not choose a framework merely because a competitor uses it. Windows target first, x64; ARM64/macOS/Linux only after verified scope.

Recommended boundaries:
- `IdentityObserver`: exact track ID + confidence and timeline; no guesses by song name alone.
- `CatalogClient`: authenticated resolve; dedupe requests per track/album; short negative TTL; no direct GitHub MP3 fallback.
- `ReplacementBridge`: one source mapping with revision/fencing, no stale cross-track swap; owns hook registration and cleanup.
- `SessionManager`: per-device auth/refresh, explicit logout, entitlement, secure Windows Credential Manager/OS-backed store.
- `CompatibilityManager`: version/hash and app path discovery, update detection, supported/unsupported states, backup + atomic rollback.
- `CompanionUI`: tray/window/consent with no fake Yandex controls; diagnostics opt-in.
- `UpdateManager`: signed CELIKOM updates separated from official Yandex updates; never auto-repatch unknown versions.

## Contracted playback state machine

`OFF` -> `DETECTING_YANDEX` -> `CONNECTED_ORIGINAL` -> `RESOLVING` -> (`REPLACEMENT_READY` | `NO_VERSION` | `UNSUPPORTED`) -> `REPLACING`.

Any track ID change, session revocation, Stop, user's Original preference, version mismatch, expiry or invalid URL invalidates pending work. Apply only the newest exact ID; never modify the native playback clock. Original remains audible whenever anything is uncertain. Original preference survives retries for that track; no auto-reactivation until explicit user action or next eligible track. Distinguish unavailable version from auth failure and integration failure.

## Installation lifecycle and rollback

1. User installs official Yandex Music **from Yandex** and signs into Yandex themselves.
2. User installs CELIKOM Companion, logs into **CELIKOM only**.
3. Detect official app location/version/process; show consent and compatibility; never launch elevated until required and explained.
4. If B validated: ensure Yandex process can be safely stopped only after user consent, create integrity-checked backup, apply reversible change exactly once; restart Yandex; verify health on restart.
5. Self-update of Yandex must produce `UNSUPPORTED` until reverified; do not silently reapply old patch.
6. Disable/uninstall CELIKOM: original bytes restored from valid backup with provenance check, integration state cleaned, Yandex normal; if backup missing, show safe repair route, **do not claim restored**.
7. Virus/AV warnings and code signing are release gates; never instruct disabling Windows security as routine setup.

## Security, legal and engineering gates

- **Technical**: official Yandex client source / injection hooks are private and can change without notice; no public supported CELIKOM plugin API assumed.
- **Contractual**: inspect Yandex client license and ToS, PulseSync SDK terms, modification/update behavior. Public GitHub MIT does NOT license Yandex proprietary code or the audio files.
- **Copyright**: only owner-approved, licensed or otherwise authorized audio in backend; external FckCensorData/YM Liberty tracks are unrelated to Windows design and NEVER auto-published.
- **Privacy**: do not read other apps' cookies, refresh tokens, system audio, browser history; no credentials in logs / support exports.
- **Supply chain**: pin updates, verify signature of installers, redacted diagnostics, fail-safe backups and uninstall.
- **Deployment**: do not modify production Hostinger/website/backend or publish releases without independent approval.
- **Read-only first**: no binary patching or third-party client installation in Gate W0; only after explicit user approval of an isolated test.

## Source links

- https://github.com/Hazzz895/FckCensor/blob/main/src/sdk/bridge.ts
- https://github.com/S4YN3X/FkCensor/blob/main/internal/asarpatch/asarpatch.go
- https://github.com/PulseSync-LLC/PulseSync-mod
- https://music.yandex.ru/download/
- Current CELIKOM accepted browser version: `docs/desktop/README.md`.
