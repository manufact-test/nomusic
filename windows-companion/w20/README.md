# W20 — internal Windows single-installer staging, NOT a user release

This folder is an incremental packaging and verification step on top of
`windows-companion/w15`. It deliberately does NOT claim that approved track
replacement plays inside the signed Yandex desktop application.

- `installer/CELIKOM.iss` installs only the self-contained CELIKOM-owned EXE
  per-user. The target is `%LOCALAPPDATA%\Programs\CELIKOM`, with a normal
  Programs-menu shortcut and regular Windows uninstaller. No Yandex files are
  modified or distributed. No PulseSync installer, mod or addon is bundled.
- `release-gate.ps1 -Mode Stage` checks the installer file allowlist and
  scope. `-Mode Release` intentionally fails until legal, technical,
  signature, restoration and customer E2E evidence is recorded and approved.
- `.github/workflows/windows-w20-safe-installer.yml` builds the staging EXE
  and installer on disposable Windows, performs the existing W15 tests,
  silently installs/uninstalls **only CELIKOM**, and publishes a clearly
  labeled INTERNAL-UNSIGNED CI artifact. It is not a download for customers.

**Deliberately NOT implemented:** Yandex patching, silently importing
PulseSync addons, a real source replacement without licensing, automatic
trusted publisher signing, rollback of third-party files that we never touch.

The existing W15 login/bridge window remains a developer preview. Do NOT send
this staging installer as the finished consumer product. The missing part is a
legally supportable **native audio adapter** proven with Play/Pause/Seek/Next.

See `docs/windows/W20-RELEASE-SAFETY-AND-INSTALLER-20261109.md`.
