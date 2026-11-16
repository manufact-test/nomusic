# CELIKOM Windows — active handoff W165 (16 November 2026)

**Status: W165 0.24.47.0 source, Main CI, Windows integration CI and W20 internal owner-review package all passed. Package bytes and SHA256 checksums verified. Owner manual check of the two UI details is pending. VPN/audio behavior is accepted and frozen.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- Code checkpoint: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`.
- Handoff/package-request commit: `a9020fc5d40b5118388571b917e2997c965ee62e`.
- Exact pre-W165 rollback: `backup/windows-main-pre-w165-owner-spacing-status-copy-20261116` @ `a8d9d43de68e03553acbbb21d09650c23ff64807`.
- App: **0.24.47.0**, native module **0.24.31**.
- Full handoff: `docs/windows/W165-OWNER-TRACK-SPACING-AND-ACTIVE-STATUS-20261116.md`.

## Owner acceptance carried forward from W164

The owner installed 0.24.46.0 and toggled VPN repeatedly while CELIKOM music was playing:
- Music continued without interruption.
- The UI did not flash extra recovery/status text.
- The VPN/audio behavior is accepted.

**Do not modify VPN recovery, entitlement checks, native audio, source routing, W23 host or renderer. Do not repeat broad VPN/audio testing.**

## W165 changes — UI only

1. Split the incorrectly shared bottom spacing:
   - `TrackStatusBottomSpacingPx = 18` remains for the disabled/placeholder state when there is no current track row below it.
   - `ActiveTrackStatusBottomSpacingPx = 8` is used below the current track's version-status row. This restores the previous compact gap and prevents the new 18 px idle-state spacing from leaking into active playback.
2. Active verified-version wording is now **«Играет версия CELIKOM»**.
3. The green gate is unchanged: it still requires exact current native decoder-source proof. Mapping, source-held events, file-info acceptance, HTTP media bytes or a generic PLAYING state do not qualify.

## Important unresolved proof limitation

The latest owner W54 diagnostic from 0.24.46.0 reports:
- Native integration and bridge active.
- `PlayerCelikomSourceLeftObserved=false`.
- `PlayerNativeVolumeDropObserved=false`.
- `ElectronEventLoopStallObserved=false`.
- `NativeDecoderPropertiesObserved=true`, but `NativeDecoderUrlPropertyObserved=false`.
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`.

This explains why the label remains neutral/gray: the current Yandex CDP observer sees Media properties but not the `kUrl` property needed to match the current decoder to the CELIKOM resource. The code already paints the active label green when that exact proof arrives; changing CSS or forcing mapping-only green would be misleading. The new short wording is ready for that verified state, but the supplied diagnostic does not establish that state.

If the owner later requests a green label while hearing CELIKOM, the next separate task is a focused native decoder-observer compatibility investigation for the current Yandex build. Do not weaken the proof gate and do not change the audio pipeline as a shortcut.

## Verification

- Main CI [43885551310](https://github.com/manufact-test/nomusic/actions/runs/43885551310) — **SUCCESS**.
- Windows integration CI [43885551218](https://github.com/manufact-test/nomusic/actions/runs/43885551218) — **SUCCESS**.
- W20 safe installer staging [43885551217](https://github.com/manufact-test/nomusic/actions/runs/43885551217) — **SUCCESS**.
- W20 compiled source with warnings as errors, ran W15/native tests, checked PE version and anti-downgrade, passed disposable Windows install/uninstall smoke, and packaged the exact installer into one ZIP with SHA256 checksums.

## Owner-review package

One internal unsigned owner-review build only:
- Installer: `CELIKOM-W165-OWNER-SPACING-STATUS-02447-UNSIGNED.exe`.
- ZIP: `CELIKOM-Windows-0.24.47.zip`.
- Artifact ID: `14235136060`.
- Artifact: https://github.com/manufact-test/nomusic/actions/runs/43885551217/artifacts/14235136060
- EXE SHA256: `8a8687771096ffd38d52454832e1ce6987239b2d3db9ec6c597590aa03c9bed3`.
- ZIP SHA256: `ed270f45d073e18b3350b192d995c5b45b7b95d839a38f8fa3229d5cb6294d32`.
- Expires: 26 November 2026, 14:27:45 UTC.
- Package is internal and unsigned; no production release, signing or deployment.

## Owner manual check

Install **0.24.47.0 over 0.24.46.0** and check:
- In the disabled/connection-placeholder state, the additional bottom breathing room remains.
- While a current track, artist and version status are shown, the gap below the status is back to the previous smaller 8 px spacing.
- If exact decoder proof is available, the green label reads **«Играет версия CELIKOM»**. If the observer still cannot see `kUrl`, the label correctly remains neutral; do not treat that as a spacing regression.
- No VPN/audio retest is required unless the owner observes a real regression.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, W23 native host/renderer, audio engine, VPN recovery, entitlement authority, source routing, updater architecture, production signing or deployment. No broad audits or intermediate installers.
