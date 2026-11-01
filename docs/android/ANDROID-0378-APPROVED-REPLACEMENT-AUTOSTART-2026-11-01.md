# CELIKOM Android 0.3.78 — automatic playback of approved replacements

Date: 2026-11-01  
Status: staging candidate; CI and physical HONOR listening acceptance pending. After native validation, the owner-created staging PR or a direct staging-branch push calls the original signing pipeline in explicit test-only mode and uploads a signed APK artifact. PR signing is restricted to this repository's own staging branch and repository owner; the Hostinger stable manifest and release directory are not touched.

## Baseline

- Production Android: 0.3.77, versionCode 78.
- Production source base: `f1f083ce06ada77849053dc07951cfa1fa1d7562`.
- Candidate Android: 0.3.78, versionCode 79.
- Staging branch: `feature/android-078-approved-replacement-autostart-staging-20261101`.
- Original package identity, signing certificate, updater, backend and admin panel remain unchanged.

## Owner-approved behavior

- An identified unique catalogue track ID is sent to the existing live CELIKOM resolve endpoint.
- If the backend returns an approved replacement (`found=true`) and the existing audio-session/source checks pass, playback starts automatically.
- No second confirmation, confirmation button, manual retry or post-confirmation resolve is required.
- Unique fresh own-catalogue and previously learned album metadata candidates may use the same live resolve. A stale/incomplete catalogue hint is not promoted to a candidate; ambiguous or insufficient identity continues with the original.
- The backend's approved mapping and entitlement response remain the authorization boundary. The app does not play a file merely because a title matched.

## Duration safety

- Keep the existing measured-file checks and bounded 1500ms tail allowance for a unique candidate backed by a track ID.
- The 582ms, 663ms, 1354ms and 1469ms cases should proceed automatically when the server metadata and measured file satisfy the existing bounded checks.
- Differences beyond the existing bound, invalid duration metadata, wrong audio session, stale source, entitlement denial, or invalid audio continue to fail open to the original.

## Strict scope

- Removed the user confirmation gate and the corresponding Android UI button/dialog.
- No seek timing, WARM lead, gain law, crossfade duration, pause/resume, Next, buffering, audio ownership, decoder lifecycle, Media3 arbitration or output-clock algorithm was changed.
- No desktop extension, website, backend, admin panel, Hostinger deployment, stable manifest or signing identity change.

## Required verification

- Actual-engine replay: automatic ALBUM and LEARNED_METADATA paths; one live resolve per track; 582/663/1354/1469ms bounded tails; >1500ms mismatch remains rejected; stale hint remains non-playable; all historical audio regressions.
- Android API 36 full-source/Test* host gates and release-contract/archive checks.
- Physical HONOR test after the candidate is built: confirm the previously blocked approved songs now replace automatically; verify ordinary playback, pause, seek, Next and song boundaries remain unchanged.

A green CI run is not acoustic acceptance. The owner's listening test remains the final gate.

## CI and signed test artifact

- Successful validation workflow run: `41313456137` (run #306).
- Tested application source commit: `05e2158e55e876eeb44baf8c22ee2ea8b63efe1b`. The later branch commits only adjust staging workflow concurrency; application sources are unchanged.
- Actual-engine suite: 131 checks passed; long-run replay: 604 checks, 300 track changes and 15 virtual hours passed. Physical scheduling is not established by host simulation.
- Full Android API 36 source compilation and D8 succeeded. The release builder verified the original signing identity, APK v2/v3 signature, alignment, version/API, manifest boundary, unchanged catalogue assets and exact compiled addon DEX.
- Signed APK artifact: `celikom-android-0.3.78-signed-test`, GitHub artifact ID `13086328607`.
- APK SHA-256: `8ce851a48c281cbb9121dc146e455183e59d3326c0721f030133a1ce55f55457`.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Receipt explicitly records `stable_published: false`. Hostinger stable manifest and release directory were not changed.

## Owner acceptance still required

Install the signed test APK over the existing app and replay the previously blocked approved tracks. Check ordinary playback, pause/resume, seek, Next and song boundaries. Only after the owner's listening acceptance should the candidate be considered for stable release.
