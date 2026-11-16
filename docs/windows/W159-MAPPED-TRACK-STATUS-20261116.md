# CELIKOM Windows W159 — mapped-track status consistency (16 November 2026)

## Scope

Continue only the existing CELIKOM Windows application in `manufact-test/nomusic`, branch `main`. This is a UI-state/copy correction after the owner's W158 0.24.40.0 / native 0.24.31 acceptance. Do not restart the VPN/audio work or change architecture.

## Owner result from W54 diagnostics and manual VPN check

Owner reports that switching the VPN no longer interrupts the already-playing CELIKOM replacement: the same song continues, without an audible pop or an unnecessary replacement restart. This is manual owner listening evidence; diagnostics do not independently prove audible output.

Two W54 diagnostic captures were supplied:
- 2026-11-16 07:51:10 UTC
- 2026-11-16 07:56:04 UTC
- App 0.24.40.0; native module 0.24.31; baseline `W54_GAIN_VARIANT_AND_W53_PERFORMANCE_EXPORT_SAFE`.

The captures record multiple `SOURCE_ACTIVE_REPLACEMENT` decisions, including tracks `42498653`, `85025192`, `144530503`, `50163040`, `27323616`, and `1944599`. They also record original-source decisions for other tracks. During VPN route changes the native path records `SOURCE_HELD`, `SOURCE_KEPT`, `ACTIVE_ENTITLEMENT_RECOVERED`, and `NATIVE_ROUTE_RECOVERY_RESUMED`. A short entitlement network error/suspension occurs during route churn and then recovers. The owner confirms the music continues during this sequence.

No CORS failure, native audio 403, decoder error, Electron event-loop stall, high memory or high CPU was observed. Some passive player network requests fail, but the diagnostics explicitly state that network/preload events are not proof of decoded or audible playback.

### Diagnostic limits

Both captures report:
- `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`
- `PlayerAudibleEventObserved=false`
- `NativeDecoderUrlPropertyObserved=false`
- `NativeMediaUrlExactMatchObserved=false`

Do not claim that these diagnostics prove the audible source. They support the route-hold/recovery behavior and the owner's manual report remains the evidence for uninterrupted sound.

## W159 defect

The compact popup and main window used different wording for the same current-track state:
- After VPN recovery, the popup could fall back to the neutral availability label `Версия CELIKOM доступна`.
- After Next, when the current track had an accepted mapping but no exact decoder URL proof, the same popup showed `Источник текущего трека не подтверждён` and the header could show `Ожидаем подтверждения`.

The cause was a presentation branch that treated `NATIVE_MAPPING_ACCEPTED` / `SDK_MAPPING_ACCEPTED` as a pending/error-like message even though the current track's CELIKOM version was already available and mapped. The source-proof safeguard itself was not the bug.

## W159 implementation

- Centralized the neutral availability and service-enabled copy in `CompactPlaybackPresentation`.
- A current PLAYING track with an accepted CELIKOM mapping now consistently displays `Версия CELIKOM доступна` in both compact and main UI.
- The header/service state now remains `Сервис включён`, instead of switching to `Ожидаем подтверждения` after Next.
- Removed the mapped-track false warning from both UI surfaces.
- Kept the availability state neutral/secondary. `Подмена активна` and the accent color remain gated behind the existing exact current native decoder proof. A mapping, server availability, passive network traffic or a VPN continuity hold is not promoted to decoder proof.
- No changes to VPN route recovery, native host/renderer behavior, playback, Yandex files, account, entitlement or updater.

## Files changed

- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion/MainWindow.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`

Focused W159 regression asserts that mapped current-track state remains neutral and uses the stable availability/service copy, while remaining distinct from exact active-replacement proof.

## Checkpoints

- Exact pre-W159 rollback: `backup/windows-main-pre-w159-mapped-source-status-20261116` @ `0e1de874bc15c401fcceb206511d8cb8f4005d80`.
- W159 application-source checkpoint before documentation: `09fca7a0f7fb9b0f7fe4a436978c48968054a0fa`.
- Main CI run: [43828118274](https://github.com/manufact-test/nomusic/actions/runs/43828118274) — pending at documentation time.
- Windows integration CI run: [43828118192](https://github.com/manufact-test/nomusic/actions/runs/43828118192) — pending at documentation time.

No new owner installer is included in this checkpoint. After both required CI workflows pass, bump only the Windows application/package version to 0.24.41.0 (native remains 0.24.31) and create exactly one W159 internal owner-review package. No intermediate installer, ZIP or release.
