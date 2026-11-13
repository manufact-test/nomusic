> **Updated product scope 2026-11-08:** The owner subsequently allowed exploration of a *disclosed, installable modified-client route* (without disabled antivirus or a second player). Read [W14 revised plan](W14-MODIFIED-CLIENT-PATH-20261108.md). The W13 NO-GO conclusion remains technically valid for **unmodified official client only**, not a permanent freeze on all Windows engineering. W10 integrity evidence and installation/privacy risks still apply.

# W13 — Official Windows client source integration: feasibility decision

**2026-11-08 — NO-GO for live official Yandex Music 5.126.1.0 source substitution under current safety/product constraints.**

Status: evidence-based architecture decision, **not** a proof that integration is physically impossible in all versions, and **not** a test of authenticated production playback. W13 adds no executable, launcher, debug flags, mod, installer or production change.

## Question and non-negotiable target

Can an independently installed CELIKOM Companion substitute only an approved audio source *inside the original official Windows Yandex Music player's decoder*, retaining Yandex's own Play/Pause/Seek/Next/queue/volume, without changing the signed EXE or checked app.asar, enabling a debugger on the authenticated user profile, reading Yandex tokens, or running a second music player?

**Decision: no supported, permission-limited, independently demonstrable attachment seam is currently established for the actual owner build.** Therefore do not ship, install, claim functional Windows-native support, or continue synthetic fixtures as substitutes for that missing evidence.

The decision is specific to the tested official Windows client (EXE 5.126.1.0 / package 5.126.1, Windows 10 19045 x64, owner W10) and to the owner's stated constraints. It is NOT an assertion that no private internal API exists.

## Evidence hierarchy (do not merge these categories)

**A. Actual owner machine — authoritative for this installed version**

