# CELIKOM Windows W182 — Yandex 5.128 player hook repair (26.11.2026)

## Result

The owner-provided W54 diagnostic from CELIKOM 0.24.56 showed RESOURCE_HOOK_ATTACHED but no NATIVE_FILEINFO_REQUEST, SOURCE_ACTIVE_REPLACEMENT, or actual replacement playback evidence. The old renderer finder selected a class from the file-info endpoint module, not the method owner used by the live player.

**Root cause confirmed from the exact signed official Yandex 5.128.0 ASAR:** the player-side getFileInfo method is on the live player class/base and reads an object containing id; the older endpoint wrapper exposes a different getFileInfo implementation with trackId and a two-argument signature. CELIKOM attached to the endpoint wrapper and therefore missed calls made by the live player.

## Vendor evidence

- Official vendor build: 5.128.0.r22145392.
- Signed app.asar SHA-256: b50abc625d3f426aa140b17861f8075eff3e17d71b2038e48ded1b6592cb8d0b.
- Read-only audit: W181 workflow 45828560514, SUCCESS.
- Endpoint wrapper candidate: app/_next/static/chunks/6820-4385b9c887bedd61.js, webpack module 72882. Its getFileInfo signatures take two arguments and inspect trackId; its batch method inspects trackIds.
- Live player candidate: app/_next/static/chunks/app/(product)/layout-0e6c540f981e0383.js. Its getFileInfo(e) method inspects e.id; the player class inherits the actual method owner. The old endpoint string search could not identify this player method as the active hook target.

## Repair in main

1. current-source-refresh.mjs exposes resourcePrototype(), which walks the pinned official Yandex player prototype chain and returns the prototype that actually owns getFileInfo.
2. renderer-entry.mjs now attaches the current-player observer first, asks for that actual method owner, and attaches the native resource adapter there. The old endpoint-module scan remains as a compatibility fallback for reviewed older builds.
3. native-resource-adapter.mjs accepts trackId or id from any argument object, supports the reviewed two-argument call form, reads quality from all arguments, and supports batch trackIds or ids.
4. The player remains the official Yandex player. No alternate player, audio engine, VPN, gain, UI or authentication redesign was introduced.

## Verification

- Backup before W182 player-hook integration: backup/windows-main-pre-w182-player-hook-20261126 at f3fd3408028c2b04d82b675cd81feaa97ffef9eb.
- Source fix and renderer regression: a40878bf54791cb49d45345f154ede89c484738c.
- Test-fixture corrections: f0ea1bbed86cedcd0db30122e689d5a8b0d384a1, 4cb066364ff4e5bfbb9f1f4c41618b2da69aff2a.
- Generic CI: run 45829060558, SUCCESS.
- Windows integration CI: run 45829060572, SUCCESS. Includes the native-resource, renderer relay, current-player and audio regression suite.
- Isolated FlokiNET Windows cross-build: run 45829060571, SUCCESS.

## Release boundary

- Next owner candidate: **0.24.58 / P-256 sequence 5**.
- 0.24.57 / sequence 4 is already on the owner site but remains unaccepted; do not treat it as the repaired build.
- The signed customer channel remains approved:null, baseline 0.24.55 / sequence 2.
- Last personally accepted audible version remains 0.24.54.
- The 0.24.58 owner release must be independently verified on celikom.com by the exact full EXE SHA before giving the owner a link. No GitHub draft or Actions URL is a substitute.
- Owner must personally hear mapped track 144530503 («Ау»), another mapped replacement, and confirm ordinary/unmapped playback, Next, Play/Pause. No customer promotion before explicit «выпускай всем».
- Do not change Android, browser extension, paid features, Hostinger, VPN/gain/audio architecture, or customer stable approval.
