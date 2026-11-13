W18 modified Windows host and CELIKOM addon test (2026-11-09)

Owner authorized a separate Windows test without touching their PC. W17 verified official Yandex Music 5.126.1 and PulseSync Mod v2.1.5 installed through PulseSync's own deep link with Defender realtime ON. That invalidated the original Yandex EXE Authenticode signature (HashMismatch). W17 restored both original signed files byte-for-byte, valid signature returned. W18 extends that exact disposable test: build CELIKOM add-on via pinned published SDK, create root-level metadata.json+script.js .pext archive, try importing it using the actual PulseSync Client file association, and probe an anonymous modified Yandex process launch. No subscription/account or audio stream. Report only status and restore bytes again. GitHub hosted Windows Server 2022 is not user's Windows 10. Real pause/seek/Next and protection reputation need an interactive Windows 10 Sandbox with a permitted test account. Commercial usage of proprietary PulseSync Client needs licensing review; never ship patched Yandex without permissions.

## W18 complete result, Windows CI 42585206639

- Defender antivirus/realtime: **True / True**.
- Official Yandex installed: exact W10 ASAR SHA256 + EXE valid signature before mod.
- PulseSync Client 3.0.3-beta installed; vendor PulseSync-mod v2.1.5 matched pinned release SHA256; **PulseSync's own mod handler installed it**, not our patcher.
- Installed modified app.asar exact vendor mod: **TRUE**.
- Official Yandex EXE Authenticode after mod: **HashMismatch (INVALID)**. This is a genuine commercial/trust blocker.
- CELIKOM W15.2 PulseSync SDK add-on imported: **TRUE**, actual metadata found.
- Modified Yandex process launched and remained running: **TRUE**, with no account.
- Original EXE/ASAR restored byte-identically: **True/True**; EXE signature **Valid** afterward.
- Native playback/actual sound/seek/Next: **NOT TESTED**. Windows Server 2022 CI cannot certify Windows 10 SmartScreen or audio.
- Full CI [42585206639](https://github.com/manufact-test/nomusic/actions/runs/42585206639) **SUCCESS**. Green job means tested steps executed, not that native replacement works.

**Next:** the sandbox-only W19 manual audio test with an isolated test music account; no owner signed-in Yandex or disabled protections.
