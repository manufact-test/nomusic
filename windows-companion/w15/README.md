# W15 — native Windows Companion + PulseSync bridge (preflight)

Source: `windows-companion/w15/Celikom.Companion` (.NET 10 WinForms + Kestrel loopback) and `w15/addon` (PulseSync SDK).

**Scope:** standalone CELIKOM account login and encrypted per-device session; On/Off; pairing code; localhost-only authenticated bridge; approved exact-ID signed Range URL from existing PHP API; SDK source substitution inside PulseSync host. No second player, no Yandex EXE/ASAR write from CELIKOM, no debuggers or profile reads.

**Security:** Windows DPAPI CurrentUser for access/refresh/bridge tokens; pairing code one-use/10min/5 failed attempts max; 127.0.0.1:21471 only; strict isolated PulseSync Origin + 64-hex bridge token required; unknown URLs and expired grants rejected; malformed/unauthorized/offline => original; bridge never returns access/refresh tokens or opens other network services. The user configures a real HTTPS CELIKOM backend address at login. The addon talks only to loopback and passes validated signed media URLs to host, not passwords.

**Gate:** Not an official Yandex installer. PulseSync Client itself modifies app.asar and EXE integrity hash; this may invalidate vendor signature and trigger AV/SmartScreen. Never disable protection or silently install. PulseSync Client commercial EULA must be cleared before paid product. End-to-end audio only after a separately approved isolated Windows test.

**Current code readiness:** source written; Windows CI compilation and integration tests must pass before any claim. Packaging intentionally marked PREVIEW. See `docs/windows/W14-FIRST-REAL-CLIENT-TEST-PLAN-20261109.md`.
