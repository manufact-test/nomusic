# W14 — source-only candidate against PulseSync add-on API

**Status: CODE CANDIDATE + UNIT TESTS; NOT live Yandex, NOT installable Companion.** A successful SDK mapping call is recorded as `SDK_MAPPING_ACCEPTED`, **not** proof of audible replacement. A rejected SDK call never marks active mapping.

This directory starts the actual **CELIKOM adapter** for the third-party PulseSync add-on contract rather than another Chromium/ASAR synthetic renderer. It is independent JavaScript, with no third-party runtime bundled or licenses copied. No user account token, browser profile, audio sample, official executable or network endpoint is accessed. The host contract is based on the checked-in public FckCensor SDK bridge and PulseSync-mod WebHost runtime.

Code: source-controller.mjs; tests: source-controller.test.mjs.

**Surface used:** PulseSync add-on api.player.onTrackChange / getSnapshot and api.client.setTrackReplacements / clearTrackReplacements. Host/Yandex should remain the **only** audio decoder/clock. This controller never creates an Audio element or calls play/seek.

**Safety contract:** disabled by default, exact track ID, allowlisted same HTTPS origin, signed short-lived CELIKOM Range endpoint, server-provided approval and entitlement, no username/password stored here, stale Next response cannot re-hook, Original per current track, global Stop, graceful clear on dispose. The future Companion must be the source of authorized resolve() and the allowed origin. These placeholder test URL/grants are synthetic and never shipped as real media.

**Candidate SDK package:** `windows-companion/w14/addon/` uses the actual published `@pulsesync/addon-sdk@0.18.0` Vite builder to verify compilation (CI only). Its `start` is intentionally OFF: no account, no authenticated resolver, no requested source, no second player, no window/CDP. A successful package build is not evidence of a runtime hook on Yandex 5.126.1.0.

**Not yet implemented:** consumer installation, PulseSync SDK addon packaging, approved Companion IPC/login, own server signed grant adaptation, live playback tests, compatible host/version validation, Windows integrity-safe installation, test VM, account/legal approval. Do **not** tell owner to install PulseSync based on this file. It proves only module safety contract and *that a public third-party SDK API shape exists*, not that this exact module is running in 5.126.1.0.

## External audit discoveries

- PulseSync-mod [v2.1.5](https://github.com/PulseSync-LLC/PulseSync-mod/releases/tag/v2.1.5) released 2026-11-05 calls itself a \`5.126.1\` patch but says version was **spoofed from 5.125.3**; does not prove exact binary support.
- PulseSync [Client installer source](https://github.com/PulseSync-LLC/PulseSync-client/blob/dev/src/main/core/mod/mod-files.ts) copies replacement ASAR and invokes an AsarPatcher, includes backup path and EXE-integrity restoration. PulseSync-mod [integrity utility](https://github.com/PulseSync-LLC/PulseSync-mod/blob/main/toolset/utils/integrityUtils.js) **rewrites hash bytes inside a Windows EXE resource or the EXE itself**. With W10 actual enabled integrity + signed official EXE, this is an important code-signing / SmartScreen / Defender warning risk. Editing a checksum is not equivalent to preserving the vendor's digital signature. NEVER recommend disabling protection or using evasion.
- PulseSync-mod LICENSE is MIT; PulseSync Client LICENSE (commercial copying/modification/redistribution limitations) is **not** MIT. Need rights review or independently licensed implementation before any paid distribution. Third-party SDK permissions and vendor Yandex terms require review. No claim that it can be shipped under CELIKOM branding yet.

## Next meaningful gate

1. Audit precise PulseSync installation/rollback and version checks; compare real 5.126.1 patch path without touching current owner's install.
2. Package a source-only CELIKOM add-on under the third-party SDK *for isolated environment testing*; integrate Companion-owned authorized resolver through a narrowly scoped, protected IPC, avoiding renderer account tokens.
3. Present a narrowly defined VM-based test and backup plan for owner's explicit consent **before** any actual mod installation or official client launch. Measure actual native pause/seek/next and sound with Defender ON. If impossible without insecure patching or forbidden commercial rights, change route transparently.
