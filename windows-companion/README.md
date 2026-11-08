# CELIKOM Companion Windows — first implementation checkpoint

**Status: early read-only detector. NOT a functional music replacement or public release.**

- Product architecture and UI design live in `docs/windows/`.
- `Celikom.Core`: detects an *allowlisted executable name* in known install folders and standard Windows uninstall registry keys. Reads its EXE file version, whether expected `resources/app.asar` exists, and whether a process with the **same executable path** is running.
- `Celikom.Probe`: minimal terminal-based diagnostic entry point. Prints a **redacted** report. Does not authenticate, read Yandex account tokens, patch ASAR, execute injected scripts, download audio, call CELIKOM API or write to app folders.
- `Celikom.Core.Tests`: zero-dependency deterministic tests using temporary dummy files; tests never launch or modify Yandex.

### Current known limitation

A Store/MSIX install, unexpected Yandex EXE name, custom folder or a process whose path is inaccessible may show `NOT_INSTALLED` or `CLOSED` even when a real app exists. That is conservative by design. **Do not claim universal detection.** The next stage should collect *redacted* facts about the owner's real official Windows installation before widening discovery.

### Build/check on Windows

Install .NET SDK 10 x64 and run:

```powershell
dotnet run --project windows-companion/Celikom.Core.Tests/Celikom.Core.Tests.csproj
dotnet run --project windows-companion/Celikom.Probe/Celikom.Probe.csproj
dotnet publish windows-companion/Celikom.Probe/Celikom.Probe.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:PublishReadyToRun=false
```

The published EXE can be run without .NET SDK. GitHub Actions `windows-companion-readonly.yml` builds/tests and stores only a PRIVATE CI artifact (not a GitHub Release); it does not deploy or publish to consumers. Do not install this test on production or infer source interception from detection.

### Scope policy

Only isolated `windows-companion/**` on `experiment/windows-companion-integration-20261108`; do not touch stable desktop 0.4.73, Android, the server, website, or the other chat's `experiment/desktop-native-source-20261108`. The owner must confirm real Yandex Windows version and native integration path before we add audio hooks.

### W2 checkpoint — packaged renderer topology

Owner confirmed official Yandex Music **5.126.1.0** (Windows 10 x64), installed and running; W1 read a **54.96 MiB** ASAR with SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`, entry `index.js`, Electron BrowserWindow and Webpack hints. No `getFileInfo` marker in W1's 48 local JS samples. **This is NOT proof the hook is absent:** client may load a remote frontend.

W2 adds `AsarTopology.Inspect`: bounded scan of *packaged* app files only, flags `loadURL/loadFile`, Yandex Music host, static hosting, preload, updater, Webpack and audio source marker hints. The exact owner ASAR SHA is **identity-only**, not an integrity attestation or working compatibility claim. The inspector never reads account/browser profiles, network calls, playback state, audio content or credentials; it neither injects nor patches the official app.

**Owner action:** With official Yandex Music running, extract W2 ZIP, run `START-CELIKOM-PROBE.cmd`, send only `CELIKOM-Windows-report.txt`. Old W1 folder may be removed. Do not install competitor mods or send app.asar or passwords.

**W2 gate:** next chat must inspect the report and decide whether a narrowly scoped isolated fixture/source-interception PoC is justified. No live ASAR modification until rollback and explicit approval. Automated CI validates synthetic fixtures, NOT actual Windows Yandex integration.

### W3 checkpoint — complete packaged source-seam survey + offline gate

After the owner's real W2 report confirmed **MATCH_OWNER_W1**, **1117** packaged JS,
100 scanned, `getFileInfo` and batch markers present, W3 examines up to 96 MiB
across all packaged JS files (max 12 MiB per file), exports only aggregate
method/endpoint and same-file boot/renderer/webpack hints, and records skipped
files explicitly. It does not inspect active renderer requests, user sessions,
cookies or audio. A named source marker does **not** imply an active hook.

W3 also includes an offline `SourceSwapGate` contract for exact IDs, generation
cancellation, entitlement/duration/file readiness, signed URL expiry, same
configured HTTPS API origin and Stop/Original fallback. Only synthetic CI
fixtures exercise the gate. This is **not** an installed bridge or live audio.
The console probe W3 retains W0/W1/W2 reports for comparison and adds W3.

**Owner action:** Extract W3 ZIP, run `START-CELIKOM-PROBE.cmd`, and provide
`CELIKOM-Windows-report.txt`. No change to Yandex installation; old W2 is
no longer needed for subsequent read-only tests.