- Owner W0–W3 identified a running official Yandex 5.126.1.0, ASAR SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`. W3 inspected 1117/1117 packaged JS files, but pattern matches are **not** live attachability.
- Owner W10 observed Electron fuse wire `V1_FOUND`; `EnableEmbeddedAsarIntegrityValidation=ENABLED`, `OnlyLoadAppFromAsar=ENABLED`, PE resource `Integrity/ElectronAsar=PRESENT` and resource/hash `MATCH`. Source: [W10 owner report and interpretation](W10-EXE-INTEGRITY-READONLY-20261108.md).
- The official app is **untouched** and source substitution has **never** been demonstrated inside it.

**B. Windows CI — proof only about generated fixtures**

- [W12 CI 42520309048](https://github.com/manufact-test/nomusic/actions/runs/42520309048) SUCCESS on source commit `89c648af08c2016cb49ce2605cd96cd8ccf10330`. W12 synthetic launch guard **6/6**, generic Electron single-instance experiment **5/5**; same-profile second launch forwarded to first instance, different synthetic profile could start separately.
- W11 private inherited CDP pipe: **33/33** synthetic Electron audio checks, no exposed TCP debugger; W5 **35/35** media assertions used pinned public Yandex **web** resource/source classes. Neither demonstrates a supported native attach interface for the official, signed 5.126.1.0 app. See [W11](W11-PRIVATE-PIPE-FEASIBILITY-20261108.md), [W12](W12-SINGLE-INSTANCE-ISOLATION-20261108.md).
- W9's generated unsigned ASAR copy and restore do not relax W10's enforced official ASAR integrity.

**C. External documentation / independent implementations — mechanisms, not compatibility proofs**

- Electron documents enforced [ASAR integrity](https://www.electronjs.org/docs/latest/tutorial/asar-integrity) and [fuses](https://www.electronjs.org/docs/latest/tutorial/fuses). Checked archive mutation can terminate the application. Altering EXE resources/fuses or its signing is forbidden here.
- Electron [extension API](https://www.electronjs.org/docs/latest/api/extensions/) requires the app's Electron `session` to call `loadExtension` at runtime. An extension installed in an external Chrome browser does **not** automatically inject into the installed desktop app; no such official Yandex cooperation has been established.
- PulseSync provides a real **third-party** SDK: [`@pulsesync/addon-sdk`](https://www.npmjs.com/package/@pulsesync/addon-sdk), including an `api.client` source-replacement surface. [FckCensor's SDK bridge](https://github.com/Hazzz895/FckCensor/blob/main/src/sdk/bridge.ts) calls `api.client.setTrackReplacements(...)`. However, [PulseSync-mod's installation/build instructions](https://github.com/PulseSync-LLC/PulseSync-mod/blob/main/README.md) explicitly install a mod and describe repacking to the local `resources/app.asar`. This is **not** a plugin API exposed by untouched official Yandex 5.126.1.0, and current W10 integrity makes assumptions about such a patch unjustified.
- Microsoft's [GlobalSystemMediaTransportControlsSession](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession) exposes media state and transport methods, **not** a setter for another application's source URL. [Windows audio APOs](https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/audio-processing-object-architecture) work on post-decoding audio/DSP streams; they are not a source-selection API for the Yandex decoder.
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/) provides broad, privileged inspection/execution, not a narrowly permissioned plugin bridge; W11's private pipe limits transport exposure but does **not** limit renderer privileges or enable attaching to an already-running authenticated app.
- Yandex's [official desktop download](https://music.yandex.ru/download/) describes the official app and automatic updates, not a public source-provider integration API. A source-substitution SDK officially supported for 5.126.1.0 was **not found in the examined materials**; absence from those materials is not a universal proof of nonexistence.

## Candidate decision matrix

| Candidate | Inside original Yandex decoder? | Official binaries unchanged? | Evidence / blocker | W13 verdict |
| --- | --- | --- | --- | --- |
| Documented Yandex SDK/plugin/source-provider interface | In principle yes | Yes | No verified official mechanism or permissions for 5.126.1.0 | **NOT AVAILABLE AS A PROVEN ROUTE** |
| PulseSync addon `setTrackReplacements` | Works within PulseSync-modded ecosystem, subject to its own version support | No, mod installation changes client runtime | Third-party SDK is real; not native official SDK; current integrity and owner constraints | **OUT OF SCOPE / NO-GO** |
| Direct `app.asar` edit / external `app/` fallback | Could insert hooks if validation bypassed | No | Actual W10 integrity + ASAR-only fuse; EXE modification forbidden | **HARD NO-GO** |
| Unpacked Electron / Chrome extension sideload | Potentially if host loads it | In theory | `session.extensions.loadExtension` needs cooperation by official main process; none shown | **NO-GO WITHOUT VENDOR SUPPORT** |
| CDP over TCP or private inherited pipe | Synthetic yes | Yes (for special launch), but privileged debugger | Official process cannot be safely attached as currently running; W12 lock may forward second launch; auth/debug data exposure | **NO-GO IN OWNER SESSION** |
| Native Windows injection, process-memory hook, DLL preload | Possibly | On disk maybe | Runtime tampering, version fragility and privileged private-data access; violates safety requirements | **REJECTED** |
| HTTPS interception / local proxy / response rewrite | Only if all relevant requests/keys/codec paths intercepted | EXE maybe | No proof official app follows an opt-in proxy; TLS/account privacy and update/DRM risks; unreliable decoder lifecycle | **REJECTED** |
| GSMTC / SMTC / WASAPI loopback / APO | No source swap | Yes | Media control or audio processing only; does not choose Yandex track source | **NOT A SOLUTION** |
| Independent audio element/virtual player | No — separate clock/decoder | Yes | Explicit owner product invariant violated | **REJECTED** |

**Important distinction:** a third-party mod with its own SDK can be a working *modified-client* solution. It cannot be repackaged in reporting as integration into the unchanged official, integrity-protected application.

## Decision and work stop

1. **Native Windows integration status = BLOCKED / NO-GO under current constraints.** No installation/download to owner, no runtime hook, no further W14 synthetic-only gates, no GUI promised as an operational audio product.
2. Preserve W0–W12 work and backup branches. Do not rewrite/force-move either backup. No changes to desktop extension, Android, backend, website, production or release workflows.
3. No fresh official-app executable/profile/account data, fresh W0–W10 probe, or owner intervention is needed for this decision.
4. All previous source-substitution test success remains valid **only** in its respective synthetic environment. Official native pause/seek/queue + CELIKOM replacement is **NOT TESTED**.

## Viable next product choices

**Recommended now:** keep CELIKOM's existing browser-extension route for Yandex Music web as the supported desktop computer experience. This does not claim to integrate with the official Windows application. Windows Companion native-source feature and its UI/product release are paused, not silently turned into an overlay.

**Possible path to reopen official-app development:** obtain a written vendor-supported, versioned, permission-limited **desktop source-provider/plugin API** allowing source replacement while retaining official audio ownership. Validate its exact API, host version, security/entitlement and commercial permission before any proof-of-concept.

**Alternative only if owner changes the rules:** explore a PulseSync addon as a clearly disclosed **modified-client** dependency, after independent commercial/licensing/security review, a version-pinned compatibility assessment and separately approved test/rollback. It does **not** satisfy the present 'unaltered official Yandex' requirement and must not be installed implicitly.

A second player / WASAPI audio overlay is not a fallback for this product.

## Minimum new evidence to revisit NO-GO

All must be true before calling a route GO: (1) actual reachable attachment mechanism documented by Yandex or authorized host and confirmed for the exact installed version; (2) no official signed file changes, no unrestricted authenticated debugging or private-data extraction; (3) exact-track, native single-decoder Pause/Seek/Next/queue ownership shown in a separately approved safe test; (4) safe disable/update path with original unmodified; (5) legal/commercial permission where relevant and explicit owner acceptance.

A future experiment using any **official client copy** or private CDP would be a **new, separately scoped high-risk proposal**, not W13 permission. Before requesting owner consent, document: disposable isolated VM or separate machine, no authenticated owner profile, no existing official primary process, offline/throwaway data, identity/hash checks, single-instance forwarding fail-stop, no persistent debugger or exported secrets, precise action list, threat model, isolation proof and rollback. Even a safe non-authenticated test would not by itself prove authenticated production compatibility. **No such experiment was run in W13.**

## W13 repository handoff

Only documentation should change in this W13 commit: `docs/windows/W13-OFFICIAL-CLIENT-INTEGRATION-DECISION-20261108.md`, `NEXT-CHAT.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `PRODUCT-DESIGN.md`. Previous verified checkpoint before W13: `19e6a5375453e29c7269e5b0ff1f4774a188c992`.

Protected backups (verified at W13 start):
- `backup/windows-w11-verified-before-w12-20261108` = `2e4134554843a416181153d01bc4df06bdf5590f`.
- `backup/windows-w12-verified-handoff-20261108` = `19e6a5375453e29c7269e5b0ff1f4774a188c992`.

Documentation-only changes do not require W5–W12 CI re-execution and must not be represented as new native compatibility test success.
