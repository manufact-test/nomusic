# CELIKOM Windows — W165 owner track spacing and active status

Date: 16 November 2026  
Product: CELIKOM Windows only  
Status: **source, Main CI, Windows integration CI and one internal W20 owner-review package all passed. Owner manual UI check pending.**

## Source of truth and rollback

- Repository: `manufact-test/nomusic`
- Working branch: `main`
- W165 code checkpoint: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`
- Handoff/package-request commit: `a9020fc5d40b5118388571b917e2997c965ee62e`
- Exact pre-W165 backup: `backup/windows-main-pre-w165-owner-spacing-status-copy-20261116` @ `a8d9d43de68e03553acbbb21d09650c23ff64807`
- App version: **0.24.47.0**
- Native module: **0.24.31**
- Previous owner-tested version: **0.24.46.0**

## Owner acceptance of W164 VPN/audio behavior

The owner reports that after installing 0.24.46.0 and repeatedly toggling VPN while CELIKOM music played:
- The CELIKOM version continued playing.
- No extra text flashed or appeared during the route changes.
- The VPN/audio behavior is now good and accepted.

This is a hard boundary for W165: **do not touch audio, native source routing, VPN recovery, entitlement checks, W23 host/renderer or Yandex files.** No broad VPN/audio audit is needed.

## Latest owner diagnostic

File: `Вставленный текст(20261116-141738).txt`  
Capture: W54, generated 2026-11-16 14:17:16 UTC  
App: 0.24.46.0; native module: 0.24.31.

Relevant summary fields:
- `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, `SignedIn=true`.
- `PlayerCelikomSourceLeftObserved=false`.
- `PlayerNativeVolumeDropObserved=false`.
- `ElectronEventLoopStallObserved=false`, `ElectronMemoryHighObserved=false`, `ElectronCpuHighObserved=false`.
- `NativeDecoderPropertiesObserved=true`.
- `NativeDecoderUrlPropertyObserved=false`.
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`.

The capture records route-change/recovery transitions. This is consistent with the owner's manual observation that music continued. It is not a decoder-audibility proof: the diagnostic itself explicitly says that network/preload events, accepted mapping, file-info responses and source-held markers do not prove the audible source.

## Root cause: spacing regression

W163 introduced `TrackStatusBottomSpacingPx = 18` to give the disabled/placeholder track message the lower breathing room it previously lacked.

The same constant was also applied below `_compactVersionStatus`, replacing the previous 8 px gap for a real current track. This unintentionally enlarged the active track/status-to-Account gap.

W165 separates the two cases:
- `TrackStatusBottomSpacingPx = 18` remains for the disabled/placeholder state where there is no artist/version-status row.
- New `ActiveTrackStatusBottomSpacingPx = 8` is used below the current track's version-status row.
- Existing track/title/artist heights, container dimensions and other row gaps are unchanged.

This is a local row-gap correction, not a global padding or container change.

## Root cause: green status does not reach its existing condition

The UI already has a green branch for the active version. It is not a missing color assignment.

The branch requires all of the following:
- current track playback state is PLAYING;
- source is `ACTIVE_REPLACEMENT`;
- native status is `NATIVE_SOURCE_VERIFIED`;
- approved CELIKOM version presence.

The native host produces `NATIVE_SOURCE_VERIFIED` only when its current decoder observer matches the current Yandex track to the expected CELIKOM resource through CDP `kUrl` and playing-state evidence.

The W54 capture sees Media properties but does not see `kUrl`. Therefore the host continues to report mapping/availability, and the UI correctly remains neutral with `Версия CELIKOM доступна`. This is why prior attempts to change the UI wording/color did not change the screenshot: the active branch was never reached.

Do not fake green by treating a file-info mapping, preload, HTTP 206, `SOURCE_ACTIVE_REPLACEMENT` log, source-held event or generic PLAYING state as decoder proof. If the owner later wants to pursue green status on this Yandex build, make it a separate, focused decoder-observer compatibility task. Do not modify audio playback or weaken the proof gate.

## W165 implementation

1. `CompactPlaybackPresentation.ActiveVersionMessage` now reads **`Играет версия CELIKOM`**.
2. Added `ActiveTrackStatusBottomSpacingPx = 8`.
3. `LayoutCompact` uses the 8 px constant below `_compactVersionStatus`; the 18 px constant remains for idle/placeholder spacing.
4. Existing green-color logic and `PlaybackSourceEvidence.Verified` remain unchanged.
5. App, supervisor and installer metadata bumped to 0.24.47.0 / 0.24.47.
6. Added/updated W15 assertions for the exact wording and the separate 18 px / 8 px spacing contracts.

## Changed files

- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Celikom.UpdateSupervisor.csproj`
- `windows-companion/w20/installer/CELIKOM.iss`
- `windows-companion/w20/owner-review-package-20261114.request`
- `docs/windows/NEXT-CHAT.md`
- This W165 handoff.

No W23 native host/renderer, native audio, VPN, entitlement, source-resolution, backend, Android, browser extension or Yandex files were changed.

## Verification

- Main CI [43885551310](https://github.com/manufact-test/nomusic/actions/runs/43885551310) — **SUCCESS**.
- Windows integration CI [43885551218](https://github.com/manufact-test/nomusic/actions/runs/43885551218) — **SUCCESS**.
- W20 safe installer staging [43885551217](https://github.com/manufact-test/nomusic/actions/runs/43885551217) — **SUCCESS**.
- W20 passed source compile with warnings as errors, W15/native tests, W23 native bundle/diagnostic contracts, PE version and anti-downgrade validation, disposable Windows install/uninstall smoke, and exact EXE/ZIP packaging.

## Owner-review artifact

One internal unsigned owner-review package:
- Installer: `CELIKOM-W165-OWNER-SPACING-STATUS-02447-UNSIGNED.exe`
- ZIP: `CELIKOM-Windows-0.24.47.zip`
- Artifact ID: `14235136060`
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43885551217
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43885551217/artifacts/14235136060
- EXE SHA256: `8a8687771096ffd38d52454832e1ce6987239b2d3db9ec6c597590aa03c9bed3`
- ZIP SHA256: `ed270f45d073e18b3350b192d995c5b45b7b95d839a38f8fa3229d5cb6294d32`
- Artifact expires 2026-11-26 14:27:45 UTC.
- Internal unsigned review only; no production release, signing or deployment.

## Owner review

After installing **0.24.47.0 over 0.24.46.0**, verify:
- Disabled/connection-placeholder state retains the larger lower breathing room.
- A playing track with title, artist and version status has the previous smaller 8 px gap before Account.
- If exact decoder proof is available, the green label reads **«Играет версия CELIKOM»**. If the observer still cannot see `kUrl`, the neutral availability label is expected.
- No VPN/audio retest is required unless a real regression appears.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, W23 host/renderer, audio engine, VPN recovery, entitlement authority, source routing, updater architecture, production signing or deployment. No broad audits or intermediate installers.
