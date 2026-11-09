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

## W20 CI confirmation (finished)

- [Run 42596579243](https://github.com/manufact-test/nomusic/actions/runs/42596579243) **SUCCESS** at code SHA `9009024a9f06506775c1a6757f5c3cb413049be9` (Windows Server 2022 hosted runner).
- Native app built with warnings-as-errors; `W15_NATIVE_CONTRACT_PASS 43` including read-only negative host cases.
- `W20_STAGE_PACKAGE_POLICY_PASS: OWN_EXECUTABLE_ONLY` and `W20_INTERNAL_INSTALL_UNINSTALL_PASS_NO_YANDEX_FILES` confirmed. Silent install + uninstall of CELIKOM only. No official Yandex installed on this runner, so this is **not** a before/after fingerprint check against a live Yandex installation.
- Staging artifact: `CELIKOM-W20-INTERNAL-UNSIGNED-NOT-AUDIO` (GitHub Actions artifact ID `13664066318`). Installer SHA256 `8fc7e79b0a137d2558c6009809060e05facfcb7f3d23498b319ad1f2181e3d65`.
- Do **NOT** send artifact to owner or consumers: unsigned, no native-audio E2E, no contract clearance, not a production-grade product.
- Existing W15 preview workflow also succeeded at code commit `d19d8852`: [run 42596230139](https://github.com/manufact-test/nomusic/actions/runs/42596230139). The older W15.2 owner smoke remains previous evidence, not a W20 owner audio test.

