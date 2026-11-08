# W11 — pipe-only external attach: security and feasibility gate

**2026-11-08, CELIKOM Windows isolated branch only.**
No changes to installed Yandex Music, no launch of a logged-in client,
no production CDP exposure, and no second production audio engine.

## W10 actual owner device — definitive read-only report

Windows 10 19045 x64, official Yandex Music EXE `5.126.1.0`,
package `5.126.1`, ASAR SHA-256
`5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`,
owner W3 identity **MATCH**.

- Electron fuse wire: **V1_FOUND**
- `EnableEmbeddedAsarIntegrityValidation`: **ENABLED**
- `OnlyLoadAppFromAsar`: **ENABLED**
- Windows PE `Integrity / ElectronAsar` resource: **PRESENT**
- Embedded resource header SHA-256 vs official ASAR: **MATCH**
- Official app remains running and unchanged.
- No credentials, user source code, process data or track audio collected.

**Decision: HARD NO-GO for changing the installed app.asar alone.**
Electron verifies the ASAR header against the hash embedded in its
Windows executable, and integrity mismatch can force app termination.
Changing the EXE's embedded hash would affect its signed binary and
is not an automatic safe workaround. Do not change fuses or weaken the
integrity verification. Third-party mod loaders that edit EXE and ASAR
require much higher trust and update/rollback management. They are
not a recommendation for CELIKOM production.

Canonical sources:
- https://www.electronjs.org/docs/latest/tutorial/asar-integrity
- https://www.electronjs.org/docs/latest/tutorial/fuses
- https://www.electronjs.org/docs/latest/tutorial/devtools-extension
- https://chromedevtools.github.io/devtools-protocol/

## Attach option matrix

| Approach | Tested | Official app original files intact? | Can directly replace official player's audio? | Current decision |
| --- | --- | --- | --- | --- |
| Modify in-place ASAR only | W10 owner integrity proof | No | Invalid integrity likely blocks startup | **NO-GO** |
| Modify ASAR and official EXE resource/checksum | Third-party published examples only, not CELIKOM | No | Theoretically possible but signed/auto-update hazards | **NO-GO** |
| Chrome extension in installed Electron | Electron session.loadExtension requires app main-process cooperation | Yes if supported | Not demonstrated | **UNPROVEN/NO-GO** |
| SMTC / Windows media transport | External metadata/controls only | Yes | No source replacement surface | **NOT SUITABLE** |
| External CDP over loopback TCP | W7 28/28 in private fixture, W8 33/33 | Yes | Yes in test renderer | **NOT SAFE FOR AUTHENTICATED APP** |
| **Private CDP over inherited pipe** | W11 test proposed here | Yes | In private test renderer | **RESEARCH ONLY** |
| Official documented plugin / source provider API | No verified plugin SDK found in official desktop documentation | Yes | Unknown | **UNPROVEN** |
| Separate audio output/playback engine | Already conflicts with product requirement | Yes | No, creates second playback owner | **REJECTED** |
| Browser extension for Yandex Music web | Separate existing CELIKOM browser track | Yes | Browser audio only | **NOT WINDOWS NATIVE SOLUTION** |

No published third-party project is treated as authoritative permission
or evidence that the user's installed build is safe to patch.

## W11 physical experiment (no network debugger)

The existing W7 synthetic Electron app gains a strictly
`CELIKOM_W11_PIPE_ONLY=YES`, random 128-bit nonce, disposable user
profile branch. In this branch it must **NOT** expose a TCP DevTools port.
It still serves only ephemeral loopback fixture MP3, pinned public Yandex
web resource/source class factories and the existing W4/W8 adapter.

`windows-companion/w11/run-pipe-e2e.mjs` starts **generic Electron**
from our isolated W5 development dependencies with Chromium
`--remote-debugging-pipe` and `--user-data-dir` set to the new
temporary profile. Standard FD3 and FD4 carry JSON-NUL framed CDP
messages between child and *parent only*; no HTTP debug discovery and
no port scanning. The **only external network** permitted in the
renderer is our synthetic loopback test server; all Yandex domains and
account/profile access remain blocked.

The parent process must:
1. Receive nonce-bound fixture-ready status and validate localhost origin.
2. Request `Browser.getVersion`, `Target.getTargets`,
   `Target.attachToTarget` with a single nonce/title/origin matching
   window, then `Runtime.enable` and `Runtime.evaluate`.
3. Dynamically activate the same W7/W8 source replacement and real
   media error recovery in that *test window*. It must pass the original
   33/33 (or higher) real Electron decoder tests, not a mock.
4. Close the pipe and browser, clean the temp profile; no persistent
   debugger, no public listening debug port, no user credentials.
5. Any failure to connect to an inherited pipe is an explicit red CI
   **NO-GO**. Do not silently fall back to the old W7 TCP port.
6. W11 unit tests guard malformed frames, mixed CDP events, wrong
   target identity, session confusion, and forbidden protocol domains.

All previous W4–W10 Windows CI tests continue alongside W11.

## What passing W11 would prove (and would NOT prove)

Private pipe transport avoids a globally reachable localhost debugger
port, but it is still privileged Chrome DevTools Protocol. There is no
evidence the already-installed, running Yandex 5.126.1.0 is launched
with a suitable inherited pipe or can be attached externally later.
Launching Yandex under a new debug pipe with an existing authenticated
profile is **not authorized** and does not establish a safe deployment
strategy. Chrome/Electron versions may differ in pipe support.

A passing W11 would only narrow the transport problem for a future
**separately consented**, isolated official-client *copy* experiment.
It does not justify changing signed Yandex binaries, accessing accounts
or claiming native CELIKOM playback works today.

## Next product decision

A working paid Windows CELIKOM release needs a reliable, user-safe,
permission-limited attachment point in the official desktop renderer.
If there is no supported interface, the honest next step is to agree
on a separate, explicit risk-scoped test of a non-authenticated
sandboxed copy — never silently patch the installed official app.
