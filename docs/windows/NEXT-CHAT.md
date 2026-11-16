# CELIKOM Windows — active handoff W162 (16 November 2026)

**Status: W162 0.24.44.0 source CI, Windows integration CI and one internal W20 owner-review package are complete. Waiting only for the owner's manual UI check.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W162 source checkpoint: `b6aa1dee19cd2862f23c9b656210f54db12cdfe9`.
- W20 request/package commit: `a3a3506a1acea21a0b96d7ec7ec3de9b804596f8`.
- Pre-W162 rollback: `backup/windows-main-pre-w162-title-status-polish-20261116` @ `5c6e5d902941bb931039aa54a26cc307c09b296f`.
- Version: **0.24.44.0**, native module **0.24.31**.
- Full implementation and diagnostic notes: `docs/windows/W162-OWNER-UI-METADATA-STABILITY-20261116.md`.

## W162 result

- Track title and artist now come from one lock-consistent playback snapshot.
- Empty same-track heartbeat fields no longer blank previously received title, artist or duration. A real track change replaces all previous metadata.
- Compact and main UI refreshes consume the same snapshot; compact title/artist/status labels are only assigned when their text changes.
- Exact confirmed CELIKOM decoder source: green **«Играет полная версия CELIKOM»**.
- Mapping-only availability remains gray **«Версия CELIKOM доступна»**. The exact decoder-source proof gate was not weakened.
- **«Пауза»** remains green while the service connection is confirmed.
- No changes to the VPN/audio path, W23 host/renderer, Yandex files, entitlement authority, updater/P-256, backend, Android or browser extension.

## CI and internal owner-review package

- Main CI, source checkpoint: run `43863680868` — SUCCESS.
- Windows integration CI, source checkpoint: run `43863680894` — SUCCESS.
- Main CI, W20 request commit: run `43864166741` — SUCCESS.
- Windows integration CI, W20 request commit: run `43864166849` — SUCCESS.
- W20 safe installer staging: run `43864166748` — SUCCESS.
- Artifact ID: `14224093499`.
- Artifact name: `CELIKOM-Windows-internal-stage-a3a3506a1acea21a0b96d7ec7ec3de9b804596f8`.
- Installer: `CELIKOM-W162-TRACK-STATUS-AND-METADATA-STABILITY-02444-UNSIGNED.exe`.
- ZIP: `CELIKOM-Windows-0.24.44.zip`; contains the exact same installer.
- `SHA256SUMS.txt` is included in the artifact.
- Uploaded artifact ZIP SHA256: `342e28febb81b5304cfb793a7da24405f85a683901237f56921f34f4878341c4`.
- Artifact expires: 26 November 2026, 12:13:49 UTC.
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43864166748
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43864166748/artifacts/14224093499

The W20 run passed source compilation with warnings as errors, native preflight, native image/crash-recovery tests, updater ZIP/version/anti-downgrade checks, disposable per-user install/uninstall smoke, and exact EXE+ZIP+SHA256 packaging. The artifact is internal and unsigned; this is not a production release.

## Owner's manual verification

1. Install 0.24.44.0 over 0.24.43.0.
2. Check that title and artist remain stable when hiding/restoring the compact window and opening the full window.
3. Check the active green label when exact CELIKOM decoder proof is present, the gray mapping-only label, and the green pause label.
4. VPN recovery was already manually checked by the owner and reported smooth; do not repeat broad VPN testing unless a regression appears.

Important: the latest W54 diagnostic showed `NativeDecoderUrlPropertyObserved=false` and `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`. Therefore mapping-only must remain gray even if a replacement is available. If the owner hears the full version but the status remains gray, investigate the missing exact decoder proof; do not simply relax the evidence gate.

Do not request the user to resend previous requirements. The W162 document contains the full reasoning and exact changes.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, updater/P-256 or architecture changes. No broad audits, speculative audio changes, unnecessary tests or intermediate packages. Preserve the pre-W162 rollback branch.
