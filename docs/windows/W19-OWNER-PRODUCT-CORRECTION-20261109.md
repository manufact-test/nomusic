# W19 owner correction — product acceptance, evidence, and non-goals (2026-11-09)

## What the owner actually needs

A regular Windows app called **CELIKOM** installed normally by any consumer. The customer runs it together with **desktop Yandex Music**. Yandex retains its own user sign-in, library, radio, queue, actual audio playback, pause, seek, Next, volume and media keys; CELIKOM injects/changes **only approved song source** in that same Yandex playback pipeline and handles its own CELIKOM membership/catalog. No second playback engine, no substitute web page, no in-app Yandex password collection.

The owner permits studying mods **as implementation details** but refuses a customer setup requiring Windows Sandbox, enabling Windows optional features, Hyper-V, VMware, terminal commands, developer tools, manual installation of PulseSync, separate players or disabled security. Do not interpret the earlier approval of **internal isolated research** as approval for a consumer journey requiring sandbox.

Target consumer journey: download normal branded CELIKOM installer → install and, if necessary, transparently approve supported integration → open Yandex + CELIKOM → play normally in Yandex; no extra work. Compatibility guard, backup and verified rollback are part of the installer, not end-user troubleshooting. Never promise a security-warning-free Windows installer until demonstrated with normal protection.

## What happened in W19 on owner's real PC

- A test-only `CELIKOM-W19-Sandbox-Audio-Test.zip` was provided, containing `START-W19-WINDOWS-SANDBOX.cmd`. **Its scripts/ZIP were conversation artifacts, not a product release and not a verified runnable Windows Sandbox test**.
- User executed launcher. Screenshot: `Windows Sandbox is not available on this Windows installation. No system setting has been changed. Nothing was installed.` Real Windows audio **NOT TESTED**. The launcher exited safely.
- Screenshot of `winver`: **Windows 10 Pro 22H2, build 19045.6456**. Pro supports optional Sandbox only when enabled and machine meets prerequisites; the feature was absent/disabled. Assistant suggested enabling it through `optionalfeatures.exe` and rebooting.
- Owner rejected the entire user-workflow approach; do **not** ask to enable Sandbox or retry W19; do **not** touch the installed official Yandex without a separate explicit test consent.
- Owner has already verified W15 EXE window opens (SmartScreen had flagged unknown publisher). That is **not** a proof of source integration.

## Previously verified, previously mistaken

- W17 genuine mod install via PulseSync occurred with Defender realtime ON. **But it changed the signed Yandex EXE; signature invalidated (`HashMismatch`)**, restored afterwards. This means **"sign CELIKOM and all warnings disappear" is technically unjustified**.
- W18 authentic addon import and modified Yandex process start succeeded, yet **no playable source or seek/Next/audio in the installed Yandex was ever proven**.
- W15.2 companion is a **native preview**, not a finished product/installer. The addon bridge uses real CELIKOM auth/Range flow design but end-to-end behavior remains unknown.
- Tests on GitHub hosted **Windows Server 2022** cannot establish all Windows 10 Defender/SmartScreen or licensed music behavior.
- PulseSync Client commercial license and Yandex modification/distribution permissions are not settled. PulseSync-mod's MIT license alone is insufficient.

## Mandatory course correction

**Do not make the user do developers' integration work.** The next chat should independently work through the technical and commercial viability of a real one-install UX, do code and automated tests in GitHub, use a suitable disposable developer test environment, and request exactly one manual owner check only when there is a meaningful, safe, almost-complete installation candidate. If that cannot yet be built or securely distributed, explain the specific blocker and realistic alternative; don't issue another sandbox launcher, fake no-go, empty UI build or invented guarantee. Do not simply revert to a browser-extension-only solution: native Yandex Music playback on Windows is the primary product invariant.
