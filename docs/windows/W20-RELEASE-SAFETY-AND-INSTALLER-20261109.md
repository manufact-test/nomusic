# W20 — safe single-installer staging and actual commercial go/no-go (2026-11-09)

## Verified previous evidence

- W15.2 Companion source built and its window launched on owner's Win10.
- W18 imported the SDK addon into PulseSync in disposable Windows and launched
  modified Yandex. **No real track audio, Pause/Seek/Next was tested.**
- W17/W18's PulseSync patch invalidated the original Yandex EXE Authenticode
  signature: `HashMismatch`. Restoring original bytes restored a valid signature.
- A valid new signature on our CELIKOM executable does not repair a patched
  third-party Yandex EXE. Do not bypass Defender, SmartScreen or protection.

## Commercial/legal constraints verified against primary source texts

1. PulseSync Client's current EULA at
   https://github.com/PulseSync-LLC/PulseSync-client/blob/main/LICENSE,
   particularly section 3.1, prohibits commercially copying, modifying,
   redistributing or creating derivatives without the licensor's written
   permission; §3.3 protects PulseSync naming. PulseSync-mod's MIT license
   https://github.com/PulseSync-LLC/PulseSync-mod/blob/main/LICENSE
   is **not** a license for PulseSync Client.
2. The Yandex Music application EULA, published 2026-04-03, explicitly covers
   Windows:
   https://yandex.ru/legal/music_mobile_agreement/ru/
   Clauses 4.1–4.3 restrict client modification and commercial redistribution
   without Yandex's written consent, subject to statutory exceptions.
3. The pinned `@pulsesync/addon-sdk` 0.18.0 package is separately listed on npm as **GPL-3.0-or-later** (https://www.npmjs.com/package/@pulsesync/addon-sdk). The consequences for bundling or distributing the compiled CELIKOM addon require a separate GPL compliance review; this package license does not grant distribution rights to the proprietary host.
4. As a result, neither a bundled PulseSync build nor our own unsigned modified
   Yandex client is a permitted, ready-to-distribute solution on currently
   verified evidence. A no-modification runtime attach technique would still
   require contractual/legal assessment; no official source-provider API has
   been evidenced. Obtain specialist legal review, not assumptions.

This is a deployment gate, not a claim that all independent software integration
is illegal. Specific signed permissions/agreements or a documented supported
API can reopen it.

## New W20 implementation scope

- The existing native W15 code receives a **read-only** Yandex installation
  probe for the exact tested version `5.126.1.0`: checks version, WinVerifyTrust
  EXE signature and pinned original ASAR SHA256. Does not repair, patch,
  launch, read profiles, capture audio or request login.
- W20 builds a **single internal Windows installer** using Inno Setup,
  installing only the CELIKOM-owned self-contained executable without elevation,
  foreign installers or modifications. Start-menu entry and standard uninstall
  are provided. A Windows CI smoke installs/uninstalls CELIKOM in the isolated
  runner and checks that it did not create Yandex install files.
- Release policy gate defaults to **closed**. Its Release mode always fails until
  documented, approved rights/adapter, real audio E2E, security/Win10/11,
  rollback and signing exist. The resulting unsigned installer is a developer
  staging artifact only and must NEVER be sent as an operational music product.

## What W20 does NOT solve

No verified native audio adapter, signed untouched-client source interception,
PulseSync commercial permission, Yandex license clearance or real user
Play/Pause/Seek/Next acceptance. Nor does the W20 installer restore foreign
files: it never touches them. The original W15.2 backup remains unchanged.

**Next acceptance gate:** secure a licensable supported adapter (including
written rights where required), then prove one approved track plus native
Pause/Seek/Next/fallback in an isolated developer-controlled interactive
Windows with a legitimate test music account. Only then connect the W20
consumer journey and hand the owner a meaningful one-click candidate.

No Android, browser extension, server or production changes.

## W20 CI confirmation (finished)

- [Run 42596579243](https://github.com/manufact-test/nomusic/actions/runs/42596579243) **SUCCESS** at code SHA `9009024a9f06506775c1a6757f5c3cb413049be9` (Windows Server 2022 hosted runner).
- Native app built with warnings-as-errors; `W15_NATIVE_CONTRACT_PASS 43` including read-only negative host cases.
- `W20_STAGE_PACKAGE_POLICY_PASS: OWN_EXECUTABLE_ONLY` and `W20_INTERNAL_INSTALL_UNINSTALL_PASS_NO_YANDEX_FILES` confirmed. Silent install + uninstall of CELIKOM only. No official Yandex installed on this runner, so this is **not** a before/after fingerprint check against a live Yandex installation.
- Staging artifact: `CELIKOM-W20-INTERNAL-UNSIGNED-NOT-AUDIO` (GitHub Actions artifact ID `13664066318`). Installer SHA256 `8fc7e79b0a137d2558c6009809060e05facfcb7f3d23498b319ad1f2181e3d65`.
- Do **NOT** send artifact to owner or consumers: unsigned, no native-audio E2E, no contract clearance, not a production-grade product.
- Existing W15 preview workflow also succeeded at code commit `d19d8852`: [run 42596230139](https://github.com/manufact-test/nomusic/actions/runs/42596230139). The older W15.2 owner smoke remains previous evidence, not a W20 owner audio test.

