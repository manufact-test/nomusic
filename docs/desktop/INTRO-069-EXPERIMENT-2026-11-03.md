# Desktop 0.4.69 — parallel preparation experiment

## Reference accepted by owner

On 2026-11-03 owner accepted desktop 0.4.68 as the new reference and authorized further isolated experiments. It remains available as ZIP SHA-256 `911d5c9d4c5557901e61b7f07e4531bbabc22b51e38f113b9cfc87dcf4c5cc40`, 2,485,658 bytes, persisted file `libfile_81880ff627ec819190f0dc9f3809c9ef` (version 1). Frozen branch `archive/desktop-0.4.68-accepted-20261103` points at `43f9ade7b8e7bb1668818f10a7086efd940bffd6`. Earlier 0.4.67 rollback remains untouched.

The owner heard partial recovery of the first syllable of тело. Diagnostic 20261103-185231 uses 0.4.68, latest startupHistory contains one join: preparation 292ms, resolve/preparation phase 220ms, audio preparation 65ms, master position at activation 361ms. This is not acoustic zero latency. Prior 1187ms preparation was in different network conditions. Do not attribute the entire difference to the code change.

## Research, without Android modifications

Read Android NEXT-CHAT and actual NativeApi/ReplacementEngine from `feature/android-0385-test15-permissionless-recovery-20261103`. Test.15 is the accepted mobile foundation; Test.16/17 were rejected and reverted. Relevant principles: prepare work early, current audio priority, no duplicate downloads, keep authoritative identity/access checks and frozen seek/ACK intact. This desktop experiment does not copy Android timing constants or control audio through MediaSession. No Android files, APK, signing, server, website, live deployment, stable feature/api-range or accepted audio synchronization code changes.

## Implemented desktop scope

- Existing fresh `auth/me` and entitlement GET checks overlap. Neither result alone grants authority. The playback callback still runs only after both succeed. Keep sessionVersion and transportEpoch fences; after access-token rotation, discard the old-token entitlement result and require another entitlement with the rotated token. Early rejection is reflected/handled to avoid orphaned promise errors. No authority cache, no skipped check, no replayed POST, no changed diagnostics/upload permission checks.
- Worker can warm PUBLIC `/config` while the above checks run. This request carries no access token. Only after authorized access and validated public config may signed `/resolve` execute; audio starts through unchanged controller/player admission. Config maintenance/disabled policy also overrides a cached positive mapping. This does not preload the next song or start any speculative audio request.
- Public configuration reads coalesce while in flight. Network reset fences late policy responses and clears policy state. Existing bounded TTL, config shape/minimum-version checks and URL validation remain enforced.
- Preserve 0.4.68 first 64 KiB MP3 range, all seek/pause/guard/decoder behavior and existing twelve-join diagnostics. Version becomes 0.4.69.
- Deterministically fix an existing test fixture's clock for an exact synthetic modulo-seek assertion (a real 1ms scheduler advance produced 2.001 vs 2 seconds). Production sync behavior is untouched.

## Validation and owner check

Dedicated `desktop-intro-069.yml` runs desktop regressions, existing native Chrome synthetic MP3/M4A playback, delayed loading/seek, pause and original restoration, manifest validation, lint and configured desktop ZIP build. Check actual run outcome before claiming browser validation.

New deterministic gates prove auth/me, entitlement and public config all start before any completes; descriptor waits for all; denied cached entitlement never dispatches resolve; logout fences late entitlement; rotated bearer is rechecked; public config is single-flight and network-reset fenced; maintenance blocks positive-cache reuse. These tests establish request ordering and authority boundaries, not perceptual improvement or universal compatibility.

After one install: тело first word, several Next transitions, pause and seek; export one diagnostic at end. Remaining native 100ms initial offset, audio-file alignment and a cold unidentified track can still lose initial audio; this experiment does not guarantee zero missing phonemes. Next-track prefetch/decoder reuse is a separate future investigation requiring reliable next-track identity, cancellation, account scope, expiry and current-track priority, not enabled speculatively in this release.

Rollback: stop playback, replace files in the existing unpacked extension folder with preserved 0.4.68, reload extension, refresh Yandex tab, start. Do not uninstall extension or clear account data.

## Verified delivery

- 339 desktop tests PASS locally and in GitHub; manifest validation and repository lint PASS.
- GitHub run `41699592784` SUCCESS, including native Chrome synthetic MP3/M4A playback, pause, delayed seek and original restoration checks. These checks validate functioning playback boundaries, not the opening consonant on the owner's actual song.
- Configured ZIP `celikom-extension-0.4.69.zip`: 2,486,069 bytes; SHA-256 `ff53cc6db565a6502484d672eebf462a1543b6d1879d5ac46ef359e8b6394dd6`.
- Persisted delivery `libfile_a7f2ec6afad48191891127928a656d69`.
- Owner acoustic check PENDING; 0.4.68 remains accepted reference.
