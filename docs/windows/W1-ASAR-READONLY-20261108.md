# Windows Companion — W1 read-only ASAR checkpoint (2026-11-08)

## Received actual owner diagnostics

- Host: Windows 10 build 19045, x64.
- Official Yandex Music EXE version: **5.126.1.0**.
- Installed under `%LOCALAPPDATA%\\Programs\\YandexMusic\\Яндекс Музыка.exe`.
- Process running: yes, matched same executable path.
- `resources/app.asar` exists.
- No integration hook was active during the owner's first check. No Yandex files were changed.

## New W1 diagnostic

Functional source SHA: `06bd0132a4a2a34e8f4a7963c014f7875c93afa0`.
Branch: `experiment/windows-companion-integration-20261108`.
Workflow `Windows Companion — read-only probe`, run [42505216768](https://github.com/manufact-test/nomusic/actions/runs/42505216768): **SUCCESS**, native Windows compile/tests/ZIP upload. No physical test of this **new W1** exe has yet been performed by the owner.

Artifacts: CI `celikom-windows-readonly-probe` and personal ChatGPT Library `CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W1-ASAR.zip` (Library ID `libfile_a0559609a6a48191b7f07af05502dfa5`).

W1 executable includes `AsarInspector.cs` and `AsarReport.cs`; operates strictly read-only:
1. Retains prior official installation discovery and redacted path / version reporting.
2. Reads Electron `app.asar` binary header with hard limits; obtains package name, package version, main entry and presence of entry.
3. Computes ASAR SHA-256, useful for exact version identity (NOT an authenticity proof).
4. Scans bounded shipped JS sources in memory for **presence-only** Electron and file-info hook markers. Never outputs snippets, URLs, credentials or full personal paths.
5. Reports conservative state, never claims a working audio hook. If marker is absent, a remote renderer bundle may still contain it.
6. Uses only synthetic temporary-file test fixtures on CI; no actual official Yandex application was modified/tested there.
7. ZIP has `CELIKOM-Windows-Probe.exe` and `START-CELIKOM-PROBE.cmd`: launcher creates `CELIKOM-Windows-report.txt` and opens Notepad.

## Required owner action (only one)

With original Yandex Music running, unzip W1 and double-click `START-CELIKOM-PROBE.cmd`; provide generated `CELIKOM-Windows-report.txt`.

## Next development gate after receiving W1 report

- Decide if `app.asar` is readable and where the Electron entry/hook path lives.
- Examine official app compatibility with the exact hashed build and app-update integrity checks. Do not patch the installed Yandex client or replace its executable without explicit owner informed permission and a verified rollback.
- Build source-replacement PoC in a **separate test copy or isolated compatible test runtime** first, reusing CELIKOM backend exact-ID/entitlement and signed Range audio only after verifying transport. The agreed target is ONE player, native Play/Pause/Seek, original on no mapping. No second audio decoder, no PulseSync mandatory dependency.
- Before authorizing a live patch on the user's PC, establish backups, version-hash verification and restoration. A broken Yandex launch is a hard stop.
- Continue avoiding all edits outside Windows Companion isolation. The older browser native-source spike failed to prove production gains and must not be merged.
