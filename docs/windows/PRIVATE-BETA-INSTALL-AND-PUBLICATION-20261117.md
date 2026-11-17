# CELIKOM Windows 0.24.51 — private beta installation and website readiness

## Official owner-approved beta package

Read `docs/windows/CURRENT-WORKING-RELEASE.md` first. Download only the exact **unchanged unsigned EXE** `CELIKOM-W169-TRACK-HANDOFF-02451-UNSIGNED.exe` from ChatGPT personal Library `/CELIKOM/W169/` or use the matching ZIP `CELIKOM-Windows-0.24.51.zip`. No need to install both. Correct hashes are in the current working release document. This private beta is not yet a public, signed installer.

### 1. Clean uninstall + reinstall on owner's own Windows PC

1. Close **CELIKOM** and **Yandex Music**, including their tray/background instances. Keep copies of support diagnostics if you may need to report a rare crash.
2. Windows Settings → Apps → Installed apps → **CELIKOM** → Uninstall. Use **the application's normal uninstaller**: it first calls CELIKOM `--restore-native` to restore the **official Yandex EXE and ASAR** from the verified snapshot, then uninstalls CELIKOM. If original restoration fails, **stop** and resolve it; do not manually delete integration/backup or Yandex program files. The uninstaller displays an actionable warning if Yandex is still running.
3. In the uninstall prompt, opt in to **“Также удалить сохранённые данные входа”** if a **truly new local CELIKOM login** is desired. Without checking it, the per-Windows-user encrypted session is kept intentionally. This checkbox removes only `%LOCALAPPDATA%\CELIKOM\Windows\session.dpapi`; cloud trial/subscription state is NOT reset.
4. The normal uninstall leaves additional CELIKOM diagnostic data and a native snapshot in `%LOCALAPPDATA%\CELIKOM\Windows\` by design. **Do not manually delete that directory or the YandexMusic directory during uninstall.** If the user explicitly wants a forensic-free local cleanup, first independently verify the uninstaller successfully restored the original Yandex pair, preserve useful logs/backup and only then consider deleting leftover CELIKOM-only diagnostic data; deleting it is not required for a clean new installation.
5. From Library folder `/CELIKOM/W169/`, obtain and run the same EXE. It is built for **Windows 10/11 x64**, is **per-user**, and does not require administrative installation or ship Yandex Music. Check SHA256 if Windows flags an unrecognized publisher; the file is unsigned. Do not disable antivirus or advise testers to bypass safety protections indiscriminately.
6. Open CELIKOM and sign in; with a supported official Yandex Music installed, press **Старт** and follow the native integration prompt. Verify the version shown is **0.24.51**, native module **0.24.32** and the module matches; select a track in Yandex and check a normal Next, pause and VPN toggle.
7. The snapshot is used by CELIKOM for reversible integration. Do not delete it by hand while CELIKOM is installed/active.

### 2. Friend/tester setup

- Friend should download the **same** verified EXE via the owner's private transfer, **not a guessed public ChatGPT Library URL**. A Library file remains accessible only to the owner, unless deliberately shared by a supported product action; this process does not make it public.
- Friend must use **their own Windows account and their own CELIKOM credentials**, not the owner's encrypted session or keys. Official Yandex Music is a separate dependency; the installer does not bundle it. Compatibility remains restricted to the vendor images already supported by the native installer.
- Obtain tester's consent that the installer is **unsigned private beta**, not a general public release. The app may be flagged by Windows SmartScreen until it is signed and gains reputation; do not falsely imply malware is impossible just because SHA256 matches.
- Ask for simple feedback: version/native module; audio continuity across ten Next transitions; pause/status UI; whether VPN interrupts audio; whether Yandex unexpectedly closes/reopens; local time of any incident plus CELIKOM support diagnostics. No passwords, access tokens, or signed audio URLs in submitted reports.
- A successful owner test is not a substitute for a second-machine test. Do not publish as a fully verified consumer release merely because the friend launches it once.

### 3. Website publication plan (NOT YET LIVE)

1. **Sign & security:** acquire a trusted Windows code-signing certificate, sign the distributable, validate signature and malicious-file/security checks, user-consent and rollback, and update the immutable release manifest with EXE/ZIP SHA256. An unsigned executable from today's Library should not be presented as a completed publicly trusted release.
2. **Compatibility and support:** run clean PC tests on Win10/11 x64 with officially installed, exactly supported Yandex version; verify first-time account, reinstall/uninstall restores originals, native 0.24.32 upgrade and auto-update behavior. Re-test ordinary playback, Next, pause, VPN and long-session reliability.
3. **Publisher and hosting:** publish signed immutable assets on a controlled `celikom.com` downloads endpoint/CDN after owners approve a release; serve SHA256 plus file size, changelog, requirements, support/privacy/licensing. Never use a temporary private GitHub Actions artifact link or a personal ChatGPT Library link as the public website binary URL.
4. **Release gate:** `windows-companion/w20/release-gate.ps1 -Mode Release` currently blocks production with `W24_RELEASE_BLOCKED_NO_VERIFIED_AUDIO_OR_SIGNING`. Keep it blocked until actual signing/audio/installer/security acceptance is documented. No bypass via changing gate text alone.
5. **Owner decision:** product status currently **owner-accepted working build / private beta 0.24.51**. Do not tag as fully public GA or change production update feed until explicitly authorized and checks above pass.

### Rollback

Exact package source, frozen stable branch and exact backup are in `docs/windows/CURRENT-WORKING-RELEASE.md`. `main` has NOT been modified. If a future version regresses, use the frozen 0.24.51 source/binary and existing safe in-place installer behavior. Do not restore Yandex files manually.
