# W128 — Read-only audit of CELIKOM elevation launch paths — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Audit basis: W127 code/test HEAD `7e4c8268cba30f781a3fa091d9657718ec463b66` plus the documentation-only commits currently on `main`.
- The initial review was read-only. A CI-only regression guard was then added; no application code, installer, permissions, or runtime behavior was changed.

## Files reviewed

- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion/Program.cs`
- `windows-companion/w15/Celikom.Companion/AppUpdateManager.cs`
- `windows-companion/w15/Celikom.Companion/StableUpdateSupervisorLauncher.cs`
- `windows-companion/w15/Celikom.Companion/StartupHostPreflight.cs`
- `windows-companion/w15/Celikom.Companion/NativeTokenPublisher.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Program.cs`
- `windows-companion/w24/Celikom.NativeInstaller/NativeIntegrationManager.cs`
- `windows-companion/w24/Celikom.NativeInstaller/NativeAsarImageBuilder.cs`
- `windows-companion/w24/Celikom.NativeInstaller/NativeModuleIdentity.cs`
- `windows-companion/w20/installer/CELIKOM.iss`
- `windows-companion/w20/release-gate.ps1`

## Findings

1. No explicit `runas` / `Verb="runas"` request was found in the reviewed CELIKOM process-launch paths.
2. `MainWindow` launches the installed Yandex executable or the Yandex URI using normal shell execution; no elevation verb is supplied.
3. `AppUpdateManager` launches the verified Inno application updater using normal shell execution; no elevation verb is supplied.
4. `StableUpdateSupervisorLauncher` starts the Supervisor as a same-user child process with `UseShellExecute=false`.
5. The Inno installer declares `PrivilegesRequired=lowest` and installs under `%LOCALAPPDATA%\Programs\CELIKOM`. The release gate explicitly checks both constraints.
6. The companion project does not declare a custom `ApplicationManifest` or an explicit administrator execution level in its project file.

## CI regression guard

Added a Windows Integration CI step in `.github/workflows/windows-w98-integration-ci.yml` that:
- rejects an explicit `Verb="runas"` in the reviewed CELIKOM launch paths;
- checks that the app updater uses ordinary shell execution and the Supervisor uses a same-user child process;
- requires the Inno installer to remain `PrivilegesRequired=lowest` under `%LOCALAPPDATA%\Programs\CELIKOM`;
- rejects an explicit administrator manifest setting in the companion project.

Exact pre-guard backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`.
CI guard commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`.
Main CI [43604761393](https://github.com/manufact-test/nomusic/actions/runs/43604761393) — **SUCCESS**.
Windows integration CI [43604761386](https://github.com/manufact-test/nomusic/actions/runs/43604761386) — **SUCCESS**; the new `W128 CELIKOM launch paths stay non-elevated` step passed.

The guard protects the reviewed launch paths against a future explicit elevation regression. It cannot identify or suppress a prompt raised by Yandex, Windows, a driver, or another third-party process.

## What remains unknown

This audit does **not** identify the prompt the owner saw. It does not prove that the prompt came from Yandex, Windows, CELIKOM, or a third party, and it is not evidence that the prompt was harmless or malicious. A prompt can originate from an executable or updater outside the reviewed CELIKOM launch paths.

To identify it safely, the remaining evidence is the exact prompt screenshot/title/publisher and a process/resource snapshot taken only if the issue recurs and it is safe to do so. Do not grant administrator rights to an unknown prompt for testing. Do not request elevation as a workaround.

## Issue status

- #53 remains OPEN.
- W120's CELIKOM-process CPU/RSS/event-loop instrumentation remains useful but cannot identify load from Brave, Yandex, GPU drivers or other processes.
- Owner Task Manager CPU/RAM/GPU evidence and the exact prompt publisher are still required before attributing the system slowdown or elevation request.
- No code change or runtime test is claimed by this audit. No installer was built or delivered.
