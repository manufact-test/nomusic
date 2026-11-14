# W128 — Read-only audit of CELIKOM elevation launch paths — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Audit basis: W127 code/test HEAD `7e4c8268cba30f781a3fa091d9657718ec463b66` plus the documentation-only commits currently on `main`.
- This is a read-only code audit. No application code, installer, permissions, or runtime behavior was changed.

## Files reviewed

- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion/Program.cs`
- `windows-companion/w15/Celikom.Companion/AppUpdateManager.cs`
- `windows-companion/w15/Celikom.Companion/StableUpdateSupervisorLauncher.cs`
- `windows-companion/w15/Celikom.Companion/StartupHostPreflight.cs`
- `windows-companion/w15/Celikom.Companion/NativeTokenPublisher.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Program.cs`
- `windows-companion/w20/installer/CELIKOM.iss`
- `windows-companion/w20/release-gate.ps1`

## Findings

1. No explicit `runas` / `Verb="runas"` request was found in the reviewed CELIKOM process-launch paths.
2. `MainWindow` launches the installed Yandex executable or the Yandex URI using normal shell execution; no elevation verb is supplied.
3. `AppUpdateManager` launches the verified Inno application updater using normal shell execution; no elevation verb is supplied.
4. `StableUpdateSupervisorLauncher` starts the Supervisor as a same-user child process with `UseShellExecute=false`.
5. The Inno installer declares `PrivilegesRequired=lowest` and installs under `%LOCALAPPDATA%\Programs\CELIKOM`. The release gate explicitly checks both constraints.
6. The companion project does not declare a custom `ApplicationManifest` or an explicit administrator execution level in its project file.

## What remains unknown

This audit does **not** identify the prompt the owner saw. It does not prove that the prompt came from Yandex, Windows, CELIKOM, or a third party, and it is not evidence that the prompt was harmless or malicious. A prompt can originate from an executable or updater outside the reviewed CELIKOM launch paths.

To identify it safely, the remaining evidence is the exact prompt screenshot/title/publisher and a process/resource snapshot taken only if the issue recurs and it is safe to do so. Do not grant administrator rights to an unknown prompt for testing. Do not request elevation as a workaround.

## Issue status

- #53 remains OPEN.
- W120's CELIKOM-process CPU/RSS/event-loop instrumentation remains useful but cannot identify load from Brave, Yandex, GPU drivers or other processes.
- Owner Task Manager CPU/RAM/GPU evidence and the exact prompt publisher are still required before attributing the system slowdown or elevation request.
- No code change or runtime test is claimed by this audit. No installer was built or delivered.
