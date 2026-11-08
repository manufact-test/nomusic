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
