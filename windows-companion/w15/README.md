# W15 — native Windows Companion + PulseSync bridge (preflight)

## Owner UI smoke, 2026-11-09

W15 app launched successfully in owner's Windows 10 (screenshot), after standard SmartScreen unknown-publisher warning. UI window verified; CELIKOM login and actual Yandex source replacement not tested. W15.1 updated UI to Home/Account tabs with copyable pairing code; login/logout now rotate addon pairing token; Stop resets stale state. Windows W15.1 CI [42581622466](https://github.com/manufact-test/nomusic/actions/runs/42581622466) SUCCESS. Inner W15.1 preview ZIP SHA-256 `14f62042fa99d7cfabc831629182543c8db873f7447e7273950a6ecdbe28776e`, artifact `13657009476`. User does not need to rerun a GUI-only smoke immediately.

**Real installed Yandex integration is still untested.** Next safety-gated test is in an isolated/snapshotted Windows machine only, with explicit approval and Microsoft security ON. PulseSync proprietary client licensing requires commercial clearance.


**Verified delivery (2026-11-09):** [W15 Windows CI 42530365857](https://github.com/manufact-test/nomusic/actions/runs/42530365857) **SUCCESS** for source `040a3dd5e0ec0d829137e6192b6b231d69fe80eb`: compiled standalone Win-x64 EXE; compiled PulseSync SDK addon; unit contracts, WinForms compile, real local Kestrel HTTP and DPAPI contract tests, all older regression checks; ZIP artifact `13637501124` created and CRC checked. **Native Yandex audio substitution is NOT TESTED**. First owner check is to start the CELIKOM EXE alone, with no changes to Yandex or Windows security. Then arrange a separately approved isolated VM integration test. No server/browser/Android code changed.


Source: `windows-companion/w15/Celikom.Companion` (.NET 10 WinForms + Kestrel loopback) and `w15/addon` (PulseSync SDK).

**Scope:** standalone CELIKOM account login and encrypted per-device session; On/Off; pairing code; localhost-only authenticated bridge; approved exact-ID signed Range URL from existing PHP API; SDK source substitution inside PulseSync host. No second player, no Yandex EXE/ASAR write from CELIKOM, no debuggers or profile reads.

**Security:** Windows DPAPI CurrentUser for access/refresh/bridge tokens; pairing code one-use/10min/5 failed attempts max; 127.0.0.1:21471 only; strict isolated PulseSync Origin + 64-hex bridge token required; unknown URLs and expired grants rejected; malformed/unauthorized/offline => original; bridge never returns access/refresh tokens or opens other network services. The user configures a real HTTPS CELIKOM backend address at login. The addon talks only to loopback and passes validated signed media URLs to host, not passwords.

**Gate:** Not an official Yandex installer. PulseSync Client itself modifies app.asar and EXE integrity hash; this may invalidate vendor signature and trigger AV/SmartScreen. Never disable protection or silently install. PulseSync Client commercial EULA must be cleared before paid product. End-to-end audio only after a separately approved isolated Windows test.

**Current code readiness:** source written; Windows CI compilation and integration tests must pass before any claim. Packaging intentionally marked PREVIEW. See `docs/windows/W14-FIRST-REAL-CLIENT-TEST-PLAN-20261109.md`.
