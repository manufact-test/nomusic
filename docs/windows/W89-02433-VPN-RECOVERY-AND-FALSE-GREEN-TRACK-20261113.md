# W89: Windows 0.24.33 TEST — VPN switch revalidation + false green original (2026-11-13)

## User-supplied evidence / current scope

Owner reported two audio drops while listening on **0.24.32**, second after turning off one VPN and turning on another. First drop was loud with a brief hiss and fast apparent recovery; second smoothly fell back to original, then took around 40–50 seconds to reconnect.

Two diagnostics (`диагна.txt`, `Вставленный текст(20261113-123416).txt`) show:
- At 2026-11-13 **12:06:46 UTC** an expired audio URL received HTTP 403 `PLAYER_403_PHP_INVALID_AUDIO_TOKEN`, a new signed URL received HTTP 206 and a new player start at 12:06:47. **No confirmation about why hiss was loud**.
- At **12:26:28–12:26:29 UTC**, a track source `track=106040459` hit LOCAL_HTTP_TIMEOUT/RESOLVE_TRANSIENT while VPN changed. At **12:26:40** entitlement GET retried, at 12:26:44 the app disabled the bridge `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED`. `ACTIVE_ENTITLEMENT_ROUTE_CHANGED` appeared only at **12:26:58** because old code ignored route changes while still enabled and busy. Failed rechecks at 12:27:07/18/28; recovered only at **12:27:29**. The long outage is real, not a visual warning.
- Owner screenshot has song **«Ты» by тринадцать карат** while CELIKOM UI showed **«Подмена активна · версия CELIKOM»**, but the owner hears the censored original. Fresh diagnostic at **12:33:19 UTC**: current `track=89285816`, grant found, `SOURCE_BATCH_MAPPED`, but **no matching signed media HTTP GET** in the following 34 seconds and `NativeMediaUrlExactMatchObserved=false`. A mapping alone does not prove current Yandex decoder used it. Avoid equating HTTP 206/prefetch or file-info mapping with sound. This **does not yet prove the exact cause** of original fallback; owner listening remains definitive.
- NativeIntegration Active, native module matching in 0.24.32. Old source witness CDP `kUrl` availability remains unknown and may never expose that property.

## Exact backup / work

Repo `manufact-test/nomusic`. Work branch `experiment/windows-w89-vpn-fast-recovery-audio-proof-20261113`.
- Exact rollback before any W89 code `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`; stable W88 0.24.32 installer in Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.32-AUTORUN-DEFAULT-ON-TEST.exe` (id `libfile_c4548e97dfac81918a6d250d92ba3e73`), SHA256 `715D7F8B97F2D97E2ACE2FBBB0211F760F9A34E2EB14864FE91CB261C965CF4E`.
- New TEST version **0.24.33**, native module **0.24.26** (upgrade via original safe NativeIntegrationManager.Upgrade). Never overwrite owner's previous installed version remotely. Owner autostart/DPAPI/CI checks must be retained.

## Changes / safety

### VPN refresh
- `MainWindow.OnNetworkAddressChanged`: react even when playback still active; mark new route; cancel old GET; coalesce via 1.4s debounce and 750ms settle, reschedule one new check after current ends.
- `CompactPopupActions.RefreshCompactAccessAsync`: single shared CTS on active HTTP, passes cancellation to GET and original ordinary retry; short 3s GET on changed route or while suspended. An intentionally canceled old-route request must **not** disable music by itself.
- `EntitlementCheckRecovery`: suspended recheck cadence 3s instead of 5s, normal healthy 15s unchanged; fast-route mode only within 30s after network signal. Any recovered activation still needs a fresh successful authenticated server GET and unchanged account and verified official native module. Explicit Stop remains authoritative. No offline authorization bypass.
- No guarantee reconnects in under N seconds if new VPN blocks the CELIKOM server; no fabricated success.

### «Ты» / false green
- `PlaybackSourceEvidence` + CompactPopup: green **only** when native status is `NATIVE_SOURCE_VERIFIED`, a narrow CDP current decoder `kUrl`/signed-fields/`kIsPlaying` corroboration for current song. Merely `NATIVE_MAPPING_ACCEPTED`, `SDK_MAPPING_ACCEPTED`, `SOURCE_BATCH_MAPPED` yields **neutral** `Версия CELIKOM передана Яндексу` (NOT proof of actual speakers). No new yellow banners.
- `BridgeServer` accepts verified-only status; matching `MainWindow` label.
- `w23/host.cjs`: retains existing passive CDP proof but now attaches source confirmation to current status; invalidates on pause/source changes/bridge loss. Tracks recent **successful native Media HTTP 206/200 for the exact track** as only a suppression condition for a recovery attempt, NOT proof of sound.
- If current mapping accepted, a signed grant issued for the current song, native Network observer is present, **no corresponding 200/206 media GET** occurs within ~3.5–16s of first observed current entity: at most **one** `__celikomBridgeNativeRefreshUnfetched` request per track per 120s. Renderer independently checks exact current track, enabled state and native player availability, then requests Yandex's existing version-pinned `reloadEntity("QUALITY_CHANGE")` only; preserves queue/pause/seek. Cannot touch other tracks, no loop, no synthetic audio requests. This may help a Yandex original source retained from cache, but **requires owner field QA** and won't guarantee fix if cause is elsewhere.
- Approved signed URL, exact source and audio error evidence never exported to diagnostics; only allowlisted code/track IDs.
- Native host/renderer modified intentionally, so **0.24.32→0.24.33 manual Start may need safe module upgrade**, and W89 in-place CI MUST expect new assets, preserve encrypted DPAPI, same installer AppId and rollback.

## Required checks before delivering

1. W23 Node tests: native resource, renderer, source reload position/pause, CDP source witness, transient/403. W15 .NET entitlement and false-green. W21/W24 safe vendor and backup. GUI `-warnaserror`; Inno setup in-place from exact W88 artifact SHA.
2. Do not release until latest Actions W89 run is GREEN. Then confirm installer SHA and Library upload; preserve old candidate. Do not declare user's VPN/audio actually fixed without playback test on their PC.
3. Manual owner QA: change VPN while listening and check reconnect time; play **«Ты» by тринадцать карат**, distinguish original vs CELIKOM sound, and note the small neutral vs green status. Capture diagnostics if still original, and any hissing/transients. No forced VPN change or synthetic tests remotely.

## CI pending

- Workflow `.github/workflows/windows-w89-vpn-fast-recovery-track-fix-installer.yml`.
- Latest started workflow https://github.com/manufact-test/nomusic/actions/runs/43428796923; **verify outcome** before asserting success.
