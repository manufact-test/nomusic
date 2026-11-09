# CELIKOM Android — lessons from Windows W28 (09.11.2026)

READ-ONLY CROSS-PLATFORM AUDIT. No Windows source changed; no Android behavior changed. Evidence: Windows branch experiment/windows-companion-integration-20261108 @ 7c1858e634a91c7c5516353fd7010aa822bf73d0. Functional Windows W28 SHA 4418f4fa190d247694696558b8016cd7d7e2cc8a, CI native-host 42634928333 PASS, user audio playback still FAIL/UNVERIFIED.

## What Windows has already proven

- Real Electron/ASAR host can attach its source adapter to renderer's getFileInfo and getFileInfoBatch inside the native Windows Yandex app; source resolve passes renderer -> trusted Electron main -> local CELIKOM .NET bridge -> backend; renderer never gets local bridge capability. These are process/contract proofs, not audible sound.
- Windows W22 adapter guards exact numeric track ID, current revision, and cancellation after Next/Stop, bounded deadlines and original fallback. Calls original native method when no grant; restores hooks on dispose.
- Windows W28 exports redacted owner events: NATIVE_FILEINFO_REQUEST, NATIVE_FILEINFO_OK/ERROR/SLOW, SOURCE_ORIGINAL/MAPPED/SYNTHETIC_RESPONSE, MEDIA_REQUEST_SEEN / HTTP status when observable, MEDIA_PLAY/PAUSE/ERROR when DOM audio exists; absence of events means NOT_OBSERVED, not PASS.
- Windows source-only tests/actual Yandex non-authenticated startup passed. Owner W26 actual music test FAILED: with CELIKOM active a new track immediately paused; starting replacement mid-track left original playing. W28 logs are waiting for owner evidence; no repair verified.

## Android applicability

1. Reuse the **design contract** (exact track+edition, current generation fencing, timeout, original fallback, range/mime/codec checks) but NOT Electron/JS getFileInfo hooks. Android has distinct native Retrofit FileInfoDto -> sw7.y0/z0 -> eed path and the single original Yandex decoder. Existing libxposed observer only counts conversions.
2. Import the **diagnostic stage boundaries**, not the DOM listeners: Android should distinguish APP_LOADED, HOOK_ARMED, DTO_CONVERTED, EXACT_TRACK_EDITION_BOUND, PREPARE_SOURCE_SELECTED, MEDIA_SOURCE_OPENED, DECODE_STARTED, PLAYING, PAUSED, SEEK, NEXT, FALLBACK and NO_OBSERVATION where APIs cannot observe them. Keep only sanitized event types, optional preapproved test track IDs; no URLs, key, OAuth, headers or audio data.
3. Windows toDownloadInfo currently deletes key/iv, rewrites codec/bitrate, sets urls/url, and may return a synthetic envelope after 130 ms grace if native file-info stalls (see windows-companion/w22/native-resource-adapter.mjs lines 19-31, 146-187). **Do not copy this behavior blindly into Android**: native Yandex FileInfoDto has key/codec/r128/gain and different decoder ownership; a syntactically valid source mapping can still cause pause/decoder rejection. Treat synthetic metadata as high-risk until proven on a real decoded track.
4. Windows's stale-cache Start mid-track is not evidence that Android can force immediate replacement; decide clearly between next-track-only vs prepare-before-play using observed native pipeline. Never mid-play oscillate between original and replacement.
5. Do NOT copy Windows .NET bridge auth/IPC into Yandex process. Android owns its own grant flow after explicit account authorization, no Yandex session extraction. Keep single native player/clock.

## Next Android gate

- First solve an **isolated rootless in-process runtime** compatible with physical ARMv7 (the signed #170gpr split includes armeabi-v7a), without deleting official HONOR Yandex. Investigating a package-ID-isolated clone is only a hypothesis; no installable patched client or owner audio PASS exists.
- After runtime hooks actually arm, build sanitized event recorder BEFORE modifying FileInfoDto/e ed or serving replacement audio. Determine exact track+edition -> DTO -> eed -> native MediaSource before prepare; only then one legally permitted source swap.
- Windows W28 owner diagnosis, when available, can be compared for **stage failure patterns**; never assume it is the same bug or that Windows has working audio.

Sources in this repository:
- docs/windows/NEXT-CHAT.md
- docs/windows/W28-OWNER-DIAGNOSTICS-20261109.md
- docs/windows/W27-OWNER-AUDIO-FAILURE-20261109.md
- windows-companion/w22/native-resource-adapter.mjs
- windows-companion/w23/host.cjs
- windows-companion/w23/renderer-entry.mjs
- android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeHookEntry.java
