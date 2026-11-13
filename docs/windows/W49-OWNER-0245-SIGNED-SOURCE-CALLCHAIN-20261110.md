# W49 — Real 0.24.5 owner diagnostic + exact signed native file-info path (2026-11-10)

**Status: Windows audio NO-GO, approved replacements remain silent per owner's 0.24.4 report; 0.24.5 delivered diagnostics, not an audio fix.** No owner install, no backend/Android/production changes in W49.

## Source: owner-uploaded `CELIKOM-diagnostics-20261110-105211.txt`
Generated 2026-11-10 07:52:13 UTC. `AppVersion=0.24.5.0`, `NativeModuleVersion=0.24.5`, `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, `SignedIn=true`.

### What newly became observable
- `PLAYER_CDP_READY` at 07:51:30.346 UTC, so the passive CDP Media observer successfully attached in native Electron.
- `PLAYER_ENGINE_STARTED` 07:51:30.834, 07:51:31.958; `PLAYER_ENGINE_PAUSED` 07:51:31.959; `PLAYER_ENGINE_FAST_PAUSE` 07:51:31.960. Further `PLAYER_ENGINE_STARTED` at 07:51:38.388/38.400 and `PLAYER_ENGINE_PAUSED` 07:51:45.637. `PLAYER_CDP_EVENT_START` and `PLAYER_CDP_EVENT_PAUSE` confirm underlying events exist.
- **Critical timing:** the fast-pause at 07:51:31 occurred about 15 seconds **before the first approved replacement** track 42498653 was mapped at ~07:51:47.378. Therefore `EngineFastPauseObserved=true` in the export header is a **global recent-session indicator**; **DO NOT ascribe it to approved replacement**, or claim this specific pause is the owner-observed substitution failure.
- After the earliest approved replacement mapping at ~07:51:47, **no further PLAYER_ENGINE_STARTED/PAUSED or CDP start/pause events were logged until 07:52:13 export**. So native source selection occurred but a new Chromium media playback start **was not observed**. It might still have made internal calls that CDP Media does not expose, particularly WebAudio. Real owner playback remains FAIL.
- `PlayerAudibleEventObserved=false`; no `PLAYER_AUDIO_AUDIBLE` event; `DecoderErrorObserved=false` and no `PLAYER_CDP_PIPELINE_ERROR`/error message event. Do not interpret missing error as proof decoder accepted the source.
- Two original/unsupported IDs 40193669 and 149888838 had `GRANT_MISS`; the first `SOURCE_ORIGINAL`. Their earlier player Start/Pause events cannot be treated as alternate-source playback.
- Approved IDs 42498653, 85025192, 50163052, 1944605, 50163063, 39949113 all have GRANT_FOUND/RESOLVE_APPROVED and mapping. Four approved IDs (42498653, 85025192, 50163052, 1944605) also have **separate diagnostic** 206 + audio/mpeg + MP3 first bytes. The 50163063 and 39949113 lack independent probes because the probe is capped at 4 tracks; that is **not** network failure.
- For every observed actual native file-info `downloadInfo` before mapping: `FILEINFO_NATIVE_KEY_FIELD`, `FILEINFO_NATIVE_TRANSPORT_FIELD`, `FILEINFO_NATIVE_CODEC_AAC`, `FILEINFO_NATIVE_URLS_ARRAY`. `FILEINFO_NATIVE_IV_FIELD` not observed. These events record **property presence**, not original encrypted transport value, actual secret key or contents. W22 adapter clears `key/iv` and sets `codec='mp3'`, `transport='raw'`, `gain=false`, `urls=[signedUrl]` for approved MP3.

## Independent genuine Windows Yandex 5.126.1 static audit
- Exact original Yandex installer pinned SHA256 `131fa1d9bc32eee2baadbdd7c1fe7aa8ba4a2f89ec972dd462aa06ee5b170435`, valid Yandex Authenticode signer; original ASAR exact SHA256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`. **No modified owner Yandex, patched app, account or native playback during this static investigation.**
- W49 read-only source CI https://github.com/manufact-test/nomusic/actions/runs/42778680569 SUCCESS.
- W49b source-to-media-path CI https://github.com/manufact-test/nomusic/actions/runs/42778881310 SUCCESS and W49c precise path https://github.com/manufact-test/nomusic/actions/runs/42779137671 SUCCESS.
- Original code in `app/_next/static/chunks/6820-4385b9c887bedd61.js` includes both `get-file-info` and `resources/v2/file-info`, `RAW='raw'`, `ENCRAW='encraw'`, AAC/MP3 codecs and an encrypted offline download branch. **Important: original Yandex supports raw and mp3, therefore substituting raw MP3 is not automatically an invalid format.**
- Actual original media-provider in `app/_next/static/chunks/app/(product)/layout-4afaa928fcc37741.js` has `getMediaSource` → `getFileInfo({...,transports:[selected],codecs:this.codecs})` → `createMediaSource({downloadInfo,...})`, with an independent fallback request using `RAW` transport under some codec/ENCRAW conditions. `createMediaSource` checks for an error response and missing `downloadInfo.urls[0]` then constructs the source; whether core playback accepts CELIKOM MP3 has **not** been proven.
- Native downloader module specifically expects `transport=ENCRAW` for offline download and uses AES-CTR, **but that is NOT the same as proving the online player rejects RAW**. Do NOT mix offline download and native playback.
- Distinct actual original playback `app/_next/static/chunks/9091-cdf5e7f5a0e6a5b5.js` contains `getMediaSource(...).then(... corePlay(...))` and its own error handling. **The next observability gap is between mapped `getFileInfo` and `getMediaSource / corePlay`, not HTTP CORS.** W49d focuses static source around that boundary.

## Next engineering action — avoid blind release
1. Add a STRICTLY READ-ONLY stage observer for **actual Yandex media provider and player core transitions** in an isolated test; distinguish `getMediaSource` ready/reject and `corePlay` call/resolve/reject, no account/source URL or error text, no extra media commands. Preserve identity/promises, no fake sound or second player.
2. If original loader rejects plaintext MP3 on a transport/metadata contract, prove the exact expected shape and implement minimal format-compatible fix. **Do not append original encrypted key to plain MP3** or force unknown codecs. Check request codecs/transports and actual source shape. Use original player/clock for pause/seek/next.
3. Owner 0.24.5 installed and matched; do NOT ask repeat unchanged trial. No new exe until a meaningful fix or a much more precise single diagnostic can be validated; no false audio PASS claims.
4. Keep W45 production native-origin CORS and original Yandex signature/recovery intact. No changes to Android/Test.50/site/backend.

**Backup:** `backup/windows-w49-owner-0245-post-cors-native-track-failure-20261110` @ `0bda005df39509db79dffb0f1e39f4fb3dcf7e9d`.
