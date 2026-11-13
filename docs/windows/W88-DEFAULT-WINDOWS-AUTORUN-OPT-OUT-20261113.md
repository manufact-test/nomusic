# CELIKOM Windows W88 (0.24.32 TEST) — default startup with Windows, user can opt out

Owner corrected requirement on 2026-11-13: **the user should NOT need to enable autostart manually**. CELIKOM starts automatically in the system tray after Windows login by default; anyone who wants to disable it can use tray menu "Отключить запуск с Windows" (also OS startup apps settings if desired). User's explicit opt-out must persist across new runs and in-place CELIKOM updates.

## Exact base and backups

- Baseline: W87 0.24.31 TEST CI green, `experiment/windows-w87-autostart-quiet-repair-20261113` @ `9acee0c2ca33c7d3ca2ed940abacc57a037ca1d3`.
- Immutable pre-change backup: `backup/windows-w88-pre-default-autorun-exact-20261113`.
- Work: `experiment/windows-w88-default-autorun-optout-20261113`.
- W87 0.24.31 existing Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.31-AUTORUN-TEST.exe`.
- **No changes to native audio** host.cjs or renderer.js. Live owner audio QA still required.

## Implementation

- `WindowsLaunchSettings.EnsureFirstLaunchDefault(Application.ExecutablePath)` called before tray context menu init, registering HKCU-only `Run\CELIKOM` entry with `--background` **on first launch**.
- The `HKCU\Software\CELIKOM\Windows\AutoRunConfigured` DWORD sticky one-time flag means subsequent launches/upgrades do not overwrite the user's intentional opt-out. `TrySetRunAtLogin` saves flag after confirmed on/off changes. Without an explicit choice, default is ON.
- Dynamic tray menu reflects actual Run registry entry, shows **Отключить запуск с Windows** while enabled and **Включить запуск с Windows** when off. No startup screens, Yandex auto-launch, permission elevations, or login prompts on Windows boot.
- Auto-resume stays independent of enrollment: requires user's prior `Старт` intent, same signed-in installation/account, valid freshly rechecked server entitlement and official native host safety; explicit `Стоп` survives reboot. Failure stays off.
- Unit tests `ShouldEnableDefault(false)==true`, `ShouldEnableDefault(true)==false`; all W87 security, login, file integrity and native audio regression tests preserved.

## Release

- Candidate Windows 0.24.32; CI `.github/workflows/windows-w88-default-autorun-installer.yml` includes in-place 0.24.31 → 0.24.32 install with unchanged DPAPI and native audio assets.
- Exact artifact, SHA256, Library location and owner field QA: pending successful CI.
